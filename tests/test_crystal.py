"""Surface cells, terminations and stacking-correct steps."""
import numpy as np
import pytest

from reflection_holo.crystal import (SurfaceCell, TerraceStructure, flat, fcc_period,
                                     steps_parallel, steps_transverse)

A = 5.4309


@pytest.mark.parametrize("frame,n_atoms,h_unit,n_planes", [
    ("si111_110", 12, A / np.sqrt(3), 2),
    ("si001_110", 4, A / 4, 2),
    ("si001_100", 8, A / 4, 4)])
def test_cells(frame, n_atoms, h_unit, n_planes):
    c = SurfaceCell(frame, A)
    assert len(c.atoms) == n_atoms
    vol = np.prod(c.periods)
    assert n_atoms / vol == pytest.approx(8 / A**3, rel=1e-12)
    units, h = c.termination_units()
    assert h == pytest.approx(h_unit, rel=1e-12)
    assert len(c.plane_z()) == n_planes


def test_fcc_periods():
    assert fcc_period((1, -1, 1), A) == pytest.approx(A * np.sqrt(3))
    assert fcc_period((1, 1, 0), A) == pytest.approx(A / np.sqrt(2))
    assert fcc_period((0, 0, 1), A) == pytest.approx(A)


def test_si111_bilayer_cut_is_in_wide_gap():
    c = SurfaceCell("si111_110", A)
    units, h = c.termination_units()
    for u in units:
        assert len(u) == 2
        assert u[1] - u[0] == pytest.approx(h / 4, abs=1e-9)    # intra-bilayer d/4


def _atoms(ts, z_planes):
    out = []
    for t, z in enumerate(z_planes):
        x, y = ts.plane_atoms(t, z)
        out.append(np.column_stack([x, y, np.full(len(x), z)]))
    return np.concatenate(out)


def _is_translate(P, Q, R, periods):
    """Is Q (top part) = P + R modulo the in-plane periods?"""
    Py, Pz = (round(float(p), 6) for p in periods)

    def wrap(a):
        a = np.round(a, 6)
        a[:, 1] = np.round(np.mod(a[:, 1], Py), 6) % Py
        a[:, 2] = np.round(np.mod(a[:, 2], Pz), 6) % Pz
        return set(map(tuple, a))
    return wrap(P + R) == wrap(Q.copy())


@pytest.mark.parametrize("frame,levels,R_cubic", [
    ("si111_110", 1, 0.5 * A * np.array([1.0, 0.0, 1.0])),   # (a/2)[101], h = d111
    ("si001_110", 2, 0.5 * A * np.array([1.0, 0.0, 1.0])),   # (a/2)[101], h = a/2
])
def test_translation_steps(frame, levels, R_cubic):
    c = SurfaceCell(frame, A)
    R = c.R @ R_cubic
    lo = TerraceStructure(c, Ly=c.periods[1], x_bottom=-20.0, level=flat(0), max_level=levels)
    hi = TerraceStructure(c, Ly=c.periods[1], x_bottom=-20.0, level=flat(levels), max_level=levels)
    P = _atoms(lo, lo.plane_z)
    Q = _atoms(hi, hi.plane_z)
    assert R[0] == pytest.approx(levels * lo.h_unit, abs=1e-9)
    top = P[P[:, 0] > -20.0 + 8.0]                     # away from the bottom cut
    Qtop = Q[Q[:, 0] > -20.0 + 8.0 + R[0]]
    assert _is_translate(top, Qtop, R, (c.periods[1], c.periods[2]))


def test_si001_single_layer_step_is_not_a_translation():
    c = SurfaceCell("si001_110", A)
    lo = TerraceStructure(c, Ly=c.periods[1], x_bottom=-20.0, level=flat(0), max_level=1)
    hi = TerraceStructure(c, Ly=c.periods[1], x_bottom=-20.0, level=flat(1), max_level=1)
    P = _atoms(lo, lo.plane_z)
    Q = _atoms(hi, hi.plane_z)
    top = P[P[:, 0] > -12.0]
    Qtop = Q[Q[:, 0] > -12.0 + A / 4]
    # no in-plane shift on an a/8 grid maps the lower terrace onto the upper one
    Py, Pz = c.periods[1], c.periods[2]
    for sy in np.arange(0, Py, A / 8 / np.sqrt(2)):
        for sz in np.arange(0, Pz, A / 8 / np.sqrt(2)):
            assert not _is_translate(top, Qtop, np.array([A / 4, sy, sz]), (Py, Pz))


def test_step_maps():
    f = steps_parallel(20.0, [0, 1])
    assert list(f(np.array([1.0, 11.0]), 0.0)) == [0, 1]
    g = steps_transverse([100.0], [0, 1])
    assert g(np.array([0.0]), 50.0)[0] == 0 and g(np.array([0.0]), 150.0)[0] == 1
