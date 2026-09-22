"""Si(001) terrace builder: construction, counts, steps, terrace relations, frame (spec 4.2)."""
import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.geometry.frames import surface_frame
from reflection_holo.structure import Staircase, find_terrace_relations
from reflection_holo.structure.checks import POSITION_TOL_A, assert_on_lattice_sites
from reflection_holo.structure.lattice import is_diamond_site_quarter
from si001_test_inputs import brute_force_pairs, build

Q = A_SI_A / 4.0
D_NN = A_SI_A * np.sqrt(3.0) / 4.0
AZIMUTHS = [(1, 1, 0), (1, -1, 0), (1, 0, 0), (0, 1, 0)]


@pytest.mark.parametrize("az", AZIMUTHS)
@pytest.mark.parametrize("edges", ["parallel", "transverse"])
def test_builds_and_passes_all_assertions(az, edges):
    st = Staircase(edges=edges, terrace_layers=(0, 1, 3, 2), terrace_widths=(3, 2, 3, 2),
                   boundary_step_layers=-2)
    s = build(st, azimuth=az, edge_periods=2, substrate_layers=5)
    md = s.metadata
    assert md["atom_count"] == s.n_atoms == md["expected_atom_count"]
    for tag in ("(a)", "(b)", "(c)", "(d)", "(e)", "(f)", "(g)"):
        assert any(p.startswith(tag) for p in md["assertions_passed"]), tag
    assert [x["type"] for x in md["steps"]] == ["screw", "translation", "screw", "translation"]
    assert [x["delta_layers"] for x in md["steps"]] == [1, 2, -1, -2]
    assert md["steps"][-1]["at_periodic_boundary"] is True
    assert md["azimuth"]["uvw"] == list(az) and md["azimuth"]["label"].startswith("TEST_ONLY")


def test_expected_count_independent_formula():
    # [110]: one atom per layer per (a/sqrt2)^2 cell; [100]: two per a^2 cell
    for az, per_cell in (((1, 1, 0), 1), ((1, 0, 0), 2)):
        st = Staircase(edges="parallel", terrace_layers=(0, 1), terrace_widths=(3, 4),
                       boundary_step_layers=-1)
        s = build(st, azimuth=az, edge_periods=5, substrate_layers=6)
        # lower terrace (layer 0) has 6 layers, upper (layer 1) 7 layers
        assert s.n_atoms == per_cell * 5 * (3 * 6 + 4 * 7)


def test_one_continuous_lattice(mixed_110):
    s = mixed_110
    rc = s.frame.to_crystal(s.positions_A - s.crystal_origin_slab_A)
    n = rc * 4.0 / A_SI_A
    assert np.max(np.abs(n - np.rint(n))) * Q < POSITION_TOL_A
    assert np.all(is_diamond_site_quarter(np.rint(n).astype(int)))
    assert_on_lattice_sites(s.positions_A, s.frame, s.crystal_origin_slab_A, A_SI_A)
    # layer index is x / (a/4), bottom layer at x = 0
    assert np.allclose(s.positions_A[:, 0], s.layer_index * Q, atol=POSITION_TOL_A, rtol=0)
    assert s.positions_A[:, 0].min() == pytest.approx(0.0, abs=POSITION_TOL_A)


def test_min_distance_and_no_duplicates_bruteforce(mixed_110):
    s = mixed_110
    Ly, Lz = s.cell_A[1, 1], s.cell_A[2, 2]
    assert Ly > 2 * 1.05 * D_NN and Lz > 2 * 1.05 * D_NN      # minimum image valid
    r = brute_force_pairs(s.positions_A, Ly, Lz, 1.05 * D_NN)
    assert abs(r.min() - D_NN) < POSITION_TOL_A
    assert np.all(s.positions_A[:, 1] >= 0) and np.all(s.positions_A[:, 1] < Ly)
    assert np.all(s.positions_A[:, 2] >= 0) and np.all(s.positions_A[:, 2] < Lz)


