"""Continuum oxide overlayer on Si(001) (PROJECT_INPUT item 12; report E4 after L8 section 8 as
corrected by the adversarial review E9, M1-M5; numbers cited as lines of
tools/review/e9_recompute_output.txt, "out:N"; corrections after the audit A8, report X4).

Model (every physical parameter is a REQUIRED field of :class:`ContinuumOxideSpec` with its own
label; nothing has a default):

* a uniform continuum layer of complex potential V_ox + i V'_ox on every terrace, FOLLOWING THE
  SURFACE (one layer per terrace; never a function of the surface-normal coordinate alone: E6 m12,
  E9 m5). V'_ox >= 0 is the electronic absorption of the layer (a model value, not a bound: E9 M1);
  V'_ox = 0 must carry an ASSUMPTION (or TEST_ONLY) label (it is not a measurement).
* GROWN from the crystal (E9 M2, section 3 item 4): Si atoms are conserved, so a layer of thickness
  t on a terrace whose pre-oxidation SURFACE is the plane x = H_s consumes a depth f t of Si,
        f = (rho_ox / M_SiO2) / (rho_Si / M_Si),   rho_Si = 8 M_Si / (N_A a^3)
  (f = 0.4415 at 2.20 g/cm^3 and a = 5.4309 A, out:143): the oxide/Si interface lies at
  x_i = H_s - f t and the top of the layer at x_t = H_s + (1 - f) t.
* an optional amorphous-Si layer (milling damage left under the oxide, E9 M5) of thickness t_a
  between x_c = x_i - t_a and x_i, continuum potential V_a + i V'_a (both required when t_a > 0).
  t_a = 0 is accepted with any evidence label, a measured 0 (PROJECT_INPUT: below the witness
  measurement's detection limit) included (audit A8 M1); a missing or blank label is refused. Its
  density is taken equal to that of the crystal it replaced (ASSUMPTION; E9 out:148-149 use
  0.98-0.99).
* the crystal below x_c. An ATOMISTIC crystal loses its top N whole (001) layers; N (the consumed
  layer count) is a REQUIRED integer and must be the whole-layer count nearest to the continuum
  depth: |N a/4 - (f t + t_a)| <= a/8 (asserted). The distance of f t + t_a from the rounding
  boundary (N +- 1/2) a/4 is recorded; closer than MIN_ROUNDING_MARGIN_LAYERS the count (and at
  <110> its parity, i.e. the terrace type at a buried a/4 step, E9 section 3 item 2) depends on
  digits of the density or thickness below their stated precision, and the specification is
  REFUSED unless ``rounding_boundary_acknowledged`` is True (audit A8 m4; an acknowledgement that
  is not needed is refused rather than ignored).
* REFERENCE SURFACE (audit A8 M2): the pre-oxidation surface H_s of an ATOMISTIC terrace is its Si
  equivalent boundary, half a layer spacing (a/8) above its top atomic plane (Si atoms conserved:
  each (001) layer occupies a/4 centred on its plane); that of a CONTINUUM terrace is its boundary.
  The kept atomistic crystal then ends at its equivalent boundary H_s - N a/4 (top atomic plane
  H_s - N a/4 - a/8), and the continuum layer's lower boundary x_c OVERLAPS it by
  f t + t_a - N a/4 (positive) or leaves a GAP (negative) of that size, bounded by a/8 by the count
  rule; the value is recorded as ``interface_overlap_A`` (= ``interface_quantisation_A``) and is
  what the engine's potential contains (tests/forward/test_oxide_multislice_a8_fixes.py). A continuum crystal
  ends at x_c itself (overlap 0).
* CONFORMAL (E9 M2): equal thickness AND equal consumed-layer count on every terrace. Per-terrace
  overrides of the thickness and of the consumed-layer count exist for the grown-oxide sensitivity
  (E9 section 3 items 4-5: 4.27-4.71 rad per A of thickness difference, out:109-117; one extra
  consumed layer 13.70 rad, out:123); a structure with overrides that differ is NOT conformal.
* the vacuum edge is GRADED: the layer's real and imaginary potential are multiplied by
  E(x; x_t, w_v), E(x; x0, w) = erfc((x - x0) / (sqrt(2) w)) / 2 (an erf profile whose gradient is
  a Gaussian of standard deviation w: the definition of E9 out:236-243). w_v >= 0.5 A (E9 M4: a
  sharp 10.34 V edge reflects |r|^2 = 2.70e-3 by itself, out:234). EDGE_W05_REFLECTIVITY: at
  w = 0.5 A the exact 1-D reflectivity of the edge is |r|^2 = 1.95e-9 at 16.1347 mrad (|r| x 8.5e-4
  of the sharp edge; transfer matrix converged in step and span, audit A8 C6); E9's Born factor
  exp(-(q w)^2), out:241, gives 3.4e-11 (57 times lower) and is an underestimate; the multislice
  engine reproduces the exact value (1.835e-9 against 1.8345e-9 at its central bin 16.1751 mrad).
  A smaller width is refused unless ``sharp_edge_test_flag`` is True with a TEST_ONLY vacuum-edge
  label (validation of the Fresnel term only).
* the oxide/crystal (or oxide/a-Si, a-Si/crystal) transition is GRADED with the same profile of
  width w_i >= MIN_INTERFACE_WIDTH_A = 0.5 A (E9 M4: "the vacuum edge and oxide/Si transition";
  a sharp 10.34/13.90 V step reflects |r|^2 = 2.5e-4, audit A8 m5); a narrower or sharp
  (w_i = 0: cell-averaged per pixel like the continuum crystal of ContinuumTerracePotential)
  transition is refused unless ``sharp_interface_test_flag`` is True with a TEST_ONLY interface
  label.

A common shift of the reference surface moves every terrace alike and does not change a conformal
step phase.

Not represented (stated, not silently assumed): elastic diffuse scattering by the amorphous network
(the atomistic layer of L8 section 5 would produce it), charging (item 22), a carbon layer, the
denser transition layer (Hattori), TDS absorption in the layer, surface and interface plasmons
beyond the uniform V'_ox (E9 M1: the product with B38 is not a sourced quantity), partially
consumed atomic layers (the interface overlap or gap above).
"""
from __future__ import annotations

