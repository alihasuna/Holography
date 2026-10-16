"""Quick dynamical simulation of one single-layer (a/4) step on Si(001), edge transverse to the beam.

First pass at R3/R5 (orchestrator, 2026-10-16). Labels: DERIVED_HERE (method), ASSUMPTION (geometry and
numerical choices listed below). Not a validated rung: no convergence study of the step result yet.

Geometry: beam azimuth [110] along x, Si(001) bulk-terminated, 200 keV, W = 0 (absorption MISSING),
glancing angle 16.25 mrad (many-beam (008) peak, R2 result). Down-step of one atomic layer (a/4) at
x_step: lower terrace = same continuous lattice with the top layer removed (stacking-correct by
construction). Two runs: flat and stepped, identical otherwise. The incident band illuminates the surface
from x ~ gap/theta to x_end; the cell continues to L so that re-emitted (channelled) flux is captured.
Output: exit waves (y-averaged, G_y = 0 rod) of both runs and run metadata -> step_quick.npz
"""
import json, sys, time, pathlib
import numpy as np
import scipy.fft as sfft

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from reflection_holo.geometry import Surface
from reflection_holo.constants import wavelength, interaction_constant, A_SI
from reflection_holo.multislice import cell as CL, reflectivity as RF
from reflection_holo.multislice.potential import projected_potential, transmission_function
from reflection_holo.multislice.illumination import incident_wave, plateau_amplitude, z_axis
from reflection_holo.multislice.propagate import fresnel_propagator, bandlimit, flux

E = 200e3; TH = 16.25e-3
X_STEP = 15000.0          # A (1.5 um)        ASSUMPTION
X_END = 40000.0           # A, end of illuminated strip   ASSUMPTION
L = 50000.0               # A, cell length (>= X_END + ~1 um re-emission)   ASSUMPTION
GAP, SOFT = 3.0, 3.0
WORKERS = 16
import os
N_LAYERS = int(os.environ.get("N_LAYERS", "1"))   # atomic layers removed (1: a/4 screw-related; 2: a/2 lattice translation)
OUT_NAME = os.environ.get("OUT_NAME", "step_quick.npz")
FLAT_FROM = os.environ.get("FLAT_FROM", "")
SAVE_FULL = os.environ.get("SAVE_FULL", "") == "1"   # also save full 2D exit wave, cell atoms and grid        # reuse prof_flat from an earlier npz (identical flat run)

surf = Surface((0, 0, 1), (1, 1, 0)); lam = wavelength(E); sig = interaction_constant(E)
Hw = TH * X_END - GAP
vac = TH * L + 80.0
cell = CL.flat_surface_cell(surf, E, TH, thetas_for_vacuum=np.array([TH]), absorption=False,
                            vacuum=vac, length_x=min(L, 3e4), **CL.SAMPLING_QUANT)
g = cell.grid; zs = cell.z_surface; a = A_SI.value; px = cell.meta["periods"][0]
n_per = int(np.ceil(L / px)); p_step = int(round(X_STEP / px))

upper = RF.period_transmissions(cell, E, True, False)[0]          # list of n_sub transmissions
ab = RF._absorber_slice(cell, RF.ABSORBER_STRENGTH_V)
lower, removed = [], []
for at, Z in zip(cell.atoms_per_slice, cell.Z_per_slice):
    keep = at[:, 1] < zs - (N_LAYERS - 0.5) * a / 4.0                # drop the top N_LAYERS atomic layers (a/4 spacing)
    removed.append(int((~keep).sum()))
    V = projected_potential(at[keep], Z[keep], g, cell.meta["dw_B"], cell.dx, absorption=False) + ab
    lower.append(bandlimit(transmission_function(V, sig), g, CL.BANDWIDTH))

P = fresnel_propagator(g, cell.dx, lam, bandwidth=CL.BANDWIDTH)
psi0 = incident_wave(g, TH, lam, zs, (zs + GAP, zs + GAP + Hw), SOFT)
psi0 = bandlimit(psi0, g, CL.BANDWIDTH); psi0 = psi0 / np.sqrt(flux(psi0, g))
a_inc = plateau_amplitude(psi0, g, (zs + GAP, zs + GAP + Hw))


def run(step: bool):
    psi = psi0.astype(np.complex128).copy(); t0 = time.time()
    for p in range(n_per):
        ts = lower if (step and p >= p_step) else upper
        for t in ts:
            psi = sfft.ifft2(P * sfft.fft2(t * psi, workers=WORKERS), workers=WORKERS)
        if p % 2000 == 0:
            print(f"  {'step' if step else 'flat'} period {p}/{n_per}  {time.time()-t0:.0f}s", flush=True)
    return psi


print(f"grid ny={g.ny} nz={g.nz} dy={g.dy:.4f} dz={g.dz}; dx={cell.dx:.3f}; periods={n_per} (slices {n_per*len(upper)});"
      f" Hw={Hw:.0f} A; vacuum={vac:.0f} A; removed top-layer atoms per slice {removed}", flush=True)
t0 = time.time()
if FLAT_FROM:
    prev = np.load(pathlib.Path(__file__).resolve().parents[1] / "outputs" / FLAT_FROM)
    prof_flat_reuse = prev["prof_flat"]; ew_flat = None; t1 = 0.0
else:
    ew_flat = run(False); t1 = time.time() - t0
ew_step = run(True); t2 = time.time() - t0 - t1
print(f"flat run {t1:.0f}s, step run {t2:.0f}s; flux out/in step {flux(ew_step,g):.4f}", flush=True)
np.savez(pathlib.Path(__file__).resolve().parents[1] / "outputs" / OUT_NAME,
         z=z_axis(g), zs=zs, prof_flat=(prof_flat_reuse if FLAT_FROM else ew_flat.mean(axis=1)), prof_step=ew_step.mean(axis=1), prof_in=psi0.mean(axis=1),
         a_inc=a_inc, theta=TH, E=E, lam=lam, L=n_per * px, x_step=p_step * px, x_end=X_END, Hw=Hw, gap=GAP,
         dz=g.dz, step_height=N_LAYERS * a / 4, meta=json.dumps({"ny": g.ny, "nz": g.nz, "dy": g.dy, "dx": cell.dx,
         "removed_per_slice": removed, "t_flat_s": t1, "t_step_s": t2}))
if SAVE_FULL:
    np.savez(pathlib.Path(__file__).resolve().parents[1] / "outputs" / OUT_NAME.replace(".npz", "_full.npz"),
             ew_step=ew_step.astype(np.complex64), psi0=psi0.astype(np.complex64), z=z_axis(g), zs=zs, dy=g.dy, dz=g.dz, ny=g.ny,
             upper_atoms=np.array(cell.atoms_per_slice, dtype=object), slice_dx=cell.dx, periods=np.array(cell.meta["periods"]),
             removed_layers=N_LAYERS, theta=TH, lam=lam, L=n_per * px, x_step=p_step * px, a=a, allow_pickle=True)
print("saved", OUT_NAME, flush=True)
