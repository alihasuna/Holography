"""Exceptions raised by the geometry guards (docs/05_final_repository_specification.md section 4.1).

Every guard REFUSES (raises) instead of warning, so that no result can be produced from a forbidden,
inaccessible or badly sampled configuration without the caller handling the error explicitly.
"""
from __future__ import annotations


class GeometryError(ValueError):
    """Base class of the geometry guards."""


class ForbiddenReflectionError(GeometryError):
    """Raised when a kinematically forbidden reflection (F_hkl = 0) is requested as a TARGET.

    Source map SM02 (DERIVED_HERE). Examples: (2,-2,2), (6,-6,6), (10,-10,10) on the CFG-A rod;
    (002), (006), (0,0,10) on the CFG-B rod.
    """


class InaccessibleReflectionError(GeometryError):
    """Raised when a reflection cannot connect two vacuum-propagating beams (G.n_hat < 2 dK, SM06),
    or when an internal angle is below the escape angle theta_c (SM04)."""


class NotSpecularError(GeometryError):
    """Raised when a reflection requested as specular is not parallel to the outward normal."""


class SamplingError(GeometryError):
    """Raised when an angle lies outside the anti-aliasing band of a grid (SM15)."""
