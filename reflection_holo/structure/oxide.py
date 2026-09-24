"""Continuum oxide overlayer on Si(001) (PROJECT_INPUT item 12; report E4 after L8 section 8 as
corrected by the adversarial review E9, M1-M5; numbers cited as lines of
tools/review/e9_recompute_output.txt, "out:N"; corrections after the audit A8, report X4, and after
the audit A9b, report X5, whose numbers are printed by the scripts in tools/review/x5/).

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
  depth: |N a/4 - (f t + t_a)| <= a/8 (asserted). N is DERIVED by this rule from the thickness,
  density and a-Si labels: its label is DERIVED_HERE (TEST_ONLY in tests), never PROJECT_INPUT
  (audit A9b M2). The distance of f t + t_a from the rounding boundary (N +- 1/2) a/4 is recorded;
  closer than MIN_ROUNDING_MARGIN_LAYERS (an ARBITRARY numerical guard, audit A9b m2: it does not
  make the count robust against the uncertainty of a witness measurement; for that see
  item12_count_interval, used by the pipeline) the count (and at <110> its parity, i.e. the
  terrace type at a buried a/4 step, E9 section 3 item 2) depends on the last digits of the
  density or thickness, and the specification is REFUSED unless ``rounding_boundary_acknowledged``
  is True (audit A8 m4; an acknowledgement that is not needed is refused rather than ignored).
* PARITY VARIANT (re-audit A10b M1, orchestrator's decision; report X6): when the count interval
  over the stated item-12 uncertainties (item12_count_interval: thickness, density AND a-Si
  thickness; standard uncertainties combined in quadrature, the nominal depth +- 2 combined
  standard uncertainties, re-audit A12 m2; half-widths as their worst case) spans ONE rounding
  boundary, both counts of the interval are consistent with the measurement; the specification
  then states ``consumed_layers_parity_variant`` = {parity: lower | upper, the uncertainties, their
  kind} and N must be the LOWER or the UPPER count of the interval (not necessarily the nearest
  one; the record names the variant whose count is the nearest, nearest_count_variant). The
  thickness, density and a-Si values are NOT altered, so for the variant whose count is NOT the
  nearest one the continuum layer overlaps the kept crystal (lower variant) or leaves a gap (upper
  variant) of MORE than a/8 (at most 1.5 a/4; recorded as interface_overlap_A; its effect is not
  computed); the nearest-count variant stays within a/8. The other variant is a separate run. An
  interval of more than two counts (more than one boundary) is refused: lower and upper would not
  cover the counts between them. No variant when the interval spans no boundary (refused).
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
  The two engines do NOT agree for a non-conformal layer on an ATOMISTIC crystal
  (NONCONFORMAL_SUBLAYER, audit A9b M1): the atomistic crystal loses whole layers only, so the
  multislice does not represent the grown-oxide term of a sub-layer thickness difference, while the
  geometric engine applies the continuum rate; an atomistic multislice cell whose terraces carry
  different thicknesses is refused (forward.cell.build_reflection_cell) unless
  ``nonconformal_sublayer_acknowledged`` is True with a TEST_ONLY overrides label.
* the vacuum edge is GRADED: the layer's real and imaginary potential are multiplied by
  E(x; x_t, w_v), E(x; x0, w) = erfc((x - x0) / (sqrt(2) w)) / 2 (an erf profile whose gradient is
  a Gaussian of standard deviation w: the definition of E9 out:236-243). w_v >= 0.5 A (E9 M4: a
  sharp 10.34 V edge reflects |r|^2 = 2.70e-3 by itself, out:234). EDGE_W05_REFLECTIVITY: at
  w = 0.5 A the exact 1-D reflectivity of the edge is |r|^2 = 1.9545e-9 at 16.1347 mrad
  (|r| x 8.513e-4 of the sharp edge; ODE and transfer matrix converged in step and span, audits A8
  C6 and A9b C2, tools/review/x5/a9b_c2_edge.py); E9's Born factor exp(-(q w)^2), out:241, gives
  3.44e-11 (56.8 times lower) and is an underestimate; the multislice engine reproduces the exact
  value at its central bin 16.1751 mrad (1.8350e-9 against 1.8345e-9).
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
consumed atomic layers (the interface overlap or gap above), and, for a non-conformal layer on an
atomistic crystal, the grown-oxide term of a sub-layer thickness difference in the multislice
(NONCONFORMAL_SUBLAYER).
"""
from __future__ import annotations

import hashlib
import json
import math
import numbers
import re
from dataclasses import asdict, dataclass
from typing import Mapping

from reflection_holo.constants import AVOGADRO_PER_MOL, M_O_G_PER_MOL, M_SI_G_PER_MOL
from reflection_holo.io.labels import require_evidence_label

