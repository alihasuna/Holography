# Provenance checks for the prismatique/embeam API (from report D)

These scripts were written by the software-provenance audit (docs/agent_reports/D_software_provenance.md,
section 0, commands 14-17). They exercise, without running any simulation, the exact API calls made by
`si110-reflection-holography/pipeline/multislice_forward_model.py` and
`multislice_tilt_series_runner.py` against an installed `prismatique` + `embeam`, and they demonstrate:

* `check_api.py`  - every repository call succeeds except `sample.ModelParams(absorbing_layers=...)`,
                    which raises `TypeError` (the repository swallows it, so the absorber is never applied).
* `tilt_test.py`  - the tilt "window" makes the engine simulate every FFT-grid tilt inside the window
                    (1309 tilts for the default 0-11 mrad sweep) and a 24 mrad tilt at the generator's
                    default 0.5 A pixel raises `IndexError` (anti-aliasing ceiling lambda/(4*dx)).
* `schema_test.py`- the HDF5 layout: `/data/image_wavefunctions` is 5-D (config, defocus, tilt, r_y, r_x),
                    complex64, image pixel = 2 x potential pixel, `r_y` descending.
* `nan_test.py`   - `tilt_weights` becomes `[nan]` unless the offset matches a grid tilt bit-for-bit,
                    so `hrtem_sim_intensity_output.h5` is all-NaN for the repository's snapped offsets.

`pyprismatic_stub.py` is a stand-in that only lets `import prismatique` succeed when the compiled
engine is absent; its `go()` raises, so nothing is ever simulated. The scripts insert their own
directory on `sys.path`; rename the stub to `pyprismatic.py` in that directory ONLY on a machine
without the real engine. On the laboratory machine with the real engine installed, do not copy the stub.

Environment used for the recorded results: `pip install prismatique==0.0.1 embeam==0.0.1` in a clean
venv (Python 3.11), which does NOT install `pyprismatic` (prismatique does not declare it).