def test_step_heights_measured_on_atoms(mixed_110):
    s = mixed_110
    tops = np.array([s.positions_A[s.terrace_index == k, 0].max() for k in range(3)])
    steps = np.diff(np.append(tops, tops[0]))
    assert np.allclose(steps, [2 * Q, -Q, -Q], atol=POSITION_TOL_A, rtol=0)
    for st in s.metadata["steps"]:
        assert abs(st["measured_height_A"] - st["delta_layers"] * Q) < POSITION_TOL_A


def _top_layers(s, k, nlay=4):
    top = s.metadata["terrace_map"][k]["top_layer_index"]
    sel = (s.terrace_index == k) & (s.layer_index >= top - (nlay - 1))
    rc = s.frame.to_crystal(s.positions_A[sel] - s.crystal_origin_slab_A)
    return rc, top - s.layer_index[sel]


def _backbond_axis_bruteforce(s, k):
    """Top-layer back-bond axis of terrace k from an independent O(N^2) bond search."""
    top = s.metadata["terrace_map"][k]["top_layer_index"]
    Ly, Lz = s.cell_A[1, 1], s.cell_A[2, 2]
    pos = s.positions_A
    i_top = np.nonzero((s.terrace_index == k) & (s.layer_index == top))[0]
    i_bel = np.nonzero(s.layer_index == top - 1)[0]
    axes = set()
    for i in i_top:
        d = pos[i_bel] - pos[i]
        d[:, 1] -= Ly * np.rint(d[:, 1] / Ly)
        d[:, 2] -= Lz * np.rint(d[:, 2] / Lz)
        bonded = np.abs(np.linalg.norm(d, axis=1) - D_NN) < POSITION_TOL_A
        for v in s.frame.to_crystal(d[bonded]):
            axes.add((1, 1, 0) if v[0] * v[1] > 0 else (1, -1, 0))
    assert len(axes) == 1
    return axes.pop()


def test_a2_step_is_pure_lattice_translation(mixed_110):
    s = mixed_110
    st = s.metadata["steps"][0]
    assert st["delta_layers"] == 2 and st["type"] == "translation"
    rel = find_terrace_relations(*_top_layers(s, 0), *_top_layers(s, 1), A_SI_A)
    pure = [r for r in rel if r["operation"] == "identity"]
    assert pure and not [r for r in rel if r["operation"] in ("Rz(+90)", "Rz(-90)")]
    for r in pure:
        t = r["t_crystal_A"]
        assert t[2] == pytest.approx(A_SI_A / 2, abs=POSITION_TOL_A)
        m = 2 * t / A_SI_A
        assert np.allclose(m, np.rint(m), atol=1e-9) and int(np.rint(m).sum()) % 2 == 0
    assert _backbond_axis_bruteforce(s, 0) == _backbond_axis_bruteforce(s, 1)


def test_a4_step_is_screw_with_rotated_top_bonds(mixed_110):
    s = mixed_110
    st = s.metadata["steps"][1]
    assert st["delta_layers"] == -1 and st["type"] == "screw"
    rel = find_terrace_relations(*_top_layers(s, 1), *_top_layers(s, 2), A_SI_A)
    ops = {r["operation"] for r in rel}
    assert "identity" not in ops and "Rz(180)" not in ops
    assert {"Rz(+90)", "Rz(-90)"} <= ops
    for r in rel:
        assert r["t_crystal_A"][2] == pytest.approx(-Q, abs=POSITION_TOL_A)
    a1, a2 = _backbond_axis_bruteforce(s, 1), _backbond_axis_bruteforce(s, 2)
    assert np.dot(a1, a2) == 0                        # rotated by 90 degrees
    # at the [110] azimuth the two terrace types have bonds along and across the beam
    ang = sorted(t["backbond_angle_to_beam_deg"] for t in s.metadata["terrace_map"][1:])
    assert ang == pytest.approx([0.0, 90.0], abs=1e-9)


