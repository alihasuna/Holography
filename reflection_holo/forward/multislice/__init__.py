"""reflection_holo.forward.multislice: custom numpy/cupy grazing-incidence reflection multislice
(docs/05 section 4.3; milestone M2). Status: UNVALIDATED for atomistic reflection (see
engine.VALIDATION_STATUS and docs/agent_reports/M2_multislice_engine.md).

Typical use (every argument required; no default stands in for a PROJECT_INPUT):

    cell = forward.cell.build_reflection_cell(structure, vacuum_above_A=..., depth_below_A=...,
                                              bulk_absorber_A=..., top_absorber_A=...,
                                              entrance_vacuum_z_A=...)
    pot = AtomicPotential(cell, parameterisation="kirkland",
                          physical_absorption=PhysicalAbsorption(model="proportional", ratio=...,
                                                                 label="PROJECT_INPUT item 21 ..."),
                          frozen_phonons=None, static_lattice_label="ASSUMPTION ...")
    beam = SheetBeam(height_A=..., edge_A=..., x_bottom_A=..., theta_in_ext_rad=...,
                     theta_label="PROJECT_INPUT item 7 ...")
    params = MultisliceParams(energy_keV=200.0, nx=..., ny=..., dz_A=..., propagator="exact",
                              band_limit="2/3", backend="numpy", precision="complex64",
                              threads=4, absorber=NumericalAbsorber(strength_V=..., profile="sin2"),
                              theta_out_ext_rad=..., buildup_depth_A=...)
    waves, manifest = simulate(cell, potential=pot, beam=beam, params=params, realisations=1,
                               seed=None, outputs_root=".../outputs", run_name="...",
                               save_waves=True, config=None, input_paths=[])
"""
from .analysis import (analytic_step_reflection, flat_reflection_coefficient,
                       geometric_step_phase, refracted_frequency, select_beam,
                       terrace_step_phase, wrap)
from .engine import (GPU_ASSUMED, PLANE_TEXT, VALIDATION_STATUS, MultisliceParams,
                     estimate_resources, propagate_slices, reflection_setup, run_realisation,
                     simulate)
from .exitwave_io import ExitWaveFileError, load_exit_wave, save_exit_wave
from .grid import (BAND_LIMIT_RULES, Grid, band_limit_mask, check_band, fft_friendly,
                   grid_shape_for_pixel, make_grid)
from .illumination import SheetBeam, sheet_beam_wave
from .physics import beam_constants, interaction_constant_rad_per_VA, require_beam_energy
from .potentials import (AtomicPotential, ContinuumTerracePotential, FrozenPhonons,
                         NumericalAbsorber, PhysicalAbsorption, absorber_profile_V,
                         potential_mean_inner_potential_V)
from .propagator import propagate, propagator_kernel, propagator_phase

__all__ = [
    "analytic_step_reflection", "flat_reflection_coefficient", "geometric_step_phase",
    "refracted_frequency", "select_beam", "terrace_step_phase", "wrap",
    "GPU_ASSUMED", "PLANE_TEXT", "VALIDATION_STATUS", "MultisliceParams", "estimate_resources",
    "propagate_slices", "reflection_setup", "run_realisation", "simulate",
    "ExitWaveFileError", "load_exit_wave", "save_exit_wave",
    "BAND_LIMIT_RULES", "Grid", "band_limit_mask", "check_band", "fft_friendly",
    "grid_shape_for_pixel", "make_grid", "SheetBeam", "sheet_beam_wave",
    "beam_constants", "interaction_constant_rad_per_VA", "require_beam_energy",
    "AtomicPotential", "ContinuumTerracePotential", "FrozenPhonons", "NumericalAbsorber",
    "PhysicalAbsorption", "absorber_profile_V", "potential_mean_inner_potential_V", "propagate", "propagator_kernel",
    "propagator_phase",
]
