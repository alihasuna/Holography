#!/usr/bin/env python3
"""E8: independent recomputation for the review of S5 (docs/agent_reports/S5_independent_rheed_solver.md):
sim-trhepd-rheed (upstream d98d6252, S5's output patch) against the multislice engine on flat Si(001).

Written by review agent E8 (2026-09-24) WITHOUT reading the S5 tool's implementation
(tools/validation/rheed_solver_compare.py) of the quantities recomputed here. Inputs are only:
  * the raw solver output files amp.txt and the Fortran inputs bulk.txt / surf.txt in S5's scratch
    run directories (RUNS below), and the sources of sim-trhepd-rheed and trhepd-opt there;
  * the stored engine exit columns in tools/validation/rheed_engine_results.json (col_re, col_im,
    x0_A, dx_A and the geometry record 'info');
  * the repository engine itself (sections 10 and 11 run it with E8's own driver and read-out).
The S5 tool is only executed as a black box in section 12 (its report mode) to compare outputs.
Every number quoted in docs/agent_reports/E8_solver_review.md is printed here; the saved run is
tools/review/e8_recompute_output.txt.

Conventions (docs/physics_conventions.md): exp(+i k.r - i omega t); s or x = outward normal; theta =
external glancing angle; R = (upward wave)/(downward wave) at a stated plane.

Run:  venv/bin/python tools/review/e8_recompute.py [--sections 1,2,...] [--threads N]
Sections: 1 provenance and constants; 2 convention (own transfer matrices); 3 solver R at the
top-layer nuclei, flux, numerical routes, r = 0 slabs, two-fold symmetry; 4 own engine read-out of
S5's stored columns and S5's tolerance; 5 plane fit and tolerance power; 6 curve level; 7, 7b engine
and tool version history (git); 8 H2 plateaus; 9 incident sheet-beam amplitude; 10, 10b own engine
runs (regression, pixel study, along-beam-averaged potential, more angles, [110]); 11 rung-2
continuum at coarse pixels; 12 S5 tool re-run as a black box; 13 P49 Eq. (36) algebra.
The engine sections (10, 10b, 11) run the engine from `git archive` copies in the scratch directory
(SCR/e8/engine_HEAD, commit d3de34a, with tests/forward and tools/physics_checks) in subprocesses and
cache their raw results in ENGINE_CACHE (about 25 min of 2-thread CPU on the shared machine); a
re-run only re-reads the cache; delete the cache files to recompute. Memory below 0.5 GB per run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
_JOBFLAG = [f for f in ("--engine-job", "--rung2-job") if f in sys.argv]
if _JOBFLAG:                            # job subprocess: the archived engine commit comes first
    sys.path.insert(0, json.loads(sys.argv[sys.argv.index(_JOBFLAG[0]) + 1])["engine_root"])
else:
    sys.path.insert(0, str(REPO))
SCR = Path("/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad")
SOLVER_DIR = SCR / "rheed_solver"
RUNS = SOLVER_DIR / "runs"
UPSTREAM = SOLVER_DIR / "sim-trhepd-rheed"
FORK = SOLVER_DIR / "trhepd-opt"
E8_WORK = SCR / "e8"
ENGINE_CACHE = E8_WORK / "engine_cache"
SOLVER_JSON = REPO / "tools/validation/rheed_solver_results.json"
ENGINE_JSON = REPO / "tools/validation/rheed_engine_results.json"

# ------------------------------------------------------------------------------------------------
# constants (own formulas; CODATA 2018 via the repository constants for the engine side)
# ------------------------------------------------------------------------------------------------
from reflection_holo.constants import HC_EV_M, M_E_C2_EV  # noqa: E402

T_EV = 200.0e3                                  # PROJECT_INPUT item 1
HC_EV_A = HC_EV_M * 1e10
LAM = HC_EV_A / np.sqrt(T_EV * (T_EV + 2 * M_E_C2_EV))     # relativistic vacuum wavelength (A)
K_ENG = 2 * np.pi / LAM                                    # rad/A
GAMMA_ENG = 1 + T_EV / M_E_C2_EV
# solver constants as printed in scpot.f90 (c2m, ek) -- SECTION_READ, re-typed here
C2M_SOL, EK_SOL = 511.001, 0.262466
K_SOL = np.sqrt(1e3 * 200.0 * EK_SOL * (1 + 0.5 * 200.0 / C2M_SOL))
GAMMA_SOL = 1 + 200.0 / C2M_SOL
A_SI = 5.4309                                              # ASSUMPTION B2 (both codes)

CHECKS: list[tuple[str, bool, str]] = []


def check(name, ok, detail):
    CHECKS.append((name, bool(ok), detail))
    print(f"  CHECK {'PASS' if ok else 'FAIL'} {name}: {detail}")


def hr(title):
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)


def sha256(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def wrap(p):
    return (np.asarray(p) + np.pi) % (2 * np.pi) - np.pi


# ------------------------------------------------------------------------------------------------
# solver file readers (own parsers of the Fortran inputs and of S5's amp.txt; formats from
# bulkio.f90 / surfio.f90 read statements and the patch's write statements)
# ------------------------------------------------------------------------------------------------
def _nums(line):
    head = line.split("   ,")[0] if "   ," in line else line
    return [float(v) for v in head.replace(",", " ").split()]


def read_bulk_txt(path):
    L = [ln.rstrip("\n") for ln in Path(path).read_text().splitlines()]
    i = 0
    nh, nk, ndom = (int(v) for v in _nums(L[i])); i += 1
    nb = int(_nums(L[i])[0]); i += 1
    i += 1                                             # RDOM
    beams = []
    while len(beams) < nb:
        v = [int(x) for x in _nums(L[i])]
        beams += [(v[j], v[j + 1]) for j in range(0, len(v), 2)]
        i += 1
    be, azi, azf, daz, gi, gf, dg = _nums(L[i]); i += 1
    dz, ml = _nums(L[i]); i += 1
    nelm = int(_nums(L[i])[0]); i += 1
    elems = []
    for _ in range(nelm):
        z, da1, sap = _nums(L[i]); i += 1
        bh, bk, bz = _nums(L[i]); i += 1
        elems.append(dict(Z=int(z), da1=da1, sap=sap, B=(bh, bk, bz)))
    nsg, aa, bb, gam, cc, dx, dy = _nums(L[i]); i += 1
    natm = int(_nums(L[i])[0]); i += 1
    atoms = [tuple(_nums(L[i + j])[:5]) for j in range(natm)]
    return dict(beams=beams, be=be, azi=azi, dz=dz, ml=int(ml), elems=elems, aa=aa, bb=bb, gam=gam,
                cc=cc, dxb=dx, dyb=dy, atoms=atoms, gi_deg=gi, gf_deg=gf, dg_deg=dg)


def read_surf_txt(path):
    L = [ln.rstrip("\n") for ln in Path(path).read_text().splitlines()]
    i = 0
    nel = int(_nums(L[i])[0]); i += 1
    elems = []
    for _ in range(nel):
        z, da1, sap = _nums(L[i]); i += 1
        bh, bk, bz = _nums(L[i]); i += 1
        elems.append(dict(Z=int(z), da1=da1, sap=sap, B=(bh, bk, bz)))
    nsgs, msa, msb, nsa, nsb, dthick, dxs, dys = _nums(L[i]); i += 1
    natm = int(_nums(L[i])[0]); i += 1
    atoms = [tuple(_nums(L[i + j])[:5]) for j in range(natm)]
    return dict(elems=elems, dthick=dthick, dxs=dxs, dys=dys, atoms=atoms)


def read_amp(path, nb):
    lines = Path(path).read_text().splitlines()
    hdr = [ln for ln in lines if ln.startswith("# S5")][0].split()
    dz, ns, stop, wn = float(hdr[-4]), int(hdr[-3]), float(hdr[-2]), float(hdr[-1])
    rows = [np.array([float(v) for v in ln.split()]) for ln in lines if ln.strip()
            and not ln.startswith("#")]
    ga = np.array([r[0] for r in rows])
    az = np.array([r[1] for r in rows])
    f = np.array([[r[2 + 4 * j] + 1j * r[3 + 4 * j] for j in range(nb)] for r in rows])
    g = np.array([[r[4 + 4 * j] + 1j * r[5 + 4 * j] for j in range(nb)] for r in rows])
    return dict(dz=dz, ns=ns, s_top=stop, wn=wn, theta=ga, az=az, f=f, gamma=g)


def solver_run(dirname):
    """Everything needed from one solver run directory: specular R at s_top and at the top-layer
    nuclei (own geometry: s of the highest atom in the slice region), the rods and the flux."""
    d = RUNS / dirname
    b = read_bulk_txt(d / "bulk.txt")
    s = read_surf_txt(d / "surf.txt")
    nb = len(b["beams"])
    a = read_amp(d / "amp.txt", nb)
    j0 = b["beams"].index((0, 0))
    # slice-region coordinate s (surfio.f90: surface atoms at z + CC, topmost bulk unit at z,
    # unit below at z - CC); the top-layer nuclei are the highest atom
    if s["atoms"]:
        s_a = max(at[4] for at in s["atoms"]) + b["cc"]
    else:
        s_a = max(at[4] for at in b["atoms"])
    G0 = a["gamma"][:, j0].real
    R_top = a["f"][:, j0]
    R_a = R_top * np.exp(-2j * G0 * (a["s_top"] - s_a))
    # reflected flux fraction of every propagating rod: |f_i0|^2 Gamma_0 / Re Gamma_i (DERIVED_HERE:
    # the transfer-matrix state is (Gamma_i psi_i -/+ i psi_i'), so f_i0 = Gamma_i A_i/(Gamma_0 B_0))
    prop = a["gamma"].real > 1e-10
    flux = np.where(prop, np.abs(a["f"]) ** 2 * G0[:, None] / np.where(prop, a["gamma"].real, 1.0),
                    0.0).sum(axis=1)
    return dict(dir=dirname, bulk=b, surf=s, amp=a, j0=j0, s_a=s_a, G0=G0, R_top=R_top, R=R_a,
                theta=a["theta"], flux=flux, nb=nb)


def solver_case(prefix):
    """Concatenate the numbered run directories prefix_0, prefix_1, ... (sorted by angle)."""
    dirs = sorted(p.name for p in RUNS.glob(prefix + "_[0-9]*")
                  if re.fullmatch(re.escape(prefix) + r"_\d+", p.name))
    runs = [solver_run(n) for n in dirs]
    th = np.concatenate([r["theta"] for r in runs])
    R = np.concatenate([r["R"] for r in runs])
    fl = np.concatenate([r["flux"] for r in runs])
    o = np.argsort(th)
    return dict(theta=th[o], R=R[o], flux=fl[o], runs=runs)


# ================================================================================================
# 1. provenance: patch, sources, executables, constants, scattering factors
# ================================================================================================
def section1():
    hr("E8-1. Provenance of the solver build and of the patch (REPRODUCED file checks)")
    up = sorted(p for p in (UPSTREAM / "src").iterdir() if p.is_file())
    orig = SOLVER_DIR / "build_E/src_orig"
    pat = SOLVER_DIR / "build_E/src"
    head = subprocess.run(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"], capture_output=True,
                          text=True).stdout.strip()
    dirty = subprocess.run(["git", "-C", str(UPSTREAM), "status", "--porcelain"],
                           capture_output=True, text=True).stdout.strip()
    print(f"  upstream clone HEAD {head}; working tree clean: {dirty == ''}")
    same = [p.name for p in up if (orig / p.name).exists() and sha256(p) == sha256(orig / p.name)]
    print(f"  build_E/src_orig: {len(same)} of {len(up)} upstream src files byte-identical")
    changed = [p.name for p in up if (pat / p.name).exists() and sha256(p) != sha256(pat / p.name)]
    print(f"  build_E/src files differing from upstream: {changed}")
    diff = subprocess.run(["diff", "-r", str(orig), str(pat)], capture_output=True, text=True).stdout
    minus = [ln[2:].strip() for ln in diff.splitlines() if ln.startswith("< ")]
    plus = [ln[2:].strip() for ln in diff.splitlines() if ln.startswith("> ")]
    print(f"  removed lines ({len(minus)}):")
    for ln in minus:
        print(f"     - {ln}")
    print(f"  added lines ({len(plus)}):")
    for ln in plus:
        print(f"     + {ln[:150]}")
    only_ep = all("ep='P'" in ln for ln in minus) and len(minus) == 3
    adds_ok = (sum("ep='E'" in ln for ln in plus) == 3
               and all(("ep='E'" in ln) or ln.startswith("open (8") or ln.startswith("write (8")
                       for ln in plus))
    check("patch = particle switch + output only", only_ep and adds_ok,
          f"{len(minus)} removed lines all ep='P'; added lines are 3 ep='E', 1 open(8), "
          f"{sum(ln.startswith('write (8') for ln in plus)} write(8)")
    # which of the three switched files is compiled into bulk.exe / surf.exe (Makefile BULK/SURF)
    mk = (UPSTREAM / "src/Makefile").read_text()
    blk = re.search(r"^BULK = (.*)$", mk, re.M).group(1).split()
    srf = re.search(r"^SURF = (.*)$", mk, re.M).group(1).split()
    print(f"  Makefile BULK = {blk}; SURF = {srf}; U0.f90 in either: "
          f"{'U0.f90' in blk + srf} (U0 is the separate potcalc program)")
    # what the switch does: bulkm.f90 sets inegpos from ep; surf reads inegpos from the binary
    bm = (UPSTREAM / "src/bulkm.f90").read_text()
    print(f"  bulkm.f90: {'inegpos=1' in bm and 'if (ep ==' in bm and 'inegpos=0' in bm} "
          f"(inegpos=1; if (ep == 'E') inegpos=0)")
    so = (UPSTREAM / "src/surfio.f90").read_text()
    print(f"  surfio.f90 reads inegpos from the bulk binary: "
          f"{'read (1) inegpos,nh,nk,idiag' in so}; surfm.f90 uses ep only for the file name "
          f"bulkE.b: {'bname = ' in (UPSTREAM / 'src/surfm.f90').read_text()}")
    sp = (UPSTREAM / "src/scpot.f90").read_text()
    print(f"  scpot.f90 negates the real potential only for positrons after the last call: "
          f"{'iclr == -1 .and. negpos > 0' in sp}")
    exe = json.loads(SOLVER_JSON.read_text())["exe_sha256"]
    for n in ("bulk.exe", "surf.exe"):
        h = sha256(pat / n)
        print(f"  {n} SHA-256 {h[:16]}... equals the JSON record: {h == exe[n]}")
    print(f"  patch file SHA-256 {sha256(SOLVER_DIR / 's5_patch.diff')[:16]}...")

    hr("E8-1b. Relativistic constants of the two codes (own arithmetic)")
    ek_codata = 2 * 9.1093837015e-31 * 1.602176634e-19 / (1.054571817e-34) ** 2 * 1e-20
    print(f"  2 m e / hbar^2: solver {EK_SOL} A^-2 eV^-1, CODATA 2018 {ek_codata:.6f} "
          f"(relative {EK_SOL / ek_codata - 1:+.2e})")
    print(f"  K: solver {K_SOL:.6f} rad/A, engine {K_ENG:.6f} rad/A, relative {K_SOL / K_ENG - 1:+.3e}")
    print(f"  gamma: solver {GAMMA_SOL:.8f}, engine {GAMMA_ENG:.8f}, relative "
          f"{GAMMA_SOL / GAMMA_ENG - 1:+.3e}")
    # (0,0,8) refraction: the angle scale error from K alone
    print(f"  consequence: a relative K error e shifts every glancing angle by ~ -e/2 x (Delta/theta^2) "
          f"relative; with e = {K_SOL / K_ENG - 1:+.2e} the (0,0,8) peak moves by "
          f"{abs(K_SOL / K_ENG - 1) * 16.16:.1e} mrad or less (negligible against 0.03 mrad)")

    hr("E8-1c. Doyle-Turner Si in asf.f90 (SECTION_READ of the code; own parse)")
    txt = (UPSTREAM / "src/asf.f90").read_text().splitlines()
    ad = txt[228].strip()
    bd = txt[328].strip()
    print(f"  asf.f90:229  {ad}")
    print(f"  asf.f90:329  {bd}")
    print(f"  asf.f90:3-4  {txt[2].strip()} | {txt[3].strip()}")
    a = [float(v.replace("d0", "")) for v in ad.rstrip(", &").split(",")]
    b = [float(v.replace("d0", "")) for v in bd.rstrip(", &").split(",")]
    C = HC_EV_A**2 / (2 * np.pi * M_E_C2_EV)       # h^2/(2 pi m0 e) in V A^2 (own: (hc)^2/(2 pi m c^2))
    f0 = sum(a)
    mip = 8 * C * f0 / A_SI**3
    print(f"  f_e(0) = {f0:.5f} A; C = h^2/(2 pi m0 e) = {C:.5f} V A^2; DT mean inner potential "
          f"8 C f(0)/a^3 = {mip:.4f} V")
    return dict(a=a, b=b, C=C, mip=mip)


# ================================================================================================
# 2. convention: own transfer-matrix solution of the one-beam problem against the solver's f(0,nb0)
# ================================================================================================
def u00_of_s(s, bulk, surf, dt, sap):
    """Laterally averaged potential U_00(s) in A^-2 of the solver's slice region, built HERE from the
    physics (U = 2 gamma m e V / hbar^2 = gamma 4 pi f_e / Omega for the (0,0) component; the z
    profile of f_e(q) = sum_j a_j exp(-b_j q^2/4) is sum_j a_j sqrt(4 pi/b_j) exp(-4 pi^2 z^2/b_j)).
    Atoms: surface atoms at s = z + CC, the topmost bulk unit at s = z, the unit below at s = z - CC
    (surfio.f90 scpot calls); nothing below s = 0 or above s_top is part of the slice region."""
    omega = bulk["aa"] * bulk["bb"] * np.sin(np.radians(bulk["gam"]))
    pos = [z + bulk["cc"] for (_, _, _, _, z) in surf["atoms"]]
    pos += [z for (_, _, _, _, z) in bulk["atoms"]]
    pos += [z - bulk["cc"] for (_, _, _, _, z) in bulk["atoms"]]
    pos = np.asarray(pos)
    a = np.asarray(dt["a"])
    b = np.asarray(dt["b"])
    amp = a * np.sqrt(4 * np.pi / b) * GAMMA_SOL * 4 * np.pi / omega
    U = np.zeros_like(s)
    for p in pos:
        d2 = (s - p) ** 2
        U += (amp[None, :] * np.exp(-4 * np.pi**2 * d2[:, None] / b[None, :])).sum(axis=1)
    return U * (1 + 1j * sap)


def tm_reflect(G0, U_mid, h):
    """Own transfer matrices: psi'' = -(G0^2 + U) psi, piecewise-constant U on steps h, started at
    s = 0 with a pure DOWNWARD vacuum wave (psi = 1, psi' = -i G0: R = 0 below the region), and
    decomposed at the top in the vacuum basis: up a = (psi + psi'/(i G0))/2, down b = (psi -
    psi'/(i G0))/2, R = a/b (exp(-i omega t): exp(+i G0 s) travels towards the vacuum)."""
    G0 = np.asarray(G0, float)
    psi = np.ones_like(G0, dtype=complex)
    dpsi = -1j * G0.astype(complex)
    for u in U_mid:
        k = np.sqrt(G0**2 + u + 0j)
        c, sn = np.cos(k * h), np.sin(k * h)
        psi, dpsi = c * psi + sn / k * dpsi, -k * sn * psi + c * dpsi
    a = 0.5 * (psi + dpsi / (1j * G0))
    b = 0.5 * (psi - dpsi / (1j * G0))
    return a / b


def section2(dt):
    hr("E8-2. Convention: own transfer-matrix (TM) one-beam solution vs the solver's f(0,nb0) "
       "(REPRODUCED)")
    # (a) validation of the TM code against the closed-form Fresnel coefficient of an absorbing step
    G0 = np.array([3.0, 4.0, 5.0])
    U1 = 5.0 * (1 + 0.1j)
    h = 0.002
    depth = 60.0
    G1 = np.sqrt(G0**2 + U1)                       # Im > 0: decays downwards for the down wave
    psi = np.exp(-1j * G1 * 0.0) * np.ones(3)
    dpsi = -1j * G1 * psi                         # pure down wave inside the absorbing medium
    for _ in range(int(depth / h)):
        k = G1
        c, sn = np.cos(k * h), np.sin(k * h)
        psi, dpsi = c * psi + sn / k * dpsi, -k * sn * psi + c * dpsi
    Rn = 0.5 * (psi + dpsi / (1j * G0)) / (0.5 * (psi - dpsi / (1j * G0)))
    Rf = (G0 - G1) / (G0 + G1)
    print(f"  (a) absorbing step U = 5(1+0.1i) A^-2: TM {np.round(Rn, 6)}; Fresnel (G0-G1)/(G0+G1) "
          f"{np.round(Rf, 6)}; max diff {np.abs(Rn - Rf).max():.1e}; Im R < 0 (arg near -pi): "
          f"{bool(np.all(Rf.imag < 0))}")
    check("own TM code reproduces the exp(-i omega t) Fresnel coefficient", np.abs(Rn - Rf).max()
          < 1e-9, f"{np.abs(Rn - Rf).max():.1e}")

    out = {}
    for case, sap in (("onebeam_r010", 0.1), ("onebeam_r000", 0.0)):
        run = solver_run(case + "_0")
        b, s, a = run["bulk"], run["surf"], run["amp"]
        G0 = run["G0"]
        stop = a["s_top"]
        # (b) the solver's own discretisation: slice-centre potential, dz = s_top/ns
        nsl = a["ns"]
        dz = a["dz"]
        smid = (np.arange(nsl) + 0.5) * dz
        R_disc = tm_reflect(G0, u00_of_s(smid, b, s, dt, sap), dz)
        # (c) the continuum limit (h = 0.001 and 0.0005 A, midpoint potential)
        Rc = {}
        for hh in (0.001, 0.0005):
            n = int(round(stop / hh))
            hh2 = stop / n
            sm = (np.arange(n) + 0.5) * hh2
            Rc[hh] = tm_reflect(G0, u00_of_s(sm, b, s, dt, sap), hh2)
        Rsol = run["R_top"]
        dd = np.abs(Rsol - R_disc).max()
        dc = np.abs(Rsol - Rc[0.0005]).max()
        dconj = np.abs(Rsol - np.conj(Rc[0.0005])).max()
        conv = np.abs(Rc[0.001] - Rc[0.0005]).max()
        i = int(np.argmax(np.abs(Rsol)))
        print(f"  {case}: {len(G0)} angles {1e3 * run['theta'][0]:.1f}-{1e3 * run['theta'][-1]:.1f} "
              f"mrad, s_top {stop:.5f} A, ns {nsl}, dz {dz:.6f} A, top-layer nuclei s_a {run['s_a']:.5f} A"
              f" (s_top - s_a = {stop - run['s_a']:.5f} A)")
        print(f"     max |R_solver - R_TM(solver slices)| = {dd:.2e}   (same discretisation)")
        print(f"     max |R_solver - R_TM(continuum)|    = {dc:.2e}   max |R_solver - conj(R_TM)| = "
              f"{dconj:.3f};  TM h 0.001 vs 0.0005 A: {conv:.1e};  max |R| {np.abs(Rsol).max():.4f}")
        print(f"     at the largest |R| ({1e3 * run['theta'][i]:.1f} mrad): arg R(s_top) solver "
              f"{np.angle(Rsol[i]):+.4f}, TM continuum {np.angle(Rc[0.0005][i]):+.4f}, conj "
              f"{np.angle(np.conj(Rc[0.0005][i])):+.4f}")
        check(f"{case}: solver f(0,nb0) = TM R (not its conjugate)",
              dc < 1e-3 and dconj > 0.1, f"{dc:.1e} vs conjugate {dconj:.2f}")
        check(f"{case}: TM with the solver's slices reproduces the solver to round-off",
              dd < 1e-8, f"{dd:.1e}")
        out[case] = dict(dc=dc, dd=dd, dconj=dconj)
    return out


# ================================================================================================
# 3. solver amplitudes at the top-layer nuclei, geometry of the top layer, flux, numerical routes
# ================================================================================================
def backbond_of_top(run):
    """In-plane displacement (fractional, a_s1 = (a/2)[110], a_s2 = (a/2)[-110]) from the layer
    below to the top layer, with the solver's shifts: surface atoms +(dxs+dxb, dys+dyb), the topmost
    bulk unit +(dxb, dyb), the unit below +0 (surfio.f90)."""
    b, s = run["bulk"], run["surf"]
    L = [((x + b["dxb"]) % 1, (y + b["dyb"]) % 1, z) for (_, _, x, y, z) in b["atoms"]]
    L += [((x + s["dxs"] + b["dxb"]) % 1, (y + s["dys"] + b["dyb"]) % 1, z + b["cc"])
          for (_, _, x, y, z) in s["atoms"]]
    L.sort(key=lambda t: t[2])
    (x1, y1, _), (x2, y2, _) = L[-2], L[-1]
    d = (((x2 - x1 + 0.5) % 1) - 0.5, ((y2 - y1 + 0.5) % 1) - 0.5)
    return d


def section3():
    hr("E8-3. Solver R at the top-layer nuclei recomputed from amp.txt and the inputs (own geometry)")
    sj = json.loads(SOLVER_JSON.read_text())["cases"]
    worst = 0.0
    rows = []
    for name, c in sj.items():
        for r in c["runs"]:
            d = r["workdir"].split("/")[-1]
            run = solver_run(d)
            Rj = np.array(r["R_layer_re"]) + 1j * np.array(r["R_layer_im"])
            dev = float(np.abs(run["R"] - Rj).max())
            worst = max(worst, dev)
            rows.append((name, d, run["bulk"]["azi"], run["s_a"], run["amp"]["s_top"],
                         run["amp"]["s_top"] - run["s_a"], backbond_of_top(run), dev,
                         float(run["flux"].max()), run["nb"], run["bulk"]["ml"]))
    seen = set()
    print("  case (first run)                 azi   s_a (A)   s_top (A)  s_top-s_a  top-layer shift  "
          "rods  ML   max flux  |R_E8 - R_S5|")
    for (name, d, azi, sa, st, dd, bb, dev, fl, nb, ml) in rows:
        if name in seen:
            continue
        seen.add(name)
        print(f"  {name:30s} {azi:5.1f}  {sa:8.4f}  {st:9.4f}  {dd:8.4f}   ({bb[0]:+.2f},{bb[1]:+.2f})"
              f"      {nb:3d}  {ml:3d}  {fl:.6f}  {dev:.1e}")
    check("S5's stored R_layer equals E8's own conversion of amp.txt", worst < 1e-12, f"{worst:.1e}")
    # two-fold rotation about the normal through the origin: (x, y) -> (-x, -y) mod 1 for every layer
    run = solver_run("chk_a100_N6_B_0")
    b, sf = run["bulk"], run["surf"]
    pos = [((x + b["dxb"]) % 1, (y + b["dyb"]) % 1) for (_, _, x, y, _) in b["atoms"]]
    pos += [((x + sf["dxs"] + b["dxb"]) % 1, (y + sf["dys"] + b["dyb"]) % 1) for (_, _, x, y, _) in sf["atoms"]]
    pos += [(x % 1, y % 1) for (_, _, x, y, _) in b["atoms"]]
    inv = all(abs(((-x) % 1) - x) < 1e-12 or abs(abs(((-x) % 1) - x) - 1) < 1e-12 for p_ in pos for x in p_)
    print(f"  every layer of the 90-layer slab (and the bulk units) maps onto itself under the two-fold "
          f"rotation about the normal (fractional positions 0 or 1/2 only): {inv}; distinct in-plane "
          f"positions {sorted(set((round(x, 6), round(y, 6)) for x, y in pos))}")
    fl_all = max(r[8] for r in rows if r[0] != "chk_a100_N6_A4_cc_a")
    print(f"  largest reflected flux (all cases except the CC = a failure case): {fl_all:.6f}")
    cca = solver_case("chk_a100_N6_A4_cc_a")
    print(f"  CC = a case: max |R|^2 {np.abs(cca['R']).max() ** 2:.2f}, max flux {cca['flux'].max():.2f}"
          f" (unphysical, > 1)")
    # evanescent growth across one unit for the outermost rods of the approach-A cases
    for pre, cc_name in (("chk_a100_N6_A", "a/2"), ("chk_a110_N9_A", "a/2")):
        run = solver_run(pre + "_0")
        gm = np.abs(run["amp"]["gamma"].imag).max(axis=1)
        cc = run["bulk"]["cc"]
        print(f"  {pre}: largest |Gamma| of an evanescent rod {gm.min():.2f}-{gm.max():.2f} rad/A over "
              f"the angles; growth exp(|Gamma| CC) across CC = {cc_name} ({cc:.4f} A): "
              f"{np.exp(gm.min() * cc):.1e} to {np.exp(gm.max() * cc):.1e}; across CC = a: "
              f"{np.exp(gm.min() * A_SI):.1e} to {np.exp(gm.max() * A_SI):.1e}; 1/eps = "
              f"{1 / np.finfo(float).eps:.1e}")
    # the two numerical routes and slice / slab / rod convergence (own differences)
    def cmp(a, b, lab):
        A, B = solver_case(a), solver_case(b)
        assert np.allclose(A["theta"], B["theta"])
        d = np.abs(A["R"] - B["R"])
        m = np.abs(B["R"]) > 0.05
        print(f"  {lab:44s} max |dR| {d.max():.2e}  rel {(d[m] / np.abs(B['R'][m])).max():.2e}")
        return d.max()
    cmp("chk_a100_N6_A", "chk_a100_N6_B", "[100] N=6 A vs B")
    cmp("chk_a110_N9_A", "chk_a110_N9_B", "[110] N=9 A vs B")
    cmp("chk_a100_N6_A_dz005", "chk_a100_N6_A", "[100] N=6 A dz 0.005 vs 0.01")
    cmp("chk_a100_N8_B", "chk_a100_N6_B", "[100] rods N=8 vs 6 (B)")
    cmp("chk_a100_N10_B", "chk_a100_N6_B", "[100] rods N=10 vs 6 (B)")
    cmp("chk_a100m_N6_A", "chk_a100_N6_A", "[100] phi -45 vs +45 deg")
    for az in ("a100_N6", "a110_N9"):
        A, B = solver_case(f"fine_{az}_r000_ML150"), solver_case(f"fine_{az}_r000_ML300")
        d = np.abs(A["R"] - B["R"])
        tot = (A["flux"] > 0.9999)
        print(f"  r = 0, {az}: ML 150 vs 300 differ by more than 1e-3 in R at {int((d > 1e-3).sum())} of "
              f"{len(d)} angles; total reflection (flux > 0.9999) at {int(tot.sum())} angles, max |dR| "
              f"there {d[tot].max():.1e}; largest |R|^2 {max(np.abs(A['R']).max(), np.abs(B['R']).max()) ** 2:.4f}")
    return rows


# ================================================================================================
# 4. engine read-out from the stored exit columns (own implementation) and the per-angle comparison
# ================================================================================================
WIN_START_A, EXIT_EXCL_A, BIN_A, BP_RADIUS = 2500.0, 750.0, 250.0, 0.1   # S5 report 6.1 (definitions)


def engine_readout(col, x0, dx, info, *, lam=LAM, start=WIN_START_A, excl=EXIT_EXCL_A, bin_A=BIN_A,
                   bandpass=None, x_cut=2.0):
    """R at the top-layer nuclei from a y-averaged exit column (E8's own implementation of the
    read-out described in S5 6.1): demodulate by exp(-2 pi i f_c x); ray departure point
    z_s = L - (x - x_s)/tan(theta) (vacuum geometry); window: departure 'start' after first contact
    up to 'excl' before the exit plane; R = <e> exp(+4 pi i f_c x_s) / P_L with the exact vacuum
    factor P_L = exp(-i L q^2/(k + k_z)), q = 2 pi f_c. bandpass: None (raw rows) or a radius in
    1/A (the column is zeroed below x_s + x_cut, band-passed about +f_c, then demodulated)."""
    col = np.asarray(col, complex)
    x = x0 + np.arange(len(col)) * dx
    th = float(info["theta_ext_rad"])
    xs, L, zc = float(info["x_surface_A"]), float(info["L_z_A"]), float(info["z_contact_A"])
    fc = np.sin(th) / lam
    if bandpass is not None:
        c = np.where(x >= xs + x_cut, col, 0.0)
        f = np.fft.fftfreq(len(c), dx)
        col = np.fft.ifft(np.fft.fft(c) * (np.abs(f - fc) <= bandpass))
    k = 2 * np.pi / lam
    q = 2 * np.pi * fc
    PL = np.exp(-1j * L * q * q / (k + np.sqrt(k * k - q * q)))
    Rx = col * np.exp(-2j * np.pi * fc * x) * np.exp(4j * np.pi * fc * xs) / PL
    d = L - (x - xs) / np.tan(th) - zc
    w = (d >= start) & (d < (L - zc) - excl) & (x >= xs + x_cut)
    Rm = Rx[w].mean()
    bins = []
    b = start
    while b < (L - zc) - excl - 1e-9:
        m = w & (d >= b) & (d < b + bin_A)
        if np.any(m):
            bins.append(Rx[m].mean())
        b += bin_A
    spread = max(abs(v - Rm) for v in bins)
    return dict(R=complex(Rm), spread=float(spread), bins=np.array(bins), rows=int(w.sum()),
                d=d, Rx=Rx, x=x)


def engine_case(name, **kw):
    ej = json.loads(ENGINE_JSON.read_text())["cases"][name]
    out = {}
    for ang, a in ej["angles"].items():
        col = np.array(a["col_re"]) + 1j * np.array(a["col_im"])
        info = a["info"]
        ro = engine_readout(col, a["x0_A"], a["dx_A"], info, **kw)
        ro["stored"] = complex(float(a["readout"]["r_top_re"]), float(a["readout"]["r_top_im"]))
        ro["stored_spread"] = float(a["readout"]["max_bin_deviation"])
        ro["theta"] = float(info["theta_ext_rad"])
        ro["commit"] = a.get("engine_commit")
        ro["dirty"] = a.get("engine_dirty")
        ro["info"] = info
        ro["col"] = col
        ro["x0"], ro["dx"] = a["x0_A"], a["dx_A"]
        out[float(ang)] = ro
    return out


def solver_at(case, thetas):
    sc = solver_case(case)
    R = []
    for t in thetas:
        i = int(np.argmin(np.abs(sc["theta"] - t)))
        if abs(sc["theta"][i] - t) > 1e-9:
            raise ValueError(f"{case}: no solver angle at {t}")
        R.append(sc["R"][i])
    return np.array(R)


TOL_REL, TOL_ABS, TOL_SPREAD = 0.05, 0.005, 2.0     # S5 report section 5 (as declared)


def section4():
    hr("E8-4. Engine read-out recomputed from the stored exit columns (own read-out) and the "
       "per-angle comparison with the solver (S5's declared tolerance)")
    res = {}
    for ename, sname in (("eng_a100_dt_r010", "eng_a100_N6_r010"),
                         ("eng_a110_dt_r010", "eng_a110_N9_r010"),
                         ("eng_a100_kk_r010", "eng_a100_N6_r010")):
        raw = engine_case(ename)
        bp = engine_case(ename, bandpass=BP_RADIUS)
        th = np.array(sorted(raw))
        Rraw = np.array([raw[t]["R"] for t in th])
        Rbp = np.array([bp[t]["R"] for t in th])
        Rst = np.array([raw[t]["stored"] for t in th])
        sp_bp = np.array([bp[t]["spread"] for t in th])
        sp_st = np.array([raw[t]["stored_spread"] for t in th])
        thr = np.array([raw[t]["theta"] for t in th])
        Rs = solver_at(sname, thr)
        print(f"\n  {ename} vs {sname}: {len(th)} angles")
        print(f"    own band-passed read-out vs S5's stored R: max |diff| {np.abs(Rbp - Rst).max():.1e};"
              f" own raw-row read-out vs stored: max |diff| {np.abs(Rraw - Rst).max():.1e}; "
              f"spread (own) vs stored: max |diff| {np.abs(sp_bp - sp_st).max():.1e}")
        dR = np.abs(Rbp - Rs)
        tol = TOL_REL * np.abs(Rs) + TOL_ABS + TOL_SPREAD * sp_bp
        darg = wrap(np.angle(Rbp) - np.angle(Rs))
        drel = np.abs(Rbp) / np.abs(Rs) - 1
        print("    theta   sol|R|^2  sol arg   eng|R|^2  eng arg   |dR|     tol    ok   d arg  d|R|/|R|  "
              "s_eng   raw-row |R|^2")
        for i, t in enumerate(th):
            print(f"    {t:6.2f}  {abs(Rs[i]) ** 2:8.5f}  {np.angle(Rs[i]):+6.3f}  {abs(Rbp[i]) ** 2:8.5f}"
                  f"  {np.angle(Rbp[i]):+6.3f}  {dR[i]:.4f}  {tol[i]:.4f}  {'yes' if dR[i] <= tol[i] else 'NO '}"
                  f"  {darg[i]:+.3f}  {drel[i]:+.3f}  {sp_bp[i]:.4f}  {abs(Rraw[i]) ** 2:8.5f}")
        n_ok = int((dR <= tol).sum())
        print(f"    within tolerance: {n_ok} of {len(th)}; excess where failing: "
              f"{[f'{t:.1f}: {dR[i] - tol[i]:+.4f}' for i, t in enumerate(th) if dR[i] > tol[i]]}")
        print(f"    engine |R| below solver at {int((drel < 0).sum())} of {len(th)}; d|R|/|R| "
              f"{drel.min():+.3f} to {drel.max():+.3f}; median |R_eng - R_sol| {np.median(dR):.4f}, "
              f"median |R_eng - conj(R_sol)| {np.median(np.abs(Rbp - np.conj(Rs))):.4f}")
        res[ename] = dict(th=th, thr=thr, Re=Rbp, Rraw=Rraw, Rs=Rs, sp=sp_bp, tol=tol, dR=dR,
                          darg=darg, drel=drel, cases=bp)
    return res


# ================================================================================================
# 5. reference plane: fit of the phase difference, and the power of the declared tolerance
# ================================================================================================
def plane_fit(thr, darg, w=None):
    """Least squares d arg = c + 2 Gamma0 dx (Gamma0 = K sin theta), with the standard errors from
    the residual scatter; and the one-parameter fit with c = 0."""
    G2 = 2 * K_ENG * np.sin(thr)
    X = np.vstack([np.ones_like(G2), G2]).T
    coef, res, *_ = np.linalg.lstsq(X, darg, rcond=None)
    r = darg - X @ coef
    n = len(darg)
    s2 = (r @ r) / max(n - 2, 1)
    cov = s2 * np.linalg.inv(X.T @ X)
    dx0 = float((G2 @ darg) / (G2 @ G2))
    r0 = darg - G2 * dx0
    se0 = float(np.sqrt((r0 @ r0) / max(n - 1, 1) / (G2 @ G2)))
    corr = cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1])
    return dict(c=float(coef[0]), dx=float(coef[1]), se_c=float(np.sqrt(cov[0, 0])),
                se_dx=float(np.sqrt(cov[1, 1])), corr=float(corr), dx0=dx0, se_dx0=se0,
                rms=float(np.sqrt(np.mean(darg**2))), n=n, G2=(G2.min(), G2.max()))


