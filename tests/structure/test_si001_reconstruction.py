"""Si(001) dimer reconstructions (report E2): transcription of Ramstad, Brocks and Kelly 1995 (R1)
Tables III-IV, dimer bond lengths and buckling recomputed from the BUILT atoms against R1's printed
values and E6's recomputation, dimer-row rotation across a/4 steps and not across a/2 steps
(Zandvliet 2000), no collisions at step edges, composition and layer spacings unchanged, the
flip-flop ensemble (ASSUMPTION B37), refusals. Measurements here are independent of the builder's
own records: dimers are found by a brute-force minimum-image search on the positions."""
import re

import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.structure import Staircase, StructureAssertionError, build_si001_terraces
from reflection_holo.structure import checks
from reflection_holo.structure import reconstruction as R
from reflection_holo.structure.features import (FEATURE_RECONSTRUCTION_REFUSAL,
                                                feature_termination_option)
from reflection_holo.structure.si001 import OverlayerSpec, backbond_axis_of_crystal_layer
from si001_test_inputs import OVERLAYER_LABEL, REPO_ROOT, brute_force_pairs, build

Q = A_SI_A / 4.0
D_NN = A_SI_A * np.sqrt(3.0) / 4.0
STATIC = ("p(2x1)s", "p(2x1)a", "p(2x2)", "c(4x2)")
MIXED = Staircase(edges="transverse", terrace_layers=(0, 2, 1), terrace_widths=(4, 4, 4),
                  boundary_step_layers=-1)          # a/2 up, a/4 down, a/4 down at the cell edge
FLAT = Staircase(edges="transverse", terrace_layers=(0,), terrace_widths=(4,),
                 boundary_step_layers=0)


def rbuild(term, st=MIXED, azimuth=(1, 1, 0), edge_periods=4, substrate_layers=12,
           backbond=(1, 1, 0)):
    return build(st, azimuth=azimuth, edge_periods=edge_periods,
                 substrate_layers=substrate_layers, backbond=backbond, termination=term)


def top_mask(s):
    tops = np.array([t["top_layer_index"] for t in s.metadata["terrace_map"]])
    return s.layer_index == tops[s.terrace_index]


def dimers_from_atoms(s, cutoff=3.0):
    """Brute-force dimers: top-layer atom pairs of one terrace closer than cutoff (minimum image in
    y and z). Returns [(terrace, bond_A, buckling_deg, crystal in-plane axis)]."""
    pos = s.positions_A
    idx = np.nonzero(top_mask(s))[0]
    r = brute_force_pairs(pos[idx], s.cell_A[1, 1], s.cell_A[2, 2], cutoff)
    out = []
    groups = {k: k for k in range(len(s.metadata["terrace_map"]))}
    tl = s.metadata["staircase"]["terrace_layers"]
    if len(tl) > 1 and tl[0] == tl[-1]:
        groups[len(tl) - 1] = 0
    for a, b in zip(*np.nonzero(r < cutoff)):
        if a >= b or groups[s.terrace_index[idx[a]]] != groups[s.terrace_index[idx[b]]]:
            continue
        d = pos[idx[b]] - pos[idx[a]]
        d[1] -= s.cell_A[1, 1] * np.rint(d[1] / s.cell_A[1, 1])
        d[2] -= s.cell_A[2, 2] * np.rint(d[2] / s.cell_A[2, 2])
        dc = s.frame.to_crystal(d)
        axis = "[1,1,0]" if dc[0] * dc[1] > 0 else "[1,-1,0]"
        out.append((int(s.terrace_index[idx[a]]), float(np.linalg.norm(d)),
                    float(np.degrees(np.arctan2(abs(d[0]), np.hypot(d[1], d[2])))), axis))
    return out


# ---- transcription -----------------------------------------------------------------------------
def _l7_tables():
    path = REPO_ROOT / "docs" / "agent_reports" / "L7_surface_realism.md"
    if not path.is_file():
        pytest.skip("docs/agent_reports/L7_surface_realism.md absent")
    text = path.read_text().replace("−", "-")
    sec = text[text.index("### 1.4 Transcription"):text.index("## 2. Ion-milled")]
    rows = [ln for ln in sec.splitlines() if re.match(r"\| [1-5] \| \(", ln)]
    t3, t4 = {}, {}
    for ln in rows:
        cells = [c.strip() for c in ln.strip("|").split("|")]
        key = tuple(int(v) for v in cells[1].strip("()").split(","))
        vals = tuple(float(v) for v in cells[2:])
        (t3 if len(vals) == 4 else t4)[key] = vals
    return t3, t4


