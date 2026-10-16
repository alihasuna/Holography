"""T-transmission-limit: compare the grazing-incidence kernel with abTEM in plain transmission.

The kernel runs at normal incidence on a thin Si slab with the beam along [100] and is compared with
abTEM for the same atoms. Run with: python validation/abtem_transmission.py

Both codes implement the multislice step t -> propagate with the paraxial propagator and a 2/3
bandwidth limit. With identical atoms, Kirkland parameterisation [card kirkland_appC, p.12], identical
a/4 slices aligned on the atomic planes, no Debye-Waller smearing and a REAL potential, the Bragg-beam
intensities must agree up to sampling and projection-implementation details.

Integration fix: the kernel potential is requested with absorption=False. The previous call used the
default absorption=True, which resolved constants.ABSORPTION_MODEL (now status MISSING; previously an
unrecognised name) and raised before any comparison was made.

Tolerance (ASSUMPTION; reason in NOTES_D.md section 5): 15 strongest beams,
|I_kernel - I_abtem| <= 0.01 + 0.05 * I_abtem; both total intensities in [0.95, 1 + 1e-6].

Frame mapping: kernel beam = x, arrays (nz, ny); abTEM beam = z, arrays (nX, nY); X = y, Y = z, so
kernel_array = abtem_array.T.
Labels: abTEM's 'kirkland' parametrization assumed to be the same table (UNVERIFIED);
multislice(psi0, slices, propagator) takes transmission functions (CONTRACT).
"""
from __future__ import annotations

import sys

import numpy as np

_FCC = np.array([[0, 0, 0], [0, .5, .5], [.5, 0, .5], [.5, .5, 0]], float)
DIAMOND_BASIS = np.vstack([_FCC, _FCC + 0.25])   # fractional; 8 atoms per cubic cell (conventions)

N_STRONG = 15
TOL_ABS = 0.01
TOL_REL = 0.05


def build_si_slab(a: float, n_cells_beam: int = 10):
    """Si slab, transverse 1x1 conventional cell, n_cells_beam cells along the beam (x).

    Returns (positions (N,3) columns (x_beam, y, z) in A, list of per-slice (y,z) arrays, slice dx).
    Slices are a/4 thick with one {100} plane at the centre (atoms offset by a/8). DERIVED_HERE.
    """
    pos = []
    for c in range(n_cells_beam):
        p = DIAMOND_BASIS * a
        p = p.copy()
        p[:, 0] += c * a
        pos.append(p)
    pos = np.vstack(pos)
    pos[:, 0] += a / 8.0
    dx = a / 4.0
    n_sl = 4 * n_cells_beam
    idx = np.floor(pos[:, 0] / dx).astype(int)
    slices = [pos[idx == j][:, 1:3] % a for j in range(n_sl)]
    return pos, slices, dx


def _with_images(yz: np.ndarray, a: float) -> np.ndarray:
    """Add the 3x3 periodic images of the transverse cell. DERIVED_HERE."""
    out = [yz + np.array([i * a, j * a]) for i in (-1, 0, 1) for j in (-1, 0, 1)]
    return np.vstack(out)


def kernel_exit_wave(a: float, E_eV: float, n_pix: int = 128, n_cells_beam: int = 10):
    """Kernel exit wave at normal incidence through the slab; real potential, dw_B = 0.

    Periodicity is detected (a single atom at y = 0; columns +dy and -dy compared); images are added
    only if the potential does not wrap. DERIVED_HERE.
    """
    from reflection_holo import constants as C
    from reflection_holo.multislice.potential import Grid, projected_potential, transmission_function
    from reflection_holo.multislice.propagate import fresnel_propagator, multislice

    grid = Grid(ny=n_pix, nz=n_pix, dy=a / n_pix, dz=a / n_pix, y0=0.0, z0=0.0)
    lam = float(C.wavelength(E_eV))
    sig = float(C.interaction_constant(E_eV))
    _, slices, dx = build_si_slab(a, n_cells_beam)
    probe = projected_potential(np.array([[0.0, a / 2]]), np.array([14]), grid, 0.0, dx,
                                absorption=False).real
    wraps = abs(probe[:, -1].max() - probe[:, 1].max()) < 1e-3 * abs(probe[:, 1].max())
    ts = []
    for yz in slices[:4]:
        atoms = yz if wraps else _with_images(yz, a)
        Vp = projected_potential(atoms, np.full(len(atoms), 14), grid, 0.0, dx, absorption=False)
        ts.append(transmission_function(np.real(Vp).astype(complex), sig))
    stack = [ts[j % 4] for j in range(len(slices))]
    P = fresnel_propagator(grid, dx, lam, bandwidth=2.0 / 3.0)
    psi0 = np.ones((n_pix, n_pix), complex)
    return np.asarray(multislice(psi0, stack, P))