def section5(res4):
    hr("E8-5. Reference plane: phase-difference fit with standard errors; power of the tolerance")
    for ename in ("eng_a100_dt_r010", "eng_a110_dt_r010", "eng_a100_kk_r010"):
        r = res4[ename]
        m = np.abs(r["Rs"]) >= 0.1
        f = plane_fit(r["thr"][m], r["darg"][m])
        print(f"  {ename}: {f['n']} angles with |R_sol| >= 0.1, 2 Gamma0 from {f['G2'][0]:.3f} to "
              f"{f['G2'][1]:.3f} rad/A; d arg = c + 2 Gamma0 dx: c = {f['c']:+.4f} +- {f['se_c']:.4f} rad, "
              f"dx = {f['dx']:+.4f} +- {f['se_dx']:.4f} A (correlation {f['corr']:+.3f}); with c = 0: "
              f"dx = {f['dx0']:+.4f} +- {f['se_dx0']:.4f} A; rms d arg {f['rms']:.4f} rad")
    # a plane error of 0.1 A: phase shift at 12 and 22 mrad (S5's scale statement)
    print(f"  2 K sin(theta) x 0.1 A = {2 * K_ENG * np.sin(0.012) * 0.1:.3f} rad at 12 mrad, "
          f"{2 * K_ENG * np.sin(0.022) * 0.1:.3f} rad at 22 mrad")

    hr("E8-5b. Power of the per-angle tolerance: alternatives run through the same test ([100], DT)")
    r = res4["eng_a100_dt_r010"]
    thr, Rs, Re, sp = r["thr"], r["Rs"], r["Re"], r["sp"]
    tol = TOL_REL * np.abs(Rs) + TOL_ABS + TOL_SPREAD * sp
    def n_fail(Ralt):
        return int((np.abs(Ralt - Rs) > tol).sum())
    print(f"  engine as measured: {n_fail(Re)} of {len(thr)} angles outside")
    print(f"  conjugated engine (convention bug): {n_fail(np.conj(Re))} outside")
    for dxp in (0.005, 0.01, 0.015, 0.02, 0.05):
        print(f"  engine with its reference plane moved by {dxp:.3f} A: "
              f"{n_fail(Re * np.exp(2j * K_ENG * np.sin(thr) * dxp))} outside")
    sc1 = solver_case("fine_a100_N0_r010")
    R1 = np.interp(thr, sc1["theta"], sc1["R"].real) + 1j * np.interp(thr, sc1["theta"], sc1["R"].imag)
    print(f"  the (0,0) rod alone (solver, 1 beam, interpolated on the 0.02 mrad grid): {n_fail(R1)} outside;"
          f" the per-angle |R_1rod - R_13rods| over 15.6-16.8 mrad: "
          f"{np.abs(R1 - Rs)[(thr > 0.01555) & (thr < 0.01685)].min():.3f} to "
          f"{np.abs(R1 - Rs)[(thr > 0.01555) & (thr < 0.01685)].max():.3f}")
    for s in (0.95, 0.90, 0.85):
        print(f"  engine |R| scaled by {s:.2f} (phase unchanged): {n_fail(Re * s)} outside; "
              f"solver |R| scaled by {s:.2f} (|R|^2 {s * s - 1:+.4f}) as a stand-in engine: "
              f"{n_fail(Rs * s)} outside")
    # the tolerance in relative amplitude and in phase at the (0,0,8) peak
    i = int(np.argmin(np.abs(thr - 0.0162)))
    print(f"  at 16.2 mrad: tol = {tol[i]:.4f} = {tol[i] / abs(Rs[i]):.3f} of |R_sol| "
          f"({(1 + tol[i] / abs(Rs[i])) ** 2 - 1:+.2f} / {(1 - tol[i] / abs(Rs[i])) ** 2 - 1:+.2f} in |R|^2);"
          f" a pure phase error passes up to {2 * np.arcsin(tol[i] / (2 * abs(Rs[i]))):.3f} rad")
    j = int(np.argmin(np.abs(thr - 0.021)))
    print(f"  at 21.0 mrad: tol = {TOL_REL * abs(Rs[j]):.5f} (5 %) + {TOL_ABS} + 2 x {sp[j]:.4f} = "
          f"{tol[j]:.4f}; |dR| = {abs(Re[j] - Rs[j]):.4f}; the failing quantity is the complex "
          f"amplitude difference |R_eng - R_sol| (units of |R|), dominated by d|R|/|R| = "
          f"{abs(Re[j]) / abs(Rs[j]) - 1:+.3f} with d arg {wrap(np.angle(Re[j]) - np.angle(Rs[j])):+.3f} rad")


