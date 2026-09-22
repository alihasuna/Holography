"""Exit-wave files: writer and assertion-based loader (.npz; the pixel sizes, axes, units and the
plane of the wave are READ from the file and ASSERTED, never supplied by the caller)."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV
from reflection_holo.forward.contracts import ExitWave

SCHEMA = "reflection_holo.forward.multislice.exit_wave/1"
AXES = ("x: surface normal (outward), row index", "y: in-plane transverse, column index")
_KEYS = ("schema", "psi", "axes", "units", "dx_A", "dy_A", "x0_A", "y0_A", "plane", "z_A",
         "energy_keV", "theta_in_ext_rad", "realisation", "seed", "precision", "metadata_json")


class ExitWaveFileError(ValueError):
    """An exit-wave file fails an assertion of the loader."""


def save_exit_wave(path, ew: ExitWave) -> Path:
    path = Path(path)
    if path.suffix != ".npz":
        raise ValueError("exit waves are written as .npz")
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    np.savez(path, schema=np.array(SCHEMA), psi=ew.psi, axes=np.array(AXES),
             units=np.array("angstrom"), dx_A=np.float64(ew.dx_A), dy_A=np.float64(ew.dy_A),
             x0_A=np.float64(ew.x0_A), y0_A=np.float64(ew.y0_A), plane=np.array(ew.plane),
             z_A=np.float64(ew.z_A), energy_keV=np.float64(ew.energy_keV),
             theta_in_ext_rad=np.float64(ew.theta_in_ext_rad),
             realisation=np.int64(ew.realisation),
             seed=np.int64(-1 if ew.seed is None else ew.seed),
             precision=np.array(ew.psi.dtype.name),
             metadata_json=np.array(json.dumps(ew.metadata, default=_jsonable)))
    return path


def _jsonable(o):
    if isinstance(o, np.generic):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def load_exit_wave(path, *, expected_plane: str) -> ExitWave:
    """Load and assert: schema, every key, axis order, units, finite positive pixel sizes that
    match the metadata grid, the declared plane equal to ``expected_plane`` (required), 200 keV,
    complex dtype equal to the recorded precision."""
    with np.load(Path(path), allow_pickle=False) as f:
        missing = [k for k in _KEYS if k not in f.files]
        if missing:
            raise ExitWaveFileError(f"{path}: missing datasets {missing}")
        if str(f["schema"]) != SCHEMA:
            raise ExitWaveFileError(f"{path}: schema {f['schema']} != {SCHEMA}")
        if tuple(str(a) for a in f["axes"]) != AXES:
            raise ExitWaveFileError(f"{path}: axis order {f['axes']} != {AXES}")
        if str(f["units"]) != "angstrom":
            raise ExitWaveFileError(f"{path}: units {f['units']} != angstrom")
        psi = f["psi"]
        if psi.ndim != 2 or psi.dtype.name not in ("complex64", "complex128"):
            raise ExitWaveFileError(f"{path}: psi must be a 2D complex64/complex128 array")
        if psi.dtype.name != str(f["precision"]):
            raise ExitWaveFileError(f"{path}: dtype {psi.dtype} != recorded {f['precision']}")
        dx, dy = float(f["dx_A"]), float(f["dy_A"])
        if not (np.isfinite(dx) and dx > 0 and np.isfinite(dy) and dy > 0):
            raise ExitWaveFileError(f"{path}: pixel sizes must be finite and > 0")
        meta = json.loads(str(f["metadata_json"]))
        g = meta.get("grid", {})
        if (g.get("nx"), g.get("ny")) != psi.shape or not np.isclose(g.get("dx_A"), dx) or \
                not np.isclose(g.get("dy_A"), dy):
            raise ExitWaveFileError(f"{path}: grid metadata {g} inconsistent with psi "
                                    f"{psi.shape}, dx {dx}, dy {dy}")
        plane = str(f["plane"])
        if plane != expected_plane:
            raise ExitWaveFileError(f"{path}: plane '{plane}' != expected '{expected_plane}'")
        E = float(f["energy_keV"])
        if E != BEAM_ENERGY_SUPPLIED_KEV:
            raise ExitWaveFileError(f"{path}: energy {E} keV != 200 keV (PROJECT_INPUT item 1)")
        seed = int(f["seed"])
        return ExitWave(psi=psi, dx_A=dx, dy_A=dy, x0_A=float(f["x0_A"]), y0_A=float(f["y0_A"]),
                        plane=plane, z_A=float(f["z_A"]), energy_keV=E,
                        theta_in_ext_rad=float(f["theta_in_ext_rad"]),
                        realisation=int(f["realisation"]), seed=None if seed < 0 else seed,
                        metadata=meta)
