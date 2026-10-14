"""Array backend selection: numpy on CPU, cupy on GPU (same code path)."""
from __future__ import annotations

import numpy as np


def get_xp(name: str):
    if name == "numpy":
        return np
    if name == "cupy":
        import cupy  # noqa: F401  (import error is the intended failure on CPU nodes)
        return cupy
    raise ValueError(f"unknown backend {name!r}")


def to_numpy(a):
    if isinstance(a, np.ndarray) or np.isscalar(a):
        return a
    return a.get()


def backend_info(xp):
    info = {"backend": xp.__name__}
    if xp.__name__ == "cupy":
        dev = xp.cuda.Device()
        props = xp.cuda.runtime.getDeviceProperties(dev.id)
        name = props["name"]
        info.update(
            device_id=int(dev.id),
            device_name=name.decode() if isinstance(name, bytes) else str(name),
            total_memory_GB=props["totalGlobalMem"] / 1e9,
            cuda_runtime=xp.cuda.runtime.runtimeGetVersion(),
            cupy_version=xp.__version__,
        )
    return info
