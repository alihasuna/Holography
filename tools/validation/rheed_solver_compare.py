#!/usr/bin/env python
"""S5: an independent dynamical reflection solver against the repository's multislice engine for the
flat, bulk-terminated Si(001) specular rocking curve through (0,0,8) at 200 keV: |R|^2 AND arg R.

Report: docs/agent_reports/S5_independent_rheed_solver.md (every number there is printed here).

Solver: sim-trhepd-rheed (T. Hanada et al., GPL-3.0; upstream commit d98d6252 of
https://github.com/sim-trhepd-rheed/sim-trhepd-rheed), Ichimiya's surface-parallel multislice with
the recursive reflection-matrix technique. It is NOT part of this repository: it is cloned, patched
(ep='E' for electrons and one extra output line with the complex reflection matrix column; the diff is
in the report) and built OUTSIDE the repository; this script only writes its input files, runs the
two executables through subprocess and parses their text output. No GPL code or table is copied here:
the Doyle-Turner parameters that the solver uses are READ from the solver's asf.f90 at run time and
stored, with that file's SHA-256, in the results file.

Engine: reflection_holo.forward.multislice (report M2; UNVALIDATED), run directly on flat Si(001)
strips as in report H2 (tools/hpc/supercell_sizing.py, flat_strip), with either its production
Kirkland potential (abTEM 1.0.10) or, for a like-for-like test of the METHOD, the same Doyle-Turner
scattering factors the solver uses (class DoyleTurnerPotential below: TEST_ONLY, the engine code is
unchanged, only the scattering-factor function differs).

Conventions (docs/physics_conventions.md): exp(+i k.r - i omega t); theta = external glancing angle;
R = complex specular reflection coefficient referred to the plane of the TOP-LAYER NUCLEI (the engine's
`highest_surface_x_A`); angles printed in mrad; phases in rad.

Modes
  (default)             report: print every number of the S5 report from the stored results
                        (rheed_solver_results.json, rheed_engine_results.json) and the analytic
                        quantities; exit status 1 if a self-check fails. The comparison verdicts use
                        the tolerances TOL_* declared below.
  --solver-run          run the solver cases (needs --solver-build, --solver-clone, --patch,
                        --workdir); results are merged into rheed_solver_results.json.
  --engine-run CASE     run the engine for one case of ENGINE_CASES (optionally --angles-mrad a b ..),
                        results merged into rheed_engine_results.json after every angle (resumable).

Labels: SECTION_READ, REPRODUCED, DERIVED_HERE, ASSUMPTION, TEST_ONLY, UNVERIFIED, MEASURED_HERE (a
number from the UNVALIDATED engine in this container).
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_v, "4")

import argparse  # noqa: E402
import concurrent.futures as cf  # noqa: E402
import dataclasses  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
import resource  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
SOLVER_JSON = HERE / "rheed_solver_results.json"
ENGINE_JSON = HERE / "rheed_engine_results.json"

from reflection_holo.constants import A_SI_A, DIAMOND_BASIS, HC_EV_M, M_E_C2_EV  # noqa: E402

E_KEV = 200.0                     # PROJECT_INPUT item 1 (Ali, 2026-09-22)
A = A_SI_A                        # ASSUMPTION B2
Q = A / 4.0                       # (001) layer spacing
AS = A / np.sqrt(2.0)             # side of the primitive (1x1) surface cell, along <110>
HC_EV_A = HC_EV_M * 1e10
C_VA2 = HC_EV_A**2 / (2.0 * np.pi * M_E_C2_EV)   # h^2/(2 pi m0 e) in V A^2 (DERIVED_HERE)

# ---- solver model (DERIVED_HERE; report section 3) -----------------------------------------------
# Surface cell a_s1 = (a/2)[1,1,0], a_s2 = (a/2)[-1,1,0], outward normal [0,0,1]. Crystal layer n
# (z = n a/4) has one atom per cell at fractional (u, v) = LAYER_UV[n % 4] (from DIAMOND_BASIS:
# u = X + Y, v = Y - X in cubic units). Odd layers have their back-bonds along [1,1,0] (= a_s1), the
# engine's flat strips use first_terrace_backbond_uvw=(1,1,0), so the top layer is always odd here.
LAYER_UV = {0: (0.0, 0.0), 1: (0.5, 0.0), 2: (0.5, 0.5), 3: (0.0, 0.5)}
CC = A / 2.0                      # solver bulk unit: two layers, next unit shifted by (1/2, 1/2)
Z0 = A / 8.0                      # height of the unit's first layer inside the unit (0 <= z < CC)
DTHICK_A = 4.0                    # vacuum tail region kept above the top layer (solver input)
SOLVER_E_REST_KEV = 511.001       # the solver's m c^2 (scpot.f90:25, SECTION_READ)
SOLVER_EK = 0.262466              # the solver's 2 m e / hbar^2 in A^-2 eV^-1 (scpot.f90:25)


def beams_for(azimuth: str, N: int):
    """ZOLZ rods perpendicular to the beam and the solver azimuth phi (deg, from a_s1)."""
    if azimuth == "100":          # beam along a_s1 + a_s2 = a[0,1,0], equivalent to [1,0,0] (mirror)
        return [(h, -h) for h in range(-N, N + 1)], 45.0
    if azimuth == "100m":         # beam along a_s1 - a_s2 = a[1,0,0] (symmetry check)
        return [(h, h) for h in range(-N, N + 1)], -45.0
    if azimuth == "110":          # beam along a_s1 = (a/2)[1,1,0], the top-layer back-bond axis
        return [(0, k) for k in range(-N, N + 1)], 0.0
    if azimuth == "110perp":      # beam along a_s2 = (a/2)[-1,1,0]: back-bonds of the top layer
        #                           PERPENDICULAR to the beam (orientation check, report section 6)
        return [(h, 0) for h in range(-N, N + 1)], 90.0
    if azimuth == "100disk":      # every rod with |g| <= N/a (HOLZ test at [100])
        out = [(h, k) for h in range(-12, 13) for k in range(-12, 13)
               if np.hypot(h, k) * np.sqrt(2.0) / A <= N / A + 1e-9]
        return out, 45.0
    raise ValueError(azimuth)


def rod_g_per_A(hk) -> float:
    return float(np.hypot(*hk) * np.sqrt(2.0) / A)


@dataclasses.dataclass(frozen=True)
class SolverCase:
    name: str
    azimuth: str
    N: int
    sap: float
    approach: str                 # "B": thick slab of 'surface' atoms, zero bulk (default);
    #                               "A": bulk.exe unit-layer recursion (ML units) + ideal surface
    grid: str                     # "fine" | "engine" | "check" | "onebeam"
    dz_A: float = 0.01
    slab_layers: int = 90         # approach B (even: top layer odd)
    ML: int = 300                 # approach A


def angle_grids():
    """Uniform angle grids (mrad): the solver needs uniform steps (GI, GF, DG)."""
    return {
        "fine": [(12.0, 22.0, 0.02)],
        "check": [(12.0, 22.0, 1.0)],
        "onebeam": [(12.0, 22.0, 0.5)],
        "engine100": [(12.0, 22.0, 1.0), (15.6, 16.8, 0.1)],
        "engine110": [(12.0, 22.0, 1.0)] + [(t, t, 0.0) for t in ENGINE_EXTRA_110],
        "h2": [(H2_THETA_MRAD, H2_THETA_MRAD, 0.0)],
        "holz": [(t, t, 0.0) for t in (12.0, 16.2, 21.0)],
    }


# the angle of report H2's stored flat-strip measurements (tools/hpc/supercell_sizing_measurements.json,
# info.theta_ext_rad: the (0,0,8) condition with the Kirkland MIP)
H2_THETA_MRAD = 16.134748438027965


# Engine angles (mrad), fixed from the solver's fine curves before any engine-solver comparison
# (report section 5): 1 mrad over 12-22 mrad (reduced from 0.5 mrad for CPU time: about 110 s per
# engine angle on the shared cores), 0.1 mrad through the [100] (0,0,8) peak (solver 16.16 mrad),
# and the [110] solver peaks.
ENGINE_COARSE = [12.0 + 1.0 * i for i in range(11)]
ENGINE_FINE_100 = [round(15.6 + 0.1 * i, 4) for i in range(13)]
ENGINE_EXTRA_110 = [12.3, 15.1, 17.6, 18.6]

SOLVER_CASES = [
    # 1-beam cases: the same structure as the main cases, only the (0,0) rod; compared with an
    # independent 1D integration (convention, reference plane and units test)
    SolverCase("onebeam_r010", "100", 0, 0.1, "B", "onebeam", slab_layers=60),
    SolverCase("onebeam_r000", "100", 0, 0.0, "B", "onebeam", slab_layers=60),
    # numerical checks on a 1 mrad grid (approach A against B; rods; slab; dz)
    SolverCase("chk_a100_N4_A", "100", 4, 0.1, "A", "check"),
    SolverCase("chk_a100_N4_B", "100", 4, 0.1, "B", "check"),
    SolverCase("chk_a100_N6_A", "100", 6, 0.1, "A", "check"),
    SolverCase("chk_a100_N6_B", "100", 6, 0.1, "B", "check"),
    SolverCase("chk_a100_N8_B", "100", 8, 0.1, "B", "check"),
    SolverCase("chk_a100_N10_B", "100", 10, 0.1, "B", "check"),
    SolverCase("chk_a100_N6_B_slab180", "100", 6, 0.1, "B", "check", slab_layers=180),
    SolverCase("chk_a100_N6_A_dz005", "100", 6, 0.1, "A", "check", dz_A=0.005),
    SolverCase("chk_a100_N6_A_dz02", "100", 6, 0.1, "A", "check", dz_A=0.02),
    SolverCase("chk_a100m_N6_A", "100m", 6, 0.1, "A", "check"),
    SolverCase("chk_a110_N9_A", "110", 9, 0.1, "A", "check"),
    SolverCase("chk_a110_N9_B", "110", 9, 0.1, "B", "check"),
    SolverCase("chk_a110_N12_B", "110", 12, 0.1, "B", "check"),
    SolverCase("chk_a110_N9_A_dz005", "110", 9, 0.1, "A", "check", dz_A=0.005),
    # main curves on the 0.02 mrad grid, approach A (bulk.exe + ideal truncation), the like-for-like
    # rod sets (every ZOLZ rod inside the engine's 2/3 band at dy = 0.13 A: |g| <= 2.56 1/A)
    SolverCase("fine_a100_N6_r010", "100", 6, 0.1, "A", "fine"),
    SolverCase("fine_a110_N9_r010", "110", 9, 0.1, "A", "fine"),
    SolverCase("fine_a100_N6_r000_ML150", "100", 6, 0.0, "A", "fine", ML=150),
    SolverCase("fine_a100_N6_r000_ML300", "100", 6, 0.0, "A", "fine", ML=300),
    SolverCase("fine_a110_N9_r000_ML150", "110", 9, 0.0, "A", "fine", ML=150),
    SolverCase("fine_a110_N9_r000_ML300", "110", 9, 0.0, "A", "fine", ML=300),
    # the (0,0) rod alone on the fine grid (what the many-beam rods change at the (0,0,8) peak)
    SolverCase("fine_a100_N0_r010", "100", 0, 0.1, "A", "fine"),
    # at exactly the engine angles (like-for-like rods, and rod-set sensitivity)
    SolverCase("eng_a100_N6_r010", "100", 6, 0.1, "A", "engine100"),
    SolverCase("eng_a100_N8_r010_B", "100", 8, 0.1, "B", "engine100"),
    SolverCase("eng_a100_N10_r010_B", "100", 10, 0.1, "B", "engine100"),
    SolverCase("eng_a110_N9_r010", "110", 9, 0.1, "A", "engine110"),
    SolverCase("eng_a110_N12_r010_B", "110", 12, 0.1, "B", "engine110"),
    SolverCase("eng_a110perp_N9_r010", "110perp", 9, 0.1, "A", "engine110"),
    # at report H2's angle (cross-check of H2's stored engine plateaus, report section 6)
    SolverCase("h2_a100_N6_r010", "100", 6, 0.1, "A", "h2"),
    SolverCase("h2_a110_N9_r010", "110", 9, 0.1, "A", "h2"),
    SolverCase("h2_a100_N6_r000_ML150", "100", 6, 0.0, "A", "h2", ML=150),
    SolverCase("h2_a100_N6_r000_ML300", "100", 6, 0.0, "A", "h2", ML=300),
    # HOLZ test at three angles: every rod with |g| <= 6/a = 1.10 1/A (including rods with a
    # component along the beam) against the ZOLZ row inside the same disk (|h| <= 3), same slab (40
    # layers); the full 1 mrad grid with 101 rods took about 10 min per angle on the loaded machine
    SolverCase("holz_a100disk_N6_B", "100disk", 6, 0.1, "B", "holz", slab_layers=40),
    SolverCase("holz_a100_N3_B", "100", 3, 0.1, "B", "holz", slab_layers=40),
]


# ================================================================================================
# Doyle-Turner parameters as tabulated in the solver (read from its source at run time)
# ================================================================================================
def read_dt_from_asf(asf_path: Path, Z: int = 14) -> dict:
    """Row Z of the 'data ad' and 'data bd' blocks of asf.f90 (Doyle-Turner), with line numbers."""
    lines = asf_path.read_text().splitlines()

    def block(tag):
        i0 = next(i for i, s in enumerate(lines) if s.strip().startswith(f"data {tag}"))
        row = lines[i0 + Z]                       # the block's first data line is Z = 1
        vals = [float(v.replace("d0", "")) for v in re.findall(r"[-0-9.]+d0", row)]
        return vals, i0 + Z + 1                   # 1-based line number
    a, la = block("ad")
    b, lb = block("bd")
    return dict(a=a, b=b, line_a=la, line_b=lb, file=str(asf_path),
                sha256=hashlib.sha256(asf_path.read_bytes()).hexdigest())


def fe_dt(s2, dt) -> np.ndarray:
    """Doyle-Turner electron scattering factor (A) at s^2 = (sin theta / lambda)^2 (1/A^2)."""
    a, b = np.asarray(dt["a"]), np.asarray(dt["b"])
    s2 = np.asarray(s2, float)
    return np.sum(a[:, None] * np.exp(-b[:, None] * s2.ravel()[None, :]), axis=0).reshape(s2.shape)


def F_dt(f2, dt) -> np.ndarray:
    """Projected scattering factor in the engine's units (V A^3, f in cycles/A): h^2/(2 pi m0 e)
    f_e(s = f/2) (DERIVED_HERE; the engine's abTEM function has the same meaning, M2 section 0)."""
    return C_VA2 * fe_dt(np.asarray(f2, float) / 4.0, dt)


_FK = None


def F_kirkland(f2) -> np.ndarray:
    """The engine's production function: abTEM 1.0.10 Kirkland projected_scattering_factor('Si')."""
    global _FK
    if _FK is None:
        from abtem.parametrizations import KirklandParametrization
        _FK = KirklandParametrization().projected_scattering_factor("Si")
    return np.asarray(_FK(np.asarray(f2, dtype=np.float64)), dtype=np.float64)


def structure_factor(hkl) -> complex:
    return complex(np.sum(np.exp(2j * np.pi * (DIAMOND_BASIS @ np.asarray(hkl, float)))))


def V_hkl(hkl, F) -> complex:
    h = np.asarray(hkl, float)
    return structure_factor(h) * float(F(np.array([h @ h / A**2]))[0]) / A**3


# ================================================================================================
# Solver input files, run, parse
# ================================================================================================
def _deg(mrad):
    return float(mrad) * 1e-3 * 180.0 / np.pi


def solver_inputs(case: SolverCase, grid) -> tuple[str, str, dict]:
    beams, phi = beams_for(case.azimuth, case.N)
    gi, gf, dg = grid
    ml = case.ML if case.approach == "A" else 0
    L = ["1,1,1   ,NH,NK,NDOM", f"{len(beams)}   ,NB", "0   ,RDOM",
         ",".join(f"{h},{k}" for h, k in beams) + "   ,(IH(I),IK(I))",
         f"{E_KEV:.1f},{phi:.10f},{phi:.10f},0,{_deg(gi):.15g},{_deg(gf):.15g},{_deg(dg):.15g}"
         "   ,BE,AZI,AZF,DAZ,GI,GF,DG",
         f"{case.dz_A:.6g},{ml}   ,DZ,ML", "1   ,NELM",
         f"14,0.0,{case.sap:.6g}   ,Si Z,da1,sap (da1 = 0: unmodified table; sap = absorption ratio)",
         "0,0,0   ,BH,BK,BZ (static lattice)",
         f"1,{AS:.12f},{AS:.12f},90,{CC:.12f},0.5,0.5   ,NSG,AA,BB,GAM,CC,DX,DY", "2   ,NATM"]
    for n in (0, 1):
        u, v = LAYER_UV[n]
        L.append(f"1,1,{u},{v},{Z0 + n * Q:.12f}   ,IELM,ocr,X,Y,Z")
    bulk = "\n".join(L) + "\n"
    # surf.exe: the topmost bulk unit is shifted by (DX, DY) = (1/2, 1/2): layers 2 and 3 at
    # s = Z0 and Z0 + Q; surface atoms (shifted by DXS + DX, DYS + DY) sit at s = CC + z_s.
    if case.approach == "A":
        surf = ("0   ,NELMS\n1,1,0,0,1," f"{DTHICK_A}" ",0.0,0.0   ,NSGS,msa,msb,nsa,nsb,dthick,DXS,DYS\n"
                "0   ,NATM (ideal bulk truncation)\n1   ,WDOM\n")
        s_a = Z0 + Q
        n_top = 3
    else:
        M = case.slab_layers
        if M % 2:
            raise ValueError("slab_layers must be even (odd top layer)")
        S = ["1   ,NELMS", f"14,0.0,{case.sap:.6g}   ,Si Z,da1,sap", "0,0,0   ,BH,BK,BZ",
             f"1,1,0,0,1,{DTHICK_A},0.0,0.0   ,NSGS,msa,msb,nsa,nsb,dthick,DXS,DYS", f"{M}   ,NATM"]
        for m in range(M):
            n = 4 + m
            u, v = LAYER_UV[n % 4]
            S.append(f"1,1,{(u - 0.5) % 1.0},{(v - 0.5) % 1.0},{Z0 + m * Q:.12f}")
        S.append("1   ,WDOM")
        surf = "\n".join(S) + "\n"
        s_a = CC + Z0 + (M - 1) * Q
        n_top = 3 + M
    geo = dict(beams=beams, phi_deg=phi, s_top_layer_A=s_a, top_layer_n_mod4=n_top % 4,
               top_layer_backbond="[1,1,0] (odd layer)" if n_top % 2 else "[1,-1,0]",
               bulk_ML=ml, cc_A=CC, z0_A=Z0, dthick_A=DTHICK_A, grid_mrad=list(grid))
    return bulk, surf, geo


def parse_amp(path: Path, nb: int, nb0: int) -> dict:
    head = None
    rows = []
    for line in path.read_text().splitlines():
        if line.startswith("# S5"):
            p = line.split()
            head = dict(dz=float(p[-4]), ns=int(p[-3]), s_top=float(p[-2]), wn=float(p[-1]))
        elif line.strip():
            rows.append([float(v) for v in line.split()])
    d = np.array(rows)
    if d.shape[1] != 2 + 4 * nb:
        raise ValueError(f"amp.txt has {d.shape[1]} columns, expected {2 + 4 * nb}")
    F = d[:, 2::4] + 1j * d[:, 3::4]
    G = d[:, 4::4] + 1j * d[:, 5::4]
    return dict(head=head, theta=d[:, 0], az=d[:, 1], F=F, G=G, nb0=nb0)


def run_solver_case(case: SolverCase, build: Path, workdir: Path) -> dict:
    out = dict(case=dataclasses.asdict(case), runs=[])
    for gi, grid in enumerate(angle_grids()[case.grid]):
        wd = workdir / f"{case.name}_{gi}"
        wd.mkdir(parents=True, exist_ok=True)
        bulk, surf, geo = solver_inputs(case, grid)
        (wd / "bulk.txt").write_text(bulk)
        (wd / "surf.txt").write_text(surf)
        for f in wd.glob("amp.txt"):
            f.unlink()
        t0 = time.time()
        r1 = subprocess.run([str(build / "bulk.exe")], cwd=wd, capture_output=True, text=True)
        t1 = time.time()
        r2 = subprocess.run([str(build / "surf.exe")], cwd=wd, capture_output=True, text=True)
        t2 = time.time()
        if r1.returncode or r2.returncode:
            raise RuntimeError(f"{case.name}: solver failed: {r1.stderr} {r2.stderr}")
        beams = geo["beams"]
        nb0 = beams.index((0, 0))
        amp = parse_amp(wd / "amp.txt", len(beams), nb0)
        th, F, G, hd = amp["theta"], amp["F"], amp["G"], amp["head"]
        g0 = G[:, nb0].real
        Rtop = F[:, nb0]
        Ra = Rtop * np.exp(-2j * g0 * (hd["s_top"] - geo["s_top_layer_A"]))
        prop = (G.real > 1e-10)
        flux = np.where(prop, np.abs(F) ** 2 * g0[:, None] / np.where(prop, G.real, 1.0), 0.0)
        run = dict(grid_mrad=list(grid), geometry=geo, header=hd,
                   theta_rad=th.tolist(), R_top_re=Rtop.real.tolist(), R_top_im=Rtop.imag.tolist(),
                   R_layer_re=Ra.real.tolist(), R_layer_im=Ra.imag.tolist(), gamma0=g0.tolist(),
                   reflected_flux_all_rods=flux.sum(axis=1).tolist(),
                   gamma0_check=float(np.max(np.abs(g0 - hd["wn"] * np.sin(th)))),
                   bulk_s=t1 - t0, surf_s=t2 - t1,
                   inputs_sha256=dict(bulk=hashlib.sha256(bulk.encode()).hexdigest(),
                                      surf=hashlib.sha256(surf.encode()).hexdigest()),
                   workdir=str(wd))
        if case.grid == "onebeam":
            run["ode_1d"] = ode_1d_check(case, geo, hd, th)
        out["runs"].append(run)
        print(f"[solver] {case.name} grid {grid}: {len(th)} angles, bulk {t1 - t0:.1f} s, "
              f"surf {t2 - t1:.1f} s", flush=True)
    return out


# ================================================================================================
# Independent 1D check of the (0,0)-rod problem (DERIVED_HERE): same potential, adaptive ODE
# ================================================================================================
def U00_profile(s, case: SolverCase, dt, gamma_rel):
    """Laterally averaged reduced potential U_00(s) (A^-2) of the approach-B slab (layers n = 0 .. 3+M
    at s_n = Z0 + (n - 2) Q, one atom per cell of area AS^2), with the absorption ratio."""
    M = case.slab_layers
    s = np.asarray(s, float)
    a, b = np.asarray(dt["a"]), np.asarray(dt["b"])
    sn = Z0 + (np.arange(0, 4 + M) - 2) * Q
    U = np.zeros_like(s)
    for aj, bj in zip(a, b):
        for x in sn:
            U += aj * np.sqrt(4 * np.pi / bj) * np.exp(-4 * np.pi**2 * (s - x) ** 2 / bj)
    return gamma_rel * 4 * np.pi / AS**2 * U * (1.0 + 1j * case.sap)


def _rk4_R(U, h, n, G0):
    """Classical RK4 for psi'' = -(G0^2 + U(s)) psi, all angles at once; U sampled at s = k h/2."""
    y0 = np.ones_like(G0, dtype=complex)
    y1 = -1j * G0.astype(complex)
    g2 = G0**2
    for i in range(n):
        u0, um, u1 = U[2 * i], U[2 * i + 1], U[2 * i + 2]
        k1a, k1b = y1, -(g2 + u0) * y0
        k2a, k2b = y1 + 0.5 * h * k1b, -(g2 + um) * (y0 + 0.5 * h * k1a)
        k3a, k3b = y1 + 0.5 * h * k2b, -(g2 + um) * (y0 + 0.5 * h * k2a)
        k4a, k4b = y1 + h * k3b, -(g2 + u1) * (y0 + h * k3a)
        y0 = y0 + h / 6 * (k1a + 2 * k2a + 2 * k3a + k4a)
        y1 = y1 + h / 6 * (k1b + 2 * k2b + 2 * k3b + k4b)
    up = 0.5 * (y0 + y1 / (1j * G0))
    dn = 0.5 * (y0 - y1 / (1j * G0))
    return up / dn


def ode_1d_check(case: SolverCase, geo, hd, theta) -> dict:
    """psi'' = -(Gamma0^2 + U00(s)) psi on 0 <= s <= s_top with psi = exp(-i Gamma0 s) at s = 0 (only
    the downward wave below, as the solver's R_bulk = 0), in the exp(-i omega t) convention:
    R(s_top) = u/d with psi = d exp(-i G (s - s_top)) + u exp(+i G (s - s_top)) at s_top. Fixed-step
    RK4 on the CONTINUOUS potential (the solver uses piecewise-constant slices and eigenvectors),
    at two steps for a convergence estimate. DERIVED_HERE."""
    dt = DT_PARAMS
    gam = 1.0 + E_KEV / SOLVER_E_REST_KEV
    K = hd["wn"]
    st = hd["s_top"]
    G0 = K * np.sin(np.asarray(theta, float))
    out = {}
    for h_nom in (0.002, 0.001):
        n = int(np.ceil(st / h_nom))
        h = st / n
        U = U00_profile(np.arange(2 * n + 1) * (h / 2), case, dt, gam)
        R = _rk4_R(U, h, n, G0)
        out[f"{h_nom}"] = dict(h_A=h, R_top_re=R.real.tolist(), R_top_im=R.imag.tolist())
    return dict(runs=out, method="fixed-step RK4 on the continuous U00(s), all angles at once",
                gamma_rel=gam, K=K, U00_mean_over_bulk_period=None)


DT_PARAMS: dict = {}


def solver_run(args) -> int:
    global DT_PARAMS
    build, clone, workdir = Path(args.solver_build), Path(args.solver_clone), Path(args.workdir)
    DT_PARAMS = read_dt_from_asf(clone / "src" / "asf.f90")
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=clone, capture_output=True,
                            text=True).stdout.strip()
    fc = subprocess.run(["gfortran", "--version"], capture_output=True, text=True).stdout
    data = json.loads(SOLVER_JSON.read_text()) if SOLVER_JSON.exists() else dict(cases={})
    data.update(schema="S5/solver/1", solver="sim-trhepd-rheed", solver_commit=commit,
                solver_licence="GPL-3.0 (LICENSE SHA-256 " + hashlib.sha256(
                    (clone / "LICENSE").read_bytes()).hexdigest() + ")",
                patch_sha256=hashlib.sha256(Path(args.patch).read_bytes()).hexdigest(),
                compiler=fc.splitlines()[0] if fc else None, build_dir=str(build),
                exe_sha256={e: hashlib.sha256((build / e).read_bytes()).hexdigest()
                            for e in ("bulk.exe", "surf.exe")},
                dt_params=DT_PARAMS, label="REPRODUCED: solver output in this container")
    cases = [c for c in SOLVER_CASES if not args.only or c.name in args.only]
    with cf.ThreadPoolExecutor(max_workers=args.jobs) as ex:
        futs = {ex.submit(run_solver_case, c, build, workdir): c for c in cases}
        for fu in cf.as_completed(futs):
            c = futs[fu]
            res = fu.result()
            import fcntl
            with open(SOLVER_JSON.with_suffix(".lock"), "w") as lk:
                fcntl.flock(lk, fcntl.LOCK_EX)
                cur = json.loads(SOLVER_JSON.read_text()) if SOLVER_JSON.exists() else dict(cases={})
                meta = {k: v for k, v in data.items() if k != "cases"}
                cur.update(meta)
                cur["cases"][c.name] = res
                cur["updated_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                tmp = SOLVER_JSON.with_suffix(f".tmp{os.getpid()}")
                tmp.write_text(json.dumps(cur, indent=0, default=float))
                tmp.replace(SOLVER_JSON)
                fcntl.flock(lk, fcntl.LOCK_UN)
    return 0


# ================================================================================================
# Tolerances, DECLARED BEFORE ANY ENGINE-SOLVER COMPARISON (report section 5; 2026-09-23 22:45 UTC)
# ================================================================================================
# Per angle, like-for-like (Doyle-Turner in both codes, static lattice, r = 0.1, ZOLZ rods of the
# engine band in the solver): |R_eng - R_sol| <= TOL_REL |R_sol| + TOL_ABS + TOL_SPREAD_MULT * s_eng,
# with s_eng the engine's own read-out spread at that angle (max deviation of 250 A bins in the window
# from the window mean). TOL_REL: the solver's own rod-set sensitivity (N = 6 -> 8, 10: up to 1.1 %
# of |R|) plus the engine's band-limit effect on the (0,0,l) couplings (H2 section 5 Bethe estimate
# 2.8e-2 of V_g at [100]) -> 5 %; TOL_ABS: the rod sensitivity in absolute terms (2.7e-3) rounded up.
TOL_REL = 0.05
TOL_ABS = 0.005
TOL_SPREAD_MULT = 2.0
# Curve level ([100] (0,0,8) peak; both curves sampled at the SAME engine angles, peak from a parabola
# through the three highest points): peak angle, peak |R|^2 (relative), FWHM (relative), and the
# phase sweep across the peak arg R(theta_pk + w) - arg R(theta_pk - w), w = half the solver FWHM.
TOL_PEAK_ANGLE_MRAD = 0.03
TOL_PEAK_I_REL = 0.10
TOL_FWHM_REL = 0.10
TOL_SWEEP_RAD = 0.10


# ================================================================================================
# Engine side: flat Si(001) strips (after report H2, tools/hpc/supercell_sizing.py flat_strip), with
# an arbitrary angle and a choice of scattering factor
# ================================================================================================
AZ_UVW = {"100": (1, 0, 0), "110": (1, 1, 0)}
AZ_LABEL = {"100": "TEST_ONLY: stands in for PROJECT_INPUT item 8 (exact [100], B20 demo value)",
            "110": "TEST_ONLY: stands in for PROJECT_INPUT item 8 ([110], the M2 study azimuth)"}
THETA_LABEL = "TEST_ONLY: stands in for PROJECT_INPUT item 7 (rocking-curve angle, S5 validation)"
ABSORBER_V, BULK_ABSORBER_A, TOP_ABSORBER_A = 100.0, 15.0, 10.0   # NUMERICAL (M2, H2 practice)
GAP_A, EDGE_A = 2.0, 2.0                                          # sheet beam (M2, H2 practice)
MAX_PIXEL_A = 0.13                                                # H2 section 5
# H2 section 2.4 / 3 for r = 0.1 at [100]: phase within 1e-2 rad beyond 1500 A, amplitude within 3e-2
# beyond 2500 A after first contact; exit plane contaminated over the last 500 A; clean depth 55 A.
# Read-out window: 2500 A after contact to 750 A before the exit plane (H2's exclusion).
ENGINE_DEFAULT = dict(L_after_contact_A=4500.0, clean_A=55.0, y_periods=1, precision="complex64",
                      max_pixel_A=MAX_PIXEL_A, window_start_A=2500.0, exit_excl_A=750.0,
                      bin_A=250.0, radius_per_A=0.1, dz_div=1)
_A100 = sorted(set(ENGINE_COARSE) | set(ENGINE_FINE_100))
_A110 = sorted(set(ENGINE_COARSE) | set(ENGINE_EXTRA_110))
ENGINE_CASES = {
    # like-for-like METHOD test: the solver's Doyle-Turner scattering factors inside the engine
    "eng_a100_dt_r010": dict(azimuth="100", pot="dt", r=0.1, angles=_A100),
    "eng_a110_dt_r010": dict(azimuth="110", pot="dt", r=0.1, angles=_A110),
    # the engine as used in production (Kirkland, abTEM 1.0.10); angles reduced to the (0,0,8) peak
    # and the two other [100] maxima for CPU time (report section 6)
    "eng_a100_kk_r010": dict(azimuth="100", pot="kirkland", r=0.1,
                             angles=sorted(set(ENGINE_FINE_100) | {12.0, 21.0})),
}


def _dt_potential_class():
    from reflection_holo.forward.multislice import AtomicPotential

    class DoyleTurnerPotential(AtomicPotential):
        """TEST_ONLY: the engine's AtomicPotential with the scattering-factor function replaced by the
        Doyle-Turner 4-Gaussian fit as tabulated in the solver (values stored in the results file,
        read from asf.f90). Everything else (slicing, Fourier construction, absorption, MIP) is the
        engine's own code."""

        def __init__(self, cell, *, dt, physical_absorption, static_lattice_label):
            super().__init__(cell, parameterisation="kirkland", physical_absorption=physical_absorption,
                             frozen_phonons=None, static_lattice_label=static_lattice_label)
            self._dt = dict(a=list(dt["a"]), b=list(dt["b"]))
            self.name = "doyle_turner_TEST_ONLY"
            self._prov = dict(self._prov, parameterisation="Doyle-Turner 4-Gaussian electron "
                              "scattering factors as tabulated in sim-trhepd-rheed asf.f90 (TEST_ONLY; "
                              "S5 like-for-like test)", parameterisation_class="DoyleTurnerPotential "
                              "(tools/validation/rheed_solver_compare.py)", dt_params=self._dt,
                              function="h^2/(2 pi m0 e) * sum_j a_j exp(-b_j f^2/4), V A^3")

        def scattering_factor(self, Z, f2):
            if int(Z) != 14:
                raise ValueError("Doyle-Turner test potential: Si only")
            return F_dt(f2, self._dt)
    return DoyleTurnerPotential


def _working_reflections_kw():
    """The engine gained a required MultisliceParams.working_reflections_hkl (PROJECT_INPUT item 9)
    at commit 2a3a999 (a band assertion; the propagation is unchanged, report section 6.1); pass the
    specular (0,0,8) when the field exists so that the tool runs on either engine version."""
    from reflection_holo.forward.multislice import MultisliceParams
    names = {f.name for f in dataclasses.fields(MultisliceParams)}
    return dict(working_reflections_hkl=((0, 0, 8),)) if "working_reflections_hkl" in names else {}


def engine_flat_strip(*, azimuth, theta_ext, pot, r, dt, L_after_contact_A, clean_A, y_periods,
                      precision, max_pixel_A, dz_div=1, threads=4, **_):
    from reflection_holo.forward.cell import build_reflection_cell
    from reflection_holo.forward.multislice import (AtomicPotential, MultisliceParams,
                                                    NumericalAbsorber, PhysicalAbsorption,
                                                    SheetBeam, fft_friendly)
    from reflection_holo.structure import Staircase, build_si001_terraces
    th = float(theta_ext)
    P = A if azimuth == "100" else A / np.sqrt(2.0)
    dz = (A / 4.0 if azimuth == "100" else P / 4.0) / int(dz_div)
    depth = BULK_ABSORBER_A + clean_A
    sub = int(np.ceil(depth / Q)) + 2
    ent = 10 * dz * int(dz_div)
    periods = int(np.ceil((GAP_A / np.tan(th) + L_after_contact_A - ent) / P))
    one = build_si001_terraces(
        azimuth_uvw=AZ_UVW[azimuth], azimuth_label=AZ_LABEL[azimuth],
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
    st = dataclasses.replace(one, positions_A=pos, species=np.tile(one.species, periods),
                             cell_A=cell_A, layer_index=np.tile(one.layer_index, periods),
                             terrace_index=np.tile(one.terrace_index, periods), metadata=md)
    Lz = ent + periods * P
    H = Lz * np.tan(th) - GAP_A - 1.0
    vac = float(np.ceil(H + Lz * np.tan(th) + 1.0))
    cell = build_reflection_cell(st, vacuum_above_A=vac, depth_below_A=depth,
                                 bulk_absorber_A=BULK_ABSORBER_A, top_absorber_A=TOP_ABSORBER_A,
                                 entrance_vacuum_z_A=ent)
    absn = PhysicalAbsorption(model="proportional", ratio=float(r),
                              label=("TEST_ONLY: stands in for PROJECT_INPUT item 21" if r > 0 else
                                     "ASSUMPTION: no physical absorption (B30)"))
    if pot == "dt":
        potential = _dt_potential_class()(cell, dt=dt, physical_absorption=absn,
                                          static_lattice_label="ASSUMPTION: static lattice")
    else:
        potential = AtomicPotential(cell, parameterisation="kirkland", physical_absorption=absn,
                                    frozen_phonons=None,
                                    static_lattice_label="ASSUMPTION: static lattice")
    xs = float(cell.metadata["layout"]["highest_surface_x_A"])
    beam = SheetBeam(height_A=float(H), edge_A=EDGE_A, x_bottom_A=xs + GAP_A, theta_in_ext_rad=th,
                     theta_label=THETA_LABEL)
    nx = fft_friendly(int(np.ceil(cell.extent_x_A / max_pixel_A)))
    ny = fft_friendly(int(np.ceil(cell.extent_y_A / max_pixel_A)))
    params = MultisliceParams(energy_keV=E_KEV, nx=nx, ny=ny, dz_A=dz, propagator="exact",
                              band_limit="2/3", backend="numpy", precision=precision,
                              threads=threads,
                              absorber=NumericalAbsorber(strength_V=ABSORBER_V, profile="sin2"),
                              theta_out_ext_rad=th, buildup_depth_A=20.0,
                              **_working_reflections_kw())
    info = dict(azimuth=azimuth, pot=pot, r=r, theta_ext_rad=th, L_after_contact_A=L_after_contact_A,
                clean_A=clean_A, y_periods=y_periods, precision=precision, nx=nx, ny=ny, dz_A=dz,
                dx_A=cell.extent_x_A / nx, dy_A=cell.extent_y_A / ny, L_z_A=Lz, H_A=float(H),
                vacuum_above_A=vac, x_surface_A=xs, z_contact_A=GAP_A / np.tan(th),
                n_slices=int(round(Lz / dz)), n_atoms=int(len(cell.Z)),
                mip_V=float(potential.mean_inner_potential_V()))
    return cell, potential, beam, params, info


def engine_readout(col, x, lam, info, *, radius_per_A, window_start_A, exit_excl_A, bin_A, **_):
    """Specular reflection coefficient at the top-layer plane from the y-averaged exit column
    (DERIVED_HERE): f_y = 0 component (y average), vacuum part only (sin^2 taper from 2 A above the
    top layer, as H2), band-pass |f_x - f_c| <= radius about f_c = sin(theta)/lambda, demodulation by
    exp(-2 pi i f_c x) (x from the box bottom, the phase reference of the launched sheet beam). A
    plane wave reflected at the plane x_s gives e = r exp(-4 pi i f_c x_s) P_L with
    P_L = exp(i L_z (k_z - k)) the exact vacuum propagation factor of both the incident and the
    reflected component, hence r = <e>_window exp(+4 pi i f_c x_s) / P_L (the formula of
    analysis.flat_reflection_coefficient). The ray found at height x left the surface at
    z_s = L_z - (x - x_s)/tan(theta)."""
    k = 2 * np.pi / lam
    th, xs, Lz, zc = (info["theta_ext_rad"], info["x_surface_A"], info["L_z_A"], info["z_contact_A"])
    fc = np.sin(th) / lam
    nx = len(col)
    dxg = x[1] - x[0]
    w = np.sin(0.5 * np.pi * np.clip((x - (xs + 2.0)) / 3.0, 0.0, 1.0)) ** 2
    fx = np.fft.fftfreq(nx, dxg)
    e = np.fft.ifft(np.fft.fft(col * w) * (np.abs(fx - fc) <= radius_per_A)) * np.exp(-2j * np.pi * fc * x)
    d = Lz - (x - xs) / np.tan(th) - zc
    L = Lz - zc
    ok = x >= xs + 5.0
    win = ok & (d >= window_start_A) & (d < L - exit_excl_A)
    if win.sum() < 3:
        raise ValueError("read-out window empty")
    e_mean = complex(e[win].mean())
    q = 2 * np.pi * fc
    PL = np.exp(1j * Lz * (-q**2 / (k + np.sqrt(k**2 - q**2))))
    r_top = e_mean * np.exp(4j * np.pi * fc * xs) / PL
    bins = []
    b = 0.0
    while b < L:
        m = ok & (d >= b) & (d < b + bin_A)
        if np.any(m):
            v = complex(e[m].mean()) * np.exp(4j * np.pi * fc * xs) / PL
            bins.append(dict(start_A=b, re=v.real, im=v.imag))
        b += bin_A
    inwin = [complex(q_["re"], q_["im"]) for q_ in bins
             if q_["start_A"] >= window_start_A - 1e-9 and q_["start_A"] + bin_A <= L - exit_excl_A + 1e-9]
    spread = max(abs(v - r_top) for v in inwin) if inwin else None
    return dict(r_top_re=r_top.real, r_top_im=r_top.imag, e_mean_re=e_mean.real,
                e_mean_im=e_mean.imag, P_L_phase_rad=float(np.angle(PL)),
                window_A=[window_start_A, L - exit_excl_A], window_rows=int(win.sum()),
                bins=bins, max_bin_deviation=spread, f_c_per_A=fc, wavelength_A=lam)


def _merge_engine_record(tag, spec, variant, key, rec):
    """Re-read, merge and rewrite the results file under an exclusive lock (several engine cases
    may run concurrently)."""
    import fcntl
    with open(ENGINE_JSON.with_suffix(".lock"), "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        data = json.loads(ENGINE_JSON.read_text()) if ENGINE_JSON.exists() else dict(cases={})
        case = data["cases"].setdefault(tag, dict(spec=spec, variant=variant, angles={}))
        case["angles"][key] = rec
        data["updated_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        data["label"] = ("MEASURED_HERE with the UNVALIDATED engine; TEST_ONLY absorption, azimuth, "
                         "angle stand-ins; static lattice")
        tmp = ENGINE_JSON.with_suffix(f".tmp{os.getpid()}")
        tmp.write_text(json.dumps(data, indent=0, default=float))
        tmp.replace(ENGINE_JSON)
        fcntl.flock(lk, fcntl.LOCK_UN)


def engine_run(args) -> int:
    from reflection_holo.forward.multislice import run_realisation
    sol = json.loads(SOLVER_JSON.read_text())
    dt = sol["dt_params"]
    spec = dict(ENGINE_CASES[args.engine_run])
    variant = dict(ENGINE_DEFAULT)
    for kv in args.set or []:
        key, val = kv.split("=")
        variant[key] = type(ENGINE_DEFAULT[key])(val)
    tag = args.engine_run + ("" if not args.set else "__" + "_".join(args.set))
    angles = args.angles_mrad or spec["angles"]
    data = json.loads(ENGINE_JSON.read_text()) if ENGINE_JSON.exists() else dict(cases={})
    git = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True,
                         text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "reflection_holo"], cwd=REPO,
                                capture_output=True, text=True).stdout.strip())
    done = data["cases"].get(tag, {}).get("angles", {})
    for th_mrad in angles:
        key = f"{th_mrad:.4f}"
        if key in done:
            print(f"[engine] {tag} {key} mrad: stored, skipped", flush=True)
            continue
        t0 = time.time()
        cell, pot, beam, params, info = engine_flat_strip(
            azimuth=spec["azimuth"], theta_ext=th_mrad * 1e-3, pot=spec["pot"], r=spec["r"], dt=dt,
            threads=args.threads, **variant)
        t1 = time.time()
        ew = run_realisation(cell, potential=pot, beam=beam, params=params, realisation=0, seed=None)
        t2 = time.time()
        col = ew.psi.astype(np.complex128).mean(axis=1)
        x = ew.x0_A + np.arange(len(col)) * ew.dx_A
        lam = ew.metadata["beam"]["wavelength_A"]
        ro = engine_readout(col, x, lam, info, **variant)
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
        rec = dict(info=info, readout=ro, build_s=t1 - t0, run_s=t2 - t1, wavelength_A=lam,
                   x0_A=float(ew.x0_A), dx_A=float(ew.dx_A),
                   col_re=[float(f"{v:.7g}") for v in col.real],
                   col_im=[float(f"{v:.7g}") for v in col.imag],
                   peak_rss_MB=rss, loadavg=list(os.getloadavg()),
                   engine_commit=git, engine_dirty=dirty,
                   validation_status=ew.metadata["validation_status"])
        _merge_engine_record(tag, spec, variant, key, rec)
        r = complex(ro["r_top_re"], ro["r_top_im"])
        print(f"[engine] {tag} {th_mrad:.3f} mrad: grid {info['nx']}x{info['ny']}, "
              f"{info['n_slices']} slices, {info['n_atoms']} atoms, run {t2 - t1:.0f} s, RSS {rss:.0f} MB,"
              f" |r|^2 {abs(r)**2:.5f} arg {np.angle(r):+.4f}, bin spread {ro['max_bin_deviation']:.2e}",
              flush=True)
    return 0


