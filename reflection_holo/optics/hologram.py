"""Off-axis hologram formation from explicitly specified object and reference waves.

Source map SM12 (hologram I = |u_o + u_r|^2; P07 para 56, Eqs. (18)-(26); SECTION_READ for the sideband
rule, DERIVED_HERE for the noise formula), SM13 (ensemble average after squaring, object and
reference sharing each realisation; METADATA_VERIFIED/SECTION_READ), SM21 (R1: a direct vacuum
reference, Hitachi patent US 4,998,788; SECTION_READ), SM22 (R2 reading of the P01 abstract;
DERIVED_HERE). Model assumption B5 (the reference is one of the idealisations R1, R2, R3; ASSUMPTION)
and B8 (no charging; the charging option below is the declared alternative).

    I(r) = |u_o(r) + u_r(r)|^2
         = |u_o|^2 + |u_r|^2 + 2 |u_o| |u_r| cos(phi_o - phi_r)                    (docs/03 section 6)

Reference-wave models (selectable by name; every parameter is REQUIRED, no defaults):

* R1  vacuum plane wave  u_r = A exp(i (2 pi q_c.r + phi_rel)).
      q_c (cycles/A, ordered (axis 0, axis 1)) is the reference tilt relative to the object wave in
      the exp(+ik.r) convention, i.e. the MEASURED carrier of PROJECT_INPUT item 16 including its
      sign (which side the reference comes from, items 10 and 16). The intrinsic 2 theta_ext
      inclination of a vacuum reference and its compensation are NOT modelled here: q_c is the
      carrier after compensation. The declared passage of the reference through the dark-field
      objective aperture ("second_aperture_hole", "condenser_biprism_pretilt", "no_aperture") is
      recorded (docs/05 section 5 item 3; L1 inference I6); it does not change the field.
* R2  self-reference     u_r(r) = s u_o(r + shift) exp(i (2 pi q_c.r + phi_rel)).
      The reference at r is the object field of the region displaced by ``shift`` (an integer number
      of pixels on each axis; no periodic wrap: pixels whose source lies outside the field are set
      to zero and flagged in ``metadata["valid_mask"]``). The reconstruction then gives
      phi(r) - phi(r + shift): every feature appears at its own position and, with the opposite
      sign, displaced by -shift (the twin of docs/03 section 6).
* R3  plane wave with residual tilt and curvature, given explicitly:
      u_r = A exp(i (2 pi (q_c + t).r + phi_rel + c00 d0^2 + 2 c01 d0 d1 + c11 d1^2)),
      d = r - r_centre. Long-wavelength object phase is entangled with this residual unless an empty
      hologram recorded with the same reference is used for correction (PROJECT_INPUT item 17).

``relative_phase_rad`` is a free simulation parameter; it is NOT evidence that the hardware can set
the phase (docs/05 section 5 item 3).

Instrument artefacts (docs/05 section 5 item 5) are declared through ``ArtefactOptions`` (no defaults):
the biprism's Fresnel fringes / finite overlap width and specimen drift raise NotImplementedError when
requested; specimen charging is implemented as an explicit static phase map added to the object branch
(B8, PROJECT_INPUT item 22); a charging phase that drifts during the exposure is an ensemble over time
and must be built with ``ensemble_hologram_intensity``.

Detector: Poisson noise at a declared dose (mean counts per pixel, PROJECT_INPUT item 6) with a
declared integer seed; gain 1 count per electron; MTF NOT IMPLEMENTED.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np

from reflection_holo.constants import TWO_PI
from reflection_holo.optics.fields import Grid, Hologram, Wave, _require_2vector, sha256_array

REFERENCE_MODELS = ("R1", "R2", "R3")
APERTURE_PASSAGES = ("second_aperture_hole", "condenser_biprism_pretilt", "no_aperture")


def _require_finite(name: str, value, *, positive: bool = False) -> float:
    if value is None:
        raise ValueError(f"{name} is required and was None (no default is substituted)")
    v = float(value)
    if not np.isfinite(v):
        raise ValueError(f"{name} must be finite; got {value!r}")
    if positive and not v > 0:
        raise ValueError(f"{name} must be > 0; got {value!r}")
    return v


def _check_carrier(grid: Grid, carrier) -> tuple[float, float]:
    q = _require_2vector("carrier_cycles_per_A (PROJECT_INPUT item 16)", carrier, allow_zero=False)
    nyq = grid.nyquist_cycles_per_A
    if abs(q[0]) >= nyq[0] or abs(q[1]) >= nyq[1]:
        raise ValueError(f"carrier {q} cycles/A is not below the Nyquist frequency {nyq} of the grid")
    return q


# ------------------------------------------------------------------------------------------------
# object-branch helpers
# ------------------------------------------------------------------------------------------------

def vacuum_object_wave(grid: Grid, *, amplitude: float, realisation: int | None) -> Wave:
    """Uniform object-branch wave (no specimen), used to form an EMPTY hologram."""
    a = _require_finite("amplitude", amplitude, positive=True)
    return Wave(np.full(grid.shape, a, dtype=np.complex128), grid, "vacuum object branch", realisation,
                {"model": "vacuum", "amplitude": a})


# ------------------------------------------------------------------------------------------------
# reference-wave models
# ------------------------------------------------------------------------------------------------

def reference_r1_vacuum_plane_wave(grid: Grid, *, carrier_cycles_per_A, amplitude: float,
                                   relative_phase_rad: float, aperture_passage: str,
                                   realisation: int | None) -> Wave:
    """R1: vacuum plane-wave reference (SM21; B5). All arguments required; see module docstring."""
    if not isinstance(grid, Grid):
        raise TypeError("grid must be a Grid")
    q = _check_carrier(grid, carrier_cycles_per_A)
    a = _require_finite("amplitude", amplitude, positive=True)
    ph = _require_finite("relative_phase_rad", relative_phase_rad)
    if aperture_passage not in APERTURE_PASSAGES:
        raise ValueError(f"aperture_passage must be one of {APERTURE_PASSAGES} (docs/05 section 5 "
                         f"item 3); got {aperture_passage!r}")
    r0, r1 = grid.coordinates_A()
    data = a * np.exp(1j * (TWO_PI * (q[0] * r0 + q[1] * r1) + ph))
    meta = {"reference_model": "R1", "carrier_cycles_per_A": list(q), "amplitude": a,
            "relative_phase_rad": ph, "aperture_passage": aperture_passage,
            "effective_carrier_cycles_per_A": list(q),
            "labels": {"carrier": "PROJECT_INPUT item 16", "model": "ASSUMPTION B5; SM21",
                       "relative_phase": "simulation parameter only"}}
    return Wave(data, grid, "reference R1", realisation, meta)


def reference_r2_self_reference(object_wave: Wave, *, shift_A, carrier_cycles_per_A,
                                amplitude_scale: float, relative_phase_rad: float) -> Wave:
    """R2: self-reference from the displaced region of the same object field (SM22, DERIVED_HERE).

    u_r(r) = amplitude_scale * u_o(r + shift) * exp(i (2 pi q_c.r + phi_rel)); the shift must be an
    integer number of pixels on each axis (checked to 1e-9 pixel); no periodic wrap is applied.
    """
    if not isinstance(object_wave, Wave):
        raise TypeError("object_wave must be a Wave")
    grid = object_wave.grid
    s = _require_2vector("shift_A", shift_A, allow_zero=False)
    q = _check_carrier(grid, carrier_cycles_per_A)
    sc = _require_finite("amplitude_scale", amplitude_scale, positive=True)
    ph = _require_finite("relative_phase_rad", relative_phase_rad)
    npx = []
    for ax in (0, 1):
        f = s[ax] / grid.pixel_size_A[ax]
        if abs(f - round(f)) > 1e-9:
            raise ValueError(f"shift_A[{ax}] = {s[ax]} A is not an integer number of pixels "
                             f"({grid.pixel_size_A[ax]} A); sub-pixel shifts are not implemented")
        npx.append(int(round(f)))
        if abs(npx[-1]) >= grid.shape[ax]:
            raise ValueError("shift larger than the field")
    n0, n1 = grid.shape
    src = np.zeros(grid.shape, dtype=np.complex128)
    valid = np.zeros(grid.shape, dtype=bool)
    # destination index i receives source index i + shift, when that lies inside the field
    d0 = slice(max(0, -npx[0]), min(n0, n0 - npx[0]))
    d1 = slice(max(0, -npx[1]), min(n1, n1 - npx[1]))
    s0 = slice(d0.start + npx[0], d0.stop + npx[0])
    s1 = slice(d1.start + npx[1], d1.stop + npx[1])
    src[d0, d1] = object_wave.data[s0, s1]
    valid[d0, d1] = True
    r0, r1 = grid.coordinates_A()
    data = sc * src * np.exp(1j * (TWO_PI * (q[0] * r0 + q[1] * r1) + ph))
    meta = {"reference_model": "R2", "shift_A": list(s), "shift_px": npx,
            "carrier_cycles_per_A": list(q), "effective_carrier_cycles_per_A": list(q),
            "amplitude_scale": sc, "relative_phase_rad": ph, "valid_mask": valid,
            "source_object_label": object_wave.label,
            "labels": {"model": "ASSUMPTION B5; R2 reading of P01 is DERIVED_HERE (SM22)",
                       "carrier": "PROJECT_INPUT item 16", "shift": "PROJECT_INPUT item 16",
                       "relative_phase": "simulation parameter only"}}
    return Wave(data, grid, "reference R2", object_wave.realisation, meta)


def reference_r3_curved_tilted(grid: Grid, *, carrier_cycles_per_A, amplitude: float,
                               relative_phase_rad: float, residual_tilt_cycles_per_A,
                               residual_curvature_rad_per_A2, curvature_centre_A,
                               realisation: int | None) -> Wave:
    """R3: plane-wave reference with an explicit residual tilt and quadratic phase (B5; no source).

    residual_curvature_rad_per_A2 = (c00, c01, c11): phase c00 d0^2 + 2 c01 d0 d1 + c11 d1^2 with
    d = r - curvature_centre_A. All arguments required.
    """
    if not isinstance(grid, Grid):
        raise TypeError("grid must be a Grid")
    q = _check_carrier(grid, carrier_cycles_per_A)
    t = _require_2vector("residual_tilt_cycles_per_A", residual_tilt_cycles_per_A)
    qe = _check_carrier(grid, (q[0] + t[0], q[1] + t[1]))
    a = _require_finite("amplitude", amplitude, positive=True)
    ph = _require_finite("relative_phase_rad", relative_phase_rad)
    if residual_curvature_rad_per_A2 is None:
        raise ValueError("residual_curvature_rad_per_A2 is required")
    c = np.asarray(residual_curvature_rad_per_A2, dtype=float)
    if c.shape != (3,) or not np.all(np.isfinite(c)):
        raise ValueError("residual_curvature_rad_per_A2 must be (c00, c01, c11), finite")
    rc = _require_2vector("curvature_centre_A", curvature_centre_A)
    r0, r1 = grid.coordinates_A()
    d0, d1 = r0 - rc[0], r1 - rc[1]
    quad = c[0] * d0 ** 2 + 2.0 * c[1] * d0 * d1 + c[2] * d1 ** 2
    data = a * np.exp(1j * (TWO_PI * (qe[0] * r0 + qe[1] * r1) + ph + quad))
    meta = {"reference_model": "R3", "carrier_cycles_per_A": list(q), "residual_tilt_cycles_per_A": list(t),
            "effective_carrier_cycles_per_A": list(qe),
            "residual_curvature_rad_per_A2": c.tolist(), "curvature_centre_A": list(rc),
            "amplitude": a, "relative_phase_rad": ph,
            "labels": {"model": "ASSUMPTION B5 (R3 has no source)", "carrier": "PROJECT_INPUT item 16",
                       "residual": "PROJECT_INPUT item 17", "relative_phase": "simulation parameter only"}}
    return Wave(data, grid, "reference R3", realisation, meta)


def make_reference(model: str, **kwargs) -> Wave:
    """Select a reference model by name ("R1", "R2", "R3"); keyword arguments as the model function."""
    if model == "R1":
        return reference_r1_vacuum_plane_wave(**kwargs)
    if model == "R2":
        return reference_r2_self_reference(**kwargs)
    if model == "R3":
        return reference_r3_curved_tilted(**kwargs)
    raise ValueError(f"unknown reference model {model!r}; expected one of {REFERENCE_MODELS}")


# ------------------------------------------------------------------------------------------------
# artefact declaration
# ------------------------------------------------------------------------------------------------

@dataclass(frozen=True, eq=False)
class ArtefactOptions:
    """Declared instrument artefacts (docs/05 section 5 item 5). Every field is required.

    biprism_fresnel_fringes  None = not modelled; anything else raises NotImplementedError
    drift                    None = not modelled; anything else raises NotImplementedError
    charging_phase_rad       None = no charging (ASSUMPTION B8), or a real array on the grid added to
                             the object-branch phase (static within the exposure; PROJECT_INPUT 22)
    """

    biprism_fresnel_fringes: Any
    drift: Any
    charging_phase_rad: np.ndarray | None

    def check(self, grid: Grid) -> None:
        if self.biprism_fresnel_fringes is not None:
            raise NotImplementedError("biprism Fresnel fringes and finite overlap width are declared "
                                      "but not implemented (PROJECT_INPUT item 17)")
        if self.drift is not None:
            raise NotImplementedError("specimen drift during the exposure (coherent envelope loss) is "
                                      "declared but not implemented (PROJECT_INPUT item 6)")
        if self.charging_phase_rad is not None:
            c = np.asarray(self.charging_phase_rad)
            if c.shape != grid.shape or np.iscomplexobj(c) or not np.all(np.isfinite(c)):
                raise ValueError("charging_phase_rad must be a finite real array on the hologram grid")

    def as_record(self) -> dict:
        rec = {"biprism_fresnel_fringes": "not modelled", "drift": "not modelled"}
        if self.charging_phase_rad is None:
            rec["charging"] = "none (ASSUMPTION B8)"
        else:
            c = np.asarray(self.charging_phase_rad, dtype=float)
            rec["charging"] = {"static_phase_map_sha256": sha256_array(c),
                               "min_rad": float(c.min()), "max_rad": float(c.max()),
                               "label": "PROJECT_INPUT item 22"}
        return rec


# ------------------------------------------------------------------------------------------------
# intensity formation
# ------------------------------------------------------------------------------------------------

def _pair_intensity(object_wave: Wave, reference_wave: Wave, artefacts: ArtefactOptions) -> np.ndarray:
    if not isinstance(object_wave, Wave) or not isinstance(reference_wave, Wave):
        raise TypeError("object_wave and reference_wave must be Wave instances")
    object_wave.grid.assert_same(reference_wave.grid, "object and reference waves")
    if object_wave.realisation != reference_wave.realisation:
        raise ValueError(f"object (realisation {object_wave.realisation}) and reference (realisation "
                         f"{reference_wave.realisation}) must share the same realisation (SM13)")
    u_o = object_wave.data
    if artefacts.charging_phase_rad is not None:
        u_o = u_o * np.exp(1j * np.asarray(artefacts.charging_phase_rad, dtype=float))
    return np.abs(u_o + reference_wave.data) ** 2


def _reference_record(reference_wave: Wave) -> dict:
    return {k: v for k, v in reference_wave.metadata.items() if k != "valid_mask"}


def hologram_intensity(object_wave: Wave, reference_wave: Wave, *, artefacts: ArtefactOptions,
                       content: str) -> Hologram:
    """Coherent hologram I = |u_o + u_r|^2 of one realisation (SM12). ``content`` is required."""
    if not isinstance(artefacts, ArtefactOptions):
        raise TypeError("artefacts must be an ArtefactOptions (declare every artefact explicitly)")
    artefacts.check(object_wave.grid)
    intensity = _pair_intensity(object_wave, reference_wave, artefacts)
    meta = {"formation": "coherent |u_o + u_r|^2", "n_realisations": 1,
            "object_label": object_wave.label, "reference": _reference_record(reference_wave),
            "reference_carrier_cycles_per_A": reference_wave.metadata.get("effective_carrier_cycles_per_A"),
            "artefacts": artefacts.as_record(), "grid": object_wave.grid.as_record(),
            "object_sha256": sha256_array(object_wave.data),
            "reference_sha256": sha256_array(reference_wave.data)}
    if "valid_mask" in reference_wave.metadata:
        meta["valid_mask"] = reference_wave.metadata["valid_mask"]
    return Hologram(intensity, object_wave.grid, content, meta, None)


def ensemble_hologram_intensity(realisations: Sequence[tuple[Wave, Wave]], *,
                                artefacts: ArtefactOptions, content: str) -> Hologram:
    """Partially coherent hologram: mean over realisations of |u_o^k + u_r^k|^2 (SM13).

    Each element of ``realisations`` is one (object, reference) pair sharing a realisation; the
    average is taken AFTER squaring. Complex waves are never averaged. Realisation indices, when set,
    must agree within a pair and be distinct across pairs.
    """
    if not isinstance(artefacts, ArtefactOptions):
        raise TypeError("artefacts must be an ArtefactOptions")
    pairs = list(realisations)
    if not pairs:
        raise ValueError("at least one realisation is required")
    grid = pairs[0][0].grid
    artefacts.check(grid)
    seen = set()
    acc = np.zeros(grid.shape, dtype=np.float64)
    for k, pair in enumerate(pairs):
        if len(pair) != 2:
            raise ValueError(f"realisation {k}: expected an (object, reference) pair")
        u_o, u_r = pair
        grid.assert_same(u_o.grid, f"realisation {k}")
        acc += _pair_intensity(u_o, u_r, artefacts)
        if u_o.realisation is not None:
            if u_o.realisation in seen:
                raise ValueError(f"realisation index {u_o.realisation} used twice")
            seen.add(u_o.realisation)
    intensity = acc / len(pairs)
    carriers = {tuple(p[1].metadata.get("effective_carrier_cycles_per_A") or ()) for p in pairs}
    meta = {"formation": "incoherent mean over realisations of |u_o^k + u_r^k|^2 (after squaring)",
            "n_realisations": len(pairs),
            "reference_models": sorted({str(p[1].metadata.get("reference_model")) for p in pairs}),
            "reference_carrier_cycles_per_A": (list(next(iter(carriers))) if len(carriers) == 1
                                               and next(iter(carriers)) else None),
            "artefacts": artefacts.as_record(), "grid": grid.as_record()}
    return Hologram(intensity, grid, content, meta, None)


# ------------------------------------------------------------------------------------------------
# detector
# ------------------------------------------------------------------------------------------------

def apply_poisson_noise(holograms: Sequence[Hologram], *, dose_e_per_px: float, seed: int) -> list[Hologram]:
    """Poisson detector noise at a declared dose (mean counts per pixel; gain 1 count/electron).

    counts = Poisson(I / mean(I) * dose), drawn from ``numpy.random.default_rng(seed)`` for the
    holograms IN THE ORDER GIVEN (one generator for the whole list, so the draw order is part of the
    record). Both arguments are required: the dose is PROJECT_INPUT item 6. Returns new Hologram
    objects whose ``noiseless_intensity`` keeps the input intensity. MTF: NOT IMPLEMENTED.
    """
    if isinstance(holograms, Hologram):
        raise TypeError("pass a list of holograms (the draw order is recorded)")
    hs = list(holograms)
    if not hs:
        raise ValueError("no holograms given")
    dose = _require_finite("dose_e_per_px (PROJECT_INPUT item 6)", dose_e_per_px, positive=True)
    if seed is None or isinstance(seed, bool) or int(seed) != seed or seed < 0:
        raise ValueError(f"seed must be an explicit non-negative integer; got {seed!r}")
    rng = np.random.default_rng(int(seed))
    out = []
    for k, h in enumerate(hs):
        if not isinstance(h, Hologram):
            raise TypeError("holograms must be Hologram instances")
        mean = float(h.intensity.mean())
        if not mean > 0:
            raise ValueError("hologram mean intensity must be > 0 to scale to a dose")
        counts = rng.poisson(h.intensity / mean * dose).astype(float)
        meta = dict(h.metadata)
        meta["detector"] = {"noise": "Poisson", "dose_e_per_px": dose, "seed": int(seed),
                            "draw_index": k, "n_holograms_in_draw": len(hs),
                            "generator": "numpy.random.default_rng (PCG64)",
                            "numpy_version": np.__version__, "gain_counts_per_e": 1.0,
                            "mtf": "NOT IMPLEMENTED", "label_dose": "PROJECT_INPUT item 6"}
        out.append(Hologram(counts, h.grid, h.content, meta, h.intensity))
    return out


def fringe_contrast(amplitude_object: float, amplitude_reference: float) -> float:
    """Ideal fringe contrast mu = 2 |u_o| |u_r| / (|u_o|^2 + |u_r|^2) of two uniform waves."""
    a = _require_finite("amplitude_object", amplitude_object, positive=True)
    b = _require_finite("amplitude_reference", amplitude_reference, positive=True)
    return 2.0 * a * b / (a * a + b * b)
