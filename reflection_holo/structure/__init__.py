"""reflection_holo.structure (see docs/05_final_repository_specification.md sections 3 and 4.2).

Si(001) terrace builder with the spec 4.2 assertions (``si001``), assertion primitives (``checks``),
diamond-lattice primitives (``lattice``), shadowed strips and patterned features (``shadows``) and an
extended-XYZ writer that records the frame (``xyz``).
"""
from .checks import StructureAssertionError
from .shadows import (EdgeProfile, PatternedFeature, ShadowStrips, feature_shadow_intervals,
                      feature_shadow_mask, shadow_length_A, terrace_shadow_strips)
from .si001 import (OverlayerSpec, Si001Structure, Staircase, StaircaseError,
                    build_si001_terraces, find_terrace_relations, validate_staircase)
from .xyz import read_xyz, write_metadata_json, write_xyz

__all__ = [
    "StructureAssertionError", "EdgeProfile", "PatternedFeature", "ShadowStrips",
    "feature_shadow_intervals", "feature_shadow_mask", "shadow_length_A", "terrace_shadow_strips",
    "OverlayerSpec", "Si001Structure", "Staircase", "StaircaseError", "build_si001_terraces",
    "find_terrace_relations", "validate_staircase", "read_xyz", "write_metadata_json", "write_xyz",
]
