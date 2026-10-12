#!/usr/bin/env python3
"""Si[110] cleave-edge slab with (1,-1,1) terraces, ported from hussienba/si110-reflection-holography @ 6694959.

Runs in: em-abtem (CPU; ase, scipy). No GPU.

    gemicro run --kind sim --name slab --params params/slab.yaml --output sims/slab -- \
        /opt/envs/em-abtem/bin/python code/si110_cleave_slab_generator.py --params params/slab.yaml --output sims/slab

Slab frame (docs/physics_conventions.md): x = [1,-1,1]/√3 outward surface normal, y = [1,-1,-2]/√6 in plane
(step edges run along the beam), z = [1,1,0]/√2 beam direction; right-handed. Terraces are bands along y whose
surface is lowered by an integer number of (1,-1,1) bilayers (d_111 = a/√3), so step edges run along the beam.

Changes from the original generator (audit docs/agent_reports/A_code_audit.md):
  M7   half-open periodic bounds in y and z (no duplicated atomic plane), plus a periodic duplicate-atom check
  M8   the realised geometry (surface height of every terrace, back face, vacuum) is measured and written
  spec §4.2  the terrace sequence must be cyclic under the periodic boundary (no hidden multi-bilayer step)
  spec §4.1  a target reflection is refused if it is kinematically forbidden or not on the specular rod
  every setting from the parameter file (no argparse defaults); outputs: extxyz (exact cell), CIF, slab.json
"""

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:] = [p for p in sys.path if p not in ("", ".") and Path(p).resolve() != HERE] + [str(HERE)]

import numpy as np  # noqa: E402

import holo_common as hc  # noqa: E402
from holo_optics import diamond_structure_factor  # noqa: E402


def slab_rotation_matrix():
    """Rows: slab x, y, z expressed in cubic crystal coordinates (active rotation r_slab = R r_crystal)."""
    e_x = np.array([1, -1, 1], float) / math.sqrt(3)
    e_y = np.array([1, -1, -2], float) / math.sqrt(6)
    e_z = np.array([1, 1, 0], float) / math.sqrt(2)
    R = np.array([e_x, e_y, e_z])
    assert np.allclose(R @ R.T, np.eye(3), atol=1e-12) and np.isclose(np.linalg.det(R), 1.0)
    return R