# ================================================================================================
# 6. curve level at the [100] (0,0,8) peak (own parabola, FWHM, phase sweep)
# ================================================================================================
def peak_analysis(th_mrad, R, w_half=None, th_pk_common=None):
    """Parabola through the three highest |R|^2 samples (vertex = peak angle and height); FWHM from
    linear interpolation of |R|^2 at half the parabola height; phase sweep = unwrapped arg R
    (linear interpolation of the unwrapped phase) at th_pk +- w_half."""
    I = np.abs(R) ** 2
    i = int(np.argmax(I))
    x3, y3 = th_mrad[i - 1:i + 2], I[i - 1:i + 2]
    A = np.vstack([x3**2, x3, np.ones(3)]).T
    a, b, c = np.linalg.solve(A, y3)
    tp = -b / (2 * a)
    Ip = c - b * b / (4 * a)
    half = Ip / 2
    lo = i
    while lo > 0 and I[lo] > half:
        lo -= 1
    hi = i
    while hi < len(I) - 1 and I[hi] > half:
        hi += 1
    tl = th_mrad[lo] + (half - I[lo]) * (th_mrad[lo + 1] - th_mrad[lo]) / (I[lo + 1] - I[lo])
    tr = th_mrad[hi - 1] + (half - I[hi - 1]) * (th_mrad[hi] - th_mrad[hi - 1]) / (I[hi] - I[hi - 1])
    ph = np.unwrap(np.angle(R))
    out = dict(tp=tp, Ip=Ip, fwhm=tr - tl, tl=tl, tr=tr)
    if w_half is not None:
        t0 = tp if th_pk_common is None else th_pk_common
        out["sweep"] = float(np.interp(t0 + w_half, th_mrad, ph) - np.interp(t0 - w_half, th_mrad, ph))
    return out