def test_tables_equal_the_L7_transcription_entry_by_entry():
    t3, t4 = _l7_tables()
    assert len(t3) == 10 and len(t4) == 20                   # 40 + 120 entries
    assert t3 == R._TABLE_III
    assert t4 == R._TABLE_IV
    n = sum(len(v) for v in t3.values()) + sum(len(v) for v in t4.values())
    assert n == 160


def test_table_indices_are_diamond_sites_in_the_frame():
    """Every R1 (k, l, m) maps to a diamond site from a top-layer origin (both layer parities)."""
    from reflection_holo.structure.lattice import is_diamond_site_quarter
    for n3, O in ((3, np.array([3, 1, 3])), (2, np.array([2, 0, 2]))):
        assert is_diamond_site_quarter(O)
        d, b = R.dimer_frame(n3)
        assert np.all(np.cross(d, b) == [0, 0, 2])            # right-handed, z = [001]
        assert abs(int(np.dot(d, backbond_axis_of_crystal_layer(n3)))) == 0
        for (k, l, m) in list(R._TABLE_III) + list(R._TABLE_IV):
            assert is_diamond_site_quarter(O + k * d + l * b + np.array([0, 0, m]))


# ---- dimer bond length and buckling from the built atoms ---------------------------------------
@pytest.mark.parametrize("term", STATIC)
def test_dimer_bond_and_buckling_recomputed_from_atoms_match_R1_printed(term):
    s = rbuild(term, st=FLAT, edge_periods=4)
    dims = dimers_from_atoms(s)
    assert len(dims) == s.reconstruction.n_cells > 0
    kinds = sorted({(round(b, 9), round(th, 9)) for _, b, th, _ in dims}, key=lambda v: v[1])
    pr = R.PRINTED_R1[term]
    bound = R.rounding_bound(term, A_SI_A)
    refs = sorted(zip(pr["dimer_bond_A"], pr["buckling_deg"], bound), key=lambda v: v[1] or 0)
    assert len(kinds) == len(refs)
    for (b, th), (pb, pth, bd) in zip(kinds, refs):
        # printed to 0.01 A and 0.1 deg: half a unit, plus the effect of R1's 0.001 A rounding of
        # the four tabulated displacements and of a = 5.4309 vs 5.431 A (reconstruction.
        # rounding_bound, first order)
        assert abs(b - pb) <= 0.005 + bd["bond_A"] + 1e-12, (term, b, pb)
        if pth is None:
            assert th == pytest.approx(0.0, abs=1e-9)          # p(2x1)s is symmetric
        else:
            assert abs(th - pth) <= 0.05 + bd["buckling_deg"] + 1e-12, (term, th, pth)


E6_RECOMPUTED = {       # E6 section 2 (tools/review/e6_recompute_output.txt), a = 5.431 A
    "p(2x1)s": [(2.230, 0.0)], "p(2x1)a": [(2.258, 18.27)],
    "p(2x2)": [(2.283, 18.86), (2.283, 19.26)], "c(4x2)": [(2.287, 18.72), (2.288, 18.95)]}


@pytest.mark.parametrize("term", STATIC)
def test_dimer_geometry_matches_E6_recomputation(term):
    s = rbuild(term, st=FLAT, edge_periods=4)
    kinds = sorted({(round(b, 9), round(th, 9)) for _, b, th, _ in dimers_from_atoms(s)},
                   key=lambda v: v[1])
    da = abs(A_SI_A - R.A_R1_A) * np.sqrt(2) / 2           # ideal dimer separation 5.4309 vs 5.431
    for (b, th), (eb, eth) in zip(kinds, E6_RECOMPUTED[term]):
        assert abs(b - eb) <= 0.0005 + da + 1e-12            # E6 prints 3 decimals
        assert abs(th - eth) <= 0.005 + np.degrees(da / b) + 1e-12   # E6 prints 2 decimals
    if term == "c(4x2)":                                     # the values quoted in the task
        assert round(kinds[0][0], 3) == 2.287 and round(kinds[0][1], 2) == 18.72


