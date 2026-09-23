#!/usr/bin/env python
"""H2: supercell sizing for a physically realistic reflection multislice of Si(001) at 200 keV.

Report: docs/agent_reports/H2_realistic_supercell_sizing.md (every number printed here). Beam energy
200 keV (PROJECT_INPUT item 1; 300 keV is never used). Working reflection (0,0,8) (ASSUMPTION B17),
glancing angle = external angle of the (0,0,8) internal Bragg condition computed with the mean inner
potential of the potential the engine actually uses (Kirkland independent-atom model via abTEM
1.0.10, 13.903 V; ASSUMPTION B32). Engine: reflection_holo.forward.multislice (Peng-Cowley geometry,
slices along the beam z, grid x = outward surface normal by y = in-plane transverse; UNVALIDATED).

Conventions (docs/physics_conventions.md): exp(+i k.r); angular wavevectors k, K, G, q in rad/A;
reciprocal vectors g and spatial frequencies f in cycles/A (G = 2 pi g); theta = GLANCING angle to
the surface plane (external or internal as stated); x = OUTWARD normal (the crystal is at x below the
surface); step phase signed as in docs/physics_conventions.md (not used for sizing).

Modes
  (default)               print every number of the report: analytic derivations (two-beam Bragg
                          case, Bethe terms, absorption lengths), the stored engine measurements, the
                          cell layouts of every scenario, and the resources from a replica of
                          engine.estimate_resources that is checked against the engine on small
                          cells. Self-checks; exit status 1 if any check fails.
  --calibrate OUT.json    measure the CPU component costs on this machine with the operations that
                          engine.estimate_resources times (FFT, element-wise pass, potential slice).
  --measure OUT.json      run the engine on flat Si(001) strips: build-up of the specular beam with
                          distance from first contact, depth profile, frozen-phonon fluctuation
                          ratio (about 1 h on 4 shared cores). Results are written after every run.
                          Options: --only NAME ..., --backend numpy|cupy (cupy for the first GPU
                          sanity run: compare bu_100_r010 with the stored CPU plateau), --threads N.

Labels: every quantity carries one of METADATA_VERIFIED, SECTION_READ, REPRODUCED, PROJECT_INPUT,
ASSUMPTION, DERIVED_HERE, UNVERIFIED, TEST_ONLY (stand-in used only for a test run), MEASURED_HERE
(a measurement with the repository's engine in this container; a REPRODUCED-type number whose
premises are the labelled inputs of the run). Constants come only from reflection_holo.constants
(through the package functions that use them).
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "4")

import argparse  # noqa: E402
import dataclasses  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
DEFAULT_CAL = HERE / "supercell_sizing_cpu_calibration.json"
DEFAULT_MEAS = HERE / "supercell_sizing_measurements.json"

from reflection_holo.constants import A_SI_A, DIAMOND_BASIS  # noqa: E402
from reflection_holo.forward.cell import build_reflection_cell  # noqa: E402
from reflection_holo.forward.multislice import (AtomicPotential, FrozenPhonons,  # noqa: E402
                                                MultisliceParams, NumericalAbsorber,
                                                PhysicalAbsorption, SheetBeam, fft_friendly,
                                                run_realisation)
from reflection_holo.forward.multislice.physics import beam_constants  # noqa: E402
from reflection_holo.geometry.refraction import theta_int_from_ext_rad  # noqa: E402
from reflection_holo.geometry.specular import specular_condition_for  # noqa: E402
from reflection_holo.structure import Staircase, build_si001_terraces  # noqa: E402

E_KEV = 200.0                      # PROJECT_INPUT item 1 (Ali, 2026-09-22)
A = A_SI_A                         # ASSUMPTION B2 (reflection_holo.constants)
Q = A / 4.0                        # (001) layer spacing
AZ = {"100": (1, 0, 0), "110": (1, 1, 0)}
AZ_LABEL = {"100": "TEST_ONLY: stands in for PROJECT_INPUT item 8 (exact [100], the B20 demo value)",
            "110": "TEST_ONLY: stands in for PROJECT_INPUT item 8 ([110], the M2 null-test azimuth)"}
THETA_LABEL = ("TEST_ONLY: stands in for PROJECT_INPUT item 7; external angle of the (0,0,8) internal "
               "Bragg condition with the potential's own mean inner potential (B32)")
U_RMS_ASSUMED_A = 0.076            # ASSUMPTION (A7): inspected repository's value, also the value in
#                                    Prismatic's example input SI100.XYZ (L2 C14, SECTION_READ of the
#                                    format page); NOT a sourced Debye-Waller value for Si
B22_APERTURE_MRAD = 3.0            # ASSUMPTION B22 (demo dark-field objective aperture semi-angle)
T2_IMAGE_RES_A = 6.0               # T2 report: reconstruction resolution 6.0 A in the image plane
#                                    (B28 carrier 2 A x 3, B29 mask |q_c|/3; ASSUMPTION stand-ins)
B29_MARGIN_RES = 3                 # ASSUMPTION B29: regions 3 resolution elements from unusable px
ABSORBER_V = 100.0                 # NUMERICAL: engine practice (M2, T1, demo_hpc), sin^2 profile
BULK_ABSORBER_A = 15.0             # NUMERICAL: M2 cases and T1
TOP_ABSORBER_A = 10.0              # NUMERICAL: M2 cases, T1, demo_hpc
GAP_A, EDGE_A = 2.0, 2.0           # sheet beam: bottom 2 A above the surface, sin^2 edges 2 A (M2)
MAX_PIXEL_A = 0.13                 # derived below (band requirements); the M2/T1 practice

CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, ok, detail: str) -> bool:
    ok = bool(ok)
    CHECKS.append((name, ok, detail))
    print(f"  CHECK {'PASS' if ok else 'FAIL'} {name}: {detail}")
    return ok


def git_state() -> dict:
    try:
        c = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True,
                           text=True, check=True).stdout.strip()
        d = subprocess.run(["git", "-C", str(REPO), "status", "--porcelain"], capture_output=True,
                           text=True, check=True).stdout.strip()
        return dict(commit=c, dirty=bool(d))
    except Exception as exc:                                  # pragma: no cover
        return dict(commit=None, error=str(exc))


def loadavg() -> list[float]:
    try:
        return [float(v) for v in Path("/proc/loadavg").read_text().split()[:3]]
    except OSError:                                           # pragma: no cover
        return []


# ================================================================================================
# Potential the engine uses: Kirkland (abTEM 1.0.10), exact structure factors of the 8-atom basis
# ================================================================================================
_F = None


def kirkland_F(f2):
    """abTEM KirklandParametrization().projected_scattering_factor("Si")(f^2), V A^3, f in
    cycles/A: the function the engine calls (potentials.AtomicPotential.scattering_factor)."""
    global _F
    if _F is None:
        from abtem.parametrizations import KirklandParametrization
        _F = KirklandParametrization().projected_scattering_factor("Si")
    return np.asarray(_F(np.asarray(f2, dtype=np.float64)), dtype=np.float64)


def structure_factor(hkl) -> complex:
    """sum_j exp(+2 pi i hkl.r_j) over constants.DIAMOND_BASIS (docs/physics_conventions.md)."""
    return complex(np.sum(np.exp(2j * np.pi * (DIAMOND_BASIS @ np.asarray(hkl, float)))))


def V_hkl(hkl) -> complex:
    """Fourier coefficient of the crystal potential (V): S_hkl F(|g|^2) / a^3 (DERIVED_HERE: the 2D
    transform of the infinite projection equals the 3D transform in the plane k_z = 0, and the
    atomic potential is spherical)."""
    h = np.asarray(hkl, float)
    return structure_factor(h) * float(kirkland_F(np.array([h @ h / A**2]))[0]) / A**3


def kirkland_mip() -> float:
    return float(8.0 / A**3 * kirkland_F(np.array([0.0]))[0])


def theta_0008(V0) -> tuple[float, float]:
    sc = specular_condition_for((0, 0, 8), (0, 0, 1), E_keV=E_KEV, V0_V=V0, a_A=A)
    return float(sc.theta_ext), float(theta_int_from_ext_rad(sc.theta_ext, E_KEV, V0))


# ================================================================================================
# Flat Si(001) strip for the engine measurements (one z period built with every builder assertion,
# then tiled along z: exact for a flat terrace, which is periodic along the beam)
# ================================================================================================
def flat_strip(*, azimuth: str, r: float, L_after_contact_A: float, y_periods: int, clean_A: float,
               u_rms_A=None, precision="complex64", threads=4, buildup_depth_A=20.0,
               backend="numpy"):
    V0 = kirkland_mip()
    th, th_int = theta_0008(V0)
    az = AZ[azimuth]
    P = A if azimuth == "100" else A / np.sqrt(2.0)
    dz = A / 4.0 if azimuth == "100" else P / 4.0
    depth = BULK_ABSORBER_A + clean_A
    sub = int(np.ceil(depth / Q)) + 2
    ent = 10 * dz
    periods = int(np.ceil((GAP_A / np.tan(th) + L_after_contact_A - ent) / P))
    one = build_si001_terraces(
        azimuth_uvw=az, azimuth_label=AZ_LABEL[azimuth],
        staircase=Staircase(edges="parallel", terrace_layers=(0,), terrace_widths=(y_periods,),
                            boundary_step_layers=0),
        edge_periods=1, substrate_layers=sub, first_terrace_backbond_uvw=(1, 1, 0),
        termination="bulk", overlayer=None, vacuum_above_A=10.0, lattice_parameter_A=A,
        lattice_parameter_label="ASSUMPTION B2")
    n = one.n_atoms
    pos = np.tile(one.positions_A, (periods, 1))
    pos[:, 2] += np.repeat(np.arange(periods), n) * P
    cell_A = one.cell_A.copy()
    cell_A[2, 2] = periods * P
    md = dict(one.metadata)
    md["edge_periods"] = periods
    md["atom_count"] = int(n * periods)
    md["positions_sha256"] = hashlib.sha256(np.ascontiguousarray(pos, "<f8").tobytes()).hexdigest()
    md["tiled_along_z"] = dict(periods=periods, from_verified_build_of_periods=1)
    s = dataclasses.replace(one, positions_A=pos, species=np.tile(one.species, periods),
                            cell_A=cell_A, layer_index=np.tile(one.layer_index, periods),
                            terrace_index=np.tile(one.terrace_index, periods), metadata=md)
    Lz = ent + periods * P
    H = Lz * np.tan(th) - GAP_A - 1.0
    vac = float(np.ceil(H + Lz * np.tan(th) + 1.0))
    cell = build_reflection_cell(s, vacuum_above_A=vac, depth_below_A=depth,
                                 bulk_absorber_A=BULK_ABSORBER_A, top_absorber_A=TOP_ABSORBER_A,
                                 entrance_vacuum_z_A=ent)
    lab = ("TEST_ONLY: stands in for PROJECT_INPUT item 21" if r > 0 else
           "ASSUMPTION: no physical absorption (B30)")
    absn = PhysicalAbsorption(model="proportional", ratio=float(r), label=lab)
    if u_rms_A is None:
        pot = AtomicPotential(cell, parameterisation="kirkland", physical_absorption=absn,
                              frozen_phonons=None,
                              static_lattice_label="ASSUMPTION: static lattice")
    else:
        pot = AtomicPotential(cell, parameterisation="kirkland", physical_absorption=absn,
                              frozen_phonons=FrozenPhonons(
                                  rms_displacement_A=float(u_rms_A),
                                  label="ASSUMPTION: 0.076 A per axis (A7), not a sourced value"),
                              static_lattice_label=None)
    xs = float(cell.metadata["layout"]["highest_surface_x_A"])
    beam = SheetBeam(height_A=float(H), edge_A=EDGE_A, x_bottom_A=xs + GAP_A,
                     theta_in_ext_rad=th, theta_label=THETA_LABEL)
    nx = fft_friendly(int(np.ceil(cell.extent_x_A / MAX_PIXEL_A)))
    ny = fft_friendly(int(np.ceil(cell.extent_y_A / MAX_PIXEL_A)))
    params = MultisliceParams(energy_keV=E_KEV, nx=nx, ny=ny, dz_A=dz, propagator="exact",
                              band_limit="2/3", backend=backend, precision=precision,
                              threads=threads,
                              absorber=NumericalAbsorber(strength_V=ABSORBER_V, profile="sin2"),
                              theta_out_ext_rad=th, buildup_depth_A=buildup_depth_A)
    info = dict(azimuth=azimuth, absorption_ratio=r, absorption_label=lab, backend=backend,
                L_after_contact_A=L_after_contact_A, y_periods=y_periods, clean_depth_A=clean_A,
                bulk_absorber_A=BULK_ABSORBER_A, top_absorber_A=TOP_ABSORBER_A,
                absorber_V=ABSORBER_V, depth_below_A=depth, substrate_layers=sub, periods=periods,
                entrance_A=ent, L_z_A=Lz, H_A=float(H), vacuum_above_A=vac, gap_A=GAP_A,
                edge_A=EDGE_A, x_surface_A=xs, extent_x_A=cell.extent_x_A,
                extent_y_A=cell.extent_y_A, nx=nx, ny=ny, dz_A=dz,
                n_slices=int(round(Lz / dz)), n_atoms=int(len(cell.Z)), theta_ext_rad=th,
                theta_int_rad=th_int, V0_mip_V=V0, z_contact_A=GAP_A / np.tan(th),
                u_rms_A=u_rms_A, precision=precision, threads=threads)
    return cell, pot, beam, params, info


def _vacuum_window(x, xs, x_cut, taper):
    w = np.clip((x - (xs + x_cut)) / taper, 0.0, 1.0)
    return np.sin(0.5 * np.pi * w) ** 2


def specular_column(ew, *, xs, th, radius, x_cut=2.0, taper=3.0):
    """f_y = 0 component (y average) of the exit wave in the VACUUM (crystal masked with a sin^2
    taper), band-passed |f_x - f_c| <= radius about f_c = sin(theta)/lambda, demodulated by
    exp(-2 pi i f_c x): the specular envelope R versus exit-plane height x (DERIVED_HERE)."""
    lam = ew.metadata["beam"]["wavelength_A"]
    fc = np.sin(th) / lam
    nx = ew.psi.shape[0]
    x = ew.x0_A + np.arange(nx) * ew.dx_A
    col = ew.psi.astype(np.complex128).mean(axis=1) * _vacuum_window(x, xs, x_cut, taper)
    fx = np.fft.fftfreq(nx, ew.dx_A)
    e = np.fft.ifft(np.fft.fft(col) * (np.abs(fx - fc) <= radius)) * np.exp(-2j * np.pi * fc * x)
    return x, e


def darkfield_2d(ew, *, xs, th, radius, x_cut=2.0, taper=3.0):
    """2D dark-field wave: crystal masked, circular aperture of radius `radius` (cycles/A) about
    (f_c, 0), demodulated (the B22 dark-field selection applied to the vacuum part)."""
    lam = ew.metadata["beam"]["wavelength_A"]
    fc = np.sin(th) / lam
    nx, ny = ew.psi.shape
    x = ew.x0_A + np.arange(nx) * ew.dx_A
    psi = ew.psi.astype(np.complex128) * _vacuum_window(x, xs, x_cut, taper)[:, None]
    fx = np.fft.fftfreq(nx, ew.dx_A)[:, None]
    fy = np.fft.fftfreq(ny, ew.dy_A)[None, :]
    ap = (fx - fc) ** 2 + fy ** 2 <= radius ** 2
    return x, np.fft.ifft2(np.fft.fft2(psi) * ap) * np.exp(-2j * np.pi * fc * x)[:, None]


def buildup_analysis(x, e, info, *, bin_A=500.0, exit_excl_A=750.0, plateau_A=2500.0):
    th, xs, Lz, zc = (info["theta_ext_rad"], info["x_surface_A"], info["L_z_A"],
                      info["z_contact_A"])
    zs = Lz - (x - xs) / np.tan(th)                      # surface point of the ray (DERIVED_HERE)
    ok = (x >= xs + 5.0) & (zs >= zc)
    d = zs[ok] - zc
    R = e[ok]
    L = Lz - zc
    p0, p1 = L - exit_excl_A - plateau_A, L - exit_excl_A
    pl = (d >= p0) & (d < p1)
    Rpl = complex(R[pl].mean())
    bins = []
    b = 0.0
    while b < L:
        m = (d >= b) & (d < b + bin_A)
        if np.any(m):
            v = complex(R[m].mean())
            bins.append(dict(start_A=b, end_A=min(b + bin_A, L), R_abs=abs(v),
                             R_arg=float(np.angle(v)), amp_dev=abs(v) / abs(Rpl) - 1.0,
                             phase_dev=float(np.angle(v / Rpl))))
        b += bin_A
    inside = [q for q in bins if q["end_A"] <= p1 + 1e-9]
    pq = [q for q in inside if q["start_A"] >= p0 - 1e-9]

    def conv(key, eps):
        last_bad = None
        for q in inside:
            if abs(q[key]) > eps:
                last_bad = q
        return 0.0 if last_bad is None else last_bad["end_A"]

    return dict(bins=bins, plateau_A=[p0, p1], R_plateau_abs=abs(Rpl),
                R_plateau_arg=float(np.angle(Rpl)),
                plateau_max_phase_dev=float(max(abs(q["phase_dev"]) for q in pq)) if pq else None,
                plateau_max_amp_dev=float(max(abs(q["amp_dev"]) for q in pq)) if pq else None,
                converged_phase_1e_2_A=conv("phase_dev", 1e-2),
                converged_phase_3e_3_A=conv("phase_dev", 3e-3),
                converged_amp_1e_2_A=conv("amp_dev", 1e-2),
                converged_amp_3e_2_A=conv("amp_dev", 3e-2),
                exit_bins=[q for q in bins if q["start_A"] >= p1 - 1e-9],
                bin_A=bin_A, exit_excluded_A=exit_excl_A, distance_origin="bottom-edge contact")


def depth_profile(ew, info):
    nx = ew.psi.shape[0]
    x = ew.x0_A + np.arange(nx) * ew.dx_A
    I = (np.abs(ew.psi.astype(np.complex128)) ** 2).mean(axis=1)
    xs = info["x_surface_A"]
    depths = np.arange(0.0, info["clean_depth_A"] + 0.1, 5.0)
    prof = [dict(depth_A=float(dd), I=float(I[np.argmin(np.abs(x - (xs - dd)))])) for dd in depths]
    below = x <= xs
    dep = xs - x[below]
    Ib = I[below]
    out = {}
    for thr in (1e-2, 1e-4, 1e-6):
        # deepest point whose intensity still exceeds thr (so everything deeper is below thr)
        above = dep[Ib > thr]
        out[f"depth_I_below_{thr:.0e}_A"] = float(above.max()) if above.size else 0.0
    return dict(profile=prof, **out, note="y-averaged |psi|^2 at the exit plane, incident = 1")


def run_buildup(name, **kw):
    t0 = time.time()
    cell, pot, beam, params, info = flat_strip(**kw)
    t1 = time.time()
    ew = run_realisation(cell, potential=pot, beam=beam, params=params, realisation=0, seed=None)
    t2 = time.time()
    x, e = specular_column(ew, xs=info["x_surface_A"], th=info["theta_ext_rad"], radius=0.1)
    res = dict(info=info, build_s=t1 - t0, run_s=t2 - t1, loadavg_after=loadavg(),
               buildup=buildup_analysis(x, e, info), depth=depth_profile(ew, info),
               specular_filter_radius_per_A=0.1,
               validation_status=ew.metadata["validation_status"])
    print(f"[measure] {name}: atoms {info['n_atoms']}, grid {info['nx']}x{info['ny']}, "
          f"{info['n_slices']} slices, run {t2 - t1:.0f} s", flush=True)
    return res


def run_phonons(name, *, n_real, seed, **kw):
    t0 = time.time()
    cell, pot0, beam, params, info = flat_strip(u_rms_A=None, **kw)
    _, potf, _, _, _ = flat_strip(u_rms_A=U_RMS_ASSUMED_A, **kw)
    lam = beam_constants(E_KEV)["wavelength_A"]
    rad = B22_APERTURE_MRAD * 1e-3 / lam
    th, xs = info["theta_ext_rad"], info["x_surface_A"]
    ew0 = run_realisation(cell, potential=pot0, beam=beam, params=params, realisation=0, seed=None)
    x, D0 = darkfield_2d(ew0, xs=xs, th=th, radius=rad)
    s1 = np.zeros_like(D0)
    s2 = np.zeros(D0.shape)
    times = []
    for i in range(n_real):
        t = time.time()
        ew = run_realisation(cell, potential=potf, beam=beam, params=params, realisation=i,
                             seed=seed)
        _, D = darkfield_2d(ew, xs=xs, th=th, radius=rad)
        s1 += D
        s2 += np.abs(D) ** 2
        times.append(time.time() - t)
        print(f"[measure] {name}: realisation {i} {times[-1]:.0f} s", flush=True)
    m = s1 / n_real
    v = (s2 - n_real * np.abs(m) ** 2) / (n_real - 1)
    zs = info["L_z_A"] - (x - xs) / np.tan(th)
    d = zs - info["z_contact_A"]
    L = info["L_z_A"] - info["z_contact_A"]
    reg = (x >= xs + 5.0) & (d >= 1500.0) & (d <= L - 750.0)
    coh = np.abs(m[reg]) ** 2 - v[reg] / n_real
    rho2 = float(v[reg].mean() / coh.mean())
    ph_sys = float(np.angle(np.sum(m[reg] * np.conj(D0[reg]))))
    amp_ratio = float(np.sqrt(np.mean(np.abs(m[reg]) ** 2) / np.mean(np.abs(D0[reg]) ** 2)))
    # per-row (surface position) ratio to show the dependence on distance
    rows = []
    for lo in np.arange(0.0, L, 500.0):
        rr = (x >= xs + 5.0) & (d >= lo) & (d < lo + 500.0)
        if np.any(rr):
            c = np.abs(m[rr]) ** 2 - v[rr] / n_real
            rows.append(dict(start_A=float(lo), rho2=float(v[rr].mean() / c.mean()),
                             amp_mean_over_static=float(np.sqrt(np.mean(np.abs(m[rr]) ** 2) /
                                                                np.mean(np.abs(D0[rr]) ** 2)))))
    res = dict(info=info, n_realisations=n_real, seed=seed, u_rms_A=U_RMS_ASSUMED_A,
               u_label="ASSUMPTION A7 (not sourced)", aperture_mrad=B22_APERTURE_MRAD,
               aperture_radius_per_A=rad, region=dict(distance_A=[1500.0, L - 750.0],
                                                      min_height_above_surface_A=5.0,
                                                      x_rows=int(reg.sum()),
                                                      pixels=int(reg.sum()) * D0.shape[1]),
               rho2=rho2, rho=float(np.sqrt(rho2)), phase_mean_minus_static_rad=ph_sys,
               amp_mean_over_static=amp_ratio, rows=rows, times_s=times,
               total_s=time.time() - t0, loadavg_after=loadavg())
    print(f"[measure] {name}: rho^2 {rho2:.4g}, phase(mean) - phase(static) {ph_sys:+.4f} rad",
          flush=True)
    return res


MEASUREMENTS = [
    ("bu_100_r010", dict(kind="buildup", azimuth="100", r=0.10, L_after_contact_A=6000.0,
                         y_periods=2, clean_A=100.0)),
    ("bu_100_r005", dict(kind="buildup", azimuth="100", r=0.05, L_after_contact_A=9000.0,
                         y_periods=2, clean_A=100.0)),
    ("bu_110_r010", dict(kind="buildup", azimuth="110", r=0.10, L_after_contact_A=6000.0,
                         y_periods=2, clean_A=100.0)),
    ("bu_100_r000", dict(kind="buildup", azimuth="100", r=0.0, L_after_contact_A=12000.0,
                         y_periods=2, clean_A=100.0)),
    ("fp_100_r010", dict(kind="phonons", azimuth="100", r=0.10, L_after_contact_A=3000.0,
                         y_periods=3, clean_A=60.0, n_real=8, seed=20260923)),
]


def measure(out: Path, only=None, backend="numpy", threads=4):
    data = dict(schema="H2/measurements/1", created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                                       time.gmtime()),
                git=git_state(), nproc=os.cpu_count(), loadavg_start=loadavg(),
                threads_env={k: os.environ.get(k) for k in ("OMP_NUM_THREADS",
                                                           "OPENBLAS_NUM_THREADS")},
                label="MEASURED_HERE with the UNVALIDATED engine; TEST_ONLY absorption and "
                      "azimuth stand-ins; static lattice unless stated", runs={})
    if out.exists():
        data = json.loads(out.read_text())
    for name, spec in MEASUREMENTS:
        if only and name not in only:
            continue
        if name in data["runs"]:
            print(f"[measure] {name}: already in {out}, skipped", flush=True)
            continue
        spec = dict(spec, backend=backend, threads=threads)
        kind = spec.pop("kind")
        res = run_buildup(name, **spec) if kind == "buildup" else run_phonons(name, **spec)
        data["runs"][name] = res
        data["loadavg_end"] = loadavg()
        tmp = out.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=1, default=float))
        tmp.replace(out)


# ================================================================================================
# CPU calibration: the operations engine.estimate_resources times, at several grid sizes
# ================================================================================================
def calibrate(out: Path, threads=4, precision="complex64"):
    from reflection_holo.forward.multislice.backend import get_backend
    be = get_backend("numpy", precision, threads)
    rng = np.random.default_rng(0)
    fft_rows = []
    for nx, ny in ((512, 256), (1024, 512), (1024, 1024), (2048, 1024), (2048, 2048),
                   (4096, 2048)):
        a = (rng.standard_normal((nx, ny)) + 1j * rng.standard_normal((nx, ny))).astype(precision)
        be.fft2(a)
        t0 = time.perf_counter()
        for _ in range(6):
            b = be.fft2(a)
        t_fft = (time.perf_counter() - t0) / 6
        t0 = time.perf_counter()
        for _ in range(6):
            b = a * b * a
        t_elem = (time.perf_counter() - t0) / 6 / 2
        fft_rows.append(dict(nx=nx, ny=ny, npx=nx * ny, fft_s=t_fft, elementwise_pass_s=t_elem))
        print(f"[calibrate] fft {nx}x{ny}: {t_fft * 1e3:.2f} ms, elementwise {t_elem * 1e3:.2f} ms",
              flush=True)
        del a, b
    pot_rows = []
    for nx, ny, m in ((1024, 256, 64), (1024, 256, 256), (2048, 512, 256), (2048, 1024, 512),
                      (4096, 1024, 512), (2048, 2048, 1024)):
        a = (rng.standard_normal((nx, ny)) + 1j * rng.standard_normal((nx, ny))).astype(precision)
        Ex = a[:, :1].repeat(m, axis=1)
        Ey = a[:1, :].T.repeat(m, axis=1)
        np.exp(1j * np.angle(Ex))
        t0 = time.perf_counter()
        for _ in range(3):
            np.exp(1j * np.angle(Ex))
            np.exp(1j * np.angle(Ey))
        t_exp = (time.perf_counter() - t0) / 3
        Ex @ Ey.T
        t0 = time.perf_counter()
        for _ in range(3):
            Ex @ Ey.T
        t_gemm = (time.perf_counter() - t0) / 3
        pot_rows.append(dict(nx=nx, ny=ny, m=m, exp_s=t_exp, gemm_s=t_gemm,
                             gemm_flops=8.0 * nx * ny * m / t_gemm))
        print(f"[calibrate] potential {nx}x{ny} m={m}: exp {t_exp * 1e3:.2f} ms, GEMM "
              f"{t_gemm * 1e3:.2f} ms ({8.0 * nx * ny * m / t_gemm / 1e9:.1f} GFLOP/s)", flush=True)
        del a, Ex, Ey
    data = dict(schema="H2/cpu_calibration/1", created_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                                          time.gmtime()),
                git=git_state(), nproc=os.cpu_count(), loadavg=loadavg(), threads=threads,
                precision=precision, fft=fft_rows, potential=pot_rows,
                label="MEASURED_HERE (4-core container shared with other agents)")
    out.write_text(json.dumps(data, indent=1))
    print(f"[calibrate] written {out}", flush=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--calibrate", type=Path, default=None)
    ap.add_argument("--measure", type=Path, default=None)
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--backend", choices=("numpy", "cupy"), default="numpy",
                    help="measure mode only; cupy for the first GPU sanity run (compare "
                         "bu_100_r010 with the stored CPU plateau)")
    ap.add_argument("--threads", type=int, default=4, help="measure mode only (FFT workers)")
    ap.add_argument("--calibration-file", type=Path, default=DEFAULT_CAL)
    ap.add_argument("--measurement-file", type=Path, default=DEFAULT_MEAS)
    a = ap.parse_args(argv)
    if a.calibrate:
        calibrate(a.calibrate)
        return 0
    if a.measure:
        measure(a.measure, only=a.only, backend=a.backend, threads=a.threads)
        return 0
    return report(a.calibration_file, a.measurement_file)


# ================================================================================================
# Report mode (default): every number of docs/agent_reports/H2_realistic_supercell_sizing.md
# ================================================================================================
from scipy import special  # noqa: E402

from reflection_holo.forward.multislice import estimate_resources  # noqa: E402
from reflection_holo.forward.multislice.engine import GPU_ASSUMED  # noqa: E402
from reflection_holo.geometry.refraction import refraction_delta  # noqa: E402
from reflection_holo.structure.shapes import HalfTorus  # noqa: E402

D_ASSERT_A = 20.0      # engine buildup_depth_A: the minimum of its 20-100 A range; the measured
#                        amplitude 1/e depth at [100] is about 10 A (section 7), below it
EPS_PHASE = 1e-2       # rad: the M2 fixed-beam translation tolerance (docs/05 4.4 rung 3), adopted
#                        here as the convergence target of every length (DERIVED_HERE there)
N_MEAS_RES = 2         # ASSUMPTION: measuring length of one terrace region, in resolution elements
MISCUTS_DEG = (0.05, 0.1, 0.25, 0.5)   # ASSUMPTION scenarios for PROJECT_INPUT item 11
OVERLAYERS_A = (0.0, 10.0, 20.0, 30.0) # ASSUMPTION scenarios for PROJECT_INPUT item 12 (0 = B26)
TORUS_R_A, TORUS_r_A = 1000.0, 20.0     # ASSUMPTION B33/B34 (T2 geometric test size, Ali)
SIGMA_PHI_DOC03 = 0.028                 # docs/03 section 4 example (contrast 0.5, 1e4 counts)
SIGMA_H_TARGET_A = 0.1                  # ASSUMPTION: height precision target for the B16 example
DPHI_FP = 1e-2                          # rad: frozen-phonon sampling target (same as EPS_PHASE)

# M2 report section 10.5, the printed `--estimate` lines of study.yaml (grid, slices, atoms,
# engine arrays MB, CPU s with x1.5, GPU s): reference values for the replica check.
M2_STUDY = {
    "tfix_bragg_abs0_L0": (640, 60, 1434, 19224, 4, 8, 0.3),
    "tfix_bragg_abs0_L10k": (1875, 60, 11850, 159840, 16, 173, 3.7),
    "tfix_bragg_abs0_L20k": (3125, 60, 22266, 300456, 29, 606, 9.5),
    "tfix_bragg_abs05_L0": (640, 60, 1434, 19224, 4, 7, 0.3),
    "tfix_bragg_abs05_L5k": (1260, 60, 6642, 89532, 10, 58, 1.7),
    "tfix_bragg_abs05_L10k": (1875, 60, 11850, 159840, 16, 178, 3.7),
    "tfix_bragg_abs10_L5k": (1260, 60, 6642, 89532, 10, 53, 1.7),
    "tfix_bragg_abs10_L10k": (1875, 60, 11850, 159840, 16, 150, 3.7),
    "tfix_off12_abs10_L5k": (1120, 60, 7010, 94500, 10, 52, 1.7),
    "tfix_off20_abs10_L5k": (1440, 60, 6406, 86346, 11, 67, 1.7),
    "tmov_bragg_abs10_L10k": (1875, 60, 11850, 159840, 16, 210, 3.7),
    "step_w8_bragg_abs10_L5k": (1260, 480, 6642, 742784, 82, 216, 4.3),
    "step_w16_bragg_abs10_L5k": (1260, 960, 6642, 1485568, 167, 517, 9.6),
    "step_w32_bragg_abs10_L5k": (1260, 1920, 6642, 2971136, 340, 1319, 22.8),
    "step_w16_bragg_abs0_L5k": (1260, 960, 6642, 1485568, 167, 479, 9.6),
    "step_w16_off20_abs10_L5k": (1440, 960, 6406, 1432704, 177, 531, 10.7),
    "step_w16_bragg_abs10_L10k": (1875, 960, 11850, 2652160, 267, 1213, 26.0),
}


def hdr(title):
    print("\n" + "=" * 100 + "\n" + title + "\n" + "=" * 100, flush=True)


# ---- cost model: replica of engine.estimate_resources -------------------------------------------
def replica_memory(nx, ny, n_max, n_atoms, n_species=1, precision="complex64"):
    """engine.estimate_resources' array accounting, replicated line by line."""
    cb = np.dtype(precision).itemsize
    rb = cb // 2
    npx = nx * ny
    arrays = {"psi": cb * npx, "transmission (band-limited)": cb * npx,
              "propagators P(dz), P(dz/2)": 2 * cb * npx, "band mask": rb * npx,
              "scattering factor per species": rb * npx * max(1, n_species),
              "FFT work arrays (x3)": 3 * cb * npx,
              "structure-factor factors Ex, Ey (largest slice)": cb * (nx + ny) * n_max,
              "structure-factor sum S": cb * npx,
              "atom positions (float64)": 8 * 3 * n_atoms * 2}
    return arrays, int(sum(arrays.values()))