def build_si110_step_slab(a_A, n_x_si, n_y, n_z_si, x_vac_A, z_vac_A, terrace_heights_A):
    """Slab in the slab frame; terraces are N equal y-bins whose surface is lowered by terrace_heights_A[i].
    Returns (atoms, dims) with dims measured on the realised atom positions."""
    from ase.build import bulk

    period_x = a_A * math.sqrt(3.0)
    period_y = a_A * math.sqrt(1.5)
    period_z = a_A / math.sqrt(2.0)
    Lx_si, Ly, Lz_si = n_x_si * period_x, n_y * period_y, n_z_si * period_z
    Lx, Lz = Lx_si + 2.0 * x_vac_A, Lz_si + 2.0 * z_vac_A

    L_diag = math.sqrt(Lx * Lx + Ly * Ly + Lz * Lz)
    n_cubic = int(math.ceil(L_diag / a_A)) + 2
    big = bulk("Si", "diamond", a=a_A, cubic=True).repeat((n_cubic, n_cubic, n_cubic))
    big.positions -= big.cell.sum(axis=0) / 2.0
    R = slab_rotation_matrix()
    big.positions = big.positions @ R.T
    x, y, z = big.positions.T

    d_111 = a_A / math.sqrt(3.0)
    # half-open in the periodic directions (audit M7: strict inequalities at both ends duplicated a plane)
    eps = 1e-6  # rotated lattice planes land on the bounds to within rounding: decide them consistently
    in_y = (y >= -Ly / 2.0 - eps) & (y < Ly / 2.0 - eps)
    in_z = (z >= -Lz_si / 2.0 - eps) & (z < Lz_si / 2.0 - eps)
    in_x_pre = (x > -Lx_si / 2.0 - d_111) & (x < Lx_si / 2.0 + d_111)
    in_slab = in_y & in_z & in_x_pre

    # Cut planes in the wide (2.35 Å) inter-bilayer gap, located empirically on the folded x positions.
    fold = np.mod(x[in_slab], d_111)
    hist, edges = np.histogram(fold, bins=200, range=(0.0, d_111))
    centres = 0.5 * (edges[:-1] + edges[1:])
    order = np.argsort(hist)[::-1]
    p1, p2 = sorted([centres[order[0]], centres[order[1]]])
    wide_mid = (0.5 * (p1 + p2) + 0.5 * d_111) % d_111
    # restrict to the intended Si band: top of the band near +Lx_si/2, back near -Lx_si/2
    band = in_slab & (x <= Lx_si / 2.0) & (x >= -Lx_si / 2.0)
    x_top_atom = float(x[band].max())
    off = (wide_mid - x_top_atom) % d_111
    x_top_high = x_top_atom + (off if off > 1e-6 else d_111)
    x_back_atom = float(x[band].min())
    off_b = (x_back_atom - wide_mid) % d_111
    x_back = x_back_atom - (off_b if off_b > 1e-6 else d_111)

    heights = np.asarray(terrace_heights_A, float)
    N = len(heights)
    t_idx = np.clip(np.floor((y + Ly / 2.0 + eps) / Ly * N).astype(int), 0, N - 1)
    keep = (x > x_back) & (x < x_top_high - heights[t_idx]) & in_y & in_z
    del big[~keep]
    shift = np.array([Lx / 2.0, Ly / 2.0, Lz / 2.0])
    big.positions += shift
    big.set_cell(np.diag([Lx, Ly, Lz]), scale_atoms=False)
    big.set_pbc((True, True, True))

    # measured geometry (audit M8): what the downstream stages and the analysis actually see
    pos = big.positions
    tb = np.clip(np.floor((pos[:, 1] + eps) / Ly * N).astype(int), 0, N - 1)
    x_top_meas = [float(pos[tb == i, 0].max()) for i in range(N)]
    dims = dict(
        Lx_A=Lx, Ly_A=Ly, Lz_A=Lz, period_x_A=period_x, period_y_A=period_y, period_z_A=period_z,
        d_111_A=d_111, n_terraces=N,
        x_cut_back_A=x_back + Lx / 2.0, x_cut_top_A=[float(x_top_high - h + Lx / 2.0) for h in heights],
        x_top_atom_A=x_top_meas, x_back_atom_A=float(pos[:, 0].min()),
        vacuum_above_highest_atom_A=float(Lx - max(x_top_meas)), vacuum_below_back_atom_A=float(pos[:, 0].min()),
        z_first_atom_A=float(pos[:, 2].min()), z_last_atom_A=float(pos[:, 2].max()),
        terrace_y_edges_A=[float(i * Ly / N) for i in range(N + 1)],
    )
    return big, dims


def check_duplicates(atoms, r_min_A):
    """Periodic minimum-image pairs closer than r_min (Si–Si bond 2.35 Å): duplicated planes would show here."""
    from scipy.spatial import cKDTree
    box = np.diag(atoms.cell.array)
    p = np.mod(atoms.positions, box)
    p = np.where(p >= box, p - box, p)  # np.mod(-1e-16, L) == L in floating point
    pairs = cKDTree(p, boxsize=box).query_pairs(r_min_A)
    return len(pairs)


