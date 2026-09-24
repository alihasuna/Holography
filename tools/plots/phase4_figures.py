#!/usr/bin/env python3
"""Phase 4 figures for Ali (orchestrator, 2026-09-24). Every plotted number comes from a committed file.

  solver   the independent-solver comparison of reports S5/E8: sim-trhepd-rheed (patched to write the
           complex amplitude) against this repository's multislice engine, flat bulk-terminated
           Si(001), 200 keV, specular (0,0) rod, both codes with the solver's Doyle-Turner potential
           and the proportional absorption r = 0.1 (TEST_ONLY stand-in for item 21), static lattice.
           Data: tools/validation/rheed_solver_results.json (solver) and rheed_engine_results.json
           (engine), paired exactly as tools/validation/rheed_solver_compare.py does (plane R_layer).
  surface  a reconstructed Si(001) staircase built by the E2 builder (Ramstad et al. 1995 coordinates;
           report E2, audit A5): top-layer atoms and dimer bonds, showing the 90 degree rotation of the
           dimer rows across a/4 steps and none across an a/2 step.

Run with the code of a reviewed commit on PYTHONPATH, e.g.
  PYTHONPATH=<worktree> venv/bin/python tools/plots/phase4_figures.py solver --repo <worktree> --out DIR
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

# reference palette of the dataviz method (categorical slots 1 and 2, light surface; validated set)
C_SOLVER = "#2a78d6"
C_ENGINE = "#eb6834"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def _style(ax):
    ax.set_facecolor(SURF)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(INK2)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.grid(True, color=GRID, lw=0.6)
    ax.set_axisbelow(True)


def _load_compare(repo: Path):
    spec = importlib.util.spec_from_file_location("rsc", repo / "tools/validation/rheed_solver_compare.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["rsc"] = m
    spec.loader.exec_module(m)
    return m


def fig_solver(repo: Path, out: Path) -> None:
    rsc = _load_compare(repo)
    sol = json.loads((repo / "tools/validation/rheed_solver_results.json").read_text())
    eng = json.loads((repo / "tools/validation/rheed_engine_results.json").read_text())
    cases = [("[100]", "fine_a100_N6_r010", "eng_a100_N6_r010", "eng_a100_dt_r010"),
             ("[110]", "fine_a110_N9_r010", "eng_a110_N9_r010", "eng_a110_dt_r010")]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.2), facecolor="white")
    lines = []
    for row, (az, fine, pair, etag) in enumerate(cases):
        ts, Rs = rsc.solver_curve(sol, fine)
        te, Re, _sp, _recs = rsc.engine_curve(eng, etag)
        tp, Rp = rsc.solver_curve(sol, pair)
        Rp = rsc.at_angles(tp, Rp, te)
        dphi = np.angle(Re * np.conj(Rp))
        rel = np.abs(Re) / np.abs(Rp) - 1
        lines.append(f"{az}: {len(te)} engine angles; max |d arg| {np.max(np.abs(dphi)):.3f} rad; "
                     f"median |d arg| {np.median(np.abs(dphi)):.3f} rad; "
                     f"d|R|/|R| {rel.min():+.3f} to {rel.max():+.3f}")
        for t, i_s, i_e, x in zip(te, np.abs(Rp) ** 2, np.abs(Re) ** 2, dphi):
            if abs(x) > 0.05:
                lines.append(f"   {az} {t:.2f} mrad: |R|^2 solver {i_s:.5f} engine {i_e:.5f}, d arg {x:+.3f} rad")
        a0, a1 = axes[row]
        for ax in (a0, a1):
            _style(ax)
        a0.plot(ts, np.abs(Rs) ** 2, color=C_SOLVER, lw=2, label="independent solver (sim-trhepd-rheed)")
        a0.plot(te, np.abs(Re) ** 2, "o", color=C_ENGINE, ms=6, mec="white", mew=1.2,
                label="our multislice engine")
        a0.set_ylabel("reflectivity |R|²", color=INK)
        a1.plot(ts, np.unwrap(np.angle(Rs)), color=C_SOLVER, lw=2)
        # engine phase placed on the solver's unwrapped branch at the same angle
        ref = np.interp(te, ts, np.unwrap(np.angle(Rs)))
        a1.plot(te, ref + dphi, "o", color=C_ENGINE, ms=6, mec="white", mew=1.2)
        a1.set_ylabel("reflection phase arg R (rad)", color=INK)
        a0.set_title(f"azimuth {az}: reflectivity", color=INK, fontsize=11, loc="left")
        a1.set_title(f"azimuth {az}: phase", color=INK, fontsize=11, loc="left")
        for ax in (a0, a1):
            ax.set_xlabel("glancing angle (mrad)", color=INK)
            ax.set_xlim(11.8, 22.2)
        if row == 0:
            a0.legend(frameon=False, fontsize=9, loc="upper right")
    fig.suptitle("Flat Si(001), 200 keV, specular beam: our engine vs an independent dynamical solver\n"
                 "same Doyle-Turner potential, absorption r = 0.1 (TEST_ONLY), static lattice "
                 "(reports S5, E8)", color=INK, fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(out / "solver_vs_engine.png", dpi=150)
    print("\n".join(lines))


def fig_surface(repo: Path, out: Path) -> None:
    sys.path.insert(0, str(repo / "tests/structure"))
    from si001_test_inputs import build  # noqa: E402
    from reflection_holo.structure import Staircase  # noqa: E402
    st = Staircase(edges="transverse", terrace_layers=(0, 2, 1), terrace_widths=(4, 4, 4),
                   boundary_step_layers=-1)
    s = build(st, azimuth=(1, 1, 0), edge_periods=4, substrate_layers=12, backbond=(1, 1, 0),
              termination="c(4x2)")
    tops = np.array([t["top_layer_index"] for t in s.metadata["terrace_map"]])
    top = s.layer_index == tops[s.terrace_index]
    pos = s.positions_A
    P = pos[top]
    Ly, Lz = s.cell_A[1, 1], s.cell_A[2, 2]
    fig, ax = plt.subplots(figsize=(11, 4.6), facecolor="white")
    _style(ax)
    ax.grid(False)
    # dimer bonds: top-layer pairs of one terrace closer than 2.6 A (bulk nearest in-plane is 3.84 A)
    idx = np.nonzero(top)[0]
    nb = 0
    for i in range(len(idx)):
        d = pos[idx] - pos[idx[i]]
        d[:, 1] -= Ly * np.rint(d[:, 1] / Ly)
        d[:, 2] -= Lz * np.rint(d[:, 2] / Lz)
        r = np.linalg.norm(d, axis=1)
        for j in np.nonzero((r > 0.1) & (r < 2.6))[0]:
            if j > i and s.terrace_index[idx[j]] == s.terrace_index[idx[i]]:
                a, b = pos[idx[i]], pos[idx[i]] + d[j]
                ax.plot([a[2], b[2]], [a[1], b[1]], color=INK2, lw=1.4, zorder=1)
                nb += 1
    sc = ax.scatter(P[:, 2], P[:, 1], c=P[:, 0], cmap="Blues", s=26, edgecolors=INK2, linewidths=0.4,
                    zorder=2)
    cb = fig.colorbar(sc, ax=ax, pad=0.01)
    cb.set_label("height of the atom above the reference (A)", color=INK)
    ax.set_xlabel("along the beam z (A)", color=INK)
    ax.set_ylabel("across the beam y (A)", color=INK)
    ax.set_aspect("equal")
    ax.set_title("c(4x2)-reconstructed Si(001) staircase (Ramstad et al. 1995; E2 builder): terraces "
                 "a/2 up, a/4 down, a/4 down.\nDimer rows rotate by 90 deg across each a/4 step, not "
                 "across the a/2 step", color=INK, fontsize=11, loc="left")
    fig.tight_layout()
    fig.savefig(out / "si001_c4x2_staircase.png", dpi=150)
    print(f"surface: {len(P)} top-layer atoms, {nb} dimer bonds drawn")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("figure", choices=("solver", "surface"))
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    (fig_solver if a.figure == "solver" else fig_surface)(a.repo, a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
