# Running the multislice on the Arbutus GPU VM

Status: 2026-09-30. For a persistent Arbutus (Alliance cloud) VM with a 12 GB NVIDIA GPU where
you are the administrator. The cupy backend has NOT been executed yet: the development
environment has no GPU. `tests/test_multislice.py::test_cupy_backend_matches_numpy` is the gate.
Run it first on the VM.

## 0. What needs the GPU and how much

| Run | Grid | Slices per run | Runs | Memory (GPU) | Expected time |
|---|---|---|---|---|---|
| `buried_dislocation_cpu.yaml` | 1024 x 512 | 1733 | 2 (flat + defect) | < 0.3 GB | about 65 s on 4 CPU cores (measured); seconds on a GPU |
| `buried_dislocation_gpu.yaml` | 2048 x 2048 | about 1730 | 10 (5 angles x 2) | < 1 GB | minutes (estimate, not measured) |

12 GB leaves room for grids up to about 8192 x 8192 in complex64. That is enough for the
production cells of docs/05 section 4.3: 0.13 A over 200 x 80 A, thousands of slices, and a
cell length of 0.1 to 0.4 um along the beam.

## 1. GPU driver (once, as admin)

```bash
nvidia-smi          # must list the GPU and a driver version
```

If `nvidia-smi` fails, the VM needs the NVIDIA **vGPU guest driver**. Arbutus GPU flavours are
virtual GPUs, and the stock NVIDIA or distribution driver does not work with them. Follow the
Alliance page "Using cloud vGPUs" (docs.alliancecan.ca/wiki/Using_cloud_vGPUs), which gives the
repository and package names for the guest driver. That page could not be read from the
development environment because it is bot-protected, so its commands are not reproduced here.
After a kernel update, re-check `nvidia-smi`, because the driver module must match the running kernel.

## 2. Environment (once)

```bash
sudo dnf install -y git python3.11 tmux        # AlmaLinux/Rocky; on Ubuntu: sudo apt install git python3-venv tmux
git clone https://github.com/alihasuna/Holography.git && cd Holography
git checkout trixode-studios-claude/ecstatic-euler-a2b4y1   # until merged
python3.11 -m venv venv
venv/bin/pip install -U pip
venv/bin/pip install numpy scipy matplotlib pytest pyyaml
nvidia-smi | head -4        # read "CUDA Version: 12.x" (or 11.x) in the header
venv/bin/pip install cupy-cuda12x                           # use cupy-cuda11x for a CUDA 11 driver
venv/bin/python -c "import cupy as cp; print(cp.cuda.runtime.getDeviceProperties(0)['name'], cp.ones(3).sum())"
```

The `cupy-cuda12x` wheel ships its own CUDA runtime libraries, so you do not need a CUDA toolkit.
The driver only has to be new enough for CUDA 12.

## 3. Run (persistent: inside tmux so it survives disconnects)

```bash
tmux new -s holo
bash scripts/run_gpu_smoke.sh          # tests -> geometry mode -> multislice (CPU config) -> multislice (GPU config)
# detach: Ctrl-b d      re-attach: tmux attach -t holo
```

Or run each step by hand:

```bash
venv/bin/python -m pytest -q -rs       # expect 41 passed, 0 skipped (the cupy test must RUN, not skip)
venv/bin/python scripts/run_buried_dislocation.py geometric  --config configs/smoke/buried_dislocation_gpu.yaml
venv/bin/python scripts/run_buried_dislocation.py multislice --config configs/smoke/buried_dislocation_gpu.yaml --backend cupy
```

Outputs: `outputs/<config name>/<mode>/` holds `manifest.json` (versions, GPU name, CUDA runtime,
config hash, repository commit, every parameter with its evidence label), `*.npz` (profiles and
complex waves on the declared exit plane) and `*.png`. `outputs/` is git-ignored. Copy results
back with `scp -r` or commit a summary, not the arrays.

## 4. Acceptance checks for the GPU run

1. The cupy-vs-numpy test passes.
2. The CPU-sized config run with `--backend cupy` reproduces the numpy numbers in
   `docs/08_buried_defects.md` section 5: R_flat 0.1925, multislice phase peak-to-peak 12.54 rad,
   and RMS residual 0.24 rad against the geometric model at Lambda = 3 A. The tolerance is 1e-3
   relative, allowing for float32 FFT differences.
3. In the GPU config's rocking scan, the flat-surface specular intensity peaks near offset 0. If
   it does not, the refraction or potential bookkeeping is wrong; report it and do not tune the offset.
4. `manifest.json` records `backend: cupy` and the GPU name.

## 5. Useful knobs

* `OMP_NUM_THREADS` only affects the numpy backend. It is recorded in the manifest.
* To scan depth or penetration, copy a config, change `depth_A` or `penetration_A`, and change
  `name`. The output folder is named after it, so runs never overwrite each other.
* Never change a SMOKE_TEST value into a physics claim. Values labelled PROJECT_INPUT or
  ASSUMPTION must come from the laboratory (docs/06).
