"""Edge-on supercell for a flat Si(001) or Si(111) surface (2D case: one surface cell in y).

Evidence labels: SECTION_READ, DERIVED_HERE, ASSUMPTION, UNVERIFIED.

Coordinates (CONTRACT): x = beam axis, y = in-surface transverse, z = outward normal (vacuum at +z).
The z grid runs from bottom to top as follows:
* a graded imaginary absorber (bulk side) from z = 0 to z = absorber_thickness;
* crystal continuing from z = 2 A up to the surface plane z_surface, with the bulk-terminated top
  atomic plane at z_surface;
* vacuum of height `vacuum` above the surface.

Criteria (derivations in NOTES_C.md; all DERIVED_HERE from the labelled premises):

(1) Penetration depth. Premise: K_z,int^2 = K_z,vac^2 + 2 m e gamma V/hbar^2 (repo conventions),
    with 2 m e gamma/hbar^2 = 2 K sigma (algebraic identity, tested in test_geometry via dK^2).
    Complex mean potential V0 + iW0 gives Lambda_abs = K_z,int / (2 K sigma W0). With W0 = 0
    the depth is set by Bragg extinction, Lambda_ext = K_z,int / (2 K sigma |V_G|) for the rod
    coefficient at G = 2 K_z,int. D = n_depth * Lambda, clipped to [depth_min, depth_max].
(2) Cell length (steady state): L = x_b + D/tan(th_int), x_b = (gap + H_w)/tan(th_e).
(3) Window height: H_w = D T + 2s + w_extract, T = tan(th_e)/tan(th_int).
(4) Vacuum height: H_vac >= max(gap + H_w, L tan th_e) + 3 sqrt(lambda L) + guard.
    Rise term reproduces calculator T19 (4.4604 A for 198.248 A at 22.495 mrad).

Bandwidth record (integration fix): configure_angle stores the specular rod frequency
q_rod = 2 K_z,int/(2 pi) (cycles/A) and the isotropic 2/3 k_max limit of the grid (the same circle
used by projected_potential and fresnel_propagator). reflectivity.exit_wave refuses to run when the
rod lies outside the band, because the Bragg Fourier component of V would then be deleted.

Slicing: the [110] beam period is a/sqrt2 = 3.8402 A for both surfaces (calculator section 9);
default 2 sub-slices of 1.920 A; 0.960 A for convergence (calculator 'commensurate alternatives').
"""
from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field

import numpy as np

from ..constants import A_SI, B_SI_300K, wavelength, interaction_constant
from ..geometry import Surface, frame, refraction
from .potential import Grid, projected_potential

Z_SI = 14
DIMER_BOND_A = 2.35   # ASSUMPTION / UNVERIFIED: Si(001)2x1 dimer separation. No card gives it.
BANDWIDTH = 2.0 / 3.0


@dataclass
class EdgeOnCell:
    grid: Grid
    dx: float
    n_slices: int
    z_surface: float
    atoms_per_slice: list
    Z_per_slice: list
    meta: dict = field(default_factory=dict)


def _good_fft_size(n: int) -> int:
    m = max(int(n), 8)
    while True:
        r = m
        for p in (2, 3, 5):
            while r % p == 0:
                r //= p
        if r == 1:
            return m
        m += 1


def lattice_period(u: np.ndarray, a: float) -> float:
    """Shortest fcc translation (a/2)(i,j,k), i+j+k even, parallel to unit vector u (A). DERIVED_HERE."""
    u = np.asarray(u, float) / np.linalg.norm(u)
    best = None
    for i, j, k in itertools.product(range(-8, 9), repeat=3):
        if (i + j + k) % 2 or (i == j == k == 0):
            continue
        v = 0.5 * a * np.array([i, j, k], float)
        n = np.linalg.norm(v)
        if np.linalg.norm(np.cross(v, u)) < 1e-9 * n and v @ u > 0:
            best = n if best is None else min(best, n)
    if best is None:
        raise ValueError(f"no lattice period along {u}")
    return best


