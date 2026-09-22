"""Each spec 4.2 assertion catches the defect it exists for (corrupted inputs must fail)."""
import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.geometry.frames import SurfaceFrame, surface_frame
from reflection_holo.structure import Staircase, StaircaseError, validate_staircase
from reflection_holo.structure import checks
from reflection_holo.structure.checks import StructureAssertionError
from reflection_holo.structure.si001 import (assert_step_heights, classify_relation,
                                             find_terrace_relations)
from si001_test_inputs import build

Q = A_SI_A / 4.0


def _periodic(s):
    return [None, s.cell_A[1, 1], s.cell_A[2, 2]]


# --- (a) ------------------------------------------------------------------------------------------
def test_a_off_lattice_atom_is_caught(mixed_110):
    s = mixed_110
    pos = s.positions_A.copy()
    pos[7, 2] += 0.01
    with pytest.raises(StructureAssertionError, match=r"\(a\).*off the a/4 grid"):
        checks.assert_on_lattice_sites(pos, s.frame, s.crystal_origin_slab_A, A_SI_A)


def test_a_non_site_grid_point_is_caught(mixed_110):
    s = mixed_110
    pos = s.positions_A.copy()
    pos[3] += s.frame.to_slab(np.array([Q, Q, 0.0]))       # a/4 grid point, wrong parity
    with pytest.raises(StructureAssertionError, match=r"\(a\).*not diamond sites"):
        checks.assert_on_lattice_sites(pos, s.frame, s.crystal_origin_slab_A, A_SI_A)


def test_a_terrace_from_a_second_lattice_is_caught(mixed_110):
    # a terrace cut from a copy of the crystal shifted by a non-lattice vector
    s = mixed_110
    pos = s.positions_A.copy()
    sel = s.terrace_index == 1
    pos[sel] += s.frame.to_slab(np.array([A_SI_A / 2, 0.0, 0.0]))
    with pytest.raises(StructureAssertionError, match=r"\(a\)"):
        checks.assert_on_lattice_sites(pos, s.frame, s.crystal_origin_slab_A, A_SI_A)


# --- (b) ------------------------------------------------------------------------------------------
def test_b_closed_window_duplicate_plane_A_M7(mixed_110):
    """Defect A-M7: a closed window [0, L] keeps the y = 0 plane twice (again at y = L)."""
    s = mixed_110
    Ly = s.cell_A[1, 1]
    at0 = np.abs(s.positions_A[:, 1]) < checks.WINDOW_TOL_A
    assert at0.sum() > 0
    dup = s.positions_A[at0].copy()
    dup[:, 1] += Ly * (1 - 1e-15)          # floating point lands marginally inside at L
    pos = np.vstack([s.positions_A, dup])
    with pytest.raises(StructureAssertionError, match=r"\(b\) \d+ atom\(s\) outside the half-open"):
        checks.assert_half_open_window(pos[:, 1], Ly, "y")
    with pytest.raises(StructureAssertionError, match=r"\(b\) duplicate atoms"):
        checks.assert_no_duplicates_and_count(pos, _periodic(s), s.n_atoms)


def test_b_count_mismatch_is_caught(mixed_110):
    s = mixed_110
    with pytest.raises(StructureAssertionError, match=r"\(b\) atom count"):
        checks.assert_no_duplicates_and_count(s.positions_A[:-1], _periodic(s), s.n_atoms)
    checks.assert_no_duplicates_and_count(s.positions_A, _periodic(s), s.n_atoms)


def test_b_window_tolerance_is_half_open():
    L = 10.0
    checks.assert_half_open_window(np.array([-0.5e-6, 0.0, 5.0, L - 2e-6]), L, "y")
    for bad in (L - 0.5e-6, L, -2e-6):
        with pytest.raises(StructureAssertionError):
            checks.assert_half_open_window(np.array([bad]), L, "y")


# --- (c) ------------------------------------------------------------------------------------------
def test_c_too_close_atom_is_caught(mixed_110):
    s = mixed_110
    pos = np.vstack([s.positions_A, s.positions_A[10] + np.array([0.0, 0.0, 1.0])])
    with pytest.raises(StructureAssertionError, match=r"\(c\) minimum interatomic distance"):
        checks.assert_min_distance_and_coordination(pos, _periodic(s), A_SI_A, None)


def test_c_wrong_period_breaks_coordination(mixed_110):
    """A cell length that is not a lattice period leaves under-coordinated atoms at the edge."""
    s = mixed_110
    interior = (s.layer_index >= 1) & (s.layer_index <= 3)
    checks.assert_min_distance_and_coordination(s.positions_A, _periodic(s), A_SI_A, interior)
    per = _periodic(s)
    per[2] = per[2] + 0.5
    with pytest.raises(StructureAssertionError, match=r"\(c\).*4-coordinated"):
        checks.assert_min_distance_and_coordination(s.positions_A, per, A_SI_A, interior)