def abtem_exit_wave(a: float, E_eV: float, n_pix: int = 128, n_cells_beam: int = 10):
    """abTEM exit wave for the same atoms, transposed to the kernel layout (nz, ny).
    Raises ImportError if abTEM or ASE is unavailable. DERIVED_HERE (API: abTEM >= 1.0)."""
    import abtem  # noqa: F401
    from ase import Atoms

    pos, _, _ = build_si_slab(a, n_cells_beam)
    L = n_cells_beam * a
    pos_ab = np.column_stack([pos[:, 1] % a, pos[:, 2] % a, pos[:, 0]])
    atoms = Atoms(symbols=["Si"] * len(pos_ab), positions=pos_ab, cell=[a, a, L], pbc=True)
    pot = abtem.Potential(atoms, gpts=(n_pix, n_pix), slice_thickness=a / 4.0,
                          parametrization="kirkland", projection="infinite")
    wave = abtem.PlaneWave(energy=E_eV)
    ew = wave.multislice(pot)
    if hasattr(ew, "compute"):
        ew = ew.compute()
    arr = np.asarray(ew.array)
    arr = arr.reshape(arr.shape[-2:])
    return arr.T


def spot_intensities(psi: np.ndarray) -> np.ndarray:
    """Bragg-beam intensities |FFT(psi)/N|^2 (one-cell periodic window). DERIVED_HERE."""
    F = np.fft.fft2(psi) / psi.size
    return np.abs(F) ** 2


def run_comparison(E_eV: float = 200e3, n_pix: int = 128, n_cells_beam: int = 10, verbose: bool = True) -> dict:
    """Run both codes and return the comparison metrics (direct and k -> -k mapping; better one used)."""
    from reflection_holo import constants as C
    a = float(C.A_SI.value)
    psi_k = kernel_exit_wave(a, E_eV, n_pix, n_cells_beam)
    psi_a = abtem_exit_wave(a, E_eV, n_pix, n_cells_beam)
    Ik, Ia = spot_intensities(psi_k), spot_intensities(psi_a)
    Ia_inv = np.roll(Ia[::-1, ::-1], 1, axis=(0, 1))
    best = None
    for name, ref in (("direct", Ia), ("inverted", Ia_inv)):
        order = np.argsort(ref.ravel())[::-1][:N_STRONG]
        diff = np.abs(Ik.ravel()[order] - ref.ravel()[order])
        tol = TOL_ABS + TOL_REL * ref.ravel()[order]
        ok = bool(np.all(diff <= tol))
        cand = dict(mapping=name, order=order, diff=diff, tol=tol, ok=ok, ref=ref)
        if best is None or diff.max() < best["diff"].max():
            best = cand
    I_tot_k = float(np.mean(np.abs(psi_k) ** 2))
    I_tot_a = float(np.mean(np.abs(psi_a) ** 2))
    res = {"mapping": best["mapping"], "max_abs_diff": float(best["diff"].max()), "beams_ok": best["ok"],
           "I_total_kernel": I_tot_k, "I_total_abtem": I_tot_a,
           "flux_ok": (0.95 <= I_tot_k <= 1 + 1e-6) and (0.95 <= I_tot_a <= 1 + 1e-6)}
    if verbose:
        n = Ik.shape[0]
        print(f"T-transmission-limit: Si [100], {n_cells_beam} cells ({n_cells_beam * a:.2f} A), "
              f"{n_pix}^2 px, E = {E_eV / 1e3:.0f} keV, mapping = {best['mapping']}")
        print(" (k_z,k_y) index | I_kernel | I_abTEM | |diff| | tol")
        for o, d, t in zip(best["order"], best["diff"], best["tol"]):
            iz, iy = divmod(int(o), n)
            iz = iz - n if iz > n // 2 else iz
            iy = iy - n if iy > n // 2 else iy
            print(f" ({iz:+3d},{iy:+3d})       | {Ik.ravel()[o]:.5f}  | {best['ref'].ravel()[o]:.5f} "
                  f"| {d:.5f} | {t:.5f}")
        print(f" total intensity kernel {I_tot_k:.5f}, abTEM {I_tot_a:.5f}; beams_ok={best['ok']}, "
              f"flux_ok={res['flux_ok']}")
    return res


if __name__ == "__main__":  # pragma: no cover
    try:
        out = run_comparison()
    except ImportError as exc:
        print(f"abTEM/ASE not importable: {exc}")
        sys.exit(2)
    sys.exit(0 if (out["beams_ok"] and out["flux_ok"]) else 1)
