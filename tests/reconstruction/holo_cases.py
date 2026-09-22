"""Shared synthetic cases for the reconstruction tests (not a test module).

The calculator (tools/reflection_step_phase_calculator.py) is imported by path so that its reference
values are used EXACTLY, never re-typed. TEST_ONLY: the 1.0 A pixel size on both axes and the
"no_aperture" R1 declaration stand in for PROJECT_INPUT items 5 and 16; they never appear in configs/.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

from reflection_holo.optics import (ArtefactOptions, Grid, Wave, apply_poisson_noise, hologram_intensity,
                                    reference_r1_vacuum_plane_wave, vacuum_object_wave)
from reflection_holo.reconstruction import (CarrierSearch, MaskSpec, locate_carrier, reconstruct_sideband,
                                            wrap_to_pi)

REPO = Path(__file__).resolve().parents[2]
CALCULATOR_PATH = REPO / "tools" / "reflection_step_phase_calculator.py"

# Tolerances of checks T24 and T25 as written in the calculator (section 13, chk(...) calls);
# test_calculator_definitions_unchanged asserts that the calculator source still says so.
T24_TOL_RAD = 5e-3
T25_TOL_RAD = 5e-3

TEST_PIXEL_A = 1.0          # TEST_ONLY (stands in for PROJECT_INPUT item 5)
NO_ARTEFACTS = ArtefactOptions(biprism_fresnel_fringes=None, drift=None, charging_phase_rad=None)

_calc = None


def calculator():
    """The calculator module, imported once by path."""
    global _calc
    if _calc is None:
        spec = importlib.util.spec_from_file_location("reflection_step_phase_calculator", CALCULATOR_PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _calc = mod
    return _calc


def calculator_T24_reference() -> tuple[float, float]:
    """(wrapped, mod2pi) of sc666.step_phase(d111), built exactly as the calculator's main() does."""
    c = calculator()
    d111 = c.A_SI_A / np.sqrt(3.0)
    sc666 = c.SpecularCondition(d111, 6, 200.0, c.V0_SI_V)
    return float(sc666.step_phase(d111)["wrapped"]), float(sc666.step_phase(d111)["mod2pi"])


def make_grid(n: int) -> Grid:
    return Grid(shape=(n, n), pixel_size_A=(TEST_PIXEL_A, TEST_PIXEL_A), axes=("y", "x"),
                plane="image plane, specimen coordinates (TEST_ONLY synthetic)")


def calculator_step_object(grid: Grid, dphi_rad: float) -> Wave:
    """The calculator's object: unit amplitude, phase dphi * 0.5 (1 + tanh((y - n/2)/2)) along axis 0."""
    n0 = grid.shape[0]
    y = np.arange(n0, dtype=float)[:, None] * np.ones((1, grid.shape[1]))
    soft = 0.5 * (1.0 + np.tanh((y - n0 // 2) / 2.0))
    return Wave(np.exp(1j * dphi_rad * soft), grid, "two terraces (calculator section 12)", None)


def r1_reference(grid: Grid, carrier, relative_phase_rad: float = 0.0, amplitude: float = 1.0) -> Wave:
    return reference_r1_vacuum_plane_wave(grid, carrier_cycles_per_A=carrier, amplitude=amplitude,
                                          relative_phase_rad=relative_phase_rad,
                                          aperture_passage="no_aperture", realisation=None)


def calculator_measure(phase: np.ndarray, res_px: float, n: int) -> tuple[float, float]:
    """The calculator's step estimate: medians of the terrace interiors (pad = 3 resolutions)."""
    edge = n // 2
    pad = int(min(max(3.0 * res_px, 8), n // 4 - 1))
    lo = phase[pad:edge - pad, pad:n - pad]
    hi = phase[edge + pad:n - pad, pad:n - pad]
    recovered = float(wrap_to_pi(np.median(hi) - np.median(lo)))
    sigma = float(0.5 * (np.std(wrap_to_pi(lo - np.median(lo))) + np.std(wrap_to_pi(hi - np.median(hi)))))
    return recovered, sigma


def calculator_setup_holograms(dphi_rad: float, *, n: int = 512, fringe_px: float = 8.0,
                               dose_per_px: float = 0.0, seed: int = 12345, carrier_sign: float = +1.0):
    """Object and empty holograms of the calculator's hologram_roundtrip, formed by the package.

    Reference carrier q_ref = carrier_sign * (0, 1/fringe_px) cycles/A (pixel 1 A, TEST_ONLY), so the
    calculator's u_r = exp(2 pi i x / fringe) for carrier_sign = +1. Noise: one generator seeded with
    ``seed``, object first, then empty (the calculator's draw order).
    """
    grid = make_grid(n)
    q_ref = (0.0, carrier_sign / fringe_px / TEST_PIXEL_A)
    u_r = r1_reference(grid, q_ref)
    H_obj = hologram_intensity(calculator_step_object(grid, dphi_rad), u_r, artefacts=NO_ARTEFACTS,
                               content="object")
    H_emp = hologram_intensity(vacuum_object_wave(grid, amplitude=1.0, realisation=None), u_r,
                               artefacts=NO_ARTEFACTS, content="empty")
    if dose_per_px > 0:
        H_obj, H_emp = apply_poisson_noise([H_obj, H_emp], dose_e_per_px=dose_per_px, seed=seed)
    return grid, q_ref, H_obj, H_emp


def calculator_search(q_ref, subpixel: str) -> CarrierSearch:
    """Search disc of radius |q|/2 about the phi_o - phi_r sideband (-q_ref), excluding the
    calculator's centre disc r < 0.05 cycles/px."""
    qm = float(np.hypot(*q_ref))
    return CarrierSearch(sideband_guess_cycles_per_A=(-q_ref[0], -q_ref[1]), search_radius_cycles_per_A=0.5 * qm,
                         exclusion_radius_cycles_per_A=0.05 / TEST_PIXEL_A, subpixel=subpixel)


def calculator_mask(carrier) -> MaskSpec:
    """The calculator's aperture: Hann disc of radius |q_c|/3."""
    return MaskSpec(radius_cycles_per_A=carrier.carrier_magnitude_cycles_per_A / 3.0, shape="disc",
                    apodisation="hann")


def roundtrip(dphi_rad: float, *, n: int = 512, fringe_px: float = 8.0, dose_per_px: float = 0.0,
              seed: int = 12345, subpixel: str = "none", carrier_sign: float = +1.0) -> dict:
    """The calculator's T24/T25 procedure through the package chain (carrier on the EMPTY hologram,
    Hann mask |q_c|/3, reference-hologram division, medians of terrace interiors)."""
    grid, q_ref, H_obj, H_emp = calculator_setup_holograms(dphi_rad, n=n, fringe_px=fringe_px,
                                                           dose_per_px=dose_per_px, seed=seed,
                                                           carrier_sign=carrier_sign)
    carrier = locate_carrier(H_emp, calculator_search(q_ref, subpixel))
    res = reconstruct_sideband(H_obj, carrier=carrier, mask=calculator_mask(carrier), empty_hologram=H_emp,
                               reference_correction="divide_empty", unwrapping="none")
    recovered, sigma = calculator_measure(res.wrapped_phase, res.resolution_A / TEST_PIXEL_A, n)
    return {"recovered": recovered, "sigma": sigma, "res_px": res.resolution_A / TEST_PIXEL_A,
            "result": res, "carrier": carrier}