def test_c_missing_interior_atom_is_caught(mixed_110):
    s = mixed_110
    interior = (s.layer_index >= 1) & (s.layer_index <= 3)
    k = int(np.nonzero(s.layer_index == 2)[0][0])
    keep = np.ones(s.n_atoms, bool)
    keep[k] = False
    with pytest.raises(StructureAssertionError, match=r"\(c\).*4-coordinated"):
        checks.assert_min_distance_and_coordination(s.positions_A[keep], _periodic(s), A_SI_A,
                                                     interior[keep])


# --- (d) ------------------------------------------------------------------------------------------
@pytest.mark.parametrize("layers,boundary", [((0, 3), -3), ((0, 4, 2), -2), ((0, 1, 4, 2), -2)])
def test_d_steps_other_than_a4_a2_are_refused(layers, boundary):
    st = Staircase(edges="transverse", terrace_layers=layers,
                   terrace_widths=(2,) * len(layers), boundary_step_layers=boundary)
    with pytest.raises(StaircaseError, match=r"only a/4 .* and a/2"):
        validate_staircase(st, A_SI_A)


def test_d_zero_height_step_is_refused():
    st = Staircase(edges="parallel", terrace_layers=(0, 0, 1), terrace_widths=(2, 2, 2),
                   boundary_step_layers=-1)
    with pytest.raises(StaircaseError, match="same height"):
        validate_staircase(st, A_SI_A)


def test_d_measured_height_mismatch_is_caught():
    st = Staircase(edges="parallel", terrace_layers=(0, 2), terrace_widths=(2, 2),
                   boundary_step_layers=-2)
    steps = validate_staircase(st, A_SI_A)
    assert_step_heights([10 * Q, 12 * Q], st, steps, A_SI_A)
    with pytest.raises(StructureAssertionError, match=r"\(d\)"):
        assert_step_heights([10 * Q, 11 * Q], st, steps, A_SI_A)        # built a/4 where a/2 requested
    with pytest.raises(StructureAssertionError, match=r"\(d\)"):
        assert_step_heights([10 * Q, 12 * Q + 1e-3], st, steps, A_SI_A)


# --- (e) ------------------------------------------------------------------------------------------
def test_e_inspected_repository_staircase_0123_is_refused():
    """The inspected repository's 0,1,2,3 staircase hides a 3-layer down-step at the cell edge."""
    # declared as the monotone staircase it was meant to be: net height change +4 layers
    st = Staircase(edges="transverse", terrace_layers=(0, 1, 2, 3), terrace_widths=(4, 4, 4, 4),
                   boundary_step_layers=+1)
    with pytest.raises(StaircaseError) as e:
        validate_staircase(st, A_SI_A)
    msg = str(e.value)
    assert "net height change of +4 layers" in msg
    assert "hidden 3-layer down-step" in msg and "vicinal cell" in msg
    # declared honestly: the closing step is -3 layers, neither a/4 nor a/2
    st = Staircase(edges="transverse", terrace_layers=(0, 1, 2, 3), terrace_widths=(4, 4, 4, 4),
                   boundary_step_layers=-3)
    with pytest.raises(StaircaseError, match="hidden 3-layer down-step"):
        validate_staircase(st, A_SI_A)
    # not declared at all (0): still a net height change
    st = Staircase(edges="transverse", terrace_layers=(0, 1, 2, 3), terrace_widths=(4, 4, 4, 4),
                   boundary_step_layers=0)
    with pytest.raises(StaircaseError, match="net height change of \\+3 layers"):
        validate_staircase(st, A_SI_A)
    # and the builder refuses it before building anything
    with pytest.raises(StaircaseError):
        build(st)


def test_e_continuous_staircases_are_accepted():
    for layers, b in (((0, 1, 2, 1), -1), ((0, 2, 1), -1), ((0, 1, 0), 0), ((0,), 0)):
        st = Staircase(edges="transverse", terrace_layers=layers,
                       terrace_widths=(2,) * len(layers), boundary_step_layers=b)
        steps = validate_staircase(st, A_SI_A)
        assert sum(x["delta_layers"] for x in steps) == 0


def test_e_measured_closing_step_mismatch_is_caught():
    st = Staircase(edges="parallel", terrace_layers=(0, 1), terrace_widths=(2, 2),
                   boundary_step_layers=-1)
    steps = validate_staircase(st, A_SI_A)
    with pytest.raises(StructureAssertionError, match=r"\(d\)|\(e\)"):
        assert_step_heights([10 * Q, 11 * Q + 1e-3], st, steps, A_SI_A)


# --- (f) ------------------------------------------------------------------------------------------
def _layers(s, k):
    top = s.metadata["terrace_map"][k]["top_layer_index"]
    sel = (s.terrace_index == k) & (s.layer_index >= top - 3)
    return s.frame.to_crystal(s.positions_A[sel] - s.crystal_origin_slab_A), top - s.layer_index[sel]


