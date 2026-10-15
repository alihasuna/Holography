"""Sanity test (a): current conservation without absorption."""
import numpy as np, warnings
import simulation.r_matrix as RM, simulation.bloch_wave as BW
from simulation.kinematical import generate_reciprocal_lattice
from harness import *
from patched import patched_R
warnings.simplefilter("ignore")
beams_allowed = rod_hkls("111", 8)
beams_all = rod_hkls("111", 16, allowed_only=False)
print("A. shipped legacy, absorption_ratio=0, rod-only beams (allowed only, as the code builds them):")
print("   th(mrad)  n(Im g>0)/2N   sum|R_g|^2   |sum_rod R|^2   |R_000|^2")
for tm in [6, 10, 13.2, 16, 20, 26.5, 30]:
    L = legacy_pieces(tm*1e-3, beams_allowed, "111", 0.0, "legacy")
    rod = rod_members(beams_allowed, "111")
    print("   %6.2f    %2d/%2d        %9.4f    %9.4f     %9.4f" % (tm, L["n_pos"], 2*len(beams_allowed), np.sum(abs(L["R"])**2), abs(np.sum(L["R"][rod]))**2, abs(L["R"][0])**2))
print("B. shipped legacy (compute_reflected_intensities), absorption_ratio=0, full 3-D beam set n_strong=20, max_index=6, beam azimuth [110]:")
hkl6, g6, _ = generate_reciprocal_lattice(max_index=6)
for tm in [10, 16, 20, 27.9]:
    k = k_in(tm*1e-3, "111")
    res = RM.compute_reflected_intensities(k, hkl6, g6, n_strong=20, absorption_ratio=0.0)
    hk = [r["hkl"] for r in res]; R = np.array([r["R_g"] for r in res])
    g = 2*np.pi/A*np.array(hk, float)
    kap = RM.compute_vacuum_kz(k, g)
    flux = np.sum(abs(R)**2*np.real(kap))/abs(np.dot(k, C.SURFACE_NORMAL))
    print("   th=%5.1f mrad: reported total sum|R_g|^2 = %.4f ; current-weighted sum |R_g|^2 Re(kappa_g)/kappa_0 = %.4f" % (tm, np.sum(abs(R)**2), flux))
print("C. corrected in-memory variant (U0, gamma, all rod g incl. forbidden, exact solve), mu = 0, legacy Im(gamma)>0 selection:")
for tm in [6, 10, 13.2, 16, 20, 26.5]:
    t = tm*1e-3
    Rs, R, gam = patched_R(t, beams_all, "111", mu=0.0)
    ref = exact_1d_rocking([t], "111", mmax=16, mu=0.0)[0]
    # count of Im>0 eigenvalues
    from patched import patched_matrix
    mat, *_ = patched_matrix(k_in(t,"111"), beams_all, SURF["111"][0], 0.0)
    ev = np.linalg.eigvals(mat)
    print("   th=%5.2f mrad: n(Im>1e-12)=%d, n(|Im|<1e-9)=%d of 2N=%d ; |sum_rod R|^2 = %.4f ; exact 1-D = %.4f" % (
        tm, np.sum(np.imag(ev)>1e-12), np.sum(abs(np.imag(ev))<1e-9), len(ev), abs(Rs)**2, abs(ref)**2))
