"""Continuum oxide in the multislice cell: the fix of report X5 after the audit A9b (forward level).

A9b M1  On an ATOMISTIC crystal the multislice does not represent the grown-oxide term of a
        sub-layer thickness difference (the crystal loses whole layers only; 1-D model: about
        0.85-0.87 rad/A against the geometric engine's 4.4549 rad/A, tools/review/x5/
        a9b_c4_nonconformal.py). forward.cell.build_reflection_cell therefore REFUSES an atomistic
        cell whose terraces carry different oxide thicknesses, naming the size of the discrepancy,
        unless the specification states nonconformal_sublayer_acknowledged = True with a TEST_ONLY
        overrides label; then the statement and its size are recorded in the cell layout. A
        conformal cell is unchanged, and a CONTINUUM crystal (whose boundary moves continuously with
        f t) is not affected. The geometric engine is unchanged (tests/forward_geometric).
A propagated two-terrace multislice is NOT RUN here (a cell-construction test).
"""
import pytest

from oxide_cases import LATTICE_LABEL, oxide_spec
from reflection_holo.constants import A_SI_A
from reflection_holo.forward.cell import build_continuum_oxide_cell, build_reflection_cell
from reflection_holo.structure import Staircase, build_si001_terraces
from reflection_holo.structure import oxide as ox

Q = A_SI_A / 4
ACK = "TEST_ONLY: non-conformal atomistic cell, sub-layer term acknowledged (audit A9b M1)"


def _structure(spec, n_terraces=2):
    st = Staircase(edges="transverse", terrace_layers=(0, 1)[:n_terraces],
                   terrace_widths=(2, 2)[:n_terraces], boundary_step_layers=-1)
    return build_si001_terraces(
        azimuth_uvw=(1, 0, 0), azimuth_label="TEST_ONLY: stands in for PROJECT_INPUT item 8",
        staircase=st, edge_periods=1, substrate_layers=16, first_terrace_backbond_uvw=(1, 1, 0),
        termination="bulk", overlayer=spec, vacuum_above_A=25.0, lattice_parameter_A=A_SI_A,
        lattice_parameter_label=LATTICE_LABEL)


def _cell(s):
    return build_reflection_cell(s, vacuum_above_A=20.0, depth_below_A=10.0, bulk_absorber_A=5.0,
                                 top_absorber_A=5.0, entrance_vacuum_z_A=Q)


def test_atomistic_nonconformal_cell_is_refused_with_the_size():
    s = _structure(oxide_spec(tt=(20.0, 20.5), tn=(7, 7)))
    lo, hi = ox.SUBLAYER_RATE_DIFFERENCE_RAD_PER_A
    with pytest.raises(ox.OxideSpecError) as exc:
        _cell(s)
    msg = str(exc.value)
    assert "atomistic multislice cell with a NON-CONFORMAL continuum oxide" in msg
    assert "largest sub-layer thickness difference 0.5000 A" in msg
    assert f"about {lo * 0.5:.2f}-{hi * 0.5:.2f} rad (mod 2 pi)" in msg
    assert "4.4549 rad/A" in msg and "nonconformal_sublayer_acknowledged" in msg


def test_acknowledged_nonconformal_cell_records_the_statement():
    s = _structure(oxide_spec(tt=(20.0, 20.5), tn=(7, 7), nc_ack=True,
                              labels=dict(overrides=ACK)))
    rec = _cell(s).metadata["layout"]["overlayer"]["nonconformal_sublayer"]
    assert rec["acknowledged"] is True and rec["label"] == ACK
    assert rec["largest_sublayer_thickness_difference_A"] == pytest.approx(0.5, abs=1e-12)
    assert rec["statement"] == ox.NONCONFORMAL_SUBLAYER


def test_whole_layer_difference_is_refused_too_and_recorded_as_zero():
    """The decision refuses ANY different thicknesses; for one whole extra consumed layer the
    sub-layer part (and so the stated size) is zero."""
    f = ox.consumed_si_fraction(2.20, A_SI_A)
    s = _structure(oxide_spec(tt=(20.0, 20.0 + Q / f), tn=(7, 8)))
    with pytest.raises(ox.OxideSpecError, match="largest sub-layer thickness difference 0.0000 A"):
        _cell(s)


def test_conformal_and_continuum_cells_are_unchanged():
    cell = _cell(_structure(oxide_spec()))
    assert "nonconformal_sublayer" not in cell.metadata["layout"]["overlayer"]
    # a continuum crystal moves its boundary continuously with f t: no refusal, no record
    c = build_continuum_oxide_cell(
        extent_y_A=10.0, terrace_y_bounds_A=[0.0, 5.0, 10.0], terrace_heights_A=[0.0, 0.0],
        crystal_length_z_A=100.0, vacuum_above_A=40.0, depth_below_A=20.0, bulk_absorber_A=5.0,
        top_absorber_A=5.0, entrance_vacuum_z_A=10.0, oxide=oxide_spec(tt=(20.0, 20.5), tn=(7, 7)),
        lattice_parameter_A=A_SI_A, lattice_parameter_label=LATTICE_LABEL)
    assert "nonconformal_sublayer" not in c.metadata["layout"]["overlayer"]
    assert c.metadata["layout"]["overlayer"]["conformal"] is False
