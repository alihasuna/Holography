"""Si thermal displacement for the frozen-phonon model (model_assumptions B35; report E2).

Sourced values (SECTION_READ in docs/agent_reports/L6_sourced_si_parameters.md section 2.2, each
re-read and CONFIRMED by the reviewer E6, E6 sections 1 and 8):

* B = 0.4761(17) A^2 at 295.5 K, neutron Pendelloesung interferometry: B. Heacock et al.,
  "Pendelloesung interferometry probes the neutron charge radius, lattice dynamics, and fifth
  forces", arXiv:2103.05428v3, PDF p. 6 ("our results are B = 0.4761(17) A2"); version of record
  Science 373, 1239 (2021), doi:10.1126/science.abc2794 (pagination not read);
* dB/dT = 0.0014 A^2/K at 295.5 K (same source, PDF p. 25: "the BvK model predicted slope of B at
  room temperature dB/dT = 0.0014 A2 K-1 at 295.5 K");
* convention <u^2> = B / (8 pi^2) per Cartesian axis (same source, PDF p. 3), the convention of the
  engine's FrozenPhonons (independent Gaussian per axis; L6 section 2.3).

Model (ASSUMPTION B35, a use of the sourced values):
    B(T) = 0.4761 A^2 + 0.0014 A^2/K (T - 295.5 K),     u(T) = sqrt(B(T) / (8 pi^2)) per axis,
u(295.5 K) = 0.07765 A (+- 0.00014 A from the +- 0.0017 A^2). The linear form is an extrapolation
of the slope quoted AT 295.5 K; it is refused outside [T_MIN_K, T_MAX_K] = [273.15 K, 323.15 K]
(0 to 50 deg C: room-temperature holography including modest beam heating). Justification of the
range (DERIVED_HERE, tools: none, numbers reproduced by tests/structure/test_thermal.py): the
curvature of B(T) is not in the source; two harmonic lattice models matched to B and dB/dT at
295.5 K (an Einstein model, Theta_E = 275.1 K, and a Debye model, Theta_D = 482.1 K; model forms
not sourced, used only to size the curvature) depart from the linear form by at most 2.4e-4 A^2
inside the range, one seventh of the stated measurement uncertainty 0.0017 A^2 (they reach
0.0017 A^2 only near 225 K and 375 K). Anharmonicity is not bounded by any source read. In-situ
annealed specimens (e.g. Tanishiro 2003 at 750 deg C, E6 section 5 item 2) are outside the range.

The specimen temperature is PROJECT_INPUT item 23 ("specimen temperature during holography"); it
has no default: ``frozen_phonon_arguments`` refuses a missing, unlabelled or out-of-range value. The
demo configurations use the stand-in ASSUMPTION B36 (295.5 K, the reference temperature of the
source). Model_assumptions A7 (0.076 A per axis, inherited from the inspected repository) is NOT
replaced: FrozenPhonons(rms_displacement_A=0.076, label="ASSUMPTION A7 ...") keeps working for
the inspected-repository comparisons (E6 m3).

Einstein-model caveat (L6 2.3; Hajek and Rusz 2026, SECTION_READ in L6): independent Gaussian
displacements miss phonon correlations; the single-site B is still the right input for it.
"""
from __future__ import annotations

import math

from reflection_holo.io.labels import require_evidence_label

B_REF_A2 = 0.4761                 # Heacock et al. 2021, arXiv:2103.05428v3 PDF p. 6
B_REF_SIGMA_A2 = 0.0017           # same, the (17)
T_REF_K = 295.5                   # same
DB_DT_A2_PER_K = 0.0014           # same, PDF p. 25 (BvK slope at 295.5 K)
T_MIN_K = 273.15                  # validity range of the linear extrapolation (module docstring)
T_MAX_K = 323.15
SOURCE = ("Heacock et al. 2021, arXiv:2103.05428v3: B = 0.4761(17) A^2 at 295.5 K (PDF p. 6), "
          "dB/dT = 0.0014 A^2/K at 295.5 K (PDF p. 25), <u^2> = B/(8 pi^2) (PDF p. 3); "
          "SECTION_READ (L6 section 2.2, confirmed by E6)")
