"""Legacy Bloch/R-matrix restricted to the Si(111) specular rod vs the exact 1-D reference."""
import numpy as np, warnings
from harness import *
warnings.simplefilter("ignore")
mmax = 8
beams = rod_hkls("111", mmax)
print("beam list (rod only):", beams)
th = np.arange(3.0, 40.01, 0.25) * 1e-3
# exact references
ref_legphys = exact_1d_rocking(th, "111", mmax=mmax, gamma=1.0, mu=0.07, include_U0=False)   # same physics as legacy
ref_true = exact_1d_rocking(th, "111", mmax=24, gamma=GAMMA, mu=0.07, include_U0=True)       # U0 + gamma, mu on all U_g
rows = []
for t, r1, r2 in zip(th, ref_legphys, ref_true):
    L = legacy_pieces(t, beams, "111", 0.07, "legacy")
    E = legacy_pieces(t, beams, "111", 0.07, "exact")
    rod = rod_members(beams, "111")
    rows.append((t*1e3, abs(L["R"][0])**2, abs(np.sum(L["R"][rod]))**2, abs(E["R"][0])**2, abs(np.sum(E["R"][rod]))**2,
                 abs(r1)**2, abs(r2)**2, L["n_pos"], np.sum(abs(L["R"])**2), np.angle(np.sum(E["R"][rod])), np.angle(r1)))
rows = np.array(rows)
np.save("t3_rows.npy", rows)
print(" th(mrad) |R000|^2 leg  |sumR|^2 leg  |R000|^2 exactsolve |sumR|^2 exactsolve  ref(no U0,no gamma)  ref(U0,gamma)  nIm>0  sum|R_g|^2(leg)")
for r in rows[::4]:
    print(" %6.2f   %9.5f   %9.5f   %9.5f   %9.5f   %9.5f   %9.5f   %3d   %8.4f" % tuple(r[:9]))
# agreement metrics
d1 = np.max(np.abs(rows[:,4]-rows[:,5]))
d2 = np.max(np.abs(rows[:,2]-rows[:,5]))
print("max | |sumR|^2(legacy matrices, exact solve) - ref(same physics) | = %.3e" % d1)
print("max | |sumR|^2(legacy as shipped) - ref(same physics) | = %.3e" % d2)
ph = np.angle(np.exp(1j*(rows[:,9]-rows[:,10])))
print("max |phase(sumR exact solve) - phase(ref same physics)| = %.3e rad" % np.max(np.abs(ph)))
# peak positions
for name, col in [("legacy shipped |R000|^2", 1), ("legacy shipped |sum rod R|^2", 2), ("legacy exact-solve |sum rod R|^2", 4), ("ref same physics", 5), ("ref U0+gamma", 6)]:
    y = rows[:, col]
    # local maxima above 0.02
    pk = [rows[i,0] for i in range(1,len(y)-1) if y[i]>y[i-1] and y[i]>=y[i+1] and y[i]>0.01]
    print("%-34s maxima at (mrad): %s" % (name, np.round(pk, 2)))
for n in [3,4,5,7,8]:
    tb = theta_B((n,-n,n))
    print("(%d,-%d,%d): vacuum Bragg %.3f mrad; refraction-corrected ext (V0=14.12 V) %.3f; (V0=12 V) %.3f" % (n,n,n, tb*1e3, theta_ext_refr(tb,14.12)*1e3, theta_ext_refr(tb,12.0)*1e3))
