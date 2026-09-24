"""Surface-plasmon (inelastic) losses in hologram formation (report E3 section 3; E6 M1, M2;
model_assumptions B6; docs/06 items 16 and 21).

Premises (each labelled):
* P1 (SECTION_READ via E6, Tanishiro 2003 pp. 166-167): for the specular beam the main inelastic
  process is surface-plasmon excitation, mostly OUTSIDE the crystal (decay distance v/(2 omega_s),
  about 6 nm at 200 keV, p. 170). The number of excitations per reflection is Poisson distributed
  with mean n (independent excitations of a linearly coupled boson field: ASSUMPTION, the standard
  model behind the Lucas-Sunjic mean number cited on pp. 166-167).
* P2 (ASSUMPTION): a loss electron keeps the spatial wave of the elastic object wave (theta_E =
  dE/(2E) = 2.8e-5 rad, p. 171, far inside the objective aperture); only its coherence with the
  other arm changes. The detected intensity of each arm is conserved without an energy filter.
* P3 (DERIVED_HERE, coherent-state bookkeeping): the passage of the electron along arm P leaves the
  plasmon field in a coherent state |alpha_P> with mean occupation n_P = sum_m |alpha_P,m|^2. Tracing
  the plasmons out, the fringe term of |psi_O> |alpha_O> + |psi_R> |alpha_R> is multiplied by
  <alpha_R|alpha_O> = exp(-(n_O + n_R)/2 + c), c = sum_m alpha_R,m^* alpha_O,m. The k = 0 term of
  exp(c) is the ZERO-LOSS (elastic) channel, amplitude factors exp(-n_O/2), exp(-n_R/2); the k >= 1
  terms are the LOSS channels, which interfere only through excitations SHARED by the two arms
  (c != 0 requires both arms to excite the same modes: J-e's one-plasmon "interference distance"
  and Tanishiro's decreasing loss visibility with object-reference separation, E6 M2).

Model (DERIVED_HERE from P1-P3, with the loss channels summarised by ONE declared visibility):

    I = | e^(-n_O/2) u_o + e^(-n_R/2) u_r |^2                                (zero-loss, coherent)
      + L_O |u_o|^2 + L_R |u_r|^2 + 2 V_loss sqrt(L_O L_R) Re(u_o u_r^*)         (loss electrons)

with L_P = 1 - exp(-n_P) the loss fraction of arm P and V_loss in [0, 1] the degree of mutual
coherence of the loss electrons of the two arms (the fringe visibility of the loss-electron
hologram for equal arm intensities; PROJECT_INPUT item 16 decides it through the object-reference
separation, E6 M2). u_o, u_r are the lossless waves (u_o from the engine without plasmons). With an
energy filter passing only the zero-loss electrons ("zero_loss") the second line is absent.

Consequences (DERIVED_HERE; tested in tests/optics/test_inelastic.py):
* Fringe (sideband) amplitude factor F = e^(-(n_O + n_R)/2) + V_loss sqrt(L_O L_R) (unfiltered).
  - R1, vacuum reference (the reference arm does not reflect, n_R = 0, so L_R = 0): F = e^(-n/2)
    whatever V_loss: the loss electrons of the object arm are pure background (no reference-arm
    electron shares their final plasmon state). E6's transfer n = 1.25 gives F = 0.536.
  - R2, self-reference (both arms reflect from the same, uniform surface, n_O = n_R = n):
    F = e^(-n) + V_loss (1 - e^(-n)); n = 1.25: 0.287 + 0.713 V_loss (0.358 at V_loss = 0.1).
* Visibility mu = 2 A_O A_R F / (A_O^2 + A_R^2) (unfiltered: the detected intensity is unchanged),
  i.e. mu = mu_0 F. With the zero-loss filter mu = 2 A_O A_R e^(-(n_O+n_R)/2) /
  (e^(-n_O) A_O^2 + e^(-n_R) A_R^2) at the reduced dose.
* Phase: F is real and positive, so the reconstructed phase phi_o - phi_r (R1) or
  phi(r) - phi(r + s) (R2) is UNCHANGED by a uniform n (exactly within this model; a loss channel
  with a complex c, i.e. a mode-structure phase, is not modelled). The phase NOISE grows: the
  sideband phase noise sqrt(2)/(mu sqrt(N)) (SM12) must be evaluated with the reduced mu
  (``fringe_contrast_with_losses``).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from reflection_holo.io.labels import require_evidence_label

ENERGY_FILTERS = ("none", "zero_loss")
_LABELS = ("PROJECT_INPUT", "ASSUMPTION", "DERIVED_HERE", "SECTION_READ", "TEST_ONLY")
R1_REFERENCE_LABEL = ("DERIVED_HERE: R1/R3 vacuum reference, the reference arm does not reflect "
                      "(model_assumptions B5; SM21), so it excites no surface plasmon; aloof "
                      "excitation by a reference passing within about v/(2 omega_s) = 6 nm of a "
                      "surface is neglected (ASSUMPTION)")
R2_REFERENCE_LABEL = ("DERIVED_HERE: R2 self-reference reflected from a flat region of the same "
                      "surface (B5): the same mean excitation number as the object arm (uniform "
                      "surface, ASSUMPTION)")


def _num(name: str, v, lo: float, hi: float | None) -> float:
    if v is None or isinstance(v, bool):
        raise ValueError(f"{name} is required (no default is substituted), got {v!r}")
    x = float(v)
    if not math.isfinite(x) or x < lo or (hi is not None and x > hi):
        rng = f"[{lo}, {hi}]" if hi is not None else f">= {lo}"
        raise ValueError(f"{name} must be finite and {rng}, got {v!r}")
    return x


@dataclass(frozen=True)
class SurfacePlasmonLoss:
    """Declared surface-plasmon loss model of one hologram (module docstring). Every field is
    required (no defaults).

    mean_excitations_object     n_O >= 0: mean number of surface-plasmon excitations of the object
                                arm per reflection (PROJECT_INPUT: an energy-filtered EELS of the
                                specular beam at the working angle, a new request under item 21;
                                stand-in B38)
    object_label                qualified evidence label of n_O
    mean_excitations_reference  n_R >= 0 (R1/R3: 0, R2: n_O; ``for_reference_model``)
    reference_label             qualified evidence label of n_R
    loss_visibility             V_loss in [0, 1] (item 16; stand-in B39)
    visibility_label            qualified evidence label of V_loss
    energy_filter               "none" (every electron detected) or "zero_loss"
    energy_filter_label         qualified evidence label of the filter declaration"""
    mean_excitations_object: float
    object_label: str
    mean_excitations_reference: float
    reference_label: str
    loss_visibility: float
    visibility_label: str
    energy_filter: str
    energy_filter_label: str

    def __post_init__(self):
        object.__setattr__(self, "mean_excitations_object",
                           _num("mean_excitations_object", self.mean_excitations_object, 0.0, 50.0))
        object.__setattr__(self, "mean_excitations_reference",
                           _num("mean_excitations_reference", self.mean_excitations_reference,
                                0.0, 50.0))
        object.__setattr__(self, "loss_visibility",
                           _num("loss_visibility", self.loss_visibility, 0.0, 1.0))
        for name, what in (("object_label", "surface-plasmon excitation number (item 21)"),
                           ("reference_label", "reference-arm excitation number"),
                           ("visibility_label", "loss-electron visibility (item 16)"),
                           ("energy_filter_label", "energy-filter declaration")):
            require_evidence_label(getattr(self, name), what, accepted=_LABELS, qualified=True)
        if self.energy_filter not in ENERGY_FILTERS:
            raise ValueError(f"energy_filter must be one of {ENERGY_FILTERS}, got "
                             f"{self.energy_filter!r}")

    # -- factors ---------------------------------------------------------------------------------
    @property
    def zero_loss_amplitude_object(self) -> float:
        return math.exp(-0.5 * self.mean_excitations_object)

    @property
    def zero_loss_amplitude_reference(self) -> float:
        return math.exp(-0.5 * self.mean_excitations_reference)

    @property
    def loss_fraction_object(self) -> float:
        return -math.expm1(-self.mean_excitations_object)

    @property
    def loss_fraction_reference(self) -> float:
        return -math.expm1(-self.mean_excitations_reference)

    def fringe_factor(self) -> float:
        """F: the factor multiplying the lossless fringe (sideband) term (module docstring)."""
        f = self.zero_loss_amplitude_object * self.zero_loss_amplitude_reference
        if self.energy_filter == "none":
            f += self.loss_visibility * math.sqrt(self.loss_fraction_object
                                                  * self.loss_fraction_reference)
        return f

    def detected_fractions(self) -> tuple[float, float]:
        """Fraction of each arm's intensity that is detected: 1 (no filter) or exp(-n) (zero-loss)."""
        if self.energy_filter == "none":
            return 1.0, 1.0
        return math.exp(-self.mean_excitations_object), math.exp(-self.mean_excitations_reference)

    def as_record(self) -> dict:
        return dict(
            model="surface-plasmon losses, Poisson excitation, coherent-state bookkeeping "
                  "(optics.inelastic docstring; DERIVED_HERE)",
            mean_excitations_object=self.mean_excitations_object, object_label=self.object_label,
            mean_excitations_reference=self.mean_excitations_reference,
            reference_label=self.reference_label, loss_visibility=self.loss_visibility,
            visibility_label=self.visibility_label, energy_filter=self.energy_filter,
            energy_filter_label=self.energy_filter_label,
            zero_loss_amplitude_object=self.zero_loss_amplitude_object,
            zero_loss_amplitude_reference=self.zero_loss_amplitude_reference,
            loss_fraction_object=self.loss_fraction_object,
            loss_fraction_reference=self.loss_fraction_reference,
            fringe_factor=self.fringe_factor(),
            phase="unchanged (the fringe factor is real and positive)")