import hashlib
import json
import math
import numbers
from dataclasses import asdict, dataclass
from typing import Mapping

from reflection_holo.constants import AVOGADRO_PER_MOL, M_O_G_PER_MOL, M_SI_G_PER_MOL
from reflection_holo.io.labels import require_evidence_label

MODEL_NAME = "continuum_oxide"
LABEL_PREFIXES = ("PROJECT_INPUT", "ASSUMPTION", "TEST_ONLY")
ZERO_LABEL_PREFIXES = ("ASSUMPTION", "TEST_ONLY")      # V'_ox = 0, V'_a = 0 (not measurements)
MIN_VACUUM_EDGE_WIDTH_A = 0.5          # E9 M4 ("graded over at least 0.5 A")
MIN_INTERFACE_WIDTH_A = 0.5            # E9 M4 ("the vacuum edge and oxide/Si transition"), A8 m5
# A8 m4: the consumed-layer count must lie at least this far (in layers of a/4) from its rounding
# boundary (N +- 1/2) a/4, unless acknowledged. 0.05 layer = 0.068 A of consumed depth: at
# t_ox = 2 nm and 2.20 g/cm^3 the count then survives a thickness change of 0.15 A or a density
# change of 0.8 % (0.017 g/cm^3), the precision to which item-12 values are stated (DERIVED_HERE,
# a stated rule); the B41 2.0 nm stand-in lies 0.0036 layer from the boundary (count 7 becomes 6
# at 2.19877 g/cm^3, audit A8 C5).
MIN_ROUNDING_MARGIN_LAYERS = 0.05
EDGE_W05_REFLECTIVITY = (
    "vacuum edge graded over w = 0.5 A: exact 1-D reflectivity |r|^2 = 1.95e-9 at 16.1347 mrad "
    "(|r| x 8.5e-4 of the sharp edge's 2.70e-3; transfer matrix converged in step and span, audit "
    "A8 C6); E9's Born factor exp(-(q w)^2) (out:241) gives 3.4e-11, 57 times lower (an "
    "underestimate); the multislice engine reproduces the exact value (1.835e-9 against 1.8345e-9 "
    "at its central bin, 16.1751 mrad)")
LABEL_KEYS = ("thickness", "density", "consumed_layers", "V_real", "V_imag", "vacuum_edge",
              "interface", "amorphous_si")
LABEL_KEYS_AMORPHOUS_POTENTIAL = ("amorphous_si_potential",)
LABEL_KEYS_OVERRIDES = ("overrides",)
CRYSTAL_ATOMISTIC = "atomistic"
CRYSTAL_CONTINUUM = "continuum"
CRYSTAL_KINDS = (CRYSTAL_ATOMISTIC, CRYSTAL_CONTINUUM)
_TOL_A = 1e-9
REFERENCE_PLANE = (
    "pre-oxidation SURFACE of each terrace (the stack reference, pre_oxidation_surface_x_A): for an "
    "ATOMISTIC terrace its Si equivalent boundary, half a layer spacing (a/8) above its ideal top "
    "atomic-layer plane (pre_oxidation_plane_x_A = structure.si001 terrace_map top_height_A; Si "
    "atoms conserved: each (001) layer occupies a/4 centred on its plane); for a CONTINUUM terrace "
    "its boundary (audit A8 M2); a common shift of this reference does not change a conformal step "
    "phase")