def replica_gpu_s(nx, ny, N, nonempty, n_mean, precision="complex64"):
    """engine.estimate_resources' GPU model (constants engine.GPU_ASSUMED: ASSUMPTION)."""
    g = GPU_ASSUMED
    cb = np.dtype(precision).itemsize
    npx = nx * ny
    t_fft = max(g["launch_s"], 2 * cb * npx * np.log2(max(npx, 2)) / 4 /
                (g["bandwidth_Bps"] * g["fft_efficiency"]))
    t_el = max(g["launch_s"], 3 * cb * npx / g["bandwidth_Bps"])
    t_pot = max(g["launch_s"], 8.0 * npx * n_mean / g["gemm_flops"])
    per_e = 2 * t_fft + 4 * t_el
    per_f = per_e + 3 * t_fft + 6 * t_el + t_pot
    return (N - nonempty) * per_e + nonempty * per_f


def cpu_constants(cal):
    """Component costs fitted to the --calibrate measurements (large grids, npx >= 1e6)."""
    big = [r for r in cal["fft"] if r["npx"] >= 1_000_000]
    pot = cal["potential"]
    return dict(
        c_fft=float(np.median([r["fft_s"] / (r["npx"] * np.log2(r["npx"])) for r in big])),
        c_el=float(np.median([r["elementwise_pass_s"] / r["npx"] for r in big])),
        c_exp=float(np.median([r["exp_s"] / ((r["nx"] + r["ny"]) * r["m"]) for r in pot])),
        c_gemm=float(np.median([r["gemm_s"] / (8.0 * r["nx"] * r["ny"] * r["m"]) for r in pot])))


