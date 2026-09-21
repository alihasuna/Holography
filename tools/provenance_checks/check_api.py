import sys, json, traceback
import os, importlib.util
_HERE = os.path.dirname(os.path.abspath(__file__))
if importlib.util.find_spec("pyprismatic") is None:
    sys.path.insert(0, _HERE)  # only then may a local pyprismatic.py (renamed stub) be picked up; it never shadows a real engine

import prismatique, embeam, prismatique.version, embeam.version
print("prismatique", prismatique.__version__, "| embeam", embeam.version.__version__)
res = {}
def T(name, fn):
    try:
        v = fn(); res[name] = ("OK", repr(v)[:160]); print(f"[OK]   {name}")
    except Exception as e:
        res[name] = ("FAIL", f"{type(e).__name__}: {e}"); print(f"[FAIL] {name}: {type(e).__name__}: {str(e)[:300]}")

# --- exactly the repo's calls (multislice_forward_model.py / multislice_tilt_series_runner.py) ---
T("sample.ModelParams(absorbing_layers=...)  [repo L269-276]",
  lambda: prismatique.sample.ModelParams(atomic_coords_filename="x.xyz", unit_cell_tiling=(1,1,1),
        atomic_potential_extent=8.0,
        absorbing_layers=[{"zmin_A":0.0,"zmax_A":1.0,"eta":0.5}]))
T("sample.ModelParams(no absorber, no disc)  [repo fallback]",
  lambda: prismatique.sample.ModelParams(atomic_coords_filename="x.xyz", unit_cell_tiling=(1,1,1),
        atomic_potential_extent=8.0))
T("embeam.gun.ModelParams(mean_beam_energy, intrinsic_energy_spread)  [repo L284]",
  lambda: embeam.gun.ModelParams(mean_beam_energy=200.0, intrinsic_energy_spread=0.5e-3))
T("embeam.lens.ModelParams(coherent_aberrations=(), chromatic_aberration_coef=0.0)  [repo L291]",
  lambda: embeam.lens.ModelParams(coherent_aberrations=(), chromatic_aberration_coef=0.0))
T("discretization.Params(reduced_dims,num_slices,z_supersampling,interpolation_factors)  [repo L417]",
  lambda: prismatique.discretization.Params(sample_supercell_reduced_xy_dims_in_pixels=(64,64),
        num_slices=100, z_supersampling=4, interpolation_factors=(1,1)))
T("hrtem.image.Params(postprocessing_seq,avg_num_electrons...,apply_shot_noise,save_wavefunctions,save_final_intensity)  [repo L428]",
  lambda: prismatique.hrtem.image.Params(postprocessing_seq=(), avg_num_electrons_per_postprocessed_image=1.0,
        apply_shot_noise=False, save_wavefunctions=True, save_final_intensity=True))
T("hrtem.output.Params(output_dirname,image_params,max_data_size,save_potential_slices)  [repo L306-322]",
  lambda: prismatique.hrtem.output.Params(output_dirname="/tmp/o",
        image_params=prismatique.hrtem.image.Params(), max_data_size=8_000_000_000, save_potential_slices=False))
T("worker.cpu.Params(enable_workers,num_worker_threads,batch_size)  [repo L357]",
  lambda: prismatique.worker.cpu.Params(enable_workers=True, num_worker_threads=4, batch_size=1))
T("worker.gpu.Params(num_gpus,batch_size,data_transfer_mode='auto',num_streams_per_gpu)  [repo L365]",
  lambda: prismatique.worker.gpu.Params(num_gpus=0, batch_size=1, data_transfer_mode="auto", num_streams_per_gpu=1))
T("tilt.Params(offset=(24.0,0.0), window=(0.0,0.1))  [repo runner L402]",
  lambda: prismatique.tilt.Params(offset=(24.0,0.0), window=(0.0,0.1)))
T("prismatique.sample.check_atomic_coords_file_format exists  [repo L257]",
  lambda: prismatique.sample.check_atomic_coords_file_format)

# constructor signatures
import inspect
print("\n--- ctor param names (0.0.1) ---")
for cls in [prismatique.sample.ModelParams, prismatique.discretization.Params, prismatique.thermal.Params,
            prismatique.tilt.Params, prismatique.aperture.Params, prismatique.hrtem.image.Params,
            prismatique.hrtem.output.Params, prismatique.hrtem.system.ModelParams, prismatique.hrtem.sim.Params,
            prismatique.worker.cpu.Params, prismatique.worker.gpu.Params, prismatique.worker.Params,
            embeam.gun.ModelParams, embeam.lens.ModelParams]:
    try:
        sig = inspect.signature(cls.__init__)
        names = [p for p in sig.parameters if p != "self"]
        print(f"{cls.__module__}.{cls.__qualname__}: {names}")
    except Exception as e:
        print(f"{cls}: ERR {e}")

print("\n--- defaults actually taken by the repo (unset params) ---")
tp = prismatique.thermal.Params(); print("thermal.Params defaults:", tp.get_core_attrs())
ap = prismatique.aperture.Params(); print("aperture.Params defaults:", ap.get_core_attrs())
sm = prismatique.sample.ModelParams(atomic_coords_filename="x.xyz", unit_cell_tiling=(1,1,1), atomic_potential_extent=8.0)
print("sample.ModelParams core_attrs keys:", list(sm.get_core_attrs().keys()))
print("  thermal_params ->", sm.get_core_attrs()["thermal_params"].get_core_attrs())
lm = embeam.lens.ModelParams(coherent_aberrations=(), chromatic_aberration_coef=0.0)
print("lens.ModelParams core_attrs:", lm.get_core_attrs())
gm = embeam.gun.ModelParams(mean_beam_energy=200.0, intrinsic_energy_spread=0.5e-3)
print("gun.ModelParams core_attrs:", gm.get_core_attrs())
pm = embeam.stem.probe.ModelParams(lens_model_params=lm, gun_model_params=gm, defocal_offset_supersampling=9)
print("probe is_coherent:", pm.is_coherent)
print("embeam.wavelength(200 keV) =", embeam.wavelength(200.0), "Angstrom")
json.dump(res, open(os.path.join(_HERE, "result.json"), "w"), indent=1)
