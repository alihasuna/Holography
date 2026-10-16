"""Grazing-incidence (beam-perpendicular, Peng-Cowley) multislice kernel.
Packaging only (DERIVED_HERE, no physics). Submodules are imported lazily by name to keep
import-time coupling minimal; integration glue fixed by the orchestrator on 2026-10-16."""
from . import potential, propagate  # noqa: F401
from .potential import (Grid, SlicePotential, projected_potential, absorber_profile,  # noqa: F401
                        frozen_phonon_displacements, transmission_function)
from .propagate import fresnel_propagator, multislice, flux  # noqa: F401
__all__ = ["Grid", "SlicePotential", "projected_potential", "absorber_profile", "frozen_phonon_displacements",
           "transmission_function", "fresnel_propagator", "multislice", "flux", "potential", "propagate"]
