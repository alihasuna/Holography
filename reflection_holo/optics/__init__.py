"""reflection_holo.optics (see docs/05_final_repository_specification.md sections 3 and 5).

Implemented (S1c, P1): declared grids, waves and holograms (``fields``); hologram formation with
the reference models R1/R2/R3, ensemble averaging after squaring, charging phase option and Poisson
detector noise (``hologram``); dark-field aperture selection around k_out (``darkfield``);
projection along k_out onto surface and image coordinates (``projection``); magnification, pixel
mapping and detector recording (``detector``); report E3: convergence ensembles (source
quadrature, members, illumination phases: ``coherence``), surface-plasmon losses (``inelastic``) and
their incoherent hologram formation (``hologram.partially_coherent_hologram``). Not implemented:
lens transfer, biprism Fresnel fringes, drift, source-size and energy-spread ensembles, detector
MTF (audit A3 n2).
"""
from reflection_holo.optics.fields import Grid, Hologram, Wave, sha256_array  # noqa: F401
from reflection_holo.optics.hologram import (  # noqa: F401
    APERTURE_PASSAGES, REFERENCE_MODELS, ArtefactOptions, apply_poisson_noise,
    ensemble_hologram_intensity, fringe_contrast, hologram_intensity, make_reference,
    reference_r1_vacuum_plane_wave, reference_r2_self_reference, reference_r3_curved_tilted,
    vacuum_object_wave, MemberPairs, inelastic_hologram_intensity, partially_coherent_hologram)
from reflection_holo.optics.inelastic import (  # noqa: F401
    SurfacePlasmonLoss, fringe_contrast_with_losses, inelastic_pair_intensity)
