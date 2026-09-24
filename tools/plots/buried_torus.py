#!/usr/bin/env python3
"""Buried torus void under an intact cap (agent T3; analysis revised by agent T4 after audit A9a and
by agent T5 after re-audit A10a):
the change of the specular beam of the reflection multislice against the flat reference computed in
the IDENTICAL cell, with its VACUUM-ORIGIN part separated from its END-FACE part.

Usage: venv/bin/python tools/plots/buried_torus.py --runs <dir> --out <figure dir>

Reads the files written by scripts/torus/run_torus_multislice.py (kinds buried, buried_flat): every
exit wave torus_<name>_r0000.npz found under --runs (exactly one per name) through
multislice.load_exit_wave (pixel sizes, axes, plane and 200 keV asserted from the file) and the
structure_<name>.npz beside it (schema, axes and units asserted). Before any comparison it asserts
that each cap run and its flat reference share the grid, the exit plane, the angle, the cell, the
absorbers and the physical absorption, and that their atoms differ exactly by the removed void sites.

Specular selection F: the sharp circular aperture of radius 0.2 1/A about +sin(theta_out)/lambda of
tools/plots/torus_atomistic.py (T1), applied to the whole exit plane. F is LINEAR. With
D = psi_cap - psi_flat (raw exit waves), the TOTAL change is F(D) = F(psi_cap) - F(psi_flat).
Vacuum-origin split (A9a M-2, T4): the sharp aperture carries end-face signal (inside the crystal,
no experimental counterpart) into the vacuum pixels, so the vacuum-side total is not a vacuum
signal. The exit plane is therefore split BEFORE the aperture with an apodised mask
    m(x_rel) = 0 for x_rel <= 0 (the top atomic plane and below),
               sin^2(pi x_rel / (2 w)) for 0 < x_rel < w,  1 for x_rel >= w,   w = 2.5 A
(w = the resolution 1 / (2 x 0.2 1/A) of the selection; conservative: nothing at or below the top
atomic plane enters), and
    VACUUM-ORIGIN part  F(D m),      END-FACE part  F(D (1 - m))   (their sum is F(D) exactly).
The end-face part holds the end face and the first w above the top plane.
Mask FAMILY (audit A10a-M1, agent T5): the main mask is ONE choice. The vacuum-origin values of the
shallow caps depend on how the first w = 2.5 A above the top atomic plane (the resolution of the
selection, and the range of the top layer's potential) is assigned, vacuum or crystal, which the
cell cannot decide. The script therefore prints them over a stated family of masks (mask_family:
sharp steps and sin^2 ramps, every one 0 at and below the top atomic plane, starts 0, 1.0, 2.5 A,
a/8 and a/4 with a read from the structure file) with the min-max range per metric; the reading of
a shallow cap quotes that range, which is mask-dependent and not a bound. Metrics of a part p
(total or vacuum-origin): phase change arg((psi_s,flat + p) psi_s,flat*), amplitude ratio
|psi_s,flat + p| / |psi_s,flat| (pixels below 5 % of the maximum amplitude over x_rel in [-15, 35] A
masked, as T1), and |p| / A_ref with A_ref = max |psi_s,flat| over x_rel in [0, 25] A (no mask).

Regions of the exit plane (y, x_rel = x - x_surface), DERIVED_HERE:
  P    PROJECTED RING: pixels whose surface source point z_s = L_z - x_rel / tan(theta_out) lies in
       the ring's annulus |rho - R| < r, dilated by the resolution d = 2.5 A;
  V    TWO-BEAM CAUSAL VACUUM REGION: the (0,0,8) wave scattered at depth t reaches the surface
       t / tan(theta_int) downstream (two-beam characteristic, DERIVED_HERE); V = 0 < x_rel <=
       x_V + d, |y - y_c| <= R + r + d, x_V = (L_z - z_ring,min - cap / tan(theta_int))
       tan(theta_out) (empty when x_V + d <= 0). NOT a strict bound of the engine: its band also
       carries steeper systematic beams (below);
  V16  FASTEST SYSTEMATIC-ROW PATH (information): as V with the internal angle of the steepest
       upward (0,0,l) beam inside the engine's band (l = 16 on T3's grid); its amplitude
       is not computed here;
  (no region) STEEPEST IN-BAND CAUSAL PATH (information, A10a-m2): the void is not periodic and
       scatters into every in-band k_x, so the engine's steepest path runs at the BAND EDGE,
       asin(lambda f_x,max), f_x,max read from the exit-wave metadata (2/3 rule, asserted equal to
       1/(3 dx)); after surfacing, the aperture accepts vacuum waves from theta_out up to
       asin(sin theta_out + lambda 0.2 1/A). For the two-beam, the (0,0,l) and the band-edge
       angles the script prints the surfacing distance of the void top, cap / tan(angle), and the
       exit-plane reach (L_z - (z_c - R - r) - cap / tan(angle)) tan(exit angle) at both exit
       angles (void's upstream edge with the void-top depth: an upper bound of the reach). The
       sharp aperture's point-spread function has long tails: the reach is not a hard edge in
       the filtered image. vacuum_class stays on the two-beam layer (the band-edge reach bounds
       where signal COULD go; it demonstrates nothing);
  VAC  VACUUM BAND over the ring: 0 < x_rel <= 25 A, |y - y_c| <= R + r + d;
  E    END FACE (finite-cell diagnostic, no experimental counterpart): x_rel < 0 between the two-beam
       predictions (L_z - z0) tan(theta_int) - t, t in [cap, cap + 2 r], dilated by d;
  C_up UPSTREAM REFERENCE: x_rel in [x_P,max + 2 d, x_core]; C_y LATERAL REFERENCE: |y - y_c| >=
       R + r + 2 d, x_rel in [0, x_core]. They are LEAKAGE REFERENCES, not a noise floor: the
       simulations are noiseless, and the references hold end-face signal carried by the sharp
       aperture and numerical tails (A9a M-2).
No detection rule is applied (the earlier "3 x floor" rule is withdrawn, A9a M-2); all values are
absolute. Experimental detectability needs a dose model: NOT RUN. The earlier fitted decay lengths
are withdrawn (cell artefacts, not physical lengths; A9a m-6).
Geometric (surface-height) model: layer_height_A = 0 for a buried void, so its zero signal holds by
construction of the surface-height model; this is not a geometric-engine run (A9a m-2).

DEMO (ASSUMPTION B20, B30, B32, B42; TEST_ONLY r = 0.1) and UNVALIDATED (engine not validated for
step heights; finite-cell build-up): not comparable to experiment.
Frame: x = outward normal, y = in-plane transverse, z = beam azimuth; exp(+i k.r), numpy FFT sign.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from types import SimpleNamespace

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy import ndimage  # noqa: E402

from reflection_holo.forward.multislice import PLANE_TEXT, load_exit_wave, select_beam  # noqa: E402
from reflection_holo.forward.multislice.analysis import geometric_step_phase  # noqa: E402
from reflection_holo.geometry.frames import surface_frame  # noqa: E402
from reflection_holo.structure.shapes import BuriedTorus  # noqa: E402

INK, MUTED = "#1f1f1e", "#6b6a64"
C_REGION = {"P": "#2a78d6", "V": "#1baf7a", "V16": "#8a5cc2", "VAC": "#444441", "E": "#eb6834",
            "C_up": "#6b6a64", "C_y": "#9a9a9a"}
MASKED = "#9a9a9a"
APERTURE_PER_A = 0.2          # as tools/plots/torus_atomistic.py (M2 report section 10.3)
MASK_FRACTION = 0.05          # as tools/plots/torus_atomistic.py
RES_A = 1.0 / (2.0 * APERTURE_PER_A)      # 2.5 A, resolution of the selected beam (stated)
VAC_RAMP_A = RES_A            # width w of the apodised vacuum mask (stated)
VAC_BAND_A = 25.0             # top of the vacuum band VAC and of the A_ref window
# attribution of the deep-cap vacuum difference at P (audit A9a M-1), from the T4 test
# tools/review/t4/m1_nonlocal_tail_test.py (TEST_ONLY small cell; outputs beside it). Wording after
# audit A10a-m1/M-2 (agent T5): the history of the small-cell criterion and the analogy qualifier
# travel with the label. The numbers are those printed in tools/review/t4/m1_stage2_px0.09_output.txt
# (tails/full, the pixel ratios) and m1_stage1_px0.13_output.txt:44 (the cap-20/cap-30 ratio).
M1_ATTRIBUTION = ("attributed to a numerical artefact of the non-local tails of the engine's "
                  "transmission function BY ANALOGY, UNVALIDATED in this cell; CONFIRMED in a "
                  "TEST_ONLY small cell on a criterion set after a first stage whose pre-stated "
                  "criterion gave NOT CONFIRMED (aperture leakage). The small cell (T4 M-1 test, "
                  "tools/review/t4/m1_nonlocal_tail_test.py) has the same engine, pixel rule and z "
                  "geometry and a smaller void (R 20 A, r 6 A); there the vacuum-origin value at P is "
                  "reproduced by the far change of the transmission function alone (tails/full "
                  "0.998-1.012), and from dx 0.129 A to 0.090 A it falls to 0.040 (cap 20) and 0.128 "
                  "(cap 30) of its value while the end-face signal changes by factors 1.008 and 0.918 "
                  "(tools/review/t4/m1_stage2_px0.09_output.txt). No full-size rerun and no "
                  "local/tails split of this cell")
# the small cell's cap-20 / cap-30 ratio of the P vacuum-origin maximum at T3's pixel rule
# (tools/review/t4/m1_stage1_px0.13_output.txt:44), printed beside this cell's ratio
SMALL_CELL_P_VAC_RATIO_20_30 = 2.637
FAMILY_METRICS = ("max_abs_dphi_rad", "max_abs_ratio_minus_1", "max_rel_diff")
COMPACT_X_WINDOW_A = (0.0, 20.0)   # vacuum-side window of the compact figure's bottom row
COMPACT_LOG_DECADES = 4.0          # decades shown on the compact figure's shared log scale
CAPS = (5.0, 10.0, 20.0, 30.0)
REGIONS = ("P", "V", "V16", "VAC", "E", "C_up", "C_y")
AXES = ["x: outward normal [001]", "y: z cross x", "z: beam azimuth"]
STATUS = ("UNVALIDATED demo (engine not validated for step heights; finite-cell build-up; TEST_ONLY "
          "r = 0.1 or no absorption B30); DEMO B42; no dose model (experimental detectability NOT "
          "RUN)")


def name_of(cap, tag):
    return f"buried_flat_{tag}" if cap is None else f"buried_cap{cap:g}A_{tag}"


# --------------------------------------------------------------------------------------------------
# loading and assertions
# --------------------------------------------------------------------------------------------------
def find_run(root: Path, name: str):
    hits = sorted(root.glob(f"**/outputs/exit_waves/torus_{name}_r0000.npz"))
    if len(hits) != 1:
        raise FileNotFoundError(f"{root}: expected exactly one exit wave torus_{name}_r0000.npz, "
                                f"found {len(hits)}")
    return hits[0], hits[0].parents[2]


def load_structure(path: Path) -> dict:
    with np.load(path, allow_pickle=False) as f:
        if str(f["schema"]) != "T3 buried torus structure/1":
            raise ValueError(f"{path}: unexpected schema {f['schema']}")
        if [str(a) for a in f["axes"]] != AXES or str(f["units"]) != "angstrom":
            raise ValueError(f"{path}: axes/units {list(f['axes'])} {f['units']} not as expected")
        d = {k: f[k] for k in ("positions_A", "feature_sites_A", "cell_A",
                               "structure_to_cell_shift_A")}
        d["metadata"] = json.loads(str(f["metadata_json"]))
        d["cell_feature"] = json.loads(str(f["cell_feature_json"]))
        d["cap_A"] = float(f["cap_A"])
        d["physical_absorption"] = json.loads(str(f["physical_absorption_json"]))
    md = d["metadata"]
    fr = surface_frame(tuple(md["surface"]["hkl"]), tuple(md["azimuth"]["uvw"]))
    for k, row in (("x_hat_crystal", fr.x_hat), ("y_hat_crystal", fr.y_hat),
                   ("z_hat_crystal", fr.z_hat)):
        if not np.allclose(md["frame"][k], row, atol=1e-12):
            raise ValueError(f"{path}: frame row {k} differs from surface_frame")
    d["frame"] = fr
    f = md["feature"]
    d["feature"] = None if f is None else BuriedTorus(
        center_y_A=f["center_y_A"], center_z_A=f["center_z_A"], major_radius_A=f["major_radius_A"],
        minor_radius_A=f["minor_radius_A"], cap_A=f["cap_A"], label=f["label"],
        source=f["source"])
    return d


def assert_same_cell(ew, ew_f, st, st_f) -> dict:
    """Same grid, plane, angle, cell, absorbers and absorption; atoms differ by the void only."""
    for k in ("dx_A", "dy_A", "x0_A", "y0_A", "z_A", "energy_keV", "theta_in_ext_rad"):
        if not np.isclose(getattr(ew, k), getattr(ew_f, k), rtol=0, atol=1e-12):
            raise ValueError(f"cap and flat exit waves differ in {k}")
    if ew.psi.shape != ew_f.psi.shape or ew.plane != ew_f.plane:
        raise ValueError("cap and flat exit waves differ in shape or plane")
    m, mf = ew.metadata, ew_f.metadata
    for k in ("extent_x_A", "extent_y_A", "length_z_A", "crystal_start_z_A", "surface_x_A"):
        if not np.isclose(m["cell"][k], mf["cell"][k], rtol=0, atol=1e-9):
            raise ValueError(f"cells differ in {k}")
    for path in (("absorbers",), ("theta_out_ext_rad",), ("slices", "dz_A"),
                 ("potential", "physical_absorption"), ("band_limit",)):
        a, b = m, mf
        for p in path:
            a, b = a[p], b[p]
        if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
            raise ValueError(f"cap and flat runs differ in {'.'.join(path)}")
    if json.dumps(st["physical_absorption"], sort_keys=True) != json.dumps(
            st_f["physical_absorption"], sort_keys=True):
        raise ValueError("structure files record different physical absorption")
    a = st["metadata"]["lattice"]["a_A"]
    q = a / 4.0

    def keys(p):
        n = np.rint(st["frame"].to_crystal(np.asarray(p, float)) / q).astype(np.int64)
        n += 1 << 20
        return (n[:, 0] << 42) | (n[:, 1] << 21) | n[:, 2]

    kc, kf, kv = keys(st["positions_A"]), keys(st_f["positions_A"]), keys(st["feature_sites_A"])
    if not (np.array_equal(np.sort(np.concatenate([kc, kv])), np.sort(kf))
            and np.intersect1d(kc, kv).size == 0):
        raise ValueError("the cap structure is not the flat reference minus the void sites")
    if not np.allclose(st["cell_A"], st_f["cell_A"]):
        raise ValueError("structure cells differ")
    return dict(n_atoms_flat=int(len(kf)), n_atoms_cap=int(len(kc)), n_removed=int(len(kv)),
                check="grid, plane, angle, cell, absorbers, absorption equal; atoms = flat - void")


# --------------------------------------------------------------------------------------------------
# signals
# --------------------------------------------------------------------------------------------------
def specular_of(psi, ew):
    """F(psi): the specular selection of an array on the grid of the exit wave ew (linear)."""
    lam = float(ew.metadata["beam"]["wavelength_A"])
    fc = np.sin(float(ew.metadata["theta_out_ext_rad"])) / lam
    carrier = SimpleNamespace(psi=np.asarray(psi), dx_A=ew.dx_A, dy_A=ew.dy_A)
    return select_beam(carrier, fx_centre_per_A=fc, fy_centre_per_A=0.0,
                       radius_per_A=APERTURE_PER_A)


def specular(ew):
    return specular_of(ew.psi, ew)


def vacuum_mask(x_rel, ramp_A: float = VAC_RAMP_A) -> np.ndarray:
    """m(x_rel): 0 at and below the top atomic plane (x_rel <= 0), sin^2 ramp to 1 at x_rel = ramp_A,
    1 above (module docstring). Applied to the raw exit-plane difference BEFORE the aperture."""
    if not (np.isfinite(ramp_A) and ramp_A > 0):
        raise ValueError("ramp_A must be finite and > 0")
    x = np.asarray(x_rel, float)
    s = np.clip(x / ramp_A, 0.0, 1.0)
    return np.where(x <= 0.0, 0.0, np.sin(0.5 * np.pi * s) ** 2)


def family_mask(x_rel, start_A: float, ramp_A: float) -> np.ndarray:
    """One member of the mask family (A10a-M1): 0 for x_rel <= start_A, then a sin^2 ramp to 1 at
    start_A + ramp_A (ramp_A > 0) or a sharp step (ramp_A == 0). start_A >= 0 is required, so no
    member admits anything at or below the top atomic plane."""
    if not (np.isfinite(start_A) and start_A >= 0.0):
        raise ValueError("start_A must be finite and >= 0 (nothing at or below the top atomic "
                         "plane may enter the vacuum-origin part)")
    if not (np.isfinite(ramp_A) and ramp_A >= 0.0):
        raise ValueError("ramp_A must be finite and >= 0")
    x = np.asarray(x_rel, float)
    if ramp_A == 0.0:
        return np.where(x > start_A, 1.0, 0.0)
    s = np.clip((x - start_A) / ramp_A, 0.0, 1.0)
    return np.where(x <= start_A, 0.0, np.sin(0.5 * np.pi * s) ** 2)


def mask_family(lattice_a_A: float) -> tuple:
    """The stated family of vacuum masks (A10a-M1, its nine): (label, start_A, ramp_A), ramp 0 =
    sharp step. a/8 is half the Si(001) layer spacing a/4 (a from the structure file)."""
    if not (np.isfinite(lattice_a_A) and lattice_a_A > 0):
        raise ValueError("lattice parameter must be finite and > 0")
    a8, a4 = lattice_a_A / 8.0, lattice_a_A / 4.0
    return (("sharp step at 0", 0.0, 0.0),
            ("sin^2 ramp 0-1.0 A", 0.0, 1.0),
            (f"sin^2 ramp 0-{VAC_RAMP_A:g} A (main mask)", 0.0, VAC_RAMP_A),
            ("sin^2 ramp 0-5.0 A", 0.0, 5.0),
            ("sin^2 ramp 1.0-2.0 A", 1.0, 1.0),
            ("sin^2 ramp 2.5-5.0 A", 2.5, 2.5),
            (f"sharp step at a/8 = {a8:.3f} A", a8, 0.0),
            (f"sin^2 ramp a/8-(a/8+2.5) = {a8:.3f}-{a8 + 2.5:.3f} A", a8, 2.5),
            (f"sin^2 ramp a/4-(a/4+2.5) = {a4:.3f}-{a4 + 2.5:.3f} A", a4, 2.5))


def split_with_mask(D, ew, m) -> dict:
    """F(D) and its vacuum-origin and end-face parts F(D m), F(D (1 - m)) for a mask m(x_rel);
    asserts linearity."""
    m = np.asarray(m, float)[:, None]
    total = specular_of(D, ew)
    vac = specular_of(D * m, ew)
    end = specular_of(D * (1.0 - m), ew)
    scale = max(float(np.abs(total).max()), 1e-300)
    if float(np.abs(vac + end - total).max()) > 1e-9 * scale:
        raise AssertionError("specular selection is not linear: F(D m) + F(D (1 - m)) != F(D)")
    return dict(total=total, vacuum_origin=vac, end_face=end, mask=m[:, 0])


def split_parts(D, ew, x_rel, ramp_A: float = VAC_RAMP_A) -> dict:
    """F(D) and its vacuum-origin and end-face parts F(D m), F(D (1 - m)); asserts linearity."""
    out = split_with_mask(D, ew, vacuum_mask(x_rel, ramp_A))
    out["ramp_A"] = float(ramp_A)
    return out


def steepest_row_beam(lattice_a_A: float, dx_A: float, wavelength_A: float,
                      working_l: int = 8) -> dict:
    """Steepest upward systematic (0,0,l) beam inside the engine's 2/3 band (DERIVED_HERE): at the
    symmetric (0,0,working_l) Bragg condition the incident internal beam has f_x = -(working_l/2)/a,
    beam l has f_x = (l - working_l/2)/a; diamond (0,0,l) is allowed for l = 4n; band edge
    f_x,max = 1/(3 dx). Angle = asin(lambda f_x) (the internal wavelength differs by ~1e-4)."""
    fmax = 1.0 / (3.0 * dx_A)
    l = working_l
    while ((l + 4) - working_l / 2) / lattice_a_A <= fmax:
        l += 4
    fx = (l - working_l / 2) / lattice_a_A
    return dict(l=int(l), fx_per_A=float(fx), angle_rad=float(np.arcsin(wavelength_A * fx)),
                band_edge_fx_per_A=float(fmax),
                band_edge_angle_rad=float(np.arcsin(wavelength_A * fmax)))


def geometry(ew, st) -> dict:
    m = ew.metadata
    nx, ny = ew.psi.shape
    x = ew.x0_A + np.arange(nx) * ew.dx_A
    y = ew.y0_A + np.arange(ny) * ew.dy_A
    xs = float(m["cell"]["surface_x_A"])
    Lz = float(ew.z_A)
    if abs(Lz - float(m["cell"]["length_z_A"])) > float(m["slices"]["dz_A"]):
        raise ValueError("exit plane is not the downstream end of the cell")
    fc_ = st["cell_feature"]
    lam = float(m["beam"]["wavelength_A"])
    a = float(st["metadata"]["lattice"]["a_A"]) if "metadata" in st else float(st["lattice_a_A"])
    row = steepest_row_beam(a, float(ew.dx_A), lam)
    # the band edge is read from the exit-wave file and asserted (A10a-m2): 2/3 rule, 1/(3 dx)
    bl = m["band_limit"]
    if bl.get("rule") != "2/3":
        raise ValueError(f"band-limit rule {bl.get('rule')!r} is not the 2/3 rule assumed here")
    if not np.isclose(float(bl["fx_max_per_A"]), row["band_edge_fx_per_A"], rtol=1e-9, atol=0.0):
        raise ValueError(f"band edge in the exit-wave metadata {bl['fx_max_per_A']} 1/A != "
                         f"1/(3 dx) = {row['band_edge_fx_per_A']} 1/A")
    return dict(x=x, y=y, x_rel=x - xs, xs=xs, Lz=Lz, th_out=float(m["theta_out_ext_rad"]),
                th_int=float(m["theta_int_out_rad"]), yc=float(fc_["center_y_A"]),
                zc=float(fc_["center_z_A"]), R=float(fc_["major_radius_A"]),
                r=float(fc_["minor_radius_A"]), cap=float(fc_["cap_A"]), lam=lam, a_A=a,
                energy_keV=float(ew.energy_keV), row=row,
                crystal_start_z_A=float(m["cell"]["crystal_start_z_A"]),
                # start of the fully lit footprint core on the flat surface (feature_cell F2),
                # from the illumination recorded in the exit-wave file
                core_z0_A=float((m["illumination"]["x_bottom_A"] + m["illumination"]["edge_A"]
                                 - xs) / np.tan(m["illumination"]["theta_in_ext_rad"])),
                # first contact of the sheet beam's bottom edge with the flat surface
                contact_z_A=float((m["illumination"]["x_bottom_A"] - xs)
                                  / np.tan(m["illumination"]["theta_in_ext_rad"])))


def aperture_max_exit_angle(th_out_rad: float, wavelength_A: float) -> float:
    """Steepest exit angle the specular aperture accepts: asin(sin theta_out + lambda 0.2 1/A)."""
    return float(np.arcsin(np.sin(th_out_rad) + wavelength_A * APERTURE_PER_A))


def causal_paths(g) -> dict:
    """Surfacing distance of the void top and exit-plane reach for the two-beam, the steepest
    systematic (0,0,l) and the band-edge internal angles (module docstring; DERIVED_HERE). The
    reach uses the void's upstream edge z_c - R - r with the void-top depth (an upper bound)."""
    t_out = np.tan(g["th_out"])
    th_ap = aperture_max_exit_angle(g["th_out"], g["lam"])
    z_up = g["zc"] - g["R"] - g["r"]
    out = dict(aperture_max_exit_angle_rad=th_ap, theta_out_rad=float(g["th_out"]),
               void_upstream_edge_z_A=float(z_up), paths={})
    for key, ang in (("two_beam", float(g["th_int"])),
                     (f"row_0_0_{g['row']['l']}", float(g["row"]["angle_rad"])),
                     ("band_edge", float(g["row"]["band_edge_angle_rad"]))):
        d = g["cap"] / np.tan(ang)
        out["paths"][key] = dict(
            internal_angle_rad=ang, surfacing_distance_void_top_A=float(d),
            reach_x_rel_at_theta_out_A=float((g["Lz"] - z_up - d) * t_out),
            reach_x_rel_at_aperture_max_A=float((g["Lz"] - z_up - d) * np.tan(th_ap)))
    return out