def section6(res4):
    hr("E8-6. Curve level at the [100] (0,0,8) peak: own peak, FWHM and phase sweep")
    fine = solver_case("fine_a100_N6_r010")
    tf = fine["theta"] * 1e3
    pf = peak_analysis(tf, fine["R"])
    pf = peak_analysis(tf, fine["R"], w_half=pf["fwhm"] / 2)
    print(f"  solver fine grid (0.02 mrad): peak {pf['tp']:.4f} mrad, |R|^2 {pf['Ip']:.5f}, FWHM "
          f"{pf['fwhm']:.4f} mrad ({pf['tl']:.3f} to {pf['tr']:.3f}), sweep over +-FWHM/2 {pf['sweep']:+.4f} rad")
    i0, i1 = int(np.argmin(np.abs(tf - 15.5))), int(np.argmin(np.abs(tf - 16.9)))
    ph = np.unwrap(np.angle(fine["R"][i0:i1 + 1]))
    print(f"  solver fine: unwrapped arg R from 15.50 to 16.90 mrad {ph[0]:+.3f} -> {ph[-1]:+.3f} "
          f"(total {ph[-1] - ph[0]:+.3f} rad); monotonic: {bool(np.all(np.diff(ph) > 0))}")
    w = pf["fwhm"] / 2
    for ename in ("eng_a100_dt_r010", "eng_a100_kk_r010"):
        r = res4[ename]
        tm = r["thr"] * 1e3
        sel = (tm >= 15.55) & (tm <= 16.85)
        pe = peak_analysis(tm[sel], r["Re"][sel], w_half=w)
        ps = peak_analysis(tm[sel], r["Rs"][sel], w_half=w)
        pe_c = peak_analysis(tm[sel], r["Re"][sel], w_half=w, th_pk_common=ps["tp"])
        print(f"  {ename} (15.6-16.8 mrad, 0.1 mrad): engine peak {pe['tp']:.4f} | solver same angles "
              f"{ps['tp']:.4f} mrad (diff {pe['tp'] - ps['tp']:+.4f}); peak |R|^2 {pe['Ip']:.5f} | "
              f"{ps['Ip']:.5f} ({pe['Ip'] / ps['Ip'] - 1:+.4f}; in |R| {np.sqrt(pe['Ip'] / ps['Ip']) - 1:+.4f});"
              f" FWHM {pe['fwhm']:.4f} | {ps['fwhm']:.4f} ({pe['fwhm'] / ps['fwhm'] - 1:+.4f}); sweep "
              f"(own peak) {pe['sweep']:+.4f} | {ps['sweep']:+.4f} (diff {pe['sweep'] - ps['sweep']:+.4f});"
              f" sweep about the solver's peak {pe_c['sweep']:+.4f}")
    return pf