# ================================================================================================
# Report mode: every number of the S5 report
# ================================================================================================
CHECKS: list = []


def check(name, ok, detail):
    CHECKS.append((name, bool(ok), detail))
    print(f"  CHECK {'PASS' if ok else 'FAIL'} {name}: {detail}")


def hdr(t):
    print("\n" + "=" * 100 + "\n" + t + "\n" + "=" * 100)


def _cplx(d, pre):
    return np.array(d[pre + "_re"]) + 1j * np.array(d[pre + "_im"])


def solver_curve(sol, name, plane="R_layer"):
    th, R = [], []
    for run in sol["cases"][name]["runs"]:
        th += list(np.array(run["theta_rad"]) * 1e3)
        R += list(_cplx(run, plane))
    o = np.argsort(th)
    return np.array(th)[o], np.array(R)[o]


def engine_curve(eng, tag):
    c = eng["cases"].get(tag)
    if not c:
        return np.array([]), np.array([]), np.array([]), []
    keys = sorted(c["angles"], key=float)
    th = np.array([float(k) for k in keys])
    R = np.array([complex(c["angles"][k]["readout"]["r_top_re"], c["angles"][k]["readout"]["r_top_im"])
                  for k in keys])
    sp = np.array([c["angles"][k]["readout"]["max_bin_deviation"] for k in keys])
    return th, R, sp, [c["angles"][k] for k in keys]


