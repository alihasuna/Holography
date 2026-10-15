"""
multislice_3d.py
================
3D multislice simulation for reflection electron diffraction.

Implements the Peng-Cowley periodic continuation method (1986/1988)
in the correct coordinate frame:

    z = [110]/sqrt(2)       beam propagation direction
    y = [1,-1,1]/sqrt(3)    outward surface normal
    x = [-1,1,2]/sqrt(6)    in-surface, perpendicular to beam

The crystal fills y < 0 and vacuum fills y > 0. The beam tilt for
grazing incidence is purely along y (the surface normal direction).

Algorithm per slice:
    1. Phase grating:      psi *= exp(i * sigma * V_proj)
    2. Absorbing boundary: psi *= A(y)
    3. Fresnel propagation: psi_k *= P(kx, ky)   [with beam tilt ky0]

Sign conventions follow Kirkland (2020):
    - Phase grating:  exp(+i * sigma * V)  [positive for attractive potential]
    - Propagator:     exp(-i * pi * lambda * k^2 * dz)  [negative in Fourier space]

References:
    Peng & Cowley, Acta Cryst. A42, 545 (1986)
    Peng & Cowley, Surface Science 199, 609 (1988)
    Kirkland, Advanced Computing in Electron Microscopy (2020), Ch. 6
    Ma & Marks, Acta Cryst. A46, 11 (1990) [BMCR / edge patching]
"""

import argparse
import numpy as np
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm, LogNorm

from simulation.constants import (
    LAMBDA_200KV, K_200KV, VOLTAGE_V,
    M_E, E_CHARGE, C_LIGHT,
)
from simulation.supercell import generate_supercell, compute_projected_potential


# ── physics ──────────────────────────────────────────────────────────────────

def interaction_parameter(voltage_v=VOLTAGE_V):
    """Relativistic interaction parameter sigma (Kirkland Eq. 5.19).

    sigma = (2*pi / (lambda*V)) * (m0*c^2 + eV) / (2*m0*c^2 + eV)

    At 200 kV: sigma = 7.2885e-4  1/(V*A).
    """
    lam = LAMBDA_200KV
    m0c2 = M_E * C_LIGHT**2 / E_CHARGE  # eV
    eV = voltage_v
    return (2 * np.pi / (lam * eV)) * (m0c2 + eV) / (2 * m0c2 + eV)


def make_propagator(nx, ny, cell_x, cell_y, dz,
                    lam=LAMBDA_200KV, ky_tilt_mrad=0.0):
    """Fresnel propagator in reciprocal space (Kirkland Eq. 6.64).

    P(kx, ky) = exp(-i * pi * lambda * (kx^2 + (ky - ky0)^2) * dz)

    The beam tilt for grazing incidence is encoded as a shift ky0
    along the surface normal direction (y).

    Parameters
    ----------
    ky_tilt_mrad : float
        Grazing angle in mrad. The beam is tilted toward the crystal
        (negative y direction) by this amount.
    """
    kx = np.fft.fftfreq(nx, d=cell_x / nx)
    ky = np.fft.fftfreq(ny, d=cell_y / ny)
    KX, KY = np.meshgrid(kx, ky)

    # beam tilt along y (toward crystal = negative y = negative ky0)
    ky0 = -ky_tilt_mrad * 1e-3 / lam  # negative because crystal is at y<0

    k_sq = KX**2 + (KY - ky0)**2
    return np.exp(-1j * np.pi * lam * k_sq * dz)


