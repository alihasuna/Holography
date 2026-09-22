"""Mean inner potential of bulk Si implied by the atomic-potential parameterisations shipped with abTEM.

Source-map row SM17, planned test "MIP-of-parameterisation vs sourced V0" (report
docs/agent_reports/D3_abtem_potential_provenance.md, section 7).

Definition used (independent atom model, IAM):

    V0 = (1 / Omega) * integral_cell V(r) d^3r = (1 / Omega) * sum_j integral V_j(r) d^3r

where the sum runs over the atoms of one cell and each per-atom integral extends over all space
(the tails of neighbouring atoms that enter the cell are exactly compensated by the tails that
leave it). Omega = a^3 and the cell holds the 8 atoms of the diamond conventional cell.

The per-atom volume integral is obtained three ways:
  (1) analytic: abTEM's projected scattering factor at k = 0, F_j(0) = integral V_j d^3r [V A^3]
      (abtem/parametrizations/functions/{kirkland,lobato}.py projected_scattering_factor;
      Peng via PengParametrization.scaled_parameters);
  (2) numerical radial quadrature 4 pi integral r^2 V_j(r) dr of abTEM's 3D potential V_j(r);
  (3) f_e(0) / kappa with abTEM's electron scattering factor f_e(0) [A] and
      1 / kappa = 2 pi a0 e [V A^2] (abtem/core/constants.py:7-8).
and V0 is also taken from the grid mean of abTEM's own Potential for the 8-atom cell, both with the
infinite projection (default) and with the finite (real-space quadrature) projection, which truncates
and tapers the potential at the cutoff radius and therefore changes the mean.

Inputs and labels:
  a = 5.4309 A           reflection_holo.constants.A_SI_A, ASSUMPTION B2 (docs/model_assumptions.md)
  12.0 V                 reflection_holo.constants.V0_SI_ASSUMPTION_V, ASSUMPTION B1
  12.53 V                DFT Si endpoint read from Fig. 2c of Schowalter, Kruse and Rosenauer,
                         arXiv:2607.05948v1 (SECTION_READ, recorded in docs/model_assumptions.md B1);
                         used here for comparison only, never adopted.
Nothing is random; no seed is used. abTEM precision is set to float64 for all numbers except the one
line that repeats the grid check in abTEM's default float32.

Run (from the repository root, with abTEM 1.0.10 installed in the venv):
    venv/bin/python tools/provenance_checks/abtem_mip.py
"""
from __future__ import annotations

import warnings

import numpy as np
from scipy import integrate

import abtem
from abtem.core.constants import kappa
from abtem.parametrizations import (
    KirklandParametrization,
    LobatoParametrization,
    PengParametrization,
)
from ase import Atoms

from reflection_holo.constants import A_SI_A, DIAMOND_BASIS, V0_SI_ASSUMPTION_V

REQUIRED_ABTEM_VERSION = "1.0.10"
V0_DFT_SI_V = 12.53  # SECTION_READ (arXiv:2607.05948v1, Fig. 2c); comparison only

PARAMETRISATIONS = {
    "kirkland (kirkland.json)": lambda: KirklandParametrization(),
    "lobato (lobato.json, abTEM default)": lambda: LobatoParametrization(),
    "peng (peng_high.json, class default)": lambda: PengParametrization(),
    "peng (peng_low.json)": lambda: PengParametrization(parameters="peng_low.json"),
}
ABTEM_NAME = {  # string accepted by abtem.Potential(parametrization=...)
    "kirkland (kirkland.json)": "kirkland",
    "lobato (lobato.json, abTEM default)": "lobato",
    "peng (peng_high.json, class default)": "peng",
}


def volume_integral_analytic(par, symbol: str) -> float:
    """integral V d^3r [V A^3] as the k = 0 value of abTEM's projected scattering factor."""
    return float(np.asarray(par.projected_scattering_factor(symbol)(np.array([0.0])))[0])


def volume_integral_radial(par, symbol: str) -> float:
    """4 pi integral_0^inf r^2 V(r) dr [V A^3] by adaptive quadrature of abTEM's 3D potential."""
    v = par.potential(symbol)

    def integrand(r: float) -> float:
        return 4.0 * np.pi * r * r * float(v(np.array([r]))[0])

    edges = [0.0, 1e-3, 1e-2, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 100.0, 400.0]
    return sum(
        integrate.quad(integrand, lo, hi, limit=400, epsabs=0.0, epsrel=1e-11)[0]
        for lo, hi in zip(edges[:-1], edges[1:])
    )


def electron_scattering_factor_at_zero(par, symbol: str) -> float:
    """f_e(k = 0) [A] from abTEM's scattering_factor(symbol)(k^2)."""
    return float(np.asarray(par.scattering_factor(symbol)(np.array([0.0])))[0])


def si_cell(a: float) -> Atoms:
    atoms = Atoms("Si8", scaled_positions=DIAMOND_BASIS, cell=[a, a, a], pbc=True)
    atoms.positions[:, 2] += a / 8.0  # every atomic plane in the middle of an a/4 slice
    atoms.wrap()
    return atoms


