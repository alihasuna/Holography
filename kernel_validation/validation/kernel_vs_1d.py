"""Like-for-like validation of the grazing-incidence multislice kernel against the 1D one-beam solver.

Both codes receive the IDENTICAL laterally (x, y) averaged complex potential Vbar(z) + iW(z), taken from
the kernel's own transmission functions (absorber included). For an x-independent potential each K_z
component of the G_y = 0 rod scatters independently in the paraxial beam-perpendicular scheme, with the
stationary equation  phi'' + (K_z^2 + 2 K sigma V(z)) phi = 0,  which is the 1D problem solved by
reflectivity1d.reflect_1d (uconv = 2 K sigma, checked). Differences are therefore numerical only.

Findings recorded 2026-10-16 (orchestrator, executed in this repository):
* Slice thickness: halving dx (1.92 -> 0.96 A) changes the result by < 1e-4 (not the error source).
* Spectral interpolation: evaluating at exact grid modes K_z,n = 2 pi n / L_z gives the same error.
* 1D discretisation: the 1D answer converges with slab thickness (Fourier up-sampling to 0.01 A).
* The kernel error is set by the isotropic 2/3 band limit min(1/2dy, 1/2dz): doubling it (dy, dz halved)
  halves the complex error |r_kernel - r_1D| (median 0.021 -> 0.009 for Si(001) (008), 200 keV).
  Halving dz alone does not raise the limit when dy is the coarser sampling.
* The averaged potential itself depends on the band limit at the ~0.02 level in r; quantitative work
  needs a per-configuration convergence check (recommended start: dy ~ 0.075 A, dz ~ 0.04 A).
Labels: DERIVED_HERE (method), REPRODUCED (numbers, by running this module).
"""
from __future__ import annotations

import numpy as np

from reflection_holo.constants import interaction_constant, wavelength
from reflection_holo import reflectivity1d as R1
from reflection_holo.multislice import cell as CL
from reflection_holo.multislice import reflectivity as RF
from reflection_holo.multislice.illumination import incident_wave, z_axis
from reflection_holo.multislice.propagate import bandlimit, flux, fresnel_propagator, multislice

TEST_DAMPING = 0.05   # W = 0.05 * Re V (test-only; suppresses termination fringes; not a physics claim)


def averaged_potential(cell, E_eV: float, damping: float = TEST_DAMPING) -> np.ndarray:
    """Vbar(z) + iW(z) in V from the kernel's own transmission functions (absorber on, absorption off)."""
    sig = interaction_constant(E_eV)
    sets = RF.period_transmissions(cell, E_eV, True, False)
    Vp = np.mean([(np.log(t) / (1j * sig)).mean(axis=1) for t in sets[0]], axis=0)
    V = Vp / cell.dx
    return V + 1j * damping * np.clip(V.real, 0, None)


def kernel_spectral_uniform(cell, E_eV: float, Vz: np.ndarray, centres, thetas) -> np.ndarray:
    """Kernel run on an x,y-uniform potential Vz(z); spectral-ratio extraction; returns r(thetas)."""
    lam = wavelength(E_eV); sig = interaction_constant(E_eV)
    t = np.exp(1j * sig * Vz * cell.dx)[:, None] * np.ones((1, cell.grid.ny))
    P = fresnel_propagator(cell.grid, cell.dx, lam, bandwidth=CL.BANDWIDTH)
    best = np.zeros(len(thetas)); r = np.zeros(len(thetas), complex); resid = np.zeros(len(thetas))
    for c in centres:
        ang = CL.configure_angle(cell, E_eV, float(c), None)
        psi0 = bandlimit(incident_wave(cell.grid, float(c), lam, cell.z_surface, ang["window"],
                                       cell.meta["softness"]), cell.grid, CL.BANDWIDTH)
        psi0 = psi0 / np.sqrt(flux(psi0, cell.grid))
        ew = multislice(psi0, (t for _ in range(ang["n_slices"])), P)
        cell.meta["angle"] = ang
        d = RF.specular_spectrum(ew, psi0, cell, lam, thetas)
        u = d["weight"] > best
        r[u] = d["r"][u]; best[u] = d["weight"][u]; resid[u] = d["residual_down"][u]
    return r, best, resid


def fourier_upsample(v: np.ndarray, m: int) -> np.ndarray:
    n = len(v); F = np.fft.fft(v); Fp = np.zeros(n * m, complex); h = n // 2
    Fp[:h] = F[:h]; Fp[-h:] = F[-h:]
    return np.fft.ifft(Fp) * m


def compare(surface, E_eV: float, thetas, centres, dy: float, dz: float, slab_1d: float = 0.01) -> dict:
    """Kernel vs converged 1D on the same averaged potential, at sampling (dy, dz)."""
    c = CL.flat_surface_cell(surface, E_eV, float(np.min(thetas)), thetas_for_vacuum=np.asarray(thetas),
                             absorption=False, dy=dy, dz=dz)
    Vz = averaged_potential(c, E_eV)
    rk, w, resid = kernel_spectral_uniform(c, E_eV, Vz, centres, thetas)
    z = z_axis(c.grid); m = max(1, int(round(c.grid.dz / slab_1d)))
    Vf = fourier_upsample(Vz, m) if m > 1 else Vz
    zf = z[0] + np.arange(len(Vf)) * (c.grid.dz / m)
    r1 = R1.reflect_1d(np.asarray(thetas), E_eV, Vf, zf, z_ref=c.z_surface, V_sub=Vf[0])
    band = CL.BANDWIDTH * min(1 / (2 * c.grid.dy), 1 / (2 * c.grid.dz))
    return {"r_kernel": rk, "r_1d": r1, "weight": w, "residual_down": resid, "band_limit": band,
            "abs_dr": np.abs(rk - r1), "dR": np.abs(np.abs(rk) ** 2 - np.abs(r1) ** 2),
            "grid": (c.grid.ny, c.grid.nz, c.grid.dy, c.grid.dz)}


if __name__ == "__main__":
    from reflection_holo.geometry import Surface
    E = 200e3
    th = np.linspace(0.01580, 0.01660, 17)
    cen = np.linspace(th.min(), th.max(), 7)
    for dy, dz in [(0.15, 0.08), (0.075, 0.04)]:
        out = compare(Surface((0, 0, 1), (1, 1, 0)), E, th, cen, dy, dz)
        print(f"dy={out['grid'][2]:.4f} dz={out['grid'][3]:.3f} band {out['band_limit']:.2f}/A: "
              f"|dr| max {out['abs_dr'].max():.5f} median {np.median(out['abs_dr']):.5f}; "
              f"dR max {out['dR'].max():.5f}; residual_down max {out['residual_down'].max():.1e}")
    # Expected (2026-10-16): default |dr| max 0.0357 median 0.0206, dR max 0.0243;
    #                        refined |dr| max 0.0201 median 0.0094, dR max 0.0098; residual_down ~1e-4
