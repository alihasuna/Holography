import numpy as np, warnings
from harness import *
from layered import Layered, PENG_HIGH
warnings.simplefilter("ignore")
a = 5.4309
FE2V = 47.87764
def V0_of(par): return FE2V * 8 * np.sum(par[0]) / a**3
def th_ext_bragg(n_hkl, V0):
    d = a / np.linalg.norm(n_hkl)
    Dl = V0 * (1 + T / MEC2) / (T * (1 + T / (2 * MEC2)))
    th_int = np.arcsin(LAM / (2 * d) / np.sqrt(1 + Dl))   # internal Bragg with k_int
    return theta_ext_refr(th_int, V0), th_int
# check against reflection_holo's own number for (008)
print("V0(Peng high) = %.4f V ; theta_ext Bragg (008) = %.3f mrad (reflection_holo: 16.133)" % (V0_of(PENG_HIGH), th_ext_bragg((0,0,8), V0_of(PENG_HIGH))[0]*1e3))
# sanity: vacuum only -> R = 0; convergence in hz
L = Layered("001", hz=0.004); L2 = Layered("001", hz=0.002)
t = 16.933e-3
print("hz convergence at 16.933 mrad (001): R(hz=.004)=%s R(hz=.002)=%s" % (np.round(L.R(t), 6), np.round(L2.R(t), 6)))
Lb = Layered("001", n_bulk=8)
print("bulk-plane depth convergence: R(n_bulk=4)=%s R(n_bulk=8)=%s" % (np.round(L.R(t), 6), np.round(Lb.R(t), 6)))
res = {}
for surf, hkl in [("001", (0,0,8)), ("001", (0,0,12)), ("001", (0,0,4)), ("111", (4,-4,4)), ("111", (3,-3,3)), ("111", (5,-5,5))]:
    V0 = V0_of(PENG_HIGH)
    te, ti = th_ext_bragg(hkl, V0)
    if np.isnan(te):
        print(surf, hkl, "below escape angle"); continue
    offs = np.arange(-3.0, 3.0001, 0.02)
    Lm = Layered(surf, mu=0.05)
    R = np.array([Lm.R(te + o*1e-3) for o in offs])
    i = np.argmax(abs(R)**2)
    half = offs[abs(R)**2 > 0.5*abs(R[i])**2]
    res[(surf, hkl)] = (te, offs, R)
    print("%s %-11s theta_ext(Bragg,V0=%.2f)=%.3f mrad | 1-D layered max at offset %+.2f mrad (theta=%.3f), |R|^2max=%.4f, FWHM %.2f mrad, |R|^2 at offset 0 = %.4f, at +0.8 = %.4f" % (
        surf, str(hkl), V0, te*1e3, offs[i], te*1e3+offs[i], abs(R[i])**2, half.max()-half.min(), abs(R[np.argmin(abs(offs))])**2, abs(R[np.argmin(abs(offs-0.8))])**2))
np.save("t10_res.npy", np.array([0]))
# translation covariance and single-bilayer step phase on Si(111)
print("\nTranslation covariance, Si(111), layered model: crystal (and its surface) moved OUTWARD by one bilayer h = d111")
d111 = a/np.sqrt(3)
te, ti = th_ext_bragg((4,-4,4), V0_of(PENG_HIGH))
Lr = Layered("111", mu=0.05); Ls = Layered("111", mu=0.05, shift=-d111)
for th in [te, te+0.3e-3, 10e-3, 20e-3]:
    R0 = Lr.R(th); R1 = Ls.R(th)
    kap = K_TRUE*np.sin(th)
    pred = np.exp(-2j*kap*d111)     # exp(-i (k_out-k_in).R), vacuum vectors
    print("  theta=%.3f mrad: R_shift/R = %.6f%+.6fj ; exp(-2 i kappa_vac h) = %.6f%+.6fj ; |diff| = %.1e ; step phase arg = %+.4f rad" % (
        th*1e3, (R1/R0).real, (R1/R0).imag, pred.real, pred.imag, abs(R1/R0-pred), np.angle(R1/R0)))
# step phase at the reflectivity maximum and at vacuum Bragg
offs = np.arange(-2.0, 2.0001, 0.01); R = np.array([Lr.R(te+o*1e-3) for o in offs]); tmax = te + offs[np.argmax(abs(R)**2)]*1e-3
for name, th in [("1-D layered maximum", tmax), ("refraction-corrected Bragg (V0=13.91)", te), ("V0=12 V Bragg ext (physics_summary)", th_ext_bragg((4,-4,4),12.0)[0]), ("vacuum Bragg (no refraction: legacy physics)", theta_B((4,-4,4)))]:
    ph = -2*K_TRUE*np.sin(th)*d111
    print("  (4,-4,4) %-46s theta=%.3f mrad: Delta_phi = -2 k sin(theta) h = %.3f rad -> mod 2pi |.| = %.3f rad" % (name, th*1e3, ph, abs(np.angle(np.exp(1j*ph)))))
