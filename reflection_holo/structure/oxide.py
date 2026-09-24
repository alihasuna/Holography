"""Continuum oxide overlayer on Si(001) (PROJECT_INPUT item 12; report E4 after L8 section 8 as
corrected by the adversarial review E9, M1-M5; numbers cited as lines of
tools/review/e9_recompute_output.txt, "out:N").

Model (every physical parameter is a REQUIRED field of :class:`ContinuumOxideSpec` with its label;
nothing has a default):

* a uniform continuum layer of complex potential V_ox + i V'_ox on every terrace, FOLLOWING THE
  SURFACE (one layer per terrace; never a function of the surface-normal coordinate alone: E6 m12,
  E9 m5). V'_ox >= 0 is the electronic absorption of the layer (a model value, not a bound: E9 M1);
  V'_ox = 0 must carry an ASSUMPTION (or TEST_ONLY) label.
* GROWN from the crystal (E9 M2, section 3 item 4): Si atoms are conserved, so a layer of thickness
  t on a terrace whose pre-oxidation surface is the plane x = H consumes a depth f t of Si,
        f = (rho_ox / M_SiO2) / (rho_Si / M_Si),   rho_Si = 8 M_Si / (N_A a^3)
  (f = 0.4415 at 2.20 g/cm^3 and a = 5.4309 A, out:143): the oxide/Si interface lies at
  x_i = H - f t and the top of the layer at x_t = H + (1 - f) t.
* an optional amorphous-Si layer (milling damage left under the oxide, E9 M5) of thickness t_a
  between x_c = x_i - t_a and x_i, continuum potential V_a + i V'_a (both required when t_a > 0);
  t_a = 0 is the optimistic bound and must carry an ASSUMPTION (or TEST_ONLY) label. Its density is
  taken equal to that of the crystal it replaced (ASSUMPTION; E9 out:148-149 use 0.98-0.99).
* the crystal below x_c. An ATOMISTIC crystal loses its top N whole (001) layers; N (the consumed
  layer count) is a REQUIRED integer and must be the whole-layer count nearest to the continuum
  depth: |N a/4 - (f t + t_a)| <= a/8 (asserted; the difference is recorded as the interface
  quantisation, E9 section 3 item 5: differences come in whole consumed layers).
* CONFORMAL (E9 M2): equal thickness AND equal consumed-layer count on every terrace. Per-terrace
  overrides of the thickness and of the consumed-layer count exist for the grown-oxide sensitivity
  (E9 section 3 items 4-5: 4.27-4.71 rad per A of thickness difference, out:109-117; one extra
  consumed layer 13.70 rad, out:123); a structure with overrides that differ is NOT conformal.
* the vacuum edge is GRADED: the layer's real and imaginary potential are multiplied by
  E(x; x_t, w_v), E(x; x0, w) = erfc((x - x0) / (sqrt(2) w)) / 2 (an erf profile whose gradient is
  a Gaussian of standard deviation w: the definition of E9 out:236-243). w_v >= 0.5 A (E9 M4: a
  sharp 10.34 V edge reflects |r|^2 = 2.70e-3 by itself, out:234; w = 0.5 A suppresses |r| by
  1.1e-4, out:241). A smaller width is refused unless ``sharp_edge_test_flag`` is True with a
  TEST_ONLY vacuum-edge label (validation of the Fresnel term only).
* the oxide/crystal (or oxide/a-Si, a-Si/crystal) transition: graded with the same profile of
  width w_i > 0, or sharp (w_i = 0: cell-averaged per pixel like the continuum crystal of
  ContinuumTerracePotential). E9 M4 recommends >= 0.5 A (ASSUMPTION motivated by the measured oxide
  roughness, Hattori 2001 p. 697); an option here, with its label.

Reference plane: the pre-oxidation surface H of a terrace is its ideal top atomic-layer plane (the
convention of structure.si001 terrace_map "top_height_A", of forward.cell's continuum cells and of
the geometric engine). A common shift of this reference moves every terrace alike and does not
change a conformal step phase.

Not represented (stated, not silently assumed): elastic diffuse scattering by the amorphous network
(the atomistic layer of L8 section 5 would produce it), charging (item 22), a carbon layer, the
denser transition layer (Hattori), TDS absorption in the layer, surface and interface plasmons
beyond the uniform V'_ox (E9 M1: the product with B38 is not a sourced quantity).
"""
from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Mapping