INTERFACE_OVERLAP_RULE = (
    "interface_overlap_A = (kept crystal's equivalent boundary) - x_c: positive = the continuum "
    "layer overlaps the kept atomistic crystal's top half-layer slab, negative = a gap between them; "
    "= f t + t_a - N a/4 for an atomistic crystal (bounded by a/8 by the count rule), 0 for a "
    "continuum crystal (it ends at x_c); measured on the engine's potential by "
    "tests/forward/test_oxide_multislice_a8_fixes.py (audit A8 M2)")
NOT_REPRESENTED = (
    "elastic diffuse scattering by the amorphous network (continuum layer); charging (item 22); "
    "carbon; the denser transition layer (Hattori 2001); TDS absorption in the layer; surface and "
    "interface plasmons beyond the uniform V'_ox (E9 M1: not to be multiplied with B38); partially "
    "consumed atomic layers (the interface overlap or gap of an atomistic crystal, <= a/8)")


class OxideSpecError(ValueError):
    """A continuum oxide specification is refused (missing or inconsistent PROJECT_INPUT item 12)."""


@dataclass(frozen=True)
class ContinuumOxideSpec:
    """Continuum oxide overlayer (module docstring). Every field is REQUIRED (no defaults).

    material                  e.g. "amorphous SiO2" (recorded)
    thickness_A               t_ox on every terrace (thermal-oxide equivalent at density_g_cm3,
                              E9 M3), A, > 0
    density_g_cm3             oxide density, g/cm^3 (sets f and the IAM value recorded for
                              comparison), > 0
    consumed_layers           N: whole crystalline Si(001) layers of each terrace converted into
                              oxide or amorphous Si (int >= 0; |N a/4 - (f t + t_a)| <= a/8)
    V_real_V, V_imag_V        V_ox > 0 and V'_ox >= 0 (V)
    vacuum_edge_width_A       w_v (A), >= 0.5 unless sharp_edge_test_flag (TEST_ONLY)
    interface_width_A         w_i (A), >= 0.5 unless sharp_interface_test_flag (TEST_ONLY; then
                              >= 0, 0 = sharp, cell-averaged)
    amorphous_si_thickness_A  t_a (A), >= 0
    amorphous_si_V_real_V, amorphous_si_V_imag_V
                              V_a > 0, V'_a >= 0 when t_a > 0; None (stated) when t_a = 0
    terrace_thickness_A       None (every terrace carries thickness_A) or one thickness per
                              terrace (per-terrace override; label "overrides")
    terrace_consumed_layers   None or one consumed-layer count per terrace (override)
    sharp_edge_test_flag      True only with a TEST_ONLY vacuum-edge label: permits w_v < 0.5 A
    sharp_interface_test_flag True only with a TEST_ONLY interface label: permits w_i < 0.5 A
                              (audit A8 m5)
    rounding_boundary_acknowledged
                              True exactly when some terrace's continuum depth f t + t_a lies
                              closer than MIN_ROUNDING_MARGIN_LAYERS to the rounding boundary of
                              its consumed-layer count (audit A8 m4; checked by terrace_stacks,
                              which knows the lattice parameter); False otherwise
    labels                    mapping with exactly the keys LABEL_KEYS, plus
                              "amorphous_si_potential" when t_a > 0 and "overrides" when an
                              override is given; each value a label starting with PROJECT_INPUT,
                              ASSUMPTION or TEST_ONLY
    """
    material: str
    thickness_A: float
    density_g_cm3: float
    consumed_layers: int
    V_real_V: float
    V_imag_V: float
    vacuum_edge_width_A: float
    interface_width_A: float
    amorphous_si_thickness_A: float
    amorphous_si_V_real_V: float | None
    amorphous_si_V_imag_V: float | None
    terrace_thickness_A: tuple | None
    terrace_consumed_layers: tuple | None
    sharp_edge_test_flag: bool
    sharp_interface_test_flag: bool
    rounding_boundary_acknowledged: bool
    labels: Mapping[str, str]


def _num(v, what: str, *, positive: bool = False, nonneg: bool = False) -> float:
    if isinstance(v, bool) or v is None:
        raise OxideSpecError(f"{what} is required (a finite number), got {v!r}")
    if not isinstance(v, numbers.Real):          # audit A8 n1: no strings or other types
        raise OxideSpecError(f"{what} must be a finite number (int or float), got {v!r}")
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise OxideSpecError(f"{what} must be a finite number, got {v!r}") from None
    if not math.isfinite(x):
        raise OxideSpecError(f"{what} must be finite, got {v!r}")
    if positive and not x > 0.0:
        raise OxideSpecError(f"{what} must be > 0, got {v!r}")
    if nonneg and not x >= 0.0:
        raise OxideSpecError(f"{what} must be >= 0, got {v!r}")
    return x


