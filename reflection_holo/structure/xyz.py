"""Extended-XYZ writer (and reader for round trips) that records the slab frame.

Positions are in angstrom in the slab frame x = outward normal, y = z x x, z = beam azimuth
(docs/physics_conventions.md). The comment line carries the cell (``Lattice``), ``pbc``, the frame
rows in cubic crystal coordinates, the crystal origin, the azimuth, the options with their labels
and the SHA-256 of the positions. No engine-specific writer exists yet.
"""
from __future__ import annotations

import json
import shlex
from pathlib import Path

import numpy as np


def _vec(v) -> str:
    return " ".join(f"{float(x):.15g}" for x in np.ravel(v))


def _kv(key: str, value) -> str:
    v = str(value)
    if '"' in v or "\n" in v:
        raise ValueError(f"extended-XYZ value for {key} may not contain quotes or newlines")
    return f'{key}="{v}"' if (not v or any(c in v for c in ' ="\'')) else f"{key}={v}"


def write_xyz(structure, path) -> Path:
    path = Path(path)
    md = structure.metadata
    cell = np.asarray(structure.cell_A, float)
    opts = md["options"]
    header = {
        "Lattice": _vec(cell),
        "Properties": "species:S:1:pos:R:3",
        "pbc": " ".join("T" if p else "F" for p in structure.pbc),
        "units": "angstrom",
        "frame": "slab: x=outward normal, z=beam azimuth, y=z cross x",
        "normal_hkl": _vec(md["surface"]["hkl"]),
        "azimuth_uvw": _vec(md["azimuth"]["uvw"]),
        "azimuth_label": md["azimuth"]["label"],
        "x_hat_crystal": _vec(structure.frame.x_hat),
        "y_hat_crystal": _vec(structure.frame.y_hat),
        "z_hat_crystal": _vec(structure.frame.z_hat),
        "crystal_origin_slab_A": _vec(structure.crystal_origin_slab_A),
        "lattice_parameter_A": f"{md['lattice']['a_A']:.15g}",
        "termination": f"{opts['termination']['value']} ({opts['termination']['label']})",
        "overlayer": (f"{opts['overlayer']['value']} ({opts['overlayer']['label']})"),
        "riser_relaxation": f"{opts['riser_relaxation']['value']}",
        "builder": md["builder"],
        "positions_sha256": md["positions_sha256"],
    }
    comment = " ".join(_kv(k, v) for k, v in header.items())
    lines = [str(structure.n_atoms), comment]
    for s, r in zip(structure.species, structure.positions_A):
        lines.append(f"{s} {r[0]:.10f} {r[1]:.10f} {r[2]:.10f}")
    path.write_text("\n".join(lines) + "\n")
    return path


def read_xyz(path):
    """Return (species, positions_A, header dict) of a file written by :func:`write_xyz`."""
    lines = Path(path).read_text().splitlines()
    n = int(lines[0])
    header = {}
    for tok in shlex.split(lines[1]):
        k, _, v = tok.partition("=")
        header[k] = v
    species, pos = [], []
    for ln in lines[2:2 + n]:
        p = ln.split()
        species.append(p[0])
        pos.append([float(x) for x in p[1:4]])
    if len(species) != n:
        raise ValueError(f"{path}: {len(species)} atom lines, header says {n}")
    return np.array(species), np.array(pos), header


def write_metadata_json(structure, path) -> Path:
    """Write the full structure metadata (terrace map, steps, options, labels) as JSON."""
    path = Path(path)
    path.write_text(json.dumps(structure.metadata, indent=2, sort_keys=True, default=_jsonable))
    return path


def _jsonable(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    raise TypeError(f"not JSON serialisable: {type(o)}")
