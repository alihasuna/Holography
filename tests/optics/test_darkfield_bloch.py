"""Dark-field selection of an azimuthally tilted convergence member (report E3 section 2.2):
the exit wave is the Bloch envelope u of the physical wave u exp(2 pi i f_y y); the objective
aperture stays centred on the CENTRAL k_out and is applied to the PHYSICAL directions
(lambda q_x, lambda (q_y' + f_y)). TEST_ONLY grid, angle and aperture. Exact checks only (a plane
wave on a grid frequency passes entirely or not at all)."""
import numpy as np
import pytest

from reflection_holo.forward.contracts import ExitWave
from reflection_holo.geometry.wavelength import wavelength_A
from reflection_holo.optics.darkfield import DarkFieldAperture, select_dark_field

LAM = wavelength_A(200.0)
NX, NY, DX, DY = 256, 64, 0.1, 0.5
M_X = 17                                            # q_out on the grid: sin(theta) = lambda m/(nx dx)
THETA = float(np.arcsin(LAM * M_X / (NX * DX)))
AP = DarkFieldAperture(semi_angle_rad=1e-3, beam="specular", label="TEST_ONLY: item 4")


def wave(qy_native, fb):
    x = np.arange(NX)[:, None] * DX
    y = np.arange(NY)[None, :] * DY
    psi = np.exp(2j * np.pi * (M_X / (NX * DX) * x + qy_native * y))
    meta = {} if fb is None else {"bloch": {"fy_per_A": fb, "direction_cosine_y": fb * LAM}}
    return ExitWave(psi=psi, dx_A=DX, dy_A=DY, x0_A=0.0, y0_A=0.0, plane="exit plane (TEST_ONLY)",
                    z_A=100.0, energy_keV=200.0, theta_in_ext_rad=THETA, realisation=0, seed=None,
                    metadata=meta)


def passed(ew):
    return select_dark_field(ew, AP, energy_keV=200.0, theta_out_ext_rad=THETA).record


def test_aperture_acts_on_the_physical_direction_of_a_bloch_envelope():
    step = 1.0 / (NY * DY)                           # 0.03125 1/A = 0.78 mrad of y tilt
    fb = 0.1                                         # member tilt 2.5 mrad in y (off-grid)
    near = -3 * step                                 # native component, physical 0.00625 1/A
    # physical 0.157 mrad from k_out: inside the 1 mrad aperture only with the Bloch shift
    r = passed(wave(near, fb))
    assert r["fraction_of_power_passed"] == pytest.approx(1.0, abs=1e-12)
    assert r["bloch_fy_per_A"] == fb and "Bloch envelope" in r["bloch_note"]
    r = passed(wave(0.0, fb))                        # physical 2.5 mrad: outside
    assert r["fraction_of_power_passed"] == pytest.approx(0.0, abs=1e-12)
    # without the Bloch record the same arrays are read as physical waves: the opposite result
    assert passed(wave(near, None))["fraction_of_power_passed"] == pytest.approx(0.0, abs=1e-12)
    assert passed(wave(0.0, None))["fraction_of_power_passed"] == pytest.approx(1.0, abs=1e-12)
    assert passed(wave(0.0, None))["bloch_fy_per_A"] == 0.0


def test_zero_bloch_frequency_is_the_untilted_computation():
    a = select_dark_field(wave(0.0, None), AP, energy_keV=200.0, theta_out_ext_rad=THETA)
    b = select_dark_field(wave(0.0, 0.0), AP, energy_keV=200.0, theta_out_ext_rad=THETA)
    assert np.array_equal(a.wave.data, b.wave.data)