def test_relation_finder_agrees_with_calculator_screw_search(calculator):
    st = Staircase(edges="parallel", terrace_layers=(0, 1), terrace_widths=(3, 3),
                   boundary_step_layers=-1)
    s = build(st, azimuth=(1, 0, 0), edge_periods=2, substrate_layers=5)
    rel = find_terrace_relations(*_top_layers(s, 0), *_top_layers(s, 1), A_SI_A)
    Ninv = np.linalg.inv(0.5 * A_SI_A * np.array([[1.0, 1.0], [1.0, -1.0]]))

    def cls(t_xy):                                    # translation class modulo the (001) net
        f = np.asarray(t_xy) @ Ninv.T
        return tuple(np.round(np.round(f, 6) % 1.0, 6))

    mine = {(r["operation"], cls(r["t_crystal_A"][:2]))
            for r in rel if r["operation"] in ("Rz(+90)", "Rz(-90)")}
    calc = {(nm, cls(np.asarray(t[:2]) * A_SI_A)) for nm, t in calculator.screw_search()}
    # the crystal origin sits on a site of both, so the screw sets coincide modulo the net
    assert mine == calc
    assert all(t[2] == 0.25 for _, t in calculator.screw_search())


@pytest.mark.parametrize("backbond,angle", [((1, 1, 0), 0.0), ((1, -1, 0), 90.0)])
def test_first_terrace_type_is_explicit(backbond, angle):
    st = Staircase(edges="parallel", terrace_layers=(0,), terrace_widths=(3,),
                   boundary_step_layers=0)
    s = build(st, azimuth=(1, 1, 0), backbond=backbond)
    tm = s.metadata["terrace_map"][0]
    assert tuple(tm["top_layer_backbond_axis_crystal"]) == backbond
    assert tm["backbond_angle_to_beam_deg"] == pytest.approx(angle, abs=1e-9)
    assert _backbond_axis_bruteforce(s, 0) == backbond


def test_incidence_plane_mirror_found_at_100_not_110():
    """DERIVED_HERE symmetry fact: at a <100> azimuth the a/4 terraces are also related by a glide
    whose mirror plane contains the beam and the normal; at a <110> azimuth they are not."""
    st = Staircase(edges="transverse", terrace_layers=(0, 1), terrace_widths=(3, 3),
                   boundary_step_layers=-1)
    s100 = build(st, azimuth=(1, 0, 0))
    s110 = build(st, azimuth=(1, 1, 0))
    for x in s100.metadata["steps"]:
        assert x["relation"]["incidence_plane_mirror_operations"] == ["mirror(010)"]
    for x in s110.metadata["steps"]:
        assert x["relation"]["incidence_plane_mirror_operations"] == []


@pytest.mark.parametrize("az", AZIMUTHS)
def test_frame_right_handed_and_azimuth_in_surface(az):
    st = Staircase(edges="transverse", terrace_layers=(0,), terrace_widths=(2,),
                   boundary_step_layers=0)
    s = build(st, azimuth=az)
    f = s.frame
    ref = surface_frame((0, 0, 1), az)
    assert np.allclose(f.R, ref.R, atol=0)
    assert np.linalg.det(f.R) == pytest.approx(1.0, abs=1e-12)
    assert np.allclose(np.cross(f.x_hat, f.y_hat), f.z_hat, atol=1e-12)
    assert np.allclose(f.x_hat, [0, 0, 1]) and abs(f.z_hat @ f.x_hat) < 1e-15
    md = s.metadata["frame"]
    assert np.allclose(md["z_hat_crystal"], np.asarray(az) / np.linalg.norm(az))
    # cell vectors are along the slab axes; y and z periodic, x not
    assert np.allclose(s.cell_A, np.diag(np.diag(s.cell_A)))
    assert s.pbc == (False, True, True)