def diamond_atoms_slab(surface: Surface, a: float):
    """All atoms of the orthorhombic period box (px, py, pz) in slab coordinates (x_beam, y, z_normal).

    The box edges are lattice translations, so the box is a supercell; its atom count must equal
    8 V/a^3 (8-atom diamond cell, conventions 'Structure factor'; calculator section 2).

    Reduction into the box is done in FRACTIONAL box coordinates f = s/per, rounded to 1e-6 and then
    taken mod 1, so that a coordinate within rounding of an edge maps to 0 and not to a duplicate at
    the far edge (integration fix: the previous Cartesian rounding produced 9 instead of 4 and 18
    instead of 12 atoms). DERIVED_HERE.
    """
    F = np.asarray(frame(surface), float)
    per = np.array([lattice_period(F[i], a) for i in range(3)])
    N = int(np.ceil(np.linalg.norm(per) / a)) + 2
    base = np.array([[0, 0, 0], [0, .5, .5], [.5, 0, .5], [.5, .5, 0]], float)
    basis = np.vstack([base, base + 0.25])
    r = np.arange(-N, N + 1)
    cells = np.array(np.meshgrid(r, r, r, indexing="ij")).reshape(3, -1).T
    pos = ((cells[:, None, :] + basis[None]).reshape(-1, 3)) * a
    s = pos @ F.T
    f = np.mod(np.round(np.mod(s / per, 1.0), 6), 1.0)
    f = np.unique(f, axis=0)
    s = f * per
    expected = int(round(8 * np.prod(per) / a ** 3))
    if len(s) != expected:
        raise RuntimeError(f"period box has {len(s)} atoms, expected {expected}")
    return s, per


def top_plane(atoms: np.ndarray, pz: float) -> float:
    """Bulk-terminated top plane: the atomic plane with the largest gap above it (cyclic in pz).

    Returns the actual z of the atoms in that plane (not the 3-decimal rounded label), so that the
    termination shift is exact. For Si(111) this selects the upper atom of a bilayer (gaps
    0.7839/2.3516 A, calculator 2b). For Si(001) all gaps are a/4 and the first plane is taken.
    """
    z = atoms[:, 2]
    zs = np.unique(np.round(z, 3))
    gaps = np.diff(np.append(zs, zs[0] + pz))
    i = int(np.argmax(np.round(gaps, 3)))
    sel = np.abs(z - zs[i]) < 2e-3
    return float(np.mean(z[sel]))


def _unit_with_termination(surface: Surface, a: float, reconstruction):
    atoms, per = diamond_atoms_slab(surface, a)
    px, py, pz = per
    zt = top_plane(atoms, pz)
    tol = 1e-6
    zrel = -(np.mod(zt - atoms[:, 2] + tol, pz) - tol)
    zrel[np.abs(zrel) < tol] = 0.0
    unit = np.column_stack([atoms[:, 0], atoms[:, 1], zrel])
    disp = np.zeros_like(unit)
    if reconstruction == "2x1":
        if tuple(surface.hkl) != (0, 0, 1):
            raise ValueError("2x1 dimer option only for Si(001)")
        unit = np.vstack([unit, unit + [0, py, 0]])
        py = 2 * py
        disp = np.zeros_like(unit)
        top = np.where(np.abs(unit[:, 2]) < 1e-4)[0]
        top = top[np.argsort(unit[top, 1])]
        if len(top) != 2:
            raise RuntimeError("expected 2 top atoms in the 2x1 cell")
        sep = unit[top[1], 1] - unit[top[0], 1]
        d = 0.5 * (sep - DIMER_BOND_A)          # ASSUMPTION: symmetric dimer, no buckling, no z relaxation
        disp[top[0], 1] = +d
        disp[top[1], 1] = -d
    elif reconstruction not in (None, "none"):
        raise ValueError(f"unknown reconstruction {reconstruction}")
    return unit, disp, np.array([px, py, pz])