def test_c4x2_rows_in_antiphase_and_p2x2_rows_in_phase():
    """Adjacent dimer rows: c(4x2) buckles in antiphase, p(2x2) in phase (R1 cells, L7 1.4)."""
    for term, want_same in (("c(4x2)", False), ("p(2x2)", True)):
        s = rbuild(term, st=FLAT, edge_periods=4)
        rec = s.reconstruction
        up = top_mask(s) & (rec.cell_index >= 0)
        d = rec.displacement_A
        # down atom of each dimer: the one with the lower x; group dimers by row (coordinate along
        # the dimer bond axis) and compare the down-atom side of neighbouring rows at equal row coord
        tm = rec.metadata["terraces"][0]
        dh = np.array(tm["dimer_bond_axis_slab"])
        bh = np.array(tm["dimer_row_axis_slab"])
        p = rec.ideal_positions_A
        cells = {}
        for i in np.nonzero(up)[0]:
            cells.setdefault(int(rec.cell_index[i]), []).append(i)
        sides = {}
        for c, (i, j) in ((c, v) for c, v in cells.items() if len(v) == 2):
            lo, hi = (i, j) if p[i] @ dh < p[j] @ dh else (j, i)
            down_first = d[lo, 0] < d[hi, 0]
            sides[(round(float(p[lo] @ dh), 3), round(float(p[lo] @ bh), 3))] = down_first
        rows = sorted({k[0] for k in sides})
        assert len(rows) >= 2
        a = {k[1]: v for k, v in sides.items() if k[0] == rows[0]}
        b = {k[1]: v for k, v in sides.items() if k[0] == rows[1]}
        common = sorted(set(a) & set(b))
        assert common
        assert all((a[y] == b[y]) == want_same for y in common)
        along = [a[y] for y in sorted(a)]
        assert all(u != v for u, v in zip(along, along[1:]))     # alternate along the row


# ---- steps: rotation, edges, collisions --------------------------------------------------------
@pytest.mark.parametrize("term", STATIC + ("p(2x1)a flip-flop ensemble",))
@pytest.mark.parametrize("azimuth", [(1, 1, 0), (1, 0, 0)])
def test_dimer_rows_rotate_across_a4_and_not_across_a2(term, azimuth):
    s = rbuild(term, azimuth=azimuth)
    axes = {}
    for t, _, _, ax in dimers_from_atoms(s):
        axes.setdefault(t, set()).add(ax)
    assert all(len(v) == 1 for v in axes.values()) and set(axes) == {0, 1, 2}
    ax = {t: next(iter(v)) for t, v in axes.items()}
    for st in s.metadata["steps"]:
        a, b = ax[st["from_terrace"]], ax[st["to_terrace"]]
        if abs(st["delta_layers"]) == 1:
            assert a != b and st["reconstruction"]["dimer_rows_rotated_90_deg"] is True
            assert st["reconstruction"]["step_type_zandvliet"][0] == "S"
        else:
            assert a == b and st["reconstruction"]["dimer_rows_rotated_90_deg"] is False
            assert st["reconstruction"]["step_type_zandvliet"][0] == "D"
    # the dimer bond is normal to each terrace's top-layer back-bond axis (dimer rows along it)
    for t in s.metadata["terrace_map"]:
        bb = t["top_layer_backbond_axis_crystal"]
        want = "[1,-1,0]" if list(bb) == [1, 1, 0] else "[1,1,0]"
        assert ax[t["index"]] == want


def test_sa_sb_labels_at_110_and_none_at_100():
    s = rbuild("p(2x1)s", azimuth=(1, 1, 0))
    types = {st["reconstruction"]["step_type_zandvliet"] for st in s.metadata["steps"]}
    assert types <= {"SA", "SB", "DA", "DB"} and len(types & {"SA", "SB"}) >= 1
    s = rbuild("p(2x1)s", azimuth=(1, 0, 0))
    assert all("neither" in st["reconstruction"]["step_type_zandvliet"]
               for st in s.metadata["steps"])


@pytest.mark.parametrize("term", STATIC + ("p(2x1)a flip-flop ensemble",))
@pytest.mark.parametrize("azimuth,edges", [((1, 1, 0), "transverse"), ((1, 0, 0), "transverse"),
                                           ((1, 1, 0), "parallel"), ((1, 0, 0), "parallel")])