def _int(v, what: str) -> int:
    if isinstance(v, bool) or not isinstance(v, int) or v < 0:
        raise OxideSpecError(f"{what} must be an integer >= 0 (whole consumed Si(001) layers), "
                             f"got {v!r}")
    return int(v)


def validate_spec(spec: ContinuumOxideSpec) -> dict:
    """Spec-level checks (everything that does not need the terraces); returns the record of the
    parameters with their labels. Raises OxideSpecError (a ValueError) or TypeError."""
    if not isinstance(spec, ContinuumOxideSpec):
        raise TypeError("the continuum oxide must be a ContinuumOxideSpec")
    if not isinstance(spec.labels, Mapping):
        raise TypeError("labels must be a mapping {parameter: label}")
    t_a = _num(spec.amorphous_si_thickness_A, "amorphous_si_thickness_A (item 12, E9 M5)",
               nonneg=True)
    overrides = spec.terrace_thickness_A is not None or spec.terrace_consumed_layers is not None
    want = set(LABEL_KEYS) | (set(LABEL_KEYS_AMORPHOUS_POTENTIAL) if t_a > 0 else set()) | (
        set(LABEL_KEYS_OVERRIDES) if overrides else set())
    got = set(spec.labels)
    if got != want:
        raise OxideSpecError(f"labels must have exactly the keys {sorted(want)} (one evidence "
                             f"label per physical parameter; no default), got {sorted(got)}")
    labels = {}
    for k in sorted(want):
        labels[k] = require_evidence_label(spec.labels[k], f"continuum oxide {k} (item 12)",
                                           accepted=LABEL_PREFIXES, qualified=True,
                                           error=OxideSpecError)
    if not isinstance(spec.material, str) or not spec.material.strip():
        raise OxideSpecError("material is required (e.g. 'amorphous SiO2')")
    t = _num(spec.thickness_A, "thickness_A (t_ox, item 12)", positive=True)
    rho = _num(spec.density_g_cm3, "density_g_cm3 (item 12)", positive=True)
    N = _int(spec.consumed_layers, "consumed_layers")
    V = _num(spec.V_real_V, "V_real_V (V_ox)", positive=True)
    Vi = _num(spec.V_imag_V, "V_imag_V (V'_ox)", nonneg=True)
    if Vi == 0.0 and not labels["V_imag"].startswith(ZERO_LABEL_PREFIXES):
        raise OxideSpecError("V_imag_V = 0 (no electronic absorption in the layer) must carry the "
                             "label ASSUMPTION (or TEST_ONLY in tests)")
    w_v = _num(spec.vacuum_edge_width_A, "vacuum_edge_width_A", nonneg=True)
    if not isinstance(spec.sharp_edge_test_flag, bool):
        raise OxideSpecError("sharp_edge_test_flag must be True or False (stated)")
    if spec.sharp_edge_test_flag:
        if not labels["vacuum_edge"].startswith("TEST_ONLY"):
            raise OxideSpecError("sharp_edge_test_flag = True is accepted only with a TEST_ONLY "
                                 "vacuum_edge label (validation of the Fresnel term; E9 M4)")
        if w_v >= MIN_VACUUM_EDGE_WIDTH_A:
            raise OxideSpecError(f"sharp_edge_test_flag = True with vacuum_edge_width_A = {w_v} "
                                 f">= {MIN_VACUUM_EDGE_WIDTH_A} A: the flag is not needed; refused "
                                 f"rather than ignored")
    elif w_v < MIN_VACUUM_EDGE_WIDTH_A:
        raise OxideSpecError(
            f"vacuum_edge_width_A = {w_v} A: the vacuum edge of the continuum layer must be graded "
            f"over at least {MIN_VACUUM_EDGE_WIDTH_A} A (E9 M4: a sharp 10.34 V edge reflects "
            f"|r|^2 = 2.70e-3 by itself, tools/review/e9_recompute_output.txt line 234; graded "
            f"over 0.5 A its exact 1-D reflectivity is 1.95e-9, |r| x 8.5e-4, audit A8 C6); a "
            f"narrower edge needs sharp_edge_test_flag with a TEST_ONLY label")
    w_i = _num(spec.interface_width_A, "interface_width_A", nonneg=True)
    if not isinstance(spec.sharp_interface_test_flag, bool):
        raise OxideSpecError("sharp_interface_test_flag must be True or False (stated)")
    if spec.sharp_interface_test_flag:
        if not labels["interface"].startswith("TEST_ONLY"):
            raise OxideSpecError("sharp_interface_test_flag = True is accepted only with a "
                                 "TEST_ONLY interface label (E9 M4; audit A8 m5)")
        if w_i >= MIN_INTERFACE_WIDTH_A:
            raise OxideSpecError(f"sharp_interface_test_flag = True with interface_width_A = {w_i} "
                                 f">= {MIN_INTERFACE_WIDTH_A} A: the flag is not needed; refused "
                                 f"rather than ignored")
    elif w_i < MIN_INTERFACE_WIDTH_A:
        raise OxideSpecError(
            f"interface_width_A = {w_i} A: the oxide/Si (and a-Si) transition must be graded over "
            f"at least {MIN_INTERFACE_WIDTH_A} A (E9 M4, 'the vacuum edge and oxide/Si transition'; "
            f"a sharp 10.34/13.90 V step reflects |r|^2 = 2.5e-4, which would dominate the "
            f"attenuated crystal reflectivity at [110], audit A8 m5); a narrower or sharp "
            f"transition needs sharp_interface_test_flag with a TEST_ONLY interface label")
    if not isinstance(spec.rounding_boundary_acknowledged, bool):
        raise OxideSpecError("rounding_boundary_acknowledged must be True or False (stated; audit "
                             "A8 m4)")
    if t_a == 0.0:
        # audit A8 M1: a measured zero (PROJECT_INPUT: no amorphous Si above the witness
        # measurement's detection limit) is accepted like any labelled value; an unlabelled zero
        # is refused by the label check above (every key required, a non-blank evidence label)
        if spec.amorphous_si_V_real_V is not None or spec.amorphous_si_V_imag_V is not None:
            raise OxideSpecError("amorphous_si_V_real_V and amorphous_si_V_imag_V must be None "
                                 "(stated) when amorphous_si_thickness_A = 0; refused rather than "
                                 "ignored")
        Va = Vai = None
    else:
        Va = _num(spec.amorphous_si_V_real_V, "amorphous_si_V_real_V (required when t_a > 0)",
                  positive=True)
        Vai = _num(spec.amorphous_si_V_imag_V, "amorphous_si_V_imag_V (required when t_a > 0)",
                   nonneg=True)
        if Vai == 0.0 and not labels["amorphous_si_potential"].startswith(ZERO_LABEL_PREFIXES):
            raise OxideSpecError("amorphous_si_V_imag_V = 0 must carry the label ASSUMPTION (or "
                                 "TEST_ONLY in tests)")
    tt = None
    if spec.terrace_thickness_A is not None:
        if not isinstance(spec.terrace_thickness_A, (tuple, list)) or not spec.terrace_thickness_A:
            raise OxideSpecError("terrace_thickness_A must be None or a non-empty tuple (one "
                                 "thickness per terrace)")
        tt = tuple(_num(v, "terrace_thickness_A entry", positive=True)
                   for v in spec.terrace_thickness_A)
    tn = None
    if spec.terrace_consumed_layers is not None:
        if not isinstance(spec.terrace_consumed_layers, (tuple, list)) or \
                not spec.terrace_consumed_layers:
            raise OxideSpecError("terrace_consumed_layers must be None or a non-empty tuple (one "
                                 "count per terrace)")
        tn = tuple(_int(v, "terrace_consumed_layers entry") for v in spec.terrace_consumed_layers)
    return dict(model=MODEL_NAME, material=spec.material, thickness_A=t, density_g_cm3=rho,
                consumed_layers=N, V_real_V=V, V_imag_V=Vi, vacuum_edge_width_A=w_v,
                interface_width_A=w_i, amorphous_si_thickness_A=t_a, amorphous_si_V_real_V=Va,
                amorphous_si_V_imag_V=Vai, terrace_thickness_A=None if tt is None else list(tt),
                terrace_consumed_layers=None if tn is None else list(tn),
                sharp_edge_test_flag=bool(spec.sharp_edge_test_flag),
                sharp_interface_test_flag=bool(spec.sharp_interface_test_flag),
                rounding_boundary_acknowledged=bool(spec.rounding_boundary_acknowledged),
                amorphous_si_zero=(None if t_a > 0 else
                                   "a measured zero (below the detection limit of the witness "
                                   "measurement)" if labels["amorphous_si"].startswith(
                                       "PROJECT_INPUT") else
                                   "the optimistic bound (E9 M5), " + labels["amorphous_si"]),
                labels=labels)