def replica_cpu_s(nx, ny, N, nonempty, n_mean, cc):
    """engine.estimate_resources' CPU model with the fitted component costs (MEASURED_HERE),
    WITHOUT the x1.5 factor of run_study.py (the caller applies it and says so)."""
    npx = nx * ny
    t_fft = cc["c_fft"] * npx * np.log2(npx)
    t_el = cc["c_el"] * npx
    t_pot = n_mean * (cc["c_exp"] * (nx + ny) + 8.0 * cc["c_gemm"] * npx)
    per_e = 2 * t_fft + 4 * t_el
    per_f = per_e + 3 * t_fft + 6 * t_el + t_pot
    return (N - nonempty) * per_e + nonempty * per_f


def fmt_t(s):
    if s < 120:
        return f"{s:.0f} s"
    if s < 7200:
        return f"{s / 60:.0f} min"
    if s < 172800:
        return f"{s / 3600:.1f} h"
    return f"{s / 86400:.1f} d"


# ---- two-beam Bragg case (DERIVED_HERE; premises in the report section 2) -----------------------
def two_beam(k, sig, V0, Vg, th_ext, r, G):
    K2 = k ** 2 + 2 * k * sig * V0 * (1 + 1j * r)
    kz = k * np.cos(th_ext)
    kappa0 = np.sqrt(K2 - kz ** 2 + 0j)
    eta0 = kappa0 - G / 2
    c = 2 * k * sig * Vg * (1 + 1j * r) / G
    W = eta0 / c
    X = -(W - np.sqrt(W - 1) * np.sqrt(W + 1))
    q = -np.sqrt(eta0 - c) * np.sqrt(eta0 + c)
    return dict(K2=K2, kappa0=kappa0, eta0=eta0, c=c, X=X, q=q)


def X_of_eta(eta, c):
    W = eta / c
    return -(W - np.sqrt(W - 1) * np.sqrt(W + 1))


def green_closed(s, c, eta0):
    """Depth-equivalent Green's function g(s) = i J1(c s) exp(i eta0 s)/s, s = z tan(theta_int)."""
    s = np.asarray(s, float)
    return 1j * special.jv(1, c * s) * np.exp(1j * eta0 * s) / s


def green_numeric(s, c, eta0, P_mult=2000.0, dp_div=100.0):
    """(1/2 pi) integral X(eta0 - p) exp(i p s) dp by the trapezoid rule on [-P, P]."""
    ac = abs(c)
    P = P_mult * ac
    dp = ac / dp_div
    p = np.arange(-P, P + dp / 2, dp)
    Xp = X_of_eta(eta0 - p, c)
    out = []
    for sv in np.atleast_1d(s):
        w = Xp * np.exp(1j * p * sv)
        out.append((np.sum(w) - 0.5 * (w[0] + w[-1])) * dp / (2 * np.pi))
    return np.array(out), float(np.max(np.abs(Xp)))


def step_error(c, eta0, X, s_max, ds):
    """Relative error E(s)/X of the reflected field at distance s tan-scaled from a sharp
    illumination edge: E = X - i integral_0^s J1(c s') exp(i eta0 s')/s' ds'."""
    s = np.arange(0.0, s_max + ds / 2, ds)
    f = np.empty(s.shape, complex)
    f[0] = 1j * c / 2
    f[1:] = 1j * special.jv(1, c * s[1:]) * np.exp(1j * eta0 * s[1:]) / s[1:]
    R = np.concatenate([[0.0 + 0j], np.cumsum(0.5 * (f[1:] + f[:-1]) * ds)])
    return s, (X - R) / X


def run_length(s, E, eps):
    env = np.maximum.accumulate(np.abs(E)[::-1])[::-1]
    i = int(np.argmax(env <= eps))
    return float(s[i]) if env[i] <= eps else float("nan")


# ---- many-beam bookkeeping in the transverse reciprocal plane (g_z = 0) -------------------------
def transverse_beams(azimuth, lmax=24, kmax=12):
    out = []
    for l in range(-lmax, lmax + 1):
        for kk in range(-kmax, kmax + 1):
            hkl = (0, kk, l) if azimuth == "100" else (kk, -kk, l)
            gx = l / A
            gy = kk / A if azimuth == "100" else np.sqrt(2.0) * kk / A
            out.append((hkl, gx, gy))
    return out


