"""Shared helpers for the ElectroSim holography pipeline (parameters, physics constants, output, plots).

Runs in: em-abtem AND em-holography (numpy; PyYAML for .yaml parameter files; matplotlib optional).

Imported by every stage script in this folder. Nothing here touches raw/, gemicro.json or .gemicro/: the
output helper refuses those paths. Conventions follow docs/physics_conventions.md of alihasuna/Holography:
lengths in Å, angles in mrad, phases in rad, numpy FFT sign (a tilted plane wave exp(+2πi q0·r) appears at
+q0), arrays indexed [ix, iy] (axis 0 = x, as abTEM), wave convention exp(+i k·r).
"""

import hashlib
import json
import math
import os
import platform
import shutil
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

FORMAT = "electrosim-holo/1"

# ---------------------------------------------------------------------------------------------------------------
# Physics constants (CODATA 2018 / SI-2019 exact values), as in docs/physics_conventions.md.
# ---------------------------------------------------------------------------------------------------------------
M_E_C2_EV = 510998.95000  # electron rest energy (eV), CODATA 2018
HC_EV_A = 12398.419843320026  # h c in eV·Å (h, c, e exact in SI-2019)


def wavelength_A(energy_keV):
    """Relativistic electron wavelength λ = hc / sqrt(T (T + 2 m c²)) in Å (T kinetic energy in eV)."""
    T = float(energy_keV) * 1e3
    return HC_EV_A / math.sqrt(T * (T + 2.0 * M_E_C2_EV))


def interaction_constant(energy_keV):
    """σ in rad/(V·Å): σ = (2π / (λ V)) (m c² + eV) / (2 m c² + eV). 7.2884e-4 at 200 kV (abTEM: 7.28840e-4)."""
    V = float(energy_keV) * 1e3
    return 2.0 * math.pi / (wavelength_A(energy_keV) * V) * (M_E_C2_EV + V) / (2.0 * M_E_C2_EV + V)


# ---------------------------------------------------------------------------------------------------------------
# Parameters: one file per run, every setting explicit. A missing key is an error, an unused key is an error.
# ---------------------------------------------------------------------------------------------------------------
class ParamError(ValueError):
    """A parameter file is incomplete, has an unknown key, or a value is out of range."""


def load_params(path):
    """Read a YAML (.yaml/.yml) or JSON parameter file into a dict."""
    p = Path(path)
    if not p.is_file():
        raise ParamError(f"parameter file {p} does not exist")
    text = p.read_text()
    if p.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError as e:  # PyYAML comes with dask (em-abtem) and HyperSpy (em-holography)
            raise ParamError(f"{p}: PyYAML is not importable in this interpreter ({e}); use a .json file") from e
        data = yaml.safe_load(text)
    elif p.suffix.lower() == ".json":
        data = json.loads(text)
    else:
        raise ParamError(f"{p}: parameter files must be .yaml, .yml or .json")
    if not isinstance(data, dict):
        raise ParamError(f"{p}: the top level must be a mapping")
    return data


def _is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


