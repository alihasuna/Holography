"""Is the residual between the corrected per-g Bloch variant and the transfer matrix due to
per-g matching? Compare with a rod-summed single-Bloch-wave match using the same eigenvectors."""
import numpy as np, warnings
import simulation.bloch_wave as BW
from harness import *
from patched import patched_matrix, patched_R
warnings.simplefilter("ignore")
mm = 16
beams = rod_hkls("111", mm, allowed_only=False)
n_out = SURF["111"][0]
mvals = np.array([int(round(np.dot(hk, (1,-1,1))/3)) for hk in beams])
for tm in [5, 7, 8, 10, 13.25, 18, 22, 26.5]:
    t = tm*1e-3
    k = k_in(t, "111")
    mat, g, kz, s_g = patched_matrix(k, beams, n_out, 0.07)
    ev, evec = np.linalg.eig(mat)
    n = len(beams)
    kap = K_LEG*np.sin(t)
    sel = np.where(np.imag(ev) > 0)[0]
    betas = []
    for j in sel:
        Cj = evec[:n, j]
        w = np.abs(Cj)**2; cen = np.sum(mvals*w)/np.sum(w)
        beta = 1j*np.sum((kz+ev[j])*Cj)/np.sum(Cj)
        betas.append((abs(cen), beta, ev[j]))
    betas.sort(key=lambda x: x[0])
    beta = betas[0][1]
    Rrod = (1j*kap - beta)/(1j*kap + beta)
    ref = exact_1d_rocking([t], "111", mmax=mm, gamma=GAMMA, mu=0.07, include_U0=True, K=K_LEG)[0]
    Ppg = patched_R(t, beams, "111", 0.07)[0]
    spread = np.std([ (1j*kap-b)/(1j*kap+b) for c,b,e in betas[:5]])
    print("%6.2f mrad: n(Im>0)=%d of %d | ref |R|^2=%.4f arg=%+.3f | rod-summed single wave |R|^2=%.4f arg=%+.3f | per-g (legacy-style) |R|^2=%.4f arg=%+.3f | spread of R over 5 central copies %.1e" % (
        tm, len(sel), 2*n, abs(ref)**2, np.angle(ref), abs(Rrod)**2, np.angle(Rrod), abs(Ppg)**2, np.angle(Ppg), spread))
