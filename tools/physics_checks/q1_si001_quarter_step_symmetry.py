#!/usr/bin/env python3
r"""
C2 question 1: symmetry of the a/4 single-layer step on bulk-terminated Si(001).

Run:  venv/bin/python tools/physics_checks/q1_si001_quarter_step_symmetry.py
Exit status 0 only if every self-check passes.  Report: docs/agent_reports/C2_phase2_physics_checks.md

Conventions (docs/physics_conventions.md): exp(+i k.r); angular wavevectors in rad/A; theta is the
glancing angle to the surface plane; outward normal n_hat = [001] (cubic crystal axes);
Delta_phi = phi(upper) - phi(lower).  Atom positions are handled as exact integers in units of a/4
on the cubic axes and converted to A with a = 5.4309 A (reflection_holo.constants.A_SI_A,
ASSUMPTION B2).  Azimuth angles phi are measured in the (001) plane from [100] towards [010].

Premises (DERIVED_HERE unless labelled):
  P1  Bulk-terminated, unrelaxed terraces (ASSUMPTION B3).  Terrace N is the half crystal
      H_N = {diamond sites n with n3 <= N} (z = n3 a/4).  An a/4 up-step joins the lower terrace
      H_0 to the upper terrace H_1; both are truncations of ONE lattice (as in the package builder).
  P2  Each terrace is laterally infinite and semi-infinite (the terrace amplitude far from the
      riser, model_assumptions B4).
  P3  The scattering potential of a terrace, including any absorptive part and thermal averaging,
      is invariant under every isometry that maps its atoms onto themselves.
  P4  Elastic scattering of a monochromatic plane wave; amplitudes of vacuum plane waves; no
      magnetic field in the scattering region.
  P5  Used only where stated ("reciprocity route"): A(k -> k') = A(-k' -> -k) for the specular
      beam, from the symmetry G(r, r') = G(r', r) of the Green's function of a local, possibly
      complex (absorbing) potential.  Checked on the toy model in section H.

Covariance (DERIVED_HERE, section 2 of the report): if the upper terrace is S(lower), S r = M r + t,
then A_upper(k_in -> k_out) = exp(-i (k_out - k_in).t) A_lower(M^T k_in -> M^T k_out).

Sections: A site rule; B the 48 point operations of m-3m and their Fd-3m translation cosets;
C exhaustive search of isometries mapping half crystals onto half crystals; D classification
(screw axes, mirror / glide planes, glide vectors); E incidence-plane test per azimuth;
F azimuth orbits and misalignment; G package cross-check; H multiple-scattering toy (Foldy-Lax
point scatterers) checking covariance, reciprocity and the consequences; I reconstruction symmetry
toy (TEST_ONLY displacements, no sourced dimer geometry); J geometric step phases at 200 keV.
"""
from __future__ import annotations

import importlib.util
import itertools
import pathlib
import sys
from fractions import Fraction

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from reflection_holo.constants import A_SI_A, DIAMOND_BASIS  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "c2_calc", REPO / "tools" / "reflection_step_phase_calculator.py")
calc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(calc)

A = float(A_SI_A)
QA = A / 4.0                       # a/4 in A: the layer spacing and the grid unit
CHECKS: list[tuple[str, bool]] = []


def rule(title: str) -> None:
    print()
    print("=" * 100)
    print(title)
    print("=" * 100)


def check(name: str, ok: bool, detail: str = "") -> None:
    CHECKS.append((name, bool(ok)))
    print(f"   [{'PASS' if ok else 'FAIL'}] {name}" + (f"   ({detail})" if detail else ""))


def check_close(name: str, got: float, want: float, tol: float, unit: str = "") -> None:
    ok = bool(abs(got - want) <= tol)
    CHECKS.append((name, ok))
    print(f"   [{'PASS' if ok else 'FAIL'}] {name}: got {got:.12g} {unit} want {want:.12g} "
          f"+/- {tol:g}")


# ================================================================================================
# A. Diamond site rule from DIAMOND_BASIS (integer a/4 units)
# ================================================================================================
BQ = np.rint(4.0 * DIAMOND_BASIS).astype(np.int64)          # basis in a/4 units


def is_site(n: np.ndarray) -> np.ndarray:
    """Diamond site test on integer a/4 coordinates (..., 3)."""
    n = np.asarray(n, dtype=np.int64)
    par = n % 2
    s = n.sum(axis=-1) % 4
    even = np.all(par == 0, axis=-1)
    odd = np.all(par == 1, axis=-1)
    return (even & (s == 0)) | (odd & (s == 3))


def in_half(n: np.ndarray, N: int) -> np.ndarray:
    """Membership of the half crystal H_N = {sites with n3 <= N}."""
    n = np.asarray(n, dtype=np.int64)
    return is_site(n) & (n[..., 2] <= N)


def sites_box(lo, hi) -> np.ndarray:
    """All diamond sites with lo <= n <= hi (componentwise, a/4 units), generated from the basis."""
    lo = np.asarray(lo, int)
    hi = np.asarray(hi, int)
    cl = np.floor(lo / 4).astype(int) - 1
    ch = np.ceil(hi / 4).astype(int) + 1
    cells = np.stack(np.meshgrid(*[np.arange(cl[k], ch[k] + 1) for k in range(3)],
                                 indexing="ij"), axis=-1).reshape(-1, 3)
    n = (4 * cells[:, None, :] + BQ[None, :, :]).reshape(-1, 3)
    keep = np.all((n >= lo) & (n <= hi), axis=1)
    n = np.unique(n[keep], axis=0)
    return n