from reflection_holo.constants import AVOGADRO_PER_MOL, M_O_G_PER_MOL, M_SI_G_PER_MOL
from reflection_holo.io.labels import require_evidence_label

MODEL_NAME = "continuum_oxide"
LABEL_PREFIXES = ("PROJECT_INPUT", "ASSUMPTION", "TEST_ONLY")
ZERO_LABEL_PREFIXES = ("ASSUMPTION", "TEST_ONLY")
MIN_VACUUM_EDGE_WIDTH_A = 0.5          # E9 M4 ("graded over at least 0.5 A"), out:241
LABEL_KEYS = ("thickness", "density", "consumed_layers", "V_real", "V_imag", "vacuum_edge",
              "interface", "amorphous_si")
LABEL_KEYS_AMORPHOUS_POTENTIAL = ("amorphous_si_potential",)
LABEL_KEYS_OVERRIDES = ("overrides",)
_TOL_A = 1e-9
REFERENCE_PLANE = ("pre-oxidation surface of each terrace = its ideal top atomic-layer plane "
                   "(structure.si001 terrace_map top_height_A); a common shift of this reference "
                   "does not change a conformal step phase")
NOT_REPRESENTED = (
    "elastic diffuse scattering by the amorphous network (continuum layer); charging (item 22); "
    "carbon; the denser transition layer (Hattori 2001); TDS absorption in the layer; surface and "
    "interface plasmons beyond the uniform V'_ox (E9 M1: not to be multiplied with B38)")


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
    interface_width_A         w_i (A), >= 0 (0 = sharp, cell-averaged)
    amorphous_si_thickness_A  t_a (A), >= 0
    amorphous_si_V_real_V, amorphous_si_V_imag_V
                              V_a > 0, V'_a >= 0 when t_a > 0; None (stated) when t_a = 0
    terrace_thickness_A       None (every terrace carries thickness_A) or one thickness per
                              terrace (per-terrace override; label "overrides")
    terrace_consumed_layers   None or one consumed-layer count per terrace (override)
    sharp_edge_test_flag      True only with a TEST_ONLY vacuum-edge label: permits w_v < 0.5 A
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
    labels: Mapping[str, str]


def _num(v, what: str, *, positive: bool = False, nonneg: bool = False) -> float:
    if isinstance(v, bool) or v is None:
        raise OxideSpecError(f"{what} is required (a finite number), got {v!r}")
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
            f"|r|^2 = 2.70e-3 by itself, tools/review/e9_recompute_output.txt line 234; 0.5 A "
            f"suppresses |r| by 1.1e-4, line 241); a narrower edge needs sharp_edge_test_flag with "
            f"a TEST_ONLY label")
    w_i = _num(spec.interface_width_A, "interface_width_A", nonneg=True)
    if t_a == 0.0:
        if not labels["amorphous_si"].startswith(ZERO_LABEL_PREFIXES):
            raise OxideSpecError("amorphous_si_thickness_A = 0 (the optimistic bound, E9 M5) must "
                                 "carry the label ASSUMPTION (or TEST_ONLY in tests)")
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
                sharp_edge_test_flag=bool(spec.sharp_edge_test_flag), labels=labels)


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


