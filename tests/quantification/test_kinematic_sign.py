"""Independent physical anchor for the SIGN of the step phase (audit A2 finding m9; docs/05 5.8).

The existing sign tests invert the package's own forward model. Here the step phase is computed from
an explicit kinematic (first Born) scattering sum over the atoms built by build_si001_terraces, in the
exp(+ik.r) convention (docs/physics_conventions.md), and compared with the SIGNED relation of
reflection_holo.quantification.height:
    A_T = sum_{j in terrace T} exp(-i q.r_j) exp(-depth_j / L),   q = k_out - k_in,
    arg(A_to / A_from) = -|q.n_hat| (h_to - h_from)   (mod 2 pi),   |q.n_hat| = sensitivity_rad_per_A.
The wavevectors are written out here (slab frame x = outward normal, z = beam azimuth):
k_in = k (-sin th, 0, cos th), k_out = k (sin th, 0, cos th), k = 2 pi / lambda; th is the external
(0,0,8) angle at 200 keV, V0 = 12 V (ASSUMPTION B1). The attenuation exp(-depth/L), L = 10 A, depth
below each terrace's own top, makes the sum converge; it is common to both terraces. The laterally
averaged potential of the two a/4 terrace types is the same up to the a/4 shift, so the kinematic
residual vanishes at every azimuth (C2 check H6). Heights h are measured on the built atoms.

Tolerance, stated a priori: the slab is truncated after 120 layers (163 A), so the neglected tail is
exp(-163/10) = 8e-8 of each amplitude; the phase error is below 2 x 8e-8 rad. Tolerance 1e-6 rad.
Discrimination: the opposite sign convention would differ by |2 wrap(q h)| > 0.1 rad in every case
(asserted), so the test fails for a sign error. The inversion height_from_phase, with the branch
from the lattice constraint (the candidate nearest to a multiple of a/4), returns the signed h.
"""
import numpy as np
import pytest

from reflection_holo.constants import A_SI_A, BEAM_ENERGY_SUPPLIED_KEV, V0_SI_ASSUMPTION_V
from reflection_holo.geometry.specular import specular_condition_for, wrap_to_pi
from reflection_holo.geometry.wavelength import wavelength_A
from reflection_holo.quantification.height import (height_candidates_A, height_from_phase,
                                                    sensitivity_rad_per_A)
from reflection_holo.structure import Staircase, build_si001_terraces

LAM = wavelength_A(BEAM_ENERGY_SUPPLIED_KEV)
TH = specular_condition_for((0, 0, 8), (0, 0, 1), E_keV=BEAM_ENERGY_SUPPLIED_KEV,
                            V0_V=V0_SI_ASSUMPTION_V, a_A=A_SI_A).theta_ext
L_ATT = 10.0
TOL = 1e-6
SIGMAS = dict(sigma_phi_rad=0.01, sigma_theta_in_rad=0.05e-3, sigma_theta_out_rad=0.05e-3,
              sigma_wavelength_rel=1e-6)          # TEST_ONLY


def born_ratio(structure, step):
    k = 2 * np.pi / LAM
    q = k * np.array([2 * np.sin(TH), 0.0, 0.0])            # k_out - k_in, slab frame
    tops = [t["top_height_A"] for t in structure.metadata["terrace_map"]]
    amp = {}
    for T in (step["from_terrace"], step["to_terrace"]):
        r = structure.positions_A[structure.terrace_index == T]
        depth = tops[T] - r[:, 0]
        amp[T] = np.sum(np.exp(-1j * (r @ q)) * np.exp(-depth / L_ATT))
    return amp[step["to_terrace"]] / amp[step["from_terrace"]]


@pytest.mark.parametrize("az", [(1, 1, 0), (1, 0, 0)])
@pytest.mark.parametrize("layers,boundary", [((0, 2), -2), ((2, 0), 2), ((0, 1), -1), ((1, 0), 1)],
                         ids=["a2_up", "a2_down", "a4_up", "a4_down"])
def test_born_sum_over_built_atoms_gives_the_signed_step_phase(az, layers, boundary):
    st = Staircase(edges="transverse", terrace_layers=layers, terrace_widths=(6, 6),
                   boundary_step_layers=boundary)
    s = build_si001_terraces(azimuth_uvw=az, azimuth_label="TEST_ONLY: stands in for item 8",
                             staircase=st, edge_periods=2, substrate_layers=120,
                             first_terrace_backbond_uvw=(1, 1, 0), termination="bulk",
                             overlayer=None, vacuum_above_A=5.0, lattice_parameter_A=A_SI_A,
                             lattice_parameter_label="ASSUMPTION B2")
    step = s.metadata["steps"][0]
    h = step["measured_height_A"]                               # signed, to minus from
    assert np.sign(h) == np.sign(layers[1] - layers[0])
    born = float(np.angle(born_ratio(s, step)))
    sens = sensitivity_rad_per_A(wavelength_A=LAM, theta_in_ext_rad=TH, theta_out_ext_rad=TH)
    want = wrap_to_pi(-sens * h)                                # quantification's signed relation
    opposite = wrap_to_pi(+sens * h)
    assert abs(wrap_to_pi(born - want)) <= TOL
    assert abs(wrap_to_pi(born - opposite)) > 0.1               # a sign error would be seen
    # inversion with the branch from the lattice constraint (h a multiple of a/4)
    cands = height_candidates_A(born, range(-8, 9), wavelength_A=LAM, theta_in_ext_rad=TH,
                                theta_out_ext_rad=TH)
    m = int(np.arange(-8, 9)[np.argmin(np.abs(cands / (A_SI_A / 4) - np.rint(cands / (A_SI_A / 4))))])
    est = height_from_phase(born, branch_index=m, branch_source="lattice constraint (a/4 multiple)",
                            wavelength_A=LAM, theta_in_ext_rad=TH, theta_out_ext_rad=TH, **SIGMAS)
    assert est.h_A == pytest.approx(h, abs=1e-6)