def spec_sha256(spec: ContinuumOxideSpec) -> str:
    """Canonical hash of a specification (tuples as lists), recorded by the builders and asserted
    by the multislice potential so that geometry and potential cannot diverge."""
    d = asdict(spec)
    d["labels"] = dict(spec.labels)
    for k in ("terrace_thickness_A", "terrace_consumed_layers"):
        if d[k] is not None:
            d[k] = list(d[k])
    return hashlib.sha256(json.dumps(d, sort_keys=True, default=float).encode()).hexdigest()


def silicon_density_g_cm3(a_A: float) -> float:
    """rho_Si = 8 M_Si / (N_A a^3) (diamond cubic; 2.3292 g/cm^3 at a = 5.4309 A, out:138)."""
    a = _num(a_A, "lattice parameter a_A", positive=True)
    return 8.0 * M_SI_G_PER_MOL / AVOGADRO_PER_MOL / (a * 1e-8) ** 3


def consumed_si_fraction(density_g_cm3: float, a_A: float) -> float:
    """f = (rho_ox / M_SiO2) / (rho_Si / M_Si): Si thickness consumed per unit oxide thickness
    (Si atoms conserved; E9 section 3; 0.4415 at 2.20 g/cm^3, a = 5.4309 A, out:143)."""
    rho = _num(density_g_cm3, "density_g_cm3", positive=True)
    m_sio2 = M_SI_G_PER_MOL + 2.0 * M_O_G_PER_MOL
    f = (rho / m_sio2) / (silicon_density_g_cm3(a_A) / M_SI_G_PER_MOL)
    if not 0.0 < f < 1.0:
        raise OxideSpecError(f"density {rho} g/cm^3 gives a consumed-Si fraction f = {f:.4f} "
                             f"outside (0, 1)")
    return float(f)