# ================================================================================================
# 7. engine version consistency of S5's runs (git history; numerics of the atomic path)
# ================================================================================================
ENGINE_FUNCS = {
    "reflection_holo/forward/multislice/engine.py": ["propagate_slices"],
    "reflection_holo/forward/multislice/potentials.py": ["_phase_factors", "_RealisedAtomic",
                                                         "absorber_profile_V", "_profile"],
    "reflection_holo/forward/multislice/propagator.py": ["propagator_phase", "propagator_kernel"],
    "reflection_holo/forward/multislice/illumination.py": ["sheet_beam_wave", "SheetBeam"],
    "reflection_holo/forward/multislice/grid.py": ["band_limit_mask", "make_grid"],
    "reflection_holo/forward/multislice/physics.py": ["beam_constants"],
    "reflection_holo/forward/cell.py": ["build_reflection_cell"],
}


def _func_src(commit, path, name):
    import ast
    txt = subprocess.run(["git", "-C", str(REPO), "show", f"{commit}:{path}"], capture_output=True,
                         text=True).stdout
    if not txt:
        return None
    tree = ast.parse(txt)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == name:
            return ast.get_source_segment(txt, node)
    return None


def section7():
    hr("E8-7. Engine version of S5's runs: commits recorded per run and the atomic-path code at each")
    ej = json.loads(ENGINE_JSON.read_text())["cases"]
    commits = {}
    for name, c in ej.items():
        for ang, a in c["angles"].items():
            commits.setdefault((a.get("engine_commit", "?")[:7], a.get("engine_dirty")), []).append(
                f"{name}@{ang}")
    for (cm, dirty), runs in commits.items():
        print(f"  engine {cm} dirty={dirty}: {len(runs)} runs ({sorted(set(r.split('@')[0] for r in runs))})")
    first = subprocess.run(["git", "-C", str(REPO), "show",
                            "242b566:tools/validation/rheed_engine_results.json"],
                           capture_output=True, text=True).stdout
    f0 = json.loads(first)["cases"]["eng_a100_dt_r010"]["angles"]["16.2000"]
    print(f"  first recorded engine run (snapshot 242b566): 16.2 mrad, engine {f0['engine_commit'][:7]}, "
          f"r_top {float(f0['readout']['r_top_re']):+.17f} {float(f0['readout']['r_top_im']):+.17f}")
    ref = "a84b4b3"
    allc = sorted({cm for (cm, _) in commits} | {ref})
    same_all = True
    for path, names in ENGINE_FUNCS.items():
        for nm in names:
            srcs = {cm: _func_src(cm, path, nm) for cm in allc}
            base = srcs[ref]
            diff = [cm for cm in allc if srcs[cm] != base]
            same_all &= not diff
            absent = [cm for cm in allc if srcs[cm] is None]
            print(f"  {path.split('/')[-1]}:{nm}: identical at {', '.join(allc)}: {not diff}"
                  + (f" (differs at {diff})" if diff else "")
                  + (f" (absent at {absent})" if absent else ""))
    check("atomic-path functions identical across every engine commit S5 used", same_all,
          "propagate_slices, _RealisedAtomic, propagators, sheet beam, band mask, cell builder")
    a = ej["eng_a100_dt_r010"]["angles"]["16.2000"]
    b = ej["eng_a100_dt_r010__bin_A=250.0"]["angles"]["16.2000"]
    same_col = (a["col_re"] == b["col_re"]) and (a["col_im"] == b["col_im"])
    print(f"  16.2 mrad: main run ({a['engine_commit'][:7]}, dirty {a['engine_dirty']}) and repeat "
          f"({b['engine_commit'][:7]}, dirty {b['engine_dirty']}): stored exit columns identical: {same_col}; "
          f"first-pass r_top equal to the main run's: "
          f"{float(f0['readout']['r_top_re']) == float(a['readout']['r_top_re'])}")
    # after S5: the commit E8 archived for its own engine runs against S5's last engine commit
    later = (SCR / "e8/engine_HEAD/COMMIT").read_text().strip()
    for path, names in (("reflection_holo/forward/multislice/engine.py",
                         ["propagate_slices", "run_realisation", "reflection_setup"]),
                        ("reflection_holo/forward/multislice/potentials.py",
                         ["_RealisedAtomic", "AtomicPotential", "absorber_profile_V"]),
                        ("reflection_holo/forward/multislice/propagator.py", ["propagator_kernel"]),
                        ("reflection_holo/forward/multislice/illumination.py", ["sheet_beam_wave"]),
                        ("reflection_holo/forward/multislice/grid.py", ["band_limit_mask"]),
                        ("reflection_holo/structure/si001.py", ["build_si001_terraces"])):
        for nm in names:
            same = _func_src("a1ef2a0", path, nm) == _func_src(later, path, nm)
            print(f"  {path.split('/')[-1]}:{nm}: identical at a1ef2a0 and {later} (E8's engine runs): {same}")
    st = subprocess.run(["git", "-C", str(REPO), "diff", "--stat", "a84b4b3", "a1ef2a0", "--",
                         "reflection_holo/structure"], capture_output=True, text=True).stdout.strip()
    print(f"  reflection_holo/structure between a84b4b3 and a1ef2a0: "
          f"{'unchanged' if not st else st.splitlines()[-1]}")
    # run_realisation itself: identical text at every commit used
    for cm in allc:
        s = _func_src(cm, "reflection_holo/forward/multislice/engine.py", "run_realisation") or ""
        print(f"  engine.py:run_realisation at {cm}: {len(s.splitlines())} lines, sha256 "
              f"{hashlib.sha256(s.encode()).hexdigest()[:12]}")


