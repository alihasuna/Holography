import numpy as np, warnings
from harness import *
from patched import patched_R
warnings.simplefilter("ignore")
th = np.array([5, 6, 7, 8, 8.5, 10, 13.25, 18, 22, 26.5]) * 1e-3
for mm in [8, 12, 16, 24]:
    beams = rod_hkls("111", mm, allowed_only=False)
    ref = exact_1d_rocking(th, "111", mmax=mm, gamma=GAMMA, mu=0.07, include_U0=True)
    P = np.array([patched_R(t, beams, "111", 0.07)[0] for t in th])
    print("orders<=%2d (%2d beams): |dR|^2 per angle:" % (mm, len(beams)), " ".join("%.1e" % x for x in abs(abs(P)**2-abs(ref)**2)),
          "| dphase:", " ".join("%.2f" % x for x in np.abs(np.angle(P/ref))))
