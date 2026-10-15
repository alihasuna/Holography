"""Shipped code paths: run_simulation-style beam set, own rocking-curve function, SVD sweep diagnostics."""
import numpy as np, warnings
import simulation.r_matrix as RM, simulation.bloch_wave as BW
from simulation.kinematical import generate_reciprocal_lattice
from simulation.calibration import btx_bty_to_tilt_mrad, compute_incident_wavevector, compute_grazing_angle
from harness import *
warnings.simplefilter("ignore")

# 1. which rcond does the sweep pick? instrument by replicating the sweep on the shipped matrices
hkl6, g6, _ = generate_reciprocal_lattice(max_index=6)
print("generate_reciprocal_lattice(6): %d vectors; contains (2,-2,2)? %s ; (0,0,2)? %s ; (0,0,0)? %s" % (
    len(hkl6), (2,-2,2) in hkl6, (0,0,2) in hkl6, (0,0,0) in hkl6))
tx, ty = btx_bty_to_tilt_mrad(-814.0, 135.0)
k_exp = compute_incident_wavevector(tx, ty)
print("experimental k_i . n_out = %.4f 1/A (negative = into crystal); grazing %.2f mrad" % (np.dot(k_exp, C.SURFACE_NORMAL), compute_grazing_angle(tx, ty)))

def sweep_report(k, hkl_list, g_vectors, n_strong=20, mu=0.07):
    idx, _ = BW.select_strong_beams(k, hkl_list, g_vectors, n_strong=n_strong)
    sel_hkl = [hkl_list[i] for i in idx]; sel_g = g_vectors[idx]
    if (0,0,0) not in sel_hkl:
        sel_hkl.insert(0,(0,0,0)); sel_g = np.vstack([np.zeros((1,3)), sel_g])
    ev, evec, s_g, kz = BW.solve_bloch(k, sel_hkl, sel_g, absorption_ratio=mu)
    n = len(sel_hkl)
    gam, Cv = BW.select_evanescent(ev, evec, n)
    kappa = RM.compute_vacuum_kz(k, sel_g)
    kinc = np.dot(k, C.SURFACE_NORMAL)
    S = np.zeros((n,n),complex)
    for j in range(n): S[:,j] = (kz+gam[j]+kappa)*Cv[:,j]
    b = np.zeros(n,complex); b[0] = kappa[0]-kinc
    sv = np.linalg.svd(S, compute_uv=False)
    out = []
    for rc in [None, 1e-10, 1e-6, 1e-4, 1e-3, 5e-3, 0.01, 0.05, 0.1]:
        a = np.linalg.solve(S,b) if rc is None else np.linalg.lstsq(S,b,rcond=rc)[0]
        R = Cv@a; R[0]-=1
        resid = np.linalg.norm(S@a-b)/np.linalg.norm(b)
        flux = np.sum(np.abs(R)**2*np.real(kappa))/kappa[0].real
        out.append((rc, np.sum(abs(R)**2), flux, abs(R[0])**2, resid, int(np.sum(sv>(rc or 0)*sv[0]))))
    return sel_hkl, sv, out, int(np.sum(np.imag(ev)>0)), n

sel, sv, out, npos, n = sweep_report(k_exp, hkl6, g6)
print("\nexperimental tilt, n_strong=20 (+000): N=%d, eigenvalues with Im>0: %d of %d; singular values of S: max %.3g min %.3g (cond %.2e)" % (n, npos, 2*n, sv[0], sv[-1], sv[0]/sv[-1]))
print("  rcond      sum|R_g|^2   flux sum|R|^2 Re(kappa_g)/kappa_0   |R_000|^2   rel.residual   kept s.v.")
for r in out:
    print("  %-9s  %10.5f   %10.5f   %10.5f   %10.2e   %d" % (("exact" if r[0] is None else "%.0e"%r[0]),)+r[1:]) if False else \
    print("  %-9s  %10.5f   %10.5f   %10.5f   %10.2e   %d" % ((("exact" if r[0] is None else "%.0e" % r[0]),) + tuple(r[1:])))
chosen = [r for r in out[1:] if r[1] <= 1.05]
print("  -> shipped sweep keeps the LAST rcond with sum<=1.05: %s" % (("%.0e" % chosen[-1][0]) if chosen else "none (falls back to 0.1)"))

# 2. shipped rocking-curve function: sign of the tilt
print("\nr_matrix.compute_rocking_curve (shipped), 6 angles, n_strong=20, max_index=6:")
from simulation.calibration import compute_incident_wavevector as civ
angles, I = RM.compute_rocking_curve(hkl6, g6, grazing_range_mrad=(5, 80), n_points=6, n_strong=20)
n_x = np.dot(C.SURFACE_NORMAL, C.ZA_X); n_y = np.dot(C.SURFACE_NORMAL, C.ZA_Y)
for a_, i_ in zip(angles, I):
    k = civ(a_*n_x, a_*n_y)
    print("  alpha=%5.1f mrad  k.n_out=%+.3f 1/A (beam points %s)  specular intensity returned = %.6f" % (a_, np.dot(k, C.SURFACE_NORMAL), "OUT of the crystal" if np.dot(k, C.SURFACE_NORMAL) > 0 else "into crystal", i_))
