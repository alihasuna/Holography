"""reflection_holo.forward.geometric: the geometric-phase reflection model (docs/05 section 4.5).

Fast engine for pipeline tests and large fields of view. Every output is labelled
"geometric model, no dynamical amplitude, B4 scope applies"; a/4 steps outside the B4 scope are
refused (``OutsideB4ScopeError``).
"""
from reflection_holo.forward.geometric.model import (  # noqa: F401
    ENGINE_NAME, EXIT_PLANE, GEOMETRIC_LABEL, STATUS, FieldLayout, GeometricParams, GeometricRun,
    OutsideB4ScopeError, TerraceModel, field_length_A, geometric_exit_wave, require_b4_scope,
    terrace_model_from_structure, trace_exit_points)
