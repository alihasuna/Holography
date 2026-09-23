"""Height-field geometric engine (agent T2): shadow and blocked-view masks against the 1-D
``quantification.shadow.shadow_masks``, the exit-plane ray trace against the terrace engine's
``trace_exit_points``, brute-force checks of the definitions, the phase sign of a ridge against a
trench, and the B4 scope refusals. TEST_ONLY values stand in for PROJECT_INPUT items 7, 8 and 13 and
never appear in configs/.

Tolerances, fixed before the first run: masks and statuses must be IDENTICAL (they are boolean
results of the same inequalities); source positions and phases agree to 1e-9 (A, rad; floating
point)."""
import math

import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.forward.geometric import (STATUS, FieldLayout, OutsideB4ScopeError,
                                               terrace_model_from_structure, trace_exit_points)
from reflection_holo.forward.geometric.height_field import (HeightField, HeightFieldParams,
                                                            height_field_exit_wave,
                                                            require_b4_scope_height_field,
                                                            trace_height_field)
from reflection_holo.geometry.specular import specular_condition_for, wrap_to_pi
from reflection_holo.geometry.wavelength import k_ang_per_A
from reflection_holo.quantification.shadow import height_field_masks, shadow_masks
from reflection_holo.structure import Staircase, build_si001_terraces
from reflection_holo.structure.shapes import HalfTorus

THETA = specular_condition_for((0, 0, 8), (0, 0, 1), E_keV=200.0, V0_V=12.0, a_A=A_SI_A).theta_ext
LAYER = A_SI_A / 4.0
TH_LABEL = "TEST_ONLY: stands in for PROJECT_INPUT item 7 (glancing angle)"
GEO = "TEST_ONLY: stands in for PROJECT_INPUT item 13 (feature geometry)"


def _field(fn, *, profile="piecewise_constant", L=3000.0, dz=1.0, up=0.0, label=GEO):
    return HeightField(height_fn=fn, profile=profile,
                       layer_spacing_A=LAYER if profile == "piecewise_constant" else None,
                       z_start_A=0.0, field_length_A=L, surface_dz_A=dz, upstream_level_A=up,
                       description="test surface", label=label, source="test")


# --------------------------------------------------------------------------------------------------
# masks against the 1-D shadow module
# --------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("h_start, after", [
    (0.0, (2 * LAYER, LAYER)),             # up-step (blocked strip before it), then down-step
    (2 * LAYER, (0.0, 3 * LAYER)),          # down-step (shadow behind it), then up-step
    (0.0, (-LAYER, 0.0)),                    # a one-layer trench crossing the beam
    (0.0, (14 * LAYER, 0.0)),                # a tall ridge crossing the beam (1154 A strips)
])
def test_height_field_masks_equal_shadow_masks_row_by_row(h_start, after):
    """Each row of a 2-D field (edges moving with y) equals shadow_masks on its own profile."""
    dz, n = 1.0, 4000
    z = (np.arange(n) + 0.5) * dz
    rows = []
    refs = []
    for shift in (0.0, 37.0, 123.0, 400.0):
        edges = np.array([800.0, 1900.0]) + shift          # on cell boundaries (integers)
        ref = shadow_masks(z, edges_A=edges, h_start_A=h_start, heights_after_A=np.array(after),
                           theta_in_ext_rad=THETA, theta_out_ext_rad=THETA)
        rows.append(ref.height_A)
        refs.append(ref)
    m = height_field_masks(np.array(rows), z_start_A=0.0, dz_A=dz, profile="piecewise_constant",
                           upstream_level_A=h_start, theta_in_ext_rad=THETA,
                           theta_out_ext_rad=THETA)
    for i, ref in enumerate(refs):
        assert np.array_equal(m.illuminated[i], ref.illuminated)
        assert np.array_equal(m.visible[i], ref.visible)
        assert np.array_equal(m.usable[i], ref.usable)
    assert (~m.usable).any()                                   # the test has strips to compare


def test_piecewise_linear_masks_equal_the_definition_brute_force():
    """Vertices of a continuous surface: SHADOWED iff an upstream point z' < z has
    h(z') > h(z) + (z - z') tan(theta_in) (the flat surface upstream included), BLOCKED iff a
    downstream point z' > z has h(z') > h(z) + (z' - z) tan(theta_out); evaluated directly."""
    rng = np.random.default_rng(20260923)
    n, dz = 400, 5.0
    z = np.arange(n + 1) * dz
    t = math.tan(THETA)
    H = np.cumsum(rng.normal(0.0, 0.08, size=(6, n + 1)), axis=1)
    up = 0.3
    m = height_field_masks(H, z_start_A=0.0, dz_A=dz, profile="piecewise_linear",
                           upstream_level_A=up, theta_in_ext_rad=THETA, theta_out_ext_rad=THETA)
    for r in range(H.shape[0]):
        h = H[r]
        for j in range(n + 1):
            shadowed = max(up, h[0]) > h[j] + (z[j] - 0.0) * t + 1e-9 or any(
                h[k] > h[j] + (z[j] - z[k]) * t + 1e-9 for k in range(j))
            blocked = any(h[k] > h[j] + (z[k] - z[j]) * t + 1e-9 for k in range(j + 1, n + 1))
            assert m.illuminated[r, j] == (not shadowed), (r, j)
            assert m.visible[r, j] == (not blocked), (r, j)
    assert (~m.illuminated).any() and (~m.visible).any()


