"""Tests for multislice/cell.py (R2 item 2d)."""
import numpy as np
import pytest

from reflection_holo.constants import A_SI, wavelength
from reflection_holo.geometry import Surface
from reflection_holo.multislice.cell import (diamond_atoms_slab, top_plane, vacuum_criterion,
                                             flat_surface_cell, length_and_window,
                                             _unit_with_termination)
from reflection_holo.multislice.illumination import incident_wave, end_face_fraction
from reflection_holo.multislice.propagate import bandlimit, flux

S001 = Surface((0, 0, 1), (1, 1, 0))
S111 = Surface((1, -1, 1), (1, 1, 0))
a = A_SI.value


def test_periods_and_density_001():
    """External fact: calculator section 9: the beam-axis period is a/sqrt2 = 3.8402 A for the [110] azimuth.

    Also the diamond density is 8 atoms per a^3 (calculator section 2). Tolerance 1e-3 A.
    """
    at, per = diamond_atoms_slab(S001, a)
    assert abs(per[0] - a / np.sqrt(2)) < 1e-3 and abs(per[2] - a) < 1e-3
    assert len(at) == round(8 * np.prod(per) / a ** 3)


def test_periods_111_and_bilayer_termination():
    """External fact: calculator section 8 gives periods a sqrt3 = 9.4066 A and a sqrt1.5 = 6.6515 A.

    Calculator 2b gives intra/inter-bilayer gaps 0.7839/2.3516 A. The bulk-terminated top plane must
    sit above the 2.35 A gap, so the next plane down is 0.7839 A below. Tolerance 1e-3 A.
    """
    at, per = diamond_atoms_slab(S111, a)
    assert abs(per[2] - a * np.sqrt(3)) < 1e-3 and abs(per[1] - a * np.sqrt(1.5)) < 1e-3
    zt = top_plane(at, per[2])
    zs = np.unique(np.round(at[:, 2], 3))
    below = zs[zs < zt - 1e-3]
    nxt = (zt - below.max()) if len(below) else (zt + per[2] - zs.max())
    assert abs(nxt - a * np.sqrt(3) / 12) < 1e-3   # 0.7839 = d111/4


@pytest.mark.parametrize("surf,recon", [(S001, None), (S111, None), (S001, "2x1")],
                         ids=["Si001", "Si111", "Si001_2x1"])
def test_box_density_equals_8_over_a3(surf, recon):
    """External fact: the diamond conventional cell a^3 holds 8 atoms (repo:physics_conventions.md
    'Structure factor': 8-atom diamond cell; calculator sec.2). The terminated period box (and the
    doubled 2x1 box) must have number density 8/a^3. Tolerance 1e-9 relative."""
    unit, _, per = _unit_with_termination(surf, a, recon)
    assert abs(len(unit) / np.prod(per) / (8 / a ** 3) - 1) < 1e-9
    assert np.all(unit[:, 2] <= 1e-9) and np.any(unit[:, 2] == 0.0)


def test_built_cell_density_8_over_a3():
    """External fact: 8 atoms per a^3 (conventions 'Structure factor'). The atoms of the BUILT cell in
    the two outermost z periods, summed over all sub-slices, must have density 8/a^3. Tolerance 1e-9."""
    c = flat_surface_cell(S001, 200e3, 16.474e-3, dz=0.1, dy=0.3, depth=20.0, absorber_thickness=20.0,
                          absorption=False)
    px, py, pz = c.meta["periods"]
    zs = c.z_surface
    n = sum(int(np.count_nonzero((at[:, 1] > zs - 2 * pz + 1e-6) & (at[:, 1] <= zs + 1e-6)))
            for at in c.atoms_per_slice)
    assert abs(n / (px * py * 2 * pz) / (8 / a ** 3) - 1) < 1e-9


def test_no_wrap_rise_matches_calculator_T19():
    """External fact: calculator T19: rise of the reflected beam over L = 198.248 A at 22.495 mrad is 4.4604 A.

    The vacuum criterion must contain this rise term exactly; tolerance 1e-3 A. The Fresnel and guard
    terms are set to zero by construction for the check.
    """
    L, th = 198.248, 22.4953e-3
    v = vacuum_criterion(L, th, 0.0, 0.0, 0.0, guard=0.0)
    assert abs(v - 4.4604) < 1e-3


def test_window_criterion_leaves_steady_band():
    """External fact (derivation premise): a steady state is reached after a distance (NOTES_C P5).

    Criterion (3) gives H_w - 2s - D T = w_extract exactly (DERIVED_HERE identity). Tolerance 1e-9 A.
    """
    Hw, L, DT = length_and_window(16.474e-3, 18.47e-3, 100.0, 3.0, 3.0, 20.0)
    assert abs(Hw - 2 * 3.0 - DT - 20.0) < 1e-9
    assert L > (3.0 + Hw) / np.tan(16.474e-3)


def test_built_cell_window_no_end_face_leak():
    """External fact: task 2c/2d require that the built cell's illumination has end-face fraction < 1e-3.

    Checked at the entrance plane both for the raw compact window and for the wave band-limited to the
    propagator circle (what reflectivity.exit_wave propagates). The extraction band must lie inside the
    vacuum and the cell must be bulk-terminated with atoms below z_surface only (tolerance 1e-6 A).
    absorption=False: Si absorptive parameters are MISSING (item 21; card:peng_ch13 p.20).
    """
    c = flat_surface_cell(S001, 200e3, 16.474e-3, dz=0.1, dy=0.3, depth=20.0, absorber_thickness=20.0,
                          absorption=False)
    ang = c.meta["angle"]
    psi = incident_wave(c.grid, 16.474e-3, wavelength(200e3), c.z_surface, ang["window"], c.meta["softness"])
    assert end_face_fraction(psi, c.grid, c.z_surface) < 1e-3
    pb = bandlimit(psi, c.grid, 2 / 3)
    pb = pb / np.sqrt(flux(pb, c.grid))
    assert end_face_fraction(pb, c.grid, c.z_surface) < 1e-3
    zmax = max(at[:, 1].max() for at in c.atoms_per_slice)
    assert zmax <= c.z_surface + 1e-6
    assert ang["band"][0] > c.z_surface and ang["band"][1] < c.z_surface + c.meta["vacuum"]