def sio2_formula_units_per_A3(density_g_cm3: float) -> float:
    """n_SiO2 = rho N_A / M_SiO2 in 1/A^3 (0.02205 at 2.20 g/cm^3, out:166)."""
    rho = _num(density_g_cm3, "density_g_cm3", positive=True)
    return rho * AVOGADRO_PER_MOL / (M_SI_G_PER_MOL + 2.0 * M_O_G_PER_MOL) * 1e-24


def rounding_margin(*, thickness_A: float, density_g_cm3: float, amorphous_si_thickness_A: float,
                    consumed_layers: int, a_A: float) -> dict:
    """Distance of the continuum depth f t + t_a from the rounding boundary (N +- 1/2) a/4 of the
    consumed-layer count N (audit A8 m4), in layers and in A, and where N would change: the
    density (thickness, a-Si fixed) and the thickness (density fixed) at the nearer boundary."""
    a = _num(a_A, "a_A", positive=True)
    q = a / 4.0
    t = _num(thickness_A, "thickness_A", positive=True)
    rho = _num(density_g_cm3, "density_g_cm3", positive=True)
    t_a = _num(amorphous_si_thickness_A, "amorphous_si_thickness_A", nonneg=True)
    N = _int(consumed_layers, "consumed_layers")
    f = consumed_si_fraction(rho, a)
    depth = f * t + t_a
    u = depth / q - N
    side = 1.0 if u >= 0.0 else -1.0                 # the nearer rounding boundary N + side/2
    boundary_A = (N + 0.5 * side) * q
    margin = 0.5 - abs(u)
    return dict(margin_layers=float(margin), margin_A=float(margin * q),
                continuum_layers=float(depth / q), consumed_layers=N,
                count_changes_to=int(N + side),
                count_changes_at_density_g_cm3=float(rho * (boundary_A - t_a) / (f * t)),
                count_changes_at_thickness_A=float((boundary_A - t_a) / f),
                min_margin_layers=MIN_ROUNDING_MARGIN_LAYERS,
                near_boundary=bool(margin < MIN_ROUNDING_MARGIN_LAYERS))