def report(cal_path: Path, meas_path: Path) -> int:
    t_start = time.time()
    S = {}                                     # numbers carried between sections
    hdr("0. Run record")
    print(f"git {git_state()}; loadavg {loadavg()}; numpy {np.__version__}; nproc {os.cpu_count()}")
    print(f"calibration file {cal_path} (sha256 "
          f"{hashlib.sha256(cal_path.read_bytes()).hexdigest()[:16] if cal_path.exists() else 'MISSING'})")
    print(f"measurement file {meas_path} (sha256 "
          f"{hashlib.sha256(meas_path.read_bytes()).hexdigest()[:16] if meas_path.exists() else 'MISSING'})")

    # --------------------------------------------------------------------------------------------
    hdr("1. Beam, potential, (0,0,8) geometry")
    bc = beam_constants(E_KEV)
    k, sig, lam = bc["k_rad_per_A"], bc["sigma_rad_per_VA"], bc["wavelength_A"]
    print(f"200 keV (PROJECT_INPUT item 1): lambda = {lam:.8f} A, k = {k:.4f} rad/A, "
          f"sigma = {sig:.6e} rad/(V A) (DERIVED_HERE, engine physics.py)")
    check("lambda", abs(lam - 0.02507934) < 1e-8, f"{lam:.8f} vs 0.02507934 A (conventions)")
    check("k", abs(k - 250.5323) < 1e-4, f"{k:.4f} vs 250.5323 rad/A (conventions)")
    check("sigma", abs(sig - 7.28840e-4) < 1e-9, f"{sig:.6e} vs 7.28840e-4 (M2 section 4)")
    V0 = kirkland_mip()
    print(f"mean inner potential of the engine's potential (Kirkland IAM, 8 F(0)/a^3): "
          f"V0 = {V0:.6f} V (REPRODUCED: D3 F16 13.902842 V)")
    check("MIP", abs(V0 - 13.902842) < 1e-6, f"{V0:.6f} V vs D3 13.902842 V")
    th, th_int = theta_0008(V0)
    G = 2 * np.pi * 8 / A
    K = float(np.sqrt(k ** 2 + 2 * k * sig * V0))
    kap0 = K * np.sin(th_int)
    print(f"(0,0,8) with V0 = MIP: theta_ext = {th * 1e3:.4f} mrad, theta_int = {th_int * 1e3:.4f} "
          f"mrad (B32); G_008 = 2 pi 8/a = {G:.5f} rad/A; K sin(theta_int) = {kap0:.5f} rad/A")
    check("theta_T1", abs(th * 1e3 - 16.1347) < 1e-4 and abs(th_int * 1e3 - 18.4719) < 1e-4,
          f"{th * 1e3:.4f}/{th_int * 1e3:.4f} mrad vs T1 16.1347/18.4719")
    check("bragg_internal", abs(2 * kap0 / G - 1) < 1e-5, f"2 K sin(theta_int)/G - 1 = "
          f"{2 * kap0 / G - 1:.2e} (engine dispersion vs exact SM04 refraction)")
    tan_e = np.tan(th)
    fs = 1 / np.sin(th)
    ds_res = T2_IMAGE_RES_A / tan_e
    th_b19 = float(specular_condition_for((0, 0, 8), (0, 0, 1), E_keV=E_KEV, V0_V=12.0, a_A=A).theta_ext)
    print(f"foreshortening 1/sin(theta_ext) = {fs:.2f}; one image resolution element "
          f"({T2_IMAGE_RES_A} A, T2) = {ds_res:.1f} A of surface along the beam at this angle "
          f"(T2: {T2_IMAGE_RES_A / np.tan(th_b19):.1f} A at the B19 angle {th_b19 * 1e3:.4f} mrad)")
    check("T2_res_element", abs(T2_IMAGE_RES_A / np.tan(th_b19) - 364.0) < 0.5,
          f"{T2_IMAGE_RES_A / np.tan(th_b19):.2f} A vs T2 364 A")
    for nm, h in (("a/4", Q), ("a/2", 2 * Q)):
        print(f"shadow / blocked-view strip of an {nm} step: h/tan(theta_ext) = {h / tan_e:.1f} A")
    S.update(k=k, sig=sig, lam=lam, V0=V0, th=th, th_int=th_int, G=G, K=K, kap0=kap0,
             tan_e=tan_e, ds_res=ds_res)

    # --------------------------------------------------------------------------------------------
    hdr("2. Fourier coefficients of the engine's potential (Kirkland via abTEM, exact S_hkl)")
    for hkl in ((0, 0, 2), (0, 0, 6), (0, 0, 10)):
        check(f"forbidden_{hkl}", abs(structure_factor(hkl)) < 1e-9,
              f"|S{hkl}| = {abs(structure_factor(hkl)):.1e}")
    check("S_008", abs(structure_factor((0, 0, 8)) - 8) < 1e-9, "S(0,0,8) = 8")
    rows = [(0, 0, 0), (0, 0, 4), (0, 0, 8), (0, 0, 12), (0, 0, 16), (0, 0, 20), (0, 4, 4),
            (0, 2, 2), (0, 2, 6), (0, 4, 0), (0, 4, 8), (1, -1, 1), (1, -1, 3), (1, -1, 5),
            (1, -1, 7), (2, -2, 0), (2, -2, 4), (2, -2, 8)]
    u = U_RMS_ASSUMED_A
    for hkl in rows:
        V = V_hkl(hkl)
        g = np.sqrt(np.dot(hkl, hkl)) / A
        dw = np.exp(-2 * np.pi ** 2 * u ** 2 * g ** 2)
        print(f"  V{str(hkl):12s} |g| = {g:.4f} 1/A  |V| = {abs(V):.4f} V  arg {np.angle(V):+.4f}  "
              f"sigma|V| = {sig * abs(V):.4e} rad/A  DW(u={u} A) = {dw:.4f}")
    Vg = abs(V_hkl((0, 0, 8)))
    S["Vg"] = Vg
    dw8 = np.exp(-2 * np.pi ** 2 * u ** 2 * (8 / A) ** 2)
    print(f"V(0,0,8) = {Vg:.4f} V; with u = {u} A per axis (ASSUMPTION A7) the thermally averaged "
          f"coefficient is {Vg * dw8:.4f} V (factor {dw8:.4f}, intensity {dw8 ** 2:.4f})")
    check("V008_vs_M2", Vg > 0.84 * 1.2, f"engine V(0,0,8) = {Vg:.4f} V exceeds the M2 estimate "
          f"0.84 V by {100 * (Vg / 0.84 - 1):.0f} %")

    # --------------------------------------------------------------------------------------------
    hdr("3. Two-beam Bragg case (DERIVED_HERE; premises P1-P5 in the report)")
    ug = 2 * k * sig * Vg
    b = ug / G
    Lam = 1 / b
    xi = np.pi / (sig * Vg)
    Lb = 1 / (b * np.tan(th_int))
    print(f"u_g = 2 k sigma V_g = {ug:.5f} rad^2/A^2; b = u_g/G = {b:.5f} rad/A")
    print(f"penetration (amplitude 1/e depth at the stop-band centre, no absorption) Lambda = 1/b = "
          f"{Lam:.2f} A")
    print(f"extinction distance xi_g = pi/(sigma V_g) = {xi:.1f} A; along-surface build-up scale "
          f"L_b = 1/(b tan theta_int) = {Lb:.1f} A (= xi_g/pi x {Lb * sig * Vg:.5f})")
    print(f"M2 section 10.2 used V_g ~ 0.84 V: 1/(sigma 0.84 V) = {1 / (sig * 0.84):.0f} A "
          f"('~1600 A'); with the engine's own coefficient the two-beam scale is "
          f"{Lb:.0f} A ({100 * (Lb / (1 / (sig * 0.84)) - 1):+.0f} %)")
    check("Lb_identity", abs(Lb * sig * Vg - 1) < 2e-3, f"L_b sigma V_g - 1 = {Lb * sig * Vg - 1:.2e}"
          " (k/K and cos(theta) factors)")
    # exact two-beam root at the Bragg condition: [K^2 - (q - G/2)^2][K^2 - (q + G/2)^2] = u^2
    kx = G / 2
    # expand (kx^2 - (q - G/2)^2)(kx^2 - (q + G/2)^2) - ug^2 in q
    p1 = np.poly1d([-1, G, kx ** 2 - G ** 2 / 4])            # kx^2 - (q - G/2)^2
    p2 = np.poly1d([-1, -G, kx ** 2 - G ** 2 / 4])           # kx^2 - (q + G/2)^2
    roots = (p1 * p2 - ug ** 2).roots
    im = np.max(np.abs(roots.imag))
    check("two_beam_exact_root", abs(im / b - 1) < 1e-3, f"exact |Im q| = {im:.6f} vs b = {b:.6f}")
    Delta = refraction_delta(E_KEV, V0)
    dthi = 2 * b / (K * np.cos(th_int))
    dthe = dthi * (1 + Delta) * np.sin(th_int) * np.cos(th_int) / (np.sin(th) * np.cos(th))
    print(f"Darwin (total-reflection) full width, two-beam: {dthi * 1e3:.4f} mrad internal, "
          f"{dthe * 1e3:.4f} mrad external (Delta = {Delta:.4e})")
    S.update(b=b, Lam=Lam, xi=xi, Lb=Lb, dthe=dthe)
    for r in (0.0, 0.05, 0.10):
        tb = two_beam(k, sig, V0, Vg, th, r, G)
        print(f"  r = {r:.2f}: eta0 = {tb['eta0']:.3e} rad/A, c = {tb['c']:.4e}, "
              f"|X| = {abs(tb['X']):.4f}, arg X = {np.angle(tb['X']):+.4f} rad, "
              f"depth 1/|Im q| = {1 / abs(tb['q'].imag):.2f} A")
        S[f"tb_{r}"] = tb
    check("two_beam_total_reflection", abs(abs(S["tb_0.0"]["X"]) - 1) < 1e-4,
          f"|X| = {abs(S['tb_0.0']['X']):.6f} at the centre without absorption")

    # --------------------------------------------------------------------------------------------
    hdr("4. Many-beam bookkeeping at the (0,0,8) condition (transverse reciprocal plane, g_z = 0)")
    gvec = np.array([0, 0, 8])
    for azimuth in ("100", "110"):
        beams = transverse_beams(azimuth)
        terms = []
        for hkl, gx, gy in beams:
            if hkl == (0, 0, 0) or hkl == (0, 0, 8):
                continue
            Vh = V_hkl(hkl)
            Vgh = V_hkl(tuple(gvec - np.array(hkl)))
            if abs(Vh) < 1e-9 and abs(Vgh) < 1e-9:
                continue
            kxh = 2 * np.pi * gx - kap0
            zeta = (kap0 ** 2 - kxh ** 2 - (2 * np.pi * gy) ** 2) / (2 * K)
            terms.append(dict(hkl=hkl, gx=gx, gy=gy, Vh=Vh, Vgh=Vgh, zeta=zeta, kx=kxh,
                              alpha_y=2 * np.pi * abs(gy) / K,
                              exact=abs(zeta) < 1e-9))
        exact = [t for t in terms if t["exact"]]
        ok_terms = [t for t in terms if not t["exact"]]
        for t in ok_terms:
            t["admix"] = sig * (abs(t["Vh"]) + abs(t["Vgh"])) / abs(t["zeta"])
            t["off"] = sig * t["Vgh"] * t["Vh"] / t["zeta"]          # V (Bethe off-diagonal)
            t["diag"] = sig * abs(t["Vh"]) ** 2 / t["zeta"]          # V (Bethe diagonal)
        off = sum(t["off"] for t in ok_terms)
        diag = sum(t["diag"] for t in ok_terms)
        dshift = sig * diag / np.sin(th_int)                          # rad/A shift of the centre
        print(f"[{azimuth}] {len(terms)} beams with a coupling; exactly on the Ewald sphere: "
              f"{[t['hkl'] for t in exact]}")
        for t in exact:
            print(f"   EXACT {t['hkl']}: k_x(beam) = {t['kx']:+.2e} rad/A (surface-parallel inside), "
                  f"in-plane angle {t['alpha_y'] * 1e3:.2f} mrad, |V_h| = {abs(t['Vh']):.4f} V, "
                  f"|V_g-h| = {abs(t['Vgh']):.4f} V (sigma|V| {sig * abs(t['Vh']):.3e} vs "
                  f"sigma V_008 {sig * Vg:.3e} rad/A)")
        big = sorted(ok_terms, key=lambda t: -t["admix"])[:8]
        for t in big:
            print(f"   {str(t['hkl']):14s} zeta = {t['zeta']:+.4e} rad/A  admixture "
                  f"{t['admix']:.3f}  k_x = {t['kx']:+.3f} rad/A  angle_y = "
                  f"{t['alpha_y'] * 1e3:5.2f} mrad  Bethe off-diag {t['off'].real:+.4f} V")
        print(f"   sum of perturbative Bethe terms (exact beams excluded): V_eff = V_g - "
              f"{off.real:+.4f} V -> |V_eff|/V_g = {abs(Vg - off) / Vg:.3f}; centre shift "
              f"{dshift:+.4e} rad/A = {dshift / b:+.2f} half-widths b")
        for dxv in (0.13, 0.10):
            fm = 1 / (3 * dxv)
            inc = 0.0
            for t in ok_terms:
                fbx = t["gx"] - kap0 / (2 * np.pi)
                if (np.hypot(fbx, t["gy"]) <= fm and np.hypot(t["gx"], t["gy"]) <= fm
                        and np.hypot(8 / A - t["gx"], t["gy"]) <= fm):
                    inc += t["off"]
            print(f"   dx = {dxv} A (2/3 band {fm:.3f} 1/A): Bethe correction carried "
                  f"{inc.real:+.5f} of {off.real:+.5f} V (missing {abs(off - inc) / Vg:.2e} V_g)")
            S[f"bethe_missing_{azimuth}_{dxv}"] = abs(off - inc) / Vg
        alpha = max([t["alpha_y"] for t in exact] +
                    [t["alpha_y"] for t in ok_terms if t["admix"] >= 0.05])
        print(f"   largest in-plane angle of an exactly or strongly (admixture >= 0.05) excited "
              f"beam: alpha_y = {alpha * 1e3:.2f} mrad")
        S[f"alpha_y_{azimuth}"] = alpha
        S[f"exact_{azimuth}"] = [t["hkl"] for t in exact]
        S[f"Veff_ratio_{azimuth}"] = abs(Vg - off) / Vg
        S[f"shift_{azimuth}"] = dshift / b
    check("four_beam_100", set(S["exact_100"]) == {(0, 4, 4), (0, -4, 4)},
          f"exactly excited at [100]: {S['exact_100']}")
    check("no_exact_110", S["exact_110"] == [], f"exactly excited at [110]: {S['exact_110']}")

    # --------------------------------------------------------------------------------------------
    hdr("5. Absorption lengths of the TEST_ONLY proportional stand-ins (PROJECT_INPUT item 21)")
    for r in (0.05, 0.10):
        Lp = 1 / (sig * r * V0)
        Ls = 1 / (sig * r * (V0 - Vg))
        dr = np.sin(th_int) / (sig * r * V0)
        print(f"  r = {r:.2f}: V' = r V: mean imaginary potential {r * V0:.3f} V; amplitude 1/e "
              f"length along the path 1/(sigma r V0) = {Lp:.0f} A (intensity {Lp / 2:.0f} A); "
              f"slow (anomalous) two-beam transient 1/(sigma r (V0 - V_g)) = {Ls:.0f} A; depth "
              f"1/e of a refracted non-Bragg wave sin(theta_int)/(sigma r V0) = {dr:.1f} A")
        S[f"Lpath_{r}"], S[f"Lslow_{r}"] = Lp, Ls

    # --------------------------------------------------------------------------------------------
    hdr("6. Two-beam leading-edge transient (Green's function along the surface, DERIVED_HERE)")
    for r in (0.0, 0.10):
        tb = S[f"tb_{r}"]
        c, eta0 = tb["c"], tb["eta0"]
        sv = np.array([1.0, 3.0, 10.0, 30.0]) / abs(c)
        gn, xmax = green_numeric(sv, c, eta0)
        gc = green_closed(sv, c, eta0)
        err = float(np.max(np.abs(gn - gc)) / (abs(c) / 2))
        caus, _ = green_numeric(-sv[1:3], c, eta0)
        cz = float(np.max(np.abs(caus)) / (abs(c) / 2))
        check(f"green_closed_vs_numeric_r{r}", err < 2e-2 and xmax <= 1 + 1e-9,
              f"max |g_num - g_closed| = {err:.2e} of |c|/2; max |X(p)| = {xmax:.6f}")
        check(f"green_causal_r{r}", cz < 2e-2, f"|g_num(s < 0)| = {cz:.2e} of |c|/2")
    print("Relative error E of the reflected field at distance L downstream of a sharp illumination "
          "edge (two-beam, V_g = V(0,0,8)):")
    Lgrid = (1000, 2000, 3000, 5000, 10000, 20000, 50000)
    for r in (0.0, 0.05, 0.10):
        tb = S[f"tb_{r}"]
        s, E = step_error(tb["c"], tb["eta0"], tb["X"], s_max=6000.0, ds=0.25)
        L = s / np.tan(th_int)
        vals = "  ".join(f"{Lv}: {abs(E[np.argmin(np.abs(L - Lv))]):.1e}" for Lv in Lgrid)
        rl = {eps: run_length(s, E, eps) / np.tan(th_int) for eps in (1e-2, 3e-3, 1e-3)}
        print(f"  r = {r:.2f}: |E| at L (A) = {vals}")
        print(f"          envelope below 1e-2 / 3e-3 / 1e-3 beyond L = {rl[1e-2]:.0f} / "
              f"{rl[3e-3]:.0f} / {rl[1e-3]:.0f} A")
        S[f"tb_Lrun_{r}"] = rl
        if r == 0.0:
            for T in (20.0, 50.0):
                i0 = np.argmin(np.abs(s * tb["c"].real - T))
                i1 = np.argmin(np.abs(s * tb["c"].real - (T + 2 * np.pi)))
                env = np.max(np.abs(E[i0:i1]))
                asym = np.sqrt(2 / np.pi) * T ** -1.5
                check(f"tail_asymptote_T{T:.0f}", abs(env / asym - 1) < 0.1,
                      f"max |E| over one period at b s = {T}: {env:.3e} vs sqrt(2/pi) T^-1.5 = "
                      f"{asym:.3e}")
    return report_part2(S, cal_path, meas_path, t_start)