# ================================================================================================
# 10. own engine runs (E8 driver; the engine is imported from an archived commit, see --engine-job)
# ================================================================================================
def _engine_job(spec):
    """Runs INSIDE a subprocess whose sys.path starts with spec['engine_root'] (a `git archive` of
    reflection_holo at the stated commit): E8's own flat Si(001) strip after the recipe of H2's
    flat_strip / S5 6.1 (one period built with every builder assertion, tiled along the beam), the
    Doyle-Turner potential written here (engine AtomicPotential with only scattering_factor
    replaced), optional along-beam (ZOLZ) averaging of the slice potentials, and the y-averaged
    exit column saved for E8's read-out."""
    import dataclasses
    import resource
    root = spec["engine_root"]
    sys.path.insert(0, root)
    import reflection_holo
    assert reflection_holo.__file__.startswith(root), reflection_holo.__file__
    from reflection_holo.forward.cell import build_reflection_cell
    from reflection_holo.forward.multislice import (AtomicPotential, MultisliceParams,
                                                    NumericalAbsorber, PhysicalAbsorption,
                                                    SheetBeam, fft_friendly, run_realisation)
    from reflection_holo.structure import Staircase, build_si001_terraces
    A = 5.4309
    Q = A / 4
    th = spec["theta_mrad"] * 1e-3
    azim = spec.get("azimuth", "100")
    P = A if azim == "100" else A / np.sqrt(2.0)
    dz = P / 4.0
    GAP, EDGE, BAB, TAB, WABS = 2.0, 2.0, 15.0, 10.0, 100.0
    depth = BAB + spec.get("clean_A", 55.0)
    sub = int(np.ceil(depth / Q)) + 2
    ent = 10 * dz
    periods = int(np.ceil((GAP / np.tan(th) + spec.get("L_after_A", 4500.0) - ent) / P))
    one = build_si001_terraces(
        azimuth_uvw=(1, 0, 0) if azim == "100" else (1, 1, 0),
        azimuth_label=f"TEST_ONLY: E8 review rerun, exact [{azim}]",
        staircase=Staircase(edges="parallel", terrace_layers=(0,), terrace_widths=(1,),
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
    s = dataclasses.replace(one, positions_A=pos, species=np.tile(one.species, periods),
                            cell_A=cell_A, layer_index=np.tile(one.layer_index, periods),
                            terrace_index=np.tile(one.terrace_index, periods), metadata=md)
    Lz = ent + periods * P
    H = Lz * np.tan(th) - GAP - 1.0
    vac = float(np.ceil(H + Lz * np.tan(th) + 1.0))
    cell = build_reflection_cell(s, vacuum_above_A=vac, depth_below_A=depth, bulk_absorber_A=BAB,
                                 top_absorber_A=TAB, entrance_vacuum_z_A=ent)
    xs = float(cell.metadata["layout"]["highest_surface_x_A"])
    top_atom_x = float(np.asarray(cell.atoms_xyz_A)[:, 0].max())
    a_dt = np.array(spec["dt_a"])
    b_dt = np.array(spec["dt_b"])
    C = spec["C"]

    class DTPotential(AtomicPotential):
        def scattering_factor(self, Z, f2):
            f2 = np.asarray(f2, dtype=np.float64)
            return C * (a_dt[:, None] * np.exp(-b_dt[:, None] * f2.reshape(1, -1) / 4.0)).sum(
                axis=0).reshape(f2.shape)

        def realise(self, *, grid, dz_A, n_slices, backend, rng):
            base = super().realise(grid=grid, dz_A=dz_A, n_slices=n_slices, backend=backend, rng=rng)
            if not spec.get("zolz"):
                return base
            return ZolzRealised(base, backend)

    class ZolzRealised:
        """Along-beam (ZOLZ) average: every crystal slice carries the mean projected potential of
        one full period (4 slices of a/4 at [100]) taken from the middle of the strip."""
        def __init__(self, base, be):
            first = int(np.argmax(np.diff(base.starts) > 0))
            per = int(round(P / dz))
            mid = first + per * ((len(base.starts) - 1 - first) // (2 * per))
            acc = None
            for i in range(mid, mid + per):
                v = base.projected(i)
                acc = v if acc is None else acc + v
            self.V = acc / per
            self.first = first
            self.zero = be.xp.zeros_like(self.V)
            self.metadata = dict(base.metadata, zolz_average=dict(first_crystal_slice=first,
                                                                   period_slices=per, from_slice=mid))

        def slice_key(self, i):
            return "empty" if i < self.first else "zolz"

        def projected(self, i):
            return self.zero if i < self.first else self.V

    absn = PhysicalAbsorption(model="proportional", ratio=0.1,
                              label="TEST_ONLY: stands in for PROJECT_INPUT item 21 (E8 rerun)")
    pot = DTPotential(cell, parameterisation="kirkland", physical_absorption=absn,
                      frozen_phonons=None, static_lattice_label="ASSUMPTION: static lattice")
    beam = SheetBeam(height_A=float(H), edge_A=EDGE, x_bottom_A=xs + GAP, theta_in_ext_rad=th,
                     theta_label="TEST_ONLY: E8 review rerun angle")
    mp = spec["max_pixel_A"]
    nx = fft_friendly(int(np.ceil(cell.extent_x_A / mp)))
    ny = fft_friendly(int(np.ceil(cell.extent_y_A / mp)))
    params = MultisliceParams(energy_keV=200.0, nx=nx, ny=ny, dz_A=dz, propagator="exact",
                              band_limit="2/3", backend="numpy", precision="complex64",
                              threads=int(spec["threads"]),
                              absorber=NumericalAbsorber(strength_V=WABS, profile="sin2"),
                              theta_out_ext_rad=th, buildup_depth_A=20.0,
                              working_reflections_hkl=((0, 0, 8),))
    t0 = time.time()
    ew = run_realisation(cell, potential=pot, beam=beam, params=params, realisation=0, seed=None)
    t1 = time.time()
    col = ew.psi.astype(np.complex128).mean(axis=1)
    info = dict(theta_ext_rad=th, x_surface_A=xs, L_z_A=float(ew.z_A), z_contact_A=GAP / np.tan(th),
                nx=nx, ny=ny, dx_A=ew.dx_A, dy_A=ew.dy_A, n_slices=int(round(Lz / dz)),
                n_atoms=int(len(cell.Z)), top_atom_x_A=top_atom_x, H_A=float(H),
                mip_V=float(pot.mean_inner_potential_V()), run_s=t1 - t0,
                built=int(ew.metadata["slices"]["transmission_functions_built"]),
                peak_rss_MB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
                engine_commit=Path(root, "COMMIT").read_text().strip(),
                positions_sha256_one_period=hashlib.sha256(
                    np.ascontiguousarray(one.positions_A, "<f8").tobytes()).hexdigest())
    np.savez(spec["out"], col=col, x0=ew.x0_A, dx=ew.dx_A, info=json.dumps(info))


def run_engine_job(tag, *, engine_root, theta_mrad, max_pixel_A, zolz, threads, dt, L_after_A=4500.0,
                   azimuth="100"):
    ENGINE_CACHE.mkdir(parents=True, exist_ok=True)
    out = ENGINE_CACHE / f"{tag}.npz"
    if not out.exists():
        spec = dict(engine_root=str(engine_root), theta_mrad=theta_mrad, max_pixel_A=max_pixel_A,
                    zolz=zolz, threads=threads, dt_a=dt["a"], dt_b=dt["b"], C=dt["C"],
                    L_after_A=L_after_A, out=str(out), azimuth=azimuth)
        t = time.time()
        env = dict(os.environ, PYTHONPATH=str(engine_root))
        r = subprocess.run([sys.executable, __file__, "--engine-job", json.dumps(spec)], env=env,
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-2000:], r.stderr[-4000:])
            raise RuntimeError(f"engine job {tag} failed")
        print(f"  [{tag}: computed now in {time.time() - t:.0f} s wall]")
    z = np.load(out, allow_pickle=False)
    info = json.loads(str(z["info"]))
    return dict(col=z["col"], x0=float(z["x0"]), dx=float(z["dx"]), info=info)


ENGINE_MATRIX = [   # (tag, engine archive, theta mrad, max pixel A, zolz, L after contact A)
    ("head_dt_full_p013_t16.2", "engine_HEAD", 16.2, 0.13, False, 4500.0),
    ("head_dt_full_p010_t16.2", "engine_HEAD", 16.2, 0.10, False, 4500.0),
    ("head_dt_full_p0075_t16.2", "engine_HEAD", 16.2, 0.075, False, 4500.0),
    ("head_dt_full_p0065_t16.2", "engine_HEAD", 16.2, 0.065, False, 4500.0),
    ("head_dt_zolz_p013_t16.2", "engine_HEAD", 16.2, 0.13, True, 4500.0),
    ("head_dt_zolz_p010_t16.2", "engine_HEAD", 16.2, 0.10, True, 4500.0),
    ("head_dt_zolz_p0075_t16.2", "engine_HEAD", 16.2, 0.075, True, 4500.0),
    ("head_dt_zolz_p0065_t16.2", "engine_HEAD", 16.2, 0.065, True, 4500.0),
    ("head_dt_zolz_p010_L7000_t16.2", "engine_HEAD", 16.2, 0.10, True, 7000.0),
]
# the like-for-like engine (along-beam average, pixel 0.10 A) and the full engine at 0.10 A at more
# angles, both azimuths: (tag, azimuth, theta mrad, max pixel, zolz)
ENGINE_CURVE = [
    ("c100_zolz_p0075_t12.0", "100", 12.0, 0.075, True), ("c100_full_p0075_t12.0", "100", 12.0, 0.075, False),
    ("c100_zolz_p0075_t15.8", "100", 15.8, 0.075, True), ("c100_full_p0075_t15.8", "100", 15.8, 0.075, False),
    ("c100_zolz_p0075_t16.0", "100", 16.0, 0.075, True), ("c100_zolz_p0075_t16.4", "100", 16.4, 0.075, True),
    ("c100_zolz_p0075_t21.0", "100", 21.0, 0.075, True), ("c100_full_p0075_t21.0", "100", 21.0, 0.075, False),
    ("c110_zolz_p0075_t15.1", "110", 15.1, 0.075, True), ("c110_full_p0075_t15.1", "110", 15.1, 0.075, False),
    ("c110_zolz_p0075_t17.6", "110", 17.6, 0.075, True), ("c110_full_p0075_t17.6", "110", 17.6, 0.075, False),
    ("c110_zolz_p013_t17.6", "110", 17.6, 0.13, True),
]


def section10(dt, threads, only_run=False):
    hr("E8-10. Own engine runs at 16.2 mrad [100] (DT, r = 0.1, static): regression against S5's "
       "stored column, pixel study, along-beam (ZOLZ) averaged potential (MEASURED_HERE)")
    res = {}
    for tag, root, th, mp, zolz, L in ENGINE_MATRIX:
        res[tag] = run_engine_job(tag, engine_root=SCR / "e8" / root, theta_mrad=th, max_pixel_A=mp,
                                  zolz=zolz, threads=threads, dt=dt, L_after_A=L)
    if only_run:
        return res
    ej = json.loads(ENGINE_JSON.read_text())["cases"]["eng_a100_dt_r010"]["angles"]["16.2000"]
    st = np.array(ej["col_re"]) + 1j * np.array(ej["col_im"])
    mine = res["head_dt_full_p013_t16.2"]
    d = np.abs(mine["col"] - st)
    print(f"  regression: E8 run with the engine at {mine['info']['engine_commit']} (git archive) vs S5's "
          f"stored column (148e4f6, 7 significant digits): grid {mine['info']['nx']}x{mine['info']['ny']}x"
          f"{mine['info']['n_slices']} vs {ej['info']['nx']}x{ej['info']['ny']}x{ej['info']['n_slices']}, "
          f"atoms {mine['info']['n_atoms']} vs {ej['info']['n_atoms']}; max |diff| {d.max():.1e} "
          f"(column max {np.abs(st).max():.3f}); relative to |c|: {np.max(d / np.maximum(np.abs(st), 1e-3)):.1e}")
    check("current engine reproduces S5's 16.2 mrad column", d.max() < 1e-5, f"max |diff| {d.max():.1e}")
    print(f"  top-layer nuclei at x = {mine['info']['top_atom_x_A']:.6f} A, reference plane x_s = "
          f"{mine['info']['x_surface_A']:.6f} A (the engine's R is referred to the top-layer nuclei)")
    sol = {n: solver_at(c, [0.0162])[0] for n, c in (("N6", "eng_a100_N6_r010"),
                                                     ("N8", "eng_a100_N8_r010_B"),
                                                     ("N10", "eng_a100_N10_r010_B"))}
    print("  solver at 16.2 mrad: " + ", ".join(f"{k} |R|^2 {abs(v) ** 2:.5f} arg {np.angle(v):+.4f}"
                                                  for k, v in sol.items()))
    g8 = 8 / A_SI
    f_holz = np.sqrt(K_ENG**2 - (K_ENG * np.cos(0.0162) - 2 * np.pi / A_SI) ** 2) / (2 * np.pi)
    print(f"  first along-beam (Laue) ring at 16.2 mrad, period a along [100]: transverse frequency "
          f"{f_holz:.3f} 1/A")
    dy0 = res["head_dt_full_p013_t16.2"]["info"]["dy_A"]
    print(f"  at the production grid dy = {dy0:.5f} A the y band edge 1/(3 dy) = {1 / (3 * dy0):.6f} 1/A and "
          f"the (7,-7) rod 14/a = {14 / A_SI:.6f} 1/A (on the edge); (0,0,16) at 16/a = {16 / A_SI:.4f} "
          f"1/A, (0,0,14) at {14 / A_SI:.4f} 1/A")
    for tag, root, th, mp, zolz, L in ENGINE_MATRIX:
        if zolz or L != 4500.0:
            continue
        dxr = res[tag]["info"]["dx_A"]
        fm = 1 / (3 * dxr)
        hmax = int(np.floor(fm * A_SI / 2 + 1e-9))
        h8 = int(np.floor(np.sqrt(max(fm**2 - g8**2, 0)) * A_SI / 2 + 1e-9))
        print(f"  pixel {dxr:.4f} A: band radius {fm:.3f} 1/A; ZOLZ rods (h,-h) inside up to |h| = "
              f"{hmax}; rods that still carry the (0,0,8) normal component (8/a = {g8:.4f}): |h| <= {h8}"
              f"; first along-beam ring inside the band: {f_holz < fm}")
    print(f"  peak RSS of the E8 engine subprocesses: {min(r['info']['peak_rss_MB'] for r in res.values()):.0f}"
          f" to {max(r['info']['peak_rss_MB'] for r in res.values()):.0f} MB")
    print("  run                              grid          built  run_s  |R|^2(window) arg     "
          "|R|/|R_N10|-1  d arg     plateau bins |R| (2500..3750 A, 250 A)")
    for tag, root, th, mp, zolz, L in ENGINE_MATRIX:
        r = res[tag]
        ro = engine_readout(r["col"], r["x0"], r["dx"], r["info"], bandpass=BP_RADIUS)
        R = ro["R"]
        rel = abs(R) / abs(sol["N10"]) - 1
        da = wrap(np.angle(R) - np.angle(sol["N10"]))
        bins = " ".join(f"{abs(b):.4f}" for b in ro["bins"][:5])
        print(f"  {tag:32s} {r['info']['nx']}x{r['info']['ny']}x{r['info']['n_slices']:<5d} "
              f"{r['info']['built']:5d} {r['info']['run_s']:6.0f}  {abs(R) ** 2:.5f}  {np.angle(R):+.4f}  "
              f"{rel:+.4f}       {da:+.4f}   {bins}")
        res[tag]["R"] = R
        res[tag]["ro"] = ro
    print("  along-beam couplings in the engine (full / along-beam-averaged, same pixel, 4500 A strips):")
    for mp in ("013", "010", "0075", "0065"):
        fu, zo = res[f"head_dt_full_p{mp}_t16.2"], res[f"head_dt_zolz_p{mp}_t16.2"]
        print(f"     pixel {fu['info']['dx_A']:.4f} A: |R_full|/|R_zolz| - 1 = {abs(fu['R']) / abs(zo['R']) - 1:+.4f}, "
              f"arg R_full - arg R_zolz = {wrap(np.angle(fu['R']) - np.angle(zo['R'])):+.4f} rad")
    z1, z2 = res["head_dt_zolz_p010_t16.2"], res["head_dt_zolz_p010_L7000_t16.2"]
    print(f"  strip length (along-beam-averaged, 0.0990 A): 7000 A vs 4500 A: |R| ratio - 1 "
          f"{abs(z2['R']) / abs(z1['R']) - 1:+.4f}, d arg {wrap(np.angle(z2['R']) - np.angle(z1['R'])):+.4f} rad")
    return res



def section10b(dt, threads):
    hr("E8-10b. Like-for-like engine (along-beam-averaged potential, pixel <= 0.075 A) and the full "
       "engine at 0.075 A against the solver at more angles and at [110] (MEASURED_HERE)")
    print("  run                     az    theta  grid           |R|^2    arg      sol |R|^2  sol arg  "
          "|R|/|R_sol|-1  d arg    |dR|    tol(S5 rule)  spread")
    out = {}
    for tag, az, th, mp, zolz in ENGINE_CURVE:
        r = run_engine_job(tag, engine_root=SCR / "e8" / "engine_HEAD", theta_mrad=th, max_pixel_A=mp,
                           zolz=zolz, threads=threads, dt=dt, azimuth=az)
        ro = engine_readout(r["col"], r["x0"], r["dx"], r["info"], bandpass=BP_RADIUS)
        Rs = solver_at("eng_a100_N6_r010" if az == "100" else "eng_a110_N9_r010", [th * 1e-3])[0]
        R = ro["R"]
        tol = TOL_REL * abs(Rs) + TOL_ABS + TOL_SPREAD * ro["spread"]
        print(f"  {tag:23s} [{az}] {th:5.1f}  {r['info']['nx']}x{r['info']['ny']}x{r['info']['n_slices']:<5d}"
              f" {abs(R) ** 2:.5f}  {np.angle(R):+.4f}  {abs(Rs) ** 2:.5f}   {np.angle(Rs):+.4f}  "
              f"{abs(R) / abs(Rs) - 1:+.4f}        {wrap(np.angle(R) - np.angle(Rs)):+.4f}  "
              f"{abs(R - Rs):.4f}  {tol:.4f}        {ro['spread']:.4f}")
        out[tag] = dict(R=R, Rs=Rs)
    # peak angle from the three points 16.0, 16.2, 16.4 mrad, same method for every curve
    def vertex(th3, I3):
        a, b, c = np.polyfit(th3, I3, 2)
        return -b / (2 * a), c - b * b / (4 * a)
    th3 = np.array([16.0, 16.2, 16.4])
    z16 = run_engine_job("head_dt_zolz_p0075_t16.2", engine_root=SCR / "e8" / "engine_HEAD",
                         theta_mrad=16.2, max_pixel_A=0.075, zolz=True, threads=threads, dt=dt)
    zR = [out["c100_zolz_p0075_t16.0"]["R"],
          engine_readout(z16["col"], z16["x0"], z16["dx"], z16["info"], bandpass=BP_RADIUS)["R"],
          out["c100_zolz_p0075_t16.4"]["R"]]
    sR = solver_at("eng_a100_N6_r010", th3 * 1e-3)
    s5 = engine_case("eng_a100_dt_r010", bandpass=BP_RADIUS)
    fR = [s5[t]["R"] for t in (16.0, 16.2, 16.4)]
    pz, ps, pf = (vertex(th3, np.abs(np.array(v)) ** 2) for v in (zR, sR, fR))
    print(f"  peak from the parabola through 16.0/16.2/16.4 mrad: averaged engine 0.075 A {pz[0]:.4f} mrad "
          f"(|R|^2 {pz[1]:.5f}); solver 13 rods {ps[0]:.4f} ({ps[1]:.5f}); full engine 0.13 A (S5 runs) "
          f"{pf[0]:.4f} ({pf[1]:.5f}); shifts vs solver {pz[0] - ps[0]:+.4f} and {pf[0] - ps[0]:+.4f} mrad")
    return out

# ================================================================================================
# 11. rung-2 continuum problem (P2 exact reference, E1 R2-A set-up) at the atomistic runs' pixels
# ================================================================================================
def _rung2_job(spec):
    """Runs INSIDE a subprocess with the archived engine and tests/forward on sys.path: the R2-A
    cell (r = 0.1, exact propagator, clean 100 A, exit 5000 A after the top-edge contact, dz 1 A)
    at the pixel dx (x_s = 115 A on a pixel centre), read with flat_reflection_coefficient, against
    P2's exact reference (ladder_cases.rung2_measure, used as it is in tests/forward)."""
    sys.path.insert(0, str(Path(spec["engine_root"]) / "tests" / "forward"))
    from ladder_cases import rung2_measure
    out = {}
    for dx in spec["dx"]:
        t = time.time()
        res = rung2_measure(0.1, dx=dx, propagator="exact", clean_A=100.0,
                            exit_after_top_contact_A=5000.0, dz=1.0, H=24.0, edge=4.0, gap=2.0,
                            absorber_A=15.0, top_A=10.0, W0=100.0, entrance_A=10.0,
                            extra_vacuum_A=150.0, buildup_A=20.0, precision="complex128")
        out[repr(dx)] = dict(eta=res["eta"].tolist(), r_re=res["r"].real.tolist(),
                             r_im=res["r"].imag.tolist(), ref_re=res["R_ref"].real.tolist(),
                             ref_im=res["R_ref"].imag.tolist(), nx=int(res["nx"]),
                             dx=float(res.get("dx", dx)), time_s=time.time() - t)
    Path(spec["out"]).write_text(json.dumps(out))


def section11():
    hr("E8-11. Rung-2 continuum Bragg case (P2 exact reference) at coarse pixels: is the engine's "
       "1D amplitude pixel-sensitive? (MEASURED_HERE)")
    root = SCR / "e8" / "engine_HEAD"
    out = ENGINE_CACHE / "rung2_pixels.json"
    dxs = [115.0 / 885, 115.0 / 1150, 115.0 / 2300, 115.0 / 4600]    # x_s = 115 A on a pixel centre
    if not out.exists():
        spec = dict(engine_root=str(root), dx=dxs, out=str(out))
        env = dict(os.environ, PYTHONPATH=f"{root}:{root}/tests/forward")
        r = subprocess.run([sys.executable, __file__, "--rung2-job", json.dumps(spec)], env=env,
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-2000:], r.stderr[-4000:])
            raise RuntimeError("rung-2 job failed")
    d = json.loads(out.read_text())
    print("  dx (A)    nx     bins |eta|<=3  max|r-R_ref|  at eta~0: |r|/|R_ref|-1  d arg     "
          "mean over |eta|<=1 of |r|/|R_ref|-1   run s")
    for k, v in d.items():
        eta = np.array(v["eta"])
        r = np.array(v["r_re"]) + 1j * np.array(v["r_im"])
        R = np.array(v["ref_re"]) + 1j * np.array(v["ref_im"])
        m3 = np.abs(eta) <= 3
        m1 = np.abs(eta) <= 1
        i0 = int(np.argmin(np.abs(eta)))
        print(f"  {v['dx']:.5f}  {v['nx']:6d}  {int(m3.sum()):4d}        {np.abs(r - R)[m3].max():.2e}"
              f"      {abs(r[i0]) / abs(R[i0]) - 1:+.4f} (eta {eta[i0]:+.2f})  "
              f"{wrap(np.angle(r[i0]) - np.angle(R[i0])):+.4f}   "
              f"{np.mean(np.abs(r[m1]) / np.abs(R[m1]) - 1):+.4f}                       {v['time_s']:.0f}")
    return d



def section7b():
    hr("E8-7b. Git history of the S5 tool: tolerance block and engine set-up across the snapshots")
    import ast
    snaps = subprocess.run(["git", "-C", str(REPO), "log", "--reverse", "--format=%h %ad",
                            "--date=format-local:%Y-%m-%d %H:%M:%S", "872e949", "--",
                            "tools/validation/rheed_solver_compare.py"],
                           capture_output=True, text=True, env=dict(os.environ, TZ="UTC")).stdout.split("\n")
    snaps = [ln.split(" ", 1) for ln in snaps if ln.strip()]
    ref_tol = None
    for h, date in snaps:
        txt = subprocess.run(["git", "-C", str(REPO), "show", f"{h}:tools/validation/rheed_solver_compare.py"],
                             capture_output=True, text=True).stdout
        m = re.search(r"^TOL_REL = .*?^TOL_SWEEP_RAD = [^\n]*", txt, re.M | re.S)
        tol = m.group(0) if m else None
        ref_tol = ref_tol or tol
        tree = ast.parse(txt)
        hs = {}
        for n in ast.walk(tree):
            if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in (
                    "DoyleTurnerPotential", "engine_flat_strip", "engine_readout"):
                hs[n.name] = hashlib.sha256(ast.get_source_segment(txt, n).encode()).hexdigest()[:8]
        ej = subprocess.run(["git", "-C", str(REPO), "show", f"{h}:tools/validation/rheed_engine_results.json"],
                            capture_output=True, text=True).stdout
        eu = json.loads(ej).get("updated_utc") if ej.strip() else None
        print(f"  {h} {date} UTC: tolerance block identical to the first: {tol == ref_tol}; "
              f"engine results file updated {eu}; set-up hashes {hs}")
    print("  first tolerance block:\n    " + (ref_tol or "none").replace("\n", "\n    "))

# ================================================================================================
# 8. H2's stored plateaus converted to R at the top layer (own conversion) against the solver
# ================================================================================================
def section8():
    hr("E8-8. H2's stored flat-strip plateaus (Kirkland engine) converted to R at the top-layer nuclei")
    hj = json.loads((REPO / "tools/hpc/supercell_sizing_measurements.json").read_text())["runs"]
    for run, scase in (("bu_100_r010", "h2_a100_N6_r010"), ("bu_110_r010", "h2_a110_N9_r010"),
                       ("bu_100_r000", "h2_a100_N6_r000_ML150"), ("bu_100_r000", "h2_a100_N6_r000_ML300")):
        v = hj[run]
        info = v["info"]
        b = v["buildup"]
        e = b["R_plateau_abs"] * np.exp(1j * b["R_plateau_arg"])
        th = info["theta_ext_rad"]
        fc = np.sin(th) / LAM
        q = 2 * np.pi * fc
        PL = np.exp(-1j * info["L_z_A"] * q * q / (K_ENG + np.sqrt(K_ENG**2 - q * q)))
        R = e * np.exp(4j * np.pi * fc * info["x_surface_A"]) / PL
        Rs = solver_case(scase)["R"][0]
        print(f"  {run} (plateau {b['plateau_A'][0]:.0f}-{b['plateau_A'][1]:.0f} A, theta {1e3 * th:.4f} "
              f"mrad): engine |R|^2 {abs(R) ** 2:.5f} arg {np.angle(R):+.4f}; solver {scase} |R|^2 "
              f"{abs(Rs) ** 2:.5f} arg {np.angle(Rs):+.4f}; |dR| {abs(R - Rs):.4f}, d arg "
              f"{wrap(np.angle(R) - np.angle(Rs)):+.4f}, |R_eng|/|R_sol| - 1 {abs(R) / abs(Rs) - 1:+.4f}")


# ================================================================================================
# 9. incident amplitude of the sheet beam at the surface in the read-out window (vacuum, own FFT)
# ================================================================================================
def section9(res4):
    hr("E8-9. Incident sheet-beam amplitude at the surface plane in the read-out window (vacuum "
       "propagation of the launched wave, no crystal; own 1D FFT with the exact kernel and 2/3 band)")
    for ename in ("eng_a100_dt_r010",):
        for ang in (12.0, 16.2, 21.0):
            ro = res4[ename]["cases"][ang]
            info = ro["info"]
            th, xs, L, zc, H = (float(info["theta_ext_rad"]), float(info["x_surface_A"]),
                                float(info["L_z_A"]), float(info["z_contact_A"]), float(info["H_A"]))
            nx = int(info["nx"])
            dx = ro["dx"]
            x = np.arange(nx) * dx
            fc = np.sin(th) / LAM
            # launched wave: sin^2-edged sheet (edge 2 A) from xs + 2 to xs + 2 + H, projected onto f < 0
            a0, e0 = xs + 2.0, 2.0
            A = np.zeros(nx)
            A[(x >= a0 + e0) & (x <= a0 + H - e0)] = 1.0
            lo = (x > a0) & (x < a0 + e0)
            A[lo] = np.sin(0.5 * np.pi * (x[lo] - a0) / e0) ** 2
            hi = (x > a0 + H - e0) & (x < a0 + H)
            A[hi] = np.sin(0.5 * np.pi * (a0 + H - x[hi]) / e0) ** 2
            f = np.fft.fftfreq(nx, dx)
            S = np.fft.fft(A * np.exp(-2j * np.pi * fc * x))
            S[f >= 0] = 0.0
            band = np.abs(f) <= 1.0 / (3 * dx)
            q = 2 * np.pi * f
            kz = np.sqrt(np.maximum(K_ENG**2 - q * q, 0.0))
            phase = -q * q / (K_ENG + kz)
            dwin = ro["d"]
            wrows = (dwin >= WIN_START_A) & (dwin < (L - zc) - EXIT_EXCL_A) & (ro["x"] >= xs + 2.0)
            ds = dwin[wrows]
            z = zc + ds
            # field at x = xs for every z: sum_f S(f) band(f) exp(i z phase(f)) exp(2 pi i f xs) / nx
            M = np.exp(1j * np.outer(z, phase)) * (S * band * np.exp(2j * np.pi * f * xs))[None, :]
            psi = M.sum(axis=1) / nx
            ideal = np.exp(-2j * np.pi * fc * xs) * np.exp(-1j * z * (2 * np.pi * fc) ** 2 /
                                                              (K_ENG + np.sqrt(K_ENG**2 - (2 * np.pi * fc) ** 2)))
            rel = psi / ideal
            below = H - ((L - zc) - EXIT_EXCL_A) * np.tan(th)
            print(f"  {ename} {ang:.1f} mrad: the window's last ray left the sheet {below:.2f} A below its "
                  f"top edge (sheet height {H:.2f} A)")
            print(f"  {ename} {ang:.1f} mrad: window {WIN_START_A:.0f}-{(L - zc) - EXIT_EXCL_A:.0f} A after "
                  f"first contact; incident amplitude / ideal plane wave at x_s: mean {abs(rel.mean()):.4f}"
                  f" (arg {np.angle(rel.mean()):+.4f}), range {np.abs(rel).min():.4f}-{np.abs(rel).max():.4f}")
            # read-out normalised row by row by the incident field at the ray's departure point
            # (local approximation: the reflection builds up over ~2000 A, so this is indicative)
            Rrow = ro["Rx"][wrows]
            Rn = Rrow / rel
            def spread(v):
                bins = [v[(ds >= b) & (ds < b + BIN_A)].mean() for b in np.arange(WIN_START_A,
                        (L - zc) - EXIT_EXCL_A - BIN_A + 1e-9, BIN_A)]
                return max(abs(q - v.mean()) for q in bins)
            print(f"     window mean |R|^2 plain {abs(Rrow.mean()) ** 2:.5f}, incident-normalised "
                  f"{abs(Rn.mean()) ** 2:.5f} (ratio {abs(Rn.mean()) / abs(Rrow.mean()) - 1:+.4f} in |R|); "
                  f"250 A bin spread plain {spread(Rrow):.4f}, normalised {spread(Rn):.4f}")


# ================================================================================================
# 12. S5's tool as a black box: report mode re-run and compared with S5's saved output
# ================================================================================================
def section12():
    hr("E8-12. The S5 tool's report mode re-run (black box) and compared with its saved output")
    saved = (SOLVER_DIR / "report_final.txt").read_text().splitlines()
    r = subprocess.run([sys.executable, str(REPO / "tools/validation/rheed_solver_compare.py")],
                       capture_output=True, text=True, cwd=str(REPO))
    new = r.stdout.splitlines()
    diff = [(a, b) for a, b in zip(saved[1:], new[1:]) if a != b]
    print(f"  exit status {r.returncode} (1 = a self-check fails: the 21.0 mrad [100] tolerance); "
          f"{len(saved)} saved lines, {len(new)} new lines; lines that differ (apart from the header):"
          f" {len(diff)}")
    for a, b in diff:
        print(f"     saved: {a.strip()}\n     now:   {b.strip()}")


# ================================================================================================
# 13. the P49 Eq. (36) assignment against the codes' strans (algebra, numerically)
# ================================================================================================
def section13():
    hr("E8-13. Which amplitude does each formula return? (absorbing step, exp(-i omega t) solution)")
    G0 = 4.0
    U = 5.0 * (1 + 0.1j)
    G1 = np.sqrt(G0**2 + U)
    R = (G0 - G1) / (G0 + G1)                    # exp(-i omega t) Fresnel coefficient at s = 0
    psi, dpsi = 1 + R, 1j * G0 * (R - 1)         # vacuum side at s = 0: exp(-i G0 s) + R exp(+i G0 s)
    f_code = (G0 * psi - 1j * dpsi) / (G0 * psi + 1j * dpsi)          # strans (both codes)
    f_eq36 = (G0 + 1j * dpsi / psi) / (G0 - 1j * dpsi / psi)          # P49 Eq. (36), same (Q, P)
    c, dc = np.conj(psi), np.conj(dpsi)                                # exp(+i omega t) solution
    f_eq36_conj = (G0 + 1j * dc / c) / (G0 - 1j * dc / c)
    print(f"  R (Fresnel, exp(-i w t)) = {R:.6f}")
    print(f"  code formula (Gamma Q - i P)(Gamma Q + i P)^-1 on the physical solution: {f_code:.6f}")
    print(f"  Eq. (36) (Gamma + i P Q^-1)(Gamma - i P Q^-1)^-1 on the same solution: {f_eq36:.6f} "
          f"= 1/R: {abs(f_eq36 - 1 / R) < 1e-12}")
    print(f"  Eq. (36) on the exp(+i w t) solution (conjugated psi): {f_eq36_conj:.6f} = conj(R): "
          f"{abs(f_eq36_conj - np.conj(R)) < 1e-12}")
    check("code formula returns R, Eq. (36) returns conj(R) for the exp(+i w t) solution",
          abs(f_code - R) < 1e-12 and abs(f_eq36_conj - np.conj(R)) < 1e-12, "algebra")



# ================================================================================================
def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--sections", default="1,2,3,4,5,6,7,8,9,10,11,12,13")
    p.add_argument("--engine-job", default=None)
    p.add_argument("--rung2-job", default=None)
    p.add_argument("--threads", type=int, default=2)
    p.add_argument("--only-run", action="store_true")
    a = p.parse_args(argv)
    if a.engine_job:
        _engine_job(json.loads(a.engine_job))
        return 0
    if a.rung2_job:
        _rung2_job(json.loads(a.rung2_job))
        return 0
    secs = {int(x) for x in a.sections.split(",")}
    t0 = time.time()
    print(f"E8 recompute; repository HEAD "
          f"{subprocess.run(['git', '-C', str(REPO), 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True).stdout.strip()}"
          f"; sections {sorted(secs)}")
    dt = section1()
    if 2 in secs:
        section2(dt)
    if 3 in secs:
        section3()
    r4 = section4() if secs & {4, 5, 6, 9} else None
    if 5 in secs:
        section5(r4)
    if 6 in secs:
        section6(r4)
    if 7 in secs:
        section7()
        section7b()
    if 8 in secs:
        section8()
    if 9 in secs:
        section9(r4)
    if 10 in secs:
        section10(dt, a.threads, a.only_run)
        section10b(dt, a.threads)
    if 11 in secs:
        section11()
    if 12 in secs:
        section12()
    if 13 in secs:
        section13()
    hr("Summary of self-checks")
    for name, ok, det in CHECKS:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: {det}")
    print(f"\n{sum(c[1] for c in CHECKS)}/{len(CHECKS)} checks pass; ran in {time.time() - t0:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
