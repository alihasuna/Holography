"""No-step control helper and shadow-exclusion masks computed from the geometry at the operating
angle (docs/05 section 5 item 8; source map SM07)."""
import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV as E
from reflection_holo.constants import V0_SI_ASSUMPTION_V as V0
from reflection_holo.geometry.projection import shadow_length_A
from reflection_holo.geometry.specular import specular_condition_for
from reflection_holo.quantification.controls import no_step_control
from reflection_holo.quantification.shadow import shadow_masks, terrace_profile_A

D111 = A_SI_A / np.sqrt(3.0)
TH444 = specular_condition_for((4, -4, 4), (1, -1, 1), E_keV=E, V0_V=V0, a_A=A_SI_A).theta_ext
TH008 = specular_condition_for((0, 0, 8), (0, 0, 1), E_keV=E, V0_V=V0, a_A=A_SI_A).theta_ext


# ---------------------------------------------------------------- no-step control
def _two_regions(shape):
    a = np.zeros(shape, bool)
    b = np.zeros(shape, bool)
    a[:, : shape[1] // 2 - 4] = True
    b[:, shape[1] // 2 + 4:] = True
    return a, b


def test_no_step_control_passes_on_flat_noisy_phase_near_wrap():
    rng = np.random.default_rng(7)
    phase = np.pi - 0.01 + rng.normal(0.0, 0.05, (64, 64))     # straddles the +-pi cut
    a, b = _two_regions(phase.shape)
    res = no_step_control(phase, a, b, valid_mask=None, tolerance_rad=0.02)
    assert res.passed, res
    assert abs(res.delta_rad) < 5 * res.sigma_rad + 1e-12


def test_no_step_control_fails_when_a_step_is_present():
    phase = np.zeros((32, 64))
    phase[:, 32:] = 0.3
    a, b = _two_regions(phase.shape)
    res = no_step_control(phase, a, b, valid_mask=None, tolerance_rad=0.02)
    assert not res.passed
    assert abs(res.delta_rad - 0.3) < 1e-12


def test_no_step_control_excludes_invalid_pixels():
    phase = np.zeros((16, 64))
    phase[:, 60:] = 2.0                                   # e.g. a shadowed strip, garbage phase
    a, b = _two_regions(phase.shape)
    valid = np.ones_like(a)
    valid[:, 40:] = False
    b2 = b.copy()
    b2[:, 36:40] = True
    res = no_step_control(phase, a, b2, valid_mask=valid, tolerance_rad=0.02)
    assert res.passed and res.n_b == 16 * 4
    with pytest.raises(ValueError):
        no_step_control(phase, a, a, valid_mask=None, tolerance_rad=0.02)   # overlapping
    with pytest.raises(TypeError):
        no_step_control(phase, a, b, tolerance_rad=0.02)                 # valid_mask required


# ---------------------------------------------------------------- shadow masks
def _strip_length(z, mask_false):
    dz = z[1] - z[0]
    return mask_false.sum() * dz


@pytest.mark.parametrize("theta,h", [(TH444, D111), (TH444, 100.0), (TH008, A_SI_A / 4),
                                     (22.5e-3, 100.0)])
def test_mask_strip_length_equals_h_over_tan_theta(theta, h):
    """The masked strips have the length h/tan(theta) at the operating angle (grid-limited)."""
    L = shadow_length_A(h, theta)
    dz = L / 400.0
    z = np.arange(-2 * L, 3 * L, dz)
    # upper terrace upstream (step DOWN along the beam at z = 0): illumination shadow downstream
    m = shadow_masks(z, edges_A=[0.0], h_start_A=h, heights_after_A=[0.0],
                     theta_in_ext_rad=theta, theta_out_ext_rad=theta)
    assert abs(_strip_length(z, ~m.illuminated) - L) <= dz
    assert m.visible.all()
    shadow_z = z[~m.usable]
    assert shadow_z.min() >= 0.0 and shadow_z.max() < L          # behind the riser
    # upper terrace downstream (step UP along the beam): blocked-view strip upstream of the riser
    m2 = shadow_masks(z, edges_A=[0.0], h_start_A=0.0, heights_after_A=[h],
                      theta_in_ext_rad=theta, theta_out_ext_rad=theta)
    assert abs(_strip_length(z, ~m2.visible) - L) <= dz
    assert m2.illuminated.all()
    blocked_z = z[~m2.usable]
    assert blocked_z.max() < 0.0 and blocked_z.min() >= -L - dz  # in front of the riser


def test_shadow_side_distinguishes_step_sense():
    z = np.linspace(-500, 500, 2001)
    down = shadow_masks(z, edges_A=[0.0], h_start_A=D111, heights_after_A=[0.0],
                        theta_in_ext_rad=TH444, theta_out_ext_rad=TH444)
    up = shadow_masks(z, edges_A=[0.0], h_start_A=0.0, heights_after_A=[D111],
                      theta_in_ext_rad=TH444, theta_out_ext_rad=TH444)
    assert np.all(z[~down.usable] >= 0) and np.all(z[~up.usable] < 0)


def test_masks_use_the_actual_angle_not_a_constant():
    z = np.linspace(-1000, 1000, 4001)
    kw = dict(edges_A=[0.0], h_start_A=D111, heights_after_A=[0.0])
    a = shadow_masks(z, theta_in_ext_rad=TH444, theta_out_ext_rad=TH444, **kw)
    b = shadow_masks(z, theta_in_ext_rad=2 * TH444, theta_out_ext_rad=2 * TH444, **kw)
    assert (~a.usable).sum() > 1.9 * (~b.usable).sum()


def test_staircase_profile_and_incidence_vs_exit_angles():
    """Two down-steps: each casts its own illumination shadow of h/tan(theta_in); unequal
    in/out angles use theta_in for the illumination shadow."""
    z = np.linspace(-200, 1400, 16001)
    dz = z[1] - z[0]
    th_in, th_out = 0.02, 0.03
    m = shadow_masks(z, edges_A=[0.0, 600.0], h_start_A=2 * D111,
                     heights_after_A=[D111, 0.0], theta_in_ext_rad=th_in,
                     theta_out_ext_rad=th_out)
    L = shadow_length_A(D111, th_in)
    assert abs(_strip_length(z, ~m.illuminated) - 2 * L) <= 2 * dz
    h = terrace_profile_A(np.array([-1.0, 0.0, 599.0, 600.0]), edges_A=[0.0, 600.0],
                          h_start_A=2.0, heights_after_A=[1.0, 0.0])
    assert list(h) == [2.0, 1.0, 1.0, 0.0]