def slice_stats_parity(layer_counts_and_widths, n_crystal_slices):
    """[100], dz = a/4: every crystal slice holds one atomic plane; a (001) layer puts one atom per
    y period into every second slice (even layers into slices 0, 2 mod 4, odd layers into 1, 3), so
    a strip of `layers` layers and `wy` y periods puts ceil(layers/2) wy or floor(layers/2) wy atoms
    into a slice (DERIVED_HERE from DIAMOND_BASIS; checked against the builder below)."""
    n_max = sum(int(np.ceil(nl / 2)) * wy for nl, wy in layer_counts_and_widths)
    n_mean_crystal = sum(nl * wy / 2 for nl, wy in layer_counts_and_widths)
    return n_max, n_mean_crystal


def layers_kept(depth_below_A):
    """Layers of the LOWEST terrace kept by forward.cell.build_reflection_cell (x >= top - depth)."""
    return int(np.floor(depth_below_A / Q + 1e-9)) + 1


def layout_100(*, name, L_run, z_fov, y_A, D_clean, S, terraces_y=None, terraces_z=None,
               step_layers=0, ridge_A=0.0, trench_A=0.0, overlayer_A=0.0, feature_atoms=0,
               feature_slice_max=0):
    """Reflection-cell layout at the [100] azimuth (dz = a/4, in-plane period a).
    terraces_y: list of (extra layers, width in y periods) for edges parallel to the beam;
    terraces_z: list of (extra layers, length in z periods) for edges transverse (y periods from
    y_A). Returns the geometry, grid, slices, atoms and the engine-rule checks (DERIVED_HERE)."""
    th, th_int, tan_e = S["th"], S["th_int"], S["tan_e"]
    P, dz = A, A / 4
    ent = 10 * dz
    z_contact = GAP_A / tan_e
    L_exit = B29_MARGIN_RES * S["ds_res"]
    Lz_need = z_contact + L_run + z_fov + L_exit
    pz = int(np.ceil((Lz_need - ent) / P - 1e-9))
    Lz = ent + pz * P
    py = int(np.ceil(y_A / P - 1e-9))
    Ly = py * P
    h_step = step_layers * Q
    H = Lz * tan_e - GAP_A - h_step - 1.0
    vac_margin = float(np.ceil(H + Lz * tan_e + 1.0))
    vac = vac_margin + ridge_A + overlayer_A           # above the highest terrace top layer
    depth_below = BULK_ABSORBER_A + D_clean + trench_A
    ext_x = depth_below + h_step + vac + TOP_ABSORBER_A
    nx = fft_friendly(int(np.ceil(ext_x / MAX_PIXEL_A)))
    ny = fft_friendly(int(np.ceil(Ly / MAX_PIXEL_A)))
    N = int(round(Lz / dz))
    ncs = N - 10                                        # crystal slices (entrance slices empty)
    nl = layers_kept(depth_below)
    if terraces_y is not None:
        assert sum(w for _, w in terraces_y) == py
        strips = [(nl + m, w) for m, w in terraces_y]
        n_atoms = sum(2 * nlt * w * pz for nlt, w in strips)
        n_max, _ = slice_stats_parity(strips, ncs)
    else:
        assert sum(zl for _, zl in terraces_z) == pz
        n_atoms = sum(2 * (nl + m) * py * zl for m, zl in terraces_z)
        n_max = max(int(np.ceil((nl + m) / 2)) * py for m, _ in terraces_z)
    n_atoms += feature_atoms
    n_max += feature_slice_max
    n_mean = n_atoms / ncs
    # engine assertions (forward.cell.check_reflection_geometry), replicated
    s_lo, s_hi = depth_below, depth_below + h_step
    top_abs = ext_x - TOP_ABSORBER_A
    xb = s_hi + GAP_A
    ok = dict(
        item2_vacuum_margin=(top_abs - s_hi - ridge_A - overlayer_A) > H + Lz * tan_e,
        item3_beam_in_band=(xb >= s_hi) and (xb + H <= top_abs),
        item3_no_end_face=(xb - ent * tan_e) >= s_hi,
        item3_footprint=(Lz - ent >= H / tan_e) and ((xb + H - s_lo) / tan_e <= Lz),
        item4_buildup=(Lz - (xb - s_lo) / tan_e) >= D_ASSERT_A / np.tan(th_int),
        item4_depth=D_clean >= D_ASSERT_A,
        fov_lit=((GAP_A + H - EDGE_A) / tan_e) >= (Lz - L_exit) - 1e-6)
    return dict(name=name, Lz=Lz, Ly=Ly, ext_x=ext_x, pz=pz, py=py, H=H, vac=vac,
                depth_below=depth_below, nx=nx, ny=ny, N=N, nonempty=ncs, n_atoms=int(n_atoms),
                n_max=int(n_max), n_mean=n_mean, layers_low=nl, L_run=L_run, z_fov=z_fov,
                L_exit=L_exit, z_contact=z_contact, h_step=h_step, engine_rules=ok)