def make_absorber(ny, y_min, y_max, y_surface=0.0,
                  crystal_absorber_depth=10.0,
                  vacuum_absorber_depth=10.0,
                  strength=0.02):
    """Absorbing boundary mask A(y).

    Smooth exponential absorption at:
    - Bottom of crystal (y near y_min): simulates semi-infinite bulk
    - Top of vacuum (y near y_max): prevents periodic wrap-around

    The absorption ramps up quadratically from the edge of the
    "active" region.
    """
    y = np.linspace(y_min, y_max, ny, endpoint=False)
    mask = np.ones(ny, dtype=float)

    # bottom absorber: y in [y_min, y_min + crystal_absorber_depth]
    y_abs_bottom = y_min + crystal_absorber_depth
    below = y < y_abs_bottom
    if np.any(below):
        t = (y_abs_bottom - y[below]) / crystal_absorber_depth
        mask[below] = np.exp(-strength * t**2 * crystal_absorber_depth)

    # top absorber: y in [y_max - vacuum_absorber_depth, y_max]
    y_abs_top = y_max - vacuum_absorber_depth
    above = y > y_abs_top
    if np.any(above):
        t = (y[above] - y_abs_top) / vacuum_absorber_depth
        mask[above] = np.exp(-strength * t**2 * vacuum_absorber_depth)

    return mask


# ── multislice engine ────────────────────────────────────────────────────────

def run_multislice(n_cells_x=4, n_cells_z=200,
                   crystal_depth_A=50.0, vacuum_thickness_A=50.0,
                   nx=256, ny=256,
                   grazing_angle_mrad=28.0,
                   absorber_strength=0.02,
                   verbose=True):
    """Run the Peng-Cowley reflection multislice.

    Parameters
    ----------
    n_cells_x : int
        Repeats along x (in-surface). More = better lateral sampling.
    n_cells_z : int
        Slices along z (beam propagation). More = longer propagation.
    crystal_depth_A : float
        Crystal depth below surface (Angstroms).
    vacuum_thickness_A : float
        Vacuum above surface (Angstroms).
    nx, ny : int
        Real-space grid dimensions.
    grazing_angle_mrad : float
        Grazing angle on (1-11) surface in mrad.
    absorber_strength : float
        Absorbing boundary strength.
    verbose : bool
        Print progress.
    """
    if verbose:
        print("Building supercell...")
    sc = generate_supercell(
        n_cells_x=n_cells_x, n_cells_z=n_cells_z,
        crystal_depth_A=crystal_depth_A,
        vacuum_thickness_A=vacuum_thickness_A)

    cell_x = sc["cell_x"]
    cell_y = sc["cell_y"]
    dz = sc["dz"]
    n_slices = sc["n_slices"]
    sigma = interaction_parameter()

    if verbose:
        print(f"Supercell: {cell_x:.1f} x {cell_y:.1f} x {sc['cell_z']:.1f} A")
        print(f"Crystal depth: {crystal_depth_A:.0f} A, Vacuum: {vacuum_thickness_A:.0f} A")
        print(f"Grid: {nx}x{ny}, {n_slices} slices (dz={dz:.3f} A)")
        print(f"Atoms: {sc['n_atoms']}")
        print(f"Grazing angle: {grazing_angle_mrad:.1f} mrad "
              f"({grazing_angle_mrad/1e3*180/np.pi:.2f} deg)")
        print(f"Propagation: {sc['cell_z']:.0f} A = {sc['cell_z']/10:.1f} nm")

    # propagator with grazing angle tilt along y
    # NOTE: with SURFACE_NORMAL = [-1,1,-1]/sqrt(3), the crystal is at y > 0
    # in the PC frame (the outward normal points toward -y).
    # The beam tilt toward the crystal is in the +y direction.
    P = make_propagator(nx, ny, cell_x, cell_y, dz,
                        ky_tilt_mrad=grazing_angle_mrad)

    # bandwidth limiting aperture (Kirkland Ch. 6.8):
    # zero out Fourier components beyond 2/3 of Nyquist to prevent aliasing
    kx_arr = np.fft.fftfreq(nx, d=cell_x / nx)
    ky_arr = np.fft.fftfreq(ny, d=cell_y / ny)
    KX_bw, KY_bw = np.meshgrid(kx_arr, ky_arr)
    kx_max = nx / (2 * cell_x)  # Nyquist frequency
    ky_max = ny / (2 * cell_y)
    bandwidth_mask = ((KX_bw / kx_max)**2 + (KY_bw / ky_max)**2) <= (2.0/3.0)**2
    bandwidth_mask = bandwidth_mask.astype(float)

    # absorbing boundaries
    absorber_1d = make_absorber(
        ny, sc["y_min"], sc["y_max"],
        crystal_absorber_depth=min(15.0, crystal_depth_A * 0.3),
        vacuum_absorber_depth=min(15.0, vacuum_thickness_A * 0.3),
        strength=absorber_strength)
    absorber_2d = absorber_1d[:, None] * np.ones(nx)[None, :]

    # initial wavefunction: unit plane wave
    # (BMCR would seed with Bloch wave solution here — future improvement)
    psi = np.ones((ny, nx), dtype=complex)

    # multislice loop
    for islice in range(n_slices):
        z_start = islice * dz
        z_end = z_start + dz

        # projected potential
        V_proj = compute_projected_potential(
            sc["atoms_pc"], cell_x, cell_y, sc["y_min"],
            dz, z_start, z_end, nx_grid=nx, ny_grid=ny)

        # phase grating: T = exp(+i * sigma * V_proj)
        psi = psi * np.exp(1j * sigma * V_proj)

        # absorbing boundaries
        psi = psi * absorber_2d

        # Fresnel propagation + bandwidth limiting
        psi_k = np.fft.fft2(psi)
        psi_k = psi_k * P * bandwidth_mask
        psi = np.fft.ifft2(psi_k)

        if verbose and (islice + 1) % 50 == 0:
            amp = np.abs(psi)
            print(f"  Slice {islice+1}/{n_slices}: "
                  f"|psi|_max={amp.max():.4f}, "
                  f"|psi|_mean(crystal)={amp[:ny//2,:].mean():.4f}, "
                  f"|psi|_mean(vacuum)={amp[ny//2:,:].mean():.4f}")

    # diffraction pattern = |FFT(exit wave)|^2
    psi_k_exit = np.fft.fftshift(np.fft.fft2(psi))
    diffraction = np.abs(psi_k_exit)**2

    return {
        "psi_exit": psi,
        "diffraction": diffraction,
        "supercell": sc,
        "grazing_mrad": grazing_angle_mrad,
        "params": {
            "n_cells_x": n_cells_x,
            "n_cells_z": n_cells_z,
            "grid": (nx, ny),
            "n_slices": n_slices,
            "dz": dz,
            "grazing_mrad": grazing_angle_mrad,
            "cell": (cell_x, cell_y, sc["cell_z"]),
            "crystal_depth": crystal_depth_A,
            "vacuum_thickness": vacuum_thickness_A,
        },
    }


