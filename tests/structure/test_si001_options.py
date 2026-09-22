"""Options and required arguments of the Si(001) builder (spec 4.2; no silent defaults)."""
import inspect

import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.structure import OverlayerSpec, Staircase, build_si001_terraces
from si001_test_inputs import AZIMUTH_LABEL, LATTICE_LABEL, OVERLAYER_LABEL, build

FLAT = Staircase(edges="transverse", terrace_layers=(0, 1), terrace_widths=(2, 2),
                 boundary_step_layers=-1)


def _kwargs():
    return dict(azimuth_uvw=(1, 1, 0), azimuth_label=AZIMUTH_LABEL, staircase=FLAT,
                edge_periods=2, substrate_layers=5, first_terrace_backbond_uvw=(1, 1, 0),
                termination="bulk", overlayer=None, vacuum_above_A=10.0,
                lattice_parameter_A=A_SI_A, lattice_parameter_label=LATTICE_LABEL)


def test_builder_has_no_defaults():
    sig = inspect.signature(build_si001_terraces)
    assert all(p.default is inspect.Parameter.empty for p in sig.parameters.values())
    assert all(p.kind is inspect.Parameter.KEYWORD_ONLY for p in sig.parameters.values())


@pytest.mark.parametrize("missing", list(_kwargs()))
def test_every_argument_is_required(missing):
    kw = _kwargs()
    kw.pop(missing)
    with pytest.raises(TypeError, match=missing):
        build_si001_terraces(**kw)


@pytest.mark.parametrize("label", ["", "  ", "item 8", "measured [110]", None])
def test_azimuth_needs_an_evidence_label(label):
    kw = _kwargs()
    kw["azimuth_label"] = label
    with pytest.raises(ValueError, match="label"):
        build_si001_terraces(**kw)


def test_dimer_reconstruction_not_implemented_names_missing_source():
    kw = _kwargs()
    kw["termination"] = "dimer_2x1"
    with pytest.raises(NotImplementedError) as e:
        build_si001_terraces(**kw)
    msg = str(e.value)
    assert "NOT IMPLEMENTED" in msg and "source" in msg and "dimer bond length" in msg
    assert "must not be invented" in msg


def test_unknown_termination_refused():
    kw = _kwargs()
    kw["termination"] = "7x7"
    with pytest.raises(ValueError, match="ASSUMPTION B3"):
        build_si001_terraces(**kw)


def test_option_labels_recorded_bulk_clean():
    s = build(FLAT)
    o = s.metadata["options"]
    assert o["termination"] == {"value": "bulk", "label": "ASSUMPTION B3",
                                "note": "unreconstructed bulk truncation of the diamond lattice"}
    assert o["dimer_reconstruction"]["status"].startswith("NOT IMPLEMENTED")
    assert o["overlayer"]["value"] is None and o["overlayer"]["label"] == "ASSUMPTION B7"
    assert o["riser_relaxation"]["value"] == "none"
    assert o["riser_relaxation"]["label"] == "ASSUMPTION"
    assert s.metadata["lattice"]["a_label"] == "ASSUMPTION B2"


def test_overlayer_spec_fields_are_required():
    with pytest.raises(TypeError):
        OverlayerSpec(material="amorphous SiO2", thickness_A=10.0, label=OVERLAYER_LABEL)
    with pytest.raises(TypeError):
        OverlayerSpec(material="amorphous SiO2", density_g_cm3=2.2, label=OVERLAYER_LABEL)


@pytest.mark.parametrize("thick,rho,label,err", [
    (0.0, 2.2, OVERLAYER_LABEL, "thickness"),
    (-5.0, 2.2, OVERLAYER_LABEL, "thickness"),
    (10.0, 0.0, OVERLAYER_LABEL, "density"),
    (10.0, 2.2, "guess", "label"),
    (50.0, 2.2, OVERLAYER_LABEL, "cannot hold"),       # vacuum_above_A = 10 A
])
def test_overlayer_invalid_values_refused(thick, rho, label, err):
    ov = OverlayerSpec(material="amorphous SiO2", thickness_A=thick, density_g_cm3=rho,
                       label=label)
    with pytest.raises(ValueError, match=err):
        build(FLAT, overlayer=ov)


def test_overlayer_declared_region_only():
    # TEST_ONLY values standing in for PROJECT_INPUT item 12
    ov = OverlayerSpec(material="amorphous SiO2", thickness_A=8.0, density_g_cm3=2.2,
                       label=OVERLAYER_LABEL)
    s = build(FLAT, overlayer=ov, vacuum_above_A=12.0)
    s0 = build(FLAT, vacuum_above_A=12.0)
    o = s.metadata["options"]["overlayer"]
    assert o["thickness_A"] == 8.0 and o["density_g_cm3"] == 2.2 and o["label"] == OVERLAYER_LABEL
    assert o["atomistic_content"].startswith("NOT IMPLEMENTED") and o["atoms_placed"] == 0
    tops = [t["top_height_A"] for t in s.metadata["terrace_map"]]
    assert o["per_terrace_x_range_A"] == [[h, h + 8.0] for h in tops]
    assert s.n_atoms == s0.n_atoms                     # no overlayer atoms invented
    assert s.metadata["positions_sha256"] == s0.metadata["positions_sha256"]


def test_overlayer_must_be_spec_or_explicit_none():
    with pytest.raises(TypeError):
        build(FLAT, overlayer={"thickness_A": 10.0})


@pytest.mark.parametrize("bad", [3, 0, 2.5])
def test_substrate_too_thin_or_non_integer_refused(bad):
    kw = _kwargs()
    kw["substrate_layers"] = bad
    with pytest.raises(ValueError, match="substrate_layers"):
        build_si001_terraces(**kw)


def test_backbond_axis_must_be_110_type():
    kw = _kwargs()
    kw["first_terrace_backbond_uvw"] = (1, 0, 0)
    with pytest.raises(ValueError, match="back-bond axis"):
        build_si001_terraces(**kw)
