"""Sanity test (b): two-beam limit {000, (-4,4,-4)} on Si(111) against the analytic two-beam (Darwin) form."""
import numpy as np, warnings
from harness import *
from patched import patched_R
warnings.simplefilter("ignore")
G_hkl = (-4, 4, -4)
beams = [(0, 0, 0), G_hkl]
b, _ = rod_period("111"); G = 4 * b
def darwin(theta, mu, gamma=GAMMA, include_U0=True):
    U0 = U_hkl((0,0,0), LEG5, gamma, mu) if include_U0 else 0.0
    Ug = U_hkl((4,-4,4), LEG5, gamma, mu); Umg = U_hkl((-4,4,-4), LEG5, gamma, mu)
    kap = K_LEG*np.sin(theta)
    A0 = kap**2 + U0 - G**2/4
    root = np.sqrt(A0**2 - Ug*Umg + 0j)
    cands = [-(A0 - s*root)/Ug for s in (+1, -1)]
    return min(cands, key=abs)  # physical branch |R|<=1
for mu in [0.0, 0.07]:
    th = np.arange(10.0, 18.0001, 0.02) * 1e-3
    D = np.array([darwin(t, mu) for t in th])
    P = np.array([patched_R(t, beams, "111", mu=max(mu, 1e-6))[0] for t in th]) # corrected 2-beam Bloch (tiny mu for selection when mu=0)
    L = [legacy_pieces(t, beams, "111", mu, "legacy") for t in th]
    L0 = np.array([abs(x["R"][0])**2 for x in L]); Lg = np.array([abs(x["R"][1])**2 for x in L]); Ls = np.array([abs(x["R"][0]+x["R"][1])**2 for x in L])
    Le = [legacy_pieces(t, beams, "111", mu, "exact") for t in th]
    Les = np.array([abs(x["R"][0]+x["R"][1])**2 for x in Le])
    b_, co = rod_potential_coeffs("111", 4, mu=mu, only=[0, 4, -4])
    E = np.array([exact_1d_R(K_TRUE*np.sin(t), b_, co, 1500)[0] for t in th])
    def centre(y):
        w = y > 0.5*y.max(); return th[w].mean()*1e3, (th[w].max()-th[w].min())*1e3, y.max()
    print("mu=%.2f" % mu)
    for name, y in [("Darwin analytic (U0,gamma)", abs(D)**2), ("corrected 2-beam Bloch, sum over rod", abs(P)**2), ("exact 1-D, U0+U(+-444) only", abs(E)**2),
                    ("SHIPPED |R_000|^2", L0), ("SHIPPED |R_(-4,4,-4)|^2", Lg), ("SHIPPED |R_000+R_g|^2", Ls), ("legacy matrices exact solve |R_000+R_g|^2", Les)]:
        c_, w_, m_ = centre(y)
        print("   %-42s centre(FWHM-mean) %.3f mrad  FWHM %.3f mrad  peak %.4f" % (name, c_, w_, m_))
tb = theta_B((4,-4,4))
U0 = U_hkl((0,0,0)).real; Ug = abs(U_hkl((4,-4,4)))
print("vacuum Bragg (4,-4,4): %.3f mrad; Darwin centre sqrt(thB^2 - U0/K^2) = %.3f mrad; plateau width |U_g|/(K^2 th) = %.3f mrad" % (
    tb*1e3, np.sqrt(tb**2 - U0/K_LEG**2)*1e3, Ug/(K_LEG**2*np.sqrt(tb**2-U0/K_LEG**2))*1e3))
print("same without gamma: plateau width %.3f mrad" % (Ug/GAMMA/(K_LEG**2*np.sqrt(tb**2-U0/K_LEG**2))*1e3))
