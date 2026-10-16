"""Cross-check 1: this kernel run under the conditions of the repository engine's rocking curve.

Reproduces scripts/rocking_flat.py (repository root) setup for Si(001) (008), 200 keV, 31 offsets:
sheet beam centred XC = 22 A above the surface, full height H = 20 A, cosine edges 4 A, cell length
2 XC / tan(theta), imaginary potential 5 % of the real one, vacuum mask z > 8 A with a 3 A ramp,
circular aperture 0.06 /A around the specular direction. Reference: docs/figures/data/rocking_001_008.json.
Recovered verbatim from the executed session kernel cell that produced outputs/crosscheck_their_conditions.npz
(only the imports, paths and the np.savez line were added). Runtime about 8 min on 16 CPU threads.
Result (session): shape correlation 0.9994, same peak (+0.8 mrad), R_mine/R_theirs 0.88-0.95.
"""
import sys, json, time, pathlib
import numpy as np
import scipy.fft as sfft
HERE = pathlib.Path(__file__).resolve().parents[1]; ROOT = HERE.parent
sys.path.insert(0, str(HERE))                       # this folder's reflection_holo (not the repository engine)
from reflection_holo.geometry import Surface
from reflection_holo.multislice import reflectivity as RF, cell as CL
from reflection_holo.multislice.potential import transmission_function
from reflection_holo.multislice.illumination import incident_wave, z_axis
from reflection_holo.multislice.propagate import fresnel_propagator, bandlimit, flux
from reflection_holo.constants import wavelength, interaction_constant
EE = json.load(open(ROOT / "docs/figures/data/rocking_001_008.json"))
thB = EE["theta_ext_bragg_mrad_V0potential"] * 1e-3; offs = np.array(EE["offsets_mrad"]); R_theirs = np.array(EE["R"])
E = 200e3; surf = Surface((0, 0, 1), (1, 1, 0)); lam = wavelength(E); sig = interaction_constant(E); K = 2 * np.pi / lam
XC, H, EDGE, QAP, ABSR = 22.0, 20.0, 4.0, 0.06, 0.05
def their_conditions(th, absr=ABSR, sampling=CL.SAMPLING_QUANT):
    Lc=2*XC/np.tan(th)
    c=CL.flat_surface_cell(surf,E,th,thetas_for_vacuum=np.array([th]),absorption=False,**sampling)
    g=c.grid; zs=c.z_surface
    tr=RF.period_transmissions(c,E,False,False)[0]
    ab=RF._absorber_slice(c,RF.ABSORBER_STRENGTH_V)
    T=[bandlimit(transmission_function((np.log(t)/(1j*sig))*(1+1j*absr)+ab,sig),g,CL.BANDWIDTH) for t in tr]
    P=fresnel_propagator(g,c.dx,lam,bandwidth=CL.BANDWIDTH)
    psi0=bandlimit(incident_wave(g,th,lam,zs,(zs+XC-H/2,zs+XC+H/2),EDGE),g,CL.BANDWIDTH)
    n=int(np.ceil(Lc/c.dx)); psi=psi0.copy()
    for j in range(n):
        psi=sfft.ifft2(P*sfft.fft2(T[j%len(T)]*psi,workers=16),workers=16)
    z=z_axis(g); w=np.clip((z-(zs+8.0))/3.0,0,1)[:,None]
    F=np.fft.fft2(psi*w); qz=np.fft.fftfreq(g.nz,g.dz)[:,None]; qy=np.fft.fftfreq(g.ny,g.dy)[None,:]
    sel=np.hypot(qz-np.sin(th)/lam,qy)<QAP
    return np.sum(np.abs(F[sel])**2)/np.sum(np.abs(np.fft.fft2(psi0))**2), Lc
t0=time.time(); R_mine=np.array([their_conditions(thB+o*1e-3)[0] for o in offs])
print(f"{time.time()-t0:.0f} s for {len(offs)} angles")
print(f"theirs: R_peak {R_theirs.max():.4f} at {offs[R_theirs.argmax()]:+.1f} mrad, R(0) {R_theirs[np.argmin(abs(offs))]:.4f}")
print(f"mine  : R_peak {R_mine.max():.4f} at {offs[R_mine.argmax()]:+.1f} mrad, R(0) {R_mine[np.argmin(abs(offs))]:.4f}")
print("shape correlation:",round(np.corrcoef(R_mine,R_theirs)[0,1],4))
for o,a,b in zip(offs[::3],R_theirs[::3],R_mine[::3]): print(f"  {o:+.1f} mrad  theirs {a:.4f}  mine {b:.4f}  ratio {b/a:.2f}")
np.savez(HERE / "outputs" / "crosscheck_their_conditions.npz",offsets_mrad=offs,R_theirs=R_theirs,R_mine=R_mine,theta_B=thB)
print("saved outputs/crosscheck_their_conditions.npz")
