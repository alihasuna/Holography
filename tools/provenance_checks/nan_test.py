import sys, math, numpy as np
import os, importlib.util
_HERE = os.path.dirname(os.path.abspath(__file__))
if importlib.util.find_spec("pyprismatic") is None:
    sys.path.insert(0, _HERE)  # only then may a local pyprismatic.py (renamed stub) be picked up; it never shadows a real engine

import prismatique, embeam
from prismatique.hrtem import sim as HS
XYZ=os.path.join(_HERE, "slab.xyz")
E=200.0
lam_embeam = embeam.wavelength(E)
V=E*1e3; lam_repo = 12.2643/math.sqrt(V*(1.0+V*0.978476e-6))
print(f"embeam.wavelength(200) = {lam_embeam!r}")
print(f"repo runner formula    = {lam_repo!r}")
print(f"difference             = {lam_embeam-lam_repo:.3e} A  ({abs(lam_embeam-lam_repo)/lam_embeam*100:.4f} %)")
disc=prismatique.discretization.Params(sample_supercell_reduced_xy_dims_in_pixels=(200,150),
      num_slices=198,z_supersampling=4,interpolation_factors=(1,1))
sm=prismatique.sample.ModelParams(atomic_coords_filename=XYZ,unit_cell_tiling=(1,1,1),
      discretization_params=disc,atomic_potential_extent=8.0)
gun=embeam.gun.ModelParams(mean_beam_energy=E,intrinsic_energy_spread=0.5e-3)
lens=embeam.lens.ModelParams(coherent_aberrations=(),chromatic_aberration_coef=0.0)
imgp=prismatique.hrtem.image.Params(postprocessing_seq=(),avg_num_electrons_per_postprocessed_image=1.0,
      apply_shot_noise=False,save_wavefunctions=True,save_final_intensity=True)
outp=prismatique.hrtem.output.Params(output_dirname="/tmp/o",image_params=imgp,max_data_size=8_000_000_000,
      save_potential_slices=False)
Lx=prismatique.sample._supercell_dims(sm)[0]
def weights(offset,window):
    tp=prismatique.tilt.Params(offset=list(offset),window=list(window),spread=0.0)
    sysp=prismatique.hrtem.system.ModelParams(sample_specification=sm,gun_model_params=gun,
          lens_model_params=lens,tilt_params=tp)
    sp=prismatique.hrtem.sim.Params(hrtem_system_model_params=sysp,output_params=outp)
    ts=np.array(HS._tilt_series(sp)); w=HS._tilt_weights(sp)
    return ts,w
import warnings; warnings.filterwarnings("ignore")
print("\n--- case 1: repo's own snapping (lam_repo), az=0, single tilt ---")
off=round(23.997/(lam_repo/Lx*1000))*(lam_repo/Lx*1000)
ts,w=weights((off,0.0),(0.0,0.1)); print(f"  offset={off!r}; grid tilt={ts[0]}; weights={w}  -> all-NaN? {np.all(np.isnan(w))}")
print("\n--- case 2: offset set EXACTLY to the grid tilt value ---")
ts,w=weights((float(ts[0][0]),float(ts[0][1])),(0.0,0.1)); print(f"  offset={ts[0]}; weights={w}  -> NaN? {np.any(np.isnan(w))}")
print("\n--- case 3: multi-tilt sweep 0..11 mrad, offset 5.5 (repo default) ---")
ts,w=weights((5.5,0.0),(0.0,5.6)); print(f"  n_tilts={len(ts)}; nonzero weights={int(np.nansum(w!=0))}; any NaN={np.any(np.isnan(w))}; sum={np.nansum(w)}")
print("\n--- case 4: zero tilt (forward-model script: no tilt_params at all -> default offset (0,0), window (0,0)) ---")
sysp=prismatique.hrtem.system.ModelParams(sample_specification=sm,gun_model_params=gun,lens_model_params=lens)
sp=prismatique.hrtem.sim.Params(hrtem_system_model_params=sysp,output_params=outp)
ts=np.array(HS._tilt_series(sp)); w=HS._tilt_weights(sp)
print(f"  default tilt_params -> offset={sysp.get_core_attrs()['tilt_params'].get_core_attrs()}")
print(f"  n_tilts={len(ts)}; tilts={ts}; weights={w}")