def bulk_averages(unit, per, n_sub, dy, dz, dw_B, E_eV, absorption=True, absorption_model=None,
                  accept_assumptions=False) -> dict:
    """Mean inner potential V0, mean absorptive W0 (V) and rod Fourier coefficients of the bulk.

    The bulk potential is projected on a one-period (y, z) grid and averaged over x:
    V(y, z) = sum_j Vproj_j / px. The Fourier construction is periodic over the grid (pz exactly),
    so NO z images are added (integration fix: the previous +-pz images tripled V0). The
    laterally averaged V(z) gives V_m = <V(z) exp(-2 pi i m z / pz)> at G = 2 pi m / pz.
    DERIVED_HERE. absorption flags are passed through to projected_potential (loud path).
    """
    px, py, pz = per
    ny = max(4, int(round(py / dy)))
    nz = max(8, int(round(pz / dz)))
    g = Grid(ny, nz, py / ny, pz / nz, 0.0, -pz)
    dx = px / n_sub
    Vtot = np.zeros((nz, ny), complex)
    for j in range(n_sub):
        m = (unit[:, 0] >= j * dx) & (unit[:, 0] < (j + 1) * dx)
        yz = unit[m][:, 1:3]
        Vtot += projected_potential(yz, np.full(len(yz), Z_SI), g, dw_B, dx, absorption=absorption,
                                    absorption_model=absorption_model,
                                    accept_assumptions=accept_assumptions)
    V = Vtot / px
    zz = g.z0 + g.dz * np.arange(nz)
    vbar = V.mean(axis=1)
    mmax = nz // 2
    coeff = np.array([np.mean(vbar * np.exp(-2j * np.pi * m * zz / pz)) for m in range(mmax)])
    return {"V0": float(V.real.mean()), "W0": float(V.imag.mean()), "coeff": coeff, "pz": float(pz)}


def penetration(theta_ext, E_eV, bulk, n_depth, depth_min, depth_max, absorption=True) -> dict:
    """Penetration depth and crystal depth D for one angle (criterion (1), DERIVED_HERE)."""
    lam = wavelength(E_eV)
    K = 2 * np.pi / lam
    sig = interaction_constant(E_eV)
    th_int = refraction(theta_ext, E_eV, bulk["V0"])
    Kz = K * np.sin(th_int)
    W0 = bulk["W0"] if absorption else 0.0
    lam_abs = math.inf if W0 <= 0 else Kz / (2 * K * sig * W0)
    m = int(round(2 * Kz / (2 * np.pi) * bulk["pz"]))
    VG = abs(bulk["coeff"][m]) if 0 < m < len(bulk["coeff"]) else 0.0
    lam_ext = math.inf if VG == 0 else Kz / (2 * K * sig * VG)
    lam_use = lam_abs if math.isfinite(lam_abs) else lam_ext
    D = depth_max if not math.isfinite(lam_use) else float(np.clip(n_depth * lam_use, depth_min, depth_max))
    return {"theta_int": th_int, "Kz_int": Kz, "Lambda_abs": lam_abs, "Lambda_ext": lam_ext,
            "rod_m": m, "V_G": VG, "D": D}


def length_and_window(theta_ext, theta_int, D, gap, softness, w_extract):
    """Criteria (2)-(3): returns H_w, L and D*T (A)."""
    T = np.tan(theta_ext) / np.tan(theta_int)
    Hw = D * T + 2 * softness + w_extract
    L = (gap + Hw) / np.tan(theta_ext) + D / np.tan(theta_int)
    return Hw, L, D * T


def vacuum_criterion(L, theta_ext, Hw, gap, lam, guard=10.0) -> float:
    """Criterion (4): H_vac = max(gap + H_w, L tan th) + 3 sqrt(lambda L) + guard (A)."""
    return max(gap + Hw, L * np.tan(theta_ext)) + 3 * np.sqrt(lam * L) + guard


