import numpy as np
from harness import *
b, co = rod_potential_coeffs("111", 24, mu=0.0)
print("Si(111) rod: b = %.5f 1/A, d = %.5f A, #coeffs=%d, U0=%.5f" % (b, 2*np.pi/b, len(co), co[0].real))
# 1. Fresnel step only
kap = K_TRUE*np.sin(10e-3)
R, w = exact_1d_R(kap, b, {0: co[0]}, nsub=200)
ki = np.sqrt(kap**2 + co[0])
print("U0 only: R=%s  Fresnel=%s" % (R, (kap-ki)/(kap+ki)))
# 2. convergence in nsub
for ns in [500, 1000, 3000, 6000]:
    R, w = exact_1d_R(K_TRUE*np.sin(16e-3), b, co, nsub=ns)
    print("nsub=%5d R=%.6f%+.6fj |R|^2=%.6f" % (ns, R.real, R.imag, abs(R)**2))
# 3. convergence in mmax
for mm in [8, 16, 24, 32]:
    b2, co2 = rod_potential_coeffs("111", mm, mu=0.0)
    R, w = exact_1d_R(K_TRUE*np.sin(16e-3), b2, co2, nsub=3000)
    print("mmax=%2d R=%.6f%+.6fj |R|^2=%.6f" % (mm, R.real, R.imag, abs(R)**2))
# 4. no absorption: |R|<=1 over a scan
th = np.linspace(2e-3, 40e-3, 381)
Rs = exact_1d_rocking(th, "111", mmax=16, mu=0.0, nsub=1500)
print("no absorption: max|R|^2 = %.8f, min = %.3e, n(|R|^2>0.999)=%d" % (np.max(abs(Rs)**2), np.min(abs(Rs)**2), np.sum(abs(Rs)**2>0.999)))
np.save("ref111_mu0.npy", np.vstack([th, Rs]))
