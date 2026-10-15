"""Audit test 1: constants and structure factors of the legacy code vs independent values."""
import json, sys
import numpy as np
import simulation.constants as C
import simulation.structure_factors as SF
from simulation.calibration import relativistic_wavelength

h = 6.62607015e-34; c = 299792458.0; e = 1.602176634e-19; mec2 = 510998.95  # eV
me = mec2 * e / c**2
T = 200e3
lam = h * c / e * 1e10 / np.sqrt(T * (T + 2 * mec2))
gam = 1 + T / mec2
print(f"lambda(200 keV) independent = {lam:.7f} A ; legacy LAMBDA_200KV = {C.LAMBDA_200KV} ; rel diff = {C.LAMBDA_200KV/lam-1:.2e}")
print(f"calibration.relativistic_wavelength(200) = {relativistic_wavelength(200):.7f} A")
print(f"K = 2pi/lambda independent = {2*np.pi/lam:.4f} 1/A ; legacy K_200KV = {C.K_200KV:.4f}")
print(f"gamma independent = {gam:.6f} ; legacy RELATIVISTIC_GAMMA = {C.RELATIVISTIC_GAMMA:.6f}")
sigma = 2*np.pi/(lam*T)*(mec2+T)/(2*mec2+T)
print(f"sigma = {sigma:.5e} rad/(V A)")
FE2V = h**2/(2*np.pi*me*e)*1e20  # V A^2
print(f"h^2/(2 pi m0 e) = {FE2V:.4f} V A^2")
Om = C.SI_LATTICE_PARAM**3
print(f"a = {C.SI_LATTICE_PARAM} A, Omega = {Om:.3f} A^3")
# atom positions: diamond check
pos = C.SI_ATOM_POSITIONS
ref = np.vstack([[[0,0,0],[0,.5,.5],[.5,0,.5],[.5,.5,0]], np.array([[0,0,0],[0,.5,.5],[.5,0,.5],[.5,.5,0]])+0.25])
same = all(any(np.allclose(np.mod(p-q+1e-9,1)-1e-9,0,atol=1e-9) for q in ref) for p in pos)
print("atom positions equal the diamond basis (mod 1):", same)

# scattering factor parametrisations (s = sin(theta)/lambda = q/2 with q = 1/d)
legacy_a, legacy_b = C.SI_SCATTERING_A, C.SI_SCATTERING_B
dt4_a, dt4_b = legacy_a[:4], legacy_b[:4]
peng_high = np.array([[0.0567, 0.3365, 0.8104, 2.496, 2.1186],[0.0582, 0.6155, 3.2522, 16.7929, 57.6767]])
peng_low = np.array([[0.2519, 0.6372, 1.3795, 2.5082, 1.05],[0.3075, 2.0174, 9.6746, 29.3744, 80.4732]])
kirk = np.array([[1.06543892, 0.120143691, 0.180915263], [1.04118455, 68.7113368, 0.0887533926], [1.1206562, 0.0305452816, 1.59963502], [3.70062619, 0.214097897, 9.99096638]])
def f_gauss(s, a, b): return np.sum(a*np.exp(-b*np.asarray(s)[...,None]**2), -1)
def f_kirk(s, p):
    q2 = (2*np.asarray(s))**2
    return sum(p[0,i]/(p[1,i]+q2) + p[2,i]*np.exp(-p[3,i]*q2) for i in range(3))
print("\nf_e(s) [A]:   s     legacy5   DT4(legacy[:4])  Kirkland  Peng_low  Peng_high")
for s in [0, 0.1, 0.1595, 0.2, 0.319, 0.5, 0.6380, 1.0, 1.5, 2.0]:
    print(f"   {s:6.4f}  {f_gauss(s,legacy_a,legacy_b):8.4f}  {f_gauss(s,dt4_a,dt4_b):8.4f}  {f_kirk(s,kirk):8.4f}  {f_gauss(s,*peng_low):8.4f}  {f_gauss(s,*peng_high):8.4f}")

def V0(f0): return FE2V*8*f0/Om
print("\nMean inner potential V_000 = (h^2/2pi m0 e) 8 f(0)/Omega:")
for name, f0 in [("legacy 5-term", f_gauss(0,legacy_a,legacy_b)), ("Doyle-Turner 4-term (legacy[:4])", f_gauss(0,dt4_a,dt4_b)),
                 ("Kirkland (abTEM 1.0.6 json)", f_kirk(0,kirk)), ("Peng low (abTEM json)", f_gauss(0,*peng_low)), ("Peng high (abTEM json)", f_gauss(0,*peng_high))]:
    print(f"   {name:36s} f(0)={f0:.4f} A  V0={V0(f0):.3f} V")

# V_g in volts with DW B=0.4632, legacy formula vs Kirkland
B = C.SI_DEBYE_WALLER_B
print("\nV_g (volts, |V_g|, DW B=%.4f): legacy F_G via structure_factor() vs Kirkland f_e with same geometry and DW" % B)
print("   hkl       s      |V_g| legacy   |V_g| Kirkland   ratio   |U_g| code(1/A^2)  |U_g| correct=4 pi gamma F/Omega   ratio")
for hkl in [(1,1,1),(2,2,0),(0,0,4),(2,2,2),(3,3,3),(4,4,4),(6,6,6),(0,0,8),(5,5,5),(0,0,12),(1,-1,1),(4,-4,4)]:
    F = SF.structure_factor(*hkl)
    s = np.linalg.norm(hkl)/(2*C.SI_LATTICE_PARAM)
    geo = np.sum(np.exp(-2j*np.pi*pos@np.array(hkl,float)))
    Fk = f_kirk(s,kirk)*np.exp(-B*s**2)*geo
    Vg = FE2V*F/Om; Vk = FE2V*Fk/Om
    Ucode = SF.fourier_potential(*hkl)
    Ucorr = 4*np.pi*gam*F/Om
    print(f"   {str(hkl):11s} {s:.4f}  {abs(Vg):10.4f}   {abs(Vk):10.4f}   {abs(Vg)/max(abs(Vk),1e-30):6.3f}   {abs(Ucode):.5f}   {abs(Ucorr):.5f}   {abs(Ucorr)/max(abs(Ucode),1e-30):.4f}")
# theta_c from legacy V0 and from 12 V
for v0 in [12.0, V0(f_gauss(0,legacy_a,legacy_b)), V0(f_kirk(0,kirk))]:
    D = v0*(1+T/mec2)/(T*(1+T/(2*mec2)))
    print(f"V0={v0:.3f} V: Delta={D:.4e}, theta_c={np.sqrt(D)*1e3:.3f} mrad ; U0=4pi gamma 8f0/Omega route gives theta_c^2 = U0/K^2")
U0 = 4*np.pi*gam*8*f_gauss(0,legacy_a,legacy_b)/Om
print(f"U0 (legacy params, with gamma) = {U0:.5f} 1/A^2 ; sqrt(U0)/K = {np.sqrt(U0)/(2*np.pi/lam)*1e3:.3f} mrad")