def report_part2(S, cal_path, meas_path, t_start) -> int:
    k, sig, V0, th, th_int, tan_e, Vg, b = (S["k"], S["sig"], S["V0"], S["th"], S["th_int"],
                                           S["tan_e"], S["Vg"], S["b"])
    # --------------------------------------------------------------------------------------------
    hdr("7. Engine measurements on flat strips (MEASURED_HERE, UNVALIDATED engine, TEST_ONLY inputs)")
    meas = json.loads(meas_path.read_text()) if meas_path.exists() else {"runs": {}}
    runs = meas["runs"]
    print(f"measurement file: created {meas.get('created_utc')}, git {meas.get('git')}, "
          f"loadavg start {meas.get('loadavg_start')} end {meas.get('loadavg_end')}")
    lam_ = S["lam"]
    print(f"read-out resolution: pass band 0.1 1/A -> 1/(2 x 0.1) = 5 A in x = {5.0 / tan_e:.0f} A "
          f"of surface; free-space diffraction between surface and exit plane sqrt(lambda D)/tan = "
          f"{np.sqrt(lam_ * 1000) / tan_e:.0f} A (D = 1000 A) to {np.sqrt(lam_ * 6000) / tan_e:.0f} A "
          f"(D = 6000 A); bins 500 A")
    need = [n for n, _ in MEASUREMENTS]
    check("measurements_present", all(n in runs for n in need),
          f"runs present: {sorted(runs)}; required: {need}")
    for name in need:
        if name not in runs or not name.startswith("bu_"):
            continue
        m = runs[name]
        inf, bu, dp = m["info"], m["buildup"], m["depth"]
        print(f"[{name}] azimuth [{inf['azimuth']}], r = {inf['absorption_ratio']}, crystal "
              f"{inf['L_z_A']:.0f} A long ({inf['L_after_contact_A']:.0f} A after first contact), "
              f"y {inf['extent_y_A']:.2f} A, clean depth {inf['clean_depth_A']} A; {inf['n_atoms']} "
              f"atoms, grid {inf['nx']}x{inf['ny']}, {inf['n_slices']} slices; run {m['run_s']:.0f} s"
              f" (loadavg after {m['loadavg_after']})")
        for q in bu["bins"]:
            print(f"    {q['start_A']:6.0f}-{q['end_A']:6.0f} A: |R| {q['R_abs']:.4f}  arg "
                  f"{q['R_arg']:+.4f}  |R|/|R_pl| - 1 = {q['amp_dev']:+.4f}  phase - phase_pl = "
                  f"{q['phase_dev']:+.4f}")
        print(f"    plateau {bu['plateau_A'][0]:.0f}-{bu['plateau_A'][1]:.0f} A: |R| "
              f"{bu['R_plateau_abs']:.4f} (|R|^2 = {bu['R_plateau_abs'] ** 2:.3f}, not reflected "
              f"{1 - bu['R_plateau_abs'] ** 2:.3f}), arg {bu['R_plateau_arg']:+.4f}; largest bin deviation "
              f"inside the plateau: phase {bu['plateau_max_phase_dev']:.4f} rad, amplitude "
              f"{bu['plateau_max_amp_dev']:.4f}")
        print(f"    converged (every later bin up to the plateau end within the tolerance) beyond: "
              f"phase 1e-2 rad {bu['converged_phase_1e_2_A']:.0f} A, 3e-3 rad "
              f"{bu['converged_phase_3e_3_A']:.0f} A; amplitude 1e-2 {bu['converged_amp_1e_2_A']:.0f}"
              f" A, 3e-2 {bu['converged_amp_3e_2_A']:.0f} A")
        dstr = ", ".join(f"{p['depth_A']:.0f}: {p['I']:.1e}" for p in dp["profile"][::2])
        print(f"    exit-plane intensity versus depth below the top layer (A: I): {dstr}")
        print(f"    deepest point with I > 1e-2 / 1e-4 / 1e-6: {dp['depth_I_below_1e-02_A']:.1f} / "
              f"{dp['depth_I_below_1e-04_A']:.1f} / {dp['depth_I_below_1e-06_A']:.1f} A")
        S[f"meas_{name}"] = m
    if "fp_100_r010" in runs:
        fp = runs["fp_100_r010"]
        rows_x = fp["region"].get("x_rows", fp["region"]["pixels"])   # v1 files stored x rows as "pixels"
        print(f"[fp_100_r010] region: surface distance {fp['region']['distance_A'][0]:.0f}-"
              f"{fp['region']['distance_A'][1]:.0f} A after contact, >= 5 A above the surface: "
              f"{rows_x} x-rows x {fp['info']['ny']} y-columns = {rows_x * fp['info']['ny']} pixels")
        print(f"[fp_100_r010] {fp['n_realisations']} frozen-phonon realisations, u = "
              f"{fp['u_rms_A']} A per axis ({fp['u_label']}), seed {fp['seed']}, aperture "
              f"{fp['aperture_mrad']} mrad = {fp['aperture_radius_per_A']:.4f} 1/A (B22): "
              f"variance/coherent intensity rho^2 = {fp['rho2']:.4e} (rho = "
              f"{fp['rho']:.4f}); arg(mean) - arg(static) = {fp['phase_mean_minus_static_rad']:+.4f}"
              f" rad; |mean|/|static| = {fp['amp_mean_over_static']:.4f}; "
              f"{np.mean(fp['times_s']):.0f} s per realisation")
        for rw in fp["rows"]:
            print(f"    {rw['start_A']:6.0f}-{rw['start_A'] + 500:6.0f} A: rho^2 {rw['rho2']:.3e}, "
                  f"|mean|/|static| {rw['amp_mean_over_static']:.4f}")
        S["fp"] = fp

    # comparison two-beam vs engine
    for r, nm in ((0.10, "bu_100_r010"), (0.05, "bu_100_r005"), (0.0, "bu_100_r000")):
        if f"meas_{nm}" in S:
            mb = S[f"meas_{nm}"]["buildup"]
            print(f"r = {r:.2f} [100]: two-beam run-in for 1e-2 rad {S[f'tb_Lrun_{r}'][1e-2]:.0f} A; "
                  f"engine phase converged within 1e-2 rad beyond {mb['converged_phase_1e_2_A']:.0f} "
                  f"A (plateau drift {mb['plateau_max_phase_dev']:.3f} rad); engine plateau |R| "
                  f"{mb['R_plateau_abs']:.3f} vs two-beam |X| {abs(S[f'tb_{r}']['X']):.3f}")

    # --------------------------------------------------------------------------------------------
    hdr("8. Sizing rules (DERIVED_HERE from sections 3-7 and the labelled stand-ins)")
    ds_res = S["ds_res"]
    M_up = B29_MARGIN_RES * ds_res
    L_exit = B29_MARGIN_RES * ds_res
    print(f"image resolution element {T2_IMAGE_RES_A} A = {ds_res:.1f} A of surface along the beam; "
          f"B29 margin {B29_MARGIN_RES} elements = {M_up:.1f} A upstream of every measured region; "
          f"exit margin L_exit = {L_exit:.1f} A")
    design = {}
    for r, nm in ((0.10, "bu_100_r010"), (0.05, "bu_100_r005"), (0.0, "bu_100_r000")):
        mm = S.get(f"meas_{nm}")
        tbL = S[f"tb_Lrun_{r}"][1e-2]
        if mm is not None:
            bu = mm["buildup"]
            conv_ok = (bu["plateau_max_phase_dev"] is not None
                       and bu["plateau_max_phase_dev"] <= EPS_PHASE
                       and bu["plateau_max_amp_dev"] <= 3e-2)
            Lm = (max(bu["converged_phase_1e_2_A"], bu["converged_amp_3e_2_A"]) if conv_ok
                  else float("nan"))
            Dm = mm["depth"]["depth_I_below_1e-04_A"]
            exit_bad = [q for q in bu["exit_bins"] if abs(q["phase_dev"]) > EPS_PHASE]
        else:
            conv_ok, Lm, Dm, exit_bad = False, float("nan"), float("nan"), []
        L_run = Lm if conv_ok else tbL
        src = "engine measurement" if conv_ok else "two-beam estimate (engine did not converge)"
        floor = mm is not None and Dm >= mm["info"]["clean_depth_A"] - 5.0
        if floor:
            # the 1e-4 depth reaches the bulk absorber: transmitted (non-Bragg) waves, not the
            # evanescent Bragg field, set the floor; the clean depth then follows the evanescent
            # part as measured with the weaker stand-in absorption, and the absorber must take the
            # transmitted wave (its reflectivity is untested, N-list)
            D_clean = design[0.05]["D_clean"]
            src_d = (f"floor of transmitted waves (I > 1e-4 down to {Dm:.0f} A, the absorber); "
                     f"evanescent part as for r = 0.05")
        else:
            D_clean = float(5 * np.ceil(Dm / 5)) if np.isfinite(Dm) else float("nan")
            src_d = "exit-plane intensity below 1e-4 (amplitude 1e-2), measured"
        design[r] = dict(L_run=L_run, L_run_src=src, D_clean=D_clean, L_tb=tbL, D_src=src_d,
                         tested_to=(mm["buildup"]["plateau_A"][1] if mm is not None else None))
        print(f"r = {r:.2f}: run-in L_run = {L_run:.0f} A ({src}: phase within 1e-2 rad AND "
              f"amplitude within 3e-2 of the plateau, tested to {design[r]['tested_to']:.0f} A; "
              f"two-beam phase estimate {tbL:.0f} A); clean depth D_clean = {D_clean:.0f} A "
              f"({src_d}); exit bins beyond the plateau worse than 1e-2 rad: "
              f"{[(q['start_A'], round(q['phase_dev'], 3)) for q in exit_bad]}")
    S["design"] = design
    alpha = S["alpha_y_100"]
    print(f"lateral spread angle at [100]: alpha_y = {alpha * 1e3:.2f} mrad (section 4)")
    for r in (0.10, 0.05, 0.0):
        d = design[r]
        d["dlat"] = d["L_run"] * np.tan(alpha) + B29_MARGIN_RES * T2_IMAGE_RES_A
        d["W_min"] = 2 * d["dlat"] + N_MEAS_RES * T2_IMAGE_RES_A
        print(f"r = {r:.2f}: lateral buffer from a step edge parallel to the beam dlat = L_run "
              f"tan(alpha_y) + {B29_MARGIN_RES} x {T2_IMAGE_RES_A} A = {d['dlat']:.1f} A; minimum "
              f"terrace width W_min = 2 dlat + {N_MEAS_RES} x {T2_IMAGE_RES_A} A = {d['W_min']:.1f} A")
    print("terrace widths from the miscut (ASSUMPTION scenarios for PROJECT_INPUT item 11): "
          "W = h/tan(miscut)")
    for md in MISCUTS_DEG:
        phi = np.radians(md)
        print(f"  miscut {md:.2f} deg = {phi * 1e3:.3f} mrad: single-layer (a/4) W = "
              f"{Q / np.tan(phi):7.1f} A; double-layer (a/2) W = {2 * Q / np.tan(phi):7.1f} A")
    print("overlayer scenarios (PROJECT_INPUT item 12; ASSUMPTION thicknesses; 0 = B26):")
    for t in OVERLAYERS_A:
        print(f"  t = {t:4.1f} A: adds {t:.1f} A to x; glancing path through it "
              f"2 t/sin(theta_ext) = {2 * t / np.sin(th):7.0f} A (in and out)")
    for kind in ("ridge", "trench"):
        ht = HalfTorus(center_y_A=0.0, center_z_A=0.0, major_radius_A=TORUS_R_A,
                       minor_radius_A=TORUS_r_A, kind=kind, label="ASSUMPTION B33/B34",
                       source="T2 geometric test size")
        yy = np.linspace(TORUS_R_A - TORUS_r_A, TORUS_R_A + TORUS_r_A, 4001)
        hmap = ht.layer_height_A(yy, np.zeros_like(yy), layer_spacing_A=Q)
        ext = float(hmap.max()) if kind == "ridge" else float(hmap.min())
        S[f"torus_{kind}_A"] = ext
        print(f"half-torus {kind} (R = {TORUS_R_A:.0f} A, r = {TORUS_r_A:.0f} A): layer-quantised "
              f"extreme {ext:+.3f} A; strip h/tan(theta_ext) = {abs(ext) / tan_e:.0f} A")
    check("torus_extremes_T2", abs(S["torus_ridge_A"] - 19.008) < 0.01
          and abs(S["torus_trench_A"] + 20.366) < 0.01,
          f"crest {S['torus_ridge_A']:.3f} A, floor {S['torus_trench_A']:.3f} A (T2: 19.01, -20.37)")
    nV = 8 / A ** 3 * np.pi ** 2 * TORUS_R_A * TORUS_r_A ** 2
    S["torus_nV"] = nV
    print(f"half-torus volume x density n V = {nV:.0f} atoms")

    # --------------------------------------------------------------------------------------------
    hdr("9. Sampling (2/3 band limit f_max = 1/(3 dx); DERIVED_HERE)")
    lam = S["lam"]
    reqs = [("incident beam, external", np.sin(th) / lam),
            ("specular beam inside (internal Bragg wave)", np.sin(th_int) / lam),
            ("(0,0,8) coupling g_008 (transmission function)", 8 / A),
            ("(0,+-4,4) coupling at [100] (exact beam)", np.sqrt(32) / A),
            ("(0,0,12) coupling / beam (0,0,16) f_x", 12 / A),
            ("(0,0,16) coupling", 16 / A)]
    for nm, f in reqs:
        print(f"  {nm:52s} f = {f:.4f} 1/A -> dx <= {1 / (3 * f):.4f} A")
    print(f"  engine check_band asserts only the beam angles: dx <= {1 / (3 * np.sin(th_int) / lam):.4f}"
          f" A passes although it drops the (0,0,8) coupling (needs dx <= {A / 24:.4f} A)")
    for dxv in (0.13, 0.10):
        fm = 1 / (3 * dxv)
        print(f"  dx = dy = {dxv} A: f_max = {fm:.4f} 1/A; F(f_max^2)/F(0) = "
              f"{float(kirkland_F(np.array([fm * fm]))[0] / kirkland_F(np.array([0.0]))[0]):.4f}; "
              f"Bethe correction of V(0,0,8) outside the band: [100] "
              f"{S[f'bethe_missing_100_{dxv}']:.1e}, [110] {S[f'bethe_missing_110_{dxv}']:.1e} of V_g")
    print(f"  slice thickness: [100] dz = a/4 = {A / 4:.6f} A (one atomic plane per slice), [110] "
          f"dz = p/4 = {A / np.sqrt(2) / 4:.6f} A (half the slices empty); both commensurate")

    # --------------------------------------------------------------------------------------------
    hdr("10. Frozen phonons (u = 0.076 A per axis: ASSUMPTION A7)")
    dphi = DPHI_FP
    if "fp" in S:
        rho2 = S["fp"]["rho2"]
        N_pix = int(np.ceil(rho2 / (2 * dphi ** 2)))
        print(f"measured rho^2 = {rho2:.4e}: realisations for {dphi} rad per resolution element "
              f"N = rho^2/(2 dphi^2) = {rho2 / (2 * dphi ** 2):.2f} -> {N_pix}; the static-lattice "
              f"phase differs from the ensemble-mean phase by "
              f"{S['fp']['phase_mean_minus_static_rad']:+.4f} rad (a systematic, not noise)")
        S["N_pix"] = N_pix
    else:
        S["N_pix"] = None

    # --------------------------------------------------------------------------------------------
    hdr("11. Rocking angles")
    w = S["dthe"]
    n_rock = int(round(2 * 1.5 * w / (w / 6))) + 1
    print(f"validation rocking curve (flat strip): range +-1.5 two-beam Darwin widths "
          f"(+-{1.5 * w * 1e3:.3f} mrad) at steps of 1/6 width ({w / 6 * 1e3:.4f} mrad): "
          f"{n_rock} angles (ASSUMPTION design)")
    S["n_rock"] = n_rock
    hmax = abs(S["torus_trench_A"])
    sig_pair = 3 * np.sqrt(2) * SIGMA_PHI_DOC03
    dtheta_max = (np.pi - sig_pair) / ((2 * np.pi / lam) * hmax * 2 * np.cos(th))
    n = 2
    while True:
        ds_ = 2 * np.cos(th) * dtheta_max
        sh = (lam / (2 * np.pi)) * SIGMA_PHI_DOC03 / (ds_ * np.sqrt(n * (n * n - 1) / 12))
        if sh <= SIGMA_H_TARGET_A:
            break
        n += 1
    print(f"B16 for the half-torus (h_max = {hmax:.2f} A, sigma_phi = {SIGMA_PHI_DOC03} rad per "
          f"hologram, docs/03 example): largest tilt step {dtheta_max * 1e3:.4f} mrad; {n} "
          f"equally spaced angles ({(n - 1) * dtheta_max * 1e3:.3f} mrad) give sigma_h <= "
          f"{SIGMA_H_TARGET_A} A (slope standard error {sh:.3f} A)")
    S["n_b16"] = n
    print("atomic steps (a/4, a/2): branch from the lattice constraint (B29): 1 angle")
    return report_part3(S, cal_path, meas_path, t_start)


def _stats_from_cell(cell, dz):
    idx = np.floor((np.asarray(cell.atoms_xyz_A)[:, 2] + 1e-9) / dz).astype(np.int64)
    n = int(round(cell.length_z_A / dz))
    counts = np.bincount(np.clip(idx, 0, n - 1), minlength=n)
    return counts