def configure_angle(cell: EdgeOnCell, E_eV: float, theta_ext: float, length_x=None) -> dict:
    """Per-angle window, length, slice count, extraction band and bandwidth record.

    Raises ValueError if the vacuum is too low or the extraction band is empty.
    """
    M = cell.meta
    lam = wavelength(E_eV)
    pen = penetration(theta_ext, E_eV, M["bulk"], M["n_depth"], M["depth_min"], M["depth_grid"],
                      M["absorption"])
    D = min(pen["D"], M["depth_grid"])
    g, s = M["gap"], M["softness"]
    Hw, L, DT = length_and_window(theta_ext, pen["theta_int"], D, g, s, M["w_extract"])
    if length_x is not None:
        L = float(length_x)
    capped = L > M["length_max"]
    L = min(L, M["length_max"])
    px = M["periods"][0]
    n_per = int(math.ceil(L / px))
    L_act = n_per * px
    te, ti = np.tan(theta_ext), np.tan(pen["theta_int"])
    x_a, x_b = g / te, (g + Hw) / te
    h_hi = (L_act - x_a - D / ti) * te - s
    h_lo = max((L_act - x_b) * te + s, g)
    if h_hi - h_lo < 5.0:
        raise ValueError(f"extraction band too narrow ({h_lo:.1f}..{h_hi:.1f} A); increase w_extract/length")
    need = vacuum_criterion(L_act, theta_ext, Hw, g, lam, M["guard"])
    if need > M["vacuum"] + 1e-9:
        raise ValueError(f"vacuum {M['vacuum']:.1f} A < criterion {need:.1f} A at theta={theta_ext*1e3:.3f} mrad")
    q_rod = 2.0 * pen["Kz_int"] / (2 * np.pi)
    q_lim = BANDWIDTH * cell.grid.kmax
    zs = cell.z_surface
    return {"theta": float(theta_ext), "window": (zs + g, zs + g + Hw), "Hw": Hw, "L": L_act,
            "n_periods": n_per, "n_slices": n_per * M["n_sub"], "band": (zs + h_lo, zs + h_hi),
            "DT": DT, "D": D, "length_capped": capped, "vacuum_needed": need,
            "q_rod": q_rod, "q_limit": q_lim, "rod_in_band": bool(q_rod < q_lim), **pen}