def test_no_atom_collisions_at_step_edges(term, azimuth, edges):
    st = Staircase(edges=edges, terrace_layers=(0, 2, 1), terrace_widths=(4, 4, 4),
                   boundary_step_layers=-1)
    s = rbuild(term, st=st, azimuth=azimuth)
    per = [None, s.cell_A[1, 1], s.cell_A[2, 2]]
    # the repository's existing duplicate check (assertion (b) criterion, 0.5 A) on the atoms
    checks.assert_no_duplicates_and_count(s.positions_A, per, s.n_atoms)
    # independent brute-force minimum distance, whole structure and at the step edges
    r = brute_force_pairs(s.positions_A, per[1], per[2], 10.0)
    dmin = float(r.min())
    assert dmin >= R.COLLISION_FRACTION_OF_DNN * D_NN
    shortest = min(x["bond_A"] for x in R.reference_dimers(term, A_SI_A))
    edge = np.zeros(s.n_atoms, bool)                        # atoms within 6 A of a riser plane
    s_ax = 2 if edges == "transverse" else 1
    for t in s.metadata["terrace_map"]:
        for b in t["s_range_A"]:
            dd = np.abs(s.positions_A[:, s_ax] - b)
            edge |= np.minimum(dd, s.cell_A[s_ax, s_ax] - dd) < 6.0
    r_edge = r[np.ix_(edge, edge)]
    assert r_edge.min() >= R.COLLISION_FRACTION_OF_DNN * D_NN
    col = s.metadata["options"]["dimer_reconstruction"]["checks"]["collision"]
    assert col["interior_min_A"] == pytest.approx(shortest, abs=1e-9)   # the source's geometry
    assert col["riser_edge_min_A"] >= R.COLLISION_FRACTION_OF_DNN * D_NN
    assert dmin == pytest.approx(min(col["interior_min_A"], col["riser_edge_min_A"]), abs=1e-9) \
        or s.reconstruction.mirror_displacement_A is not None


def test_bulk_termination_unchanged_minimum_distance_is_d_nn():
    s = rbuild("bulk")
    r = brute_force_pairs(s.positions_A, s.cell_A[1, 1], s.cell_A[2, 2], 10.0)
    assert float(r.min()) == pytest.approx(D_NN, abs=1e-9)
    assert s.reconstruction is None


@pytest.mark.parametrize("term", STATIC + ("p(2x1)a flip-flop ensemble",))
def test_composition_layers_and_step_heights_unchanged(term):
    bulk = rbuild("bulk")
    s = rbuild(term)
    assert s.n_atoms == bulk.n_atoms and set(s.species) == {"Si"}
    assert np.array_equal(s.reconstruction.ideal_positions_A, bulk.positions_A)
    assert np.array_equal(s.layer_index, bulk.layer_index)
    assert np.array_equal(s.terrace_index, bulk.terrace_index)
    assert s.metadata["assertions_passed"][:8] == bulk.metadata["assertions_passed"]
    for a, b in zip(s.metadata["steps"], bulk.metadata["steps"]):
        assert a["measured_height_A"] == b["measured_height_A"]
        assert a["type"] == b["type"]
    tops = np.array([t["top_layer_index"] for t in s.metadata["terrace_map"]])
    depth = tops[s.terrace_index] - s.layer_index
    disp = s.positions_A - s.reconstruction.ideal_positions_A
    assert np.all(disp[depth >= 5] == 0.0)                   # layers 6 and deeper at bulk sites
    assert np.any(np.abs(disp[depth == 4]) > 0)              # layer 5 is displaced (R1)
    deep = s.positions_A[s.layer_index <= int(tops.min()) - 6]
    xs = np.unique(np.round(deep[:, 0], 9))
    assert np.allclose(np.diff(xs), Q, atol=1e-9)            # bulk layer spacing a/4 below
    for t in s.metadata["terrace_map"]:
        assert t["top_atom_height_A"] < t["top_height_A"]    # dimers lie below the ideal plane


def test_edge_atoms_keep_bulk_sites_at_100_and_are_counted():
    s = rbuild("p(2x1)a", azimuth=(1, 0, 0))
    rec = s.reconstruction
    tm = top_mask(s)
    unpaired = tm & (rec.cell_index < 0)
    assert np.any(unpaired)                                  # <100> edges cut dimer cells
    assert np.all(rec.displacement_A[unpaired] == 0.0)
    n = sum(v["unpaired_top_atoms_at_bulk_sites"] for v in rec.metadata["terraces"].values())
    assert n == int(unpaired.sum())
    s = rbuild("p(2x1)a", azimuth=(1, 1, 0))                 # even widths at <110>: all paired
    assert not np.any(top_mask(s) & (s.reconstruction.cell_index < 0))