def at_angles(th_src, R_src, th_q, tol=1e-6):
    out = []
    for t in th_q:
        i = int(np.argmin(np.abs(th_src - t)))
        out.append(R_src[i] if abs(th_src[i] - t) < tol else np.nan)
    return np.array(out)


def peak_parabola(th, I):
    i = int(np.nanargmax(I))
    if i == 0 or i == len(I) - 1:
        return th[i], I[i], i
    y0, y1, y2 = I[i - 1], I[i], I[i + 1]
    h = th[i + 1] - th[i]
    den = y0 - 2 * y1 + y2
    dx = 0.5 * (y0 - y2) / den * h
    return th[i] + dx, y1 - 0.25 * (y0 - y2) * dx / h, i


def fwhm(th, I, i):
    half = 0.5 * I[i]
    lo = i
    while lo > 0 and I[lo] > half:
        lo -= 1
    hi = i
    while hi < len(I) - 1 and I[hi] > half:
        hi += 1
    if I[lo] > half or I[hi] > half:
        return np.nan, np.nan, np.nan
    tl = th[lo] + (half - I[lo]) / (I[lo + 1] - I[lo]) * (th[lo + 1] - th[lo])
    tr = th[hi - 1] + (half - I[hi - 1]) / (I[hi] - I[hi - 1]) * (th[hi] - th[hi - 1])
    return tr - tl, tl, tr