MODEL_NAME = "continuum_oxide"
LABEL_PREFIXES = ("PROJECT_INPUT", "ASSUMPTION", "TEST_ONLY")
ZERO_LABEL_PREFIXES = ("ASSUMPTION", "TEST_ONLY")      # V'_ox = 0, V'_a = 0 (not measurements)
# audit A9b M2: the consumed-layer count is computed by the nearest-count rule from the thickness,
# density and a-Si values; it is DERIVED_HERE (TEST_ONLY in tests), never a PROJECT_INPUT
DERIVED_LABEL_KEYS = ("consumed_layers",)
DERIVED_LABEL_PREFIXES = ("DERIVED_HERE", "TEST_ONLY")
MIN_VACUUM_EDGE_WIDTH_A = 0.5          # E9 M4 ("graded over at least 0.5 A")
MIN_INTERFACE_WIDTH_A = 0.5            # E9 M4 ("the vacuum edge and oxide/Si transition"), A8 m5
# A8 m4, A9b m2: the consumed-layer count must lie at least this far (in layers of a/4) from its
# rounding boundary (N +- 1/2) a/4, unless acknowledged. 0.05 layer is an ARBITRARY NUMERICAL GUARD
# (no measured precision stands behind it; no item-12 value exists yet): 0.068 A of consumed
# depth, i.e. at t_ox = 2 nm and 2.20 g/cm^3 a thickness change of 0.1538 A or a density change of
# 0.769 % (0.0169 g/cm^3). It does NOT make the count or its parity robust: a witness-thickness
# uncertainty of +-1 A moves the continuum depth by +-0.325 layer, a density uncertainty of
# +-0.05 g/cm^3 at 2 nm by +-0.148 layer (tools/review/x5/x5_oxide_numbers.py); comparison runs
# therefore state the item-12 uncertainties, and when the count interval spans a count boundary
# they state which of its two counts they build (consumed_layers_parity_variant: lower or upper;
# the other count is a separate run; item12_count_interval; pipeline.config; re-audit A10b M1).
# The B41 2.0 nm stand-in lies 0.0036 layer from the boundary (count 7 becomes 6 at
# 2.19877 g/cm^3, -0.056 %; audit A8 C5).
MIN_ROUNDING_MARGIN_LAYERS = 0.05
# re-audit A10b m2, A12 m2: the kind of a stated item-12 uncertainty. STANDARD uncertainties: the
# continuum depth f(rho) t + t_a is (to first order) linear in the thickness, the density and the
# a-Si thickness, so its combined standard uncertainty is the quadrature sum of the three
# contributions, and the count interval is the nominal depth +- k u_c with the coverage factor
# k = 2 (about 95 % coverage for a normally distributed depth: 95.45 %; the coverage check is
# printed by tools/review/x7/x7_oxide_numbers.py); the a-Si term is one-sided at the lower end (the
# a-Si thickness is clipped at 0). HALF_WIDTHS: the worst case, the corners of the box (the depth
# interval is the linear sum of the three half-widths).
UNCERTAINTY_KINDS = ("standard", "half_width")
STANDARD_COVERAGE_FACTOR = 2.0
COVERAGE_STATEMENT = {
    "standard": "the nominal depth +- 2 combined standard uncertainties of the depth (the three "
                "contributions combined in quadrature, first-order propagation; coverage factor "
                "k = 2: about 95 % coverage for a normally distributed depth; the a-Si term "
                "one-sided at its lower end, clipped at zero thickness)",
    "half_width": "the worst case of the stated half-widths (the corners of the box: the linear "
                  "sum of the three contributions; coverage as stated by the supplier)"}
# re-audit A12 n1: each item-12 uncertainty is bounded (item12_count_interval)
UNCERTAINTY_DEPTH_BOUND_LAYERS = 2.0
UNCERTAINTY_BOUND_STATEMENT = (
    "each item-12 uncertainty is bounded: its interval half-width h (k u for a standard "
    "uncertainty, the half-width itself otherwise) must be smaller than the thickness or density "
    "it belongs to, and must move the continuum depth by less than "
    "UNCERTAINTY_DEPTH_BOUND_LAYERS = 2 layers of a/4 (a/2): h_t f < a/2, h_rho f t / rho < a/2, "
    "h_a < a/2. At two layers or more the count interval holds at least three counts, which is "
    "refused anyway (a parity variant is defined for two counts only), so the bound refuses no "
    "record that would otherwise run; it keeps an absurd value from building the list of counts "
    "(re-audit A12 n1)")
_MAX_COUNTS_BUILT = 16            # above the largest interval the bounds admit (printed by
                                  # tools/review/x7/x7_oxide_numbers.py)
# re-audit A10b M1 (orchestrator's decision): the two counts of an interval spanning ONE boundary
PARITY_VARIANTS = ("lower", "upper")
PARITY_VARIANT_KEYS = ("parity", "thickness_uncertainty_A", "density_uncertainty_g_cm3",
                       "amorphous_si_thickness_uncertainty_A", "uncertainty_kind")


def parity_variant_qualifier(parity: str) -> str:
    """The qualifier the DERIVED_HERE count label of a parity variant carries (re-audit A10b M1)."""
    return f"parity variant {parity} of an interval spanning a boundary"


# re-audit A12 n4: the qualifier is checked as an exact token, not as a substring
_PARITY_VARIANT_WORDS = re.compile(r"\bparity variant\b")
_PARITY_VARIANT_QUALIFIER = re.compile(r"\bparity variant (lower|upper) of an interval spanning a "
                                       r"boundary\b")


def nearest_count_variant(interval: Mapping) -> str | None:
    """Which parity variant ('lower' or 'upper') of a two-count interval (item12_count_interval)
    builds the nearest count at the stated values; None unless the interval holds two counts
    (re-audit A12 m3)."""
    counts = list(interval["counts"])
    if len(counts) != 2:
        return None
    return PARITY_VARIANTS[counts.index(interval["nearest_count"])]
