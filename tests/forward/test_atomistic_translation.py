"""Atomistic whole-crystal translation test (null-test diagnosis, M2 report section 10).

A flat Si(001) terrace (Kirkland potential, [110] azimuth, (0,0,8) condition with the potential's
own MIP) and the same crystal translated by the builder's a/2 translation vector R
(normal component a/2): the translated atom set is verified to equal the builder's crystal with two
more layers (periodic in y and z; 2.6e-13 A measured). With the illumination envelope translated
as well (a fully covariant configuration), the specular Fourier component must change by
exp(-i (k_out - k_in).R) with the engine's k_in and k_out: tolerance 1.0e-2 rad (the rung-3
tolerance, as instructed; measured 1.1e-3 rad, amplitude ratio 1.0024).

With the beam NOT translated the same comparison fails (+0.57 rad at this cell length; -0.06 and
-0.14 rad in cells 2500 and 5000 A longer): the beam then meets the upper crystal 168 A earlier and
the dynamical (0,0,8) reflection has not converged along z. That is a property of the finite cell,
asserted here only as "differs by more than the tolerance" so that a future change that silently
alters it is noticed; it is documented, not a pass criterion of the engine.
"""
import numpy as np
import pytest

pytest.importorskip("abtem")

from null_test_cases import (LEGACY_M2_BEAM, LEGACY_M2_CLEAN_DEPTH_A, run_translation,  # noqa
                             theta_0008, translation_pair)

# the M2 cells (legacy clean depth 21 A and legacy 8 A sheet beam, explicit; [110]): these tests
# reproduce M2 section 10
M2_CELL = dict(clean_depth_A=LEGACY_M2_CLEAN_DEPTH_A, azimuth="110", **LEGACY_M2_BEAM)


@pytest.fixture(scope="module")
def theta():
    return theta_0008()


def test_translated_crystal_is_the_builders_crystal(theta):
    pair = translation_pair(theta=theta, **M2_CELL)
    cA, cB = pair["A"][0], pair["B"][0]
    R = pair["R_slab_A"]
    assert R[0] == pytest.approx(2.71545, abs=1e-9)
    Ly = cA.extent_y_A
    z0, Lc = cA.crystal_start_z_A, cA.metadata["layout"]["crystal_length_z_A"]
    m = cA.atoms_xyz_A + R
    m[:, 1] %= Ly
    m[:, 2] = (m[:, 2] - z0) % Lc
    b = cB.atoms_xyz_A[cB.atoms_xyz_A[:, 0] >= cA.atoms_xyz_A[:, 0].min() + R[0] - 1e-6].copy()
    b[:, 2] -= z0
    from scipy.spatial import cKDTree
    # periodic in y and in z (the crystal's period along the beam; A6 n4: a tree non-periodic in z
    # reports a false mismatch for a translation with a z component, e.g. at [100])
    bs = np.array([1e6, Ly, Lc])

    def wrap(p):
        w = np.mod(p, bs)
        w[w >= bs] = 0.0
        return w
    d, _ = cKDTree(wrap(b), boxsize=bs).query(wrap(m))
    assert len(b) == len(m) and d.max() < 1e-9
    assert pair["check"]["identical_sets"] and pair["check"]["max_distance_A"] < 1e-9


# surface-position-resolved read-out (H2 2.4, N12; null_test_cases.resolved_translation) with bins
# small enough for this short cell (study_depth100.yaml uses 500 A bins, a 1115.5 A exit exclusion
# and a beam lit to the exit plane); amplitude floor as study_depth100.yaml (X2)
RESOLVED = dict(radius_per_A=0.1, x_cut_A=2.0, taper_A=3.0, min_height_A=5.0, bin_A=250.0,
                exit_excl_A=500.0, tol_phase_rad=1e-2, tol_amp=1e-2, amp_floor_rel=0.05)


@pytest.fixture(scope="module")
def covariant(theta):
    """One run of the covariant (moved-beam) pair, read out over all x and surface-resolved."""
    return run_translation(translation_pair(theta=theta, move_beam=True, **M2_CELL),
                           surface_resolved=RESOLVED)


def test_whole_configuration_translation_gives_geometric_phase(covariant):
    r = covariant
    print(f"covariant translation: Delta_phi {r['delta_phi_rad']:+.5f} rad, expected "
          f"{r['expected_wrapped']:+.5f}, error {r['err_rad']:+.2e}, |B|/|A| {r['amp_ratio']:.4f}")
    assert abs(r["err_rad"]) <= 1.0e-2
    assert abs(r["amp_ratio"] - 1) <= 1.0e-2


def test_fixed_beam_translation_is_not_converged_at_minimum_buildup(theta):
    r = run_translation(translation_pair(theta=theta, move_beam=False, **M2_CELL))
    print(f"fixed beam: Delta_phi {r['delta_phi_rad']:+.5f} rad, error {r['err_rad']:+.2e}")
    assert abs(r["err_rad"]) > 1.0e-2


def test_whole_configuration_translation_surface_resolved(covariant):
    """The covariant pair must give the geometric phase in EVERY surface bin (same 1e-2 rad and
    1e-2 amplitude criteria as above), not only in the x-summed component."""
    sr = covariant["surface_resolved"]
    for q in sr["rows"]:
        print(f"z_s {q['z_start_A']:7.1f}-{q['z_end_A']:7.1f} A (from contact {q['d_start_A']:6.1f}): "
              f"err {q['err_rad']:+.2e} rad, |B|/|A| {q['amp_ratio']:.4f}, |E_A| {q['E_A_abs']:.4f}")
    assert sr["n_bins"] >= 2
    assert sr["z_contact_A"]["A"] == pytest.approx(sr["z_contact_A"]["B"], abs=1e-9)
    for q in sr["rows"]:
        assert abs(q["err_rad"]) <= 1.0e-2
        assert abs(q["amp_ratio"] - 1) <= 1.0e-2
