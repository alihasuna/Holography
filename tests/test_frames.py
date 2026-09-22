import numpy as np
import pytest

from reflection_holo.geometry.frames import surface_frame


def test_cfg_a_frame_matches_conventions():
    f = surface_frame((1, -1, 1), (1, 1, 0))
    assert np.allclose(f.x_hat, np.array([1, -1, 1]) / np.sqrt(3))
    assert np.allclose(f.y_hat, np.array([1, -1, -2]) / np.sqrt(6))
    assert np.allclose(f.z_hat, np.array([1, 1, 0]) / np.sqrt(2))
    assert np.allclose(np.cross(f.x_hat, f.y_hat), f.z_hat)


@pytest.mark.parametrize("az", [(1, 1, 0), (1, 0, 0), (1, -1, 0), (0, 1, 0)])
def test_cfg_b_frames_orthonormal_right_handed(az):
    f = surface_frame((0, 0, 1), az)
    assert np.allclose(f.R @ f.R.T, np.eye(3))
    assert np.isclose(np.linalg.det(f.R), 1.0)
    assert np.allclose(f.x_hat, [0, 0, 1])
    v = np.array([[0.1, 0.2, 0.3], [1.0, -2.0, 0.5]])
    assert np.allclose(f.to_crystal(f.to_slab(v)), v)


def test_inconsistent_azimuth_rejected():
    # the inspected repository's README "(1,1,-1) facet" with a [110] beam: [1,1,-1].[1,1,0] = 2
    with pytest.raises(ValueError):
        surface_frame((1, 1, -1), (1, 1, 0))