EDGE_W05_REFLECTIVITY = (
    "vacuum edge graded over w = 0.5 A: exact 1-D reflectivity |r|^2 = 1.9545e-9 at 16.1347 mrad "
    "(|r| x 8.513e-4 of the sharp edge's 2.697e-3; ODE and transfer matrix converged in step and "
    "span, audits A8 C6 and A9b C2, tools/review/x5/a9b_c2_edge.py); E9's Born factor "
    "exp(-(q w)^2) (out:241) gives 3.44e-11, 56.8 times lower (an underestimate); at the multislice "
    "engine's central bin 16.1751 mrad the exact value is 1.8345e-9 (58.4 times the Born factor) "
    "and the engine gives 1.8350e-9 (tests/forward/test_oxide_multislice.py)")
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
    "tests/forward/test_oxide_multislice_a8_fixes.py (audit A8 M2). A gap is a dip of the "
    "potential inside the stack (audit A9b m4): for B41 at 2.0 nm (gap 0.674 A) the laterally "
    "averaged potential falls to 4.84 V, 0.96 A above the kept top atomic plane; its own Born "
    "reflectivity at q = 2 k'_ox is |r|^2 = 1.7e-12, and in the 1-D (0,0,8) reflection at 16.1347 "
    "mrad it changes |r| by -0.05 % and the phase by +0.023 rad against a stack joined to the "
    "crystal, common to every terrace of a conformal layer (1.5 nm, gap 0.166 A: +0.01 %, "
    "+0.009 rad; 1-D laterally averaged model, tools/review/x5/a9b_c3_gap.py); for a non-conformal "
    "layer the gap differs per terrace (NONCONFORMAL_SUBLAYER)")
# audit A9b M1 (tools/review/x5/a9b_c4_nonconformal.py: 1-D laterally averaged model, DERIVED_HERE,
# an estimate, at the B41 values V_ox 10.34 V, 2.20 g/cm^3, 16.1347 mrad)
SUBLAYER_RATE_DIFFERENCE_RAD_PER_A = (3.58, 3.61)       # geometric minus multislice, printed range
NONCONFORMAL_SUBLAYER = (
    "NON-CONFORMAL layer on an ATOMISTIC crystal: the engines disagree (audit A9b M1). The atomistic "
    "crystal loses whole layers only, so while the thickness changes by less than one consumed "
    "layer the multislice crystal does not move (only the layer top and the layer/crystal gap "
    "move) and a sub-layer thickness difference gives about 0.85-0.87 rad/A (0.8455, 0.8729, "
    "0.8599 rad/A in a 1-D laterally averaged model, close to the top-surface rate 2 (k'_ox - k) = "
    "0.886 rad/A), whereas the geometric engine applies the continuum grown-oxide rate "
    "2 k'_ox - 2 k (1 - f) = 4.4549 rad/A to any thickness difference (one consumed layer = "
    "13.6998 rad = 3.0752 A of oxide): the engines differ by 3.58-3.61 rad per A of sub-layer "
    "thickness difference (mod 2 pi), e.g. 2.23 rad against 0.42-0.44 rad for 0.5 A at a fixed "
    "count (V_ox 10.34 V, 2.20 g/cm^3, 16.1347 mrad; tools/review/x5/a9b_c4_nonconformal.py). "
    "The sub-layer thickness difference of two terraces is Dt - DN (a/4)/f. A propagated "
    "two-terrace multislice was not run")
NOT_REPRESENTED = (
    "elastic diffuse scattering by the amorphous network (continuum layer); charging (item 22); "
    "carbon; the denser transition layer (Hattori 2001); TDS absorption in the layer; surface and "
    "interface plasmons beyond the uniform V'_ox (E9 M1: not to be multiplied with B38); partially "
    "consumed atomic layers (the interface overlap or gap of an atomistic crystal, <= a/8); in the "
    "multislice, the grown-oxide term of a sub-layer thickness difference between terraces of an "
    "atomistic crystal: " + NONCONFORMAL_SUBLAYER)


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
    nonconformal_sublayer_acknowledged
                              True only with per-terrace thicknesses that differ and a TEST_ONLY
                              overrides label: acknowledges that the atomistic multislice does not
                              represent the grown-oxide term of a sub-layer thickness difference
                              (NONCONFORMAL_SUBLAYER; audit A9b M1); without it
                              forward.cell.build_reflection_cell refuses such a cell; False
                              otherwise (an acknowledgement that is not needed is refused). Also
                              needed when the terraces carry different consumed-layer counts at
                              one thickness (the rounding tie; re-audit A10b n1)
    consumed_layers_parity_variant
                              None (consumed_layers is the nearest count), or the mapping
                              {parity: "lower" | "upper", thickness_uncertainty_A,
                              density_uncertainty_g_cm3, amorphous_si_thickness_uncertainty_A,
                              uncertainty_kind: "standard" | "half_width"} of a PARITY VARIANT
                              (module docstring; re-audit A10b M1): consumed_layers is then the
                              lower or upper count of item12_count_interval, which must span
                              exactly one boundary; conformal only (no overrides); a DERIVED_HERE
                              count label must carry parity_variant_qualifier(parity)
    labels                    mapping with exactly the keys LABEL_KEYS, plus
                              "amorphous_si_potential" when t_a > 0 and "overrides" when an
                              override is given; each value a label starting with PROJECT_INPUT,
                              ASSUMPTION or TEST_ONLY, except consumed_layers: DERIVED_HERE (or
                              TEST_ONLY), never PROJECT_INPUT (audit A9b M2)
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
    nonconformal_sublayer_acknowledged: bool
    consumed_layers_parity_variant: Mapping | None
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
        if k in DERIVED_LABEL_KEYS:
            lab = spec.labels[k]
            if isinstance(lab, str) and lab.startswith(("PROJECT_INPUT", "ASSUMPTION")):
                raise OxideSpecError(
                    f"continuum oxide {k}: label {lab!r} refused: the consumed-layer count is "
                    f"computed by the nearest-count rule from the thickness, density and a-Si "
                    f"values and is labelled DERIVED_HERE (TEST_ONLY in tests); it never carries "
                    f"PROJECT_INPUT or ASSUMPTION (audit A9b M2)")
            labels[k] = require_evidence_label(lab, f"continuum oxide {k} (derived)",
                                               accepted=DERIVED_LABEL_PREFIXES, qualified=True,
                                               error=OxideSpecError)
            continue
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
            f"over 0.5 A its exact 1-D reflectivity is 1.9545e-9, |r| x 8.513e-4, audits A8 C6 "
            f"and A9b C2); a "
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
    ack_nc = spec.nonconformal_sublayer_acknowledged
    if not isinstance(ack_nc, bool):
        raise OxideSpecError("nonconformal_sublayer_acknowledged must be True or False (stated; "
                             "audit A9b M1)")
    if ack_nc:
        # needed for different thicknesses (A9b M1) or different counts at one thickness (the
        # rounding tie; re-audit A10b n1)
        if (tt is None or len({round(v, 12) for v in tt}) < 2) and (tn is None or len(set(tn)) < 2):
            raise OxideSpecError(
                "nonconformal_sublayer_acknowledged = True, but the terraces carry one thickness "
                "and one consumed-layer count: the acknowledgement is not needed; refused rather "
                "than ignored (audit A9b M1, re-audit A10b n1)")
        if not labels["overrides"].startswith("TEST_ONLY"):
            raise OxideSpecError(
                "nonconformal_sublayer_acknowledged = True is accepted only with a TEST_ONLY "
                "overrides label: the atomistic multislice does not represent the grown-oxide term "
                "of a sub-layer thickness difference (audit A9b M1; NONCONFORMAL_SUBLAYER)")
    variant = _parity_variant(spec.consumed_layers_parity_variant, labels["consumed_layers"],
                              overrides=overrides)
    return dict(model=MODEL_NAME, material=spec.material, thickness_A=t, density_g_cm3=rho,
                consumed_layers=N, V_real_V=V, V_imag_V=Vi, vacuum_edge_width_A=w_v,
                interface_width_A=w_i, amorphous_si_thickness_A=t_a, amorphous_si_V_real_V=Va,
                amorphous_si_V_imag_V=Vai, terrace_thickness_A=None if tt is None else list(tt),
                terrace_consumed_layers=None if tn is None else list(tn),
                sharp_edge_test_flag=bool(spec.sharp_edge_test_flag),
                sharp_interface_test_flag=bool(spec.sharp_interface_test_flag),
                rounding_boundary_acknowledged=bool(spec.rounding_boundary_acknowledged),
                nonconformal_sublayer_acknowledged=bool(ack_nc),
                consumed_layers_parity_variant=variant,
                amorphous_si_zero=(None if t_a > 0 else
                                   "a measured zero (below the detection limit of the witness "
                                   "measurement)" if labels["amorphous_si"].startswith(
                                       "PROJECT_INPUT") else
                                   "the optimistic bound (E9 M5), " + labels["amorphous_si"]),
                labels=labels, label=headline_label(labels))


