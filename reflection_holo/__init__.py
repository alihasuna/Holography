"""Reflection-mode dark-field electron holography simulation (milestone subset).

Implemented so far: geometry core, buried-dislocation displacement fields in an isotropic
half-space, the geometric-phase forward model with penetration weighting, and a custom
grazing-incidence multislice kernel (numpy or cupy). The multislice kernel is NOT validated
against abTEM or a dynamical reflection solver yet (docs/05 section 4.3, milestone M2); its
outputs are smoke-test results only.

Conventions: docs/physics_conventions.md (exp(+ik.r), angstrom, glancing angles, outward normal).
"""

__version__ = "0.1.0.dev0"
