#!/usr/bin/env python3
"""Cross-check of the reflection_holo multislice kernel against abTEM in transmission.

Specification docs/05 section 4.3: the custom kernel is not trusted until it agrees
with abTEM to a stated tolerance.  This script runs the same Si slab (beam along
[110], Kirkland parametrization, same slicing, same grid, same 2/3 antialias cutoff
without taper, Fresnel propagator) through both codes and reports:

  1. normal incidence: relative L2 difference of the exit waves inside the band;
  2. tilted incidence at about 24 and 48 mrad: the reflection_holo wave launched as
     an explicit Fourier component (commensurate with the cell) versus abTEM's
     propagator-shear tilt, after removing the carrier and a global phase.

Differences come from the potential construction (abTEM superposes sub-pixel
deltas and divides by a sinc; reflection_holo evaluates exact structure-factor
phases) and, for the tilt, from abTEM's shear approximation, whose docstring
recommends tilts below about one degree.

Usage: python validation/abtem_crosscheck.py [--out report.json] [--backend numpy|cupy]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from reflection_holo.backend import get_xp, to_numpy  # noqa: E402
from reflection_holo.constants import wavelength_A  # noqa: E402
from reflection_holo.crystal import SurfaceCell  # noqa: E402
from reflection_holo.grid import Grid  # noqa: E402
from reflection_holo.multislice import Propagator, run_multislice  # noqa: E402
from reflection_holo.potential import PotentialBuilder  # noqa: E402

E_KEV = 200.0
A_SI = 5.4309


def slab_atoms(nx=3, ny=4, nz=10):
    cell = SurfaceCell("si111_110", A_SI)
    P = cell.periods
    pos = []
    for i in range(nx):
        for j in range(ny):
            for k in range(nz):
                pos.append(cell.atoms + np.array([i * P[0], j * P[1], k * P[2]]))
    pos = np.concatenate(pos)
    box = np.array([nx * P[0], ny * P[1], nz * P[2]])
    dz = P[2] / 2
    pos[:, 2] += dz / 2           # atoms at slice centres of abTEM's [i dz, (i+1) dz)
    return pos, box, dz


def run_ours(pos, box, dz, gpts, q0x, xp, dtype="complex128"):
    lam = float(wavelength_A(E_KEV))
    g = Grid(gpts[0], gpts[1], box[0], box[1], x0=0.0)
    pb = PotentialBuilder(g, xp, E_KEV, parametrization="kirkland", dtype=dtype)
    nslices = int(round(box[2] / dz))
    planes = np.arange(nslices) * dz            # transmit-then-propagate, like abTEM
    ts = []
    for s in range(nslices):
        sel = (pos[:, 2] >= s * dz) & (pos[:, 2] < (s + 1) * dz)
        ts.append(pb.transmission(pb.projected(pos[sel, 0], pos[sel, 1]), dz))
    psi0 = np.exp(2j * np.pi * q0x * g.x)[:, None] * np.ones((1, gpts[1]))
    psi0 = xp.asarray(psi0[None].astype(dtype))
    prop = Propagator(g, lam, xp, dtype, kind="fresnel")
    # the exit wave is wanted at nslices*dz, one slice after the last plane: add an
    # empty plane there (transmission 1)
    planes = np.append(planes, nslices * dz)
    ts.append(xp.ones_like(ts[0]))
    ex, _, _, _, _ = run_multislice(psi0, planes, lambda i: ts[i], [nslices * dz], prop, xp)
    return to_numpy(ex[0]), g


def run_abtem(pos, box, dz, gpts, tilt_mrad):
    import abtem
    from ase import Atoms
    abtem.config.set({"antialias.taper": 0.0, "precision": "float64"})
    atoms = Atoms("Si" * len(pos), positions=pos, cell=box, pbc=True)
    pot = abtem.Potential(atoms, gpts=gpts, slice_thickness=dz, projection="infinite",
                          parametrization="kirkland")
    wave = abtem.PlaneWave(energy=E_KEV * 1e3, tilt=(tilt_mrad, 0.0))
    exit_wave = wave.multislice(pot).compute()
    return np.asarray(exit_wave.array), abtem.__version__


def compare(a, b, g, q_max):
    """Relative L2 difference of the exit waves restricted to |q| <= q_max (cycles/A)
    after removing the best global phase; also the largest relative error of the
    beams carrying more than 1e-4 of the intensity."""
    band = g.q2 <= q_max**2
    A = np.fft.fft2(a) * band
    B = np.fft.fft2(b) * band
    ph = np.vdot(B, A)
    ph = ph / abs(ph)
    diff = np.linalg.norm(A - ph * B) / np.linalg.norm(B)
    strong = np.abs(B) ** 2 > 1e-4 * np.sum(np.abs(B) ** 2)
    beam_err = np.max(np.abs(A[strong] - ph * B[strong]) / np.abs(B[strong]))
    return dict(rel_L2_diff=float(diff), global_phase=float(np.angle(ph)),
                max_rel_err_strong_beams=float(beam_err), n_strong_beams=int(strong.sum()),
                q_max_per_A=q_max)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--backend", default="numpy")
    ap.add_argument("--gpts", type=int, nargs=2, default=(288, 256))
    args = ap.parse_args()
    xp = get_xp(args.backend)
    pos, box, dz = slab_atoms()
    gpts = tuple(args.gpts)
    lam = float(wavelength_A(E_KEV))
    report = dict(slab_box_A=box.tolist(), slice_thickness_A=dz, n_atoms=len(pos),
                  gpts=gpts, energy_keV=E_KEV, cases=[])
    ours0, g = run_ours(pos, box, dz, gpts, 0.0, xp)
    theirs0, ver = run_abtem(pos, box, dz, gpts, 0.0)
    report["abtem_version"] = ver
    for qm in (1.0, 2.0):
        report["cases"].append(dict(case="normal incidence", **compare(ours0, theirs0, g, qm)))
    for target in (24.0, 48.0):
        n = int(round(np.sin(target * 1e-3) / lam * box[0]))
        q0 = n / box[0]
        th = np.arcsin(q0 * lam) * 1e3
        if q0 > g.q_band:
            report["cases"].append(dict(case=f"tilt {th:.3f} mrad", skipped="outside band"))
            continue
        ours, _ = run_ours(pos, box, dz, gpts, q0, xp)
        theirs, _ = run_abtem(pos, box, dz, gpts, th)
        # abTEM's tilted wave omits the carrier exp(2 pi i q0 x); remove it from ours
        ours_c = ours * np.exp(-2j * np.pi * q0 * g.x)[:, None]
        # compare in a band shifted by the carrier: use the band of the carrier-free wave
        for qm in (1.0, 2.0):
            report["cases"].append(dict(case=f"tilt {th:.3f} mrad (explicit Fourier "
                                        "component vs abTEM propagator shear)",
                                        theta_mrad=th, **compare(ours_c, theirs, g, qm)))
    print(json.dumps(report, indent=1))
    if args.out:
        with open(args.out, "w") as fh:
            json.dump(report, fh, indent=1)


if __name__ == "__main__":
    main()