class Section:
    """Strict view of a parameter mapping: `req` reads a key that must exist; `finish` fails on keys never read.

    Keys that only apply to another model (e.g. `curvature_rad` with `model: R1_plane`) are therefore reported
    instead of being silently ignored, and nothing falls back to a default that is not in the file."""

    def __init__(self, data, path="params"):
        if not isinstance(data, dict):
            raise ParamError(f"{path} must be a mapping, got {type(data).__name__}")
        self.data = data
        self.path = path
        self.used = set()
        self.children = []

    def req(self, key):
        if key not in self.data:
            raise ParamError(f"missing required parameter {self.path}.{key}")
        self.used.add(key)
        return self.data[key]

    def has(self, key):
        return key in self.data

    def sub(self, key):
        s = Section(self.req(key), f"{self.path}.{key}")
        self.children.append(s)
        return s

    def num(self, key, lo=None, hi=None, allow_none=False, lo_open=False):
        v = self.req(key)
        if v is None and allow_none:
            return None
        if not _is_number(v):
            raise ParamError(f"{self.path}.{key} must be a number, got {v!r}")
        v = float(v)
        if not math.isfinite(v):
            raise ParamError(f"{self.path}.{key} must be finite")
        if lo is not None and (v < lo or (lo_open and v == lo)):
            raise ParamError(f"{self.path}.{key} = {v} must be {'>' if lo_open else '>='} {lo}")
        if hi is not None and v > hi:
            raise ParamError(f"{self.path}.{key} = {v} must be <= {hi}")
        return v

    def integer(self, key, lo=None, hi=None, allow_none=False):
        v = self.req(key)
        if v is None and allow_none:
            return None
        if not isinstance(v, int) or isinstance(v, bool):
            raise ParamError(f"{self.path}.{key} must be an integer, got {v!r}")
        if lo is not None and v < lo:
            raise ParamError(f"{self.path}.{key} = {v} must be >= {lo}")
        if hi is not None and v > hi:
            raise ParamError(f"{self.path}.{key} = {v} must be <= {hi}")
        return v

    def boolean(self, key):
        v = self.req(key)
        if not isinstance(v, bool):
            raise ParamError(f"{self.path}.{key} must be true or false, got {v!r}")
        return v

    def choice(self, key, choices):
        v = self.req(key)
        if v not in choices:
            raise ParamError(f"{self.path}.{key} = {v!r} must be one of {list(choices)}")
        return v

    def vec(self, key, n=None, allow_none=False, integer=False):
        v = self.req(key)
        if v is None and allow_none:
            return None
        if not isinstance(v, (list, tuple)) or (n is not None and len(v) != n):
            raise ParamError(f"{self.path}.{key} must be a list of {n if n else 'some'} numbers, got {v!r}")
        for x in v:
            if integer and (not isinstance(x, int) or isinstance(x, bool)):
                raise ParamError(f"{self.path}.{key} must contain integers, got {v!r}")
            if not _is_number(x):
                raise ParamError(f"{self.path}.{key} must contain numbers, got {v!r}")
        return [int(x) for x in v] if integer else [float(x) for x in v]

    def unused(self):
        out = [f"{self.path}.{k}" for k in self.data if k not in self.used]
        for c in self.children:
            out += c.unused()
        return out

    def finish(self):
        extra = self.unused()
        if extra:
            raise ParamError("parameters present but not used by this script (typo, or they belong to another "
                             "model/stage): " + ", ".join(extra))


# ---------------------------------------------------------------------------------------------------------------
# Output folder: written atomically, never through a link, never inside raw/ or .gemicro/ of a gemicro project.
# ---------------------------------------------------------------------------------------------------------------
def raw_roots(root):
    """Raw-data roots declared in the project's gemicro.json (`raw_roots`), resolved against the project root."""
    try:
        cfg = json.loads((Path(root) / "gemicro.json").read_text())
    except (OSError, ValueError):
        return []
    out = []
    for r in cfg.get("raw_roots") or []:
        q = Path(os.path.expanduser(str(r)))
        out.append((q if q.is_absolute() else Path(root) / q).resolve())
    return out


def find_project_root(start):
    """The nearest ancestor that holds gemicro.json (a gemicro project), or None."""
    p = Path(start).resolve()
    for d in [p] + list(p.parents):
        if (d / "gemicro.json").is_file():
            return d
    return None


def jsonable(o):
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, np.ndarray):
        return jsonable(o.tolist())
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        v = float(o)
        return v if math.isfinite(v) else None
    if isinstance(o, float):
        return o if math.isfinite(o) else None
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, complex):
        return [o.real, o.imag]
    if isinstance(o, Path):
        return str(o)
    return o