# ── output ───────────────────────────────────────────────────────────────────

def save_results(result, outdir):
    """Save diffraction pattern, exit wave, and diagnostic plots."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    params = result["params"]

    # 1. diffraction pattern
    diff = result["diffraction"]
    fig, axes = plt.subplots(1, 2, figsize=(16, 7), dpi=200)

    ax = axes[0]
    vmax = np.percentile(diff, 99.9)
    ax.imshow(diff, cmap="gray", norm=PowerNorm(gamma=0.3, vmin=0, vmax=vmax),
              origin="lower")
    ax.set_title("Simulated Diffraction (power-law scale)")
    ax.set_xlabel("kx"); ax.set_ylabel("ky (surface normal)")

    ax = axes[1]
    ax.imshow(np.log10(diff + 1), cmap="inferno", origin="lower")
    ax.set_title("log10(I + 1)")
    ax.set_xlabel("kx"); ax.set_ylabel("ky")

    info = (f"Si[110] reflection, grazing={params['grazing_mrad']:.1f} mrad\n"
            f"Cell: {params['cell'][0]:.0f}x{params['cell'][1]:.0f}x"
            f"{params['cell'][2]:.0f} A, {params['n_slices']} slices\n"
            f"Grid: {params['grid'][0]}x{params['grid'][1]}, "
            f"Atoms: {result['supercell']['n_atoms']}")
    fig.suptitle(info, fontsize=10, fontfamily="monospace")
    plt.tight_layout()
    plt.savefig(str(outdir / "multislice_diffraction.tiff"), dpi=200, format="tiff")
    plt.close()

    # 2. exit wave
    psi = result["psi_exit"]
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), dpi=200)
    axes[0].imshow(np.abs(psi), cmap="gray", origin="lower",
                   extent=[0, params['cell'][0],
                           -params['crystal_depth'], params['vacuum_thickness']])
    axes[0].axhline(0, color='r', linewidth=0.5, linestyle='--', label='surface')
    axes[0].set_title("|psi| exit wave"); axes[0].set_ylabel("y (A)")
    axes[0].legend(fontsize=8)

    axes[1].imshow(np.angle(psi), cmap="twilight", origin="lower",
                   vmin=-np.pi, vmax=np.pi,
                   extent=[0, params['cell'][0],
                           -params['crystal_depth'], params['vacuum_thickness']])
    axes[1].axhline(0, color='r', linewidth=0.5, linestyle='--')
    axes[1].set_title("Phase of exit wave"); axes[1].set_ylabel("y (A)")

    plt.tight_layout()
    plt.savefig(str(outdir / "multislice_exit_wave.tiff"), dpi=200, format="tiff")
    plt.close()

    # 3. y-profile of amplitude (diagnostic: is reflected wave visible?)
    amp = np.abs(psi)
    y_profile = amp.mean(axis=1)
    y_vals = np.linspace(-params['crystal_depth'], params['vacuum_thickness'],
                         len(y_profile))

    fig, ax = plt.subplots(figsize=(8, 4), dpi=150)
    ax.plot(y_vals, y_profile)
    ax.axvline(0, color='r', linewidth=0.5, linestyle='--', label='surface')
    ax.set_xlabel("y (A) [crystal < 0, vacuum > 0]")
    ax.set_ylabel("Mean |psi|")
    ax.set_title("y-profile of exit wave amplitude")
    ax.legend()
    plt.tight_layout()
    plt.savefig(str(outdir / "multislice_y_profile.tiff"), dpi=150, format="tiff")
    plt.close()

    print(f"Saved results to {outdir}/")


# ── main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Peng-Cowley reflection multislice for Si[110]")
    parser.add_argument("--nx", type=int, default=256)
    parser.add_argument("--ny", type=int, default=256)
    parser.add_argument("--ncx", type=int, default=4,
                        help="Unit cells along x (in-surface)")
    parser.add_argument("--ncz", type=int, default=200,
                        help="Slices along z (beam propagation)")
    parser.add_argument("--crystal-depth", type=float, default=50.0,
                        help="Crystal depth below surface (A)")
    parser.add_argument("--vacuum", type=float, default=50.0,
                        help="Vacuum above surface (A)")
    parser.add_argument("--grazing", type=float, default=28.0,
                        help="Grazing angle in mrad")
    parser.add_argument("--outdir", type=str, default=None)
    args = parser.parse_args()

    outdir = (Path(args.outdir) if args.outdir
              else Path(__file__).resolve().parent.parent / "simulation_results")

    print("=" * 60)
    print("Peng-Cowley Reflection Multislice: Si[110] / (1-11)")
    print("=" * 60)

    result = run_multislice(
        n_cells_x=args.ncx, n_cells_z=args.ncz,
        crystal_depth_A=args.crystal_depth,
        vacuum_thickness_A=args.vacuum,
        nx=args.nx, ny=args.ny,
        grazing_angle_mrad=args.grazing)

    save_results(result, outdir)
    print("Done.")