def _parity_variant(variant, count_label: str, *, overrides: bool) -> dict | None:
    """Form of ``consumed_layers_parity_variant`` (re-audit A10b M1; the interval itself is checked
    by terrace_stacks, which knows the lattice parameter). Returns the validated mapping or None."""
    derived = isinstance(count_label, str) and count_label.startswith("DERIVED_HERE")
    if variant is None:
        if derived and _PARITY_VARIANT_WORDS.search(count_label):
            raise OxideSpecError(
                f"consumed_layers label {count_label!r} names a parity variant, but "
                f"consumed_layers_parity_variant is None (the count is the nearest count): "
                f"refused (re-audit A10b M1)")
        return None
    if not isinstance(variant, Mapping) or set(variant) != set(PARITY_VARIANT_KEYS):
        got = sorted(variant) if isinstance(variant, Mapping) else variant
        raise OxideSpecError(f"consumed_layers_parity_variant must be None or a mapping with "
                             f"exactly the keys {list(PARITY_VARIANT_KEYS)} (re-audit A10b M1), "
                             f"got {got!r}")
    parity = variant["parity"]
    if parity not in PARITY_VARIANTS:
        raise OxideSpecError(f"consumed_layers_parity_variant.parity must be one of "
                             f"{list(PARITY_VARIANTS)} (re-audit A10b M1), got {parity!r}")
    kind = variant["uncertainty_kind"]
    if kind not in UNCERTAINTY_KINDS:
        raise OxideSpecError(f"consumed_layers_parity_variant.uncertainty_kind must be one of "
                             f"{list(UNCERTAINTY_KINDS)} (re-audit A10b m2), got {kind!r}")
    out = dict(parity=parity, uncertainty_kind=kind)
    for k in ("thickness_uncertainty_A", "density_uncertainty_g_cm3",
              "amorphous_si_thickness_uncertainty_A"):
        out[k] = _num(variant[k], f"consumed_layers_parity_variant.{k} (item 12; zero or negative "
                                  f"refused, re-audit A10b n2)", positive=True)
    if overrides:
        raise OxideSpecError("a parity variant is a conformal layer (one thickness and one count "
                             "on every terrace): per-terrace overrides are refused with "
                             "consumed_layers_parity_variant (re-audit A10b M1)")
    # re-audit A12 n4: exact token: the qualifier of this parity once, and no other parity-variant
    # text (a label naming both qualifiers was accepted by the substring test)
    if derived and (len(_PARITY_VARIANT_WORDS.findall(count_label)) != 1
                    or _PARITY_VARIANT_QUALIFIER.findall(count_label) != [parity]):
        raise OxideSpecError(
            f"consumed_layers label {count_label!r}: a DERIVED_HERE count of a parity variant must "
            f"carry the qualifier {parity_variant_qualifier(parity)!r} exactly once and name no "
            f"other parity variant (exact token; re-audit A10b M1, A12 n4)")
    return out


