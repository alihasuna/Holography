import sys, math, numpy as np
import os, importlib.util
_HERE = os.path.dirname(os.path.abspath(__file__))
# Guard against a renamed stub (pyprismatic.py in this directory) shadowing an installed engine:
# look for the engine with this directory (and the implicit script directory) removed from sys.path.
_local_stub = os.path.exists(os.path.join(_HERE, "pyprismatic.py"))
_saved_path = list(sys.path)
sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != _HERE]
_engine_elsewhere = importlib.util.find_spec("pyprismatic") is not None
sys.path[:] = _saved_path
assert not (_local_stub and _engine_elsewhere), (
    "pyprismatic.py stub in " + _HERE + " would shadow the installed engine; delete the stub")
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import prismatique, embeam
from prismatique.hrtem import sim as HS
XYZ = os.path.join(_HERE, "slab.xyz")
E = 200.0
disc = prismatique.discretization.Params(sample_supercell_reduced_xy_dims_in_pixels=(200,150),
        num_slices=198, z_supersampling=4, interpolation_factors=(1,1))
sm  = prismatique.sample.ModelParams(atomic_coords_filename=XYZ, unit_cell_tiling=(1,1,1),
        discretization_params=disc, atomic_potential_extent=8.0)
gun = embeam.gun.ModelParams(mean_beam_energy=E, intrinsic_energy_spread=0.5e-3)
lens= embeam.lens.ModelParams(coherent_aberrations=(), chromatic_aberration_coef=0.0)

print("### A) azimuth 35.26 deg, single 23.997 mrad tilt (repo cleave-edge case) ###")
for az in (0.0, 35.264):
    lam = 12.2643/math.sqrt(E*1e3*(1+E*1e3*0.978476e-6))
    Lx = prismatique.sample._supercell_dims(sm)[0]
    dth = lam/Lx*1000.0
    snapped = round(23.997/dth)*dth
    ox, oy = snapped*math.cos(math.radians(az)), snapped*math.sin(math.radians(az))
    tp = prismatique.tilt.Params(offset=[ox,oy], window=[0.0, 0.1], spread=0.0)
    try:
        ts = np.array(prismatique.tilt._series(sm, E, tp))
        print(f"  az={az:7.3f} deg  offset=({ox:8.4f},{oy:8.4f}) mrad -> {len(ts)} tilt(s); first={ts[0]}")
    except Exception as e:
        print(f"  az={az:7.3f} deg  offset=({ox:8.4f},{oy:8.4f}) mrad -> {type(e).__name__}: {e}")

print("\n### B) full sim_params -> exact HDF5 schema that would be written ###")
tp  = prismatique.tilt.Params(offset=[23.9628,0.0], window=[0.0,0.1], spread=0.0)
sysp= prismatique.hrtem.system.ModelParams(sample_specification=sm, gun_model_params=gun,
        lens_model_params=lens, tilt_params=tp)
imgp= prismatique.hrtem.image.Params(postprocessing_seq=(), avg_num_electrons_per_postprocessed_image=1.0,
        apply_shot_noise=False, save_wavefunctions=True, save_final_intensity=True)
outp= prismatique.hrtem.output.Params(output_dirname="/tmp/o", image_params=imgp,
        max_data_size=8_000_000_000, save_potential_slices=False)
sp  = prismatique.hrtem.sim.Params(hrtem_system_model_params=sysp, output_params=outp)

Nx,Ny = prismatique.sample._supercell_xy_dims_in_pixels(sm)
dx,dy = prismatique.sample._supercell_lateral_pixel_size(sm)
rx = HS._r_x(sp, for_postprocessed_image=False); ry = HS._r_y(sp, for_postprocessed_image=False)
tilts = HS._tilt_series(sp); defocii = HS._defocii(sp)
nsub  = prismatique.sample._num_frozen_phonon_config_subsets(sm)
ncfg  = prismatique.sample._num_frozen_phonon_configs_in_subset(sm, 0)
tot   = prismatique.sample._total_num_frozen_phonon_configs(sm)
print(f"  potential grid N_x,N_y = ({Nx},{Ny}); dx,dy = {dx:.5f},{dy:.5f} A")
print(f"  image_wavefunctions shape = ({ncfg}, {len(defocii)}, {len(tilts)}, {len(ry)}, {len(rx)})  dtype=complex64")
print(f"    dim1 'atomic config idx'  size {ncfg}   (num subsets={nsub}, total FP configs={tot})")
print(f"    dim2 'defocus idx'        size {len(defocii)}  defocii={defocii} A")
print(f"    dim3 'tilt idx'           size {len(tilts)}  tilts={np.array(tilts)} mrad")
print(f"    dim4 'r_y idx'            size {len(ry)}   r_y[0]={ry[0]:.4f}  r_y[1]={ry[1]:.4f}  r_y[-1]={ry[-1]:.4f} A  (step {ry[1]-ry[0]:+.5f})")
print(f"    dim5 'r_x idx'            size {len(rx)}   r_x[0]={rx[0]:.4f}  r_x[1]={rx[1]:.4f}  r_x[-1]={rx[-1]:.4f} A  (step {rx[1]-rx[0]:+.5f})")
print(f"  => HRTEM image pixel = ({rx[1]-rx[0]:.5f}, {abs(ry[1]-ry[0]):.5f}) A  == 2*(dx,dy) = ({2*dx:.5f},{2*dy:.5f}) : {np.isclose(rx[1]-rx[0],2*dx)}")
print(f"  intensity file r_x size (postprocessed) = {len(HS._r_x(sp, True))}")
print(f"  objective aperture window used = {sysp.get_core_attrs()['objective_aperture_params'].get_core_attrs()}")
print(f"  tilt weights (used to COLLAPSE the tilt axis in the intensity file) = {HS._tilt_weights(sp)}")
print(f"  wavefunction output filenames = {HS._wavefunction_output_filenames(sp)}")
print(f"  intensity output filename     = {HS._intensity_output_filename(sp)}")
try:
    HS._check_data_size(sp); print("  _check_data_size: OK (within max_data_size)")
except Exception as e: print("  _check_data_size:", type(e).__name__, e)