def grid_mip(atoms: Atoms, parametrization: str, projection: str, gpts: int = 48) -> float:
    """V0 [V] from the pixel mean of every slice of abTEM's Potential, divided by the cell height."""
    a = atoms.cell[2, 2]
    pot = abtem.Potential(
        atoms,
        gpts=(gpts, gpts),
        slice_thickness=a / 4.0,
        parametrization=parametrization,
        projection=projection,
    ).build(lazy=False)
    arr = np.asarray(pot.array)
    return float(arr.mean(axis=(-2, -1)).sum() / a)


def main() -> None:
    warnings.filterwarnings("ignore")
    if abtem.__version__ != REQUIRED_ABTEM_VERSION:
        raise SystemExit(
            f"abTEM {abtem.__version__} found; these numbers are pinned to {REQUIRED_ABTEM_VERSION}"
        )
    abtem.config.set({"precision": "float64", "dask.lazy": False})

    a = A_SI_A
    omega = a**3
    n_atoms = len(DIAMOND_BASIS)
    print(f"abTEM {abtem.__version__}; precision float64; 1/kappa = 2 pi a0 e = {1 / kappa:.8f} V A^2")
    print(f"Si diamond cell: a = {a} A (ASSUMPTION B2), Omega = {omega:.6f} A^3, {n_atoms} atoms")
    print()
    header = (
        f"{'parameterisation':38s} {'f_e(0) Si [A]':>13s} {'intV Si analytic':>16s} "
        f"{'intV Si radial':>15s} {'rel.diff':>9s} {'intV O':>10s} {'V0 Si [V]':>10s} "
        f"{'-12.0 V':>8s} {'/12.0':>7s} {'-12.53 V':>9s} {'/12.53':>7s}"
    )
    print(header)
    print("-" * len(header))
    results = {}
    for name, make in PARAMETRISATIONS.items():
        par = make()
        fe0 = electron_scattering_factor_at_zero(par, "Si")
        iv = volume_integral_analytic(par, "Si")
        iv_rad = volume_integral_radial(par, "Si")
        iv_fe = fe0 / kappa
        iv_o = volume_integral_analytic(par, "O")
        assert abs(iv_fe / iv - 1.0) < 1e-6, (name, iv_fe, iv)
        v0 = n_atoms * iv / omega
        results[name] = v0
        print(
            f"{name:38s} {fe0:13.6f} {iv:16.6f} {iv_rad:15.6f} {iv_rad / iv - 1:9.1e} "
            f"{iv_o:10.4f} {v0:10.4f} {v0 - V0_SI_ASSUMPTION_V:+8.3f} {v0 / V0_SI_ASSUMPTION_V:7.4f} "
            f"{v0 - V0_DFT_SI_V:+9.3f} {v0 / V0_DFT_SI_V:7.4f}"
        )
    print()
    print("Units: f_e(0) in A; intV = integral V d^3r per atom in V A^3; V0 in V.")
    print("intV O is given for later use (SiO2 overlayer); it is not used for the Si V0.")
    print()
    print("Grid check with abtem.Potential on the 8-atom cell (48 x 48 pixels, 4 slices of a/4):")
    atoms = si_cell(a)
    for name, abtem_name in ABTEM_NAME.items():
        v_inf = grid_mip(atoms, abtem_name, "infinite")
        line = f"  {abtem_name:9s} infinite projection: V0 = {v_inf:.6f} V (analytic {results[name]:.6f} V)"
        if abtem_name != "peng":
            v_fin = grid_mip(atoms, abtem_name, "finite")
            line += f"; finite projection: V0 = {v_fin:.6f} V ({v_fin / results[name] - 1:+.2e} relative)"
        print(line)
    abtem.config.set({"precision": "float32"})
    v32 = grid_mip(atoms, "lobato", "infinite")
    name = "lobato (lobato.json, abTEM default)"
    print(f"  lobato    infinite projection, float32 (abTEM default precision): V0 = {v32:.6f} V "
          f"({v32 / results[name] - 1:+.1e} relative)")
    abtem.config.set({"precision": "float64"})
    # a Debye-Waller smearing multiplies the projected scattering factor by exp(-2 pi^2 sigma^2 k^2),
    # which is 1 at k = 0 (abtem/integrals.py:442-447): the mean is unchanged. 0.1 A is a test value.
    smeared = LobatoParametrization(sigmas={"Si": 0.1})
    pot = abtem.Potential(atoms, gpts=(48, 48), slice_thickness=a / 4.0, parametrization=smeared,
                          projection="infinite").build(lazy=False)
    v_dw = float(np.asarray(pot.array).mean(axis=(-2, -1)).sum() / a)
    print(f"  lobato    infinite projection with sigmas={{'Si': 0.1}} (test value): V0 = {v_dw:.6f} V")


if __name__ == "__main__":
    main()