def for_reference_model(reference_model: str, *, mean_excitations: float, excitation_label: str,
                        loss_visibility: float, visibility_label: str, energy_filter: str,
                        energy_filter_label: str) -> SurfacePlasmonLoss:
    """The loss model of a reference scheme: R1 and R3 (vacuum references) n_R = 0; R2 (self-
    reference from the same surface) n_R = n_O (module docstring). All arguments required."""
    if reference_model in ("R1", "R3"):
        n_r, lab = 0.0, R1_REFERENCE_LABEL
    elif reference_model == "R2":
        n_r, lab = mean_excitations, R2_REFERENCE_LABEL
    else:
        raise ValueError(f"reference model must be R1, R2 or R3, got {reference_model!r}")
    return SurfacePlasmonLoss(mean_excitations_object=mean_excitations,
                              object_label=excitation_label, mean_excitations_reference=n_r,
                              reference_label=lab, loss_visibility=loss_visibility,
                              visibility_label=visibility_label, energy_filter=energy_filter,
                              energy_filter_label=energy_filter_label)


def inelastic_pair_intensity(u_o: np.ndarray, u_r: np.ndarray, loss: SurfacePlasmonLoss
                             ) -> np.ndarray:
    """I of the module docstring for one realisation (arrays of equal shape). For n_O = n_R = 0
    it is |u_o + u_r|^2 bit for bit (factors exactly 1.0 and 0.0)."""
    if not isinstance(loss, SurfacePlasmonLoss):
        raise TypeError("loss must be a SurfacePlasmonLoss (declare it; no default)")
    a_o, a_r = loss.zero_loss_amplitude_object, loss.zero_loss_amplitude_reference
    intensity = np.abs(a_o * u_o + a_r * u_r) ** 2
    if loss.energy_filter == "none":
        l_o, l_r = loss.loss_fraction_object, loss.loss_fraction_reference
        intensity = (intensity + (l_o * np.abs(u_o) ** 2 + l_r * np.abs(u_r) ** 2)
                     + 2.0 * loss.loss_visibility * math.sqrt(l_o * l_r)
                     * np.real(u_o * np.conj(u_r)))
    return intensity


def fringe_contrast_with_losses(amplitude_object: float, amplitude_reference: float,
                                loss: SurfacePlasmonLoss) -> float:
    """Fringe contrast mu of two uniform lossless waves of amplitudes A_O, A_R under the loss model:
    2 A_O A_R F / (f_O A_O^2 + f_R A_R^2) (f the detected fractions). The noise model
    sqrt(2)/(mu sqrt(N)) (quantification.noise, SM12) must use this reduced mu."""
    a = _num("amplitude_object", amplitude_object, 0.0, None)
    b = _num("amplitude_reference", amplitude_reference, 0.0, None)
    if not (a > 0 and b > 0):
        raise ValueError("amplitudes must be > 0")
    f_o, f_r = loss.detected_fractions()
    return 2.0 * a * b * loss.fringe_factor() / (f_o * a * a + f_r * b * b)