def interp_c(th, R, t):
    return np.interp(t, th, R.real) + 1j * np.interp(t, th, R.imag)


def report() -> int:
    t_start = time.time()
    sol = json.loads(SOLVER_JSON.read_text())
    eng = json.loads(ENGINE_JSON.read_text()) if ENGINE_JSON.exists() else dict(cases={})
    git = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True,
                         text=True).stdout.strip()
    print(f"S5 report mode; repository HEAD {git}; solver results updated {sol.get('updated_utc')}; "
          f"engine results updated {eng.get('updated_utc')}")
    dt = sol["dt_params"]

    hdr("1. Solver provenance record (REPRODUCED in this container)")
    print(f"  solver {sol['solver']} commit {sol['solver_commit']}; {sol['solver_licence']}")
    print(f"  patch SHA-256 {sol['patch_sha256']}; compiler: {sol['compiler']}")
    for e, h in sol["exe_sha256"].items():
        print(f"  {e} SHA-256 {h}")
    print(f"  Doyle-Turner Si read from {Path(dt['file']).name} (SHA-256 {dt['sha256']}): a = {dt['a']} A "
          f"(line {dt['line_a']}), b = {dt['b']} A^2 (line {dt['line_b']})")

    hdr("2. Constants and potentials of the two codes (DERIVED_HERE)")
    from reflection_holo.forward.multislice.physics import beam_constants
    from reflection_holo.geometry.specular import specular_condition_for
    bc = beam_constants(E_KEV)
    K_sol = sol["cases"]["onebeam_r010"]["runs"][0]["header"]["wn"]
    print(f"  engine k = {bc['k_rad_per_A']:.6f} rad/A (CODATA 2018, m c^2 = {M_E_C2_EV / 1e3:.5f} keV); "
          f"solver K = {K_sol:.6f} rad/A (m c^2 = {SOLVER_E_REST_KEV} keV, 2me/hbar^2 = {SOLVER_EK}); "
          f"relative difference {K_sol / bc['k_rad_per_A'] - 1:+.2e}")
    g_e = 1 + E_KEV / (M_E_C2_EV / 1e3)
    g_s = 1 + E_KEV / SOLVER_E_REST_KEV
    print(f"  gamma: engine {g_e:.8f}, solver {g_s:.8f} (relative {g_s / g_e - 1:+.2e}); "
          f"2 k sigma / (4 pi gamma) = {2 * bc['k_rad_per_A'] * bc['sigma_rad_per_VA'] * C_VA2 / (4 * np.pi * g_e):.8f}"
          " (1 if U_engine = 2 k sigma V equals U_solver = gamma 4 pi f / Omega for V = C f / Omega)")
    print(f"  C = h^2/(2 pi m0 e) = {C_VA2:.5f} V A^2")
    fd0 = float(fe_dt(np.array([0.0]), dt)[0])
    fk0 = float(F_kirkland(np.array([0.0]))[0]) / C_VA2
    mip_d, mip_k = 8 / A**3 * C_VA2 * fd0, 8 / A**3 * C_VA2 * fk0
    print(f"  f_e(0): Doyle-Turner {fd0:.5f} A, Kirkland (abTEM) {fk0:.5f} A; mean inner potential "
          f"(8 f(0) C / a^3): DT {mip_d:.4f} V, Kirkland {mip_k:.4f} V (difference {mip_d - mip_k:+.4f} V)")
    th_d = specular_condition_for((0, 0, 8), (0, 0, 1), E_keV=E_KEV, V0_V=mip_d, a_A=A).theta_ext
    th_k = specular_condition_for((0, 0, 8), (0, 0, 1), E_keV=E_KEV, V0_V=mip_k, a_A=A).theta_ext
    print(f"  (0,0,8) external Bragg angle from refraction alone: DT {th_d * 1e3:.4f} mrad, Kirkland "
          f"{th_k * 1e3:.4f} mrad (difference {(th_d - th_k) * 1e3:+.4f} mrad)")
    print("  Fourier coefficients V_hkl (V) of bulk Si, DT / Kirkland / ratio:")
    for hkl in [(0, 0, 4), (0, 0, 8), (0, 0, 12), (0, 0, 16), (0, 2, 2), (0, 4, 0), (0, 4, 4),
                (0, 2, 6), (0, 4, 8), (1, 1, 1), (1, 1, 3), (1, 1, 5), (1, 1, 7), (2, 2, 4)]:
        vd = V_hkl(hkl, lambda f2: F_dt(f2, dt)).real
        vk = V_hkl(hkl, F_kirkland).real
        g = np.sqrt(np.dot(hkl, hkl)) / A
        print(f"    {str(hkl):12s} |g| {g:.4f} 1/A  DT {vd:+.4f}  Kirkland {vk:+.4f}  ratio {vd / vk:.4f}")
    return report_part2(sol, eng, dt, bc, mip_d, mip_k, th_d, th_k, t_start)


