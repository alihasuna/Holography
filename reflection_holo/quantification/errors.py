"""Exceptions of the quantification layer (docs/05 section 5 item 8). Each is a refusal: no height is
returned when one of these is raised. Source map SM03 and SM05; evidence DERIVED_HERE."""
from __future__ import annotations


class QuantificationError(ValueError):
    """Base class."""


class SmallDenominatorError(QuantificationError):
    """The sensitivity |q.n_hat| is not larger than its propagated uncertainty: refuse, never divide."""


class BranchAmbiguityError(QuantificationError):
    """The 2 pi branch of a rocking series is unresolved (criterion B16): the intercept standard
    error is not below pi/3, the intercept is not consistent with 2 pi n at 3 sigma (not a single
    lattice-translation height), or the residual chi-square is inconsistent with the declared
    phase uncertainties. The message starts with "branch unresolved"."""


class TiltStepTooLargeError(QuantificationError):
    """Consecutive tilts of a rocking series can change the phase by pi or more for |h| <= h_max,
    once three standard deviations of the increment's noise are included (criterion B16)."""
