"""Declared grids, complex waves and intensity holograms (docs/05 section 5; docs/physics_conventions.md).

Every array carried by this package lives on a declared ``Grid``: shape, pixel size on BOTH axes (A),
the names of the two array axes and the declared plane of the wave. Nothing is inferred: a missing or
non-positive pixel size, a missing axis name or a missing plane raises. Pixel sizes of experimental
data are PROJECT_INPUT item 5 and must be read from the data files (io/, other agent) and passed here.

Conventions (docs/physics_conventions.md):
* array index order is (axis 0, axis 1); every 2-vector in this package (positions, shifts, spatial
  frequencies) is ordered the same way;
* real-space coordinate of pixel (i0, i1) is r = (i0 * d0, i1 * d1) in A (origin at pixel (0, 0));
* spatial frequencies q in cycles/A, laid out as ``numpy.fft.fftfreq(n, d)`` (unshifted); the forward
  transform is numpy's ``fft2`` (kernel exp(-2 pi i q.r)), so a wave exp(+2 pi i q0.r) appears at +q0.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any

import numpy as np

_HOLOGRAM_CONTENTS = ("object", "empty", "flat_region")


def _require_2vector(name: str, value, *, positive: bool = False, allow_zero: bool = True) -> tuple[float, float]:
    if value is None:
        raise ValueError(f"{name} is required and was None (no default is substituted)")
    arr = np.asarray(value, dtype=float)
    if arr.shape != (2,):
        raise ValueError(f"{name} must be a 2-vector ordered (axis 0, axis 1); got shape {arr.shape}")
    if not np.all(np.isfinite(arr)):
        raise ValueError(f"{name} must be finite; got {value!r}")
    if positive and not np.all(arr > 0):
        raise ValueError(f"{name} must be > 0 on both axes; got {value!r}")
    if not allow_zero and not np.any(arr):
        raise ValueError(f"{name} must be non-zero; got {value!r}")
    return float(arr[0]), float(arr[1])


def sha256_array(a: np.ndarray) -> str:
    """SHA-256 of the array bytes together with dtype and shape (for run records)."""
    a = np.ascontiguousarray(a)
    h = hashlib.sha256()
    h.update(str(a.dtype).encode())
    h.update(str(a.shape).encode())
    h.update(a.tobytes())
    return h.hexdigest()


@dataclass(frozen=True)
class Grid:
    """A declared sampling grid. All four fields are required; there are no defaults.

    shape         (n0, n1) pixels
    pixel_size_A  (d0, d1) in A; PROJECT_INPUT item 5 for experimental data (read from the file)
    axes          names of array axis 0 and axis 1 (e.g. ("y", "x")); recorded and compared, not guessed
    plane         the declared plane of the wave (e.g. "image plane, specimen coordinates")
    """

    shape: tuple[int, int]
    pixel_size_A: tuple[float, float]
    axes: tuple[str, str]
    plane: str

    def __post_init__(self):
        if self.shape is None or len(tuple(self.shape)) != 2:
            raise ValueError(f"shape must be (n0, n1); got {self.shape!r}")
        n0, n1 = (int(v) for v in self.shape)
        if n0 != self.shape[0] or n1 != self.shape[1] or n0 < 2 or n1 < 2:
            raise ValueError(f"shape must be two integers >= 2; got {self.shape!r}")
        if self.pixel_size_A is None:
            raise ValueError("pixel_size_A is required on both axes (PROJECT_INPUT item 5 for "
                             "experimental data); no default is substituted")
        d = _require_2vector("pixel_size_A", self.pixel_size_A, positive=True)
        if (self.axes is None or len(tuple(self.axes)) != 2
                or not all(isinstance(a, str) and a for a in self.axes) or self.axes[0] == self.axes[1]):
            raise ValueError(f"axes must be two distinct non-empty names; got {self.axes!r}")
        if not isinstance(self.plane, str) or not self.plane.strip():
            raise ValueError("plane must be declared (non-empty string)")
        object.__setattr__(self, "shape", (n0, n1))
        object.__setattr__(self, "pixel_size_A", d)
        object.__setattr__(self, "axes", (str(self.axes[0]), str(self.axes[1])))

    # -- sampling ------------------------------------------------------------------------------
    def coordinates_A(self) -> tuple[np.ndarray, np.ndarray]:
        """(r0, r1) arrays of shape ``shape``: r_a = index_a * d_a (A), origin at pixel (0, 0)."""
        i0 = np.arange(self.shape[0], dtype=float) * self.pixel_size_A[0]
        i1 = np.arange(self.shape[1], dtype=float) * self.pixel_size_A[1]
        return np.meshgrid(i0, i1, indexing="ij")

    def frequencies_cycles_per_A(self) -> tuple[np.ndarray, np.ndarray]:
        """(q0, q1) arrays in cycles/A in numpy's unshifted fft layout (fftfreq(n, d))."""
        f0 = np.fft.fftfreq(self.shape[0], d=self.pixel_size_A[0])
        f1 = np.fft.fftfreq(self.shape[1], d=self.pixel_size_A[1])
        return np.meshgrid(f0, f1, indexing="ij")

    @property
    def frequency_step_cycles_per_A(self) -> tuple[float, float]:
        return (1.0 / (self.shape[0] * self.pixel_size_A[0]), 1.0 / (self.shape[1] * self.pixel_size_A[1]))

    @property
    def nyquist_cycles_per_A(self) -> tuple[float, float]:
        return (0.5 / self.pixel_size_A[0], 0.5 / self.pixel_size_A[1])

    # -- comparison ----------------------------------------------------------------------------
    def assert_same(self, other: "Grid", what: str) -> None:
        """Raise ValueError unless ``other`` has identical shape, pixel sizes, axes and plane."""
        if not isinstance(other, Grid):
            raise TypeError(f"{what}: expected a Grid, got {type(other).__name__}")
        if self != other:
            raise ValueError(f"{what}: grids differ: {self.as_record()} vs {other.as_record()}")

    def assert_same_sampling(self, other: "Grid", what: str) -> None:
        """Raise unless pixel sizes, axes and plane agree (the shape may differ, e.g. a crop)."""
        if not isinstance(other, Grid):
            raise TypeError(f"{what}: expected a Grid, got {type(other).__name__}")
        if (self.pixel_size_A != other.pixel_size_A or self.axes != other.axes
                or self.plane != other.plane):
            raise ValueError(f"{what}: sampling differs: {self.as_record()} vs {other.as_record()}")

    def as_record(self) -> dict:
        return {"shape": list(self.shape), "pixel_size_A": list(self.pixel_size_A),
                "axes": list(self.axes), "plane": self.plane}