def report_part2(sol, eng, dt, bc, mip_d, mip_k, th_d, th_k, t_start) -> int:
    hdr("3. One-beam convention test: solver (0,0) rod against an independent RK4 integration")
    for name in ("onebeam_r010", "onebeam_r000"):
        run = sol["cases"][name]["runs"][0]
        Rf = _cplx(run, "R_top")
        o = run["ode_1d"]["runs"]
        R1, R2 = _cplx(o["0.002"], "R_top"), _cplx(o["0.001"], "R_top")
        print(f"  {name}: {len(Rf)} angles 12-22 mrad, slab {sol['cases'][name]['case']['slab_layers']} "
              f"layers, s_top {run['header']['s_top']:.5f} A, dz {run['header']['dz']:.6f} A")
        print(f"    max |R_solver - R_RK4| = {np.max(np.abs(Rf - R2)):.2e};  max |R_solver - conj(R_RK4)|"
              f" = {np.max(np.abs(Rf - np.conj(R2))):.3f};  RK4 h 0.002 vs 0.001: {np.max(np.abs(R1 - R2)):.1e};"
              f"  max |R| {np.max(np.abs(Rf)):.4f}")
        check(f"{name}: solver equals RK4 (not its conjugate)",
              np.max(np.abs(Rf - R2)) < 1e-3 < np.max(np.abs(Rf - np.conj(R2))),
              f"{np.max(np.abs(Rf - R2)):.1e} < 1e-3 < {np.max(np.abs(Rf - np.conj(R2))):.2f}")
        th = np.array(run["theta_rad"]) * 1e3
        i = int(np.argmax(np.abs(Rf)))
        print(f"    largest |R|^2 {abs(Rf[i])**2:.4f} at {th[i]:.1f} mrad (0.5 mrad grid), arg R(s_top) "
              f"{np.angle(Rf[i]):+.4f} (solver) / {np.angle(R2[i]):+.4f} (RK4)")

    hdr("4. Solver numerical checks (max |Delta R| over the angles; relative where |R| > 0.05)")

    def cmp(a, b, label):
        ta, Ra = solver_curve(sol, a)
        tb, Rb = solver_curve(sol, b)
        Rb = at_angles(tb, Rb, ta)
        d = np.abs(Ra - Rb)
        m = np.abs(Rb) > 0.05
        rel = np.max(d[m] / np.abs(Rb[m])) if m.any() else np.nan
        print(f"  {label:58s} {np.max(d):.2e}  rel {rel:.2e}  ({len(ta)} angles)")
        return np.max(d), rel
    cmp("chk_a100_N6_A", "chk_a100_N6_B", "[100] N=6: approach A (bulk.exe) vs B (slab)")
    cmp("chk_a100_N4_A", "chk_a100_N4_B", "[100] N=4: A vs B")
    cmp("chk_a100_N6_B_slab180", "chk_a100_N6_B", "[100] N=6 B: slab 180 vs 90 layers")
    cmp("chk_a100_N6_A_dz005", "chk_a100_N6_A", "[100] N=6 A: dz 0.005 vs 0.01 A")
    cmp("chk_a100_N6_A_dz02", "chk_a100_N6_A", "[100] N=6 A: dz 0.02 vs 0.01 A")
    cmp("chk_a100m_N6_A", "chk_a100_N6_A", "[100]: phi = -45 deg (rods (h,h)) vs +45 deg")
    cmp("chk_a100_N4_B", "chk_a100_N6_B", "[100] rods: N=4 vs N=6 (B)")
    cmp("chk_a100_N8_B", "chk_a100_N6_B", "[100] rods: N=8 vs N=6 (B)")
    cmp("chk_a100_N10_B", "chk_a100_N6_B", "[100] rods: N=10 vs N=6 (B)")
    cmp("chk_a110_N9_A", "chk_a110_N9_B", "[110] N=9: A vs B")
    cmp("chk_a110_N9_A_dz005", "chk_a110_N9_A", "[110] N=9 A: dz 0.005 vs 0.01 A")
    cmp("chk_a110_N12_B", "chk_a110_N9_B", "[110] rods: N=12 vs N=9 (B)")
    cmp("eng_a100_N8_r010_B", "eng_a100_N6_r010", "[100] engine angles: N=8 (B) vs N=6 (A)")
    cmp("eng_a100_N10_r010_B", "eng_a100_N6_r010", "[100] engine angles: N=10 (B) vs N=6 (A)")
    cmp("eng_a110_N12_r010_B", "eng_a110_N9_r010", "[110] engine angles: N=12 (B) vs N=9 (A)")
    if "holz_a100disk_N6_B" in sol["cases"]:
        nd = len(sol["cases"]["holz_a100disk_N6_B"]["runs"][0]["geometry"]["beams"])
        cmp("holz_a100disk_N6_B", "holz_a100_N3_B",
            f"[100] HOLZ: all {nd} rods |g|<=6/a vs the row |h|<=3 (3 angles)")
        ta, Ra = solver_curve(sol, "holz_a100disk_N6_B")
        tb, Rb = solver_curve(sol, "holz_a100_N3_B")
        for t, x, y in zip(ta, Ra, Rb):
            print(f"      {t:6.2f} mrad: disk |R|^2 {abs(x)**2:.5f} arg {np.angle(x):+.4f}; row |R|^2 "
                  f"{abs(y)**2:.5f} arg {np.angle(y):+.4f}; |R_disk|/|R_row| - 1 = {abs(x) / abs(y) - 1:+.4f},"
                  f" d arg {wrapd(np.angle(x) - np.angle(y)):+.4f}")
    fl = []
    for nm in ("fine_a100_N6_r000_ML150", "fine_a100_N6_r000_ML300", "fine_a110_N9_r000_ML150",
               "fine_a110_N9_r000_ML300", "fine_a100_N6_r010", "fine_a110_N9_r010"):
        fl.append(max(max(r["reflected_flux_all_rods"]) for r in sol["cases"][nm]["runs"]))
    print(f"  total reflected flux of all propagating rods, largest over the fine grids: {max(fl):.6f}")
    check("reflected flux <= 1 everywhere (r = 0 and 0.1)", max(fl) <= 1 + 1e-6, f"{max(fl):.6f}")
    return report_part3(sol, eng, dt, bc, mip_d, mip_k, th_d, th_k, t_start)