def terrace_stacks(spec: ContinuumOxideSpec, *, terrace_heights_A, a_A: float,
                   crystal: str) -> dict:
    """The layer stack of every terrace (module docstring) from the terrace heights
    ``terrace_heights_A`` (A, any common origin), the lattice parameter (for f and a/4) and the
    kind of crystal under the layer (REQUIRED, audit A8 M2):

      crystal = "atomistic"   terrace_heights_A are the terraces' top ATOMIC-layer planes; the
                              pre-oxidation surface is each plane + a/8 (Si equivalent boundary)
      crystal = "continuum"   terrace_heights_A are the continuum crystal boundaries (= the
                              pre-oxidation surfaces)

    Returns dict(record=..., per_terrace=[...], conformal=bool). Asserts the consumed-layer counts
    against the continuum depths (|N a/4 - (f t + t_a)| <= a/8) and the rounding-boundary margin
    (MIN_ROUNDING_MARGIN_LAYERS, unless acknowledged; an unneeded acknowledgement is refused)."""
    rec = validate_spec(spec)
    if crystal not in CRYSTAL_KINDS:
        raise OxideSpecError(f"crystal must be one of {CRYSTAL_KINDS} (the reference surface "
                             f"differs: audit A8 M2), got {crystal!r}")
    atomistic = crystal == CRYSTAL_ATOMISTIC
    H = [float(h) for h in terrace_heights_A]
    n = len(H)
    if n < 1:
        raise OxideSpecError("at least one terrace is required")
    a = _num(a_A, "a_A", positive=True)
    q = a / 4.0
    f = consumed_si_fraction(rec["density_g_cm3"], a)
    tt = rec["terrace_thickness_A"] or [rec["thickness_A"]] * n
    tn = rec["terrace_consumed_layers"] or [rec["consumed_layers"]] * n
    if len(tt) != n or len(tn) != n:
        raise OxideSpecError(f"per-terrace overrides must have one entry per terrace ({n}), got "
                             f"{len(tt)} thicknesses and {len(tn)} consumed-layer counts")
    t_a = rec["amorphous_si_thickness_A"]
    shift = 0.5 * q if atomistic else 0.0          # pre-oxidation surface above the input height
    per = []
    for k in range(n):
        t, N = float(tt[k]), int(tn[k])
        depth = f * t + t_a
        if abs(N * q - depth) > 0.5 * q + _TOL_A:
            best = int(math.floor(depth / q + 0.5))
            raise OxideSpecError(
                f"terrace {k}: consumed_layers = {N} ({N * q:.4f} A) is not the whole-layer count "
                f"nearest to the continuum depth f t + t_a = {f:.4f} x {t:.4f} + {t_a:.4f} = "
                f"{depth:.4f} A ({depth / q:.3f} layers of a/4 = {q:.6f} A); the nearest whole "
                f"count is {best} (E9 section 3 items 2 and 5). State it explicitly.")
        rm = rounding_margin(thickness_A=t, density_g_cm3=rec["density_g_cm3"],
                             amorphous_si_thickness_A=t_a, consumed_layers=N, a_A=a)
        Hs = H[k] + shift
        x_i = Hs - f * t
        x_t = Hs + (1.0 - f) * t
        x_c = x_i - t_a
        x_eq = Hs - N * q if atomistic else x_c        # where the kept crystal ends
        per.append(dict(index=k, pre_oxidation_plane_x_A=H[k], pre_oxidation_surface_x_A=Hs,
                        crystal=crystal, thickness_A=t, consumed_layers=N,
                        consumed_depth_A=f * t, interface_x_A=x_i, top_x_A=x_t,
                        amorphous_si_thickness_A=t_a, crystal_boundary_x_A=x_c,
                        atomistic_crystal_top_x_A=(H[k] - N * q) if atomistic else None,
                        crystal_equivalent_boundary_x_A=x_eq,
                        interface_quantisation_A=depth - N * q,
                        interface_overlap_A=(x_eq - x_c) if atomistic else 0.0,
                        interface_overlap_bound_A=0.5 * q if atomistic else 0.0,
                        consumed_layers_continuum=depth / q,
                        rounding_margin_layers=rm["margin_layers"],
                        rounding_margin_A=rm["margin_A"],
                        count_changes_to=rm["count_changes_to"],
                        count_changes_at_density_g_cm3=rm["count_changes_at_density_g_cm3"],
                        count_changes_at_thickness_A=rm["count_changes_at_thickness_A"],
                        top_rise_A=(1.0 - f) * t))              # = x_t - Hs
    near = [p for p in per if p["rounding_margin_layers"] < MIN_ROUNDING_MARGIN_LAYERS]
    ack = rec["rounding_boundary_acknowledged"]
    if near and not ack:
        p0 = min(near, key=lambda p: p["rounding_margin_layers"])
        raise OxideSpecError(
            f"terrace {p0['index']}: the continuum depth f t + t_a = "
            f"{p0['consumed_layers_continuum']:.4f} layers lies {p0['rounding_margin_layers']:.4f} "
            f"layer ({p0['rounding_margin_A']:.4f} A) from the rounding boundary of consumed_layers "
            f"= {p0['consumed_layers']} (margin required: {MIN_ROUNDING_MARGIN_LAYERS} layer): the "
            f"count becomes {p0['count_changes_to']} at a density of "
            f"{p0['count_changes_at_density_g_cm3']:.5f} g/cm^3 or a thickness of "
            f"{p0['count_changes_at_thickness_A']:.4f} A, and at <110> its parity decides the "
            f"terrace type at a buried a/4 step (E9 section 3 item 2). Refused unless "
            f"rounding_boundary_acknowledged = True (audit A8 m4)")
    if ack and not near:
        raise OxideSpecError(
            f"rounding_boundary_acknowledged = True, but every consumed-layer count lies at least "
            f"{MIN_ROUNDING_MARGIN_LAYERS} layer from its rounding boundary (smallest margin "
            f"{min(p['rounding_margin_layers'] for p in per):.4f}): the acknowledgement is not "
            f"needed; refused rather than ignored")
    conformal = len({round(p["thickness_A"], 12) for p in per}) == 1 and \
        len({p["consumed_layers"] for p in per}) == 1
    margin_min = min(p["rounding_margin_layers"] for p in per)
    record = dict(rec, value=MODEL_NAME, label=rec["labels"]["thickness"],
                  project_input="item 12", spec_sha256=spec_sha256(spec),
                  consumed_si_fraction_f=f, silicon_density_g_cm3=silicon_density_g_cm3(a),
                  lattice_parameter_A=a, layer_spacing_A=q, crystal=crystal,
                  conformal=bool(conformal),
                  conformal_definition=("equal thickness AND equal number of consumed Si layers "
                                        "on every terrace (E9 M2)"),
                  conformal_label=("ASSUMPTION for Ali's ion-milled, plasma-oxidised surface "
                                   "(E9 m4): the behaviour of thermal oxides grown layer by layer "
                                   "on UHV-clean stepped Si (R1-R3, R6)"),
                  geometry=("grown oxide (Si atoms conserved): interface x_i = H_s - f t, top "
                            "x_t = H_s + (1 - f) t, crystal boundary x_c = x_i - t_a, H_s the "
                            "pre-oxidation surface (reference_plane; E9 section 3 item 4; E9 M5)"),
                  reference_plane=REFERENCE_PLANE,
                  interface_overlap_rule=INTERFACE_OVERLAP_RULE,
                  interface_overlap_A=[p["interface_overlap_A"] for p in per],
                  rounding_margin_min_layers=float(margin_min),
                  rounding_margin_required_layers=MIN_ROUNDING_MARGIN_LAYERS,
                  near_rounding_boundary=bool(near),
                  rounding_boundary_note=(
                      "NEAR THE ROUNDING BOUNDARY (acknowledged): the consumed-layer count of "
                      "terrace(s) " + ", ".join(str(p["index"]) for p in near) + " changes at "
                      + "; ".join(f"{p['count_changes_at_density_g_cm3']:.5f} g/cm^3 or "
                                  f"{p['count_changes_at_thickness_A']:.4f} A (to "
                                  f"{p['count_changes_to']})" for p in near)
                      + "; at <110> the terrace type at a buried a/4 step (the parity of the "
                        "count) then depends on digits of the density or thickness below their "
                        "stated precision (audit A8 m4)") if near else
                  f"every count at least {MIN_ROUNDING_MARGIN_LAYERS} layer from its rounding "
                  f"boundary",
                  edge_reflectivity_w05=EDGE_W05_REFLECTIVITY,
                  profile=("V(x) = (V + iV') [E(x; x_t, w_v) - E(x; x_i, w_i)] (+ a-Si between x_c "
                           "and x_i); E(x; x0, w) = erfc((x - x0)/(sqrt(2) w))/2, point-sampled at "
                           "the pixel centres; w = 0 (TEST_ONLY flags only): cell-averaged sharp "
                           "step"),
                  elastic_diffuse="not represented (continuum layer)",
                  not_represented=NOT_REPRESENTED,
                  sources=("L8 section 8 as corrected by E9 M1-M5 and audit A8; numbers: "
                           "tools/review/e9_recompute_output.txt"))
    return dict(record=record, per_terrace=per, conformal=bool(conformal), f=f, q=q)


