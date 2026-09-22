"""Exceptions of the quantification layer (docs/05 section 5 item 8). Each is a refusal: no height is
returned when one of these is raised. Source map SM03 and SM05; evidence DERIVED_HERE."""
from __future__ import annotations


class QuantificationError(ValueError):
    """Base class."""


class SmallDenominatorError(QuantificationError):
    """The sensitivity |q.n_hat| is not larger than its propagated uncertainty: refuse, never divide."""


class BranchAmbiguityError(QuantificationError):
    """A rocking series is inconsistent with a single lattice-translation height (the fitted
    intercept is not an integer number of 2 pi within the stated tolerance)."""


class TiltStepTooLargeError(QuantificationError):
    """Consecutive tilts of a rocking series can change the phase by pi or more for |h| <= h_max."""
