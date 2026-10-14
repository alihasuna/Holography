"""HDF5 output of task results (nested dicts, lists of dicts, arrays, scalars)."""
from __future__ import annotations

import json
import os

import numpy as np


def _write(group, key, value):
    import h5py  # noqa: F401
    if isinstance(value, dict):
        sub = group.create_group(key)
        for k, v in value.items():
            _write(sub, str(k), v)
    elif isinstance(value, (list, tuple)) and value and all(isinstance(v, dict) for v in value):
        sub = group.create_group(key)
        sub.attrs["__list_of_dicts__"] = len(value)
        for i, v in enumerate(value):
            _write(sub, str(i), v)
    elif isinstance(value, np.ndarray):
        kw = dict(compression="gzip", compression_opts=4) if value.size > 4096 else {}
        group.create_dataset(key, data=value, **kw)
    elif isinstance(value, (list, tuple)):
        arr = np.asarray(value)
        if arr.dtype.kind in "OU":
            group.attrs[key] = json.dumps(value)
        else:
            group.create_dataset(key, data=arr)
    elif value is None:
        group.attrs[key] = "None"
    elif isinstance(value, (str, bool, int, float, np.integer, np.floating, complex, np.complexfloating)):
        group.attrs[key] = value
    else:
        group.attrs[key] = json.dumps(value, default=str)


def write_result(path, result, task, manifest):
    """Atomically write result, task and manifest to an HDF5 file."""
    import h5py
    tmp = path + f".tmp{os.getpid()}"
    with h5py.File(tmp, "w") as f:
        f.attrs["task_json"] = json.dumps(task, sort_keys=True)
        f.attrs["manifest_json"] = json.dumps(manifest, sort_keys=True, default=str)
        for k, v in result.items():
            _write(f, k, v)
    os.replace(tmp, path)


def _read(node):
    import h5py
    if isinstance(node, h5py.Dataset):
        return node[()]
    out = {}
    for k, v in node.attrs.items():
        if k == "__list_of_dicts__":
            continue
        out[k] = v
    for k in node.keys():
        out[k] = _read(node[k])
    if "__list_of_dicts__" in node.attrs:
        return [out[str(i)] for i in range(int(node.attrs["__list_of_dicts__"]))]
    return out


def read_result(path):
    import h5py
    with h5py.File(path, "r") as f:
        res = _read(f)
    res["task"] = json.loads(res.pop("task_json"))
    res["manifest"] = json.loads(res.pop("manifest_json"))
    return res
