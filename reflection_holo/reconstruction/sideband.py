"""Sideband (Fourier) reconstruction of off-axis holograms: ONE code path for simulated and
experimental holograms (docs/05 section 5 item 7; PROJECT_INPUT item 19 lists the processing
choices, every one of which is a REQUIRED argument here).

Sources: SM12 (P07 para 56 and Eqs. (18)-(26): sideband method, separation q_c > 3B, resolution about
three fringe spacings; SECTION_READ. sigma_phi = sqrt(2)/(mu sqrt(N)): DERIVED_HERE). Defects avoided:
audit A, C3 (demodulation on the brightest bin of the OBJECT hologram) and M5 (plane detrend on by
default).

Procedure
1. ``locate_carrier``: on an EMPTY (reference-only) or flat-region hologram, never on an object
   hologram (refused unless the trap is demonstrated on purpose): the brightest |FFT| bin inside a
   declared search disc around the expected sideband, outside a declared exclusion disc about q = 0.
   The sideband is DECLARED (``CarrierSearch.sideband_declaration``, with its evidence) and the
   search region must lie on one side of a line through the origin (disc radius < |guess|), and
   must hold no Hermitian pair of bins on the grid (Nyquist aliasing): |F(q)| = |F(-q)| for a real
   hologram, so a region holding both sidebands would choose by array order (audit A2 M1;
   model_assumptions B15). Exactly equal bins inside the region go to the one closest to the
   guess, then to the first in centred (fftshift) order.
   Sub-pixel refinement (declared): "none" (integer bin) or "dft_ratio": along each axis, the exact
   single-tone interpolation from the complex ratio rho = X[k +- 1]/X[k] of the peak bin and its larger
   neighbour, u = (1 - rho)/(1 - rho z^-+1), z = exp(2 pi i/n), delta = n arg(u)/(2 pi) bins
   (DERIVED_HERE from the DFT of a complex exponential; exact for one noiseless tone; biased by the
   leakage of the conjugate sideband and the centre band, and noisy under shot noise).
2. Sideband selection: the sideband at q_s holds u_o u_r^*, i.e. phi_o - phi_r, when q_s = -q_ref for a
   reference u_r ~ exp(+2 pi i q_ref.r) (numpy FFT sign, exp(+ik.r) convention; physics_conventions).
   Which of the two sidebands this is in an experiment is a declared input (PROJECT_INPUT items 10 and
   16); for simulated holograms the choice is checked against the recorded reference carrier, the
   outcome is stored in ``SidebandResult.sideband_sign_check``, and a CONJUGATE result is refused
   unless the call is an explicit trap demonstration.
3. Mask: a disc of declared radius R (cycles/A) centred on the refined q_s, apodisation "none"
   (top-hat) or "hann" (0.5 (1 + cos(pi r/R)) for r < R). The disc must not contain q = 0 and must lie
   inside the Nyquist band; otherwise the call fails.
4. Demodulation: integer-bin roll of the masked spectrum to q = 0, inverse FFT, then multiplication by
   exp(-2 pi i (q_s - q_bin).r) for the sub-pixel remainder. The complex result is |u_o||u_r|
   exp(i(phi_o - phi_r)) with numpy's normalisation. No zero padding, no real-space window.
5. Reference correction (declared): "none", or "divide_empty": w_obj / w_empty with the same carrier
   and mask applied to the empty hologram (removes the residual carrier, the reference's residual
   phase and the mask's own transfer). Validity (audit A2 m1, re-audit A2b N6): with "divide_empty"
   the caller declares ``empty_min_visibility`` V_min (0 < V_min <= 1, REQUIRED); the local fringe
   visibility of the EMPTY hologram is V = 2 |w_empty| / D, D the empty intensity low-passed by the
   same mask centred on q = 0 (for I = A + B cos(...), w = B/2 and D = A, so V = B/A). Where
   V < V_min (or D <= 0) the corrected phase and amplitude are NaN and ``valid_mask`` is False, with
   a RuntimeWarning. The criterion is absolute: it does not depend on how much of the field has
   fringes. With "none", exact zeros of |w_obj| are treated the same way. The reference's own
   validity (the R2 ``valid_mask`` of the hologram metadata) is ANDed into ``valid_mask``; those
   values are kept but flagged.
6. Unwrapping (declared): "none" or "itoh_raster" (Itoh path integration; re-audit A2b N5). The
   valid pixels (``valid_mask`` and finite) are split into rows of maximal valid runs; runs in
   adjacent rows that share a column are connected (4-connectivity). Each connected region is
   unwrapped from its own seed, its first valid pixel in raster order (value = its wrapped phase):
   every run is unwrapped along its row (numpy.unwrap), and a run is joined to an already
   unwrapped run in the adjacent row through their leftmost shared column (breadth-first over the
   runs). Regions carry INDEPENDENT 2 pi offsets and are labelled (``SidebandResult.unwrap_regions``,
   ``parameters["unwrapping_regions"]``); invalid pixels are NaN. For an all-valid field this is
   exactly the raster path (column 0, then each row). Path-following, NOT residue-aware: at phase
   singularities the result depends on the path. The raw wrapped phase is always kept.
7. NO ramp or plane is removed by the reconstruction. ``fit_phase_plane`` / ``subtract_phase_plane``
   are separate, explicit calls with a declared fitting region; their inputs are never modified.

Resolution (SM12): 1/R, reported in A and in fringe spacings (|q_s|/R; 3 for R = |q_s|/3).
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from reflection_holo.constants import TWO_PI
from reflection_holo.geometry.specular import wrap_to_pi  # noqa: F401  (canonical; re-exported)
from reflection_holo.optics.fields import Grid, Hologram, _require_2vector, sha256_array
from reflection_holo.quantification.noise import phase_noise_sigma_rad

SUBPIXEL_METHODS = ("none", "dft_ratio")
MASK_SHAPES = ("disc",)
APODISATIONS = ("none", "hann")
REFERENCE_CORRECTIONS = ("none", "divide_empty")
UNWRAPPINGS = ("none", "itoh_raster")


def _positive(name: str, value, *, allow_inf: bool = False) -> float:
    if value is None:
        raise ValueError(f"{name} is required (PROJECT_INPUT item 19); no default is substituted")
    v = float(value)
    if np.isnan(v) or v <= 0 or (np.isinf(v) and not allow_inf):
        raise ValueError(f"{name} must be > 0{' (inf allowed)' if allow_inf else ''}; got {value!r}")
    return v


# ------------------------------------------------------------------------------------------------
# carrier location
# ------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class CarrierSearch:
    """Declared carrier-location method (PROJECT_INPUT item 19). No defaults.

    sideband_guess_cycles_per_A   expected position of the phi_o - phi_r sideband (= -q_ref); non-zero
    search_radius_cycles_per_A    search disc about the guess; finite and < |guess|, so that the
                                  disc lies on one side of a line through the origin and cannot
                                  hold both Hermitian partners (audit A2 M1; B15)
    exclusion_radius_cycles_per_A disc about q = 0 excluded from the search (centre band)
    subpixel                      "none" or "dft_ratio" (module docstring, step 1)
    sideband_declaration          which sideband the guess is and on what evidence, e.g. "-q_ref of
                                  the simulated reference" or "PROJECT_INPUT items 10, 16: ..."
    """

    sideband_guess_cycles_per_A: tuple[float, float]
    search_radius_cycles_per_A: float
    exclusion_radius_cycles_per_A: float
    subpixel: str
    sideband_declaration: str

    def __post_init__(self):
        g = _require_2vector("sideband_guess_cycles_per_A", self.sideband_guess_cycles_per_A,
                             allow_zero=False)
        object.__setattr__(self, "sideband_guess_cycles_per_A", g)
        r = self.search_radius_cycles_per_A
        if r is None:
            raise ValueError("search_radius_cycles_per_A is required (PROJECT_INPUT item 19); no "
                             "default is substituted")
        r = float(r)
        if np.isnan(r) or r <= 0:
            raise ValueError(f"search_radius_cycles_per_A must be > 0; got {r!r}")
        if not r < float(np.hypot(*g)):
            raise ValueError(
                f"search disc of radius {r} cycles/A about the guess {g} (|guess| = "
                f"{np.hypot(*g):.6g}) is not confined to one side of a line through the origin: it "
                f"holds Hermitian partners q and -q, whose |F| are equal for a real hologram, so the "
                f"sideband would be chosen by array order (audit A2 M1; model_assumptions B15). "
                f"Declare the phi_o - phi_r sideband and use a radius < |guess|")
        object.__setattr__(self, "search_radius_cycles_per_A", r)
        v = self.exclusion_radius_cycles_per_A
        if v is None or not np.isfinite(float(v)) or float(v) < 0:
            raise ValueError("exclusion_radius_cycles_per_A must be a finite value >= 0")
        object.__setattr__(self, "exclusion_radius_cycles_per_A", float(v))
        if self.subpixel not in SUBPIXEL_METHODS:
            raise ValueError(f"subpixel must be one of {SUBPIXEL_METHODS}; got {self.subpixel!r}")
        d = self.sideband_declaration
        if not isinstance(d, str) or not d.strip():
            raise ValueError("sideband_declaration must declare which sideband the guess is and on "
                             "what evidence (PROJECT_INPUT items 10, 16, 19 for experiments; B15)")

    def as_record(self) -> dict:
        return {"sideband_guess_cycles_per_A": list(self.sideband_guess_cycles_per_A),
                "search_radius_cycles_per_A": self.search_radius_cycles_per_A,
                "exclusion_radius_cycles_per_A": self.exclusion_radius_cycles_per_A,
                "subpixel": self.subpixel, "sideband_declaration": self.sideband_declaration}


@dataclass(frozen=True)
class CarrierLocation:
    """Located sideband centre. ``carrier_cycles_per_A`` = -q_s is the reference tilt it implies."""

    sideband_centre_cycles_per_A: tuple[float, float]
    integer_bin: tuple[int, int]
    integer_bin_frequency_cycles_per_A: tuple[float, float]
    subpixel_offset_bins: tuple[float, float]
    peak_magnitude: float
    search: CarrierSearch
    located_on: str
    hologram_content: str
    hologram_sha256: str
    grid: Grid

    @property
    def carrier_cycles_per_A(self) -> tuple[float, float]:
        return (-self.sideband_centre_cycles_per_A[0], -self.sideband_centre_cycles_per_A[1])

    @property
    def carrier_magnitude_cycles_per_A(self) -> float:
        return float(np.hypot(*self.sideband_centre_cycles_per_A))

    @property
    def fringe_spacing_A(self) -> float:
        return 1.0 / self.carrier_magnitude_cycles_per_A

    def fringe_spacing_px(self) -> tuple[float, float]:
        """Fringe spacing measured along each axis in pixels (inf if the carrier has no component)."""
        q = self.sideband_centre_cycles_per_A
        return tuple(float(np.inf) if q[a] == 0 else abs(1.0 / (q[a] * self.grid.pixel_size_A[a]))
                     for a in (0, 1))

    def as_record(self) -> dict:
        return {"sideband_centre_cycles_per_A": list(self.sideband_centre_cycles_per_A),
                "carrier_cycles_per_A (= -sideband centre)": list(self.carrier_cycles_per_A),
                "integer_bin": list(self.integer_bin),
                "integer_bin_frequency_cycles_per_A": list(self.integer_bin_frequency_cycles_per_A),
                "subpixel_offset_bins": list(self.subpixel_offset_bins),
                "peak_magnitude": self.peak_magnitude, "fringe_spacing_A": self.fringe_spacing_A,
                "search": self.search.as_record(), "located_on": self.located_on,
                "hologram_content": self.hologram_content, "hologram_sha256": self.hologram_sha256,
                "grid": self.grid.as_record()}


def _dft_ratio_offset(F: np.ndarray, k: tuple[int, int], axis: int) -> float:
    """Sub-bin offset of a single tone along ``axis`` from the peak bin and its larger neighbour."""
    n = F.shape[axis]
    kp = list(k)
    km = list(k)
    kp[axis] = (k[axis] + 1) % n
    km[axis] = (k[axis] - 1) % n
    x0 = F[tuple(k)]
    xp = F[tuple(kp)]
    xm = F[tuple(km)]
    z = np.exp(1j * TWO_PI / n)
    if abs(xp) >= abs(xm):
        rho = xp / x0
        u = (1.0 - rho) / (1.0 - rho / z)
    else:
        rho = xm / x0
        u = (1.0 - rho) / (1.0 - rho * z)
    delta = n * float(np.angle(u)) / TWO_PI
    if abs(delta) > 0.5 + 1e-9:
        raise ValueError(f"sub-pixel refinement gave {delta:.3f} bins (> 0.5): the peak is not a "
                         f"single dominant tone; use subpixel='none' or check the empty hologram")
    return delta


def locate_carrier(hologram: Hologram, search: CarrierSearch, *,
                   allow_object_hologram: bool = False) -> CarrierLocation:
    """Locate the sideband centre on an EMPTY or flat-region hologram (docs/03 section 6; audit C3).

    An object hologram is refused: its brightest bin is not the carrier in general (for a 50/50 phase
    step it sits one bin off). ``allow_object_hologram=True`` exists ONLY to demonstrate that trap in
    tests; the location is then labelled as the trap in ``located_on``.
    """
    if not isinstance(hologram, Hologram):
        raise TypeError("hologram must be a Hologram")
    if not isinstance(search, CarrierSearch):
        raise TypeError("search must be a CarrierSearch (declared carrier-location method)")
    if hologram.content == "object" and not allow_object_hologram:
        raise ValueError("the carrier must be located on an EMPTY or flat-region hologram, never on "
                         "the object hologram (brightest-bin trap, audit C3; docs/03 section 6)")
    grid = hologram.grid
    F = np.fft.fft2(hologram.intensity)
    q0, q1 = grid.frequencies_cycles_per_A()
    g = search.sideband_guess_cycles_per_A
    sel = np.hypot(q0 - g[0], q1 - g[1]) <= search.search_radius_cycles_per_A
    sel &= np.hypot(q0, q1) > search.exclusion_radius_cycles_per_A
    if not np.any(sel):
        raise ValueError("the declared search region contains no frequency bins")
    n0, n1 = grid.shape
    i0, i1 = np.nonzero(sel)
    p0, p1 = (-i0) % n0, (-i1) % n1
    partner = sel[p0, p1]
    if np.any(partner):
        distinct = partner & ((p0 != i0) | (p1 != i1))
        j = int(np.argmax(distinct)) if np.any(distinct) else int(np.argmax(partner))
        raise ValueError(
            f"the declared search region holds the bin {(int(i0[j]), int(i1[j]))} and its Hermitian "
            f"partner {(int(p0[j]), int(p1[j]))} (through Nyquist aliasing): |F| is equal on both "
            f"(a self-partner bin is real and carries no sideband phase), so the sideband would be "
            f"chosen by array order (audit A2 M1; B15); move the search disc away from the "
            f"Nyquist band")
    mag = np.where(sel, np.abs(F), -1.0)
    # exactly equal bins inside the region: closest to the guess, then first in centred order
    cand = np.argwhere(mag == mag.max())
    dist = np.hypot(q0[cand[:, 0], cand[:, 1]] - g[0], q1[cand[:, 0], cand[:, 1]] - g[1])
    shifted = np.column_stack([(cand[:, 0] + n0 // 2) % n0, (cand[:, 1] + n1 // 2) % n1])
    best = np.lexsort((shifted[:, 1], shifted[:, 0], dist))[0]
    k = (int(cand[best, 0]), int(cand[best, 1]))
    qb = (float(q0[k]), float(q1[k]))
    if search.subpixel == "dft_ratio":
        off = (_dft_ratio_offset(F, k, 0), _dft_ratio_offset(F, k, 1))
    else:
        off = (0.0, 0.0)
    dq = grid.frequency_step_cycles_per_A
    qs = (qb[0] + off[0] * dq[0], qb[1] + off[1] * dq[1])
    located_on = (f"{hologram.content} hologram" if hologram.content != "object"
                  else "OBJECT hologram (brightest-bin trap, demonstration only)")
    return CarrierLocation(qs, k, qb, off, float(np.abs(F[k])), search, located_on,
                           hologram.content, hologram.sha256, grid)


# ------------------------------------------------------------------------------------------------
# mask
# ------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class MaskSpec:
    """Declared sideband mask (PROJECT_INPUT item 19). No defaults."""

    radius_cycles_per_A: float
    shape: str
    apodisation: str

    def __post_init__(self):
        object.__setattr__(self, "radius_cycles_per_A", _positive("radius_cycles_per_A", self.radius_cycles_per_A))
        if self.shape not in MASK_SHAPES:
            raise ValueError(f"mask shape must be one of {MASK_SHAPES}; got {self.shape!r}")
        if self.apodisation not in APODISATIONS:
            raise ValueError(f"apodisation must be one of {APODISATIONS}; got {self.apodisation!r}")

    def as_record(self) -> dict:
        return {"radius_cycles_per_A": self.radius_cycles_per_A, "shape": self.shape,
                "apodisation": self.apodisation}


def sideband_mask(grid: Grid, centre_cycles_per_A, spec: MaskSpec) -> np.ndarray:
    """Mask W(q) on the unshifted FFT layout of ``grid`` (disc of radius R about ``centre``)."""
    c = _require_2vector("centre_cycles_per_A", centre_cycles_per_A)
    R = spec.radius_cycles_per_A
    if R >= np.hypot(*c):
        raise ValueError(f"mask radius {R} >= |sideband centre| {np.hypot(*c)}: the mask would contain q = 0")
    nyq = grid.nyquist_cycles_per_A
    if abs(c[0]) + R >= nyq[0] or abs(c[1]) + R >= nyq[1]:
        raise ValueError(f"mask (centre {c}, radius {R}) crosses the Nyquist band {nyq}: the fringes are "
                         f"undersampled for this mask")
    return _mask_values(grid, c, spec)


def _mask_values(grid: Grid, c, spec: MaskSpec) -> np.ndarray:
    q0, q1 = grid.frequencies_cycles_per_A()
    R = spec.radius_cycles_per_A
    r = np.hypot(q0 - c[0], q1 - c[1])
    if spec.apodisation == "hann":
        W = np.where(r < R, 0.5 * (1.0 + np.cos(np.pi * r / R)), 0.0)
    else:
        W = np.where(r < R, 1.0, 0.0)
    return W


def _demodulate(intensity: np.ndarray, grid: Grid, qs: tuple[float, float], W: np.ndarray) -> np.ndarray:
    n0, n1 = grid.shape
    dq = grid.frequency_step_cycles_per_A
    b = (int(round(qs[0] / dq[0])), int(round(qs[1] / dq[1])))
    S = np.fft.fft2(intensity) * W
    S = np.roll(S, (-b[0], -b[1]), axis=(0, 1))
    w = np.fft.ifft2(S)
    rem = (qs[0] - b[0] * dq[0], qs[1] - b[1] * dq[1])
    if rem != (0.0, 0.0):
        r0, r1 = grid.coordinates_A()
        w = w * np.exp(-1j * TWO_PI * (rem[0] * r0 + rem[1] * r1))
    return w


# ------------------------------------------------------------------------------------------------
# unwrapping and explicit ramp fitting
# ------------------------------------------------------------------------------------------------

def _runs(row_ok: np.ndarray) -> list[tuple[int, int]]:
    """Maximal runs [a, b) of True in a 1-D boolean array."""
    d = np.diff(np.concatenate([[0], row_ok.astype(np.int8), [0]]))
    return list(zip(np.flatnonzero(d == 1).tolist(), np.flatnonzero(d == -1).tolist()))


def unwrap_itoh_raster(phase: np.ndarray, valid: np.ndarray | None = None, *,
                       return_regions: bool = False):
    """Itoh unwrapping within each connected valid region (module docstring, step 6; A2b N5).

    ``valid`` (default: the finite pixels) marks the pixels that may be used. Returns the unwrapped
    phase (NaN outside the valid pixels) and, with return_regions=True, also an int array of region
    labels (0 = invalid, 1..K = connected valid regions in raster order of their seeds; each region
    has its own 2 pi offset). For an all-valid input this is exactly the plain raster unwrap."""
    p = np.asarray(phase, dtype=float)
    ok = np.isfinite(p) if valid is None else (np.asarray(valid, dtype=bool) & np.isfinite(p))
    if ok.shape != p.shape:
        raise ValueError("valid must have the shape of the phase")
    if ok.all():
        col0 = np.unwrap(p[:, 0])
        rows = np.unwrap(p, axis=1)
        un = rows + (col0 - p[:, 0])[:, None]
        return (un, np.ones(p.shape, dtype=np.int32)) if return_regions else un
    out = np.full(p.shape, np.nan)
    labels = np.zeros(p.shape, dtype=np.int32)
    runs = [_runs(ok[i]) for i in range(p.shape[0])]
    local = [[np.unwrap(p[i, a:b]) for a, b in runs[i]] for i in range(p.shape[0])]
    done = [[False] * len(r) for r in runs]
    region = 0
    for i0 in range(p.shape[0]):
        for k0 in range(len(runs[i0])):
            if done[i0][k0]:
                continue
            region += 1                                   # seed: first valid pixel of a new region
            a, b = runs[i0][k0]
            out[i0, a:b] = local[i0][k0]
            labels[i0, a:b] = region
            done[i0][k0] = True
            queue = [(i0, k0)]
            while queue:
                i, k = queue.pop(0)
                a, b = runs[i][k]
                for j in (i - 1, i + 1):
                    if not 0 <= j < p.shape[0]:
                        continue
                    for m, (c, e) in enumerate(runs[j]):
                        if done[j][m] or c >= b or e <= a:
                            continue
                        col = max(a, c)                   # leftmost shared column
                        target = out[i, col] + wrap_to_pi(p[j, col] - p[i, col])
                        out[j, c:e] = local[j][m] + (target - local[j][m][col - c])
                        labels[j, c:e] = region
                        done[j][m] = True
                        queue.append((j, m))
    return (out, labels) if return_regions else out


@dataclass(frozen=True, eq=False)
class PlaneFit:
    """Least-squares plane a0 r0 + a1 r1 + c fitted to an unwrapped phase over a declared region."""

    gradient_rad_per_A: tuple[float, float]
    offset_rad: float
    region: np.ndarray
    region_description: str
    n_pixels: int
    rms_residual_rad: float
    grid: Grid

    def evaluate(self) -> np.ndarray:
        r0, r1 = self.grid.coordinates_A()
        return self.gradient_rad_per_A[0] * r0 + self.gradient_rad_per_A[1] * r1 + self.offset_rad

    def as_record(self) -> dict:
        return {"gradient_rad_per_A": list(self.gradient_rad_per_A), "offset_rad": self.offset_rad,
                "region_description": self.region_description, "n_pixels": self.n_pixels,
                "region_sha256": sha256_array(self.region), "rms_residual_rad": self.rms_residual_rad}


def fit_phase_plane(phase_unwrapped: np.ndarray, grid: Grid, region: np.ndarray, *,
                    region_description: str) -> PlaneFit:
    """Explicit plane fit over a declared boolean region (never applied implicitly; audit M5).

    The phase must be continuous (unwrapped) inside the region: any neighbouring pair inside the
    region differing by more than pi raises. The input array is not modified.
    """
    p = np.asarray(phase_unwrapped, dtype=float)
    m = np.asarray(region, dtype=bool)
    if p.shape != grid.shape or m.shape != grid.shape:
        raise ValueError("phase and region must be on the grid")
    if not region_description or not isinstance(region_description, str):
        raise ValueError("region_description is required")
    if m.sum() < 3:
        raise ValueError("fitting region needs at least 3 pixels")
    if not np.all(np.isfinite(p[m])):
        raise ValueError("the fitting region contains invalid (non-finite) pixels; exclude them "
                         "from the declared region (SidebandResult.valid_mask)")
    for ax in (0, 1):
        both = m & np.roll(m, -1, axis=ax)
        both = both.copy()
        if ax == 0:
            both[-1, :] = False
        else:
            both[:, -1] = False
        d = np.abs(np.roll(p, -1, axis=ax) - p)[both]
        if d.size and d.max() > np.pi:
            raise ValueError("phase is not continuous inside the fitting region (|jump| > pi): unwrap first")
    r0, r1 = grid.coordinates_A()
    A = np.column_stack([r0[m], r1[m], np.ones(int(m.sum()))])
    coef, *_ = np.linalg.lstsq(A, p[m], rcond=None)
    resid = p[m] - A @ coef
    reg = m.copy()
    reg.setflags(write=False)
    return PlaneFit((float(coef[0]), float(coef[1])), float(coef[2]), reg, region_description,
                    int(m.sum()), float(np.sqrt(np.mean(resid ** 2))), grid)


def subtract_phase_plane(phase: np.ndarray, fit: PlaneFit) -> np.ndarray:
    """Return a NEW array phase - plane; the input (e.g. the raw phase) is untouched."""
    p = np.asarray(phase, dtype=float)
    if p.shape != fit.grid.shape:
        raise ValueError("phase is not on the fit's grid")
    return p - fit.evaluate()


# ------------------------------------------------------------------------------------------------
# reconstruction
# ------------------------------------------------------------------------------------------------

@dataclass(frozen=True, eq=False)
class SidebandResult:
    """Everything the reconstruction produced; nothing is discarded.

    wrapped_phase_raw     arg of the demodulated object sideband, before any reference correction
    wrapped_phase         after the declared reference correction (== raw when "none")
    unwrapped_phase       per the declared unwrapping (None when "none")
    amplitude             |w| after the declared correction (|u_o||u_r| when "none")
    valid_mask            False where the phase is undefined (NaN: sideband amplitude at or below
                          the declared threshold) or the reference is invalid (R2 source outside
                          the field; values kept); module docstring, step 5
    """

    wrapped_phase_raw: np.ndarray
    wrapped_phase: np.ndarray
    unwrapped_phase: np.ndarray | None
    amplitude: np.ndarray
    amplitude_raw: np.ndarray
    object_sideband: np.ndarray
    empty_sideband: np.ndarray | None
    mask: np.ndarray
    carrier: CarrierLocation
    mask_spec: MaskSpec
    reference_correction: str
    unwrapping: str
    resolution_A: float
    resolution_fringe_spacings: float
    sideband_sign_check: str
    grid: Grid
    valid_mask: np.ndarray
    parameters: dict[str, Any] = field(default_factory=dict)
    unwrap_regions: np.ndarray | None = None   # region labels of the unwrapping (0 = invalid)

    def __post_init__(self):
        for name in ("wrapped_phase_raw", "wrapped_phase", "unwrapped_phase", "amplitude",
                     "amplitude_raw", "object_sideband", "empty_sideband", "mask", "valid_mask",
                     "unwrap_regions"):
            a = getattr(self, name)
            if a is not None:
                a.setflags(write=False)


def _sign_check(hologram: Hologram, qs: tuple[float, float]) -> str:
    q_ref = hologram.metadata.get("reference_carrier_cycles_per_A")
    if not q_ref:
        return "unknown: no recorded reference carrier (experimental data: declared by PROJECT_INPUT items 10, 16)"
    q_ref = np.asarray(q_ref, dtype=float)
    d_right = np.hypot(*(np.asarray(qs) + q_ref))
    d_conj = np.hypot(*(np.asarray(qs) - q_ref))
    if d_right < d_conj:
        return "phi_o - phi_r (sideband at -q_ref)"
    return "CONJUGATE: phi_r - phi_o (sideband at +q_ref)"


def reconstruct_sideband(object_hologram: Hologram, *, carrier: CarrierLocation, mask: MaskSpec,
                         empty_hologram: Hologram | None, reference_correction: str,
                         unwrapping: str, empty_min_visibility: float | None = None,
                         trap_demonstration: bool = False) -> SidebandResult:
    """Sideband reconstruction with every processing choice declared (module docstring).

    The carrier must come from ``locate_carrier`` on an empty or flat-region hologram with the same
    pixel sizes, axes and plane (a crop of different shape is allowed; the sideband centre is
    transferred in cycles/A). Returns phases only; heights belong to quantification/.

    ``empty_min_visibility`` (0 < V_min <= 1, the minimum local fringe visibility of the EMPTY
    hologram) must be declared with reference_correction="divide_empty" and must not be given
    otherwise (step 5; A2b N6).

    Refused (ValueError): a carrier located on an OBJECT hologram (the brightest-bin trap, audit
    A2 m7) and, for simulated holograms that record their reference carrier, a sideband that is the
    CONJUGATE of phi_o - phi_r (audit A2 M1). ``trap_demonstration=True`` lifts both refusals ONLY
    for tests and scripts that demonstrate the trap; it is recorded in ``parameters``.
    """
    if not isinstance(trap_demonstration, bool):
        raise TypeError("trap_demonstration must be True or False")
    if not isinstance(object_hologram, Hologram):
        raise TypeError("object_hologram must be a Hologram")
    if not isinstance(carrier, CarrierLocation):
        raise TypeError("carrier must be a CarrierLocation from locate_carrier")
    if not isinstance(mask, MaskSpec):
        raise TypeError("mask must be a MaskSpec")
    if reference_correction not in REFERENCE_CORRECTIONS:
        raise ValueError(f"reference_correction must be one of {REFERENCE_CORRECTIONS}")
    if unwrapping not in UNWRAPPINGS:
        raise ValueError(f"unwrapping must be one of {UNWRAPPINGS}")
    if carrier.hologram_content == "object" and not trap_demonstration:
        raise ValueError("the carrier was located on an OBJECT hologram (brightest-bin trap, audit "
                         "C3; docs/03 section 6): refused unless trap_demonstration=True")
    grid = object_hologram.grid
    grid.assert_same_sampling(carrier.grid, "object hologram and carrier-location hologram")
    if reference_correction == "divide_empty":
        if empty_hologram is None:
            raise ValueError("reference_correction='divide_empty' requires empty_hologram")
        grid.assert_same(empty_hologram.grid, "object and empty holograms")
        if empty_hologram.content == "object":
            raise ValueError("the reference-correction hologram must be empty or flat_region")
        if empty_min_visibility is None:
            raise ValueError("reference_correction='divide_empty' requires a declared "
                             "empty_min_visibility (minimum local fringe visibility of the empty "
                             "hologram; PROJECT_INPUT item 19)")
        vmin = float(empty_min_visibility)
        if not (np.isfinite(vmin) and 0.0 < vmin <= 1.0):
            raise ValueError(f"empty_min_visibility must lie in (0, 1]; got {empty_min_visibility!r}")
    elif empty_hologram is not None:
        raise ValueError("empty_hologram given but reference_correction='none': declare the correction")
    elif empty_min_visibility is not None:
        raise ValueError("empty_min_visibility applies only to reference_correction='divide_empty'")

    qs = carrier.sideband_centre_cycles_per_A
    sign_check = _sign_check(object_hologram, qs)
    if sign_check.startswith("CONJUGATE") and not trap_demonstration:
        raise ValueError(f"sideband sign check: {sign_check}; the located sideband is the conjugate "
                         f"of the declared phi_o - phi_r sideband ({carrier.search.sideband_declaration!r}),"
                         f" which flips the sign of the phase and of every height (audit A2 M1)")
    W = sideband_mask(grid, qs, mask)
    w_obj = _demodulate(object_hologram.intensity, grid, qs, W)
    phase_raw = np.angle(w_obj)
    amp_raw = np.abs(w_obj)
    w_emp = None
    valid = np.ones(grid.shape, dtype=bool)
    reference_masks = []
    for name, h in (("object", object_hologram), ("empty", empty_hologram)):
        vm = h.metadata.get("valid_mask") if h is not None else None
        if vm is not None:
            vm = np.asarray(vm, dtype=bool)
            if vm.shape != grid.shape:
                raise ValueError(f"{name} hologram valid_mask is not on the grid")
            valid &= vm
            reference_masks.append(f"{name} hologram reference valid_mask ({int((~vm).sum())} px)")
    vis_median = None
    if reference_correction == "divide_empty":
        w_emp = _demodulate(empty_hologram.intensity, grid, qs, W)
        W_dc = _mask_values(grid, (0.0, 0.0), mask)            # the same mask centred on q = 0
        dc = np.real(np.fft.ifft2(np.fft.fft2(empty_hologram.intensity) * W_dc))
        vis = np.zeros(grid.shape)
        pos = dc > 0.0
        vis[pos] = 2.0 * np.abs(w_emp[pos]) / dc[pos]
        undefined = ~(vis >= vmin) | (amp_raw == 0.0)
        w = np.full(grid.shape, np.nan + 1j * np.nan)
        w[~undefined] = w_obj[~undefined] / w_emp[~undefined]
        what = (f"an empty-hologram sideband visibility 2|w_empty|/D below the declared minimum "
                f"{vmin:g} (or a zero object sideband)")
        if (~undefined).any():
            vis_median = float(np.median(vis[~undefined]))
    else:
        undefined = amp_raw == 0.0
        w = np.where(undefined, np.nan + 1j * np.nan, w_obj)
        what = "object-hologram sideband amplitude exactly 0 (phase undefined)"
    n_undef = int(undefined.sum())
    if n_undef:
        warnings.warn(f"{n_undef} of {undefined.size} pixels have {what}: phase and amplitude set "
                      f"to NaN and valid_mask False there (audit A2 m1)", RuntimeWarning,
                      stacklevel=2)
    valid &= ~undefined
    phase = np.angle(w)
    amp = np.abs(w)
    regions = None
    if unwrapping == "itoh_raster":
        unwrapped, regions = unwrap_itoh_raster(phase, valid, return_regions=True)
    else:
        unwrapped = None
    R = mask.radius_cycles_per_A
    qmag = float(np.hypot(*qs))
    params = {"carrier": carrier.as_record(), "mask": mask.as_record(),
              "sideband_declaration": carrier.search.sideband_declaration,
              "trap_demonstration": trap_demonstration,
              "reference_correction": reference_correction, "unwrapping": unwrapping,
              "zero_padding": "none", "real_space_window": "none", "ramp_removal": "none (never implicit)",
              "fft": "numpy.fft.fft2, kernel exp(-2 pi i q.r), unshifted layout",
              "object_hologram_sha256": object_hologram.sha256,
              "empty_hologram_sha256": empty_hologram.sha256 if empty_hologram is not None else None,
              "grid": grid.as_record(), "mask_radius_over_carrier": R / qmag,
              "centre_band_clearance_cycles_per_A": qmag - R,
              "resolution_definition": "1/R (SM12: about three fringe spacings for R = |q_c|/3)",
              "validity": {"empty_min_visibility": (vmin if reference_correction == "divide_empty"
                                                    else None),
                           "visibility_median_valid": vis_median,
                           "n_invalid_amplitude": n_undef, "reference_masks": reference_masks,
                           "n_invalid_total": int((~valid).sum())},
              "unwrapping_regions": int(regions.max()) if regions is not None else None,
              "numpy_version": np.__version__}
    return SidebandResult(phase_raw, phase, unwrapped, amp, amp_raw, w_obj, w_emp, W, carrier, mask,
                          reference_correction, unwrapping, 1.0 / R, qmag / R,
                          sign_check, grid, valid, params, regions)


# ------------------------------------------------------------------------------------------------
# noise prediction (SM12, DERIVED_HERE)
# ------------------------------------------------------------------------------------------------

def sideband_phase_noise(fringe_contrast: float, counts_per_px: float, mask: np.ndarray) -> dict:
    """Predicted phase standard deviation sigma_phi = sqrt(2)/(mu sqrt(N)) of ONE hologram (no
    reference division; dividing by an equally noisy empty hologram multiplies it by sqrt(2)).

    This function supplies N for a given mask; sigma_phi itself is computed by the canonical
    reflection_holo.quantification.noise.phase_noise_sigma_rad (SM12), whose docstring defines N.
    N = counts_per_px * A_eff, the counts in the effective real-space resolution area
    A_eff = n_pix / sum(W^2) pixels, i.e. the reciprocal of the W^2-weighted mask area (for a
    top-hat disc of radius R: 1/(pi R^2)).
    Derivation (DERIVED_HERE): I = N_px (1 + mu cos(...)) gives a sideband of modulus N_px mu/2; white
    Poisson noise of variance N_px per pixel gives a complex sideband noise of variance
    N_px sum(W^2)/n_pix; the phase variance is that over 2 |sideband|^2.
    """
    mu = float(fringe_contrast)
    n = float(counts_per_px)
    if not (0 < mu <= 1) or not n > 0:
        raise ValueError("fringe_contrast must be in (0, 1] and counts_per_px > 0")
    W = np.asarray(mask, dtype=float)
    f_eff = float(np.sum(W ** 2)) / W.size
    area_px = 1.0 / f_eff
    N = n * area_px
    return {"sigma_phi_rad": phase_noise_sigma_rad(contrast_mu=mu, counts_N=N), "N_counts": N,
            "effective_area_px": area_px, "fringe_contrast": mu, "counts_per_px": n}

