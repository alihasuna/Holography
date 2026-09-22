"""Array backend ("numpy" or "cupy", a REQUIRED choice) and precision ("complex64" or "complex128",
REQUIRED). cupy is imported lazily, only when requested; no fallback between backends exists
(a missing cupy raises)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

BACKENDS = ("numpy", "cupy")
PRECISIONS = {"complex64": np.float32, "complex128": np.float64}


@dataclass
class Backend:
    name: str
    xp: Any
    complex_dtype: Any
    real_dtype: Any
    threads: int
    _fft: Any = None
    _kw: dict | None = None

    def fft2(self, a):
        return self._fft.fft2(a, axes=(0, 1), **self._kw)

    def ifft2(self, a):
        return self._fft.ifft2(a, axes=(0, 1), **self._kw)

    def asarray(self, a, dtype=None):
        return self.xp.asarray(a, dtype=dtype)

    def to_numpy(self, a) -> np.ndarray:
        if self.name == "cupy":
            return self.xp.asnumpy(a)
        return np.asarray(a)

    def describe(self) -> dict:
        d = dict(backend=self.name, precision=np.dtype(self.complex_dtype).name,
                 threads=self.threads, fft=self._fft.__name__)
        if self.name == "cupy":
            d["cupy_version"] = self.xp.__version__
        return d


def get_backend(name: str, precision: str, threads: int) -> Backend:
    if name not in BACKENDS:
        raise ValueError(f"backend must be one of {BACKENDS}, got {name!r}")
    if precision not in PRECISIONS:
        raise ValueError(f"precision must be one of {tuple(PRECISIONS)}, got {precision!r}")
    if int(threads) != threads or threads < 1:
        raise ValueError("threads must be a positive integer")
    real = PRECISIONS[precision]
    cplx = np.dtype(precision).type
    if name == "numpy":
        try:
            import scipy.fft as sfft            # threaded pocketfft (workers)
            return Backend("numpy", np, cplx, real, int(threads), sfft, dict(workers=int(threads)))
        except ImportError:                     # pragma: no cover - scipy is installed
            if threads != 1:
                raise RuntimeError("scipy.fft is unavailable; numpy.fft is single-threaded, so "
                                   "threads must be 1")
            return Backend("numpy", np, cplx, real, 1, np.fft, {})
    import cupy as cp                           # lazy: only when requested
    import cupy.fft as cfft
    return Backend("cupy", cp, getattr(cp, precision), getattr(cp, np.dtype(real).name),
                   int(threads), cfft, {})
