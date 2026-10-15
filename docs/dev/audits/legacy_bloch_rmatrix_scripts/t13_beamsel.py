"""Beam selection: |s_g| ranking (legacy) vs rod-complete sets, using the corrected in-memory variant
(U0, gamma, mu on all U_g, forbidden g kept as basis beams, exact per-g solve, rod sums)."""
import numpy as np, warnings, time
import simulation.bloch_wave as BW
from harness import *
from patched import patched_R
warnings.simplefilter("ignore")
n_out, rod_dir, az = SURF["111"]
M = 10
allg = [(h, k, l) for h in range(-M, M+1) for k in range(-M, M+1) for l in range(-M, M+1)
        if (h+k) == 0 and (h % 2 == k % 2 == l % 2)]  # zeroth Laue zone of [110], fcc-allowed parity (diamond-forbidden kept)
allg = [g for g in allg if g != (0, 0, 0)]
G = 2*np.pi/A*np.array(allg, float)
inpl = np.array([np.linalg.norm(g - np.dot(g, n_out)*n_out) for g in G])
for tm in [13.3, 16.18]:
    t = tm*1e-3; k = k_in(t, "111")
    ref1d = exact_1d_rocking([t], "111", mmax=24, mu=0.07)[0]
    print("theta = %.2f mrad ; 1-D (specular rod only) |R|^2 = %.4f" % (tm, abs(ref1d)**2))
    idx, s_g = BW.select_strong_beams(k, allg, G, n_strong=len(allg))
    for n in [20, 40, 80, 140]:
        sel = [(0, 0, 0)] + [allg[i] for i in idx[:n]]
        Rs, R, gam = patched_R(t, sel, "111", 0.07)
        nrod = len(rod_members(sel, "111"))
        print("   |s_g|-ranked n=%3d: specular-rod members in set %2d ; |sum_rod R|^2 = %.4f" % (n, nrod, abs(Rs)**2))
    for gcut, mcut in [(0.01, 12), (2.2, 8), (2.2, 12), (4.4, 8)]:
        sel = [(0, 0, 0)] + [allg[i] for i in range(len(allg)) if inpl[i] <= gcut and abs(np.dot(G[i], n_out)) <= mcut*2*np.pi/A*np.sqrt(3)/1.0001*1.0001]
        t0 = time.time(); Rs, R, gam = patched_R(t, sel, "111", 0.07)
        print("   rod-complete: |g_par|<=%.2f 1/A, |g_perp|<=%2d b: %3d beams ; |sum_rod R|^2 = %.4f (%.1f s)" % (gcut, mcut, len(sel), abs(Rs)**2, time.time()-t0))
