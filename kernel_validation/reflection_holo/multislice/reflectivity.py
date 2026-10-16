"""Complex specular reflection coefficient r(theta_ext) from the grazing-incidence multislice kernel.

Evidence labels: SECTION_READ, DERIVED_HERE, ASSUMPTION, UNVERIFIED.

Definition of r (DERIVED_HERE). In the vacuum above the surface the y-averaged (G_y = 0 rod) field is
    a_inc [exp(-iK_z (z - z_s)) + r exp(+iK_z (z - z_s))] exp(-i pi lambda q^2 x),
K_z = K sin(theta_ext), q = sin(theta_ext)/lambda; phase origin is the top atomic plane z_s.
exp(-i pi lambda q^2 x) is the paraxial envelope phase, common to incident and specular components.

Specular extraction: r = sum_z w psibar exp(-iK_z (z - z_s)) / sum_z w / (a_inc exp(-i pi lambda q^2 L)),
with a Hann taper w over the steady band (cell.configure_angle).

Integration fixes (INTEGRATION_NOTES.md):
* absorber_profile is called with dx_slice (it already returns i W dx in V*A; no extra scaling);
* absorption flags/model are passed to projected_potential (constants model MISSING -> loud);
* t is band-limited with the same isotropic 2/3 circle as the propagator (propagate.bandlimit);
* the incident wave is band-limited to that circle and renormalised before propagation, so free
  propagation is exactly unitary; exit_wave refuses to run if the specular rod frequency lies
  outside the band (the Bragg component of V would be deleted).

Frozen phonons: average |psi|^2 (Kirkland rule, UNVERIFIED in this card set). Each configuration
gives r_c; we return <r_c> (coherent mean, UNVERIFIED interpretation) and meta['R_incoherent'] = <|r_c|^2>.
ASSUMPTIONS: only y,z displacements; n_distinct displaced periods cycled along x; DW off with phonons.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np

from ..constants import wavelength, interaction_constant
from ..geometry import Surface
from .cell import EdgeOnCell, configure_angle, flat_surface_cell, BANDWIDTH
from .illumination import incident_wave, plateau_amplitude, z_axis, end_face_fraction
from .potential import absorber_profile, frozen_phonon_displacements, projected_potential, transmission_function
from .propagate import bandlimit, flux, fresnel_propagator, multislice

ABSORBER_STRENGTH_V = 10.0      # ASSUMPTION: peak imaginary potential of the bulk-side absorber (V); cos2 graded


@dataclass
class RockingCurve:
    theta_ext: np.ndarray
    r: np.ndarray
    meta: dict = field(default_factory=dict)


def _absorber_slice(cell: EdgeOnCell, strength_V: float) -> np.ndarray:
    """i W(z) dx in V*A for one slice of thickness cell.dx (absorber_profile contract)."""
    return absorber_profile(cell.grid, cell.meta["absorber_top"], strength_V, "cos2", dx_slice=cell.dx)


def period_transmissions(cell: EdgeOnCell, E_eV: float, absorber: bool = True, absorption: bool = True,
                         rng=None, n_distinct: int = 1, bandlimit_t: bool = True,
                         absorber_strength_V: float = ABSORBER_STRENGTH_V,
                         absorption_model: dict | None = None, accept_assumptions: bool | None = None) -> list:
    """Transmission functions for one x period (n_sub slices); n_distinct sets if rng is given.

    absorption_model / accept_assumptions default to the values stored in cell.meta.
    """
    sigma = interaction_constant(E_eV)
    B = cell.meta["dw_B"]
    dwB = 0.0 if rng is not None else B
    model = cell.meta.get("absorption_model") if absorption_model is None else absorption_model
    acc = cell.meta.get("accept_assumptions", False) if accept_assumptions is None else accept_assumptions
    ab = _absorber_slice(cell, absorber_strength_V) if absorber else 0.0
    sets = []
    for _ in range(n_distinct if rng is not None else 1):
        ts = []
        for at, Z in zip(cell.atoms_per_slice, cell.Z_per_slice):
            at = at.copy()
            if rng is not None:
                u = np.asarray(frozen_phonon_displacements(len(at), B, rng))
                at = at + u[:, 1:3]
            V = projected_potential(at, Z, cell.grid, dwB, cell.dx, absorption=absorption,
                                    absorption_model=model, accept_assumptions=acc)
            V = V + ab
            t = transmission_function(V, sigma)
            ts.append(bandlimit(t, cell.grid, BANDWIDTH) if bandlimit_t else t)
        sets.append(ts)
    return sets


def exit_wave(cell: EdgeOnCell, E_eV: float, theta_ext: float, sets: list, length_x=None,
              require_rod_in_band: bool = True):
    """Run the kernel for one angle. Returns (exit_wave, psi0, angle_config); stores config in cell.meta."""
    ang = configure_angle(cell, E_eV, theta_ext, length_x)
    if require_rod_in_band and not ang["rod_in_band"]:
        raise ValueError(f"specular rod q = {ang['q_rod']:.3f}/A outside the 2/3 bandwidth "
                         f"{ang['q_limit']:.3f}/A of the grid (dy={cell.grid.dy:.3f}, dz={cell.grid.dz}); "
                         "the Bragg component of V would be deleted. Reduce dy/dz.")
    lam = wavelength(E_eV)
    psi0 = incident_wave(cell.grid, theta_ext, lam, cell.z_surface, ang["window"], cell.meta["softness"])
    psi0 = bandlimit(psi0, cell.grid, BANDWIDTH)
    psi0 = psi0 / np.sqrt(flux(psi0, cell.grid))
    ang["a_inc"] = plateau_amplitude(psi0, cell.grid, ang["window"])
    ang["end_face_fraction_x0"] = end_face_fraction(psi0, cell.grid, cell.z_surface)
    cell.meta["angle"] = ang
    cell.n_slices = ang["n_slices"]
    P = fresnel_propagator(cell.grid, cell.dx, lam, bandwidth=BANDWIDTH)

    def gen():
        for p in range(ang["n_periods"]):
            for t in sets[p % len(sets)]:
                yield t
    return multislice(psi0, gen(), P), psi0, ang


def specular_amplitude(exit_wave, cell: EdgeOnCell, theta_ext, lam) -> complex:
    """Complex r by windowed Fourier selection at +q in the steady vacuum band."""
    ang = cell.meta["angle"]
    if abs(ang["theta"] - theta_ext) > 1e-12:
        raise ValueError("cell.meta['angle'] was configured for a different theta")
    z = z_axis(cell.grid)
    zlo, zhi = ang["band"]
    w = np.zeros_like(z)
    m = (z > zlo) & (z < zhi)
    w[m] = np.sin(np.pi * (z[m] - zlo) / (zhi - zlo)) ** 2
    prof = np.asarray(exit_wave).mean(axis=1)
    K = 2 * np.pi / lam
    c = np.sum(w * prof * np.exp(-1j * K * np.sin(theta_ext) * (z - cell.z_surface))) / np.sum(w)
    q = np.sin(theta_ext) / lam
    L = ang["n_slices"] * cell.dx
    return complex(c / (ang["a_inc"] * np.exp(-1j * np.pi * lam * q * q * L)))


def rocking_curve(surface: Surface, E_eV: float, thetas, n_phonon: int = 1, absorber: bool = True,
                  absorption: bool = True, n_distinct: int = 8, seed: int = 0,
                  absorption_model: dict | None = None, accept_assumptions: bool = False,
                  **cell_kw) -> RockingCurve:
    """Kernel rocking curve. absorption=True needs an explicit absorption_model (loud otherwise)."""
    thetas = np.asarray(thetas, float)
    t0 = time.perf_counter()
    cell = flat_surface_cell(surface, E_eV, float(thetas.min()), thetas_for_vacuum=thetas,
                             absorption=absorption, absorption_model=absorption_model,
                             accept_assumptions=accept_assumptions, **cell_kw)
    lam = wavelength(E_eV)
    rng = np.random.default_rng(seed)
    configs = [period_transmissions(cell, E_eV, absorber, absorption)] if n_phonon <= 1 else \
        [period_transmissions(cell, E_eV, absorber, absorption, rng, n_distinct) for _ in range(n_phonon)]
    t_setup = time.perf_counter() - t0
    r = np.zeros(len(thetas), complex)
    Rinc = np.zeros(len(thetas))
    per_angle, angs = [], []
    for i, th in enumerate(thetas):
        ta = time.perf_counter()
        rc = []
        for sets in configs:
            ew, _, ang = exit_wave(cell, E_eV, th, sets, cell_kw.get("length_x"))
            rc.append(specular_amplitude(ew, cell, th, lam))
        rc = np.array(rc)
        r[i] = rc.mean()
        Rinc[i] = np.mean(np.abs(rc) ** 2)
        angs.append(dict(ang))
        per_angle.append(time.perf_counter() - ta)
    meta = {"R_incoherent": Rinc, "t_setup_s": t_setup, "t_per_angle_s": np.array(per_angle),
            "angles": angs, "grid": (cell.grid.ny, cell.grid.nz, cell.grid.dy, cell.grid.dz),
            "dx": cell.dx, "vacuum": cell.meta["vacuum"], "depth": cell.meta["depth_grid"],
            "V0_meas": cell.meta["bulk"]["V0"], "W0_meas": cell.meta["bulk"]["W0"],
            "n_phonon": n_phonon, "absorber": absorber, "absorption": absorption}
    return RockingCurve(thetas, r, meta)


def peak_table(rc: RockingCurve) -> dict:
    """Position of max |r|^2 and FWHM (linear interpolation; nan if crossings are outside the scan)."""
    R = np.abs(rc.r) ** 2
    th = rc.theta_ext
    i = int(np.argmax(R))
    half = R[i] / 2

    def cross(rng_):
        for j in rng_:
            a, b = j, j + (1 if rng_.step > 0 else -1)
            if 0 <= b < len(R) and (R[a] - half) * (R[b] - half) <= 0 and R[a] != R[b]:
                return th[a] + (half - R[a]) * (th[b] - th[a]) / (R[b] - R[a])
        return np.nan
    left = cross(range(i, 0, -1))
    right = cross(range(i, len(R) - 1, 1))
    return {"theta_peak": float(th[i]), "R_peak": float(R[i]), "fwhm": float(right - left),
            "arg_peak": float(np.angle(rc.r[i]))}


# ---------------------------------------------------------------------------------------------------
# Spectral-ratio extraction (added 2026-10-16, orchestrator; DERIVED_HERE)
# ---------------------------------------------------------------------------------------------------
# The windowed incident wave contains a spread of K_z (angular width ~ lambda / window height, ~0.3 mrad
# for the default 83 A window, comparable to the Darwin width of Si(001) (008)). The band method above
# therefore returns the rocking curve convolved with the beam's angular spectrum. In the paraxial
# beam-perpendicular scheme each K_z component of the G_y = 0 rod scatters independently from the
# zero-order (x-averaged) structure, with the same transverse energy K_z^2/2K on reflection. Hence
#     r(K_z) = R(K_z) / I(K_z) * exp(+i K_z^2 L / 2K),
#     I(K_z) = sum_z psi_in(z) exp(+i K_z (z - z_s)),   R(K_z) = sum_{z > z_s + margin} psi_exit(z) exp(-i K_z (z - z_s)),
# for every K_z carried by the beam, from ONE run. Validity: the whole incident beam has struck the
# surface before the exit plane (residual down-going amplitude small) and the reflected beam lies in the
# vacuum band at the exit plane (no wrap). Both are measured and returned.

def specular_spectrum(exit_wave, psi0, cell: EdgeOnCell, lam: float, thetas, z_margin: float = 5.0) -> dict:
    """r(theta) for all theta in the incident beam's angular spectrum, from one kernel run.

    Returns dict(theta, r, weight, residual_down) where weight = |I(K_z)| / max|I| over the requested
    thetas and residual_down = |D(K_z)| / |I(K_z)| is the down-going amplitude left at the exit plane.
    """
    th = np.atleast_1d(np.asarray(thetas, float))
    K = 2 * np.pi / lam
    kz = K * np.sin(th)
    z = z_axis(cell.grid)
    zs = cell.z_surface
    pe = np.asarray(exit_wave).mean(axis=1)
    pi = np.asarray(psi0).mean(axis=1)
    vac = z > zs + z_margin
    ph_up = np.exp(-1j * np.outer(kz, z[vac] - zs))
    ph_dn = np.exp(+1j * np.outer(kz, z[vac] - zs))
    R_k = ph_up @ pe[vac]
    D_k = ph_dn @ pe[vac]
    I_k = np.exp(+1j * np.outer(kz, z - zs)) @ pi
    L = cell.meta["angle"]["n_slices"] * cell.dx
    r = R_k / I_k * np.exp(1j * kz ** 2 * L / (2 * K))
    w = np.abs(I_k) / np.abs(I_k).max()
    return {"theta": th, "r": r, "weight": w, "residual_down": np.abs(D_k) / np.abs(I_k)}


def rocking_curve_spectral(surface: Surface, E_eV: float, thetas, centres=None, min_weight: float = 0.5,
                           n_phonon: int = 1, absorber: bool = True, absorption: bool = True, seed: int = 0,
                           n_distinct: int = 8, absorption_model: dict | None = None,
                           accept_assumptions: bool = False, sets_override=None, **cell_kw) -> RockingCurve:
    """Kernel rocking curve by spectral-ratio extraction (beam-spectrum deconvolved).

    Runs the kernel at a few centre angles; each requested theta takes r from the run whose beam
    weight is largest there, and must reach min_weight. sets_override replaces the transmission
    functions (used by the like-for-like 1D test with an x,y-averaged potential).
    """
    thetas = np.asarray(thetas, float)
    lam = wavelength(E_eV)
    cell = flat_surface_cell(surface, E_eV, float(thetas.min()), thetas_for_vacuum=thetas,
                             absorption=absorption, absorption_model=absorption_model,
                             accept_assumptions=accept_assumptions, **cell_kw)
    if sets_override is not None:
        configs = [sets_override]
    else:
        rng = np.random.default_rng(seed)
        configs = [period_transmissions(cell, E_eV, absorber, absorption)] if n_phonon <= 1 else \
            [period_transmissions(cell, E_eV, absorber, absorption, rng, n_distinct) for _ in range(n_phonon)]
    if centres is None:
        # beam angular spectrum width estimate: lambda / window height (first-zero scale); half of it as spacing
        ang0 = configure_angle(cell, E_eV, float(np.median(thetas)), cell_kw.get("length_x"))
        dth = 0.5 * lam / ang0["Hw"]
        n_c = int(np.ceil((thetas.max() - thetas.min()) / dth)) + 1
        centres = np.linspace(thetas.min(), thetas.max(), max(n_c, 1))
    best_w = np.zeros(len(thetas)); r = np.zeros(len(thetas), complex)
    res_dn = np.zeros(len(thetas)); Rinc = np.zeros(len(thetas))
    t0 = time.perf_counter()
    for c in centres:
        rc_list = []
        for sets in configs:
            ew, psi0, _ = exit_wave(cell, E_eV, float(c), sets, cell_kw.get("length_x"))
            rc_list.append(specular_spectrum(ew, psi0, cell, lam, thetas))
        w = rc_list[0]["weight"]
        rr = np.mean([d["r"] for d in rc_list], axis=0)
        upd = w > best_w
        r[upd] = rr[upd]; best_w[upd] = w[upd]
        res_dn[upd] = rc_list[0]["residual_down"][upd]
        Rinc[upd] = np.mean([np.abs(d["r"]) ** 2 for d in rc_list], axis=0)[upd]
    if np.any(best_w < min_weight):
        bad = thetas[best_w < min_weight]
        raise ValueError(f"beam spectral weight < {min_weight} at {len(bad)} angles (e.g. {bad[0]*1e3:.3f} mrad); add centres")
    meta = {"method": "spectral", "centres": np.asarray(centres), "weight": best_w, "residual_down": res_dn,
            "R_incoherent": Rinc, "t_total_s": time.perf_counter() - t0, "n_runs": len(centres) * len(configs),
            "V0_meas": cell.meta["bulk"]["V0"], "dx": cell.dx, "grid": (cell.grid.ny, cell.grid.nz, cell.grid.dy, cell.grid.dz)}
    return RockingCurve(thetas, r, meta), cell
