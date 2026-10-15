import numpy as np, warnings
from harness import *
from patched import patched_R
warnings.simplefilter("ignore")
beams = rod_hkls("111", 8)
th = np.arange(5.0, 36.01, 0.25) * 1e-3
ref = exact_1d_rocking(th, "111", mmax=8, gamma=GAMMA, mu=0.07, include_U0=True)
ref24 = exact_1d_rocking(th, "111", mmax=24, gamma=GAMMA, mu=0.07, include_U0=True)
P = np.array([patched_R(t, beams, "111", 0.07)[0] for t in th])
print("rod beams m<=8 (%d beams). Patched legacy (U0+gamma, per-g exact solve, sum over rod) vs exact 1-D (same 8 orders):" % len(beams))
print("  max | |R|^2 diff | = %.2e ; max |R| diff = %.2e ; max phase diff where |R|^2>1e-3 = %.2e rad" % (
    np.max(abs(abs(P)**2-abs(ref)**2)), np.max(abs(P-ref)), np.max(np.abs(np.angle(P/ref))[abs(ref)**2>1e-3])))
print("  truncation effect (exact 1-D, 8 vs 24 orders): max | |R|^2 diff | = %.2e" % np.max(abs(abs(ref24)**2-abs(ref)**2)))
# R000 alone vs rod sum in the patched variant
P0 = np.array([patched_R(t, beams, "111", 0.07)[1][0] for t in th])
print("  patched: |R_000|^2 alone vs |sum_rod R|^2: max diff = %.3f (so reporting R_000 alone is wrong)" % np.max(abs(abs(P0)**2-abs(P)**2)))
def maxima(x, y, thr=0.01):
    return [round(x[i],2) for i in range(1,len(y)-1) if y[i]>y[i-1] and y[i]>=y[i+1] and y[i]>thr]
print("  maxima ref24      :", maxima(th*1e3, abs(ref24)**2))
print("  maxima patched    :", maxima(th*1e3, abs(P)**2))
print("  maxima |R000|^2 patched:", maxima(th*1e3, abs(P0)**2))
np.save("t4.npy", np.vstack([th, ref24, ref, P, P0]))
# effect of the shipped SVD sweep on the corrected physics: replicate the sweep
import simulation.r_matrix as RM, simulation.bloch_wave as BW
from patched import patched_matrix
def patched_svd(theta):
    n_out = SURF["111"][0]; k = k_in(theta, "111")
    mat, g, kz, s_g = patched_matrix(k, beams, n_out, 0.07)
    ev, evec = np.linalg.eig(mat); n = len(beams)
    gam, Cv = BW.select_evanescent(ev, evec, n)
    R, alpha = RM.solve_reflection_amplitudes(gam, Cv, kz, k, g, surface_normal=n_out)
    return np.sum(R[rod_members(beams, "111")])
S = np.array([patched_svd(t) for t in th])
print("  shipped SVD-sweep solve on corrected matrices: max | |R|^2 - ref | = %.3f ; maxima: %s" % (np.max(abs(abs(S)**2-abs(ref)**2)), maxima(th*1e3, abs(S)**2)))
for t in [8.5e-3, 13.25e-3, 18.0e-3, 26.5e-3]:
    i = np.argmin(abs(th-t))
    print("   theta=%.2f mrad: ref |R|^2=%.4f, patched exact-solve %.4f, patched + shipped SVD sweep %.4f" % (th[i]*1e3, abs(ref[i])**2, abs(P[i])**2, abs(S[i])**2))