def headline_label(labels: Mapping[str, str]) -> str:
    """The record's headline label (audit A9b n1): the per-parameter label when every parameter
    carries the same one; otherwise "mixed (<classes>)", the distinct label classes (the evidence
    label, with the model_assumptions id of an ASSUMPTION), so that the headline never reads
    PROJECT_INPUT while some parameter is not one. The per-parameter labels are in ``labels``."""
    vals = [labels[k] for k in sorted(labels)]
    if len(set(vals)) == 1:
        return vals[0]

    def cls(v: str) -> str:
        w = v.replace(":", " ").split()
        return " ".join(w[:2]) if w[0] == "ASSUMPTION" and len(w) > 1 else w[0]
    return ("mixed (" + ", ".join(sorted({cls(v) for v in vals})) + "); per-parameter labels in "
            "'labels'")


def nearest_consumed_layers(*, thickness_A: float, density_g_cm3: float,
                            amorphous_si_thickness_A: float, a_A: float) -> int:
    """The consumed-layer count DERIVED by the nearest-count rule (audit A9b M2): the whole number of
    a/4 layers nearest to the continuum depth f t + t_a (an exact tie rounds up; such a count lies
    on its rounding boundary and is refused by terrace_stacks unless acknowledged)."""
    a = _num(a_A, "a_A", positive=True)
    t = _num(thickness_A, "thickness_A", positive=True)
    t_a = _num(amorphous_si_thickness_A, "amorphous_si_thickness_A", nonneg=True)
    depth = consumed_si_fraction(density_g_cm3, a) * t + t_a
    return int(math.floor(depth / (a / 4.0) + 0.5))


def consumed_count_interval(*, thickness_A: float, thickness_uncertainty_A: float,
                            density_g_cm3: float, density_uncertainty_g_cm3: float,
                            amorphous_si_thickness_A: float, a_A: float) -> dict:
    """Consumed-layer counts over a box of thickness and density half-widths at a FIXED a-Si
    thickness (audit A9b m2, report X5; kept for tools/review/x5/x5_oxide_numbers.py). NOT the
    interval of the pipeline since report X6: item12_count_interval adds the a-Si thickness
    uncertainty (re-audit A10b m3) and the kind of the uncertainties (A10b m2). The continuum depth
    f(rho) t + t_a increases with t and rho, so its extremes are at (t - u_t, rho - u_rho) and
    (t + u_t, rho + u_rho); the count spans a rounding boundary when the nearest counts at the two
    extremes differ. Uncertainties must be > 0 and smaller than the value."""
    a = _num(a_A, "a_A", positive=True)
    q = a / 4.0
    t = _num(thickness_A, "thickness_A", positive=True)
    ut = _num(thickness_uncertainty_A, "thickness_uncertainty_A (item 12)", positive=True)
    rho = _num(density_g_cm3, "density_g_cm3", positive=True)
    ur = _num(density_uncertainty_g_cm3, "density_uncertainty_g_cm3 (item 12)", positive=True)
    t_a = _num(amorphous_si_thickness_A, "amorphous_si_thickness_A", nonneg=True)
    if not ut < t:
        raise OxideSpecError(f"thickness_uncertainty_A = {ut} must be smaller than the thickness "
                             f"{t} A")
    if not ur < rho:
        raise OxideSpecError(f"density_uncertainty_g_cm3 = {ur} must be smaller than the density "
                             f"{rho} g/cm^3")
    lo, hi, counts = _depth_counts(t - ut, t + ut, rho - ur, rho + ur, t_a, t_a, a)
    return dict(continuum_layers_min=float(lo / q), continuum_layers_max=float(hi / q),
                counts=counts, parities=sorted({"even" if n % 2 == 0 else "odd" for n in counts}),
                spans_boundary=bool(len(counts) > 1),
                box=dict(thickness_A=[t - ut, t + ut], density_g_cm3=[rho - ur, rho + ur],
                         amorphous_si_thickness_A=t_a),
                rule=("nearest whole count of (f(rho) t + t_a)/(a/4) at the two corners of the "
                      "uncertainty box (t -+ u_t, rho -+ u_rho); audit A9b m2"))


def _counts_between(lo: float, hi: float, q: float) -> list[int]:
    """The whole counts nearest to the continuum depths lo and hi (floor(x/q + 1/2)) and those
    between. Refuses a non-finite depth and more than _MAX_COUNTS_BUILT counts BEFORE any list is
    built (re-audit A12 n1: an absurd uncertainty built a list of about 7e8 integers, MemoryError,
    or overflowed, OverflowError)."""
    if not (math.isfinite(lo) and math.isfinite(hi)):
        raise OxideSpecError(f"the continuum depth interval {lo}-{hi} A is not finite; "
                             f"{UNCERTAINTY_BOUND_STATEMENT}")
    n_lo = int(math.floor(lo / q + 0.5))
    n_hi = int(math.floor(hi / q + 0.5))
    if n_hi - n_lo + 1 > _MAX_COUNTS_BUILT:
        raise OxideSpecError(f"the count interval would hold {n_hi - n_lo + 1} counts (more than "
                             f"{_MAX_COUNTS_BUILT}); refused before the list is built; "
                             f"{UNCERTAINTY_BOUND_STATEMENT}")
    return list(range(n_lo, n_hi + 1))


def _depth_counts(t_lo, t_hi, rho_lo, rho_hi, ta_lo, ta_hi, a):
    """Continuum depths f(rho) t + t_a at the two corners of a box (the depth increases with t,
    rho and t_a) and the whole counts nearest to them and between."""
    q = a / 4.0
    lo = consumed_si_fraction(rho_lo, a) * t_lo + ta_lo
    hi = consumed_si_fraction(rho_hi, a) * t_hi + ta_hi
    return lo, hi, _counts_between(lo, hi, q)


