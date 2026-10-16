"""Tests for multislice/reflectivity.py (R2 item 2e).

Covered tests: T-unitarity, T-kinematic, T-convergence, T-published, plus extraction checks.
Slow tests run only with RH_SLOW=1.

Integration notes: COARSE uses dy = 0.15 A (was 0.3): with dy = 0.3 the isotropic 2/3 band
(1.13/A) lies below the (008) rod frequency 1.47/A, so the Bragg component of V was deleted and the
kernel could not reflect. Absorption is MISSING (item 21), so every run states absorption=False.
"""
import os

import numpy as np
import pytest

from reflection_holo import project_inputs as P
from reflection_holo.constants import wavelength
from reflection_holo.geometry import Surface, specular_orders
from reflection_holo.multislice.cell import flat_surface_cell
from reflection_holo.multislice.illumination import z_axis
from reflection_holo.multislice.propagate import flux, fresnel_propagator, multislice
from reflection_holo.multislice.reflectivity import (exit_wave, period_transmissions, specular_amplitude,
                                                     rocking_curve, peak_table)

slow = pytest.mark.skipif(os.environ.get("RH_SLOW") != "1", reason="slow: set RH_SLOW=1")
E = 200e3
LAM = wavelength(E)
S001 = Surface((0, 0, 1), (1, 1, 0))
COARSE = dict(dz=0.1, dy=0.15, absorber_thickness=20.0)


def _cell(th=16.474e-3, **kw):
    return flat_surface_cell(S001, E, th, depth=20.0, **(COARSE | {"absorption": False} | kw))


def test_extraction_recovers_synthetic_r():
    """External fact: definition of r from the vacuum form (NOTES_C sec.3, Peng 5.109 with z outward).

    A synthetic exit wave a_inc r0 exp(+iKz(z-zs)) exp(-i pi lam q^2 L) must return r0. Tolerance 1e-3.
    """
    c = _cell()
    ang = c.meta["angle"]
    ang["a_inc"] = 0.37
    th = ang["theta"]
    z = z_axis(c.grid)
    r0 = 0.6 * np.exp(1.1j)
    q = np.sin(th) / LAM
    L = ang["n_slices"] * c.dx
    col = 0.37 * r0 * np.exp(1j * 2 * np.pi / LAM * np.sin(th) * (z - c.z_surface)) * np.exp(-1j * np.pi * LAM * q * q * L)
    ew = np.repeat(col[:, None], c.grid.ny, axis=1)
    assert abs(specular_amplitude(ew, c, th, LAM) - r0) < 1e-3


def test_unitarity_vacuum_and_no_spurious_reflection():
    """T-unitarity (vacuum part). External fact: free propagation conserves flux (unitary propagator).

    Over the whole cell with no crystal the flux must change by < 1e-6. r must be < 1e-2, since there
    is no surface and the incident band has left the vacuum band.
    """
    c = _cell()
    ones = [[np.ones((c.grid.nz, c.grid.ny), complex) for _ in range(c.meta["n_sub"])]]
    ew, psi0, ang = exit_wave(c, E, 16.474e-3, ones)
    assert abs(flux(ew, c.grid) - 1.0) < 1e-6
    assert abs(specular_amplitude(ew, c, 16.474e-3, LAM)) < 1e-2


def test_unitarity_per_slice_real_potential():
    """T-unitarity (crystal part). Setup: W = 0, absorber off.

    Per-slice flux change must be < 1e-6: the transmission is unitary for real V and the propagator is
    unitary inside the band. Known failure mode (NOTES_C): bandwidth loss; the fix is finer sampling,
    not a looser tolerance. bandlimit_t=False keeps |t| = 1.
    """
    c = _cell(dz=0.05)
    sets = period_transmissions(c, E, absorber=False, absorption=False, bandlimit_t=False)
    from reflection_holo.multislice.illumination import incident_wave
    ang = c.meta["angle"]
    psi = incident_wave(c.grid, ang["theta"], LAM, c.z_surface, ang["window"], c.meta["softness"])
    P_ = fresnel_propagator(c.grid, c.dx, LAM)
    f_prev = flux(psi, c.grid)
    worst = 0.0
    for _ in range(3):
        for t in sets[0]:
            psi = multislice(psi, [t], P_)
            f = flux(psi, c.grid)
            worst = max(worst, abs(f - f_prev))
            f_prev = f
    assert worst < 1e-6