MODEL = ("B(T) = 0.4761 A^2 + 0.0014 A^2/K (T - 295.5 K), u = sqrt(B/(8 pi^2)) per axis; the "
         "linear extrapolation is an ASSUMPTION valid near room temperature "
         f"({T_MIN_K} K <= T <= {T_MAX_K} K)")
TEMPERATURE_LABELS = ("PROJECT_INPUT", "ASSUMPTION", "TEST_ONLY")


class TemperatureOutOfRangeError(ValueError):
    """The specimen temperature is outside the validity range of the linear B(T) model."""


def _temperature(T_K) -> float:
    if isinstance(T_K, bool) or not isinstance(T_K, (int, float)):
        raise TypeError(f"specimen temperature must be a number in K, got {T_K!r}")
    T = float(T_K)
    if not math.isfinite(T):
        raise ValueError(f"specimen temperature must be finite, got {T_K!r}")
    if not (T_MIN_K <= T <= T_MAX_K):
        raise TemperatureOutOfRangeError(
            f"specimen temperature {T} K is outside [{T_MIN_K}, {T_MAX_K}] K, where the linear "
            f"extrapolation of B(T) from 295.5 K (dB/dT = 0.0014 A^2/K quoted AT 295.5 K) is "
            f"accepted (model_assumptions B35; reflection_holo.structure.thermal docstring): "
            f"refused rather than extrapolated")
    return T


def si_debye_waller_B_A2(T_K) -> float:
    """B(T) of Si in A^2 (model_assumptions B35), refused outside [T_MIN_K, T_MAX_K]."""
    T = _temperature(T_K)
    return B_REF_A2 + DB_DT_A2_PER_K * (T - T_REF_K)


def si_rms_displacement_per_axis_A(T_K) -> float:
    """u(T) = sqrt(B(T) / (8 pi^2)) per Cartesian axis, in A (0.07765 A at 295.5 K)."""
    return math.sqrt(si_debye_waller_B_A2(T_K) / (8.0 * math.pi ** 2))


def si_rms_displacement_sigma_A(T_K) -> float:
    """Standard uncertainty of u(T) from the +-0.0017 A^2 of B only (the slope's uncertainty is not
    stated in the source)."""
    B = si_debye_waller_B_A2(T_K)
    return B_REF_SIGMA_A2 / (2.0 * math.sqrt(B * 8.0 * math.pi ** 2))


def frozen_phonon_arguments(*, specimen_temperature_K, temperature_label: str) -> dict:
    """Keyword arguments of forward.multislice.FrozenPhonons (rms_displacement_A, label) for the
    specimen temperature (PROJECT_INPUT item 23, required: no default). ``temperature_label``
    must start with PROJECT_INPUT (the supplied value), ASSUMPTION (a registered stand-in such as
    B36) or TEST_ONLY. The returned label starts with "ASSUMPTION B35" (the linear model and the
    Einstein model are assumptions; the parameters are sourced) and carries the temperature's
    label, so the value is traceable in every manifest."""
    if specimen_temperature_K is None:
        raise ValueError("specimen temperature is a missing PROJECT_INPUT (item 23, specimen "
                         "temperature during holography): no default is assumed")
    require_evidence_label(temperature_label, "specimen temperature (PROJECT_INPUT item 23)",
                           accepted=TEMPERATURE_LABELS, qualified=True)
    T = _temperature(specimen_temperature_K)
    u = si_rms_displacement_per_axis_A(T)
    label = (f"ASSUMPTION B35: u = {u:.6f} A per axis at T = {T} K; {MODEL}; {SOURCE}; "
             f"T: {temperature_label}")
    return dict(rms_displacement_A=u, label=label)


def describe(T_K) -> dict:
    """Record of the thermal model at T_K (for manifests and reports)."""
    T = _temperature(T_K)
    return dict(model="B35", formula=MODEL, source=SOURCE, specimen_temperature_K=T,
                B_A2=si_debye_waller_B_A2(T), u_per_axis_A=si_rms_displacement_per_axis_A(T),
                u_sigma_from_B_A=si_rms_displacement_sigma_A(T),
                validity_range_K=[T_MIN_K, T_MAX_K],
                not_replaced="model_assumptions A7 (0.076 A, inspected repository) is unchanged")