def expected_atom_count(dims, n_y, n_z, a_A):
    """Exact count when every terrace is a whole number of y periods: 2 atoms per (1,-1,1) bilayer per surface
    cell of area a²√3/4; a terrace of width w along y and length Lz_si holds (w Lz_si)/(a²√3/4) cells."""
    N = dims["n_terraces"]
    if n_y % N:
        return None
    cells = (n_y // N) * dims["period_y_A"] * n_z * dims["period_z_A"] / (a_A * a_A * math.sqrt(3) / 4)
    bil = [round((t - dims["x_cut_back_A"]) / dims["d_111_A"]) for t in dims["x_cut_top_A"]]
    return int(round(2 * cells * sum(bil)))


def reflection_geometry(hkl, a_A, energy_keV, V0):
    """Vacuum Bragg angle of a specular reflection, the refraction-corrected external angle, the wrap period."""
    R = slab_rotation_matrix()
    F = diamond_structure_factor(hkl)
    if abs(F) < 1e-9:
        raise SystemExit(f"target reflection {hkl} is kinematically forbidden in diamond-cubic Si (F = 0); "
                         f"use e.g. (4,-4,4), (5,-5,5), (7,-7,7), (8,-8,8) on this surface")
    g = R @ (np.asarray(hkl, float) / a_A)  # cycles/Å in the slab frame
    if abs(g[1]) > 1e-9 or abs(g[2]) > 1e-9 or g[0] <= 0:
        raise SystemExit(f"target reflection {hkl} is not on the specular rod (n,-n,n) of the (1,-1,1) surface "
                         f"(g in slab frame = {g.round(6).tolist()}); a non-specular target needs the accessibility "
                         f"analysis of docs/03_physics_summary.md and is not supported here")
    lam = hc.wavelength_A(energy_keV)
    d = 1.0 / np.linalg.norm(g)
    s = lam / (2 * d)
    T = energy_keV * 1e3
    Delta = V0 * (1 + T / hc.M_E_C2_EV) / (T * (1 + T / (2 * hc.M_E_C2_EV)))
    sin2_ext = s * s * (1 + Delta) - Delta
    th_ext = math.asin(math.sqrt(sin2_ext)) if sin2_ext > 0 else None
    return {"hkl": list(hkl), "abs_F_over_f": abs(F), "d_A": d, "g_slab_inv_A": g.tolist(),
            "theta_B_vacuum_mrad": 1e3 * math.asin(s),
            "theta_ext_at_bragg_peak_mrad": None if th_ext is None else 1e3 * th_ext,
            "refraction_Delta": Delta, "mean_inner_potential_V": V0,
            "wrap_period_A_at_peak": None if th_ext is None else lam / (2 * math.sin(th_ext)),
            "note": "theta_ext from sin²θ_ext = sin²θ_B (1+Δ) - Δ (relativistic Δ, docs/physics_conventions.md); "
                    "V0 is an ASSUMPTION until measured"}


def run(P, out):
    a = P.num("lattice_constant_A", lo=1.0)
    n_x = P.integer("n_x_si", lo=1)
    n_y = P.integer("n_y", lo=1)
    n_z = P.integer("n_z_si", lo=1)
    xv = P.num("x_vacuum_A", lo=0.0)
    zv = P.num("z_vacuum_A", lo=0.0)
    terr = P.vec("terraces_bilayers", integer=True)
    if not terr:
        raise hc.ParamError("terraces_bilayers needs at least one entry ([0] = flat slab)")
    if min(terr) < 0 or max(terr) >= n_x:
        raise hc.ParamError(f"terraces_bilayers {terr} must lie in [0, n_x_si) bilayers")
    steps = [terr[(i + 1) % len(terr)] - terr[i] for i in range(len(terr))]
    if len(terr) > 1 and abs(steps[-1]) > 1:
        raise hc.ParamError(f"terraces_bilayers {terr}: the periodic boundary joins the last terrace to the first "
                            f"with a hidden {steps[-1]:+d}-bilayer step (spec §4.2); use a cyclic sequence such as "
                            f"[0, 1, 2, 1]")
    tgt = P.req("target_reflection")
    refl = None
    if tgt is not None:
        T = P.sub("target_reflection")
        refl = reflection_geometry(T.vec("hkl", 3, integer=True), a, T.num("energy_keV", lo=1.0),
                                   T.num("mean_inner_potential_V", lo=0.0))
    P.finish()

    d111 = a / math.sqrt(3.0)
    atoms, dims = build_si110_step_slab(a, n_x, n_y, n_z, xv, zv, [u * d111 for u in terr])
    expected = expected_atom_count(dims, n_y, n_z, a)
    if expected is not None and expected != len(atoms):
        raise SystemExit(f"{len(atoms)} atoms, expected {expected} for the declared bilayers (a plane is missing "
                         f"or duplicated at a cell or terrace boundary)")
    ndup = check_duplicates(atoms, 1.0)
    if ndup:
        raise SystemExit(f"{ndup} atom pairs closer than 1.0 Å under periodic boundaries: duplicated planes")
    meas = np.array(dims["x_top_atom_A"])
    meas_steps = [(meas[(i + 1) % len(meas)] - meas[i]) / d111 for i in range(len(meas))]
    bad = [i for i, (m, s) in enumerate(zip(meas_steps, steps)) if abs(m + s) > 0.05]
    if bad:  # a deeper terrace has a LOWER surface: measured step = -declared step
        raise SystemExit(f"realised steps {np.round(meas_steps, 3).tolist()} bilayers disagree with the declared "
                         f"{[-s for s in steps]}")

    from ase.io import write
    write(out.path("si110_slab.extxyz"), atoms, format="extxyz")
    write(out.path("si110_slab.cif"), atoms)

    plots = []
    plt = hc._plt()
    if plt is not None:
        fig, axs = plt.subplots(1, 2, figsize=(10, 4.2))
        p = atoms.positions
        sel = p[:, 2] < p[:, 2].min() + dims["period_z_A"]  # one z period for clarity
        axs[0].scatter(p[sel, 1], p[sel, 0], s=1, c="k")
        for e in dims["terrace_y_edges_A"]:
            axs[0].axvline(e, color="r", lw=0.5)
        axs[0].set_xlabel("y (Å)  [1,-1,-2]")
        axs[0].set_ylabel("x (Å)  surface normal [1,-1,1]")
        axs[0].set_title("terraces seen along the beam (one z period)", fontsize=9)
        axs[1].scatter(p[:, 2], p[:, 0], s=0.2, c="k")
        axs[1].set_xlabel("z (Å)  beam [110]")
        axs[1].set_ylabel("x (Å)")
        axs[1].set_title("side view", fontsize=9)
        fig.tight_layout()
        fig.savefig(out.path("slab_views.png"), dpi=130)
        plt.close(fig)
        plots.append("slab_views.png")

    frame = {"rows_in_crystal_coordinates": slab_rotation_matrix().tolist(),
             "x": "[1,-1,1] outward surface normal", "y": "[1,-1,-2] in plane", "z": "[110] beam"}
    physics = {"lattice_constant_A": a, "frame": frame, "geometry": dims, "n_atoms": len(atoms),
               "terraces_bilayers": terr, "steps_bilayers_cyclic": steps, "realised_steps_bilayers": meas_steps,
               "target_reflection": refl, "structure_files": ["si110_slab.extxyz", "si110_slab.cif"]}
    summary = {"atoms": len(atoms), "box_A": [dims["Lx_A"], dims["Ly_A"], dims["Lz_A"]],
               "terrace_tops_A": [round(v, 4) for v in dims["x_top_atom_A"]],
               "vacuum_above_A": round(dims["vacuum_above_highest_atom_A"], 3), "plots": plots}
    return physics, summary


def main(argv=None):
    ap = hc.common_cli("Si[110] cleave-edge slab with (1,-1,1) terraces (env: em-abtem)", [])
    a = ap.parse_args(argv)
    raw = hc.load_params(a.params)
    out = hc.Output(a.output, a.overwrite)
    physics, summary = run(hc.Section(raw), out)
    prov = hc.provenance(sys.argv, a.params, {})
    hc.write_sidecar(out, "slab", raw, prov, physics, summary)
    out.publish()
    hc.print_summary("si110 slab", summary, out.final, out.files)


if __name__ == "__main__":
    main()