# ---- flip-flop ensemble ------------------------------------------------------------------------
def test_flipflop_states_and_every_configuration_collision_free():
    s = rbuild("p(2x1)a flip-flop ensemble", azimuth=(1, 0, 0))
    rec = s.reconstruction
    assert s.metadata["options"]["termination"]["label"].startswith("ASSUMPTION B37")
    assert "not a source" in s.metadata["options"]["termination"]["label"]
    assert np.array_equal(rec.positions_for(np.zeros(rec.n_cells, np.uint8)), s.positions_A)
    static = rbuild("p(2x1)a", azimuth=(1, 0, 0))
    assert np.array_equal(static.positions_A, s.positions_A)     # state 0 = static p(2x1)a
    allrev = rec.positions_for(np.ones(rec.n_cells, np.uint8))
    tm = top_mask(s) & (rec.cell_index >= 0)
    # reversed buckling: in every dimer the down atom becomes the up atom
    for c in range(rec.n_cells):
        i, j = np.nonzero(tm & (rec.cell_index == c))[0]
        assert np.sign(s.positions_A[i, 0] - s.positions_A[j, 0]) == \
            -np.sign(allrev[i, 0] - allrev[j, 0])
    per = [None, s.cell_A[1, 1], s.cell_A[2, 2]]
    rng = np.random.default_rng(20260924)
    for _ in range(5):                                        # random members of the ensemble
        f = rng.integers(0, 2, rec.n_cells)
        p = rec.positions_for(f)
        r = brute_force_pairs(p, per[1], per[2], 10.0)
        assert float(r.min()) >= R.COLLISION_FRACTION_OF_DNN * D_NN
        checks.assert_no_duplicates_and_count(p, per, s.n_atoms)
    col = s.metadata["options"]["dimer_reconstruction"]["checks"]["collision"]
    assert col["n_configurations"] == "all 2^n_cells"


def test_flipflop_cells_are_independent_units():
    s = rbuild("p(2x1)a flip-flop ensemble")
    rec = s.reconstruction
    f = np.zeros(rec.n_cells, np.uint8)
    f[3] = 1
    moved = np.linalg.norm(rec.positions_for(f) - s.positions_A, axis=1) > 0
    assert np.all(rec.cell_index[moved] == 3)
    assert np.count_nonzero(top_mask(s) & moved) == 2         # the two atoms of dimer 3


# ---- refusals ----------------------------------------------------------------------------------
def test_pattern_period_mismatch_is_refused():
    st = Staircase(edges="transverse", terrace_layers=(0,), terrace_widths=(4,),
                   boundary_step_layers=0)
    with pytest.raises(R.ReconstructionError, match="not a lattice vector"):
        rbuild("p(2x1)a", st=st, azimuth=(1, 0, 0), edge_periods=3)   # 3a along y at <100>


def test_reconstruction_under_an_overlayer_is_refused():
    ov = OverlayerSpec(material="amorphous SiO2", thickness_A=5.0, density_g_cm3=2.2,
                       label=OVERLAYER_LABEL)
    with pytest.raises(NotImplementedError, match="overlayer"):
        build(FLAT, edge_periods=4, overlayer=ov, termination="p(2x1)s", substrate_layers=8)


@pytest.mark.parametrize("term", ["p(2x1)s", "p(2x1)a", "p(2x2)", "c(4x2)",
                                  "p(2x1)a flip-flop ensemble", "dimer_2x1"])
def test_feature_builder_refuses_reconstruction_with_the_reason(term):
    with pytest.raises(NotImplementedError) as e:
        feature_termination_option(term)
    assert "half-torus" in str(e.value) and "unpaired" in str(e.value)
    assert feature_termination_option("bulk")["label"] == "ASSUMPTION B3"
    assert "circle" in FEATURE_RECONSTRUCTION_REFUSAL


def test_builder_assertion_r3_catches_a_wrong_dimer():
    """(r3) is live: a corrupted displacement table makes the builder fail."""
    old = R.TABLES["p(2x1)s"][(0, 0, 0)]
    try:
        R.TABLES["p(2x1)s"][(0, 0, 0)] = (old[0] - 0.01, old[1], old[2])
        with pytest.raises(StructureAssertionError, match=r"\(r3\)"):
            rbuild("p(2x1)s", st=FLAT)
    finally:
        R.TABLES["p(2x1)s"][(0, 0, 0)] = old