def test_exit_plane_trace_equals_the_terrace_engine_trace():
    """The built (0, 2, 1) staircase at [100] (60 periods per terrace) as a height field with a/4
    cells: status and source z of every exit-plane point equal forward.geometric.trace_exit_points
    (upstream: the first terrace level continues, layout upstream 'none')."""
    st = Staircase(edges="transverse", terrace_layers=(0, 2, 1), terrace_widths=(60, 60, 60),
                   boundary_step_layers=-1)
    s = build_si001_terraces(azimuth_uvw=(1, 0, 0), azimuth_label="TEST_ONLY: item 8",
                             staircase=st, edge_periods=1, substrate_layers=4,
                             first_terrace_backbond_uvw=(1, 1, 0), termination="bulk",
                             overlayer=None, vacuum_above_A=10.0, lattice_parameter_A=A_SI_A,
                             lattice_parameter_label="ASSUMPTION B2")
    model = terrace_model_from_structure(s)
    P = model.period_A
    starts, Hs = np.array(model.starts_A), np.array(model.heights_A)

    def fn(y, z):
        k = np.searchsorted(starts, np.mod(z, P), side="right") - 1
        return np.broadcast_to(Hs[k], np.broadcast(y, z).shape)

    hf = HeightField(height_fn=fn, profile="piecewise_constant", layer_spacing_A=LAYER,
                     z_start_A=0.0, field_length_A=P, surface_dz_A=LAYER, upstream_level_A=Hs[0],
                     description="staircase", label=GEO, source="test")
    x = np.linspace(Hs.min() - 3, Hs.max() + P * math.tan(THETA) + 3, 4001)
    y = np.array([0.0, 1.0])
    X, Y = np.meshgrid(x, y, indexing="ij")
    lay = FieldLayout(field_length_A=P, z_start_A=0.0, x_offset_A=0.0, periods=1, upstream="none")
    ref = trace_exit_points(model, X, Y, layout=lay, theta_in_ext_rad=THETA,
                            theta_out_ext_rad=THETA)
    got = trace_height_field(hf, x, y, theta_in_ext_rad=THETA, theta_out_ext_rad=THETA)
    assert np.array_equal(ref["status"], got["status"])
    for name in ("lit", "illumination_shadow", "riser", "below_surface", "outside_field_of_view"):
        assert (got["status"] == STATUS[name]).any(), name
    both = np.isfinite(ref["source_z_A"])
    assert np.array_equal(both, np.isfinite(got["source_z_A"]))
    assert np.max(np.abs(ref["source_z_A"][both] - got["source_z_A"][both])) <= 1e-9


def test_hidden_neighbour_marks_the_blocked_strip():
    """A single a/2 up-step (upper terrace downstream) hides h/tan(theta) of the lower terrace in
    front of the riser: exit rows whose sources straddle that strip are flagged, others not."""
    zb = 1500.0
    hf = _field(lambda y, z: np.where(z >= zb, 2 * LAYER, 0.0) + 0 * y, L=3000.0)
    x = np.linspace(-1.0, 2 * LAYER + 3000 * math.tan(THETA) + 1.0, 3001)
    tr = trace_height_field(hf, x, np.array([0.0]), theta_in_ext_rad=THETA,
                            theta_out_ext_rad=THETA)
    zs = tr["source_z_A"][:, 0]
    flagged = tr["hidden_neighbour"][:, 0]
    strip = (zb - 2 * LAYER / math.tan(THETA), zb)
    assert flagged.sum() == 2
    zf = np.sort(zs[flagged])
    assert zf[0] <= strip[0] + 1.0 and zf[1] >= zb       # one source on each side of the strip
    lit = np.isfinite(zs)
    assert not np.any((zs[lit] > strip[0] + 1.0) & (zs[lit] < zb - 1.0))   # nothing imaged inside


# --------------------------------------------------------------------------------------------------
# phase: sign of a ridge against a trench
# --------------------------------------------------------------------------------------------------
def _run(hf, n_y=8, dy=0.5):
    params = HeightFieldParams(exit_plane_pixel_A=(0.25, dy), n_y=n_y, x_margin_A=5.0,
                               reflectivity_amplitude=1.0)
    b4 = require_b4_scope_height_field(hf, azimuth_uvw=(1, 0, 0), termination="bulk",
                                       overlayer=None, illumination="plane_wave", beam="specular",
                                       layer_index_parity="any")
    return height_field_exit_wave(hf, energy_keV=200.0, theta_in_ext_rad=THETA,
                                  theta_label=TH_LABEL, params=params, b4=b4)


def _envelope_phase(run):
    ew = run.exit_wave
    x = ew.x0_A + ew.dx_A * np.arange(ew.psi.shape[0])
    k = k_ang_per_A(200.0)
    return np.angle(ew.psi * np.exp(-1j * k * math.sin(THETA) * x)[:, None])