def report_part3(sol, eng, dt, bc, mip_d, mip_k, th_d, th_k, t_start) -> int:
    hdr("5. Solver rocking curves (DT, static lattice; R at the top-layer nuclei, exp(+ikr - iwt))")
    t1, R1 = solver_curve(sol, "fine_a100_N6_r010")
    t2, R2 = solver_curve(sol, "fine_a110_N9_r010")
    print("  r = sap = 0.1, 0.02 mrad grid (printed every 0.2 mrad); [100]: 13 rods (h,-h), |h| <= 6;"
          " [110]: 19 rods (0,k), |k| <= 9")
    print("  theta(mrad)  [100] |R|^2   arg R    [110] |R|^2   arg R")
    for i in range(0, len(t1), 10):
        print(f"  {t1[i]:8.2f}    {abs(R1[i])**2:9.5f}  {np.angle(R1[i]):+7.3f}    {abs(R2[i])**2:9.5f}  "
              f"{np.angle(R2[i]):+7.3f}")
    for lab, t, R in (("[100]", t1, R1), ("[110]", t2, R2)):
        I = np.abs(R) ** 2
        pk = [i for i in range(1, len(I) - 1) if I[i] > I[i - 1] and I[i] >= I[i + 1] and I[i] > 0.005]
        print(f"  {lab} r = 0.1 local maxima with |R|^2 > 0.005 (grid points): " + "; ".join(
            f"{t[i]:.2f} mrad |R|^2 {I[i]:.4f} arg {np.angle(R[i]):+.3f}" for i in pk))
    I1 = np.abs(R1) ** 2
    m = (t1 > 15.0) & (t1 < 17.5)
    tp, Ip, ip = peak_parabola(t1[m], I1[m])
    w, tl, tr = fwhm(t1[m], I1[m], ip)
    Rl, Rr = interp_c(t1, R1, tp - w / 2), interp_c(t1, R1, tp + w / 2)
    sweep = float(np.angle(Rr / Rl))
    print(f"  [100] (0,0,8) peak (fine grid, parabola): {tp:.4f} mrad, |R|^2 {Ip:.5f}, FWHM {w:.4f} mrad "
          f"({tl:.3f} to {tr:.3f}), arg R at peak {np.angle(interp_c(t1, R1, tp)):+.4f}, phase sweep "
          f"arg R(pk + w/2) - arg R(pk - w/2) = {sweep:+.4f} rad (wrapped; the unwrapped sweep across "
          f"the peak is this plus 0 or 2 pi)")
    msk = (t1 >= 15.5 - 1e-9) & (t1 <= 16.9 + 1e-9)
    if "fine_a100_N0_r010" in sol["cases"]:
        t0_, R0_ = solver_curve(sol, "fine_a100_N0_r010")
        m0 = (t0_ > 15.0) & (t0_ < 17.5)
        tp0, Ip0, ip0 = peak_parabola(t0_[m0], np.abs(R0_[m0]) ** 2)
        w0, _, _ = fwhm(t0_[m0], np.abs(R0_[m0]) ** 2, ip0)
        print(f"  [100] (0,0) rod alone (1 beam, same potential): peak {tp0:.4f} mrad, |R|^2 {Ip0:.5f}, "
              f"FWHM {w0:.4f} mrad, arg R at peak {np.angle(interp_c(t0_, R0_, tp0)):+.4f}; the 13-rod "
              f"curve differs from it by up to {np.max(np.abs(R0_ - R1)):.4f} in R")
    un = np.unwrap(np.angle(R1[msk]))
    print(f"  [100] unwrapped arg R from {t1[msk][0]:.2f} to {t1[msk][-1]:.2f} mrad: {un[0]:+.3f} -> "
          f"{un[-1]:+.3f} rad (total {un[-1] - un[0]:+.3f} rad); monotonic increase on the 0.02 mrad "
          f"grid: {bool(np.all(np.diff(un) > 0))}")
    print(f"  [100] many-beam peak minus the refraction-only (0,0,8) angle with the DT MIP: "
          f"{tp - th_d * 1e3:+.4f} mrad")
    SOLVER_PEAK = dict(theta=tp, I=Ip, fwhm=w, sweep=sweep)

    print("\n  r = 0 (no absorption): FINITE slabs, bulk.exe ML = 150 or 300 units (407 or 815 A) on "
          "vacuum; printed every 0.2 mrad")
    c = {}
    for az, N in (("a100", 6), ("a110", 9)):
        for ml in (150, 300):
            c[(az, ml)] = solver_curve(sol, f"fine_{az}_N{N}_r000_ML{ml}")
    fl = {az: np.concatenate([np.array(r["reflected_flux_all_rods"]) for r in
                              sol["cases"][f"fine_{az}_N{6 if az == 'a100' else 9}_r000_ML150"]["runs"]])
          for az in ("a100", "a110")}
    print("  theta   [100] ML150 |R|^2 arg   ML300 |R|^2 arg  flux150 |  [110] ML150 |R|^2 arg   ML300 |R|^2 arg  flux150")
    for i in range(0, len(t1), 10):
        row = f"  {t1[i]:6.2f}"
        for az in ("a100", "a110"):
            a, b = c[(az, 150)][1][i], c[(az, 300)][1][i]
            row += (f"   {abs(a)**2:7.4f} {np.angle(a):+6.3f}   {abs(b)**2:7.4f} {np.angle(b):+6.3f}  "
                    f"{fl[az][i]:6.4f} |")
        print(row)
    for az in ("a100", "a110"):
        a, b = c[(az, 150)][1], c[(az, 300)][1]
        d = np.abs(a - b)
        tot = fl[az] > 0.9999
        print(f"  {az}: angles where ML150 and ML300 differ by more than 1e-3 in R: {int((d > 1e-3).sum())}"
              f" of {len(d)}; total reflection (flux > 0.9999) at {int(tot.sum())} angles, max |Delta R| "
              f"there {d[tot].max() if tot.any() else float('nan'):.1e}; largest |R|^2 {np.max(np.abs(a)**2):.4f}")
    return report_part4(sol, eng, dt, bc, mip_d, mip_k, th_d, th_k, SOLVER_PEAK, t_start)