def regions(g, core_z0_A) -> dict:
    X, Y = np.meshgrid(g["x_rel"], g["y"], indexing="ij")
    t_out, t_int = np.tan(g["th_out"]), np.tan(g["th_int"])
    t_16 = np.tan(g["row"]["angle_rad"])
    R, r, cap, yc, zc, Lz = g["R"], g["r"], g["cap"], g["yc"], g["zc"], g["Lz"]
    dx = g["x_rel"][1] - g["x_rel"][0]
    dy = g["y"][1] - g["y"][0]
    zs = Lz - X / t_out
    proj = (X > 0) & (np.abs(np.hypot(Y - yc, zs - zc) - R) < r)
    P = ndimage.distance_transform_edt(~proj, sampling=(dx, dy)) <= RES_A
    zmin, zmax = zc - R - r, zc + R + r
    x_proj_max = (Lz - zmin) * t_out
    x_core = (Lz - core_z0_A) * t_out
    ring_y = np.abs(Y - yc) <= R + r + RES_A
    x_V = (Lz - zmin - cap / t_int) * t_out
    V = (X > 0) & (X <= x_V + RES_A) & ring_y
    x_V16 = (Lz - zmin - cap / t_16) * t_out
    V16 = (X > 0) & (X <= x_V16 + RES_A) & ring_y
    VAC = (X > 0) & (X <= VAC_BAND_A) & ring_y
    e_hi = (Lz - zmin) * t_int - cap                    # shallowest prediction (upstream edge)
    e_lo = (Lz - zmax) * t_int - (cap + 2 * r)          # deepest prediction (downstream edge)
    E = (X < 0) & (X >= e_lo - RES_A) & (X <= e_hi + RES_A) & ring_y
    C_up = (X >= x_proj_max + 2 * RES_A) & (X <= x_core)
    C_y = (np.abs(Y - yc) >= R + r + 2 * RES_A) & (X >= 0) & (X <= x_core)
    return dict(P=P, V=V, V16=V16, VAC=VAC, E=E, C_up=C_up, C_y=C_y, geom=dict(
        x_projection_A=[float((Lz - zmax) * t_out), float(x_proj_max)],
        x_V_two_beam_A=float(x_V), x_V16_A=float(x_V16),
        crystal_length_z_A=float(Lz - g["crystal_start_z_A"]),
        void_z_A=[float(zmin), float(zmax)],
        # surface source points z_s of the pixels of V and P, and the x_rel extent of P
        V_source_z_A=([float(zs[V].min()), float(zs[V].max())] if V.any() else None),
        P_x_rel_A=([float(X[P].min()), float(X[P].max())] if P.any() else None),
        causal_paths=causal_paths(g),
        steepest_row_beam=g["row"],
        end_face_band_A=[float(e_lo), float(e_hi)], x_core_A=float(x_core),
        C_up_x_A=[float(x_proj_max + 2 * RES_A), float(x_core)],
        C_y_min_distance_from_ring_centre_A=float(R + r + 2 * RES_A),
        surfacing_distance_void_top_two_beam_A=float(cap / t_int),
        surfacing_distance_void_top_steepest_row_beam_A=float(cap / t_16),
        # deepest point the refracted beam can reach at the ring's upstream / downstream edge
        # (forward-only propagation along the incident characteristic from the first contact)
        illumination_reach_depth_at_ring_two_beam_A=[float((zmin - g["contact_z_A"]) * t_int),
                                                     float((zmax - g["contact_z_A"]) * t_int)],
        illumination_reach_depth_at_exit_plane_two_beam_A=float((Lz - g["contact_z_A"]) * t_int),
        first_contact_z_A=g["contact_z_A"],
        max_depth_reaching_vacuum_two_beam_A=[float((Lz - zmax) * t_int),
                                              float((Lz - zmin) * t_int)]))