def stack_phase_terms(per_terrace: dict, *, k_perp_vac: float, k_perp_ox: complex,
                      k_perp_asi: complex | None) -> dict:
    """Vacuum-referenced specular phase of one terrace's layer stack RELATIVE to the bare crystal
    at its pre-oxidation surface H = pre_oxidation_surface_x_A (DERIVED_HERE, E6 M4 formalism as in
    E9 section 3):

        phi_k = -2 k x_t + 2 k'_ox (x_t - x_i) + 2 k'_a (x_i - x_c) + const
              = -2 k H + [2 (k'_ox - k) (x_t - H)]  +  [2 k'_ox (H - x_i) + 2 k'_a (x_i - x_c)]
                         top-surface term               grown-oxide (interface) term

    with complex normal wavevectors (V + iV'); the real parts are phases, the imaginary parts the
    in+out attenuation (amplitude exp(-Im)). The reflection is taken at the continuum crystal
    boundary x_c; multiple reflections at the graded edges are neglected (graded over >= 0.5 A: the
    vacuum edge reflects |r|^2 = 1.95e-9, EDGE_W05_REFLECTIVITY). Returns the two terms and their
    sum (complex, rad)."""
    H = per_terrace["pre_oxidation_surface_x_A"]
    x_t, x_i, x_c = (per_terrace["top_x_A"], per_terrace["interface_x_A"],
                     per_terrace["crystal_boundary_x_A"])
    top = 2.0 * (k_perp_ox - k_perp_vac) * (x_t - H)
    inter = 2.0 * k_perp_ox * (H - x_i)
    if x_i - x_c > 0:
        if k_perp_asi is None:
            raise ValueError("an amorphous-Si layer needs its normal wavevector")
        inter = inter + 2.0 * k_perp_asi * (x_i - x_c)
    return dict(top_surface=complex(top), interface=complex(inter), total=complex(top + inter))