def item12_count_interval(*, thickness_A: float, thickness_uncertainty_A: float,
                          density_g_cm3: float, density_uncertainty_g_cm3: float,
                          amorphous_si_thickness_A: float,
                          amorphous_si_thickness_uncertainty_A: float, uncertainty_kind: str,
                          a_A: float) -> dict:
    """Consumed-layer counts consistent with the stated item-12 uncertainties (re-audit A10b m2,
    m3, n2, report X6; re-audit A12 m2, n1, report X7). Every argument is required. The continuum
    depth D = f(rho) t + t_a increases with t, rho and t_a; each quantity contributes a depth
    half-width c_i = s_i h_i (sensitivities s_t = f, s_rho = f t / rho, since f is proportional to
    rho, s_a = 1) of its interval half-width h_i:

      "standard"    h = k u, k = STANDARD_COVERAGE_FACTOR = 2; the contributions are combined in
                    QUADRATURE (first-order propagation of independent quantities): the interval is
                    D +- sqrt(c_t^2 + c_rho^2 + c_a^2), about 95 % coverage for a normally
                    distributed depth; the a-Si term is one-sided at the lower end, min(h_a, t_a),
                    since the a-Si thickness is clipped at 0;
      "half_width"  h = u; the WORST CASE: the depths at the two corners of the box (t -+ h_t,
                    rho -+ h_rho, t_a -+ h_a clipped at 0), whose width is the linear sum of the
                    contributions.

    Zero or negative uncertainties are refused. Each uncertainty is bounded
    (UNCERTAINTY_BOUND_STATEMENT): h_t < t, h_rho < rho, and each c_i < 2 a/4. The counts are the
    nearest counts at the interval ends and those between. spans_boundary: more than one count; a
    parity variant (lower or upper) is defined only for exactly two counts (one boundary)."""
    a = _num(a_A, "a_A", positive=True)
    q = a / 4.0
    if uncertainty_kind not in UNCERTAINTY_KINDS:
        raise OxideSpecError(f"uncertainty_kind must be one of {list(UNCERTAINTY_KINDS)} (stated; "
                             f"re-audit A10b m2), got {uncertainty_kind!r}")
    k = STANDARD_COVERAGE_FACTOR if uncertainty_kind == "standard" else 1.0
    t = _num(thickness_A, "thickness_A", positive=True)
    rho = _num(density_g_cm3, "density_g_cm3", positive=True)
    t_a = _num(amorphous_si_thickness_A, "amorphous_si_thickness_A", nonneg=True)
    u = {}
    for name, v in (("thickness_uncertainty_A", thickness_uncertainty_A),
                    ("density_uncertainty_g_cm3", density_uncertainty_g_cm3),
                    ("amorphous_si_thickness_uncertainty_A", amorphous_si_thickness_uncertainty_A)):
        u[name] = _num(v, f"{name} (item 12; zero or negative refused, re-audit A10b n2)",
                       positive=True)
    ht = k * u["thickness_uncertainty_A"]
    hr = k * u["density_uncertainty_g_cm3"]
    ha = k * u["amorphous_si_thickness_uncertainty_A"]
    if not ht < t:
        raise OxideSpecError(f"the thickness interval half-width {ht} A "
                             f"({COVERAGE_STATEMENT[uncertainty_kind]}) must be smaller than the "
                             f"thickness {t} A; {UNCERTAINTY_BOUND_STATEMENT}")
    if not hr < rho:
        raise OxideSpecError(f"the density interval half-width {hr} g/cm^3 "
                             f"({COVERAGE_STATEMENT[uncertainty_kind]}) must be smaller than the "
                             f"density {rho} g/cm^3; {UNCERTAINTY_BOUND_STATEMENT}")
    try:
        f = consumed_si_fraction(rho, a)
        f_lo, f_hi = consumed_si_fraction(rho - hr, a), consumed_si_fraction(rho + hr, a)
        contrib = dict(                               # depth half-width of each quantity, A
            thickness=f * ht, density=0.5 * (f_hi - f_lo) * t, amorphous_si=ha)
        sens = dict(thickness=(f, "thickness_uncertainty_A", "A"),
                    density=(f * t / rho, "density_uncertainty_g_cm3", "g/cm^3"),
                    amorphous_si=(1.0, "amorphous_si_thickness_uncertainty_A", "A"))
        bound = UNCERTAINTY_DEPTH_BOUND_LAYERS * q
        for name, c in contrib.items():
            if not c < bound:                          # also inf (k u overflowed)
                s_i, key, unit = sens[name]
                raise OxideSpecError(
                    f"{key} = {u[key]} {unit} ({uncertainty_kind}): its interval half-width moves "
                    f"the continuum depth by {c / q:.4g} layers of a/4, not below "
                    f"{UNCERTAINTY_DEPTH_BOUND_LAYERS:g} layers (a/2 = {bound:.4f} A): the upper "
                    f"bound of this uncertainty here is {bound / (k * s_i):.4g} {unit}; "
                    f"{UNCERTAINTY_BOUND_STATEMENT}")
        ha_lo = min(ha, t_a)                           # the a-Si thickness is clipped at 0
        depth = f * t + t_a
        if uncertainty_kind == "half_width":           # worst case: the corners of the box
            lo, hi, counts = _depth_counts(t - ht, t + ht, rho - hr, rho + hr, t_a - ha_lo,
                                           t_a + ha, a)
            combination = ("linear: the depths at the two corners of the box (the worst case of "
                           "the stated half-widths)")
        else:                                          # quadrature (re-audit A12 m2)
            base = contrib["thickness"] ** 2 + contrib["density"] ** 2
            lo = depth - math.sqrt(base + ha_lo ** 2)
            hi = depth + math.sqrt(base + ha ** 2)
            counts = _counts_between(lo, hi, q)
            combination = ("quadrature: the nominal depth +- sqrt(c_t^2 + c_rho^2 + c_a^2) with "
                           "c = sensitivity x k u (first-order propagation of independent "
                           "quantities), the a-Si term one-sided at the lower end")
    except (OverflowError, MemoryError) as exc:        # re-audit A12 n1: never uncaught
        raise OxideSpecError(f"the item-12 uncertainties are too large to form a count interval "
                             f"({type(exc).__name__}); {UNCERTAINTY_BOUND_STATEMENT}") from exc
    ta_lo = t_a - ha_lo
    nearest = int(math.floor(depth / q + 0.5))
    return dict(continuum_layers_min=float(lo / q), continuum_layers_max=float(hi / q),
                continuum_layers_nominal=float(depth / q), nearest_count=nearest,
                counts=counts, parities=sorted({"even" if n % 2 == 0 else "odd" for n in counts}),
                spans_boundary=bool(len(counts) > 1), boundaries_spanned=len(counts) - 1,
                uncertainty_kind=uncertainty_kind, coverage_factor=k,
                coverage=COVERAGE_STATEMENT[uncertainty_kind], combination=combination,
                uncertainties=u,
                box=dict(thickness_A=[t - ht, t + ht], density_g_cm3=[rho - hr, rho + hr],
                         amorphous_si_thickness_A=[ta_lo, t_a + ha]),
                depth_half_width_layers=dict(                # per quantity, in layers of a/4
                    thickness=float(contrib["thickness"] / q),
                    density=float(contrib["density"] / q),
                    amorphous_si=float((t_a + ha - ta_lo) / 2.0 / q)),
                combined_half_width_layers=dict(lower=float((depth - lo) / q),
                                                upper=float((hi - depth) / q)),
                rule=("nearest whole count of (f(rho) t + t_a)/(a/4) at the ends of the depth "
                      "interval: standard uncertainties in quadrature (nominal +- k u_c, k = 2), "
                      "half-widths at the corners of the box (t -+ h_t, rho -+ h_rho, t_a -+ h_a "
                      "clipped at 0); re-audit A10b m2, m3 (report X6), A12 m2 (report X7)"))