def metrics(ps, pf, g, reg) -> dict:
    xr = (g["x_rel"] >= -15.0) & (g["x_rel"] <= 35.0)
    a, af = np.abs(ps), np.abs(pf)
    mask = (a > MASK_FRACTION * a[xr].max()) & (af > MASK_FRACTION * af[xr].max())
    vac = (g["x_rel"] >= 0) & (g["x_rel"] <= VAC_BAND_A)
    A_ref = float(af[vac].max())
    dphi = np.angle(ps * np.conj(pf))
    rho = np.where(af > 0, a / np.where(af > 0, af, 1.0), np.nan)
    diff = np.abs(ps - pf) / A_ref
    out = {}
    for k, R in reg.items():
        if k == "geom":
            continue
        m = R & mask
        rec = dict(n_pixels=int(R.sum()), n_unmasked=int(m.sum()))
        if R.any():
            rec.update(max_rel_diff=float(diff[R].max()),
                       rms_rel_diff=float(np.sqrt(np.mean(diff[R] ** 2))))
        if m.any():
            rec.update(max_abs_dphi_rad=float(np.abs(dphi[m]).max()),
                       rms_dphi_rad=float(np.sqrt(np.mean(dphi[m] ** 2))),
                       max_abs_ratio_minus_1=float(np.abs(rho[m] - 1).max()),
                       rms_ratio_minus_1=float(np.sqrt(np.mean((rho[m] - 1) ** 2))))
        out[k] = rec
    return dict(regions=out, A_ref=A_ref, mask=mask, dphi=dphi, rho=rho, diff=diff)


def x_centroid(diff, g, band_y) -> dict:
    """y-integrated |psi_s - psi_s,flat| profile along x_rel; its peak and centroid."""
    prof = diff[:, band_y].sum(axis=1)
    x = g["x_rel"]
    sel = (x >= -60) & (x <= 25)
    p = prof[sel]
    xs = x[sel]
    if not p.sum() > 0:                  # no difference at all (e.g. a zero vacuum-origin part)
        return dict(peak_x_rel_A=float("nan"), centroid_x_rel_A=float("nan"),
                    fraction_in_vacuum=float("nan"))
    return dict(peak_x_rel_A=float(xs[np.argmax(p)]),
                centroid_x_rel_A=float(np.sum(xs * p) / np.sum(p)),
                fraction_in_vacuum=float(p[xs > 0].sum() / p.sum()))


