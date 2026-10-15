#!/usr/bin/env python3
"""Your first reflection hologram, start to finish, in under a minute on a laptop.

The whole pipeline in one file, using the fast geometric (column) model instead of multislice:

  1. build a Si(001) crystal in three strips: reference, raised by 4 layers, buried dislocation
  2. move the atoms with the elastic field of a Lomer dislocation 2.5 nm below the surface
  3. compute the reflected (008) dark-field wave across the strips (geometric model)
  4. record an off-axis hologram with a tilted reference wave and Poisson noise
  5. reconstruct the complex wave (FFT, sideband, inverse FFT, divide by an empty hologram)
  6. plot the surface, the hologram, and the reconstructed phase and amplitude
     (the sharp dips in amplitude at the strip edges are ringing from the objective aperture)

Run:  python examples/01_first_hologram.py            (writes first_hologram.png)
Next: the same sample with full multislice is configs/si001_three_sections_cpu.yaml, run with
      python scripts/run_sections.py --config configs/si001_three_sections_cpu.yaml
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from reflection_holo import geometry as geo
from reflection_holo import holography as H
from reflection_holo.defects.dislocation import from_config
from reflection_holo.forward import geometric as gm
from reflection_holo.structure.sections import build_sections

# ---------------------------------------------------------------------------------------------
# Parameters (the same values as configs/si001_three_sections_cpu.yaml)
# ---------------------------------------------------------------------------------------------
E_KEV = 200.0  # beam energy
A_SI = 5.4309  # silicon lattice constant, A
V0 = 13.91  # mean inner potential, V (refraction at the surface)
HKL = (0, 0, 8)  # the specular reflection: (008) planes, parallel to the (001) surface
FRAME = geo.SI001_FRAME  # x = [001] surface normal, y = [1-10] across the beam, z = [110] beam
PERIODS = [40, 40, 40]  # three strips, 40 x 3.84 A = 15.4 nm each
RAISE = [0, 4, 0]  # strip 2 raised by 4 atomic layers (0.54 nm)
DISLOCATION = [{"burgers_over_a": [-0.5, 0.5, 0.0],  # Lomer: b = a/2[-110], in the surface plane
                "line_uvw": [1, 1, 0],  # line along the beam
                "depth_A": 25.0,  # 2.5 nm below the surface
                "position_yz_A": [384.0, 0.0],  # middle of strip 3
                "sign": 1}]
NY = 3600  # pixels across the beam (0.128 A each)
APERTURE = 0.06  # objective aperture radius, 1/A
CARRIER = (0.0, 0.2)  # hologram fringes 5 A apart along y
DOSE = 400  # counts per pixel (Poisson noise)
OFFSET_MRAD = 0.8  # operating angle = rocking-curve maximum, 0.8 mrad above the Bragg angle


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=".", help="folder for first_hologram.png")
    args = ap.parse_args()

    # 1-2. Crystal with three strips and the dislocation's elastic field applied to every atom
    defects = from_config(DISLOCATION, nu=0.22, a_A=A_SI, frame=FRAME)
    sample = build_sections(FRAME, A_SI, PERIODS, RAISE, depth_A=56.0, defects=defects, seam_y=76.8)
    print(f"1-2. crystal: {len(sample.positions)} atoms per 3.84 A repeat, cell {sample.Ly / 10:.1f} nm wide")

    # 3. Reflected wave along y. The geometric model sums the phase each atomic layer adds,
    #    -q.u, with u the displacement of that layer, weighted by an absorption depth of 12 A.
    bragg = geo.SpecularCondition(E_KEV, V0, A_SI, HKL)
    cond = geo.SpecularAtAngle(E_KEV, V0, A_SI, HKL, bragg.theta_ext + OFFSET_MRAD * 1e-3)
    y = np.arange(NY) * sample.Ly / NY
    dy = y[1] - y[0]
    depths = sample.info["layer_spacing_A"] * np.arange(120)
    strip = np.clip(np.searchsorted(sample.boundaries, y, side="right") - 1, 0, 2)
    r = np.stack(np.broadcast_arrays(-depths[:, None], y[None, :], 0.0 * y[None, :]), -1)
    u = sample.u_func(r)  # displacement of every layer at every y
    u[..., 0] += sample.heights[strip][None, :]  # the raised strip is a rigid shift up
    G, q_int, q_ext = gm.specular_vectors(cond)
    phase, amp = gm.column_phase(u, depths, G, q_int, q_ext, 12.0)
    wave = gm.to_deformed_coordinates(amp * np.exp(1j * phase), y, u[0, :, 1], sample.Ly)
    wave = gm.band_limit_1d(wave, dy, APERTURE)  # the objective aperture
    print(f"3.   (008) at a glancing angle of {cond.theta_ext * 1e3:.2f} mrad "
          f"(Bragg {bragg.theta_ext * 1e3:.2f} mrad), wavelength {geo.wavelength_A(E_KEV):.4f} A")

    # 4. Hologram: the object wave (identical image rows in this model) plus a tilted reference
    rows, dx = 40, 0.5
    psi = np.broadcast_to(wave, (rows, NY)).copy()
    ref_amp = np.abs(wave[(y > 25) & (y < 128)]).mean()
    rng = np.random.default_rng(1)
    hologram = H.form_hologram(psi, dx, dy, CARRIER, ref_amp, dose=DOSE, rng=rng)
    empty = H.form_hologram(np.full_like(psi, ref_amp), dx, dy, CARRIER, ref_amp, dose=DOSE, rng=rng)

    # 5. Reconstruction: sideband -> complex wave, divided by the empty hologram's sideband
    w, carrier = H.reconstruct(hologram, empty, dx, dy, APERTURE)
    profile = w.mean(axis=0)  # average the image rows
    ph = np.unwrap(np.angle(profile))
    ref = (y > 25) & (y < 128)  # reference strip, away from its edges
    ph -= np.polyval(np.polyfit(y[ref], ph[ref], 1), y)  # remove the tilt fitted on strip 1
    am = np.abs(profile) / np.abs(profile[ref]).mean()
    step = np.median(ph[(y > 179) & (y < 282)])
    core = np.abs(y - 384.0) < 60
    print(f"5.   step (strip 2 - strip 1): {step:+.2f} rad;  dislocation signal: {ph[core].min():+.1f} rad")

    # 6. Plot
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(4, 1, figsize=(7, 8), sharex=True, gridspec_kw={"height_ratios": [1, 1.2, 1, 1]})
    ynm = y / 10
    ax[0].plot(ynm, u[0, :, 0], "k")
    ax[0].set_ylabel("surface (A)")
    ax[1].imshow(hologram, aspect="auto", cmap="gray", extent=[0, ynm[-1], 0, rows * dx / 10])
    ax[1].set_ylabel("hologram\nrow (nm)")
    ax[2].plot(ynm, ph, "C0")
    ax[2].set_ylabel("phase (rad)")
    ax[3].plot(ynm, am, "C1")
    ax[3].set_ylabel("amplitude")
    ax[3].set_xlabel("y across the beam (nm): strip 1 reference | strip 2 raised | strip 3 dislocation")
    for a in ax:
        for b in sample.boundaries[1:-1] / 10:
            a.axvline(b, color="0.7", lw=0.6, ls="--")
    fig.suptitle("Si(001), (008) reflection, 200 keV: geometric model through the full hologram chain")
    fig.tight_layout()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "first_hologram.png", dpi=120)
    print(f"6.   wrote {out / 'first_hologram.png'}  (zoom into the hologram to see the 5 A fringes)")


if __name__ == "__main__":
    main()