def wrapd(x):
    return (np.asarray(x) + np.pi) % (2 * np.pi) - np.pi


def report_part4(sol, eng, dt, bc, mip_d, mip_k, th_d, th_k, SP, t_start) -> int:
    hdr("6. Engine (UNVALIDATED, MEASURED_HERE) against the solver at the same angles")
    print(f"  tolerance per angle: |R_eng - R_sol| <= {TOL_REL} |R_sol| + {TOL_ABS} + {TOL_SPREAD_MULT} "
          f"s_eng (declared before the comparison); curve level: peak {TOL_PEAK_ANGLE_MRAD} mrad, peak "
          f"|R|^2 {TOL_PEAK_I_REL:.0%}, FWHM {TOL_FWHM_REL:.0%}, sweep {TOL_SWEEP_RAD} rad")
    mx_e = max((abs(complex(a["readout"]["r_top_re"], a["readout"]["r_top_im"]))
                for c in eng["cases"].values() for a in c["angles"].values()), default=float("nan"))
    mx_s = max(np.max(np.abs(solver_curve(sol, n)[1])) for n in ("fine_a100_N6_r010", "fine_a110_N9_r010"))
    print(f"  largest |R| (r = 0.1): engine, all runs {mx_e:.4f}; solver fine curves {mx_s:.4f}")
    solmap = {"eng_a100_dt_r010": "eng_a100_N6_r010", "eng_a110_dt_r010": "eng_a110_N9_r010",
              "eng_a100_kk_r010": "eng_a100_N6_r010"}
    results = {}
    for tag in ENGINE_CASES:
        te, Re, sp, recs = engine_curve(eng, tag)
        if not len(te):
            print(f"  {tag}: no engine results")
            continue
        ts, Rs = solver_curve(sol, solmap[tag])
        Rs = at_angles(ts, Rs, te)
        like = ENGINE_CASES[tag]["pot"] == "dt"
        print(f"\n  {tag} ({'LIKE-FOR-LIKE: Doyle-Turner in both' if like else 'PRODUCTION Kirkland engine vs DT solver: model difference, no pass/fail'}); "
              f"{len(te)} angles; solver case {solmap[tag]}")
        print("   theta   sol|R|^2  sol arg   eng|R|^2  eng arg   |dR|     tol    ok  d arg    d|R|/|R|  s_eng    run_s  grid")
        npass = 0
        for i, t in enumerate(te):
            d = abs(Re[i] - Rs[i])
            tol = TOL_REL * abs(Rs[i]) + TOL_ABS + TOL_SPREAD_MULT * sp[i]
            ok = d <= tol
            npass += ok
            inf = recs[i]["info"]
            print(f"  {t:6.2f}  {abs(Rs[i])**2:8.5f} {np.angle(Rs[i]):+7.3f}  {abs(Re[i])**2:8.5f} "
                  f"{np.angle(Re[i]):+7.3f}  {d:.4f}  {tol:.4f}  {'yes' if ok else 'NO ':3s} "
                  f"{wrapd(np.angle(Re[i]) - np.angle(Rs[i])):+7.3f}  {abs(Re[i]) / abs(Rs[i]) - 1:+7.3f}  "
                  f"{sp[i]:.4f}  {recs[i]['run_s']:5.0f}  {inf['nx']}x{inf['ny']}x{inf['n_slices']}")
        print(f"   angles within tolerance: {npass} of {len(te)}")
        rel = np.abs(Re) / np.abs(Rs) - 1
        dph = wrapd(np.angle(Re) - np.angle(Rs))
        pk = (te >= 15.6 - 1e-9) & (te <= 16.8 + 1e-9)
        print(f"   engine |R| below the solver's at {int((rel < 0).sum())} of {len(te)} angles; "
              f"d|R|/|R| range {rel.min():+.3f} to {rel.max():+.3f}")
        if pk.sum() >= 3:
            print(f"   within 15.6-16.8 mrad ({int(pk.sum())} angles): d|R|/|R| from {rel[pk].min():+.3f} to "
                  f"{rel[pk].max():+.3f}, d arg from {dph[pk].min():+.3f} to {dph[pk].max():+.3f} rad")
        dc = np.abs(Re - np.conj(Rs))
        print(f"   conjugation test: median |R_eng - R_sol| {np.median(np.abs(Re - Rs)):.4f}, median "
              f"|R_eng - conj(R_sol)| {np.median(dc):.4f}")
        big = np.abs(Rs) >= 0.1
        if big.sum() >= 3:
            G0 = bc["k_rad_per_A"] * np.sin(te[big] * 1e-3)
            dphi = wrapd(np.angle(Re[big]) - np.angle(Rs[big]))
            Am = np.vstack([np.ones_like(G0), 2 * G0]).T
            cfit, dx = np.linalg.lstsq(Am, dphi, rcond=None)[0]
            print(f"   reference-plane fit over {int(big.sum())} angles with |R_sol| >= 0.1: d arg = c + 2 Gamma0 dx,"
                  f" c = {cfit:+.4f} rad, dx = {dx:+.5f} A; rms d arg {np.sqrt(np.mean(dphi**2)):.4f} rad")
            g12, g22 = (bc["k_rad_per_A"] * np.sin(t * 1e-3) for t in (12.0, 22.0))
            print(f"   scale: a reference plane misplaced by 0.1 A shifts arg R by 2 Gamma0 x 0.1 A = "
                  f"{2 * g12 * 0.1:.3f} rad at 12 mrad and {2 * g22 * 0.1:.3f} rad at 22 mrad")
        if tag == "eng_a110_dt_r010" and "eng_a110perp_N9_r010" in sol["cases"]:
            tp_, Rp = solver_curve(sol, "eng_a110perp_N9_r010")
            Rp = at_angles(tp_, Rp, te)
            print(f"   orientation check: median |R_eng - R_sol| with the top-layer back-bonds PARALLEL to "
                  f"the beam (as built) {np.median(np.abs(Re - Rs)):.4f}, PERPENDICULAR (solver phi = 90 "
                  f"deg) {np.median(np.abs(Re - Rp)):.4f}; the two solver orientations differ by median "
                  f"{np.median(np.abs(Rs - Rp)):.4f} (max {np.max(np.abs(Rs - Rp)):.4f})")
        results[tag] = dict(te=te, Re=Re, Rs=Rs, sp=sp, npass=npass, n=len(te))
        if like:
            check(f"{tag}: every angle within the declared tolerance", npass == len(te),
                  f"{npass}/{len(te)}")
    return report_part5(sol, eng, dt, bc, mip_d, mip_k, th_d, th_k, SP, results, t_start)


def curve_metrics(te, R, lo=15.0, hi=17.5):
    m = (te > lo) & (te < hi)
    if m.sum() < 5:
        return None
    t, Rm = te[m], R[m]
    I = np.abs(Rm) ** 2
    tp, Ip, ip = peak_parabola(t, I)
    w, tl, tr = fwhm(t, I, ip)
    return dict(theta=tp, I=Ip, fwhm=w, t=t, R=Rm)