def report_part3(S, cal_path, meas_path, t_start) -> int:
    th, tan_e = S["th"], S["tan_e"]
    # --------------------------------------------------------------------------------------------
    hdr("12. Cost model: replica of engine.estimate_resources, checked against the engine")
    cal = json.loads(cal_path.read_text())
    cc = cpu_constants(cal)
    print(f"CPU calibration {cal['created_utc']} (loadavg {cal['loadavg']}, {cal['threads']} "
          f"threads, {cal['precision']}): c_fft = {cc['c_fft']:.3e} s/(px log2 px), element-wise "
          f"{cc['c_el']:.3e} s/px, exp {cc['c_exp']:.3e} s/element, GEMM "
          f"{1 / cc['c_gemm'] / 1e9:.0f} GFLOP/s (medians; FFT and element-wise from grids >= 1e6 px)")
    print(f"GPU model: engine.GPU_ASSUMED = {GPU_ASSUMED['label']}")
    # (a) every study.yaml point, built here with the M2 case code, estimate_resources vs replica
    sys.path.insert(0, str(REPO / "tests" / "forward"))
    import yaml
    from null_test_cases import step_case, theta_0008 as nt_theta, translation_pair
    study = yaml.safe_load((REPO / "scripts" / "hpc" / "null_test_study" / "study.yaml").read_text())
    tot = dict(cpu=0.0, gpu=0.0, mem=0)
    all_ok = True
    for p in study["points"]:
        thp = nt_theta() if p["theta"] == "bragg_0008_mip" else float(p["theta"]) * 1e-3
        ab = PhysicalAbsorption(model="proportional", ratio=float(p["absorption_ratio"]),
                                label=p["absorption_label"])
        if p["kind"].startswith("translation"):
            pair = translation_pair(theta=thp, width_periods=int(p["width_periods"]),
                                    extra_A=float(p["extra_length_A"]), absorption=ab,
                                    precision=p["precision"],
                                    move_beam=p["kind"] == "translation_moved_beam")
            cell, params, nrun = pair["A"][0], pair["params"], 2
        else:
            cell, _, _, params = step_case(theta=thp, width_periods=int(p["width_periods"]),
                                           extra_A=float(p["extra_length_A"]), absorption=ab,
                                           precision=p["precision"])
            nrun = 1
        est = estimate_resources(cell, params, realisations=nrun, calibrate_cpu=False)
        g = est["grid"]
        arrays, mem = replica_memory(g["nx"], g["ny"], est["atoms_per_slice_max"], est["n_atoms"],
                                     precision=params.precision)
        gpu = nrun * replica_gpu_s(g["nx"], g["ny"], est["n_slices"], est["nonempty_slices"],
                                   est["atoms_per_nonempty_slice_mean"], params.precision)
        cpu = 1.5 * nrun * replica_cpu_s(g["nx"], g["ny"], est["n_slices"], est["nonempty_slices"],
                                         est["atoms_per_nonempty_slice_mean"], cc)
        m2 = M2_STUDY[p["name"]]
        same = (mem == est["memory_bytes"]["total"]
                and abs(gpu / est["gpu"]["seconds_total"] - 1) < 1e-12)
        vs_m2 = ((g["nx"], g["ny"], est["n_slices"], est["n_atoms"]) == m2[:4]
                 and round(mem / 1e6) == m2[4] and abs(round(gpu, 1) - m2[6]) < 0.051)
        all_ok &= same and vs_m2
        tot["cpu"] += cpu
        tot["gpu"] += gpu
        tot.setdefault("ratios_m2", []).append(cpu / m2[5])
        for key, val in (("x", cell.extent_x_A), ("y", cell.extent_y_A), ("z", cell.length_z_A),
                         ("atoms", est["n_atoms"]), ("slices", est["n_slices"])):
            lo, hi = tot.get(key, (val, val))
            tot[key] = (min(lo, val), max(hi, val))
        tot["mem"] = max(tot["mem"], mem)
        print(f"  {p['name']:26s} grid {g['nx']}x{g['ny']}, {est['n_slices']} slices, "
              f"{est['n_atoms']} atoms, {mem / 1e6:.1f} MB, GPU {gpu:.2f} s (engine "
              f"{est['gpu']['seconds_total']:.2f}), CPU x1.5 {cpu:.0f} s (M2 printed {m2[5]} s); "
              f"replica==engine {same}, ==M2 {vs_m2}")
        del cell, params
    check("replica_equals_engine_and_M2_on_17_study_points", all_ok,
          "memory bytes and GPU seconds identical to estimate_resources; grid, slices, atoms, MB "
          "and GPU s identical to the M2 printout")
    S["study_tot"] = tot
    print(f"  replica CPU (x1.5) / M2 printed CPU on the 17 points: {min(tot['ratios_m2']):.2f} to "
          f"{max(tot['ratios_m2']):.2f}")
    print(f"  study.yaml total: CPU (x1.5) {fmt_t(tot['cpu'])} on 4 cores, GPU (ASSUMPTION model) "
          f"{tot['gpu']:.0f} s; largest engine arrays {tot['mem'] / 1e6:.0f} MB")
    # (b) a [100] staircase cell of the production layout at reduced width, built with every
    #     builder assertion and checked by the engine's reflection_setup; counts vs the formulas
    d = S["design"][0.10]
    lay = layout_100(name="check", L_run=d["L_run"], z_fov=B29_MARGIN_RES * S["ds_res"] +
                     N_MEAS_RES * S["ds_res"], y_A=10 * A, D_clean=d["D_clean"], S=S,
                     terraces_y=[(0, 5), (1, 5)], step_layers=1)
    one = build_si001_terraces(
        azimuth_uvw=(1, 0, 0), azimuth_label=AZ_LABEL["100"],
        staircase=Staircase(edges="parallel", terrace_layers=(0, 1), terrace_widths=(5, 5),
                            boundary_step_layers=-1),
        edge_periods=1, substrate_layers=int(np.ceil(lay["depth_below"] / Q)) + 2,
        first_terrace_backbond_uvw=(1, 1, 0), termination="bulk", overlayer=None,
        vacuum_above_A=10.0, lattice_parameter_A=A, lattice_parameter_label="ASSUMPTION B2")
    n1 = one.n_atoms
    pz = lay["pz"]
    pos = np.tile(one.positions_A, (pz, 1))
    pos[:, 2] += np.repeat(np.arange(pz), n1) * A
    cA = one.cell_A.copy()
    cA[2, 2] = pz * A
    md = dict(one.metadata)
    md["positions_sha256"] = hashlib.sha256(np.ascontiguousarray(pos, "<f8").tobytes()).hexdigest()
    s_t = dataclasses.replace(one, positions_A=pos, species=np.tile(one.species, pz), cell_A=cA,
                              layer_index=np.tile(one.layer_index, pz),
                              terrace_index=np.tile(one.terrace_index, pz), metadata=md)
    cell = build_reflection_cell(s_t, vacuum_above_A=lay["vac"], depth_below_A=lay["depth_below"],
                                 bulk_absorber_A=BULK_ABSORBER_A, top_absorber_A=TOP_ABSORBER_A,
                                 entrance_vacuum_z_A=10 * A / 4)
    pot = AtomicPotential(cell, parameterisation="kirkland",
                          physical_absorption=PhysicalAbsorption(
                              model="proportional", ratio=0.1,
                              label="TEST_ONLY: stands in for PROJECT_INPUT item 21"),
                          frozen_phonons=None, static_lattice_label="ASSUMPTION: static lattice")
    xs_hi = cell.metadata["layout"]["highest_surface_x_A"]
    beam = SheetBeam(height_A=lay["H"], edge_A=EDGE_A, x_bottom_A=xs_hi + GAP_A,
                     theta_in_ext_rad=th, theta_label=THETA_LABEL)
    params = MultisliceParams(energy_keV=E_KEV, nx=lay["nx"], ny=lay["ny"], dz_A=A / 4,
                              propagator="exact", band_limit="2/3", backend="numpy",
                              precision="complex64", threads=4,
                              absorber=NumericalAbsorber(strength_V=ABSORBER_V, profile="sin2"),
                              theta_out_ext_rad=th, buildup_depth_A=D_ASSERT_A)
    from reflection_holo.forward.multislice import reflection_setup
    setup = reflection_setup(cell, potential=pot, beam=beam, params=params)
    est = estimate_resources(cell, params, realisations=1, calibrate_cpu=True)
    _, mem = replica_memory(lay["nx"], lay["ny"], lay["n_max"], lay["n_atoms"])
    same_counts = (est["n_atoms"] == lay["n_atoms"] and est["n_slices"] == lay["N"]
                   and est["nonempty_slices"] == lay["nonempty"]
                   and est["atoms_per_slice_max"] == lay["n_max"]
                   and abs(est["atoms_per_nonempty_slice_mean"] - lay["n_mean"]) < 1e-9
                   and abs(cell.extent_x_A - lay["ext_x"]) < 1e-6
                   and (est["grid"]["nx"], est["grid"]["ny"]) == (lay["nx"], lay["ny"]))
    check("layout_formulas_vs_built_100_cell", same_counts and mem == est["memory_bytes"]["total"],
          f"built: {est['n_atoms']} atoms, {est['n_slices']} slices ({est['nonempty_slices']} "
          f"non-empty), n_max {est['atoms_per_slice_max']}, extent_x {cell.extent_x_A:.3f} A; "
          f"formulas: {lay['n_atoms']}, {lay['N']} ({lay['nonempty']}), {lay['n_max']}, "
          f"{lay['ext_x']:.3f} A")
    passed = all(v["passed"] for kk, v in setup["geometry"].items() if isinstance(v, dict))
    check("engine_reflection_setup_passes_layout", passed and all(lay["engine_rules"].values()),
          f"engine geometry checks {[kk for kk, v in setup['geometry'].items() if isinstance(v, dict)]}"
          f" all passed; replicated rules {lay['engine_rules']}")
    comp = est["cpu"]
    pe = 2 * comp["fft_s"] + 4 * comp["elementwise_pass_s"]
    pf = pe + 3 * comp["fft_s"] + 6 * comp["elementwise_pass_s"] + comp["potential_slice_s"]
    tot_formula = (lay["N"] - lay["nonempty"]) * pe + lay["nonempty"] * pf
    check("cpu_formula_replica_equals_engine",
          abs(tot_formula / comp["seconds_per_realisation"] - 1) < 1e-12,
          f"the replica's composition of the engine's own measured components gives "
          f"{tot_formula:.3f} s = estimate_resources {comp['seconds_per_realisation']:.3f} s")
    npx = lay["nx"] * lay["ny"]
    m_fft = cc["c_fft"] * npx * np.log2(npx)
    m_el = cc["c_el"] * npx
    m_pot = lay["n_mean"] * (cc["c_exp"] * (lay["nx"] + lay["ny"]) + 8 * cc["c_gemm"] * npx)
    cpu_rep = replica_cpu_s(lay["nx"], lay["ny"], lay["N"], lay["nonempty"], lay["n_mean"], cc)
    print(f"  observation (grid {lay['nx']}x{lay['ny']}, {lay['N']} slices, loadavg now {loadavg()}): "
          f"engine-measured / calibrated component: FFT {comp['fft_s'] / m_fft:.2f}, element-wise "
          f"{comp['elementwise_pass_s'] / m_el:.2f}, potential slice {comp['potential_slice_s'] / m_pot:.2f};"
          f" total {comp['seconds_per_realisation']:.0f} s vs calibrated replica {cpu_rep:.0f} s "
          f"(both without x1.5)")
    del cell, pot, s_t, pos
    # (c) the measured engine runs against the CPU replica
    for name in [n for n, _ in MEASUREMENTS]:
        m = S.get(f"meas_{name}") or (S.get("fp") if name.startswith("fp") else None)
        if m is None:
            continue
        inf = m["info"]
        az = inf["azimuth"]
        ncs = inf["n_slices"] - 10
        nonempty = ncs if az == "100" else ncs // 2
        rep = replica_cpu_s(inf["nx"], inf["ny"], inf["n_slices"], nonempty,
                            inf["n_atoms"] / nonempty, cc)
        meas_s = m["run_s"] if "run_s" in m else float(np.mean(m["times_s"]))
        L1 = float(m["loadavg_after"][0])
        norm = meas_s / rep / max(1.0, L1 / 4.0)
        print(f"  measured run {name}: {meas_s:.0f} s per realisation vs replica {rep:.0f} s "
              f"(ratio measured/replica {meas_s / rep:.2f}; 1-min load after the run {L1:.2f}; "
              f"ratio divided by max(1, load/4) = {norm:.2f}); x1.5 replica {1.5 * rep:.0f} s")
        S.setdefault("cpu_ratios", []).append(meas_s / rep)
        S.setdefault("cpu_ratios_norm", []).append(norm)
        S.setdefault("cpu_loads", []).append(L1)
    if S.get("cpu_ratios"):
        rmin, rmax = min(S["cpu_ratios"]), max(S["cpu_ratios"])
        check("cpu_replica_is_lower_bound_of_measured_runs", rmin >= 0.9,
              f"measured/replica {rmin:.2f} to {rmax:.2f}: the replica counts only FFT, element-wise "
              f"and potential-slice operations and was calibrated at load 0.36, so no measured run "
              f"may be faster (tolerance 0.9)")
        print(f"  observation: measured/replica {rmin:.2f} to {rmax:.2f} under 1-min loads of "
              f"{min(S['cpu_loads']):.2f} to {max(S['cpu_loads']):.2f} on 4 cores; divided by "
              f"max(1, load/4): {min(S['cpu_ratios_norm']):.2f} to "
              f"{max(S['cpu_ratios_norm']):.2f}. The x1.5 factor of run_study.py (used in every CPU "
              f"time below) lies inside that range")
    return report_part4(S, cc, t_start)


N_FP_MIN = 8   # ASSUMPTION: fewest frozen-phonon realisations (to estimate the ensemble variance)


def torus_slice_area_max(R, r):
    """Largest area (A^2) of the half-torus cross-section in a plane z = const (DERIVED_HERE,
    numerical): A(z) = integral dy sqrt(max(0, r^2 - (rho - R)^2)), rho = sqrt(y^2 + z^2)."""
    y = np.linspace(-(R + r), R + r, 400001)
    dy = y[1] - y[0]
    best = 0.0
    for z in np.linspace(R - r, R + r, 801):
        rho = np.hypot(y, z)
        best = max(best, float(np.sum(np.sqrt(np.clip(r * r - (rho - R) ** 2, 0, None))) * dy))
    return best


# host bytes per atom, from reading the code (DERIVED_HERE, not measured): structure object
# (si001.Si001Structure: positions f8 x3, species '<U2', layer_index i8, terrace_index i8), cell
# (forward.cell: atoms_xyz_A f8 x3, Z i8), realised potential (potentials._RealisedAtomic: sorted
# xyz f8 x3, idx_sorted i8, Z i8) and its transients in __init__ (xyz copy, idx, order, offsets,
# the tobytes() copy for the hash; with frozen phonons also the noise array and the displaced copy)
HOST_B_PER_ATOM = dict(structure=24 + 8 + 8 + 8, cell=24 + 8, realised=24 + 8 + 8,
                       init_transient_static=24 + 8 + 8 + 8 + 24, init_transient_phonon_extra=24 + 24)


def split_times(nx, ny, N, nonempty, n_mean, cc, precision="complex64"):
    """(FFT + element-wise, potential construction) seconds per realisation for the CPU replica
    (without x1.5) and the GPU model, to show which term dominates."""
    npx = nx * ny
    t_fft = cc["c_fft"] * npx * np.log2(npx)
    t_el = cc["c_el"] * npx
    t_pot = n_mean * (cc["c_exp"] * (nx + ny) + 8.0 * cc["c_gemm"] * npx)
    cpu = ((N - nonempty) * (2 * t_fft + 4 * t_el) + nonempty * (5 * t_fft + 10 * t_el), nonempty * t_pot)
    g = GPU_ASSUMED
    cb = np.dtype(precision).itemsize
    tf = max(g["launch_s"], 2 * cb * npx * np.log2(max(npx, 2)) / 4 / (g["bandwidth_Bps"] * g["fft_efficiency"]))
    te = max(g["launch_s"], 3 * cb * npx / g["bandwidth_Bps"])
    tp = max(g["launch_s"], 8.0 * npx * n_mean / g["gemm_flops"])
    gpu = ((N - nonempty) * (2 * tf + 4 * te) + nonempty * (5 * tf + 10 * te), nonempty * tp)
    return cpu, gpu


