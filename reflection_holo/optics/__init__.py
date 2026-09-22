"""reflection_holo.optics (see docs/05_final_repository_specification.md sections 3 and 5).

Implemented (S1c): declared grids, waves and holograms (``fields``); hologram formation with the
reference models R1/R2/R3, ensemble averaging after squaring, charging phase option and Poisson
detector noise (``hologram``). Not implemented: dark-field aperture selection, projection along k_out,
lens transfer, biprism Fresnel fringes, drift, partial-coherence ensembles, detector MTF.
"""
from reflection_holo.optics.fields import Grid, Hologram, Wave, sha256_array  # noqa: F401
from reflection_holo.optics.hologram import (  # noqa: F401
    APERTURE_PASSAGES, REFERENCE_MODELS, ArtefactOptions, apply_poisson_noise,
    ensemble_hologram_intensity, fringe_contrast, hologram_intensity, make_reference,
    reference_r1_vacuum_plane_wave, reference_r2_self_reference, reference_r3_curved_tilted,
    vacuum_object_wave)