def section_A() -> None:
    rule("A. DIAMOND SITE RULE (integer a/4 units) FROM reflection_holo.constants.DIAMOND_BASIS")
    lo, hi = np.array([-8, -8, -8]), np.array([8, 8, 8])
    gen = sites_box(lo, hi)
    grid = np.stack(np.meshgrid(*[np.arange(-8, 9)] * 3, indexing="ij"), axis=-1).reshape(-1, 3)
    ruled = grid[is_site(grid)]
    same = (len(gen) == len(ruled)
            and np.array_equal(np.unique(gen, axis=0), np.unique(ruled, axis=0)))
    print(f"   sites generated from the 8-atom basis in [-8, 8]^3: {len(gen)}; "
          f"sites satisfying the parity rule: {len(ruled)}")
    print("   rule: all even with n1+n2+n3 = 0 (mod 4), or all odd with n1+n2+n3 = 3 (mod 4)")
    check("A1 parity rule == basis-generated site set", same)
    top0 = gen[gen[:, 2] == 0][:3]
    top1 = gen[gen[:, 2] == 1][:3]
    print(f"   examples: layer n3 = 0 (top of H_0): {top0.tolist()};  layer n3 = 1 (top of H_1): "
          f"{top1.tolist()}")


# ================================================================================================
# B. The 48 point operations of m-3m and their Fd-3m translation cosets
# ================================================================================================
def point_ops() -> list[np.ndarray]:
    ops = []
    for perm in itertools.permutations(range(3)):
        for signs in itertools.product((1, -1), repeat=3):
            M = np.zeros((3, 3), dtype=np.int64)
            for i, (p, s) in enumerate(zip(perm, signs)):
                M[i, p] = s
            ops.append(M)
    return ops


def _int_axis(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, float)
    v = v / np.max(np.abs(v))
    k = np.rint(v * 6)
    g = np.gcd.reduce(np.abs(k[k != 0]).astype(int))
    k = (k / g).astype(int)
    first = k[np.nonzero(k)[0][0]]
    return -k if first < 0 else k


def _fmt_uvw(u) -> str:
    return "".join(str(int(x)) for x in u).replace("-1", "-1").replace("--", "-")


def describe_op(M: np.ndarray) -> str:
    """Hermann-Mauguin-like name of a cubic point operation (axis or plane NORMAL in brackets)."""
    M = np.asarray(M, float)
    det = int(round(np.linalg.det(M)))
    R = M if det == 1 else -M
    trR = int(round(np.trace(R)))
    if trR == 3:
        return "1" if det == 1 else "-1"
    w, V = np.linalg.eig(R)
    ax = np.real(V[:, np.argmin(np.abs(w - 1.0))])
    axis = _int_axis(ax)
    order = {-1: 2, 0: 3, 1: 4}[trR]
    sense = ""
    if order in (3, 4):
        a = axis / np.linalg.norm(axis)
        perp = np.cross(a, [1.0, 0.0, 0.0])
        if np.linalg.norm(perp) < 1e-9:
            perp = np.cross(a, [0.0, 1.0, 0.0])
        s = np.dot(a, np.cross(perp, R @ perp))
        sense = "+" if s > 0 else "-"
    uvw = "[" + ",".join(str(int(x)) for x in axis) + "]"
    if det == 1:
        return f"{order}{sense}{uvw}"
    if order == 2:
        return "m(" + ",".join(str(int(x)) for x in axis) + ")"      # plane with this normal
    return f"-{order}{sense}{uvw}"


def maps_diamond(M: np.ndarray, t: np.ndarray) -> bool:
    """(M, t) maps the whole diamond structure onto itself (basis test, both directions)."""
    img = BQ @ M.T + t
    pre = (BQ - t) @ M
    return bool(is_site(img).all() and is_site(pre).all())


COSET_REPS = (np.array([0, 0, 0]), np.array([1, 1, 1]))        # D modulo the fcc lattice


def section_B():
    rule("B. THE 48 POINT OPERATIONS OF m-3m AND THEIR Fd-3m TRANSLATION COSETS")
    ops = point_ops()
    keys = {tuple(M.ravel()) for M in ops}
    closed = all(tuple((A_ @ B_).ravel()) in keys for A_ in ops for B_ in ops)
    check("B1 48 distinct signed permutation matrices forming a group", len(keys) == 48 and closed)
    cos = {}
    for M in ops:
        ok = [i for i, t in enumerate(COSET_REPS) if maps_diamond(M, t)]
        cos[tuple(M.ravel())] = ok
    n_td = sum(1 for v in cos.values() if v == [0])
    n_other = sum(1 for v in cos.values() if v == [1])
    print("   For every point operation M exactly one translation coset makes (M, t) a symmetry of")
    print("   the diamond structure: t in the fcc lattice (the 24 operations of -43m = Td, the site")
    print("   symmetry of the atom at the origin) or t in (a/4)(1,1,1) + fcc (the other 24).")
    print(f"   operations with t in fcc: {n_td};  with t in (a/4)(1,1,1) + fcc: {n_other}")
    check("B2 every point operation has exactly one coset; 24 + 24",
          n_td == 24 and n_other == 24 and all(len(v) == 1 for v in cos.values()))
    ez = np.array([0, 0, 1])
    fix = [M for M in ops if np.array_equal(M @ ez, ez)]
    print("   Operations that fix the outward normal [001] (the only ones that can map a half crystal")
    print("   z <= c onto a half crystal z <= c'):")
    for M in fix:
        c = cos[tuple(M.ravel())][0]
        print(f"      {describe_op(M):>10s}  M = {M.tolist()}   coset t in "
              f"{'fcc' if c == 0 else '(a/4)(1,1,1) + fcc'}   ->  t_z in "
              f"{'(a/2) Z' if c == 0 else 'a/4 + (a/2) Z'}")
    check("B3 exactly 8 operations fix [001] (point group 4mm)", len(fix) == 8)
    return ops, cos


# ================================================================================================
# C. Exhaustive search on the TRUNCATED half crystals
# ================================================================================================
L_PATCH, D_PATCH = 16, 16          # test patch: |n1|,|n2| <= 16, N - 16 <= n3 <= N  (a/4 units)
W_WIN, D_WIN = 8, 8                # candidate window for S(p0): |q1|,|q2| <= 8, N' - 8 <= q3 <= N'
NET = np.array([[2, 2, 0], [2, -2, 0]])      # (001) surface net of H_N, a/4 units: (a/2)[110], (a/2)[1-10]


