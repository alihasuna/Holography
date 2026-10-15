"""Sanity test (c) on Si(001) (008): shipped legacy pieces (surface_normal=(0,0,1)) vs references."""
import numpy as np, warnings
from harness import *
from patched import patched_R
warnings.simplefilter("ignore")
th = np.arange(12.0, 21.001, 0.02) * 1e-3
beams_leg = rod_hkls("001", 16)                       # allowed only, as the legacy lattice generator would give
beams_all = rod_hkls("001", 16, allowed_only=False)
L = [legacy_pieces(t, beams_leg, "001", 0.07, "legacy") for t in th]
rod = rod_members(beams_leg, "001")
L0 = np.array([abs(x["R"][0])**2 for x in L]); Ls = np.array([abs(np.sum(x["R"][rod]))**2 for x in L])
P = np.array([patched_R(t, beams_all, "001", 0.07)[0] for t in th])
E = exact_1d_rocking(th, "001", mmax=16, mu=0.07)
def pk(y, lo, hi):
    w = (th*1e3 >= lo) & (th*1e3 <= hi); i = np.argmax(np.where(w, y, -1)); return th[i]*1e3, y[i]
tbv = theta_B((0,0,8)); V0leg = 14.12
print("Si(001) (008), legacy parameters (5-term f_e, B=0.4632, mu=0.07, a=5.43102):")
print("  vacuum Bragg %.3f mrad ; refraction-corrected ext (V0=14.12 V of these f_e) %.3f mrad" % (tbv*1e3, theta_ext_refr(tbv, V0leg)*1e3))
for name, y in [("SHIPPED |R_000|^2", L0), ("SHIPPED |sum_rod R|^2", Ls), ("corrected Bloch (U0,gamma,all rod g)", abs(P)**2), ("exact 1-D truncated bulk", abs(E)**2)]:
    p1 = pk(y, 15.0, 17.5); p2 = pk(y, 17.5, 19.5)
    print("  %-38s max in [15,17.5]: %.2f mrad (%.4f) ; max in [17.5,19.5]: %.2f mrad (%.4f) ; min/max over scan %.3g / %.3g" % (name, p1[0], p1[1], p2[0], p2[1], y.min(), y.max()))