def report_part5(sol, eng, dt, bc, mip_d, mip_k, th_d, th_k, SP, results, t_start) -> int:
    hdr("7. Curve-level comparison at the [100] (0,0,8) peak (engine angles 15.6-16.8 mrad at 0.1 mrad)")
    for tag in ("eng_a100_dt_r010", "eng_a100_kk_r010"):
        if tag not in results:
            continue
        r = results[tag]
        me, ms = curve_metrics(r["te"], r["Re"]), curve_metrics(r["te"], r["Rs"])
        if me is None:
            print(f"  {tag}: fewer than 5 engine angles in 15-17.5 mrad; skipped")
            continue
        w = SP["fwhm"]
        sw_e = float(np.angle(interp_c(me["t"], me["R"], me["theta"] + w / 2) /
                              interp_c(me["t"], me["R"], me["theta"] - w / 2)))
        sw_s = float(np.angle(interp_c(ms["t"], ms["R"], ms["theta"] + w / 2) /
                              interp_c(ms["t"], ms["R"], ms["theta"] - w / 2)))
        like = ENGINE_CASES[tag]["pot"] == "dt"
        print(f"  {tag}:")
        print(f"    peak angle: engine {me['theta']:.4f}, solver (same angles) {ms['theta']:.4f}, solver "
              f"(fine grid) {SP['theta']:.4f} mrad; engine - solver(same) {me['theta'] - ms['theta']:+.4f} mrad")
        print(f"    peak |R|^2: engine {me['I']:.5f}, solver (same) {ms['I']:.5f}, solver (fine) {SP['I']:.5f};"
              f" engine/solver(same) - 1 = {me['I'] / ms['I'] - 1:+.4f} (in |R|: "
              f"{np.sqrt(me['I'] / ms['I']) - 1:+.4f})")
        print(f"    FWHM: engine {me['fwhm']:.4f}, solver (same angles) {ms['fwhm']:.4f}, solver (fine) "
              f"{SP['fwhm']:.4f} mrad; engine/solver(same) - 1 = {me['fwhm'] / ms['fwhm'] - 1:+.4f}")
        print(f"    phase sweep over +-w/2 (w = solver fine FWHM {w:.4f}): engine {sw_e:+.4f}, solver (same "
              f"angles) {sw_s:+.4f}, solver (fine) {SP['sweep']:+.4f} rad; difference {wrapd(sw_e - sw_s):+.4f}")
        if like:
            check("[100] DT peak angle", abs(me["theta"] - ms["theta"]) <= TOL_PEAK_ANGLE_MRAD,
                  f"{me['theta'] - ms['theta']:+.4f} mrad")
            check("[100] DT peak |R|^2", abs(me["I"] / ms["I"] - 1) <= TOL_PEAK_I_REL,
                  f"{me['I'] / ms['I'] - 1:+.4f}")
            check("[100] DT FWHM", abs(me["fwhm"] / ms["fwhm"] - 1) <= TOL_FWHM_REL,
                  f"{me['fwhm'] / ms['fwhm'] - 1:+.4f}")
            check("[100] DT phase sweep", abs(wrapd(sw_e - sw_s)) <= TOL_SWEEP_RAD,
                  f"{wrapd(sw_e - sw_s):+.4f} rad")
    if "eng_a100_dt_r010" in results and "eng_a100_kk_r010" in results:
        a, b = results["eng_a100_dt_r010"], results["eng_a100_kk_r010"]
        common = np.intersect1d(np.round(a["te"], 4), np.round(b["te"], 4))
        ia = [int(np.argmin(np.abs(a["te"] - t))) for t in common]
        ib = [int(np.argmin(np.abs(b["te"] - t))) for t in common]
        d = b["Re"][ib] - a["Re"][ia]
        print(f"  engine Kirkland minus engine DT at {len(common)} common angles: max |Delta R| "
              f"{np.max(np.abs(d)):.4f}; per angle d|R|^2 / d arg:")
        for t, x, y in zip(common, a["Re"][ia], b["Re"][ib]):
            print(f"    {t:6.2f}  {abs(y)**2 - abs(x)**2:+.5f}  {wrapd(np.angle(y) - np.angle(x)):+.4f}")
        print(f"  refraction-only expectation of the peak shift Kirkland - DT: {(th_k - th_d) * 1e3:+.4f} mrad"
              f" (MIP {mip_k:.4f} vs {mip_d:.4f} V)")
    return report_part6(sol, eng, t_start)


def report_part6(sol, eng, t_start) -> int:
    hdr("8. Engine-internal sensitivity at one angle, and resources")
    base = eng["cases"].get("eng_a100_dt_r010", {}).get("angles", {})
    for tag, c in eng["cases"].items():
        if "__" not in tag:
            continue
        for key, rec in c["angles"].items():
            ro = rec["readout"]
            r = complex(ro["r_top_re"], ro["r_top_im"])
            b = base.get(key)
            rb = complex(b["readout"]["r_top_re"], b["readout"]["r_top_im"]) if b else np.nan
            inf = rec["info"]
            print(f"  {tag} at {key} mrad: |R|^2 {abs(r)**2:.5f} arg {np.angle(r):+.4f}; default run "
                  f"|R|^2 {abs(rb)**2:.5f} arg {np.angle(rb):+.4f}; |Delta R| {abs(r - rb):.4f}; |R|^2 "
                  f"ratio - 1 {abs(r)**2 / abs(rb)**2 - 1:+.4f}, d arg {wrapd(np.angle(r) - np.angle(rb)):+.4f}; "
                  f"spread {ro['max_bin_deviation']:.4f}; grid {inf['nx']}x{inf['ny']}x{inf['n_slices']}, dx "
                  f"{inf['dx_A']:.4f} A, run {rec['run_s']:.0f} s, RSS {rec['peak_rss_MB']:.0f} MB")
            if key == "16.2000":
                for sname in ("eng_a100_N6_r010", "eng_a100_N8_r010_B", "eng_a100_N10_r010_B"):
                    ts_, Rs_ = solver_curve(sol, sname)
                    x = at_angles(ts_, Rs_, [16.2])[0]
                    print(f"      vs solver {sname} (|R|^2 {abs(x)**2:.5f} arg {np.angle(x):+.4f}): |R|^2 "
                          f"ratio - 1 {abs(r)**2 / abs(x)**2 - 1:+.4f}, |R| ratio - 1 {abs(r) / abs(x) - 1:+.4f},"
                          f" d arg {wrapd(np.angle(r) - np.angle(x)):+.4f}")
    for tag, c in eng["cases"].items():
        recs = list(c["angles"].values())
        if not recs:
            continue
        rs = np.array([r["run_s"] for r in recs])
        rss = max(r["peak_rss_MB"] for r in recs)
        la = np.array([r["loadavg"][0] for r in recs])
        print(f"  resources {tag}: {len(recs)} angles, run {rs.min():.0f}-{rs.max():.0f} s (median "
              f"{np.median(rs):.0f}), peak RSS {rss:.0f} MB, 1-min load average {la.min():.1f}-{la.max():.1f}"
              f", engine commit {recs[0]['engine_commit'][:7]} dirty {recs[0]['engine_dirty']}")
    print("\n  read-out choices re-evaluated on the stored exit columns (max over the angles of |Delta R| "
          "against the stored default; relative where |R| >= 0.1):")
    variants = [("default (self-check)", {}), ("band-pass radius 0.05 1/A", dict(radius_per_A=0.05)),
                ("band-pass radius 0.2 1/A", dict(radius_per_A=0.2)),
                ("exit exclusion 1250 A", dict(exit_excl_A=1250.0)),
                ("window start 2000 A", dict(window_start_A=2000.0)),
                ("window start 3000 A", dict(window_start_A=3000.0))]
    for tag, c in eng["cases"].items():
        if "__" in tag:
            continue
        for vname, over in variants:
            dmax, rmax = 0.0, 0.0
            for key, rec in c["angles"].items():
                if "col_re" not in rec:
                    continue
                col = np.array(rec["col_re"]) + 1j * np.array(rec["col_im"])
                x = rec["x0_A"] + np.arange(len(col)) * rec["dx_A"]
                v = dict(c["variant"])
                v.update(over)
                ro = engine_readout(col, x, rec["wavelength_A"], rec["info"], **v)
                r = complex(ro["r_top_re"], ro["r_top_im"])
                r0 = complex(rec["readout"]["r_top_re"], rec["readout"]["r_top_im"])
                dmax = max(dmax, abs(r - r0))
                if abs(r0) >= 0.1:
                    rmax = max(rmax, abs(r - r0) / abs(r0))
            print(f"    {tag:18s} {vname:28s} max |dR| {dmax:.2e}  rel {rmax:.2e}")
            if not over:
                check(f"{tag}: stored read-out reproduced from the stored column", dmax < 1e-5,
                      f"{dmax:.1e} (column stored with 7 significant digits)")

    hdr("9. Cross-check of report H2's stored flat-strip plateaus (Kirkland engine, 16.1347 mrad)")
    h2 = json.loads((REPO / "tools/hpc/supercell_sizing_measurements.json").read_text())
    from reflection_holo.forward.multislice.physics import beam_constants
    lam = beam_constants(E_KEV)["wavelength_A"]
    k = 2 * np.pi / lam
    for run, scase in (("bu_100_r010", "h2_a100_N6_r010"), ("bu_110_r010", "h2_a110_N9_r010"),
                       ("bu_100_r000", "h2_a100_N6_r000_ML150"), ("bu_100_r000", "h2_a100_N6_r000_ML300")):
        if run not in h2["runs"] or scase not in sol["cases"]:
            continue
        i = h2["runs"][run]["info"]
        b = h2["runs"][run]["buildup"]
        e = b["R_plateau_abs"] * np.exp(1j * b["R_plateau_arg"])
        fc = np.sin(i["theta_ext_rad"]) / lam
        q = 2 * np.pi * fc
        PL = np.exp(1j * i["L_z_A"] * (-q**2 / (k + np.sqrt(k**2 - q**2))))
        r = e * np.exp(4j * np.pi * fc * i["x_surface_A"]) / PL
        ts, Rs = solver_curve(sol, scase)
        print(f"  H2 {run} (plateau {b['plateau_A'][0]:.0f}-{b['plateau_A'][1]:.0f} A, stored |e| {abs(e):.4f} "
              f"arg e {np.angle(e):+.4f}) -> R at the top layer: |R|^2 {abs(r)**2:.5f} arg {np.angle(r):+.4f};"
              f"  solver {scase}: |R|^2 {abs(Rs[0])**2:.5f} arg {np.angle(Rs[0]):+.4f};  |Delta R| "
              f"{abs(r - Rs[0]):.4f}, d arg {wrapd(np.angle(r) - np.angle(Rs[0])):+.4f}")
    tot = sum(r["bulk_s"] + r["surf_s"] for c in sol["cases"].values() for r in c["runs"])
    print(f"  solver: {len(sol['cases'])} cases, total bulk.exe + surf.exe time {tot:.0f} s (single core)")
    print(f"\n  report mode ran in {time.time() - t_start:.0f} s")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--solver-run", action="store_true")
    ap.add_argument("--solver-build")
    ap.add_argument("--solver-clone")
    ap.add_argument("--patch")
    ap.add_argument("--workdir")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--engine-run")
    ap.add_argument("--angles-mrad", type=float, nargs="*")
    ap.add_argument("--set", nargs="*", help="variant overrides, e.g. max_pixel_A=0.10")
    ap.add_argument("--threads", type=int, default=4)
    args = ap.parse_args(argv)
    if args.solver_run:
        return solver_run(args)
    if args.engine_run:
        return engine_run(args)
    rc = report()
    bad = [c for c in CHECKS if not c[1]]
    print(f"\n{len(CHECKS) - len(bad)}/{len(CHECKS)} checks pass")
    return 1 if (bad or rc) else 0


if __name__ == "__main__":
    sys.exit(main())