@dataclass(frozen=True, eq=False)
class Wave:
    """A complex wave sampled on a declared grid, exp(+ik.r) convention.

    ``realisation`` is the ensemble-realisation index (None for a single coherent realisation);
    object and reference waves of one realisation must carry the same index (SM13).
    """

    data: np.ndarray
    grid: Grid
    label: str
    realisation: int | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not isinstance(self.grid, Grid):
            raise TypeError("grid must be a Grid (declared pixel sizes, axes and plane)")
        a = np.asarray(self.data)
        if a.shape != self.grid.shape:
            raise ValueError(f"wave '{self.label}': data shape {a.shape} != grid shape {self.grid.shape}")
        a = a.astype(np.complex128, copy=True)
        if not np.all(np.isfinite(a)):
            raise ValueError(f"wave '{self.label}': non-finite values")
        a.setflags(write=False)
        object.__setattr__(self, "data", a)
        if not isinstance(self.label, str) or not self.label:
            raise ValueError("label must be a non-empty string")
        if self.realisation is not None and int(self.realisation) != self.realisation:
            raise ValueError("realisation must be an integer or None")


@dataclass(frozen=True, eq=False)
class Hologram:
    """A recorded or simulated intensity hologram on a declared grid.

    content   "object" (specimen in the object branch), "empty" (reference only / vacuum) or
              "flat_region" (a region known to be flat); required, used by the carrier locator,
              which refuses object holograms (the find_peak trap, audit C3; docs/03 section 6).
    metadata  model and processing record (reference model, carrier, artefacts, noise, seeds)
    noiseless_intensity  the intensity before detector noise, kept so that raw and noisy
              holograms are both saved (docs/05 section 5 item 6); None for experimental data
    """

    intensity: np.ndarray
    grid: Grid
    content: str
    metadata: dict[str, Any]
    noiseless_intensity: np.ndarray | None

    def __post_init__(self):
        if not isinstance(self.grid, Grid):
            raise TypeError("grid must be a Grid (declared pixel sizes, axes and plane)")
        a = np.asarray(self.intensity)
        if np.iscomplexobj(a):
            raise ValueError("a hologram is an intensity: real values only")
        if a.shape != self.grid.shape:
            raise ValueError(f"intensity shape {a.shape} != grid shape {self.grid.shape}")
        a = a.astype(np.float64, copy=True)
        if not np.all(np.isfinite(a)):
            raise ValueError("hologram intensity has non-finite values")
        a.setflags(write=False)
        object.__setattr__(self, "intensity", a)
        if self.content not in _HOLOGRAM_CONTENTS:
            raise ValueError(f"content must be one of {_HOLOGRAM_CONTENTS}; got {self.content!r}")
        if self.noiseless_intensity is not None:
            b = np.asarray(self.noiseless_intensity, dtype=np.float64).copy()
            if b.shape != self.grid.shape:
                raise ValueError("noiseless_intensity shape differs from the grid")
            b.setflags(write=False)
            object.__setattr__(self, "noiseless_intensity", b)
        if not isinstance(self.metadata, dict):
            raise TypeError("metadata must be a dict")

    @property
    def sha256(self) -> str:
        return sha256_array(self.intensity)