def test_f_classification_rejects_mislabelled_steps(mixed_110):
    s = mixed_110
    tm = s.metadata["terrace_map"]
    ax = [tuple(t["top_layer_backbond_axis_crystal"]) for t in tm]
    rel_a2 = find_terrace_relations(*_layers(s, 0), *_layers(s, 1), A_SI_A)   # a/2 step
    rel_a4 = find_terrace_relations(*_layers(s, 1), *_layers(s, 2), A_SI_A)   # a/4 step
    assert classify_relation(rel_a2, 2, ax[0], ax[1], A_SI_A) == "translation"
    assert classify_relation(rel_a4, -1, ax[1], ax[2], A_SI_A) == "screw"
    with pytest.raises(StructureAssertionError, match=r"\(f\) a/4 step"):
        classify_relation(rel_a2, 1, ax[0], ax[1], A_SI_A)
    with pytest.raises(StructureAssertionError, match=r"\(f\) a/2 step"):
        classify_relation(rel_a4, 2, ax[1], ax[2], A_SI_A)


def test_f_non_lattice_shift_of_a_terrace_is_caught(mixed_110):
    s = mixed_110
    rcB, dB = _layers(s, 1)
    rcB = rcB + np.array([A_SI_A / 8, 0.0, 0.0])     # not a lattice or screw relation
    rel = find_terrace_relations(*_layers(s, 0), rcB, dB, A_SI_A)
    # the a/8 search grid still finds the shifted copy, but not as a lattice symmetry
    assert rel and not [r for r in rel if r["lattice_symmetry"]]
    ax = [tuple(t["top_layer_backbond_axis_crystal"]) for t in s.metadata["terrace_map"]]
    with pytest.raises(StructureAssertionError, match=r"\(f\) a/2 step: no pure lattice"):
        classify_relation(rel, 2, ax[0], ax[1], A_SI_A)
    # same for a screw-related pair shifted off the lattice
    rcC, dC = _layers(s, 2)
    rel = find_terrace_relations(*_layers(s, 1), rcC + np.array([A_SI_A / 8, 0.0, 0.0]), dC,
                                 A_SI_A)
    with pytest.raises(StructureAssertionError, match=r"\(f\) a/4 step: no 90-degree lattice"):
        classify_relation(rel, -1, ax[1], ax[2], A_SI_A)


def test_f_imperfect_layer_is_caught(mixed_110):
    s = mixed_110
    rcB, dB = _layers(s, 1)
    rcB = rcB.copy()
    rcB[0, 0] += Q                                 # one atom moved within its layer
    with pytest.raises(StructureAssertionError, match=r"\(f\).*not one net coset"):
        find_terrace_relations(*_layers(s, 0), rcB, dB, A_SI_A)


# --- (g) ------------------------------------------------------------------------------------------
def test_g_left_handed_frame_is_caught():
    f = surface_frame((0, 0, 1), (1, 1, 0))
    checks.assert_frame(f)
    bad = SurfaceFrame(f.normal_hkl, f.azimuth_uvw, np.vstack([f.x_hat, -f.y_hat, f.z_hat]))
    with pytest.raises(StructureAssertionError, match=r"\(g\).*right-handed"):
        checks.assert_frame(bad)


def test_g_azimuth_out_of_surface_or_not_item8_is_refused():
    st = Staircase(edges="parallel", terrace_layers=(0,), terrace_widths=(2,),
                   boundary_step_layers=0)
    with pytest.raises(ValueError, match="not in the surface plane"):
        build(st, azimuth=(1, 1, 1))
    with pytest.raises(ValueError, match="PROJECT_INPUT item 8"):
        build(st, azimuth=(1, 2, 0))


# --- the builder runs the assertions itself --------------------------------------------------------
def test_builder_refuses_duplicated_sites(monkeypatch):
    import reflection_holo.structure.si001 as si001
    orig = si001.diamond_sites_quarter
    monkeypatch.setattr(si001, "diamond_sites_quarter",
                        lambda lo, hi, a: np.concatenate([orig(lo, hi, a)] * 2))
    st = Staircase(edges="transverse", terrace_layers=(0, 1), terrace_widths=(3, 3),
                   boundary_step_layers=-1)
    with pytest.raises(StructureAssertionError, match=r"\(b\)"):
        build(st)


def test_builder_refuses_non_site_points(monkeypatch):
    import reflection_holo.structure.si001 as si001
    orig = si001.diamond_sites_quarter

    def corrupted(lo, hi, a):
        n = orig(lo, hi, a).copy()
        n[::97] += np.array([1, 1, 0])          # a/4 grid points that are not diamond sites
        return n
    monkeypatch.setattr(si001, "diamond_sites_quarter", corrupted)
    st = Staircase(edges="transverse", terrace_layers=(0, 1), terrace_widths=(3, 3),
                   boundary_step_layers=-1)
    with pytest.raises(StructureAssertionError, match=r"\(a\)"):
        build(st)