def terrace_stacks(spec: ContinuumOxideSpec, *, terrace_heights_A, a_A: float) -> dict:
    """The layer stack of every terrace (module docstring) from the pre-oxidation surfaces
    ``terrace_heights_A`` (A, any common origin) and the lattice parameter (for f and a/4).

    Returns dict(record=..., per_terrace=[...], conformal=bool). Asserts the consumed-layer counts
    against the continuum depths (|N a/4 - (f t + t_a)| <= a/8)."""
    rec = validate_spec(spec)
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
        x_i = H[k] - f * t
        x_t = H[k] + (1.0 - f) * t
        x_c = x_i - t_a
        x_cA = H[k] - N * q
        per.append(dict(index=k, pre_oxidation_plane_x_A=H[k], thickness_A=t, consumed_layers=N,
                        consumed_depth_A=f * t, interface_x_A=x_i, top_x_A=x_t,
                        amorphous_si_thickness_A=t_a, crystal_boundary_x_A=x_c,
                        atomistic_crystal_top_x_A=x_cA,
                        interface_quantisation_A=x_cA - x_c,
                        consumed_layers_continuum=depth / q,
                        top_rise_A=(1.0 - f) * t))
    conformal = len({round(p["thickness_A"], 12) for p in per}) == 1 and \
        len({p["consumed_layers"] for p in per}) == 1
    record = dict(rec, value=MODEL_NAME, label=rec["labels"]["thickness"],
                  project_input="item 12", spec_sha256=spec_sha256(spec),
                  consumed_si_fraction_f=f, silicon_density_g_cm3=silicon_density_g_cm3(a),
                  lattice_parameter_A=a, layer_spacing_A=q,
                  conformal=bool(conformal),
                  conformal_definition=("equal thickness AND equal number of consumed Si layers "
                                        "on every terrace (E9 M2)"),
                  conformal_label=("ASSUMPTION for Ali's ion-milled, plasma-oxidised surface "
                                   "(E9 m4): the behaviour of thermal oxides grown layer by layer "
                                   "on UHV-clean stepped Si (R1-R3, R6)"),
                  geometry=("grown oxide (Si atoms conserved): interface x_i = H - f t, top "
                            "x_t = H + (1 - f) t, crystal boundary x_c = x_i - t_a (E9 section 3 "
                            "item 4; E9 M5)"),
                  reference_plane=REFERENCE_PLANE,
                  profile=("V(x) = (V + iV') [E(x; x_t, w_v) - E(x; x_i, w_i)] (+ a-Si between x_c "
                           "and x_i); E(x; x0, w) = erfc((x - x0)/(sqrt(2) w))/2, point-sampled at "
                           "the pixel centres; w = 0: cell-averaged sharp step"),
                  elastic_diffuse="not represented (continuum layer)",
                  not_represented=NOT_REPRESENTED,
                  sources=("L8 section 8 as corrected by E9 M1-M5; numbers: "
                           "tools/review/e9_recompute_output.txt"))
    return dict(record=record, per_terrace=per, conformal=bool(conformal), f=f, q=q)


def stack_phase_terms(per_terrace: dict, *, k_perp_vac: float, k_perp_ox: complex,
                      k_perp_asi: complex | None) -> dict:
    """Vacuum-referenced specular phase of one terrace's layer stack RELATIVE to the bare crystal
    at its pre-oxidation plane H (DERIVED_HERE, E6 M4 formalism as in E9 section 3):

        phi_k = -2 k x_t + 2 k'_ox (x_t - x_i) + 2 k'_a (x_i - x_c) + const
              = -2 k H + [2 (k'_ox - k) (x_t - H)]  +  [2 k'_ox (H - x_i) + 2 k'_a (x_i - x_c)]
                         top-surface term               grown-oxide (interface) term

    with complex normal wavevectors (V + iV'); the real parts are phases, the imaginary parts the
    in+out attenuation (amplitude exp(-Im)). The reflection is taken at the continuum crystal
    boundary x_c; multiple reflections at the graded edges are neglected (E9 out:241). Returns the
    two terms and their sum (complex, rad)."""
    H = per_terrace["pre_oxidation_plane_x_A"]
    x_t, x_i, x_c = (per_terrace["top_x_A"], per_terrace["interface_x_A"],
                     per_terrace["crystal_boundary_x_A"])
    top = 2.0 * (k_perp_ox - k_perp_vac) * (x_t - H)
    inter = 2.0 * k_perp_ox * (H - x_i)
    if x_i - x_c > 0:
        if k_perp_asi is None:
            raise ValueError("an amorphous-Si layer needs its normal wavevector")
        inter = inter + 2.0 * k_perp_asi * (x_i - x_c)
    return dict(top_surface=complex(top), interface=complex(inter), total=complex(top + inter))
