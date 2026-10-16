"""Tests for reflection_holo.multislice.potential (rung R2, item 2a).

Run:  pytest tests/test_potential.py -v
Expected: all tests PASSED.
"""
import warnings

import numpy as np
import pytest

from reflection_holo.constants import interaction_constant
from reflection_holo.project_inputs import MissingProjectInput
from reflection_holo.multislice import potential as P


def test_prefactor_matches_card():
    """External fact: 2 pi e a0 = 47.86 V*A^2 printed [kirkland_ch06 p.7, Eq. 6.10]. Tol 0.1 %."""
    assert abs(P.PREF_V_A2 / 47.86 - 1) < 1e-3


def test_fe0_si():
    """External fact: f_e(0) = sum a/b + sum c = 5.814 A from the printed Si row [kirkland_appC p.12]. Tol 1e-3 A."""
    assert abs(float(P.fe_kirkland(0.0)) - 5.814) < 1e-3


def test_projected_potential_at_0p1A():
    """External fact: v_z^Si(0.1 A) = 0.41 kV*A printed [kirkland_ch04-05 p.26]. Tol 5 % (2-digit print)."""
    v = float(P.projected_atom_realspace(0.1))
    assert abs(v / 410.0 - 1) < 0.05


def test_fourier_vs_realspace_C20():
    """External fact: Eq. C.20 [kirkland_appC p.11] equals the Fourier-built potential (Eqs. 5.20-5.22)
    for B = 0. Compared at r = 0.5-2 A. Tol 2 %."""
    g = P.Grid(ny=256, nz=256, dy=0.05, dz=0.05)
    c = np.array([[6.4, 6.4]])
    V = P.projected_potential(c, 14, g, 0.0, 2.0, absorption=False, bandwidth=None).real
    for r in (0.5, 1.0, 1.5, 2.0):
        j = int(round((6.4 + r) / 0.05))
        ref = float(P.projected_atom_realspace(r))
        assert abs(V[128, j] / ref - 1) < 0.02, (r, V[128, j], ref)


def test_integral_equals_fe0():
    """External fact: f_e(0) = (1/(2 pi e a0)) integral V d^3r [kirkland_appC Eq. C.5]. Tol 1e-10 relative."""
    g = P.Grid(ny=64, nz=96, dy=0.1, dz=0.1)
    V = P.projected_potential(np.array([[3.0, 4.0]]), 14, g, 0.5, 2.0, absorption=False).real
    integ = V.sum() * g.dy * g.dz
    assert abs(integ / (P.PREF_V_A2 * float(P.fe_kirkland(0.0))) - 1) < 1e-10


def test_debye_waller_smears_but_conserves():
    """External fact: T = exp(-B s^2) multiplies f_e; T(0) = 1 [peng_ch14 Eqs. 14.1-14.3]."""
    g = P.Grid(ny=64, nz=64, dy=0.1, dz=0.1)
    a = np.array([[3.2, 3.2]])
    V0 = P.projected_potential(a, 14, g, 0.0, 2.0, absorption=False).real
    V5 = P.projected_potential(a, 14, g, 0.5, 2.0, absorption=False).real
    assert V5.max() < V0.max()
    assert abs(V5.sum() / V0.sum() - 1) < 1e-10


def test_real_without_absorption():
    """External fact: the isolated-atom potential is real [kirkland_ch04-05 p.30]. Imaginary part exactly 0."""
    g = P.Grid(ny=32, nz=32, dy=0.2, dz=0.2)
    V = P.projected_potential(np.array([[1.0, 2.0], [3.0, 4.0]]), 14, g, 0.5, 2.0, absorption=False)
    assert np.all(V.imag == 0)


def test_unverified_absorption_raises():
    """External fact: no Si absorptive parameters exist on the card [peng_ch13 p.20], so the run must fail loudly."""
    g = P.Grid(ny=16, nz=16, dy=0.2, dz=0.2)
    m = {"name": "proportional", "parameters": {"fraction": 0.1}, "label": "ASSUMPTION", "source": "test"}
    with pytest.raises(MissingProjectInput):
        P.projected_potential(np.array([[1.0, 1.0]]), 14, g, 0.5, 2.0, absorption_model=m)


def test_accepted_proportional_absorption():
    """ASSUMPTION model W = kappa V, once explicitly accepted. Tol 1e-12 relative."""
    g = P.Grid(ny=16, nz=16, dy=0.2, dz=0.2)
    m = {"name": "proportional", "parameters": {"fraction": 0.1}, "label": "ASSUMPTION", "source": "test"}
    V = P.projected_potential(np.array([[1.0, 1.0]]), 14, g, 0.5, 2.0, absorption_model=m,
                              accept_assumptions=True)
    assert np.allclose(V.imag, 0.1 * V.real, rtol=0, atol=1e-12 * np.abs(V.real).max())


def test_frozen_phonon_variance():
    """External fact: B = (8/3) pi^2 <u^2>_3D, so the per-axis variance is B/(8 pi^2) [peng_ch14 Eq. 14.3].
    B = 0.5261 A^2 (Si, 300 K, from the Table 14.2 polynomial). Tol 2 %."""
    u = P.frozen_phonon_displacements(200000, 0.5261, 7)
    assert np.allclose(u.var(axis=0) / (0.5261 / (8 * np.pi**2)), 1.0, atol=0.02)


def test_transmission_attenuates():
    """DERIVED_HERE (E7): t = exp(i sigma v) with Im v > 0 gives |t| < 1 [kirkland_ch06 Eq. 6.59]."""
    t = P.transmission_function(np.array([10 + 2j]), interaction_constant(200e3))
    assert abs(t[0]) < 1


def test_absorber_profile_shape():
    """Design check: W = 0 above z_top, >= 0 below, maximal at the bottom; dx_slice required."""
    g = P.Grid(ny=4, nz=200, dy=1.0, dz=0.5)
    A = P.absorber_profile(g, 60.0, 10.0, "cos2", dx_slice=2.0)
    W = A.imag[:, 0] / 2.0
    assert np.all(W[g.z >= 60] == 0) and np.all(W >= 0)
    assert abs(W[0] - 10.0) < 1e-12
    with pytest.raises(TypeError):
        P.absorber_profile(g, 60.0, 10.0)


def test_thin_slice_warns():
    """External fact: minimum slice thickness about 1 A [kirkland_ch06 p.33, Eq. 6.90]."""
    g = P.Grid(ny=8, nz=8, dy=0.2, dz=0.2)
    with pytest.warns(UserWarning):
        P.projected_potential(np.array([[0.5, 0.5]]), 14, g, 0.5, 0.5, absorption=False)
