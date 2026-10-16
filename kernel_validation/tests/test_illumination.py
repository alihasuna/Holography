"""Tests for multislice/illumination.py (R2 item 2c).

Grid note (integration fix): the propagator band-limits to 2/3 * min(1/(2dy), 1/(2dz))
(propagate.fresnel_propagator; test_propagate.test_bandwidth_two_thirds). The former test grid
(dy = 0.48 A) put that circle at 0.694/A, below the 20 mrad beam at 0.797/A, so the propagator deleted
the beam. The grid keeps the same 3.84 A width with dy = 0.12 A (circle 2.78/A).
"""
import numpy as np
import pytest

from reflection_holo.constants import wavelength
from reflection_holo.multislice.potential import Grid
from reflection_holo.multislice.propagate import flux, fresnel_propagator, multislice
from reflection_holo.multislice.illumination import (incident_wave, end_face_fraction, soft_window,
                                                     z_axis, plateau_amplitude)

E = 200e3
LAM = wavelength(E)


def _grid():
    return Grid(32, 4096, 0.12, 0.08, 0.0, 0.0)


def test_unit_flux():
    """External fact: CONTRACT says the incident wave is normalised to unit flux. Tolerance 1e-12."""
    g = _grid()
    psi = incident_wave(g, 20e-3, LAM, 100.0, (103.0, 150.0), 3.0)
    assert abs(flux(psi, g) - 1.0) < 1e-12


def test_end_face_fraction_entrance_and_after_one_slice():
    """External fact: task 2c requires end-face transmitted fraction < 1e-3.

    At the entrance plane the compact cos^2 window gives exactly 0. After one vacuum slice through the
    band-limited Fresnel propagator the fraction must still be < 1e-3.
    """
    g = _grid()
    zs = 100.0
    psi = incident_wave(g, 20e-3, LAM, zs, (zs + 3.0, zs + 50.0), 3.0)
    assert end_face_fraction(psi, g, zs) == 0.0
    P = fresnel_propagator(g, 1.92, LAM)
    psi1 = multislice(psi, [np.ones_like(psi)], P)
    assert end_face_fraction(psi1, g, zs) < 1e-3


def test_phase_ramp_direction():
    """External fact: repo convention 'numpy fft: a tilted plane wave exp(+2 pi i q0.r) appears at +q0'.

    A beam toward -z must therefore peak at q = -sin(theta)/lambda, within one FFT bin.
    """
    g = _grid()
    th = 20e-3
    psi = incident_wave(g, th, LAM, 100.0, (103.0, 300.0), 3.0)
    spec = np.abs(np.fft.fft(psi[:, 0])) ** 2
    q = np.fft.fftfreq(g.nz, g.dz)
    assert abs(q[np.argmax(spec)] - (-np.sin(th) / LAM)) <= 1.0 / (g.nz * g.dz) + 1e-12


def test_window_and_plateau():
    """External fact: the mask edge must be rounded, not sharp (NOTES_C 2c).

    The window is continuous (max step < 0.05 per 0.08 A) and the plateau amplitude equals |psi| at the
    centre. Tolerance 1e-12.
    """
    g = _grid()
    z = z_axis(g)
    w = soft_window(z, (103.0, 150.0), 3.0)
    assert np.max(np.abs(np.diff(w))) < 0.05
    psi = incident_wave(g, 20e-3, LAM, 100.0, (103.0, 150.0), 3.0)
    i = np.argmin(abs(z - 126.5))
    assert abs(plateau_amplitude(psi, g, (103.0, 150.0)) - abs(psi[i, 0])) < 1e-12


def test_guards():
    """External fact: 2/3 bandwidth rule (calculator sec.9 / T22: 16.7 mrad at 0.5 A, 200 keV).

    A 40 mrad tilt on a 0.5 A grid must raise, and so must a window reaching below the surface.
    """
    g = Grid(8, 1024, 0.5, 0.5, 0.0, 0.0)
    with pytest.raises(ValueError):
        incident_wave(g, 40e-3, LAM, 100.0, (103.0, 200.0), 3.0)
    with pytest.raises(ValueError):
        incident_wave(_grid(), 20e-3, LAM, 100.0, (99.0, 150.0), 3.0)