def cross_cap(Fa, Fb, R, A_ref) -> dict:
    """Two complex specular differences over region R: rms of each / A_ref and |correlation|."""
    u, v = Fa[R], Fb[R]
    c = np.vdot(u, v) / np.sqrt(np.vdot(u, u).real * np.vdot(v, v).real)
    return dict(rms_a=float(np.sqrt(np.mean(np.abs(u) ** 2)) / A_ref),
                rms_b=float(np.sqrt(np.mean(np.abs(v) ** 2)) / A_ref),
                abs_corr=float(abs(c)),
                rms_of_difference=float(np.sqrt(np.mean(np.abs(u - v) ** 2)) / A_ref))


def depth_profile(ew_f, g) -> dict:
    """Flat reference: y-averaged exit-plane intensity below the surface, averaged over a/4 bins,
    and its local 1/e lengths (a property of this finite cell, not an extinction length); also the
    specular-selected amplitude."""
    psi = ew_f.psi.astype(np.complex128)
    I = np.mean(np.abs(psi) ** 2, axis=1)
    ps = np.mean(np.abs(specular(ew_f)), axis=1)
    x = g["x_rel"]
    q = 5.4309 / 4.0
    edges = np.arange(0.0, 70.0 + q, q)
    dep, Ib, Ab = [], [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (-x >= lo) & (-x < hi)
        if m.any():
            dep.append(0.5 * (lo + hi))
            Ib.append(I[m].mean())
            Ab.append(ps[m].mean())
    dep, Ib, Ab = map(np.asarray, (dep, Ib, Ab))
    local = []
    for lo, hi in ((0, 5), (5, 10), (10, 20), (20, 30), (30, 40), (40, 54)):
        f = (dep >= lo) & (dep <= hi)
        sI = np.polyfit(dep[f], np.log(Ib[f]), 1)[0]
        sA = np.polyfit(dep[f], np.log(Ab[f]), 1)[0]
        local.append(dict(depth_range_A=[lo, hi], intensity_1e_length_A=float(-1.0 / sI),
                          specular_amplitude_1e_length_A=float(-1.0 / sA)))

    def first_below(level):
        k = np.nonzero(Ib < level)[0]
        return float(dep[k[0]]) if len(k) else None

    return dict(depth_A=dep, I=Ib, A_spec=Ab, local=local,
                I_at=dict((f"{d:g}A", float(np.interp(d, dep, Ib))) for d in (5, 10, 20, 30, 40, 54)),
                **{"depth_I_below_1e-2_A": first_below(1e-2), "depth_I_below_1e-4_A": first_below(1e-4)})


# --------------------------------------------------------------------------------------------------
# wording (A9a M-1, M-2, m-2): statements printed for the supervisor-facing output
# --------------------------------------------------------------------------------------------------
def geometric_zero_statement(name: str, h_max_A: float, phase_rad: float) -> str:
    return (f"geometric (surface-height) model, {name}: max |layer_height_A| over the exit-plane "
            f"source points = {h_max_A:.1f} A, so phase {phase_rad:+.1f} rad and amplitude ratio 1: "
            f"zero by construction of the surface-height model (a buried void has no surface "
            f"height); not a geometric-engine run")


def vacuum_class(x_V_two_beam_A: float, res_A: float = RES_A) -> str:
    """What this cell can show on the vacuum side, from the two-beam geometry only (no signal
    threshold): 'shown' if the two-beam causal vacuum layer is at least the resolution thick,
    'not_demonstrated' if thinner, 'no_two_beam_path' if the signal surfaces after the exit plane."""
    if x_V_two_beam_A >= res_A:
        return "shown"
    if x_V_two_beam_A > 0.0:
        return "not_demonstrated"
    return "no_two_beam_path"


def _rng(family: dict, key: str, fmt: str = ".3g", scale: float = 1.0) -> str:
    lo, hi = family["range"][key]
    return f"{scale * lo:{fmt}}-{scale * hi:{fmt}}"


def band_edge_sentence(geom: dict) -> str:
    """The steepest in-band causal path and the (0,0,l) path (A10a-m2), from geom['causal_paths']."""
    cp = geom["causal_paths"]
    be = cp["paths"]["band_edge"]
    row_key = [k for k in cp["paths"] if k.startswith("row_0_0_")][0]
    rw = cp["paths"][row_key]
    return (f"the steepest in-band path (band edge, {1e3 * be['internal_angle_rad']:.1f} mrad inside "
            f"the crystal) surfaces {be['surfacing_distance_void_top_A']:.1f} A downstream of the "
            f"void top and reaches x_rel <= {be['reach_x_rel_at_theta_out_A']:.2f} A at the specular "
            f"exit angle ({1e3 * cp['theta_out_rad']:.2f} mrad) and "
            f"{be['reach_x_rel_at_aperture_max_A']:.2f} A at the aperture's steepest accepted exit "
            f"angle ({1e3 * cp['aperture_max_exit_angle_rad']:.2f} mrad) (the (0,0,{row_key[8:]}) "
            f"row beam, {1e3 * rw['internal_angle_rad']:.1f} mrad: "
            f"{rw['surfacing_distance_void_top_A']:.1f} A, {rw['reach_x_rel_at_theta_out_A']:.2f} and "
            f"{rw['reach_x_rel_at_aperture_max_A']:.2f} A)")


def band_edge_vs_P(geom: dict) -> str:
    """Where the band-edge reach lies relative to region P and the ring's undilated projection;
    worded from the printed numbers only (P is called beyond the band-edge reach only when the
    printed reaches say so)."""
    be = geom["causal_paths"]["paths"]["band_edge"]
    r1, r2 = be["reach_x_rel_at_theta_out_A"], be["reach_x_rel_at_aperture_max_A"]
    p_lo, p_hi = geom["P_x_rel_A"]
    j_lo, j_hi = geom["x_projection_A"]
    where = (f"region P (x_rel {p_lo:.2f}-{p_hi:.2f} A, the ring's projection {j_lo:.2f}-{j_hi:.2f} A "
             f"dilated by {RES_A:g} A)")
    if r2 < p_lo:
        s = f"both reaches lie below {where}"
    elif r1 < p_lo and r2 < j_lo:
        s = (f"at the specular angle it stays below {where}; at the aperture's steepest angle it "
             f"enters P but stays below the ring's undilated projection")
    elif r2 < j_lo:
        s = f"it enters {where} but stays below the ring's undilated projection"
    else:
        s = f"it reaches the ring's projection: an in-band causal path to {where} exists"
    return s + ("; the sharp aperture's point-spread function has long tails, so the reach is not a "
                "hard edge in the filtered image")


def reading_line(cap: float, geom: dict, tot: dict, vac: dict, end_max_V, P_tot: dict,
                 P_vac: dict, *, family: dict, loc_vac: dict | None = None,
                 raw_frac_first_res: float | None = None) -> str:
    """Supervisor-facing reading of one cap (no detection rule). family: the vacuum-origin metrics
    over the mask family (analyse_pair); required, because a shallow cap's vacuum-origin value is a
    mask-dependent range (A10a-M1)."""
    if not family or "range" not in family:
        raise ValueError("reading_line needs the mask-family results (A10a-M1)")
    cls = vacuum_class(geom["x_V_two_beam_A"])
    xv = geom["x_V_two_beam_A"]
    nan = float("nan")
    n = len(family["rows"])
    if cls == "shown":
        if loc_vac is None or raw_frac_first_res is None or geom.get("V_source_z_A") is None:
            raise ValueError("the reading of a shallow cap needs the vacuum-origin location, the raw "
                             "fraction in the first resolution layer and V's source points")
        zs_lo, zs_hi = geom["V_source_z_A"]
        vz_lo, vz_hi = geom["void_z_A"]
        down = max(0.0, zs_hi - max(zs_lo, vz_hi)) / (zs_hi - zs_lo)
        return (f"cap {cap:g} A: in this {geom['crystal_length_z_A']:.0f} A cell the void changes the "
                f"vacuum-side specular beam. Its vacuum-origin part (end face masked before the "
                f"aperture; region {family['region']}) is {_rng(family, 'max_abs_dphi_rad')} rad in "
                f"phase (max |dphi|), {_rng(family, 'max_abs_ratio_minus_1')} in amplitude ratio (max "
                f"|rho-1|, {_rng(family, 'max_abs_ratio_minus_1', '.1f', 100.0)} %) and "
                f"{_rng(family, 'max_rel_diff')} in max |dpsi|/A_ref over the {n} masks of the stated "
                f"family (none admits anything at or below the top atomic plane). This range depends "
                f"on the mask and is not a bound: the change sits within the first {RES_A:g} A above "
                f"the top atomic plane, the resolution of the specular selection "
                f"({raw_frac_first_res:.2f} of the raw vacuum-side |D|^2 over 0 < x_rel <= "
                f"{VAC_BAND_A:g} A in the ring's y band lies there; the main mask's vacuum-origin "
                f"|F(D m)| peaks at x_rel {loc_vac['peak_x_rel_A']:+.2f} A, centroid "
                f"{loc_vac['centroid_x_rel_A']:+.2f} A), and the answer depends on how that layer is "
                f"assigned (vacuum or crystal), which this cell cannot decide. The total over V, which "
                f"includes end-face signal carried by the aperture, is "
                f"{tot.get('max_abs_dphi_rad', nan):.3g} rad, {tot.get('max_abs_ratio_minus_1', nan):.3g} "
                f"({100 * tot.get('max_abs_ratio_minus_1', nan):.1f} %) and {tot['max_rel_diff']:.3g}. "
                f"V's surface source points lie at z_s {zs_lo:.1f}-{zs_hi:.1f} A and the void spans z "
                f"{vz_lo:.1f}-{vz_hi:.1f} A: {down:.2f} of V's z_s range lies downstream of the void's "
                f"downstream end. Experimental detectability not assessed (no dose model, NOT RUN).")
    if cls == "not_demonstrated":
        hi_d = family["range"]["max_rel_diff"][1]
        hi_p = family["range"]["max_abs_dphi_rad"][1]
        t_p = tot.get("max_abs_dphi_rad", nan)
        if hi_d < end_max_V:
            amp = (f"In amplitude the end-face part exceeds the vacuum-origin part for every mask, so "
                   f"the total over V is mostly end-face signal in amplitude; in phase the "
                   f"vacuum-origin part reaches up to {hi_p / t_p:.2f} of the total's max |dphi|.")
        else:
            amp = ("In amplitude the vacuum-origin part reaches or exceeds the end-face part for at "
                   "least one mask of the family.")
        return (f"cap {cap:g} A: NOT DEMONSTRATED in this cell. The two-beam causal vacuum layer is "
                f"{xv:.3f} A thick, below the {RES_A:g} A resolution of the specular selection. That "
                f"layer is not a bound of the engine: {band_edge_sentence(geom)}. Numbers, region V: "
                f"total max |dphi| {t_p:.3g} rad, max |rho-1| "
                f"{tot.get('max_abs_ratio_minus_1', nan):.3g} "
                f"({100 * tot.get('max_abs_ratio_minus_1', nan):.1f} %), max |dpsi|/A_ref "
                f"{tot['max_rel_diff']:.3g}; end-face part max |dpsi|/A_ref {end_max_V:.3g}; "
                f"vacuum-origin part over the {n} masks: max |dpsi|/A_ref "
                f"{_rng(family, 'max_rel_diff')} ({_rng(family, 'max_rel_diff', '.2f', 100.0)} % of "
                f"A_ref), max |dphi| {_rng(family, 'max_abs_dphi_rad')} rad. {amp} The vacuum-origin "
                f"part is not attributed (the cap-10 local/tails decomposition is NOT RUN).")
    return (f"cap {cap:g} A: no two-beam path to the vacuum before the exit plane (DERIVED_HERE; the "
            f"(0,0,8) signal from the void top surfaces {geom['surfacing_distance_void_top_two_beam_A']:.1f} A "
            f"downstream, beyond the exit plane); a vacuum-side change is NOT DEMONSTRATED. "
            f"{band_edge_sentence(geom)[0].upper() + band_edge_sentence(geom)[1:]}; "
            f"{band_edge_vs_P(geom)}. The engine shows a vacuum difference at P: max |dpsi|/A_ref "
            f"{P_tot['max_rel_diff']:.3g} (vacuum-origin part {P_vac['max_rel_diff']:.3g}; "
            f"{_rng(family, 'max_rel_diff')} over the {n} masks). It is {M1_ATTRIBUTION}.")


# --------------------------------------------------------------------------------------------------
# figures
# --------------------------------------------------------------------------------------------------
def _clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def _section(ax, d, cap, horizontal: str, legend: bool):
    """Section through the ring centre, two atomic planes thick; horizontal axis 'y' or 'z'."""
    md, feat = d["metadata"], d["feature"]
    q = md["lattice"]["a_A"] / 4.0
    x_s = md["feature"]["x_surface_A"]
    pos, fs = d["positions_A"], d["feature_sites_A"]
    depth_below = x_s - float(d["structure_to_cell_shift_A"][0])
    bulk_top = -(depth_below - 15.0)
    axis, other, cen = (1, 2, feat.center_z_A) if horizontal == "y" else (2, 1, feat.center_y_A)
    n0 = np.floor(cen / q)
    lo, hi = n0 * q - 1e-6, (n0 + 1) * q + 1e-6
    c0 = feat.center_y_A if axis == 1 else feat.center_z_A
    span = feat.major_radius_A + feat.minor_radius_A + 12
    w = ((pos[:, other] >= lo) & (pos[:, other] <= hi) & (np.abs(pos[:, axis] - c0) < span)
         & (pos[:, 0] - x_s > bulk_top - 6))
    ax.scatter(pos[w, axis], pos[w, 0] - x_s, s=2.5, color="#8c8c86", lw=0, rasterized=True,
               label="atoms (two atomic planes)" if legend else None)
    wf = (fs[:, other] >= lo) & (fs[:, other] <= hi)
    ax.scatter(fs[wf, axis], fs[wf, 0] - x_s, s=6, facecolors="none", edgecolors="#eb6834",
               lw=0.5, label="removed sites (void)" if legend else None)
    t = np.linspace(0, 2 * np.pi, 400)
    for sgn in (-1, 1):
        ax.plot(c0 + sgn * feat.major_radius_A + feat.minor_radius_A * np.cos(t),
                feat.tube_centre_x_rel_A + feat.minor_radius_A * np.sin(t), color=INK, lw=0.8,
                label="void outline (distance r from the tube centre line)"
                if (legend and sgn < 0) else None)
    ax.axhline(0.0, color="#2a78d6", lw=0.8, ls="-",
               label="flat top atomic plane (x_rel = 0)" if legend else None)
    ax.axhline(-cap, color="#1baf7a", lw=0.8, ls="--",
               label="void top (x_rel = -cap, per panel)" if legend else None)
    ax.axhline(bulk_top, color=MUTED, lw=0.8, ls=":",
               label="top of the bulk absorber" if legend else None)
    ax.set_xlim(c0 - span, c0 + span)
    ax.set_ylim(bulk_top - 6, 6)
    ax.set_aspect("equal")
    return lo, hi


def supercell_figure(structs: dict, out: Path, fname: str) -> Path:
    caps = [c for c in CAPS if c in structs]
    fig, axs = plt.subplots(len(caps), 2, figsize=(15, 3.3 * len(caps) + 0.6),
                            gridspec_kw=dict(hspace=0.55, wspace=0.12), squeeze=False)
    for row, cap in enumerate(caps):
        d = structs[cap]
        md = d["metadata"]
        for col, lab in enumerate(("y", "z")):
            ax = axs[row, col]
            lo, hi = _section(ax, d, cap, lab, legend=(row == 0 and col == 0))
            ax.set_xlabel(f"{lab} (A)" + (" along the beam" if lab == "z" else ""))
            ax.set_ylabel("x - x_surface (A)")
            ax.set_title(f"cap {cap:g} A, section along {lab} through the ring centre\n"
                         f"({'z' if lab == 'y' else 'y'} in [{lo:.2f}, {hi:.2f}] A, two planes); "
                         f"{md['feature']['n_removed']} sites removed, "
                         f"{md['feature']['intact_cap_layers']} intact cap layers",
                         fontsize=9, loc="left", color=INK)
            _clean(ax)
    h, l = axs[0, 0].get_legend_handles_labels()
    fig.legend(h, l, fontsize=8, ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.02),
               frameon=False)
    fig.suptitle("Buried torus void (R = 50 A, r = 12 A; ASSUMPTION B42) under an intact cap in "
                 "Si(001) [100]; 1:1 axes; the depth rule F5 puts the bulk absorber >= 30 A below "
                 "the deepest void", fontsize=10, color=INK, x=0.01, ha="left")
    p = out / fname
    fig.savefig(p, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return p


def _outline(ax, R, g, color, ls="-"):
    if R.any():
        ax.contour(g["y"], g["x_rel"], R.astype(float), levels=[0.5], colors=[color],
                   linewidths=0.9, linestyles=ls)


def maps_figure(results: list, out: Path, fname: str, title: str) -> Path:
    n = len(results)
    fig, axs = plt.subplots(n, 4, figsize=(25, 4.2 * n + 0.8), squeeze=False,
                            gridspec_kw=dict(hspace=0.5, wspace=0.3))
    for i, res in enumerate(results):
        g, reg, met, mv = res["g"], res["regions"], res["metrics"], res["metrics_vac"]
        xw = (g["x_rel"] >= -50) & (g["x_rel"] <= 25)
        ext = [g["y"][0], g["y"][-1], g["x_rel"][xw][0], g["x_rel"][xw][-1]]
        panels = ((np.where(met["mask"], met["dphi"], np.nan), "RdBu_r", "phase change (rad)",
                   "TOTAL phase change"),
                  (np.where(mv["mask"], mv["dphi"], np.nan), "RdBu_r", "phase change (rad)",
                   "VACUUM-ORIGIN phase change (mask before the aperture)"),
                  (np.log10(met["diff"] + 1e-16), "magma", "log10 |F(D)| / A_ref",
                   "TOTAL |change| (no mask)"),
                  (np.log10(mv["diff"] + 1e-16), "magma", "log10 |F(D m)| / A_ref",
                   "VACUUM-ORIGIN |change|"))
        for j, (data, cmap, lab, ttl) in enumerate(panels):
            ax = axs[i, j]
            cm = plt.get_cmap(cmap).copy()
            cm.set_bad(MASKED)
            d = data[xw]
            if j < 2:
                v = np.nanmax(np.abs(d)) if np.any(np.isfinite(d)) else 1.0
                im = ax.imshow(d, origin="lower", aspect="auto", cmap=cm, extent=ext,
                               interpolation="nearest", vmin=-v, vmax=v)
            else:
                im = ax.imshow(d, origin="lower", aspect="auto", cmap=cm, extent=ext,
                               interpolation="nearest", vmin=-8, vmax=0)
            cb = fig.colorbar(im, ax=ax, shrink=0.9)
            cb.set_label(lab, fontsize=8)
            gg = dict(y=g["y"], x_rel=g["x_rel"][xw])
            for k in ("P", "V", "E", "C_up"):
                _outline(ax, reg[k][xw], gg, C_REGION[k], ls="-" if k in ("P", "V", "E") else "--")
            ax.axhline(0.0, color=INK, lw=0.6, ls=":")
            ax.set_xlabel("y (A)")
            ax.set_ylabel("x - x_surface (A), exit plane")
            ax.set_title(f"{res['label']}: {ttl}", fontsize=9, loc="left", color=INK)
            _clean(ax)
    fig.text(0.01, 1.0 + 0.02 / n, title + ".\nOutlines: blue P = geometric projection of the ring "
             "(+2.5 A), green V = two-beam causal vacuum region, orange E = end-face band (finite "
             "cell), dashed grey = upstream leakage reference; dotted line = top atomic plane; grey "
             "pixels masked (< 5 % amplitude). Vacuum-origin: raw difference multiplied by "
             "m(x_rel) (0 at x_rel <= 0, sin^2 ramp to 1 at 2.5 A) before the specular aperture.",
             fontsize=9, color=INK, va="top")
    p = out / fname
    fig.savefig(p, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return p


def vs_cap_figure(results: list, out: Path, fname: str) -> Path:
    """Absolute values versus cap: total and vacuum-origin; no fit, no detection line."""
    fig, axs = plt.subplots(1, 3, figsize=(18, 5), gridspec_kw=dict(wspace=0.3))
    keys = (("max_rel_diff", "max |change| / A_ref"),
            ("max_abs_dphi_rad", "max |phase change| (rad)"),
            ("max_abs_ratio_minus_1", "max |amplitude ratio - 1|"))
    cs = [r["cap"] for r in results]
    for ax, (k, lab) in zip(axs, keys):
        for reg, mk in (("V", "s"), ("P", "o"), ("VAC", "^"), ("E", "D"), ("C_up", "x"),
                        ("C_y", "+")):
            tot = [r["metrics"]["regions"][reg].get(k, np.nan) for r in results]
            ax.semilogy(cs, tot, mk + "-", color=C_REGION[reg], lw=1, label=f"{reg} total")
            if reg in ("V", "P", "VAC"):
                vac = [r["metrics_vac"]["regions"][reg].get(k, np.nan) for r in results]
                ax.semilogy(cs, vac, mk + ":", color=C_REGION[reg], lw=1, mfc="none",
                            label=f"{reg} vacuum-origin")
        ax.set_xlabel("cap (A)")
        ax.set_ylabel(lab)
        _clean(ax)
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, fontsize=8, ncol=6, loc="lower center", bbox_to_anchor=(0.5, -0.12),
               frameon=False)
    fig.suptitle("Specular-beam change versus cap, TEST_ONLY r = 0.1, absolute values (no detection "
                 "rule, no fit; C_up and C_y are leakage references, not a noise floor). V is empty "
                 "for caps 20 and 30.\n" + STATUS, fontsize=9, x=0.01, ha="left", color=INK)
    p = out / fname
    fig.savefig(p, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return p


def depth_figure(prof: dict, out: Path, caps, fname: str) -> Path:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.semilogy(prof["depth_A"], prof["I"], "o-", ms=3, color=INK, lw=1,
                label="flat reference: y-averaged |psi|^2 (a/4 bins)")
    ax.semilogy(prof["depth_A"], prof["A_spec"] ** 2, "s-", ms=3, color="#2a78d6", lw=1,
                label="flat reference: specular-selected <|psi_s|>^2")
    for cap in caps:
        ax.axvspan(cap, cap + 24.0, color="#eb6834", alpha=0.07)
        ax.text(cap + 0.5, prof["I"].max() * 0.6, f"void, cap {cap:g}", fontsize=7,
                color="#eb6834", rotation=90, va="top")
    ax.set_xlabel("depth below the flat top plane in the exit plane (A)")
    ax.set_ylabel("intensity (incident = 1)")
    ax.set_title(f"flat reference (r = 0.1), exit-plane depth profile (a property of this finite "
                 f"cell); I < 1e-2 below {prof['depth_I_below_1e-2_A']} A, < 1e-4 below "
                 f"{prof['depth_I_below_1e-4_A']} A", fontsize=9, loc="left")
    ax.legend(fontsize=8)
    _clean(ax)
    p = out / fname
    fig.savefig(p, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return p


def _round2(v: float) -> float:
    """v rounded to two significant digits (for 'about 1/N')."""
    if not (np.isfinite(v) and v > 0):
        return float("nan")
    return float(round(v, 1 - int(np.floor(np.log10(v)))))


def compact_panel_info(results: list) -> dict:
    """Bottom row of the compact figure (A10a-m4): log10 |F(D m)|/A_ref of the main mask over the
    vacuum-side window, on ONE shared range for every cap; per cap the window maximum, N = (cap-5
    maximum) / (this maximum) and a plain title. Needs the cap-5 run (the reference level)."""
    lo, hi = COMPACT_X_WINDOW_A
    peak = {}
    for res in results:
        xw = (res["g"]["x_rel"] >= lo) & (res["g"]["x_rel"] <= hi)
        peak[res["cap"]] = float(res["metrics_vac"]["diff"][xw].max())
    if 5.0 not in peak:
        raise ValueError("the compact figure needs the cap-5 run (reference level)")
    vmax = float(np.ceil(2.0 * np.log10(max(peak.values()))) / 2.0)
    vmin = vmax - COMPACT_LOG_DECADES
    N = {c: peak[5.0] / v if v > 0 else float("inf") for c, v in peak.items()}
    titles = {}
    for res in results:
        cap = res["cap"]
        cls = vacuum_class(res["regions"]["geom"]["x_V_two_beam_A"])
        fam = res["family"]
        if cls == "shown":
            titles[cap] = (f"cap {cap:g} A: {_rng(fam, 'max_abs_dphi_rad', '.2f')} rad in phase, "
                           f"{_rng(fam, 'max_abs_ratio_minus_1', '.0f', 100.0)} % in amplitude\n"
                           f"(vacuum part; the range comes from how the\nfirst {RES_A:g} A above the "
                           f"surface is counted)")
        elif cls == "not_demonstrated":
            titles[cap] = f"cap {cap:g} A: not demonstrated in this cell"
        else:
            titles[cap] = (f"cap {cap:g} A: numerical artefact by analogy\n(about "
                           f"1/{_round2(N[cap]):.0f} of the cap-5 level)")
    return dict(vmin=vmin, vmax=vmax, window_A=[lo, hi], peak=peak, N=N, titles=titles)


def _compact_bottom(ax, res, info):
    """One bottom-row panel: log10 |F(D m)|/A_ref on the shared range info['vmin'..'vmax']."""
    g, reg, mv = res["g"], res["regions"], res["metrics_vac"]
    lo, hi = info["window_A"]
    xw = (g["x_rel"] >= lo) & (g["x_rel"] <= hi)
    ext = [g["y"][0], g["y"][-1], g["x_rel"][xw][0], g["x_rel"][xw][-1]]
    d = np.log10(mv["diff"][xw] + 1e-16)
    im = ax.imshow(d, origin="lower", aspect="auto", cmap="magma", extent=ext,
                   interpolation="nearest", vmin=info["vmin"], vmax=info["vmax"])
    gg = dict(y=g["y"], x_rel=g["x_rel"][xw])
    _outline(ax, reg["P"][xw], gg, C_REGION["P"])
    _outline(ax, reg["V"][xw], gg, C_REGION["V"])
    ax.set_title(info["titles"][res["cap"]], fontsize=8.5, loc="left", color=INK)
    return im


def compact_figure(results: list, out: Path, fname: str) -> Path:
    """Supervisor figure (about 15 x 7.5 in): the four supercell cross-sections on top; below them
    the size of the vacuum-origin change on the vacuum side per cap, ONE shared log colour scale
    (A10a-m4), with P and V outlined."""
    n = len(results)
    info = compact_panel_info(results)
    fig = plt.figure(figsize=(15, 7.5))
    gs = fig.add_gridspec(2, n + 1, height_ratios=[1.0, 1.25], width_ratios=[1.0] * n + [0.05],
                          hspace=0.6, wspace=0.35)
    im = None
    for j, res in enumerate(results):
        cap = res["cap"]
        ax = fig.add_subplot(gs[0, j])
        _section(ax, res["st"], cap, "y", legend=(j == 0))
        md = res["st"]["metadata"]["feature"]
        ax.set_title(f"cap {cap:g} A: void {md['n_removed']} sites,\nsection along y through the "
                     f"ring centre", fontsize=8.5, loc="left", color=INK)
        ax.set_xlabel("y (A)", fontsize=8)
        if j == 0:
            ax.set_ylabel("x - x_surface (A)", fontsize=8)
        ax.tick_params(labelsize=7)
        _clean(ax)
        ax2 = fig.add_subplot(gs[1, j])
        im = _compact_bottom(ax2, res, info)
        ax2.set_xlabel("y (A)", fontsize=8)
        if j == 0:
            ax2.set_ylabel("height above the surface (A), exit plane", fontsize=8)
        ax2.tick_params(labelsize=7)
        _clean(ax2)
    cax = fig.add_subplot(gs[1, n])
    cb = fig.colorbar(im, cax=cax)
    cb.ax.tick_params(labelsize=7)
    cb.set_label("log10 (size of the change / reference amplitude)\nsame scale for all four panels",
                 fontsize=7.5)
    h, l = fig.axes[0].get_legend_handles_labels()
    h += [plt.Line2D([], [], color=C_REGION["P"]), plt.Line2D([], [], color=C_REGION["V"])]
    l += ["P: above the buried ring (+2.5 A)", "V: where the simple two-beam estimate lets the "
          "signal out"]
    fig.legend(h, l, fontsize=7.5, ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.04),
               frameon=False)
    g0 = results[0]["g"]
    fig.suptitle(f"Buried ring-shaped void (DEMO B42, R {g0['R']:g} A, r {g0['r']:g} A) in Si(001) "
                 f"[100], {g0['energy_keV']:g} keV, TEST_ONLY absorption r = 0.1, UNVALIDATED engine, "
                 f"one {results[0]['regions']['geom']['crystal_length_z_A']:.0f} A long cell. Bottom: "
                 "size of the change of the reflected beam\nabove the surface, counting only what leaves "
                 "through the vacuum (main mask: 0-2.5 A ramp), on ONE colour scale "
                 f"({info['vmin']:g} to {info['vmax']:g}). No dose model: experimental detectability "
                 "not assessed; not comparable to experiment.", fontsize=9, x=0.01, ha="left",
                 color=INK)
    p = out / fname
    fig.savefig(p, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return p


# --------------------------------------------------------------------------------------------------
def raw_fraction_first_layer(D, g, band_y, layer_A: float = RES_A) -> float:
    """Fraction of the raw vacuum-side sum |D|^2 (ring's y band, 0 < x_rel <= VAC_BAND_A) that lies
    in the first layer_A above the top atomic plane (no aperture; information for A10a-M1)."""
    x = g["x_rel"]
    p2 = (np.abs(D[:, band_y]) ** 2).sum(axis=1)
    vac = (x > 0) & (x <= VAC_BAND_A)
    tot = float(p2[vac].sum())
    if tot <= 0.0:
        return float("nan")
    return float(p2[vac & (x <= layer_A)].sum() / tot)


def family_metrics(D, ew, g, reg, pf, band_y) -> dict:
    """The vacuum-origin part over the mask family (A10a-M1): per member the metrics of region V
    (or P when V is empty), P's max |dpsi|/A_ref and the x-location of |F(D m)|; the min-max range
    per metric over the family."""
    key = "V" if reg["V"].any() else "P"
    rows = []
    for label, start, ramp in mask_family(g["a_A"]):
        parts = split_with_mask(D, ew, family_mask(g["x_rel"], start, ramp))
        mm = metrics(pf + parts["vacuum_origin"], pf, g, reg)
        r = mm["regions"][key]
        rows.append(dict(label=label, start_A=float(start), ramp_A=float(ramp),
                         **{k: float(r.get(k, np.nan)) for k in FAMILY_METRICS},
                         P_max_rel_diff=float(mm["regions"]["P"].get("max_rel_diff", np.nan)),
                         loc=x_centroid(mm["diff"], g, band_y)))
    rng = {k: [float(np.nanmin([row[k] for row in rows])), float(np.nanmax([row[k] for row in rows]))]
           for k in FAMILY_METRICS}
    return dict(region=key, rows=rows, range=rng)


def analyse_pair(ew, ew_f, st, cap, tag) -> dict:
    """Everything after loading and after the identical-cell assertion (analyse): the total change
    F(D), D = psi_cap - psi_flat, its vacuum-origin and end-face parts and their metrics per region,
    the mask family, the x-locations and the raw fraction in the first resolution layer."""
    if ew.psi.shape != ew_f.psi.shape or any(getattr(ew, k) != getattr(ew_f, k)
                                             for k in ("dx_A", "dy_A", "x0_A", "y0_A")):
        raise ValueError("cap and flat exit waves are not on one grid")
    g = geometry(ew, st)
    reg = regions(g, g["core_z0_A"])
    ps, pf = specular(ew), specular(ew_f)
    D = ew.psi.astype(np.complex128) - ew_f.psi.astype(np.complex128)
    parts = split_parts(D, ew, g["x_rel"])
    if not np.allclose(pf + parts["total"], ps, rtol=0, atol=1e-12 * float(np.abs(pf).max())):
        raise AssertionError("F(psi_cap) - F(psi_flat) != F(psi_cap - psi_flat)")
    met = metrics(ps, pf, g, reg)
    met_vac = metrics(pf + parts["vacuum_origin"], pf, g, reg)
    end = np.abs(parts["end_face"]) / met["A_ref"]
    end_max = {k: float(end[v].max()) for k, v in reg.items() if k != "geom" and v.any()}
    raw = np.abs(D) / met["A_ref"]
    met["raw_max_rel_diff"] = {k: float(raw[v].max()) for k, v in reg.items()
                               if k != "geom" and v.any()}
    band_y = np.abs(g["y"] - g["yc"]) <= g["R"] + g["r"] + RES_A
    loc = x_centroid(met["diff"], g, band_y)
    loc_vac = x_centroid(met_vac["diff"], g, band_y)
    t_mid = g["cap"] + g["r"]
    loc["predicted_tube_centre_x_rel_two_beam_A"] = float(
        (g["Lz"] - g["zc"]) * np.tan(g["th_int"]) - t_mid)
    fam = family_metrics(D, ew, g, reg, pf, band_y)
    return dict(cap=cap, label=f"cap {cap:g} A ({tag})", g=g, regions=reg,
                metrics=met, metrics_vac=met_vac, end_face_max=end_max, loc=loc,
                loc_vac=loc_vac, st=st, ew=ew, F_total=parts["total"], family=fam,
                raw_frac_first_res=raw_fraction_first_layer(D, g, band_y))


def analyse(root: Path, cap, tag, ew_f, st_f):
    name = name_of(cap, tag)
    p, run = find_run(root, name)
    ew = load_exit_wave(p, expected_plane=PLANE_TEXT)
    st = load_structure(run / f"structure_{name}.npz")
    same = assert_same_cell(ew, ew_f, st, st_f)
    res = analyse_pair(ew, ew_f, st, cap, tag)
    res.update(name=name, same=same)
    return res


def reading_for(res) -> str:
    """The reading line of one analysed run (the wiring main() uses)."""
    reg, met, mv = res["regions"], res["metrics"]["regions"], res["metrics_vac"]["regions"]
    k = "V" if reg["V"].any() else "P"
    return reading_line(res["cap"], reg["geom"], met[k], mv[k],
                        res["end_face_max"].get("V", float("nan")), met["P"], mv["P"],
                        family=res["family"], loc_vac=res["loc_vac"],
                        raw_frac_first_res=res["raw_frac_first_res"])


def _fmt_table(results, key, title):
    hdr = ("cap", "region", "max|dphi|", "rms dphi", "max|rho-1|", "max|dpsi|/A", "rms|dpsi|/A")
    mets = ("max_abs_dphi_rad", "rms_dphi_rad", "max_abs_ratio_minus_1", "max_rel_diff",
            "rms_rel_diff")
    lines = [f"--- {title} ---", "  ".join(f"{h:>11s}" for h in hdr)]
    for res in results:
        for k in REGIONS:
            if key == "metrics_vac" and k == "E":
                continue
            r = res[key]["regions"][k]
            cells = [f"{r[m]:11.3e}" if m in r else f"{'empty' if not r['n_pixels'] else 'masked':>11s}"
                     for m in mets]
            print_k = k + ("*" if k in ("C_up", "C_y") else "")
            lines.append("  ".join([f"{res['cap']:11g}", f"{print_k:>11s}"] + cells))
    lines.append("  (* leakage references, not a noise floor; no detection rule is applied)")
    return lines


def print_family_block(r010: list) -> None:
    print("\n=== vacuum-origin part over the stated mask FAMILY (A10a-M1): every mask is 0 at and below "
          "the top atomic plane (x_rel <= 0); region V where it exists, else P ===")
    for res in r010:
        fam, cap = res["family"], res["cap"]
        k = fam["region"]
        tot = res["metrics"]["regions"][k]
        print(f"  cap {cap:g} A, region {k} ({len(fam['rows'])} masks):")
        for row in fam["rows"]:
            print(f"    {row['label']:44s} max|dphi| {row['max_abs_dphi_rad']:.4g} rad, max|rho-1| "
                  f"{row['max_abs_ratio_minus_1']:.4g}, max|dpsi|/A_ref {row['max_rel_diff']:.4g}; "
                  f"P max|dpsi|/A_ref {row['P_max_rel_diff']:.4g}; |F(D m)| peak x_rel "
                  f"{row['loc']['peak_x_rel_A']:+.2f} A, centroid {row['loc']['centroid_x_rel_A']:+.2f} A")
        rg = fam["range"]
        print(f"    RANGE over the family: max|dphi| {rg['max_abs_dphi_rad'][0]:.4g}-"
              f"{rg['max_abs_dphi_rad'][1]:.4g} rad, max|rho-1| {rg['max_abs_ratio_minus_1'][0]:.4g}-"
              f"{rg['max_abs_ratio_minus_1'][1]:.4g} ({100 * rg['max_abs_ratio_minus_1'][0]:.3g}-"
              f"{100 * rg['max_abs_ratio_minus_1'][1]:.3g} %), max|dpsi|/A_ref "
              f"{rg['max_rel_diff'][0]:.4g}-{rg['max_rel_diff'][1]:.4g} "
              f"({100 * rg['max_rel_diff'][0]:.3g}-{100 * rg['max_rel_diff'][1]:.3g} %)")
        print(f"    TOTAL over {k} (no mask; includes end-face signal carried by the aperture): "
              f"max|dphi| {tot.get('max_abs_dphi_rad', float('nan')):.4g} rad, max|rho-1| "
              f"{tot.get('max_abs_ratio_minus_1', float('nan')):.4g} "
              f"({100 * tot.get('max_abs_ratio_minus_1', float('nan')):.3g} %), max|dpsi|/A_ref "
              f"{tot['max_rel_diff']:.4g} ({100 * tot['max_rel_diff']:.3g} %)")
        print(f"    raw vacuum-side change (no aperture, ring's y band): fraction of sum |D|^2 over "
              f"0 < x_rel <= {VAC_BAND_A:g} A lying at 0 < x_rel <= {RES_A:g} A: "
              f"{res['raw_frac_first_res']:.3f}")
        lv = res["loc_vac"]
        print(f"    main mask: vacuum-origin |F(D m)| (y-integrated over the ring band) peaks at x_rel "
              f"{lv['peak_x_rel_A']:+.2f} A, centroid {lv['centroid_x_rel_A']:+.2f} A, fraction in "
              f"vacuum {lv['fraction_in_vacuum']:.2f}")
        vz = res["regions"]["geom"]["V_source_z_A"]
        if vz is not None:
            print(f"    V's surface source points z_s {vz[0]:.1f}-{vz[1]:.1f} A; void z "
                  f"{res['regions']['geom']['void_z_A'][0]:.1f}-{res['regions']['geom']['void_z_A'][1]:.1f} A")


def print_causal_block(r010: list) -> None:
    g0 = r010[0]
    cp0 = g0["regions"]["geom"]["causal_paths"]
    geo = g0["regions"]["geom"]
    print("\n=== causal paths from the void top to the exit plane (DERIVED_HERE; information: no "
          "amplitude is computed; A10a-m2) ===")
    print(f"  internal angles: " + ", ".join(f"{k} {1e3 * v['internal_angle_rad']:.2f} mrad"
                                            for k, v in cp0["paths"].items())
          + f"; band edge from f_x,max {g0['g']['row']['band_edge_fx_per_A']:.4f} 1/A; the aperture "
          f"accepts exit angles from theta_out {1e3 * cp0['theta_out_rad']:.2f} mrad up to "
          f"{1e3 * cp0['aperture_max_exit_angle_rad']:.2f} mrad")
    print(f"  reach from the void's upstream edge z {cp0['void_upstream_edge_z_A']:.2f} A with the "
          f"void-top depth (upper bound); region P x_rel {geo['P_x_rel_A'][0]:.2f}-"
          f"{geo['P_x_rel_A'][1]:.2f} A; ring's projection {geo['x_projection_A'][0]:.2f}-"
          f"{geo['x_projection_A'][1]:.2f} A; the sharp aperture's point-spread function has long "
          f"tails, so the reach is not a hard edge")
    for res in r010:
        cp = res["regions"]["geom"]["causal_paths"]
        for k, v in cp["paths"].items():
            print(f"  cap {res['cap']:2g} {k:12s}: {1e3 * v['internal_angle_rad']:6.2f} mrad, surfaces "
                  f"{v['surfacing_distance_void_top_A']:7.1f} A downstream of the void top; exit-plane "
                  f"reach x_rel {v['reach_x_rel_at_theta_out_A']:+7.2f} A at theta_out, "
                  f"{v['reach_x_rel_at_aperture_max_A']:+7.2f} A at "
                  f"{1e3 * cp['aperture_max_exit_angle_rad']:.2f} mrad")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--runs", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    np.set_printoptions(precision=4)
    print(f"STATUS: {STATUS}")
    print(f"vacuum-origin split: m(x_rel) = 0 at x_rel <= 0, sin^2 ramp to 1 at {VAC_RAMP_A:g} A, "
          f"applied to D = psi_cap - psi_flat BEFORE the specular aperture (radius "
          f"{APERTURE_PER_A:g} 1/A); F(D) = F(D m) + F(D (1 - m)) asserted")

    # ---- flat references ----------------------------------------------------------------------
    flats = {}
    for tag in ("r010", "r000"):
        try:
            p, run = find_run(args.runs, name_of(None, tag))
        except FileNotFoundError as exc:
            print(f"{exc}: runs with {tag} NOT analysed")
            continue
        flats[tag] = (load_exit_wave(p, expected_plane=PLANE_TEXT),
                      load_structure(run / f"structure_{name_of(None, tag)}.npz"))

    results = {}
    for tag, caps in (("r010", CAPS), ("r000", (10.0,))):
        if tag not in flats:
            continue
        ew_f, st_f = flats[tag]
        for cap in caps:
            try:
                res = analyse(args.runs, cap, tag, ew_f, st_f)
            except FileNotFoundError as exc:
                print(f"{exc}: NOT analysed")
                continue
            results[(tag, cap)] = res

    # ---- per run --------------------------------------------------------------------------------
    for (tag, cap), res in results.items():
        g, reg, met, mv = res["g"], res["regions"], res["metrics"], res["metrics_vac"]
        print(f"\n=== {res['name']}: cap {cap:g} A, absorption "
              f"{res['st']['physical_absorption']['ratio']} ({res['st']['physical_absorption']['label'][:40]}...)")
        print(f"  identical cell: {res['same']}")
        print(f"  theta_out {g['th_out'] * 1e3:.4f} mrad, theta_int {g['th_int'] * 1e3:.4f} mrad, "
              f"L_z {g['Lz']:.2f} A, ring centre (y, z) = ({g['yc']:.2f}, {g['zc']:.2f}) A cell, "
              f"A_ref {met['A_ref']:.4f}")
        print(f"  cell: beam {g['energy_keV']:g} keV (exit-wave file), crystal length along z "
              f"{reg['geom']['crystal_length_z_A']:.2f} A (L_z - crystal_start_z_A); ring R "
              f"{g['R']:g} A, r {g['r']:g} A, cap {g['cap']:g} A; void z {reg['geom']['void_z_A'][0]:.2f}-"
              f"{reg['geom']['void_z_A'][1]:.2f} A; band edge f_x,max {g['row']['band_edge_fx_per_A']:.4f} "
              f"1/A (exit-wave metadata, 2/3 rule, equal to 1/(3 dx): asserted)")
        print(f"  regions (two-beam and steepest-row values are DERIVED_HERE): {json.dumps(reg['geom'])}")
        for k in REGIONS:
            print(f"  TOTAL         {k:5s} {json.dumps(met['regions'][k])}")
        for k in REGIONS:
            if k != "E":
                print(f"  VACUUM-ORIGIN {k:5s} {json.dumps(mv['regions'][k])}")
        print(f"  END-FACE part max |F(D (1 - m))| / A_ref per region: {json.dumps(res['end_face_max'])}")
        fam = res["family"]
        print(f"  vacuum-origin part over the mask family, region {fam['region']} (range "
              f"{json.dumps(fam['range'])}); per member in the family block below")
        print(f"  x-location of the total |F(D)| (ring y band): {json.dumps(res['loc'])}")
        print(f"  x-location of the vacuum-origin |F(D m)|: {json.dumps(res['loc_vac'])}")
        print(f"  raw (no aperture) max |psi - psi_flat| / A_ref per region: "
              f"{json.dumps(met['raw_max_rel_diff'])}")

    r010 = [results[("r010", c)] for c in CAPS if ("r010", c) in results]
    if r010:
        print("\n=== specular-beam change, TEST_ONLY r = 0.1: ABSOLUTE values (A = A_ref) ===")
        for line in _fmt_table(r010, "metrics", "TOTAL F(D)"):
            print(line)
        for line in _fmt_table(r010, "metrics_vac", "VACUUM-ORIGIN F(D m) (end face masked before "
                                                    "the aperture)"):
            print(line)
        print("--- END-FACE part F(D (1 - m)): max |.|/A_ref ---")
        for res in r010:
            print(f"  cap {res['cap']:g}: " + ", ".join(f"{k} {v:.3e}" for k, v in
                                                        res["end_face_max"].items()))

        print("\n=== location of the total change (y-integrated over the ring band) ===")
        for res in r010:
            L = res["loc"]
            print(f"  cap {res['cap']:g}: peak x_rel {L['peak_x_rel_A']:+.2f} A, centroid "
                  f"{L['centroid_x_rel_A']:+.2f} A, fraction in vacuum {L['fraction_in_vacuum']:.2f}; "
                  f"two-beam prediction for the tube centre {L['predicted_tube_centre_x_rel_two_beam_A']:+.2f} A")

        print("\n=== caps compared as complex fields (total F(D)) ===")
        A_ref = r010[0]["metrics"]["A_ref"]
        byc = {r["cap"]: r for r in r010}
        for a, b in ((20.0, 30.0), (10.0, 20.0), (10.0, 30.0), (5.0, 30.0)):
            if a in byc and b in byc:
                for k in ("P", "VAC", "C_up"):
                    R = byc[b]["regions"][k]
                    c = cross_cap(byc[a]["F_total"], byc[b]["F_total"], R, A_ref)
                    print(f"  caps {a:g} vs {b:g}, {k:4s}: rms {c['rms_a']:.3e} vs {c['rms_b']:.3e}; "
                          f"|corr| {c['abs_corr']:.3f}; rms of difference {c['rms_of_difference']:.3e}")
        for a in (20.0, 30.0):
            if a in byc:
                P = byc[a]["metrics"]["regions"]["P"]
                Pv = byc[a]["metrics_vac"]["regions"]["P"]
                print(f"  cap {a:g}: P (vacuum, ring's projection) max |F(D)|/A_ref {P['max_rel_diff']:.3e}, "
                      f"vacuum-origin part {Pv['max_rel_diff']:.3e}")
        if 20.0 in byc and 30.0 in byc:
            ratio = (byc[20.0]["metrics_vac"]["regions"]["P"]["max_rel_diff"]
                     / byc[30.0]["metrics_vac"]["regions"]["P"]["max_rel_diff"])
            print(f"  cap 20 / cap 30, P vacuum-origin max: {ratio:.3f} in this cell; "
                  f"{SMALL_CELL_P_VAC_RATIO_20_30:.3f} in the TEST_ONLY small cell at the same pixel "
                  f"rule (tools/review/t4/m1_stage1_px0.13_output.txt:44): the analogy is imperfect")

        print_family_block(r010)
        print_causal_block(r010)

    if "r010" in flats and r010:
        ew_f, st_f = flats["r010"]
        prof = depth_profile(ew_f, r010[0]["g"])
        print(f"\n=== flat reference (r = 0.1) exit-plane depth profile (a property of this finite "
              f"cell, not an extinction length) ===\n  I at depths {prof['I_at']}; I < 1e-2 from "
              f"{prof['depth_I_below_1e-2_A']} A, < 1e-4 from {prof['depth_I_below_1e-4_A']} A "
              f"(H2 2.4: 26.0 A and 53.2 A)")
        for rec in prof["local"]:
            print(f"  local 1/e lengths {rec}")
        print(f"  figure: {depth_figure(prof, args.out, CAPS, 'depth_profile_flat_r010_t5.png')}")
    if ("r000", 10.0) in results and ("r010", 10.0) in results:
        print("\n=== absorption dependence, cap 10 A: r = 0.1 vs r = 0 (each against its own flat) ===")
        for tag in ("r010", "r000"):
            res = results[(tag, 10.0)]
            for k in ("V", "P", "VAC", "E"):
                t = res["metrics"]["regions"][k]
                v = res["metrics_vac"]["regions"][k] if k != "E" else {}
                print(f"  {tag} {k:4s} total max|dpsi|/A {t['max_rel_diff']:.3e}, max|dphi| "
                      f"{t.get('max_abs_dphi_rad', float('nan')):.3e} rad"
                      + (f"; vacuum-origin max|dpsi|/A {v['max_rel_diff']:.3e}, max|dphi| "
                         f"{v.get('max_abs_dphi_rad', float('nan')):.3e} rad" if v else ""))
            print(f"  {tag} A_ref {res['metrics']['A_ref']:.4f}")

    # geometric (surface-height) model: zero by construction (A9a m-2)
    print()
    for (tag, cap), res in results.items():
        f = res["st"]["feature"]
        g = res["g"]
        zs = g["Lz"] - np.clip(g["x_rel"], 0, None) / np.tan(g["th_out"]) - g["crystal_start_z_A"]
        Y, Z = np.meshgrid(g["y"], zs, indexing="ij")
        h = f.layer_height_A(Y, Z, layer_spacing_A=res["st"]["metadata"]["lattice"]["a_A"] / 4)
        hmax = float(np.max(np.abs(h)))
        print(geometric_zero_statement(res["name"], hmax,
                                       geometric_step_phase(hmax, g["th_out"], g["lam"])))

    # ---- reading (supervisor-facing; no detection rule) -----------------------------------------
    if r010:
        L = r010[0]["regions"]["geom"]["crystal_length_z_A"]
        print(f"\n=== reading (vacuum side; values of this {L:.0f} A cell; no dose model) ===")
        for res in r010:
            print("  " + reading_for(res))

    # ---- figures ----------------------------------------------------------------------------
    structs = {res["cap"]: res["st"] for res in r010}
    if structs:
        print(f"figure: {supercell_figure(structs, args.out, 'supercell_buried_t5.png')}")
    if r010:
        print(f"figure: {maps_figure(r010, args.out, 'signal_maps_r010_t5.png', 'Specular beam minus flat reference, TEST_ONLY r = 0.1, ' + STATUS)}")
        print(f"figure: {vs_cap_figure(r010, args.out, 'signal_vs_cap_t5.png')}")
        if 5.0 in {r["cap"] for r in r010}:
            info = compact_panel_info(r010)
            print(f"compact figure, bottom row: log10 |F(D m)|/A_ref (main mask) over x_rel "
                  f"{info['window_A'][0]:g}-{info['window_A'][1]:g} A on ONE shared range "
                  f"[{info['vmin']:g}, {info['vmax']:g}] for every cap; panel maxima: "
                  + "; ".join(f"cap {c:g} {v:.3e} (cap-5 level / this = {info['N'][c]:.1f}, "
                              f"about 1/{_round2(info['N'][c]):.0f})" for c, v in info["peak"].items()))
            for c, t in info["titles"].items():
                print(f"  panel title, cap {c:g}: {t!r}")
            print(f"figure: {compact_figure(r010, args.out, 'buried_compact.png')}")
        else:
            print("compact figure NOT drawn: the cap-5 run (its reference level) is missing")
    r0 = [results[k] for k in (("r010", 10.0), ("r000", 10.0)) if k in results]
    if len(r0) == 2:
        print(f"figure: {maps_figure(r0, args.out, 'signal_maps_cap10_absorption_t5.png', 'cap 10 A with TEST_ONLY r = 0.1 (top) and without absorption B30 (bottom), ' + STATUS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