def report_part4(S, cc, t_start) -> int:
    th, tan_e, ds_res = S["th"], S["tan_e"], S["ds_res"]
    hb = HOST_B_PER_ATOM
    persistent = hb["structure"] + hb["cell"] + hb["realised"]
    peak_s = persistent + hb["init_transient_static"]
    peak_p = peak_s + hb["init_transient_phonon_extra"]
    print(f"host memory per atom (code reading, DERIVED_HERE, not measured): persistent {persistent} B "
          f"(structure {hb['structure']}, cell {hb['cell']}, realised potential {hb['realised']}); "
          f"peak while realising {peak_s} B (static) / {peak_p} B (frozen phonons); the engine's "
          f"own accounting (estimate_resources) counts 48 B per atom")
    print(f"structure builders (reports M2, T1): si001 builder ~4.7 GB per 84 000 atoms = "
          f"{4.7e9 / 84000 / 1e3:.0f} kB/atom (M2 10.5); feature builder 1.33 GB for 547 662 atoms = "
          f"{1.33e9 / 547662 / 1e3:.1f} kB/atom (T1 section 4); tiling one verified z period is exact "
          f"only for a crystal periodic along the beam (edges parallel)")
    S["host_peak"] = (peak_s, peak_p)
    hdr("13. Scenarios ([100] azimuth B20, (0,0,8) at the MIP angle, complex64, dx = dy <= 0.13 A)")
    M = B29_MARGIN_RES * ds_res
    meas_len = N_MEAS_RES * ds_res
    rows = []

    def add(label, lay, n_real, n_ang, note, precision="complex64"):
        arrays, mem = replica_memory(lay["nx"], lay["ny"], lay["n_max"], lay["n_atoms"],
                                     precision=precision)
        gpu = replica_gpu_s(lay["nx"], lay["ny"], lay["N"], lay["nonempty"], lay["n_mean"],
                            precision)
        cpu = 1.5 * replica_cpu_s(lay["nx"], lay["ny"], lay["N"], lay["nonempty"], lay["n_mean"], cc)
        host = arrays["atom positions (float64)"]
        ok = all(lay["engine_rules"].values())
        check(f"engine_rules_{label}", ok, f"{lay['engine_rules']}")
        row = dict(label=label, lay=lay, mem=mem, dev=mem - host, gpu=gpu, cpu=cpu, n_real=n_real,
                   n_ang=n_ang, note=note, exit_bytes=8 * lay["nx"] * lay["ny"])
        rows.append(row)
        print(f"[{label}] {note}")
        print(f"    extents x {lay['ext_x']:.1f} A (depth below the lowest top layer "
              f"{lay['depth_below']:.1f}, vacuum {lay['vac']:.0f}, sheet beam H {lay['H']:.1f}), "
              f"y {lay['Ly']:.1f} A ({lay['py']} periods), z {lay['Lz']:.1f} A ({lay['pz']} "
              f"periods; contact {lay['z_contact']:.0f} + run-in {lay['L_run']:.0f} + field "
              f"{lay['z_fov']:.0f} + exit {lay['L_exit']:.0f})")
        vac_phys = max(GAP_A + lay["H"], lay["Lz"] * tan_e) + EDGE_A
        ext_phys = lay["ext_x"] - (float(np.ceil(lay["H"] + lay["Lz"] * tan_e + 1.0)) - vac_phys)
        print(f"    vacuum: engine rule (item 2) H + L_z tan(theta) -> {lay['vac']:.0f} A; physical "
              f"need max(gap + H, L_z tan(theta)) + edge = {vac_phys:.0f} A (DERIVED_HERE: incident "
              f"sheet at the entrance, reflected sheet at the exit plane; diffraction spread not "
              f"included); extent_x would be {ext_phys:.0f} A instead of {lay['ext_x']:.0f} A "
              f"({100 * (ext_phys / lay['ext_x'] - 1):+.0f} %)")
        print(f"    atoms {lay['n_atoms']:,}; grid {lay['nx']} x {lay['ny']} "
              f"(dx {lay['ext_x'] / lay['nx']:.4f}, dy {lay['Ly'] / lay['ny']:.4f} A); slices "
              f"{lay['N']} (non-empty {lay['nonempty']}, atoms per slice max {lay['n_max']}, mean "
              f"{lay['n_mean']:.0f})")
        print(f"    engine arrays {mem / 1e9:.3f} GB per realisation (device part {(mem - host) / 1e9:.3f}"
              f" GB, atom positions {host / 1e9:.3f} GB); exit wave {row['exit_bytes'] / 1e9:.3f} GB")
        (cf, cp), (gf, gp) = split_times(lay["nx"], lay["ny"], lay["N"], lay["nonempty"],
                                         lay["n_mean"], cc, precision)
        print(f"    per realisation: CPU {fmt_t(cpu)} (4 cores, replica x1.5; FFT+element-wise "
              f"{100 * cf / (cf + cp):.0f} %, potential construction {100 * cp / (cf + cp):.0f} %), "
              f"GPU {fmt_t(gpu)} (ASSUMPTION model; potential construction "
              f"{100 * gp / (gf + gp):.0f} %); x {n_real} realisations x {n_ang} angles = CPU "
              f"{fmt_t(cpu * n_real * n_ang)}, GPU {fmt_t(gpu * n_real * n_ang)}; exit waves "
              f"{row['exit_bytes'] * n_real * n_ang / 1e9:.1f} GB; host memory (code reading) "
              f"{lay['n_atoms'] * S['host_peak'][1] / 1e9:.1f} GB peak with frozen phonons")
        return row

    d10, d05, d00 = S["design"][0.10], S["design"][0.05], S["design"][0.0]
    N_pix = S.get("N_pix") or 0

    def n_terr(window_y_A):
        n_el = max(1.0, N_MEAS_RES * window_y_A / T2_IMAGE_RES_A)
        return max(N_FP_MIN, int(np.ceil(N_pix / n_el))), n_el

    # --- (2a) edges parallel to the beam, periodic up-down staircase -----------------------------
    def s2a(label, step_layers, W_A, d, note):
        py_half = int(np.ceil(W_A / A - 1e-9))
        lay = layout_100(name=label, L_run=d["L_run"], z_fov=M + meas_len, y_A=2 * py_half * A,
                         D_clean=d["D_clean"], S=S, terraces_y=[(0, py_half), (step_layers, py_half)],
                         step_layers=step_layers)
        win = py_half * A - 2 * d["dlat"]
        nr, n_el = n_terr(max(win, 0.0))
        note += (f"; W = {py_half * A:.1f} A vs W_min {d['W_min']:.1f} A; measuring window "
                 f"{win:.1f} A x {meas_len:.0f} A = {n_el:.0f} resolution elements")
        return add(label, lay, nr, 1, note)

    for md_, sl in ((0.1, 1), (0.5, 1)):
        W = sl * Q / np.tan(np.radians(md_))
        s2a(f"2a_a4_miscut{md_}_r0.10", sl, W, d10,
            f"a/4 steps parallel to the beam, miscut {md_} deg (ASSUMPTION), r = 0.10 TEST_ONLY")
    W = Q / np.tan(np.radians(0.1))
    s2a("2a_a4_miscut0.1_r0.05", 1, W, dict(d05, dlat=d05["dlat"], W_min=d05["W_min"]),
        "a/4 steps parallel to the beam, miscut 0.1 deg (ASSUMPTION), r = 0.05 TEST_ONLY")
    s2a("2a_a2_miscut0.1_r0.10", 2, 2 * Q / np.tan(np.radians(0.1)), d10,
        "a/2 steps parallel to the beam, miscut 0.1 deg (ASSUMPTION), r = 0.10 TEST_ONLY")
    s2a("2a_a4_Wmin_r0.10", 1, d10["W_min"], d10,
        "a/4 steps parallel to the beam, narrowest converged terrace W_min, r = 0.10 TEST_ONLY")
    if np.isfinite(d00["D_clean"]):
        s2a("2a_a4_miscut0.1_r0.00", 1, W, d00,
            f"a/4 steps parallel to the beam, miscut 0.1 deg, NO absorption (B30 ASSUMPTION); "
            f"run-in {d00['L_run']:.0f} A from the {d00['L_run_src']} (two-beam tail "
            f"{d00['L_tb']:.0f} A)")
    # --- (2b) edges transverse to the beam -------------------------------------------------------
    t_min = (2 * B29_MARGIN_RES + N_MEAS_RES) * ds_res
    print(f"steps transverse to the beam: each terrace >= {2 * B29_MARGIN_RES + N_MEAS_RES} "
          f"resolution elements = {t_min:.0f} A along the beam; a vicinal surface gives that only for "
          f"miscut <= {np.degrees(np.arctan(Q / t_min)):.4f} deg (a/4 steps) or "
          f"{np.degrees(np.arctan(2 * Q / t_min)):.4f} deg (a/2 steps)")
    for sl, nm in ((2, "a2"), (1, "a4")):
        strip = sl * Q / tan_e
        z_fov = M + meas_len + M + strip + M + meas_len
        L_exit = M
        Lz_need = GAP_A / tan_e + d10["L_run"] + z_fov + L_exit
        pz = int(np.ceil((Lz_need - 10 * A / 4) / A - 1e-9))
        z_step = GAP_A / tan_e + d10["L_run"] + M + meas_len + M + strip - 10 * A / 4
        pz1 = int(np.ceil(z_step / A))
        lay = layout_100(name=f"2b_{nm}", L_run=d10["L_run"], z_fov=z_fov, y_A=16 * A,
                         D_clean=d10["D_clean"], S=S, terraces_z=[(0, pz1), (sl, pz - pz1)],
                         step_layers=sl)
        nr, n_el = n_terr(16 * A)
        add(f"2b_{nm}_transverse_r0.10", lay, nr, 1,
            f"one {nm.replace('a', 'a/')} up-step transverse to the beam, terraces "
            f"{pz1 * A:.0f} A and {(pz - pz1) * A:.0f} A along the beam (>= 8 resolution elements "
            f"each), y = 16 a, r = 0.10 TEST_ONLY; strip {strip:.0f} A; {n_el:.0f} resolution "
            f"elements per measuring region")
    # --- (3) half-torus, R = 1000 A, r = 20 A, ridge and trench in one cell size ---------------
    amax = torus_slice_area_max(TORUS_R_A, TORUS_r_A)
    fmax = int(np.ceil(8 / A ** 3 * (A / 4) * amax))
    print(f"half-torus: largest cross-section in one slice {amax:.0f} A^2 -> at most {fmax} extra "
          f"atoms per slice (ridge)")
    for r, d in ((0.10, d10), (0.05, d05)):
        crest, floor = S["torus_ridge_A"], abs(S["torus_trench_A"])
        strip = max(crest, floor) / tan_e
        z_fov = M + strip + 2 * (TORUS_R_A + TORUS_r_A) + strip
        y_A = 2 * (TORUS_R_A + TORUS_r_A) + 2 * d["dlat"] + N_MEAS_RES * T2_IMAGE_RES_A
        py = int(np.ceil(y_A / A - 1e-9))
        lay = layout_100(name=f"3_torus_r{r}", L_run=d["L_run"], z_fov=z_fov, y_A=py * A,
                         D_clean=d["D_clean"], S=S, terraces_z=None,
                         terraces_y=[(0, py)], ridge_A=crest, trench_A=floor,
                         feature_atoms=int(round(S["torus_nV"])), feature_slice_max=fmax)
        add(f"3_torus_R1000_r20_r{r:.2f}", lay, max(N_FP_MIN, N_pix), 1,
            f"half-torus ridge or trench (B33/B34), one cell size for both (depth + {floor:.2f} A, "
            f"vacuum + {crest:.2f} A), r = {r:.2f} TEST_ONLY; y gap between periodic images "
            f"{py * A - 2 * (TORUS_R_A + TORUS_r_A):.1f} A; strips {strip:.0f} A; phase MAP -> "
            f"N = max({N_FP_MIN}, {N_pix}) realisations per resolution element; a B16 rocking "
            f"series would multiply by {S['n_b16']} angles but T2 shows the ring is not resolved")
    # --- (V) validation rocking curve on a flat strip --------------------------------------------
    lay = layout_100(name="V_rocking", L_run=d10["L_run"], z_fov=M + meas_len, y_A=2 * A,
                     D_clean=d10["D_clean"], S=S, terraces_y=[(0, 2)])
    add("V_rocking_flat_strip_r0.10", lay, 1, S["n_rock"],
        f"flat strip for the rocking-curve benchmark (docs/05 4.4) and the run-in check, static "
        f"lattice, {S['n_rock']} angles")
    # --- (4) patterned CFG-B feature: BLOCKED ------------------------------------------------------
    h10 = 100.0
    print(f"[4_patterned] BLOCKED on PROJECT_INPUT item 13 (docs/05 gives no lateral size). With "
          f"docs/05's illustrative 10 nm height the two strips alone are 2 x {h10 / tan_e:.0f} A = "
          f"{2 * h10 / tan_e:.0f} A along the beam and the cell needs >= {h10:.0f} A more vacuum "
          f"or depth; lower bound on z: {GAP_A / tan_e + d10['L_run'] + M + 2 * h10 / tan_e + M:.0f}"
          f" A plus the feature length")

    # --------------------------------------------------------------------------------------------
    hdr("14. Table (paste into the report)")
    st = S["study_tot"]
    print("| scenario | extents x, y, z (A) | atoms | grid | slices | memory per realisation (GB) "
          "| CPU time per realisation (4 cores, x1.5) | GPU time per realisation (ASSUMPTION "
          "model) | realisations x angles | total CPU / GPU |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    print(f"| 1 study.yaml, 17 points ([110], reference) | {st['x'][0]:.0f}-{st['x'][1]:.0f} x "
          f"{st['y'][0]:.1f}-{st['y'][1]:.1f} x {st['z'][0]:.0f}-{st['z'][1]:.0f} | "
          f"{st['atoms'][0]:,} to {st['atoms'][1]:,} | see section 8 | {st['slices'][0]} to "
          f"{st['slices'][1]} | <= {st['mem'] / 1e9:.3f} | {fmt_t(st['cpu'])} (sum) | "
          f"{st['gpu']:.0f} s (sum) | 1 x 1 (translation points 2 runs) | "
          f"{fmt_t(st['cpu'])} / {fmt_t(st['gpu'])} |")
    for rw in rows:
        L = rw["lay"]
        n = rw["n_real"] * rw["n_ang"]
        print(f"| {rw['label']} | {L['ext_x']:.0f} x {L['Ly']:.0f} x {L['Lz']:.0f} | "
              f"{L['n_atoms']:,} | {L['nx']}x{L['ny']} | {L['N']} | {rw['mem'] / 1e9:.2f} | "
              f"{fmt_t(rw['cpu'])} | {fmt_t(rw['gpu'])} | {rw['n_real']} x {rw['n_ang']} | "
              f"{fmt_t(rw['cpu'] * n)} / {fmt_t(rw['gpu'] * n)} |")
    print("| 4 patterned CFG-B feature | BLOCKED on PROJECT_INPUT item 13 | | | | | | | | |")

    # --------------------------------------------------------------------------------------------
    hdr("15. Self-checks")
    n_fail = sum(1 for _, ok, _ in CHECKS if not ok)
    print(f"{len(CHECKS) - n_fail}/{len(CHECKS)} checks pass; runtime {time.time() - t_start:.0f} s")
    for nm, ok, det in CHECKS:
        if not ok:
            print(f"  FAILED: {nm}: {det}")
    return 1 if n_fail else 0

if __name__ == "__main__":
    sys.exit(main())