def patch(N: int) -> np.ndarray:
    return sites_box([-L_PATCH, -L_PATCH, N - D_PATCH], [L_PATCH, L_PATCH, N])


def net_key(t: np.ndarray) -> tuple:
    """Class of an in-plane translation modulo the surface net (fractional net coordinates)."""
    u = Fraction(int(t[0]) + int(t[1]), 4)
    v = Fraction(int(t[0]) - int(t[1]), 4)
    return (u - (u.numerator // u.denominator), v - (v.numerator // v.denominator), int(t[2]))


def half_crystal_ops(ops, N_src: int, N_dst: int):
    """Every (M, t) with M in m-3m mapping H_N_src onto H_N_dst, tested on the atoms.

    The candidate translations are exhaustive: S(p0) must be an atom of H_N_dst for a fixed atom
    p0 of the top layer of H_N_src, so t = q - M p0 with q running over the atoms of H_N_dst in a
    window larger than one surface-net cell and several layers deep. Each candidate is tested in
    both directions on a patch (S(P_src) inside H_dst and S^-1(P_dst) inside H_src).
    """
    P_src, P_dst = patch(N_src), patch(N_dst)
    p0 = P_src[(P_src[:, 2] == N_src)][0]
    win = sites_box([-W_WIN, -W_WIN, N_dst - D_WIN], [W_WIN, W_WIN, N_dst])
    found = []
    n_tested = 0
    for M in ops:
        Mp0 = M @ p0
        for q in win:
            t = q - Mp0
            n_tested += 1
            if not in_half(P_src @ M.T + t, N_dst).all():
                continue
            if not in_half((P_dst - t) @ M, N_src).all():
                continue
            found.append((M.copy(), t.copy()))
    classes = {}
    for M, t in found:
        k = (tuple(M.ravel()), net_key(t))
        classes.setdefault(k, []).append((M, t))
    return found, classes, n_tested, p0


def section_C(ops, cos):
    rule("C. EXHAUSTIVE SEARCH: ISOMETRIES (M in m-3m, any translation) MAPPING ONE TRUNCATED HALF "
         "CRYSTAL ONTO ANOTHER")
    print(f"   Test patch |n1|,|n2| <= {L_PATCH}, {D_PATCH} layers deep (a/4 units); candidate "
          f"window |q1|,|q2| <= {W_WIN}, {D_WIN} layers deep.")
    results = {}
    for (Ns, Nd, what) in ((0, 1, "a/4 up-step: lower H_0 -> upper H_1"),
                           (1, 2, "a/4 up-step, other terrace pair: H_1 -> H_2"),
                           (0, 0, "self-symmetry of the lower terrace H_0"),
                           (1, 1, "self-symmetry of H_1"),
                           (0, 2, "a/2 up-step: H_0 -> H_2")):
        found, classes, n_tested, p0 = half_crystal_ops(ops, Ns, Nd)
        results[(Ns, Nd)] = classes
        names = sorted({describe_op(np.array(k[0]).reshape(3, 3)) for k in classes})
        print(f"\n   {what}: {n_tested} (M, t) candidates tested (p0 = {p0.tolist()}); "
              f"{len(found)} succeed, {len(classes)} class(es) modulo the surface net:")
        for k, members in sorted(classes.items(), key=lambda kv: describe_op(
                np.array(kv[0][0]).reshape(3, 3))):
            M = np.array(k[0]).reshape(3, 3)
            t = min((m[1] for m in members), key=lambda v: (abs(v[0]) + abs(v[1]), tuple(v)))
            bulk = maps_diamond(M, t)
            print(f"      {describe_op(M):>10s}  t = (a/4)*{t.tolist()}  = {np.round(t * QA, 6).tolist()} A"
                  f"   t_z = {t[2] * QA:.6f} A   bulk Fd-3m element: {bulk}")
        results[(Ns, Nd, "names")] = names
    # --- checks on the search ----------------------------------------------------------------
    up = results[(0, 1)]
    up_names = sorted(describe_op(np.array(k[0]).reshape(3, 3)) for k in up)
    check("C1 H_0 -> H_1: exactly 4 classes: 4+[0,0,1], 4-[0,0,1], m(1,0,0), m(0,1,0)",
          up_names == sorted(["4+[0,0,1]", "4-[0,0,1]", "m(1,0,0)", "m(0,1,0)"]), str(up_names))
    check("C2 H_0 -> H_1: no pure translation (identity absent)",
          all(describe_op(np.array(k[0]).reshape(3, 3)) != "1" for k in up))
    check("C3 H_0 -> H_1: no diagonal mirror m(1,1,0) or m(1,-1,0) and no 2-fold",
          all(describe_op(np.array(k[0]).reshape(3, 3)) not in ("m(1,1,0)", "m(1,-1,0)", "2[0,0,1]")
              for k in up))
    check("C4 every H_0 -> H_1 operation has t_z = a/4 exactly",
          all(k[1][2] == 1 for k in up))
    check("C5 every H_0 -> H_1 operation is an element of Fd-3m (bulk basis test)",
          all(maps_diamond(np.array(k[0]).reshape(3, 3), v[0][1]) for k, v in up.items()))
    up2 = results[(1, 2)]
    check("C6 H_1 -> H_2 gives the same four point operations",
          sorted(describe_op(np.array(k[0]).reshape(3, 3)) for k in up2) == up_names)
    self0 = sorted(describe_op(np.array(k[0]).reshape(3, 3)) for k in results[(0, 0)])
    check("C7 H_0 self-symmetry point group = {1, 2[001], m(1,1,0), m(1,-1,0)} (2mm, diagonal "
          "mirrors)", self0 == sorted(["1", "2[0,0,1]", "m(1,1,0)", "m(1,-1,0)"]), str(self0))
    half = sorted(describe_op(np.array(k[0]).reshape(3, 3)) for k in results[(0, 2)])
    check("C8 a/2 step H_0 -> H_2 includes the pure lattice translation",
          "1" in half, str(half))
    n_bulk_fix = sum(1 for M in ops if np.array_equal(M @ np.array([0, 0, 1]), [0, 0, 1]))
    n_bulk_not = 48 - n_bulk_fix
    all_up = {describe_op(np.array(k[0]).reshape(3, 3)) for k in up}
    print(f"\n   Bulk versus half crystal: all 48 point operations are Fd-3m elements with a suitable "
          f"translation; {n_bulk_not} of them do not fix [001] and map no half crystal onto another; "
          f"of the 8 that fix [001], only the {len(all_up)} of the non-Td coset reach t_z = a/4.")
    return results


# ================================================================================================
# D. Classification of the H_0 -> H_1 operations
# ================================================================================================
def mirror_normal(M: np.ndarray) -> np.ndarray:
    w, V = np.linalg.eigh(M.astype(float))
    return V[:, np.argmin(w)]


def section_D(results):
    rule("D. CLASSIFICATION OF THE OPERATIONS MAPPING THE LOWER TERRACE H_0 ONTO THE UPPER H_1 "
         "(origin on a top-layer atom of H_0)")
    up = results[(0, 1)]
    info = {}
    for k, members in up.items():
        M = np.array(k[0]).reshape(3, 3)
        name = describe_op(M)
        ts = [m[1] for m in members]
        if name.startswith("4"):
            t = min(ts, key=lambda v: (abs(v[0]) + abs(v[1]), tuple(v)))
            M2 = M[:2, :2].astype(float)
            axis = np.linalg.solve(np.eye(2) - M2, t[:2].astype(float))
            kind = "4_1 screw (rotation +90 deg, +a/4)" if name.startswith("4+") else \
                "4_3 screw (rotation -90 deg, +a/4 == 4_3^3)"
            axes = set()
            for tt in ts:
                ax = np.linalg.solve(np.eye(2) - M2, tt[:2].astype(float)) / 4.0   # units of a
                axes.add((round(ax[0] % 0.5, 6), round(ax[1] % 0.5, 6)))
            print(f"   {name}: {kind}; axis parallel to [001] through (x, y) = "
                  f"{(axis / 4).tolist()} a  (all axis positions modulo a/2: {sorted(axes)}); "
                  f"translation along the axis = a/4 = {t[2] * QA:.6f} A")
            info[name] = dict(kind="screw", t=t)
        else:
            u = mirror_normal(M)
            u = u / np.linalg.norm(u)
            rows = set()
            for tt in ts:
                tf = tt.astype(float)
                d = 0.5 * float(tf @ u)                      # plane u.r = d  (a/4 units)
                g = tf - float(tf @ u) * u                   # glide vector parallel to the plane
                inpl = g.copy()
                inpl[2] = 0.0
                along = float(np.dot(inpl, np.cross([0, 0, 1.0], u)))   # component along the
                rows.add((round((d / 4) % 0.5, 6), round(((along / 4) + 0.5) % 1.0 - 0.5, 6),
                          round(g[2] / 4, 6)))
            line = np.cross([0, 0, 1.0], u)
            print(f"   {name}: glide reflection (no pure mirror exists: every glide vector has an "
                  f"in-plane component). Plane normal {np.round(u, 6).tolist()}, the plane contains "
                  f"[001] and {np.round(line, 6).tolist()}.")
            print("      plane offset u.r (units of a, mod a/2) | in-plane glide component along the "
                  "plane (units of a, mod a) | glide component along [001] (units of a)")
            for d, gpar, gz in sorted(rows):
                print(f"      {d:10.4f} | {gpar:+10.4f} | {gz:+8.4f}")
            info[name] = dict(kind="glide", rows=sorted(rows), normal=u, line=line)
    ok_glide = True
    for nm in ("m(1,0,0)", "m(0,1,0)"):
        rows = info[nm]["rows"]
        ok_glide &= sorted(rows) == sorted([(0.125, 0.25, 0.25), (0.375, -0.25, 0.25)])
    check("D1 both <100> glides: planes at a/8 and 3a/8 (mod a/2) from the atom row, glide "
          "(+-a/4 in plane, a/4 along [001]); no zero in-plane glide", ok_glide)
    check("D2 glide component along the outward normal = a/4 = h (the step height)",
          all(all(abs(r[2] - 0.25) < 1e-12 for r in info[nm]["rows"]) for nm in ("m(1,0,0)",
                                                                                 "m(0,1,0)")))
    return info


# ================================================================================================
# E. Incidence-plane test at the beam azimuth
# ================================================================================================
AZIMUTHS = {"[100]": (1, 0, 0), "[010]": (0, 1, 0), "[-100]": (-1, 0, 0), "[0-10]": (0, -1, 0),
            "[110]": (1, 1, 0), "[1-10]": (1, -1, 0), "[-110]": (-1, 1, 0), "[-1-10]": (-1, -1, 0),
            "[210]": (2, 1, 0), "[310]": (3, 1, 0), "[1-20]": (1, -2, 0)}


def classify_for_azimuth(M: np.ndarray, b: np.ndarray) -> str:
    if np.array_equal(M @ b, b):
        return "fixes k_in, k_out"
    if np.array_equal(M @ b, -b):
        return "reverses azimuth (reciprocity P5 restores k_in, k_out)"
    return "azimuth -> [" + ",".join(str(int(x)) for x in (M.T @ b)) + "]"


def section_E(results):
    rule("E. WHICH H_0 -> H_1 OPERATION PRESERVES THE INCIDENT AND SPECULAR WAVEVECTORS?")
    print("   k_in = k (cos(theta) b_hat - sin(theta) n_hat), k_out = k (cos(theta) b_hat + sin(theta) "
          "n_hat); M fixes both for every theta iff M b = b.")
    up = results[(0, 1)]
    Ms = {describe_op(np.array(k[0]).reshape(3, 3)): np.array(k[0]).reshape(3, 3) for k in up}
    verdict = {}
    for az, b in AZIMUTHS.items():
        b = np.array(b)
        cols = {nm: classify_for_azimuth(M, b) for nm, M in sorted(Ms.items())}
        direct = [nm for nm, c in cols.items() if c.startswith("fixes")]
        recip = [nm for nm, c in cols.items() if c.startswith("reverses")]
        verdict[az] = (direct, recip)
        print(f"   azimuth {az:>8s}: direct {direct if direct else 'none'};  via reciprocity "
              f"{recip if recip else 'none'};  "
              + "; ".join(f"{nm}: {c}" for nm, c in cols.items() if not (c.startswith("fixes")
                                                                        or c.startswith("reverses"))))
    check("E1 at [100] the (010) glide fixes k_in and k_out (plane contains beam and normal)",
          verdict["[100]"][0] == ["m(0,1,0)"])
    check("E2 at [010] the (100) glide fixes k_in and k_out", verdict["[010]"][0] == ["m(1,0,0)"])
    check("E3 at every <110> azimuth no H_0 -> H_1 operation preserves k_in, k_out (direct or via "
          "reciprocity)", all(verdict[az] == ([], []) for az in ("[110]", "[1-10]", "[-110]",
                                                                "[-1-10]")))
    check("E4 at generic azimuths [210], [310], [1-20] none either",
          all(verdict[az] == ([], []) for az in ("[210]", "[310]", "[1-20]")))
    # explicit wavevectors at the (008) condition, 200 keV, V0 = 12 V (ASSUMPTION B1)
    sc = calc.SpecularCondition(A / 4.0, 2, 200.0, 12.0)
    th, k = sc.theta_ext, sc.k
    t = np.array([1, 1, 1]) * QA
    for az, nm in (("[100]", "m(0,1,0)"), ("[110]", "m(0,1,0)")):
        b = np.array(AZIMUTHS[az], float)
        b /= np.linalg.norm(b)
        n = np.array([0.0, 0.0, 1.0])
        kin = k * (np.cos(th) * b - np.sin(th) * n)
        kout = k * (np.cos(th) * b + np.sin(th) * n)
        M = Ms[nm].astype(float)
        dev = max(np.linalg.norm(M.T @ kin - kin), np.linalg.norm(M.T @ kout - kout))
        print(f"   (008), theta_ext = {th * 1e3:.4f} mrad, azimuth {az}, {nm}: "
              f"max |M^T k - k| = {dev:.3e} rad/A;  (k_out - k_in).t = {float((kout - kin) @ t):.9f} rad")
        if az == "[100]":
            check("E5 (008) at [100]: M^T k_in = k_in and M^T k_out = k_out to 1e-12 rad/A", dev < 1e-12)
            check_close("E6 (k_out - k_in).t = 2 k sin(theta_ext) a/4 (only t_z enters)",
                        float((kout - kin) @ t), 2 * k * np.sin(th) * QA, 1e-10, "rad")
        else:
            check("E7 (008) at [110]: the (010) glide moves k_in by more than 1 rad/A (not preserved)",
                  dev > 1.0, f"{dev:.3f} rad/A")
    return verdict


# ================================================================================================
# F. Azimuth orbits: misalignment
# ================================================================================================
def ang_of(M: np.ndarray, phi_deg: float) -> float:
    b = np.array([np.cos(np.radians(phi_deg)), np.sin(np.radians(phi_deg)), 0.0])
    v = M.astype(float).T @ b
    return float(np.degrees(np.arctan2(v[1], v[0])) % 360.0)


def section_F(results):
    rule("F. AZIMUTH ORBITS: WHICH LOWER-TERRACE AZIMUTH DOES THE UPPER TERRACE REPRODUCE?")
    self_ops = [np.array(k[0]).reshape(3, 3) for k in results[(0, 0)]]
    up_ops = {describe_op(np.array(k[0]).reshape(3, 3)): np.array(k[0]).reshape(3, 3)
              for k in results[(0, 1)]}

    def orbit(phi):
        s = set()
        for M in self_ops:
            a_ = ang_of(M, phi)
            s.add(round(a_ % 360.0, 9))
            s.add(round((a_ + 180.0) % 360.0, 9))          # reciprocity (P5)
        return s

    ok_all = True
    for phi in (0.0, 0.5, 2.0, 45.0, 90.0, 20.0):
        o = orbit(phi)
        targets = {nm: round(ang_of(M, phi), 9) for nm, M in up_ops.items()}
        same_as_minus = all(any(abs(((tv - x + 180) % 360) - 180) < 1e-7 for x in orbit(-phi))
                            for tv in targets.values())
        rel_plus = any(abs(((targets["m(0,1,0)"] - x + 180) % 360) - 180) < 1e-7 for x in o)
        print(f"   phi = {phi:6.2f} deg: lower-terrace orbit (own symmetries + reciprocity) "
              f"{sorted(o)};  M^T b for the four H_0->H_1 operations {sorted(targets.values())};  "
              f"all equivalent to lower terrace at -phi: {same_as_minus};  equivalent to lower "
              f"terrace at +phi: {rel_plus}")
        ok_all &= same_as_minus
        if phi in (0.0, 90.0):
            ok_all &= rel_plus
        if phi in (0.5, 2.0, 45.0, 20.0):
            ok_all &= not rel_plus
    check("F1 A_upper(phi) = exp(-i q.t) A_lower(-phi) for all four operations; A_lower(-phi) is "
          "symmetry-equivalent to A_lower(phi) only at phi = 0, 90 deg (<100>)", ok_all)


# ================================================================================================
# G. Cross-check with the package's builder and relation finder
# ================================================================================================
def section_G(results):
    rule("G. CROSS-CHECK: reflection_holo.structure.build_si001_terraces (relations measured on the "
         "built atoms, 8 operations x a/8 grid)")
    from reflection_holo.structure import si001 as S
    names_pkg = {"Rz(+90)": "4+[0,0,1]", "Rz(-90)": "4-[0,0,1]", "mirror(100)": "m(1,0,0)",
                 "mirror(010)": "m(0,1,0)", "mirror(110)": "m(1,1,0)", "mirror(1-10)": "m(1,-1,0)",
                 "identity": "1", "Rz(180)": "2[0,0,1]"}
    mine = sorted(describe_op(np.array(k[0]).reshape(3, 3)) for k in results[(0, 1)])
    ok = True
    for az, lab in (((1, 0, 0), "[100]"), ((1, 1, 0), "[110]"), ((0, 1, 0), "[010]")):
        for bb in ((1, -1, 0), (1, 1, 0)):
            st = S.Staircase(edges="parallel", terrace_layers=(0, 1), terrace_widths=(2, 2),
                             boundary_step_layers=-1)
            s = S.build_si001_terraces(azimuth_uvw=az, azimuth_label="TEST_ONLY C2 symmetry check",
                                       staircase=st, edge_periods=2, substrate_layers=4,
                                       first_terrace_backbond_uvw=bb, termination="bulk",
                                       overlayer=None, vacuum_above_A=8.0)
            st0 = s.metadata["steps"][0]
            rel = st0["relation"]
            found = sorted(names_pkg[n] for n in rel["operations_found"])
            inc = rel["incidence_plane_mirror_operations"]
            print(f"   azimuth {lab}, terrace-0 back-bond {list(bb)}: step type {st0['type']}; "
                  f"operations found {found}; incidence-plane mirrors {inc}")
            ok &= found == mine
            want_inc = {"[100]": ["mirror(010)"], "[010]": ["mirror(100)"], "[110]": []}[lab]
            ok &= inc == want_inc
    check("G1 package relation finder: same four operations as the exhaustive search, and the "
          "incidence-plane glide exactly at [100] ((010)) and [010] ((100)), none at [110]", ok)


# ================================================================================================
# H. Multiple-scattering toy (Foldy-Lax point scatterers): covariance, reciprocity, consequences
# ================================================================================================
K_TOY = 3.0                 # rad/A   TEST_ONLY toy wavenumber (not the 200 keV value)
TH_TOY = 0.40               # rad     TEST_ONLY toy glancing angle
F0_TOY = 0.40 + 0.15j       # A       TEST_ONLY s-wave scattering amplitude of each atom
R_TOY = 13.0                # A       radius of the hemispherical cluster


def foldy_lax(pos: np.ndarray, kin: np.ndarray, kouts: list[np.ndarray], born: bool = False):
    """Far-field amplitudes f(k_out) = f0 sum_j exp(-i k_out.r_j) psi_j of point scatterers.

    psi_j = exp(i k_in.r_j) + sum_{l != j} f0 exp(i k |r_j - r_l|)/|r_j - r_l| psi_l  (exp(+ik.r)).
    """
    k = np.linalg.norm(kin)
    inc = np.exp(1j * pos @ kin)
    if born:
        psi = inc
    else:
        d = np.linalg.norm(pos[:, None, :] - pos[None, :, :], axis=-1)
        np.fill_diagonal(d, 1.0)
        G = np.exp(1j * k * d) / d
        np.fill_diagonal(G, 0.0)
        psi = np.linalg.solve(np.eye(len(pos)) - F0_TOY * G, inc)
    return [complex(F0_TOY * np.sum(np.exp(-1j * pos @ ko) * psi)) for ko in kouts]


def spec_pair(phi_deg: float, k: float = K_TOY, th: float = TH_TOY):
    b = np.array([np.cos(np.radians(phi_deg)), np.sin(np.radians(phi_deg)), 0.0])
    n = np.array([0.0, 0.0, 1.0])
    return k * (np.cos(th) * b - np.sin(th) * n), k * (np.cos(th) * b + np.sin(th) * n)


def section_H(results):
    rule("H. MULTIPLE-SCATTERING TOY (Foldy-Lax point scatterers; k, theta, f0 TEST_ONLY): covariance, "
         "reciprocity, [100] equality, [110] residual, misalignment")
    print(f"   toy: k = {K_TOY} rad/A, theta = {TH_TOY} rad, f0 = {F0_TOY} A per atom; cluster = atoms "
          f"of H_0 within {R_TOY} A of the top-layer atom at the origin (hemisphere)")
    P = sites_box([-16, -16, -16], [16, 16, 0])
    pos_l = P.astype(float) * QA
    pos_l = pos_l[np.linalg.norm(pos_l, axis=1) <= R_TOY]
    up = {describe_op(np.array(k[0]).reshape(3, 3)): np.array(k[0]).reshape(3, 3)
          for k in results[(0, 1)]}
    t = np.array([1.0, 1.0, 1.0]) * QA                      # common translation part (a/4)(1,1,1)
    imgs = {nm: pos_l @ M.T.astype(float) + t for nm, M in up.items()}
    key = lambda X: {tuple(np.round(r, 6)) for r in X}      # noqa: E731
    same = all(key(imgs[nm]) == key(imgs["4+[0,0,1]"]) for nm in imgs)
    print(f"   cluster atoms: {len(pos_l)}; the images of the cluster under the four H_0 -> H_1 "
          f"operations (all with t = (a/4)(1,1,1)) coincide: {same}")
    check("H0 the hemisphere is invariant under H_0's own 2mm symmetries, so its screw and glide "
          "images coincide", same)
    pos_u = imgs["4+[0,0,1]"]
    M4 = up["4+[0,0,1]"].astype(float)
    rng = np.random.default_rng(20260922)
    worst_cov, worst_rec = 0.0, 0.0
    for _ in range(3):
        k1 = rng.normal(size=3)
        k1 *= K_TOY / np.linalg.norm(k1)
        k2 = rng.normal(size=3)
        k2 *= K_TOY / np.linalg.norm(k2)
        fu = foldy_lax(pos_u, k1, [k2])[0]
        fl = foldy_lax(pos_l, M4.T @ k1, [M4.T @ k2])[0]
        worst_cov = max(worst_cov, abs(fu - np.exp(-1j * (k2 - k1) @ t) * fl) / abs(fu))
        fa = foldy_lax(pos_l, k1, [k2])[0]
        fb = foldy_lax(pos_l, -k2, [-k1])[0]
        worst_rec = max(worst_rec, abs(fa - fb) / abs(fa))
    print(f"   covariance f_upper(k1->k2) = exp(-i (k2-k1).t) f_lower(M^T k1 -> M^T k2), random "
          f"directions, 4_1 screw: max relative residual {worst_cov:.2e}")
    print(f"   reciprocity f(k1->k2) = f(-k2 -> -k1), random directions: max relative residual "
          f"{worst_rec:.2e}")
    check("H1 covariance with the sign exp(-i (k_out - k_in).t) holds to 1e-9", worst_cov < 1e-9)
    check("H2 reciprocity of the toy (symmetric Green's function) holds to 1e-9", worst_rec < 1e-9)

    def ratio(phi, born=False):
        kin, kout = spec_pair(phi)
        fu = foldy_lax(pos_u, kin, [kout], born)[0]
        fl = foldy_lax(pos_l, kin, [kout], born)[0]
        return fu / (np.exp(-1j * (kout - kin) @ t) * fl), fl

    r0, fl0 = ratio(0.0)
    rb0, flb0 = ratio(0.0, born=True)
    ms = abs(fl0 - flb0) / abs(flb0)
    print(f"   multiple scattering is not a small correction in the toy: |f - f_Born| / |f_Born| = "
          f"{ms:.3f} at [100]")
    check("H3 toy is strongly multiple-scattering (|f - f_Born|/|f_Born| > 0.1)", ms > 0.1)
    print(f"   [100] exact:  f_up / (exp(-i q.t) f_low) = {r0.real:+.12f} {r0.imag:+.12f} i")
    check("H4 [100]: f_upper = exp(-i q.t) f_lower (ratio 1 to 1e-9)", abs(r0 - 1) < 1e-9)
    r45, _ = ratio(45.0)
    rb45, _ = ratio(45.0, born=True)
    print(f"   [110] exact:  f_up / (exp(-i q.t) f_low) = |{abs(r45):.6f}| exp(i {np.angle(r45):+.6f})"
          f"   (Born: |{abs(rb45):.12f}| exp(i {np.angle(rb45):+.3e}))")
    check("H5 [110]: residual nonzero with multiple scattering (|ratio - 1| > 1e-3)",
          abs(r45 - 1) > 1e-3, f"{abs(r45 - 1):.4f}")
    check("H6 [110]: residual zero in the Born (kinematic) limit (ratio 1 to 1e-12)",
          abs(rb45 - 1) < 1e-12)
    kin45, kout45 = spec_pair(45.0)
    fu45 = foldy_lax(pos_u, kin45, [kout45])[0]
    kinm, koutm = spec_pair(-45.0)
    flm45 = foldy_lax(pos_l, kinm, [koutm])[0]
    rel = abs(fu45 - np.exp(-1j * (kout45 - kin45) @ t) * flm45) / abs(fu45)
    check("H7 [110]: f_upper(45 deg) = exp(-i q.t) f_lower(-45 deg) (the [1-10] azimuth), to 1e-9",
          rel < 1e-9, f"{rel:.1e}")
    print("   misalignment eps from [100] (delta(eps) = arg of the ratio):")
    d = {}
    for e in (-0.3, -0.1, 0.1, 0.3):
        r, _ = ratio(e)
        d[e] = float(np.angle(r))
        print(f"      eps = {e:+.2f} deg: |ratio| = {abs(r):.9f}, delta = {d[e]:+.6e} rad")
    check("H8 delta(eps) is odd: delta(-eps) = -delta(eps) to 1e-9",
          abs(d[0.1] + d[-0.1]) < 1e-9 and abs(d[0.3] + d[-0.3]) < 1e-9)
    check("H9 delta(eps) is first order: delta(0.3 deg)/delta(0.1 deg) = 3 within 5 %",
          abs(d[0.3] / d[0.1] - 3.0) < 0.15, f"{d[0.3] / d[0.1]:.4f}")


# ================================================================================================
# I. Reconstruction symmetry toy (displacement magnitudes TEST_ONLY; no sourced dimer geometry)
# ================================================================================================
TOY_RECON = {
    # name: (lateral pairing along [110], common z, buckling +-z, twist along [1-10])   (A)
    "symmetric dimers": (0.70, -0.10, 0.00, 0.00),
    "buckled dimers p(2x1)": (0.70, -0.10, 0.35, 0.00),
    "twisted dimers (no diagonal mirror; toy only)": (0.70, -0.10, 0.00, 0.20),
}


def recon_positions(P: np.ndarray, pars) -> np.ndarray:
    """Top layer (n3 = 0) of an H_0 patch dimerised along [110]: net coordinate m1 = (n1+n2)/4;
    atoms with m1 even pair with m1 + 1."""
    lat, dz, buck, tw = pars
    r = P.astype(float) * QA
    top = P[:, 2] == 0
    m1 = (P[:, 0] + P[:, 1]) // 4
    s = np.where(m1 % 2 == 0, 1.0, -1.0)
    e110 = np.array([1.0, 1.0, 0.0]) / np.sqrt(2.0)
    e1m10 = np.array([1.0, -1.0, 0.0]) / np.sqrt(2.0)
    disp = (s[:, None] * lat * e110 + s[:, None] * tw * e1m10
            + np.array([0.0, 0.0, dz]) + (s * buck)[:, None] * np.array([0.0, 0.0, 1.0]))
    r[top] += disp[top]
    return r


def find_op(X: np.ndarray, Y: np.ndarray, M: np.ndarray, r_int: float, tol: float = 1e-6) -> bool:
    """Is there a translation t with (M, t)(X) = Y on the interior (both directions)?"""
    Mf = M.astype(float)
    cx = X[np.argmin(np.linalg.norm(X - np.array([0.0, 0.0, X[:, 2].max()]), axis=1))]
    ztop_y = Y[:, 2].max()
    cand = Y[(np.linalg.norm(Y[:, :2], axis=1) < 2.2 * A) & (Y[:, 2] > ztop_y - 1.5)]
    Xi = X[np.linalg.norm(X[:, :2], axis=1) < r_int]
    for q in cand:
        t = q - Mf @ cx
        img = Xi @ Mf.T + t
        dmin = np.min(np.linalg.norm(img[:, None, :] - Y[None, :, :], axis=-1), axis=1)
        if np.max(dmin) > tol:
            continue
        Yi = Y[np.linalg.norm(Y[:, :2] - t[:2], axis=1) < r_int]
        pre = (Yi - t) @ Mf
        dmin2 = np.min(np.linalg.norm(pre[:, None, :] - X[None, :, :], axis=-1), axis=1)
        if np.max(dmin2) <= tol:
            return True
    return False


def section_I(results):
    rule("I. RECONSTRUCTION SYMMETRY TOY: does a dimerised terrace pair keep a [100]-compatible "
         "operation? (displacements TEST_ONLY, symmetry only)")
    P = sites_box([-24, -24, -8], [24, 24, 0])
    up = {describe_op(np.array(k[0]).reshape(3, 3)): np.array(k[0]).reshape(3, 3)
          for k in results[(0, 1)]}
    t = np.array([1.0, 1.0, 1.0]) * QA
    Mdict = {"1": np.eye(3, dtype=int), "m(0,1,0)": np.diag([1, -1, 1]),
             "m(1,0,0)": np.diag([-1, 1, 1]), "2[0,0,1]": np.diag([-1, -1, 1]),
             "m(1,-1,0)": np.array([[0, 1, 0], [1, 0, 0], [0, 0, 1]]),
             "m(1,1,0)": np.array([[0, -1, 0], [-1, 0, 0], [0, 0, 1]])}
    set100 = ("1", "m(0,1,0)", "m(1,0,0)", "2[0,0,1]")          # direct: 1, m(010); reciprocity: others
    set110 = ("1", "m(1,-1,0)", "m(1,1,0)", "2[0,0,1]")
    outcome = {}
    for name, pars in TOY_RECON.items():
        X = recon_positions(P, pars)
        print(f"\n   {name}: displacements (pairing, z, buckling, twist) = {pars} A")
        for vn, Mv in sorted(up.items()):
            Y = X @ Mv.T.astype(float) + t                 # upper-terrace variant = S(lower)
            ok100 = [m for m in set100 if find_op(X, Y, Mdict[m], 10.0)]
            ok110 = [m for m in set110 if find_op(X, Y, Mdict[m], 10.0)]
            outcome[(name, vn)] = (ok100, ok110)
            print(f"      upper = {vn:>10s} image of lower: [100]-compatible operations found "
                  f"{ok100 if ok100 else 'NONE'};  [110]-compatible {ok110 if ok110 else 'NONE'}")
    sym = all(outcome[("symmetric dimers", v)][0] == ["m(0,1,0)", "m(1,0,0)"] for v in up)
    buck = all(len(outcome[("buckled dimers p(2x1)", v)][0]) == 1 for v in up)
    twist_break = any(outcome[("twisted dimers (no diagonal mirror; toy only)", v)][0] == []
                      for v in up)
    none110 = all(v[1] == [] for v in outcome.values())
    check("I1 symmetric-dimer toy: both <100> glides survive for every upper-terrace variant", sym)
    check("I2 buckled p(2x1) toy: exactly one <100> glide survives per variant (the (100) one needs "
          "reciprocity at [100])", buck)
    check("I3 twisted-dimer toy (both diagonal mirrors removed): some variant has NO [100]-"
          "compatible operation, i.e. a reconstruction can break the relation", twist_break)
    check("I4 no [110]-compatible operation for any toy or variant", none110)


# ================================================================================================
# J. Geometric step phases of the a/4 step (200 keV, V0 = 12 V ASSUMPTION B1)
# ================================================================================================
def section_J():
    rule("J. GEOMETRIC PHASE OF THE a/4 STEP AT THE Si(001) SPECULAR (00L) CONDITIONS, 200 keV, "
         "V0 = 12 V (ASSUMPTION B1)")
    E, V0 = 200.0, 12.0
    lam = float(calc.wavelength_A(E))
    k = 2 * np.pi / lam
    T = E * 1e3
    delta = V0 * (1 + T / calc.M_E_C2_EV) / (T * (1 + T / (2 * calc.M_E_C2_EV)))
    print(f"   lambda = {lam:.8f} A, k = {k:.4f} rad/A, Delta = {delta:.4e} "
          "(physics_conventions refraction formula)")
    print(f"   {'(00L)':>9} {'th_ext mrad':>12} {'dphi = -2 K_ext a/4':>20} {'wrapped':>9} "
          f"{'h_2pi (A)':>10} {'dh per 0.1 rad of residual (A)':>31}")
    worst = 0.0
    rows = {}
    for L in (4, 8, 12, 16):
        sc = calc.SpecularCondition(A / 4.0, L // 4, E, V0)
        K_ext_indep = np.sqrt((np.pi * L / A) ** 2 - k ** 2 * delta)
        worst = max(worst, abs(K_ext_indep - sc.K_ext) / sc.K_ext)
        dphi = -2.0 * sc.K_ext * QA
        wr = float(calc.wrap_to_pi(dphi))
        dh = 0.1 / (2.0 * sc.K_ext)
        rows[L] = (sc.theta_ext * 1e3, dphi, wr, sc.h_2pi_A, dh)
        print(f"   {str((0, 0, L)):>9} {sc.theta_ext * 1e3:12.4f} {dphi:20.4f} {wr:9.4f} "
              f"{sc.h_2pi_A:10.4f} {dh:31.4f}")
    check("J1 K_ext from the conventions formula equals the calculator's to 1e-9 (relative)",
          worst < 1e-9, f"{worst:.1e}")
    check_close("J2 (008) wrapped a/4 step phase equals the calculator section 4b value 1.3593",
                rows[8][2], 1.3593, 5e-5, "rad")
    return rows


def main() -> int:
    section_A()
    ops, cos = section_B()
    results = section_C(ops, cos)
    section_D(results)
    section_E(results)
    section_F(results)
    section_G(results)
    section_H(results)
    section_I(results)
    section_J()
    rule("SUMMARY")
    n_ok = sum(ok for _, ok in CHECKS)
    print(f"   {n_ok}/{len(CHECKS)} self-checks pass")
    for name, ok in CHECKS:
        if not ok:
            print(f"   FAILED: {name}")
    return 0 if n_ok == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