def flat_surface_cell(surface: Surface, E_eV: float, theta_ext: float, length_x: float | None = None,
                      depth: float | None = None, vacuum: float | None = None, dy: float = 0.15,
                      dz: float = 0.08, dx: float | None = None, reconstruction: str | None = None,
                      thetas_for_vacuum=None, gap: float = 3.0, softness: float = 3.0,
                      w_extract: float = 20.0, absorber_thickness: float = 40.0, n_depth: float = 4.0,
                      depth_min: float | None = None, depth_max: float = 300.0,
                      length_max: float = 3.0e4, guard: float = 10.0, dw_B: float | None = None,
                      absorption: bool = True, absorption_model: dict | None = None,
                      accept_assumptions: bool = False) -> EdgeOnCell:
    """Build the 2D (one surface cell in y) edge-on cell; criteria recorded in meta['criteria'].

    absorption=True requires an explicit absorption model (constants.ABSORPTION_MODEL is MISSING);
    otherwise MissingProjectInput is raised while computing the bulk averages (loud path).
    Numerical parameters (ASSUMPTION, varied in the convergence protocol): gap = 3 A, softness = 3 A,
    w_extract = 20 A, n_depth = 4; depth_min defaults to 2 pz.
    """
    a = A_SI.value
    dwB = B_SI_300K.value if dw_B is None else dw_B
    unit, disp, per = _unit_with_termination(surface, a, reconstruction)
    px, py, pz = per
    n_sub = max(1, int(round(px / (1.92 if dx is None else dx))))
    dxs = px / n_sub
    bulk = bulk_averages(unit, per, n_sub, dy, min(dz, 0.1), dwB, E_eV, absorption,
                         absorption_model, accept_assumptions)
    dmin = 2 * pz if depth_min is None else depth_min
    thetas = np.atleast_1d(thetas_for_vacuum if thetas_for_vacuum is not None else [theta_ext])
    lam = wavelength(E_eV)
    pens = [penetration(t, E_eV, bulk, n_depth, dmin, depth_max, absorption) for t in thetas]
    D_grid = float(depth) if depth is not None else max(p["D"] for p in pens)
    vac_need = 0.0
    for t, p in zip(thetas, pens):
        Dt = min(p["D"], D_grid)
        Hw, L, _ = length_and_window(t, p["theta_int"], Dt, gap, softness, w_extract)
        L = min(length_x if length_x is not None else L, length_max)
        L = math.ceil(L / px) * px
        vac_need = max(vac_need, vacuum_criterion(L, t, Hw, gap, lam, guard))
    vac = float(vacuum) if vacuum is not None else vac_need
    ny = max(4, int(round(py / dy)))
    z_s = absorber_thickness + D_grid
    nz = _good_fft_size(int(math.ceil((z_s + vac) / dz)) + 1)
    grid = Grid(ny, nz, py / ny, dz, 0.0, 0.0)
    z_min = 2.0
    M_rep = int(math.ceil((z_s - z_min) / pz)) + 1
    atoms_ps, Z_ps = [], []
    for j in range(n_sub):
        m = (unit[:, 0] >= j * dxs) & (unit[:, 0] < (j + 1) * dxs)
        u, d = unit[m], disp[m]
        rows = []
        for k in range(M_rep):
            z = z_s + u[:, 2] - k * pz + (d[:, 2] if k == 0 else 0.0)
            y = np.mod(u[:, 1] + (d[:, 1] if k == 0 else 0.0), py)
            keep = z >= z_min
            rows.append(np.column_stack([y[keep], z[keep]]))
        yz = np.vstack(rows)
        atoms_ps.append(yz)
        Z_ps.append(np.full(len(yz), Z_SI))
    meta = {"surface": (tuple(surface.hkl), tuple(surface.azimuth)), "E_eV": E_eV, "periods": per,
            "n_sub": n_sub, "bulk": bulk, "gap": gap, "softness": softness, "w_extract": w_extract,
            "n_depth": n_depth, "depth_min": dmin, "depth_grid": D_grid, "length_max": length_max,
            "guard": guard, "vacuum": vac, "absorber_top": absorber_thickness, "dw_B": dwB,
            "absorption": absorption, "absorption_model": absorption_model,
            "accept_assumptions": accept_assumptions, "reconstruction": reconstruction,
            "criteria": "see cell.py module docstring criteria (1)-(4) and NOTES_C.md"}
    cell = EdgeOnCell(grid, dxs, 0, z_s, atoms_ps, Z_ps, meta)
    ang = configure_angle(cell, E_eV, theta_ext, length_x)
    cell.meta["angle"] = ang
    cell.n_slices = ang["n_slices"]
    return cell


# Named sampling presets (orchestrator, 2026-10-16; see validation/kernel_vs_1d.py and INTEGRATION_NOTES.md F2).
# The isotropic 2/3 band limit is min(1/2dy, 1/2dz); at FAST it is 2.26/A (set by dy) and the complex
# specular amplitude at Si(001) (008) carries a ~0.02 error relative to the continuum limit. FAST is for
# unit tests only. QUANT halves that error; every result must still carry its own convergence check.
SAMPLING_FAST = {"dy": 0.15, "dz": 0.08}
SAMPLING_QUANT = {"dy": 0.075, "dz": 0.04}