class Output:
    """Collects a stage's files in a staging folder inside the output folder and publishes them at the end.

    A run that fails leaves only `.staging-*` behind, never a half-written result that looks finished."""

    def __init__(self, path, overwrite=False):
        p = Path(path)
        if p.is_symlink():
            raise SystemExit(f"output {p} is a symbolic link; refusing to write through it")
        resolved = p.resolve()
        root = find_project_root(resolved.parent if not resolved.exists() else resolved)
        if root is not None:
            if resolved == root:
                raise SystemExit(f"output {p} is the project root; give a folder such as derived/<name>")
            rel = resolved.relative_to(root) if str(resolved).startswith(str(root)) else None
            if rel is not None and rel.parts and rel.parts[0] in ("raw", ".gemicro", "gemicro.json"):
                raise SystemExit(f"output {p} is inside {rel.parts[0]} of the gemicro project {root}; refusing")
            for rr in raw_roots(root):
                if resolved == rr or rr in resolved.parents:
                    raise SystemExit(f"output {p} is inside the raw-data root {rr} declared in gemicro.json")
        if p.exists() and not p.is_dir():
            raise SystemExit(f"output {p} exists and is not a folder")
        if p.exists():
            existing = [q for q in p.iterdir() if not q.name.startswith(".staging-")]
            if existing and not overwrite:
                raise SystemExit(f"output folder {p} is not empty ({len(existing)} entries); pass --overwrite to "
                                 f"replace its contents, or choose a new folder")
        self.created = not p.exists()
        p.mkdir(parents=True, exist_ok=True)
        self.final = p
        self.overwrite = overwrite
        self.staging = Path(tempfile.mkdtemp(prefix=".staging-", dir=p))
        self.arrays = {}
        self.files = []
        self.t0 = time.time()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        """On an error, remove the staging folder (and the output folder if this run created it and it is empty),
        so a failed run leaves nothing that looks like a result."""
        if exc_type is not None and self.staging.exists():
            shutil.rmtree(self.staging, ignore_errors=True)
            if self.created and self.final.is_dir() and not any(self.final.iterdir()):
                self.final.rmdir()
        return False

    def path(self, name):
        """Path for a file written by the caller (plots); recorded in the file list."""
        self.files.append(name)
        return self.staging / name

    def save_array(self, key, arr, *, units, axes, description, sampling_A=None, filename=None):
        arr = np.asarray(arr)
        if arr.dtype.kind == "c" and arr.dtype != np.complex64:
            arr = arr.astype(np.complex64)
        elif arr.dtype.kind == "f" and arr.dtype != np.float32:
            arr = arr.astype(np.float32)
        if len(axes) != arr.ndim:
            raise ValueError(f"{key}: {arr.ndim}-D array but axes {axes}")
        if arr.dtype.kind in "fc" and not np.all(np.isfinite(arr)):
            raise SystemExit(f"{key}: non-finite values; refusing to save (the inspected pipeline once wrote an "
                             f"all-NaN intensity file without noticing)")
        name = filename or f"{key}.npy"
        np.save(self.staging / name, arr)
        entry = {"file": name, "dtype": str(arr.dtype), "shape": list(arr.shape), "axes": list(axes),
                 "units": units, "description": description}
        if sampling_A is not None:
            entry["sampling_A"] = [float(s) for s in sampling_A]
        self.arrays[key] = entry
        self.files.append(name)
        return name

    def save_json(self, name, obj):
        (self.staging / name).write_text(json.dumps(jsonable(obj), indent=2) + "\n")
        self.files.append(name)
        return name

    def publish(self):
        if self.final.is_symlink():
            raise SystemExit(f"{self.final} became a symbolic link; refusing to publish")
        if self.overwrite:
            for q in self.final.iterdir():
                if q == self.staging or q.name.startswith(".staging-"):
                    continue
                if q.is_dir() and not q.is_symlink():
                    shutil.rmtree(q)
                else:
                    q.unlink()
        for q in self.staging.iterdir():
            os.replace(q, self.final / q.name)
        self.staging.rmdir()
        return self.final


