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


def test_sixty_degree_dislocation_slip_step_at_the_glide_trace():
    """60 degree dislocation (b = a/2[011]) below the slab, as a periodic array (images), seam on
    the (1-11) glide-plane trace: the image sum is converged, the reference stays at x = 0, the
    seam carries a slip step of b_n = a/2 (two layers), and the atoms follow the field."""
    py = A / np.sqrt(2)
    depth, core = 60.0, 100 * py
    trace = core - depth / np.sqrt(2)
    e = [{"burgers_over_a": [0.0, 0.5, 0.5], "line_uvw": [1, 1, 0], "depth_A": depth,
          "position_yz_A": [core, 0.0], "sign": 1}]
    Ly = 160 * py
    d = from_config(e, 0.22, A, SI001_FRAME, Ly=Ly, n_images=10)
    b = d.items[0].b_local
    np.testing.assert_allclose(b, [A / (2 * np.sqrt(2)), A / 2, A / (2 * np.sqrt(2))], atol=1e-9)
    s = build_sections(SI001_FRAME, A, [40, 40, 80], [0, 0, 0], 24.0, d, seam_y=trace)
    assert np.abs(s.info["seam_ramp_residual_surface_A"]).max() < 0.05  # images make the cell periodic
    d40 = from_config(e, 0.22, A, SI001_FRAME, Ly=Ly, n_images=40)
    r = np.stack([np.zeros(5), np.linspace(10, Ly - 10, 5), np.zeros(5)], -1)
    np.testing.assert_allclose(np.diff(d.displacement(r), axis=0), np.diff(d40.displacement(r), axis=0), atol=1e-2)
    p = s.positions
    top = lambda y: p[np.abs(p[:, 1] - y) < 2.0, 0].max()  # noqa: E731
    uf = lambda y: s.u_func(np.array([[0.0, y, 0.0]]))[0, 0]  # noqa: E731
    assert abs(top(20 * py)) < 0.05  # reference strip at x = 0
    y0 = s.info["seam_y_A"]
    assert abs(abs(uf(y0 + 0.2) - uf(y0 - 0.2)) - A / 2) < 0.05  # slip step of two layers
    for y in (y0 - 40, y0 + 25, core - 60, core, core + 60, core + 150):
        assert abs(top(y) - uf(y)) < 0.12
    assert nearest_neighbour_distances(s)[:, 0].min() > 2.0  # no core inside the slab