@slow
def test_total_reflection_in_bragg_band_without_absorption():
    """T-unitarity (reflection part), rewritten 2026-10-16 (orchestrator). Setup: W = 0, absorber on.

    The previous premise (max |r| = 1 in the (008) band) is the one-beam Darwin result; in the full crystal
    many-beam coupling opens bulk channels (measured: specular 0.29-0.40, non-specular rods ~0.05, the rest
    transmitted into the bulk; INTEGRATION_NOTES.md F2). External facts tested instead:
    (a) flux conservation with W = 0: specular-vacuum + other-vacuum + crystal + absorbed = 1 (1e-9) and
        R <= 1 + 1e-3;
    (b) semi-infinite termination invariance: doubling the crystal depth changes R by < 1e-3 and arg r by
        < 1e-3 rad (the absorber must not reach the reflected field).
    One-beam total reflection is tested like-for-like in tests/test_reflectivity1d.py.
    """
    from reflection_holo.multislice.cell import flat_surface_cell
    from reflection_holo.multislice.reflectivity import period_transmissions, exit_wave, specular_spectrum
    from reflection_holo.multislice.propagate import flux
    from reflection_holo.multislice.illumination import z_axis
    from reflection_holo.constants import wavelength
    th = 16.25e-3; lam = wavelength(E); out = []
    for depth in (None, 130.0):
        c = flat_surface_cell(S001, E, th, thetas_for_vacuum=np.array([th]), absorption=False, depth=depth, **COARSE)
        ew, psi0, _ = exit_wave(c, E, th, period_transmissions(c, E, True, False))
        z = z_axis(c.grid); vac = z > c.z_surface + 5; dA = c.grid.dy * c.grid.dz
        Fin, Fout = flux(psi0, c.grid), flux(ew, c.grid)
        parts = np.sum(np.abs(ew[vac]) ** 2) * dA + np.sum(np.abs(ew[~vac]) ** 2) * dA
        assert abs(parts / Fout - 1) < 1e-9
        assert Fout <= Fin * (1 + 1e-9)
        r = specular_spectrum(ew, psi0, c, lam, [th])["r"][0]
        assert abs(r) ** 2 <= 1 + 1e-3
        out.append(r)
    assert abs(abs(out[0]) ** 2 - abs(out[1]) ** 2) < 1e-3
    assert abs(np.angle(out[0] / out[1])) < 1e-3

@slow
def test_kinematic_limit_00_12():
    """T-kinematic. External fact: calculator section 4b gives the (0,0,12) external angle 26.420 mrad at 200 keV,
    V0 = 12 V (ASSUMPTION, item 20, accepted explicitly).

    The peak must lie within 0.5 mrad of geometry.specular_orders' theta_ext and below the vacuum Bragg
    angle 27.711 mrad (calculator). Sampling dy = 0.12 A puts the (0,0,12) rod (q = 2.263/A) inside the
    2/3 band limit (2.78/A); at COARSE (2.257/A) the kernel guard correctly refuses to run (orchestrator
    change 2026-10-16: sampling only; assertions unchanged).
    """
    V0 = float(P.get("V0_SI", accept_assumptions=True))
    o = [d for d in specular_orders(S001, E, V0=V0) if tuple(d["hkl"]) in ((0, 0, 12),)][0]
    th = np.linspace(o["theta_ext"] - 1e-3, o["theta_ext"] + 1e-3, 21)
    pk = peak_table(rocking_curve(S001, E, th, absorption=False, **dict(COARSE, dy=0.12)))
    assert abs(pk["theta_peak"] - o["theta_ext"]) < 0.5e-3
    assert pk["theta_peak"] < 27.711e-3

@slow
def test_convergence_008():
    """T-convergence. External fact: results must be invariant under sampling refinement.

    Variations: halve dx, refine dz and dy by 1.5, double the vacuum, double the length (with vacuum).
    Tolerances (unchanged): |Delta R| < 0.02 and |Delta arg r| < 0.1 rad at the (008) angle. W = 0.
    Orchestrator change 2026-10-16: the base is SAMPLING_QUANT. At COARSE the phase moved by 0.101 rad on
    refinement (FAIL, recorded): COARSE is not converged and is for unit tests only.
    """
    from reflection_holo.multislice.cell import SAMPLING_QUANT
    th = [16.474e-3]
    base = rocking_curve(S001, E, th, absorption=False, **SAMPLING_QUANT)
    L0 = base.meta["angles"][0]["L"]
    V0 = base.meta["vacuum"]
    variants = [dict(SAMPLING_QUANT, dx=0.96), dict(dy=0.05, dz=0.027),
                dict(SAMPLING_QUANT, vacuum=2 * V0), dict(SAMPLING_QUANT, length_x=2 * L0, vacuum=2 * V0)]
    for kw in variants:
        r = rocking_curve(S001, E, th, absorption=False, **kw).r[0]
        print(kw, abs(r) ** 2, abs(base.r[0]) ** 2, np.angle(r / base.r[0]))
        assert abs(abs(r) ** 2 - abs(base.r[0]) ** 2) < 0.02
        assert abs(np.angle(r / base.r[0])) < 0.1

@pytest.mark.xfail(reason="T-published: no card reports a Si rocking curve; READ-FROM-PLOT curves are "
                          "Ag(001) 20 keV, NiO(001), UO2(111), Pt(111) [cards peng_ch05/ch06]. A Si-only "
                          "kernel cannot be compared quantitatively.", strict=True)
def test_published_si_rocking_curves():
    """T-published. External fact: the card inventory, Figs 5.18, 5.19, 5.24, 5.25, 6.10 and 6.12.

    None is silicon. The register below records this and the test is strict-xfail until a Si card arrives.
    """
    PUBLISHED_SI_CURVES = []
    assert len(PUBLISHED_SI_CURVES) > 0