@pytest.mark.parametrize("sign", [+1, -1])
def test_strip_phase_is_minus_q_h_and_ridge_opposes_trench(sign):
    """A one-layer strip along the beam (uniform in z: no shadows), raised (+a/4, ridge) or lowered
    (-a/4, trench): phase(strip) - phase(flat) = -q_x h exactly (1e-9 rad after wrapping), so the
    ridge and the trench give opposite phases."""
    hf = _field(lambda y, z: np.where(np.abs(y - 2.0) < 1.1, sign * LAYER, 0.0) + 0 * z)
    r = _run(hf)
    lit = r.trace["status"] == STATUS["lit"]
    phi = _envelope_phase(r)
    q_x = 2 * k_ang_per_A(200.0) * math.sin(THETA)
    strip = lit & (np.abs(r.trace["source_h_A"] - sign * LAYER) < 1e-12)
    flat = lit & (np.abs(r.trace["source_h_A"]) < 1e-12)
    assert strip.sum() > 100 and flat.sum() > 100
    for mask, h in ((strip, sign * LAYER), (flat, 0.0)):
        assert np.max(np.abs(wrap_to_pi(phi[mask] + q_x * h))) <= 1e-9
    d = float(np.angle(np.mean(np.exp(1j * phi[strip]))) - np.angle(np.mean(np.exp(1j * phi[flat]))))
    assert abs(float(wrap_to_pi(d + sign * q_x * LAYER))) <= 1e-9


def test_torus_ridge_and_trench_phases_have_opposite_signs():
    """The shared HalfTorus, side of the ring in the exit columns (R = 20000 A, r = 3 A: a trench
    floor is lit and visible only where the groove section along a column exceeds
    2 depth / tan(theta), about 494 A here, against 4 sqrt(R r) = 980 A): every lit exit-plane
    pixel carries -q_x layer_height_A(source) (1e-9 rad); the lit footprint sources lie above the
    flat surface for the ridge and below it for the trench, so their unwrapped geometric phases
    have opposite signs."""
    q_x = 2 * k_ang_per_A(200.0) * math.sin(THETA)
    signs = {}
    for kind in ("ridge", "trench"):
        t = HalfTorus(center_y_A=100.0 - 20000.0, center_z_A=1500.0, major_radius_A=20000.0,
                      minor_radius_A=3.0, kind=kind, label=GEO, source="test")
        hf = _field(lambda y, z, t=t: t.layer_height_A(y, z, layer_spacing_A=LAYER), L=3000.0)
        r = _run(hf, n_y=400)
        lit = r.trace["status"] == STATUS["lit"]
        phi = _envelope_phase(r)
        assert np.max(np.abs(wrap_to_pi(phi[lit] + q_x * r.trace["source_h_A"][lit]))) <= 1e-9
        foot = lit & (np.abs(r.trace["source_h_A"]) > 0)
        assert foot.sum() > 0, kind
        signs[kind] = np.sign(-q_x * r.trace["source_h_A"][foot])
    assert np.all(signs["ridge"] < 0) and np.all(signs["trench"] > 0)


# --------------------------------------------------------------------------------------------------
# scope refusals
# --------------------------------------------------------------------------------------------------
def test_b4_scope_refusals():
    hf = _field(lambda y, z: np.where(z > 100.0, LAYER, 0.0) + 0 * y)
    ok = dict(azimuth_uvw=(1, 0, 0), termination="bulk", overlayer=None, illumination="plane_wave",
              beam="specular", layer_index_parity="any")
    assert "exact <100>" in require_b4_scope_height_field(hf, **ok)["statement"]
    with pytest.raises(OutsideB4ScopeError, match="B4"):
        require_b4_scope_height_field(hf, **dict(ok, azimuth_uvw=(1, 1, 0)))
    assert require_b4_scope_height_field(hf, **dict(ok, azimuth_uvw=(1, 1, 0),
                                                    layer_index_parity="even"))
    with pytest.raises(OutsideB4ScopeError, match="overlayer"):
        require_b4_scope_height_field(hf, **dict(ok, overlayer={"material": "SiO2"}))
    with pytest.raises(OutsideB4ScopeError, match="plane-wave"):
        require_b4_scope_height_field(hf, **dict(ok, illumination="convergent"))
    with pytest.raises(OutsideB4ScopeError, match="termination"):
        require_b4_scope_height_field(hf, **dict(ok, termination="2x1"))
    cont = _field(lambda y, z: 0.1 * np.sin(z / 50.0) + 0 * y, profile="piecewise_linear",
                  label="ASSUMPTION B33 (stands in for PROJECT_INPUT item 13)")
    with pytest.raises(OutsideB4ScopeError, match="TEST_ONLY"):
        require_b4_scope_height_field(cont, **ok)
    bad = _field(lambda y, z: 0.5 + 0 * y * z)                  # not a multiple of a/4
    with pytest.raises(ValueError, match="integer multiples"):
        bad.sample(np.array([0.0]))
    with pytest.raises(ValueError, match="divide"):
        _field(lambda y, z: 0 * y * z, L=100.0, dz=3.0)
