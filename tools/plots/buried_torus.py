#!/usr/bin/env python3
"""Buried torus void under an intact cap (agent T3): detectability of the cavity in the specular beam
of the reflection multislice, against the flat reference computed in the IDENTICAL cell.

Usage: venv/bin/python tools/plots/buried_torus.py --runs <dir> --out <figure dir>

Reads the files written by scripts/torus/run_torus_multislice.py (kinds buried, buried_flat): every
exit wave torus_<name>_r0000.npz found under --runs (exactly one per name) through
multislice.load_exit_wave (pixel sizes, axes, plane and 200 keV asserted from the file) and the
structure_<name>.npz beside it (schema, axes and units asserted). Before any comparison it asserts
that each cap run and its flat reference share the grid, the exit plane, the angle, the cell, the
absorbers and the physical absorption, and that their atoms differ exactly by the removed void sites.

Signals (specular beam selected with the same 0.2 1/A aperture about +sin(theta_out)/lambda as
tools/plots/torus_atomistic.py; pixels where |psi_s| or |psi_s,flat| < 5 % of its maximum over
x_rel in [-15, 35] A masked for the phase and the ratio, as there):
  d_phi = arg(psi_s psi_s,flat*), rho = |psi_s| / |psi_s,flat|, and the complex difference
  |psi_s - psi_s,flat| / A_ref (A_ref = max |psi_s,flat| over the vacuum band x_rel in [0, 25] A; no
  mask needed).
Regions of the exit plane (y, x_rel = x - x_surface), DERIVED_HERE:
  P  PROJECTED RING (requested): pixels whose surface source point z_s = L_z - x_rel / tan(theta_out)
     lies in the ring's annulus |rho - R| < r, dilated by the resolution d = 1 / (2 x 0.2 1/A) = 2.5 A;
  V  CAUSAL VACUUM REGION: the scattered wave from a void point at depth t and z0 reaches the surface
     at z0 + t / tan(theta_int) (reflected wave's characteristic, two-beam region of influence);
     V = pixels with 0 < x_rel <= x_V + d and |y - y_c| <= R + r + d, x_V = (L_z - z_ring,min -
     cap / tan(theta_int)) tan(theta_out) (empty when x_V + d <= 0);
  E  END FACE (finite-cell diagnostic, no experimental counterpart): inside the crystal, predicted
     x_rel = (L_z - z0) tan(theta_int) - t for t in [cap, cap + 2 r]: the band between the deepest
     and the shallowest prediction, dilated by d, |y - y_c| <= R + r + d, x_rel < 0;
  C_up  UPSTREAM CONTROL: x_rel in [x_P,max + 2 d, x_core] (surface sources >= 300 A upstream of the
     ring inside the fully lit core; no causal path from the void): the floor of the difference;
  C_y   LATERAL CONTROL: |y - y_c| >= R + r + 2 d, x_rel in [0, x_core].
Floor: the larger of the two control values OF THE SAME RUN and metric (the controls scale with
the signal: they hold the leakage of the Fourier aperture and of the band-limited propagation, not
a fixed noise level); a region "detects" the void when its value exceeds FLOOR_FACTOR x that floor.
Decay with the cap: S(cap) = S0 exp(-cap / L) fitted by least squares to ln S over the caps whose
signal is detected; compared with the P2 two-beam amplitude
extinction depth Lambda = G/|U_g| = 24.47 A and the intensity depth Lambda/2 (section "decay").
The geometric (surface-height) engine sees layer_height_A = 0 everywhere: zero signal.
Also printed: the illumination reach, (z - z_contact) tan(theta_int), the deepest point that the
refracted beam launched at the first contact z_contact can reach at z (forward-only propagation
along the incident characteristic), at the ring and at the exit plane.

DEMO (ASSUMPTION B20, B30, B32, B42; TEST_ONLY r = 0.1) and UNVALIDATED (engine not validated for
step heights; finite-cell build-up): detectability only, not comparable to experiment.
Frame: x = outward normal, y = in-plane transverse, z = beam azimuth; exp(+i k.r), numpy FFT sign.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage

from reflection_holo.forward.multislice import PLANE_TEXT, load_exit_wave, select_beam
from reflection_holo.forward.multislice.analysis import geometric_step_phase
from reflection_holo.geometry.frames import surface_frame
from reflection_holo.structure.shapes import BuriedTorus

INK, MUTED = "#1f1f1e", "#6b6a64"
C_REGION = {"P": "#2a78d6", "V": "#1baf7a", "E": "#eb6834", "C_up": "#6b6a64", "C_y": "#9a9a9a"}
MASKED = "#9a9a9a"
APERTURE_PER_A = 0.2          # as tools/plots/torus_atomistic.py (M2 report section 10.3)
MASK_FRACTION = 0.05          # as tools/plots/torus_atomistic.py
RES_A = 1.0 / (2.0 * APERTURE_PER_A)      # 2.5 A, resolution of the selected beam (stated)
FLOOR_FACTOR = 3.0            # a signal counts above 3 x the larger control value (stated)
EXTINCTION_AMP_A = 24.47      # P2: G/|U_g|, two-beam amplitude extinction depth, (0,0,8), r = 0
CAPS = (5.0, 10.0, 20.0, 30.0)
AXES = ["x: outward normal [001]", "y: z cross x", "z: beam azimuth"]
STATUS = ("UNVALIDATED, detectability only (engine not validated for step heights; finite-cell "
          "build-up; TEST_ONLY r = 0.1 or no absorption B30); DEMO B42")


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
def specular(ew):
    lam = float(ew.metadata["beam"]["wavelength_A"])
    fc = np.sin(float(ew.metadata["theta_out_ext_rad"])) / lam
    return select_beam(ew, fx_centre_per_A=fc, fy_centre_per_A=0.0, radius_per_A=APERTURE_PER_A)


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
    return dict(x=x, y=y, x_rel=x - xs, xs=xs, Lz=Lz, th_out=float(m["theta_out_ext_rad"]),
                th_int=float(m["theta_int_out_rad"]), yc=float(fc_["center_y_A"]),
                zc=float(fc_["center_z_A"]), R=float(fc_["major_radius_A"]),
                r=float(fc_["minor_radius_A"]), cap=float(fc_["cap_A"]),
                lam=float(m["beam"]["wavelength_A"]),
                crystal_start_z_A=float(m["cell"]["crystal_start_z_A"]),
                # start of the fully lit footprint core on the flat surface (feature_cell F2),
                # from the illumination recorded in the exit-wave file
                core_z0_A=float((m["illumination"]["x_bottom_A"] + m["illumination"]["edge_A"]
                                 - xs) / np.tan(m["illumination"]["theta_in_ext_rad"])),
                # first contact of the sheet beam's bottom edge with the flat surface
                contact_z_A=float((m["illumination"]["x_bottom_A"] - xs)
                                  / np.tan(m["illumination"]["theta_in_ext_rad"])))


def regions(g, core_z0_A) -> dict:
    X, Y = np.meshgrid(g["x_rel"], g["y"], indexing="ij")
    t_out, t_int = np.tan(g["th_out"]), np.tan(g["th_int"])
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
    e_hi = (Lz - zmin) * t_int - cap                    # shallowest prediction (upstream edge)
    e_lo = (Lz - zmax) * t_int - (cap + 2 * r)          # deepest prediction (downstream edge)
    E = (X < 0) & (X >= e_lo - RES_A) & (X <= e_hi + RES_A) & ring_y
    C_up = (X >= x_proj_max + 2 * RES_A) & (X <= x_core)
    C_y = (np.abs(Y - yc) >= R + r + 2 * RES_A) & (X >= 0) & (X <= x_core)
    return dict(P=P, V=V, E=E, C_up=C_up, C_y=C_y, geom=dict(
        x_projection_A=[float((Lz - zmax) * t_out), float(x_proj_max)],
        x_V_A=float(x_V), end_face_band_A=[float(e_lo), float(e_hi)], x_core_A=float(x_core),
        C_up_x_A=[float(x_proj_max + 2 * RES_A), float(x_core)],
        C_y_min_distance_from_ring_centre_A=float(R + r + 2 * RES_A),
        surfacing_distance_void_top_A=float(cap / t_int),
        # deepest point the refracted beam can reach at the ring's upstream / downstream edge
        # (forward-only propagation along the incident characteristic from the first contact)
        illumination_reach_depth_at_ring_A=[float((zmin - g["contact_z_A"]) * t_int),
                                            float((zmax - g["contact_z_A"]) * t_int)],
        illumination_reach_depth_at_exit_plane_A=float((Lz - g["contact_z_A"]) * t_int),
        first_contact_z_A=g["contact_z_A"],
        max_depth_reaching_vacuum_A=[float((Lz - zmax) * t_int), float((Lz - zmin) * t_int)]))


def metrics(ps, pf, g, reg) -> dict:
    xr = (g["x_rel"] >= -15.0) & (g["x_rel"] <= 35.0)
    a, af = np.abs(ps), np.abs(pf)
    mask = (a > MASK_FRACTION * a[xr].max()) & (af > MASK_FRACTION * af[xr].max())
    vac = (g["x_rel"] >= 0) & (g["x_rel"] <= 25.0)
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
    return dict(peak_x_rel_A=float(xs[np.argmax(p)]),
                centroid_x_rel_A=float(np.sum(xs * p) / np.sum(p)),
                fraction_in_vacuum=float(p[xs > 0].sum() / p.sum()))


def depth_profile(ew_f, g) -> dict:
    """Flat reference: y-averaged exit-plane intensity below the surface, averaged over a/4 bins,
    and the 1/e intensity depth fitted over depth 2 to 40 A; also the specular-selected amplitude."""
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


def fit_decay(caps, S, floors) -> dict:
    caps, S, floors = np.asarray(caps, float), np.asarray(S, float), np.asarray(floors, float)
    ok = S > FLOOR_FACTOR * floors
    out = dict(caps_used=caps[ok].tolist(), floors=floors.tolist(), floor_factor=FLOOR_FACTOR)
    if ok.sum() >= 2:
        A = np.vstack([np.ones(ok.sum()), -caps[ok]]).T
        coef, res, *_ = np.linalg.lstsq(A, np.log(S[ok]), rcond=None)
        L = 1.0 / coef[1] if coef[1] != 0 else np.inf
        dof = ok.sum() - 2
        se = None
        if dof > 0:
            s2 = float(np.sum((np.log(S[ok]) - A @ coef) ** 2) / dof)
            cov = s2 * np.linalg.inv(A.T @ A)
            se = float(np.sqrt(cov[1, 1]) / coef[1] ** 2)
        out.update(L_A=float(L), L_stderr_A=se, S0=float(np.exp(coef[0])), n_points=int(ok.sum()))
    else:
        out.update(L_A=None, L_stderr_A=None, S0=None, n_points=int(ok.sum()),
                   note="fewer than two caps above the floor: no decay length")
    pairs = []
    for i in range(len(caps) - 1):
        if S[i] > 0 and S[i + 1] > 0 and S[i] != S[i + 1]:
            pairs.append(dict(caps=[float(caps[i]), float(caps[i + 1])],
                              L_A=float((caps[i + 1] - caps[i]) / np.log(S[i] / S[i + 1]))))
    out["pairwise"] = pairs
    return out


# --------------------------------------------------------------------------------------------------
# figures
# --------------------------------------------------------------------------------------------------
def _clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def supercell_figure(structs: dict, out: Path) -> Path:
    caps = [c for c in CAPS if c in structs]
    fig, axs = plt.subplots(len(caps), 2, figsize=(15, 3.3 * len(caps) + 0.6),
                            gridspec_kw=dict(hspace=0.55, wspace=0.12), squeeze=False)
    for row, cap in enumerate(caps):
        d = structs[cap]
        md, feat = d["metadata"], d["feature"]
        q = md["lattice"]["a_A"] / 4.0
        x_s = md["feature"]["x_surface_A"]
        pos, fs = d["positions_A"], d["feature_sites_A"]
        depth_below = x_s - float(d["structure_to_cell_shift_A"][0])
        bulk_top = -(depth_below - 15.0)
        for col, (axis, other, cen, lab) in enumerate(((1, 2, feat.center_z_A, "y"),
                                                        (2, 1, feat.center_y_A, "z"))):
            ax = axs[row, col]
            n0 = np.floor(cen / q)
            lo, hi = n0 * q - 1e-6, (n0 + 1) * q + 1e-6
            c0 = feat.center_y_A if axis == 1 else feat.center_z_A
            span = feat.major_radius_A + feat.minor_radius_A + 12
            w = ((pos[:, other] >= lo) & (pos[:, other] <= hi) & (np.abs(pos[:, axis] - c0) < span)
                 & (pos[:, 0] - x_s > bulk_top - 6))
            ax.scatter(pos[w, axis], pos[w, 0] - x_s, s=2.5, color="#8c8c86", lw=0,
                       rasterized=True, label="atoms (two atomic planes)")
            wf = (fs[:, other] >= lo) & (fs[:, other] <= hi)
            ax.scatter(fs[wf, axis], fs[wf, 0] - x_s, s=6, facecolors="none", edgecolors="#eb6834",
                       lw=0.5, label="removed sites (void)")
            t = np.linspace(0, 2 * np.pi, 400)
            for sgn in (-1, 1):
                ax.plot(c0 + sgn * feat.major_radius_A + feat.minor_radius_A * np.cos(t),
                        feat.tube_centre_x_rel_A + feat.minor_radius_A * np.sin(t), color=INK,
                        lw=0.8, label="void outline (distance r from the tube centre line)"
                        if sgn < 0 else None)
            ax.axhline(0.0, color="#2a78d6", lw=0.8, ls="-", label="flat top atomic plane")
            ax.axhline(-cap, color="#1baf7a", lw=0.8, ls="--", label="void top (x_rel = -cap)")
            ax.axhline(bulk_top, color=MUTED, lw=0.8, ls=":",
                       label=f"top of the bulk absorber ({bulk_top:.1f} A)")
            ax.set_xlim(c0 - span, c0 + span)
            ax.set_ylim(bulk_top - 6, 6)
            ax.set_aspect("equal")
            ax.set_xlabel(f"{lab} (A)" + (" along the beam" if lab == "z" else ""))
            ax.set_ylabel("x - x_surface (A)")
            ax.set_title(f"cap {cap:g} A, section along {lab} through the ring centre\n"
                         f"({'z' if axis == 1 else 'y'} in [{lo:.2f}, {hi:.2f}] A, two planes); "
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
    p = out / "supercell_buried.png"
    fig.savefig(p, dpi=130, bbox_inches="tight")
    plt.close(fig)
    return p


def _outline(ax, R, g, color, ls="-"):
    ax.contour(g["y"], g["x_rel"], R.astype(float), levels=[0.5], colors=[color], linewidths=0.9,
               linestyles=ls)


def maps_figure(results: list, out: Path, fname: str, title: str) -> Path:
    n = len(results)
    fig, axs = plt.subplots(n, 3, figsize=(20, 4.2 * n + 0.8), squeeze=False,
                            gridspec_kw=dict(hspace=0.5, wspace=0.3))
    for i, res in enumerate(results):
        g, reg, met = res["g"], res["regions"], res["metrics"]
        xw = (g["x_rel"] >= -50) & (g["x_rel"] <= 25)
        ext = [g["y"][0], g["y"][-1], g["x_rel"][xw][0], g["x_rel"][xw][-1]]
        dphi = np.where(met["mask"], met["dphi"], np.nan)
        rho = np.where(met["mask"], met["rho"] - 1.0, np.nan)
        panels = ((dphi, "RdBu_r", "arg(psi_s psi_s,flat*) (rad)", "phase difference"),
                  (rho, "PuOr_r", "|psi_s| / |psi_s,flat| - 1", "amplitude ratio - 1"),
                  (np.log10(met["diff"] + 1e-16), "magma", "log10 |psi_s - psi_s,flat| / A_ref",
                   "complex difference (no mask)"))
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
            for k in ("P", "V", "E", "C_up"):
                if reg[k].any():
                    _outline(ax, reg[k][xw], dict(y=g["y"], x_rel=g["x_rel"][xw]), C_REGION[k],
                             ls="-" if k in ("P", "V", "E") else "--")
            ax.axhline(0.0, color=INK, lw=0.6, ls=":")
            ax.set_xlabel("y (A)")
            ax.set_ylabel("x - x_surface (A), exit plane")
            ax.set_title(f"{res['label']}: {ttl}", fontsize=9, loc="left", color=INK)
            _clean(ax)
    fig.text(0.01, 1.0 + 0.02 / n, title + ".\nOutlines: blue P = geometric projection of the ring (+2.5 A), "
             "green V = causal vacuum region, orange E = end-face band (finite cell), dashed grey = "
             "upstream control; dotted line = flat surface; grey pixels masked (< 5 % amplitude)",
             fontsize=9, color=INK, va="top")
    p = out / fname
    fig.savefig(p, dpi=110, bbox_inches="tight")
    plt.close(fig)
    return p


def decay_figure(table: dict, fits: dict, out: Path) -> Path:
    fig, axs = plt.subplots(1, 3, figsize=(18, 5), gridspec_kw=dict(wspace=0.3))
    keys = (("max_rel_diff", "max |psi_s - psi_s,flat| / A_ref"),
            ("rms_dphi_rad", "RMS |d phi| (rad)"),
            ("max_abs_ratio_minus_1", "max |ratio - 1|"))
    for ax, (k, lab) in zip(axs, keys):
        for reg, mk in (("P", "o"), ("V", "s"), ("E", "D"), ("C_up", "x"), ("C_y", "+")):
            vals = [table[c]["regions"][reg].get(k, np.nan) for c in CAPS if c in table]
            cs = [c for c in CAPS if c in table]
            ax.semilogy(cs, vals, mk + "-", color=C_REGION[reg], lw=1, label=reg)
            f = fits.get((reg, k))
            if f and f.get("L_A"):
                cc = np.linspace(min(cs), max(cs), 50)
                ax.semilogy(cc, f["S0"] * np.exp(-cc / f["L_A"]), color=C_REGION[reg], lw=0.8,
                            ls=":", label=f"{reg} fit L = {f['L_A']:.1f} A")
        cs = [c for c in CAPS if c in table]
        fl = [FLOOR_FACTOR * max(table[c]["regions"][cr].get(k, 0.0) for cr in ("C_up", "C_y"))
              for c in cs]
        ax.semilogy(cs, fl, color=INK, lw=1.2, ls="--", label=f"{FLOOR_FACTOR:g} x floor (same run)")
        ax.set_xlabel("cap (A)")
        ax.set_ylabel(lab)
        ax.legend(fontsize=7)
        _clean(ax)
    fig.suptitle("Signal versus cap, TEST_ONLY r = 0.1 (" + STATUS + ")", fontsize=9, x=0.01,
                 ha="left", color=INK)
    p = out / "signal_vs_cap.png"
    fig.savefig(p, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return p


def depth_figure(prof: dict, out: Path, caps) -> Path:
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
    ax.set_title(f"flat reference (r = 0.1), exit-plane depth profile; I < 1e-2 below "
                 f"{prof['depth_I_below_1e-2_A']} A, < 1e-4 below {prof['depth_I_below_1e-4_A']} A",
                 fontsize=9, loc="left")
    ax.legend(fontsize=8)
    _clean(ax)
    p = out / "depth_profile_flat_r010.png"
    fig.savefig(p, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return p


# --------------------------------------------------------------------------------------------------
def analyse(root: Path, cap, tag, ew_f, st_f):
    name = name_of(cap, tag)
    p, run = find_run(root, name)
    ew = load_exit_wave(p, expected_plane=PLANE_TEXT)
    st = load_structure(run / f"structure_{name}.npz")
    same = assert_same_cell(ew, ew_f, st, st_f)
    g = geometry(ew, st)
    reg = regions(g, g["core_z0_A"])
    ps, pf = specular(ew), specular(ew_f)
    met = metrics(ps, pf, g, reg)
    raw = np.abs(ew.psi.astype(np.complex128) - ew_f.psi.astype(np.complex128)) / met["A_ref"]
    met["raw_max_rel_diff"] = {k: float(raw[v].max()) for k, v in reg.items()
                               if k != "geom" and v.any()}
    band_y = np.abs(g["y"] - g["yc"]) <= g["R"] + g["r"] + RES_A
    loc = x_centroid(met["diff"], g, band_y)
    t_mid = g["cap"] + g["r"]
    loc["predicted_tube_centre_x_rel_A"] = float((g["Lz"] - g["zc"]) * np.tan(g["th_int"]) - t_mid)
    return dict(name=name, cap=cap, label=f"cap {cap:g} A ({tag})", g=g, regions=reg,
                metrics=met, same=same, loc=loc, st=st, ew=ew)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--runs", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    np.set_printoptions(precision=4)
    print(f"STATUS: {STATUS}")

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

    # ---- print ------------------------------------------------------------------------------
    for (tag, cap), res in results.items():
        g, reg, met = res["g"], res["regions"], res["metrics"]
        print(f"\n=== {res['name']}: cap {cap:g} A, absorption "
              f"{res['st']['physical_absorption']['ratio']} ({res['st']['physical_absorption']['label'][:40]}...)")
        print(f"  identical cell: {res['same']}")
        print(f"  theta_out {g['th_out'] * 1e3:.4f} mrad, theta_int {g['th_int'] * 1e3:.4f} mrad, "
              f"L_z {g['Lz']:.2f} A, ring centre (y, z) = ({g['yc']:.2f}, {g['zc']:.2f}) A cell, "
              f"A_ref {met['A_ref']:.4f}")
        print(f"  regions: {json.dumps(reg['geom'])}")
        for k in ("P", "V", "E", "C_up", "C_y"):
            print(f"  {k:5s} {json.dumps(met['regions'][k])}")
        print(f"  x-location of |d psi_s|: {json.dumps(res['loc'])}")
        print(f"  raw (no aperture) max |psi - psi_flat| / A_ref per region: "
              f"{json.dumps(met['raw_max_rel_diff'])}")

    table = {cap: res["metrics"] for (tag, cap), res in results.items() if tag == "r010"}
    fits = {}
    if table:
        print("\n=== signal table (TEST_ONLY r = 0.1) ===")
        hdr = ("cap", "region", "max|dphi|", "rms dphi", "max|rho-1|", "max|dpsi|/A", "rms|dpsi|/A")
        mets = ("max_abs_dphi_rad", "rms_dphi_rad", "max_abs_ratio_minus_1", "max_rel_diff",
                "rms_rel_diff")
        print("  ".join(f"{h:>11s}" for h in hdr) + "   (value / floor of the same run in [])")
        for cap in CAPS:
            if cap not in table:
                continue
            fl = {m: max(table[cap]["regions"][c].get(m, 0.0) for c in ("C_up", "C_y"))
                  for m in mets}
            for k in ("P", "V", "E", "C_up", "C_y"):
                r = table[cap]["regions"][k]
                cells = []
                for m in mets:
                    v = r.get(m)
                    if v is None:
                        cells.append(f"{'empty':>18s}")
                    elif k in ("C_up", "C_y"):
                        cells.append(f"{v:11.3e}       ")
                    else:
                        cells.append(f"{v:11.3e} [{v / fl[m]:5.1f}]")
                print("  ".join([f"{cap:11g}", f"{k:>11s}"] + cells))
        print("\n=== decay fits S = S0 exp(-cap/L) (caps above 3 x the larger control) ===")
        for k in ("max_rel_diff", "rms_rel_diff", "max_abs_dphi_rad", "rms_dphi_rad",
                  "max_abs_ratio_minus_1"):
            cs = [c for c in CAPS if c in table]
            floors = [max(table[c]["regions"][cr].get(k, 0.0) for cr in ("C_up", "C_y"))
                      for c in cs]
            for reg in ("P", "V", "E"):
                S = [table[c]["regions"][reg].get(k, np.nan) for c in cs]
                S = [s if s is not None and np.isfinite(s) else 0.0 for s in S]
                f = fit_decay(cs, S, floors)
                fits[(reg, k)] = f
                L = f.get("L_A")
                print(f"  {k:22s} {reg:2s} floors {[f'{v:.2e}' for v in floors]}  caps used "
                      f"{f['caps_used']}  "
                      f"L = {('%.2f A' % L) if L else 'none'}"
                      f"{(' +- %.2f' % f['L_stderr_A']) if f.get('L_stderr_A') else ''}  "
                      f"pairwise {[(p['caps'], round(p['L_A'], 2)) for p in f['pairwise']]}")
        print(f"  compare: P2 amplitude extinction depth Lambda = {EXTINCTION_AMP_A} A, intensity "
              f"depth Lambda/2 = {EXTINCTION_AMP_A / 2:.2f} A")

    if "r010" in flats:
        ew_f, st_f = flats["r010"]
        g0 = next(res["g"] for (t, c), res in results.items() if t == "r010") if any(
            t == "r010" for t, _ in results) else None
        if g0 is not None:
            prof = depth_profile(ew_f, g0)
            print(f"\n=== flat reference (r = 0.1) exit-plane depth profile ===\n  I at depths "
                  f"{prof['I_at']}; I < 1e-2 from {prof['depth_I_below_1e-2_A']} A, < 1e-4 from "
                  f"{prof['depth_I_below_1e-4_A']} A (H2 2.4: 26.0 A and 53.2 A)")
            for rec in prof["local"]:
                print(f"  local 1/e lengths {rec}")
            print(f"  {figs_path(depth_figure(prof, args.out, CAPS))}")
    if ("r000", 10.0) in results and ("r010", 10.0) in results:
        a, b = results[("r010", 10.0)]["metrics"]["regions"], results[("r000", 10.0)]["metrics"][
            "regions"]
        print("\n=== absorption dependence, cap 10 A: r = 0.1 vs r = 0 (each against its own flat) ===")
        for k in ("P", "V", "E", "C_up", "C_y"):
            print(f"  {k:5s} r=0.1 {json.dumps(a[k])}\n        r=0   {json.dumps(b[k])}")

    # geometric engine: the surface is flat
    for (tag, cap), res in results.items():
        f = res["st"]["feature"]
        g = res["g"]
        zs = g["Lz"] - np.clip(g["x_rel"], 0, None) / np.tan(g["th_out"]) - g["crystal_start_z_A"]
        Y, Z = np.meshgrid(g["y"], zs, indexing="ij")
        h = f.layer_height_A(Y, Z, layer_spacing_A=res["st"]["metadata"]["lattice"]["a_A"] / 4)
        phi = geometric_step_phase(float(np.max(np.abs(h))), g["th_out"], g["lam"])
        print(f"geometric engine, {res['name']}: max |layer_height_A| over the exit-plane sources = "
              f"{np.max(np.abs(h)):.1f} A -> phase {phi:+.1f} rad, amplitude ratio 1 (zero signal)")

    # ---- figures ----------------------------------------------------------------------------
    structs = {cap: res["st"] for (tag, cap), res in results.items() if tag == "r010"}
    if structs:
        print(figs_path(supercell_figure(structs, args.out)))
    r010 = [results[("r010", c)] for c in CAPS if ("r010", c) in results]
    if r010:
        print(figs_path(maps_figure(r010, args.out, "signal_maps_r010.png",
                                    "Specular beam minus flat reference, TEST_ONLY r = 0.1, " + STATUS)))
        print(figs_path(decay_figure(table, fits, args.out)))
    r0 = [results[k] for k in (("r010", 10.0), ("r000", 10.0)) if k in results]
    if len(r0) == 2:
        print(figs_path(maps_figure(r0, args.out, "signal_maps_cap10_absorption.png",
                                    "cap 10 A with TEST_ONLY r = 0.1 (top) and without absorption "
                                    "B30 (bottom), " + STATUS)))
    return 0


def figs_path(p):
    return f"figure: {p}"


if __name__ == "__main__":
    raise SystemExit(main())
