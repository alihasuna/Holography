"""Three-section Si(001) sample builder: terraces, inserted half-plane, seam handling."""

import numpy as np
import pytest

from reflection_holo.geometry import SI001_FRAME
from reflection_holo.defects.dislocation import from_config
from reflection_holo.structure.sections import build_sections, nearest_neighbour_distances

A = 5.4309
LOMER = [{"burgers_over_a": [-0.5, 0.5, 0.0], "line_uvw": [1, 1, 0], "depth_A": 25.0,
          "position_yz_A": [384.0, 0.0], "sign": 1}]


@pytest.fixture(scope="module")
def samples():
    d = from_config(LOMER, 0.22, A, SI001_FRAME)
    ref = build_sections(SI001_FRAME, A, [40, 40, 40], [0, 4, 0], 56.0)
    dis = build_sections(SI001_FRAME, A, [40, 40, 40], [0, 4, 0], 56.0, d, seam_y=76.8)
    return ref, dis


def test_terrace_heights_and_perfect_coordination(samples):
    ref, _ = samples
    tops = [ref.positions[ref.section == k, 0].max() for k in range(3)]
    np.testing.assert_allclose(tops, [0.0, A, 0.0], atol=1e-6)
    assert nearest_neighbour_distances(ref)[:, 0].min() == pytest.approx(2.3517, abs=1e-3)


def test_edge_dislocation_inserts_one_half_plane(samples):
    ref, dis = samples
    extra = len(dis.positions) - len(ref.positions)
    n_layers_above_core = int(np.floor(25.0 / (A / 4))) + 1  # layers 0 .. -24.4 A
    assert extra in (n_layers_above_core, n_layers_above_core + 1)  # +1: layer at the core


def test_surface_bulges_over_the_core_and_reference_is_flat(samples):
    _, dis = samples
    p = dis.positions
    surf = lambda y: p[(np.abs(p[:, 1] - y) < 2) & (p[:, 0] > -0.9), 0].max()  # noqa: E731
    bump = surf(384.0) - surf(76.8)
    assert bump == pytest.approx(3.8402 / np.pi, rel=0.12)  # b/pi, reduced by the finite cell
    assert abs(surf(76.8)) < 0.05  # reference strip at its nominal height


def test_step_edges_not_disturbed_by_the_seam(samples):
    _, dis = samples
    tops = [dis.positions[dis.section == k, 0].max() for k in range(3)]
    assert tops[0] < 0.2 and abs(tops[1] - A) < 0.2 and tops[2] < 1.3


def test_no_overlapping_atoms_outside_the_core(samples):
    _, dis = samples
    nn = nearest_neighbour_distances(dis)[:, 0]
    assert (nn < 2.0).sum() <= 4 and nn.min() > 1.7