def spec_sha256(spec: ContinuumOxideSpec) -> str:
    """Canonical hash of a specification (tuples as lists), recorded by the builders and asserted
    by the multislice potential so that geometry and potential cannot diverge."""
    d = asdict(spec)
    d["labels"] = dict(spec.labels)
    for k in ("terrace_thickness_A", "terrace_consumed_layers"):
        if d[k] is not None:
            d[k] = list(d[k])
    # report X6: a specification without a parity variant hashes as before the field existed
    # (so the hashes recorded by earlier runs stay comparable); with one, the mapping is hashed
    if d["consumed_layers_parity_variant"] is None:
        del d["consumed_layers_parity_variant"]
    else:
        d["consumed_layers_parity_variant"] = dict(spec.consumed_layers_parity_variant)
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


def count_parity(n: int) -> str:
    """'even' or 'odd': the parity of a consumed-layer count (at <110> it sets the terrace type at a
    buried a/4 step, E9 section 3 item 2)."""
    return "even" if n % 2 == 0 else "odd"


def _check_parity_variant(rec: dict, a: float) -> dict:
    """re-audit A10b M1: the count of a parity variant is the lower or upper count of the item-12
    count interval, which must span exactly one rounding boundary. Returns the variant record."""
    v = rec["consumed_layers_parity_variant"]
    ci = item12_count_interval(
        thickness_A=rec["thickness_A"], thickness_uncertainty_A=v["thickness_uncertainty_A"],
        density_g_cm3=rec["density_g_cm3"],
        density_uncertainty_g_cm3=v["density_uncertainty_g_cm3"],
        amorphous_si_thickness_A=rec["amorphous_si_thickness_A"],
        amorphous_si_thickness_uncertainty_A=v["amorphous_si_thickness_uncertainty_A"],
        uncertainty_kind=v["uncertainty_kind"], a_A=a)
    span = (f"the count interval over the stated uncertainties ({ci['coverage']}) is "
            f"{ci['counts']} (continuum depth {ci['continuum_layers_min']:.3f}-"
            f"{ci['continuum_layers_max']:.3f} layers of a/4)")
    if not ci["spans_boundary"]:
        raise OxideSpecError(f"consumed_layers_parity_variant {v['parity']!r}: {span}; it spans no "
                             f"rounding boundary, so the count is the nearest count and a parity "
                             f"variant is refused (re-audit A10b M1)")
    if len(ci["counts"]) != 2:
        raise OxideSpecError(
            f"consumed_layers_parity_variant {v['parity']!r}: {span}; it spans "
            f"{ci['boundaries_spanned']} rounding boundaries: the lower and upper counts would not "
            f"cover the counts between them (and with three counts share one parity); refused: a "
            f"parity variant is defined for an interval of two counts only (re-audit A10b M1, "
            f"report X6; depth half-widths in layers: "
            + ", ".join(f"{k} {x:.3f}" for k, x in ci["depth_half_width_layers"].items()) + ")")
    idx = PARITY_VARIANTS.index(v["parity"])
    want = ci["counts"][idx]
    if rec["consumed_layers"] != want:
        raise OxideSpecError(f"consumed_layers = {rec['consumed_layers']} is not the "
                             f"{v['parity']} count {want} of the interval: {span} (re-audit A10b "
                             f"M1)")
    other = PARITY_VARIANTS[1 - idx]
    return dict(parity=v["parity"], count=want, count_parity=count_parity(want),
                qualifier=parity_variant_qualifier(v["parity"]), interval=ci,
                nearest_count=ci["nearest_count"],
                is_nearest_count=bool(want == ci["nearest_count"]),
                nearest_count_variant=nearest_count_variant(ci),         # re-audit A12 m3
                other_variant=dict(parity=other, count=ci["counts"][1 - idx],
                                   count_parity=count_parity(ci["counts"][1 - idx])),
                note=(f"parity variant {v['parity']} (count {want}, {count_parity(want)}) of an "
                      f"interval spanning a boundary; the other variant ({other}, count "
                      f"{ci['counts'][1 - idx]}) is a SEPARATE run, not built here. The "
                      f"thickness, density and a-Si values are not altered: when the count is not "
                      f"the nearest one ({ci['nearest_count']}) the continuum layer overlaps "
                      f"(lower) or leaves a gap to (upper) the kept crystal by more than a/8, at "
                      f"most 1.5 a/4 (interface_overlap_A); re-audit A10b M1, report X6"))


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
    variant = _check_parity_variant(rec, a) if rec["consumed_layers_parity_variant"] else None
    per = []
    for k in range(n):
        t, N = float(tt[k]), int(tn[k])
        depth = f * t + t_a
        if variant is not None:
            # re-audit A10b M1: N is the lower or upper count of the interval (checked above), not
            # necessarily the nearest one; the rounding guard below is judged on the nearest count
            N_guard = int(math.floor(depth / q + 0.5))
        elif abs(N * q - depth) > 0.5 * q + _TOL_A:
            best = int(math.floor(depth / q + 0.5))
            raise OxideSpecError(
                f"terrace {k}: consumed_layers = {N} ({N * q:.4f} A) is not the whole-layer count "
                f"nearest to the continuum depth f t + t_a = {f:.4f} x {t:.4f} + {t_a:.4f} = "
                f"{depth:.4f} A ({depth / q:.3f} layers of a/4 = {q:.6f} A); the nearest whole "
                f"count is {best} (E9 section 3 items 2 and 5). State it explicitly.")
        else:
            N_guard = N
        rm = rounding_margin(thickness_A=t, density_g_cm3=rec["density_g_cm3"],
                             amorphous_si_thickness_A=t_a, consumed_layers=N_guard, a_A=a)
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
                        interface_overlap_bound_A=((0.5 if variant is None else 1.5) * q
                                                   if atomistic else 0.0),
                        consumed_layers_continuum=depth / q,
                        rounding_margin_layers=rm["margin_layers"],
                        rounding_margin_A=rm["margin_A"],
                        count_changes_to=rm["count_changes_to"],
                        count_changes_at_density_g_cm3=rm["count_changes_at_density_g_cm3"],
                        count_changes_at_thickness_A=rm["count_changes_at_thickness_A"],
                        top_rise_A=(1.0 - f) * t))              # = x_t - Hs
        if variant is not None:
            # the interval spans one boundary, so |f t + t_a - N a/4| < 1.5 a/4 (report X6)
            if abs(depth - N * q) >= 1.5 * q + _TOL_A:
                raise OxideSpecError(f"terrace {k}: parity variant {variant['parity']}: "
                                     f"|f t + t_a - N a/4| = {abs(depth - N * q):.4f} A exceeds "
                                     f"1.5 a/4 (internal inconsistency)")
            per[-1].update(consumed_layers_nearest=N_guard, parity_variant=variant["parity"])
    near = [p for p in per if p["rounding_margin_layers"] < MIN_ROUNDING_MARGIN_LAYERS]
    ack = rec["rounding_boundary_acknowledged"]
    if near and not ack:
        p0 = min(near, key=lambda p: p["rounding_margin_layers"])
        raise OxideSpecError(
            f"terrace {p0['index']}: the continuum depth f t + t_a = "
            f"{p0['consumed_layers_continuum']:.4f} layers lies {p0['rounding_margin_layers']:.4f} "
            f"layer ({p0['rounding_margin_A']:.4f} A) from the rounding boundary of consumed_layers "
            f"= {p0.get('consumed_layers_nearest', p0['consumed_layers'])} (the nearest count; "
            f"margin required: {MIN_ROUNDING_MARGIN_LAYERS} layer): the "
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
    extra = {} if variant is None else dict(consumed_layers_parity_record=variant)
    record = dict(rec, **extra, value=MODEL_NAME, label=headline_label(rec["labels"]),
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
                        "count) then depends on the last digits of the density or thickness "
                        "(audit A8 m4)") if near else
                  f"every count at least {MIN_ROUNDING_MARGIN_LAYERS} layer from its rounding "
                  f"boundary",
                  rounding_margin_rule=(
                      f"{MIN_ROUNDING_MARGIN_LAYERS} layer is an arbitrary numerical guard (audit "
                      f"A9b m2): it does not make the count or its parity robust against the "
                      f"uncertainty of the item-12 thickness, density and a-Si thickness "
                      f"(item12_count_interval; the pipeline's comparison runs require those "
                      f"uncertainties and, when the interval spans a boundary, a parity variant; "
                      f"re-audit A10b M1, m3)"),
                  edge_reflectivity_w05=EDGE_W05_REFLECTIVITY,
                  profile=("V(x) = (V + iV') [E(x; x_t, w_v) - E(x; x_i, w_i)] (+ a-Si between x_c "
                           "and x_i); E(x; x0, w) = erfc((x - x0)/(sqrt(2) w))/2, point-sampled at "
                           "the pixel centres; w = 0 (TEST_ONLY flags only): cell-averaged sharp "
                           "step"),
                  elastic_diffuse="not represented (continuum layer)",
                  not_represented=NOT_REPRESENTED,
                  sources=("L8 section 8 as corrected by E9 M1-M5 and audits A8, A9b; numbers: "
                           "tools/review/e9_recompute_output.txt, tools/review/x5/"))
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
    vacuum edge reflects |r|^2 = 1.9545e-9, EDGE_W05_REFLECTIVITY). Returns the two terms and their
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
