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
   declared search disc around the expected sideband, outside a declared exclusion disc about q = 0
   (argmax taken in centred fftshift order, the calculator's tie-break for exactly equal bins).
   Sub-pixel refinement (declared): "none" (integer bin) or "dft_ratio": along each axis, the exact
   single-tone interpolation from the complex ratio rho = X[k +- 1]/X[k] of the peak bin and its larger
   neighbour, u = (1 - rho)/(1 - rho z^-+1), z = exp(2 pi i/n), delta = n arg(u)/(2 pi) bins
   (DERIVED_HERE from the DFT of a complex exponential; exact for one noiseless tone; biased by the
   leakage of the conjugate sideband and the centre band, and noisy under shot noise).
2. Sideband selection: the sideband at q_s holds u_o u_r^*, i.e. phi_o - phi_r, when q_s = -q_ref for a
   reference u_r ~ exp(+2 pi i q_ref.r) (numpy FFT sign, exp(+ik.r) convention; physics_conventions).
   Which of the two sidebands this is in an experiment is a declared input (PROJECT_INPUT items 10 and
   16); for simulated holograms the choice is checked against the recorded reference carrier and the
   outcome is stored in ``SidebandResult.sideband_sign_check``.
3. Mask: a disc of declared radius R (cycles/A) centred on the refined q_s, apodisation "none"
   (top-hat) or "hann" (0.5 (1 + cos(pi r/R)) for r < R). The disc must not contain q = 0 and must lie
   inside the Nyquist band; otherwise the call fails.
4. Demodulation: integer-bin roll of the masked spectrum to q = 0, inverse FFT, then multiplication by
   exp(-2 pi i (q_s - q_bin).r) for the sub-pixel remainder. The complex result is |u_o||u_r|
   exp(i(phi_o - phi_r)) with numpy's normalisation. No zero padding, no real-space window.
5. Reference correction (declared): "none", or "divide_empty": w_obj / w_empty with the same carrier
   and mask applied to the empty hologram (removes the residual carrier, the reference's residual
   phase and the mask's own transfer).
6. Unwrapping (declared): "none" or "itoh_raster": 1-D Itoh unwrapping down column 0, then along each
   row from its unwrapped first pixel. Path-following, NOT residue-aware: it fails at phase
   singularities and in low-amplitude or noisy regions. The raw wrapped phase is always kept.
7. NO ramp or plane is removed by the reconstruction. ``fit_phase_plane`` / ``subtract_phase_plane``
   are separate, explicit calls with a declared fitting region; their inputs are never modified.

Resolution (SM12): 1/R, reported in A and in fringe spacings (|q_s|/R; 3 for R = |q_s|/3).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from reflection_holo.constants import TWO_PI
from reflection_holo.optics.fields import Grid, Hologram, _require_2vector, sha256_array

SUBPIXEL_METHODS = ("none", "dft_ratio")
MASK_SHAPES = ("disc",)
APODISATIONS = ("none", "hann")
REFERENCE_CORRECTIONS = ("none", "divide_empty")
UNWRAPPINGS = ("none", "itoh_raster")


def wrap_to_pi(x):
    """Wrap to (-pi, +pi] (same expression as the calculator's wrap_to_pi)."""
    return -((-np.asarray(x, float) + np.pi) % TWO_PI - np.pi)


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

    sideband_guess_cycles_per_A   expected position of the phi_o - phi_r sideband (= -q_ref)
    search_radius_cycles_per_A    search disc about the guess (inf: whole plane)
    exclusion_radius_cycles_per_A disc about q = 0 excluded from the search (centre band)
    subpixel                      "none" or "dft_ratio" (module docstring, step 1)
    """

    sideband_guess_cycles_per_A: tuple[float, float]
    search_radius_cycles_per_A: float
    exclusion_radius_cycles_per_A: float
    subpixel: str

    def __post_init__(self):
        object.__setattr__(self, "sideband_guess_cycles_per_A",
                           _require_2vector("sideband_guess_cycles_per_A", self.sideband_guess_cycles_per_A))
        object.__setattr__(self, "search_radius_cycles_per_A",
                           _positive("search_radius_cycles_per_A", self.search_radius_cycles_per_A, allow_inf=True))
        v = self.exclusion_radius_cycles_per_A
        if v is None or not np.isfinite(float(v)) or float(v) < 0:
            raise ValueError("exclusion_radius_cycles_per_A must be a finite value >= 0")
        object.__setattr__(self, "exclusion_radius_cycles_per_A", float(v))
        if self.subpixel not in SUBPIXEL_METHODS:
            raise ValueError(f"subpixel must be one of {SUBPIXEL_METHODS}; got {self.subpixel!r}")

    def as_record(self) -> dict:
        return {"sideband_guess_cycles_per_A": list(self.sideband_guess_cycles_per_A),
                "search_radius_cycles_per_A": self.search_radius_cycles_per_A,
                "exclusion_radius_cycles_per_A": self.exclusion_radius_cycles_per_A,
                "subpixel": self.subpixel}


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
    mag = np.where(sel, np.abs(F), -1.0)
    # argmax in centred (fftshift) order, as the calculator's _sideband_wave: an exact tie (the
    # Hermitian pair +-q of a real hologram, when the region contains both) goes to the more negative
    # axis-0 frequency, then the more negative axis-1 frequency.
    ks = np.unravel_index(int(np.argmax(np.fft.fftshift(mag))), mag.shape)
    n0, n1 = grid.shape
    k = (int((ks[0] - n0 // 2) % n0), int((ks[1] - n1 // 2) % n1))
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
    q0, q1 = grid.frequencies_cycles_per_A()
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

def unwrap_itoh_raster(phase: np.ndarray) -> np.ndarray:
    """1-D Itoh unwrapping down column 0, then along every row (see module docstring, step 6)."""
    p = np.asarray(phase, dtype=float)
    col0 = np.unwrap(p[:, 0])
    rows = np.unwrap(p, axis=1)
    return rows + (col0 - p[:, 0])[:, None]


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
    parameters: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        for name in ("wrapped_phase_raw", "wrapped_phase", "unwrapped_phase", "amplitude",
                     "amplitude_raw", "object_sideband", "empty_sideband", "mask"):
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
                         unwrapping: str) -> SidebandResult:
    """Sideband reconstruction with every processing choice declared (module docstring).

    The carrier must come from ``locate_carrier`` on an empty or flat-region hologram with the same
    pixel sizes, axes and plane (a crop of different shape is allowed; the sideband centre is
    transferred in cycles/A). Returns phases only; heights belong to quantification/.
    """
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
    grid = object_hologram.grid
    grid.assert_same_sampling(carrier.grid, "object hologram and carrier-location hologram")
    if reference_correction == "divide_empty":
        if empty_hologram is None:
            raise ValueError("reference_correction='divide_empty' requires empty_hologram")
        grid.assert_same(empty_hologram.grid, "object and empty holograms")
        if empty_hologram.content == "object":
            raise ValueError("the reference-correction hologram must be empty or flat_region")
    elif empty_hologram is not None:
        raise ValueError("empty_hologram given but reference_correction='none': declare the correction")

    qs = carrier.sideband_centre_cycles_per_A
    W = sideband_mask(grid, qs, mask)
    w_obj = _demodulate(object_hologram.intensity, grid, qs, W)
    phase_raw = np.angle(w_obj)
    amp_raw = np.abs(w_obj)
    w_emp = None
    if reference_correction == "divide_empty":
        w_emp = _demodulate(empty_hologram.intensity, grid, qs, W)
        with np.errstate(divide="ignore", invalid="ignore"):
            w = w_obj / w_emp
    else:
        w = w_obj
    phase = np.angle(w)
    amp = np.abs(w)
    unwrapped = unwrap_itoh_raster(phase) if unwrapping == "itoh_raster" else None
    R = mask.radius_cycles_per_A
    qmag = float(np.hypot(*qs))
    params = {"carrier": carrier.as_record(), "mask": mask.as_record(),
              "reference_correction": reference_correction, "unwrapping": unwrapping,
              "zero_padding": "none", "real_space_window": "none", "ramp_removal": "none (never implicit)",
              "fft": "numpy.fft.fft2, kernel exp(-2 pi i q.r), unshifted layout",
              "object_hologram_sha256": object_hologram.sha256,
              "empty_hologram_sha256": empty_hologram.sha256 if empty_hologram is not None else None,
              "grid": grid.as_record(), "mask_radius_over_carrier": R / qmag,
              "centre_band_clearance_cycles_per_A": qmag - R,
              "resolution_definition": "1/R (SM12: about three fringe spacings for R = |q_c|/3)",
              "numpy_version": np.__version__}
    return SidebandResult(phase_raw, phase, unwrapped, amp, amp_raw, w_obj, w_emp, W, carrier, mask,
                          reference_correction, unwrapping, 1.0 / R, qmag / R,
                          _sign_check(object_hologram, qs), grid, params)


# ------------------------------------------------------------------------------------------------
# noise prediction (SM12, DERIVED_HERE)
# ------------------------------------------------------------------------------------------------

def sideband_phase_noise(fringe_contrast: float, counts_per_px: float, mask: np.ndarray) -> dict:
    """Predicted phase standard deviation sigma_phi = sqrt(2)/(mu sqrt(N)) of ONE hologram (no
    reference division; dividing by an equally noisy empty hologram multiplies it by sqrt(2)).

    N is the number of counts in the effective resolution area A_eff = n_pix / sum(W^2) pixels, i.e.
    the reciprocal of the W^2-weighted mask area (for a top-hat disc of radius R: 1/(pi R^2)).
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
    return {"sigma_phi_rad": float(np.sqrt(2.0) / (mu * np.sqrt(N))), "N_counts": N,
            "effective_area_px": area_px, "fringe_contrast": mu, "counts_per_px": n}