def sha256_file(path, chunk=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _version(mod):
    m = sys.modules.get(mod)
    if m is None:
        return None
    return getattr(m, "__version__", "unknown")


def provenance(argv, params_path, inputs, seeds=None, extra=None):
    """What gemicro records anyway, kept next to the data so a copied folder still explains itself."""
    rec = {
        "argv": list(argv),
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "host": platform.node(),
        "user": os.environ.get("USER") or os.environ.get("LOGNAME"),
        "started_unix": time.time(),
        "params_file": str(params_path),
        "params_sha256": sha256_file(params_path),
        "inputs": {str(k): {"path": str(v), "sha256": sha256_file(v)} for k, v in inputs.items()
                   if v is not None and Path(v).is_file()},
        "files_read": {str(p): sha256_file(p) for p in FILES_READ if p.is_file()},
        "packages": {k: _version(k) for k in ("numpy", "scipy", "abtem", "ase", "cupy", "holospy", "hyperspy",
                                              "skimage", "matplotlib", "yaml") if _version(k)},
        "threads": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMBA_NUM_THREADS")},
        "seeds": seeds or {},
    }
    if extra:
        rec.update(extra)
    return rec


def write_sidecar(out, stage, params_data, prov, physics, summary, name=None):
    """The stage's JSON sidecar: every array with dtype, shape, axes, units and sampling, plus the physics."""
    doc = {"format": FORMAT, "stage": stage, "arrays": out.arrays, "physics": physics, "summary": summary,
           "params": params_data, "provenance": prov,
           "wall_time_s": round(time.time() - out.t0, 3),
           "conventions": "lengths Å, angles mrad, phases rad; arrays [ix, iy] (axis 0 = x); numpy FFT sign; "
                          "wave exp(+i k·r); see docs/physics_conventions.md"}
    return out.save_json(name or f"{stage}.json", doc)


# ---------------------------------------------------------------------------------------------------------------
# Reading a stage folder back, with assertions instead of guesses (audit A, C5/C6: never trust an advisory value).
# ---------------------------------------------------------------------------------------------------------------
FILES_READ = []  # every stage file read in this process (sidecars and arrays), hashed into the provenance


def _note_read(path):
    p = Path(path)
    if p not in FILES_READ:
        FILES_READ.append(p)


class Stage:
    def __init__(self, folder, stage):
        folder = Path(folder)
        if folder.is_file():  # a .npy or .json inside the stage folder
            folder = folder.parent
        side = folder / f"{stage}.json"
        if not side.is_file():
            raise SystemExit(f"{folder}: no {stage}.json sidecar (is this the output folder of the {stage} stage?)")
        self.folder = folder
        self.sidecar_path = side
        self.meta = json.loads(side.read_text())
        _note_read(side)
        if self.meta.get("format") != FORMAT or self.meta.get("stage") != stage:
            raise SystemExit(f"{side}: format {self.meta.get('format')!r} stage {self.meta.get('stage')!r}, "
                             f"expected {FORMAT!r} {stage!r}")

    def has(self, key):
        return key in self.meta["arrays"]

    def entry(self, key):
        try:
            return self.meta["arrays"][key]
        except KeyError:
            raise SystemExit(f"{self.sidecar_path}: no array {key!r} (has {sorted(self.meta['arrays'])})")

    def array(self, key):
        e = self.entry(key)
        a = np.load(self.folder / e["file"], allow_pickle=False)
        _note_read(self.folder / e["file"])
        if list(a.shape) != e["shape"] or str(a.dtype) != e["dtype"]:
            raise SystemExit(f"{self.folder / e['file']}: shape {a.shape} dtype {a.dtype} disagree with the sidecar "
                             f"({e['shape']} {e['dtype']})")
        return a

    def sampling(self, key):
        e = self.entry(key)
        if "sampling_A" not in e:
            raise SystemExit(f"{self.sidecar_path}: array {key!r} has no sampling_A")
        return tuple(e["sampling_A"])

    def files(self):
        return [self.folder / e["file"] for e in self.meta["arrays"].values()] + [self.sidecar_path]


# ---------------------------------------------------------------------------------------------------------------
# Arrays and Fourier helpers
# ---------------------------------------------------------------------------------------------------------------
def to_host(a):
    """A NumPy array on the host. abTEM with device=gpu returns CuPy arrays, which refuse implicit conversion
    ("Implicit conversion to a NumPy array is not allowed. Please use .get()"): copy explicitly."""
    get = getattr(a, "get", None)
    if callable(get) and not isinstance(a, (dict, np.ndarray)):
        a = get()
    return np.asarray(a)


def fft_freqs(shape, sampling):
    """Spatial-frequency grids (cycles/Å) for an [ix, iy] array, unshifted (numpy FFT layout)."""
    qx = np.fft.fftfreq(shape[0], sampling[0])[:, None]
    qy = np.fft.fftfreq(shape[1], sampling[1])[None, :]
    return np.broadcast_to(qx, shape), np.broadcast_to(qy, shape)


def pixel_centres(n, pixel_A, binning):
    """Positions (Å, simulation-box coordinates) of detector pixel centres: pixel K integrates the simulation
    samples k = K b ... K b + b - 1, which abTEM places at k Δ, so its centre is K p + (b - 1) Δ / 2."""
    return np.arange(n) * pixel_A + 0.5 * (binning - 1) * pixel_A / binning


def region_mask(shape, fractions):
    """Boolean mask of a box given as [x0, x1, y0, y1] fractions of the field (x along axis 0)."""
    x0, x1, y0, y1 = fractions
    if not (0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1):
        raise ParamError(f"region {fractions} must be [x0, x1, y0, y1] with 0 <= x0 < x1 <= 1, 0 <= y0 < y1 <= 1")
    m = np.zeros(shape, bool)
    nx, ny = shape
    m[int(round(x0 * nx)):int(round(x1 * nx)), int(round(y0 * ny)):int(round(y1 * ny))] = True
    if not m.any():
        raise ParamError(f"region {fractions} contains no pixel of a {shape} array")
    return m


# ---------------------------------------------------------------------------------------------------------------
# Plots (PNG). Missing matplotlib only skips the plot, never the data.
# ---------------------------------------------------------------------------------------------------------------
def _plt():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except ImportError as e:
        print(f"plots skipped: matplotlib not importable ({e})", file=sys.stderr)
        return None


def plot_map(out, name, img, title, sampling=None, label="", cmap="viridis", vlim=None, units="Å", overlay=None,
             robust=False):
    """robust: colour limits from the 0.5-99.5 percentiles (a few edge pixels must not set the scale)."""
    plt = _plt()
    if plt is None:
        return None
    img = np.asarray(img, dtype=np.float64)
    if robust and vlim is None and np.isfinite(img).any():
        vlim = tuple(np.nanpercentile(img, [0.5, 99.5]))
    fig, ax = plt.subplots(figsize=(5.8, 4.8))
    ext = None
    if sampling is not None:
        ext = [0, img.shape[0] * sampling[0], 0, img.shape[1] * sampling[1]]
    kw = {}
    if vlim is not None:
        kw = {"vmin": vlim[0], "vmax": vlim[1]}
    im = ax.imshow(img.T, origin="lower", cmap=cmap, extent=ext, interpolation="nearest", aspect="equal", **kw)
    if overlay is not None:
        overlay(ax)
    ax.set_title(title, fontsize=9)
    ax.set_xlabel(f"x ({units})" if sampling is not None else "x (px)")
    ax.set_ylabel(f"y ({units})" if sampling is not None else "y (px)")
    fig.colorbar(im, ax=ax, label=label)
    fig.tight_layout()
    fig.savefig(out.path(name), dpi=140)
    plt.close(fig)
    return name


def plot_lines(out, name, x, curves, title, xlabel, ylabel):
    plt = _plt()
    if plt is None:
        return None
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for lab, y, style in curves:
        ax.plot(x, y, style, label=lab, lw=1.2, ms=3)
    ax.set_title(title, fontsize=9)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(out.path(name), dpi=140)
    plt.close(fig)
    return name


def plot_spectrum(out, name, arr, sampling, title, circles=()):
    """log10 |FFT| (fftshifted) with circles [(qx, qy, r, colour)] in cycles/Å."""
    plt = _plt()
    if plt is None:
        return None
    F = np.fft.fftshift(np.abs(np.fft.fft2(arr)))
    nx, ny = arr.shape
    qxm, qym = 0.5 / sampling[0], 0.5 / sampling[1]
    fig, ax = plt.subplots(figsize=(5.6, 4.8))
    im = ax.imshow(np.log10(F + F.max() * 1e-9).T, origin="lower", cmap="inferno",
                   extent=[-qxm, qxm - 1 / (nx * sampling[0]), -qym, qym - 1 / (ny * sampling[1])], aspect="equal")
    t = np.linspace(0, 2 * np.pi, 200)
    for cx, cy, r, c in circles:
        ax.plot(cx + r * np.cos(t), cy + r * np.sin(t), color=c, lw=1)
    ax.set_title(title, fontsize=9)
    ax.set_xlabel("q_x (1/Å)")
    ax.set_ylabel("q_y (1/Å)")
    fig.colorbar(im, ax=ax, label="log10 |FFT|")
    fig.tight_layout()
    fig.savefig(out.path(name), dpi=140)
    plt.close(fig)
    return name


def print_summary(title, items, out_folder, files):
    print(f"== {title}")
    w = max((len(k) for k in items), default=0)
    for k, v in items.items():
        print(f"   {k:<{w}} : {v}")
    print(f"   wrote {len(files)} files to {out_folder}: {', '.join(sorted(set(files)))}")


def common_cli(description, inputs):
    """argparse with --params, --output, --overwrite and the stage's named inputs (all required)."""
    import argparse
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--params", required=True, help="YAML or JSON parameter file (every setting lives here)")
    for flag, helptext in inputs:
        ap.add_argument(flag, required=True, help=helptext)
    ap.add_argument("--output", required=True, help="output folder (created; must be empty unless --overwrite)")
    ap.add_argument("--overwrite", action="store_true", help="replace the contents of a non-empty output folder")
    return ap
