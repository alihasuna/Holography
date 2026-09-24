"""Fit a Gaussian presampling MTF, MTF(w) = exp(-(w/w0)^2), to the digitised 200 keV Si Medipix3 SPM MTF
(Paton et al. 2021 Fig. 8(a), TH0 = 12.4 keV and 58.3 keV curves, which coincide). DERIVED_HERE."""
import numpy as np
w  = np.array([0.15,0.2,0.25,0.3,0.35,0.4,0.45,0.5,0.55,0.6,0.65,0.7,0.75,0.8,0.85])
navy = np.array([0.896,0.823,0.738,0.647,0.554,0.463,0.372,0.297,0.228,0.175,0.13,0.094,0.069,0.05,0.035])
red  = np.array([0.881,0.806,0.719,0.629,0.535,0.443,0.355,0.28,0.213,0.159,0.116,0.083,0.058,0.04,0.025])
m = 0.5*(navy+red)
# least squares on log for values > 0.03
sel = m > 0.03
w0 = np.sqrt(np.sum(w[sel]**4)/np.sum(-np.log(m[sel])*w[sel]**2))
print(f'w0 = {w0:.3f} omega_N  (omega_N = 0.5 cycles/pixel = 9.09 cycles/mm for 55 um pixels)')
print(f'q0 = {0.5*w0:.4f} cycles/pixel')
sigma_px = 1/(np.sqrt(2)*np.pi*0.5*w0)
print(f'equivalent Gaussian PSF sigma = {sigma_px:.3f} pixel = {55*sigma_px:.1f} um (MTF = exp(-2 pi^2 sigma^2 q^2))')
for wi, mi in zip(w, m):
    print(f'  w={wi:.2f}  digitised {mi:.3f}  gaussian {np.exp(-(wi/w0)**2):.3f}')
print('  w=1.00  Table 1: 0.01  gaussian', round(float(np.exp(-(1/w0)**2)),4))
# carrier sampling: pixels per fringe p -> w = 2/p (in omega_N units)
for p in (3,4,5,6,8,10,12):
    wi = 2.0/p
    mi = np.interp(wi, w, m) if wi <= 0.85 else float('nan')
    print(f'  {p:2d} px per fringe: w = {wi:.3f} omega_N, digitised MTF {mi:.3f}, gaussian {np.exp(-(wi/w0)**2):.3f}, ideal square pixel sinc {np.sinc(wi/2):.3f}')
