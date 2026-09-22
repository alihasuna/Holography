"""Si(001) terrace builder (spec docs/05 section 4.2; configuration CFG-B ``si001_patterned``).

Terraces are truncations of ONE continuous diamond lattice (the conventional cell of
``reflection_holo.constants.DIAMOND_BASIS`` repeated over a supercell) expressed in the slab frame of
``surface_frame((0, 0, 1), azimuth)``: x = outward normal [001], z = beam azimuth, y = z x x
(docs/physics_conventions.md). The (001) atomic layers are at x = l a/4 (l integer, the "a/4 layer
grid"); a terrace is the set of lattice sites with 0 <= l <= l_top inside its strip of the periodic
cell. Step edges run parallel or transverse to the beam, as the caller specifies.

Physics of the steps (docs/03 section 2; calculator section 2b and ``screw_search``; DERIVED_HERE):

* an a/2 (double-layer) step joins terraces related by a pure lattice translation with
  ``t . n_hat = a/2``: model_assumptions B4 applies far from the riser;
* an a/4 (single-layer) step joins terraces related by the diamond 4_1 screw: a 90 degree rotation
  about [001] plus a translation with ``t . n_hat = a/4``; the top-layer back-bond axis (and the
  dimer-row direction, were a reconstruction enabled) rotates by 90 degrees; B4 does NOT apply.

Both relations are verified numerically on the built atoms by :func:`find_terrace_relations`, which
generalises the calculator's ``screw_search`` (90 degree rotations times translations on an a/8
grid, tested modulo the lattice) from the 8-atom basis to the atoms of two built terraces.

Options, each recorded with its label in ``metadata["options"]``: bulk termination (ASSUMPTION B3,
the only implemented termination); 2x1 dimer reconstruction (NOT IMPLEMENTED: no geometry source
read); amorphous SiO2/damage overlayer (thickness and density are PROJECT_INPUT item 12, required;
declared region only, atomistic content NOT IMPLEMENTED); step-riser relaxation none (ASSUMPTION).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np

import reflection_holo
from reflection_holo.constants import A_SI_A, DIAMOND_BASIS
from reflection_holo.geometry.frames import SurfaceFrame, surface_frame

from . import checks
from .checks import POSITION_TOL_A, WINDOW_TOL_A, StructureAssertionError
from .lattice import diamond_sites_quarter, is_fcc_translation, nearest_neighbour_distance_A

NORMAL_HKL = (0, 0, 1)
LABEL_PREFIXES = ("PROJECT_INPUT", "TEST_ONLY", "ASSUMPTION")

# PROJECT_INPUT item 8: for Si(001) the beam azimuth is a <110> or a <100> direction in the surface.
_AZIMUTHS = {
    "<110>": {(1, 1, 0), (1, -1, 0), (-1, 1, 0), (-1, -1, 0)},
    "<100>": {(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)},
}
_ALLOWED_STEP_LAYERS = (1, 2)          # a/4 (screw) and a/2 (translation)
_MIN_SUBSTRATE_LAYERS = 4              # the relation check compares the top 4 layers (one period)


class StaircaseError(ValueError):
    """A requested terrace staircase is refused (spec 4.2 assertions (d) and (e))."""


def _check_label(label, what: str) -> str:
    if not isinstance(label, str) or not label.strip():
        raise ValueError(f"{what}: an evidence label string is required")
    if not label.startswith(LABEL_PREFIXES):
        raise ValueError(f"{what}: label {label!r} must start with one of {LABEL_PREFIXES}")
    return label


def _axis_key(uvw) -> tuple[int, int, int]:
    """Sign-free key of an in-plane <110> bond axis: (1,1,0) or (1,-1,0)."""
    v = tuple(int(x) for x in uvw)
    if v in ((1, 1, 0), (-1, -1, 0)):
        return (1, 1, 0)
    if v in ((1, -1, 0), (-1, 1, 0)):
        return (1, -1, 0)
    raise ValueError(f"back-bond axis {tuple(uvw)} is not [1,1,0] or [1,-1,0] (up to sign)")


def backbond_axis_of_crystal_layer(n3: int) -> tuple[int, int, int]:
    """Projection axis of the bonds from crystal layer n3 (z = n3 a/4) to layer n3 - 1.

    DERIVED_HERE from DIAMOND_BASIS: even n3 (fcc sublattice) -> [1,-1,0]; odd n3 -> [1,1,0].
    """
    return (1, -1, 0) if int(n3) % 2 == 0 else (1, 1, 0)


# --------------------------------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class Staircase:
    """A periodic terrace staircase on the a/4 layer grid.

    edges:                "parallel" or "transverse" (step edges relative to the beam azimuth)
    terrace_layers:       top-layer height of each terrace in a/4 layers, in order along +s, where s
                          is y (edges parallel to the beam) or z (edges transverse to the beam)
    terrace_widths:       width of each terrace in in-plane lattice periods along s
                          (a/sqrt(2) for a <110> azimuth, a for a <100> azimuth)
    boundary_step_layers: the step DECLARED at the periodic cell edge, from the last terrace back to
                          the first. It must equal terrace_layers[0] - terrace_layers[-1]; a mismatch
                          is a net height change across the period and is refused (assertion (e)).
    """
    edges: str
    terrace_layers: tuple[int, ...]
    terrace_widths: tuple[int, ...]
    boundary_step_layers: int


@dataclass(frozen=True)
class OverlayerSpec:
    """Amorphous SiO2 / damage overlayer (PROJECT_INPUT item 12; ASSUMPTION B7 is its absence).

    All fields are required. Only the declared geometry is implemented (a conformal region of the
    given thickness above each terrace); the atomistic random-network content is NOT IMPLEMENTED.
    """
    material: str
    thickness_A: float
    density_g_cm3: float
    label: str


@dataclass
class Si001Structure:
    positions_A: np.ndarray          # (N, 3) slab frame, angstrom
    species: np.ndarray              # (N,) element symbols
    cell_A: np.ndarray               # (3, 3) rows = cell vectors in the slab frame
    pbc: tuple[bool, bool, bool]     # (x, y, z); x (normal) is not periodic
    frame: SurfaceFrame
    layer_index: np.ndarray          # (N,) a/4 layer index l, x = l a/4
    terrace_index: np.ndarray        # (N,) terrace of the strip containing the atom
    crystal_origin_slab_A: np.ndarray  # slab position of the crystal origin (one lattice)
    metadata: dict

    @property
    def n_atoms(self) -> int:
        return int(self.positions_A.shape[0])

    @property
    def periodic_lengths_A(self):
        return [None if not p else float(self.cell_A[k, k]) for k, p in enumerate(self.pbc)]


# --------------------------------------------------------------------------------------------------
# Assertions (d) and (e): the staircase request
# --------------------------------------------------------------------------------------------------
def validate_staircase(st: Staircase, a_A: float = A_SI_A) -> list[dict]:
    """Refuse staircases that are not continuous under the periodic boundary or whose steps are not
    a/4 or a/2; return the step list (including a non-zero step at the periodic cell edge)."""
    if st.edges not in ("parallel", "transverse"):
        raise ValueError(f"edges must be 'parallel' or 'transverse' to the beam, got {st.edges!r}")
    t = [int(v) for v in st.terrace_layers]
    w = [int(v) for v in st.terrace_widths]
    if len(t) == 0 or len(t) != len(w):
        raise ValueError("terrace_layers and terrace_widths must be non-empty and of equal length")
    if any(v != u for v, u in zip(t, st.terrace_layers)) or any(v != u for v, u in
                                                               zip(w, st.terrace_widths)):
        raise ValueError("terrace heights (a/4 layers) and widths (periods) must be integers")
    if any(v < 1 for v in w):
        raise ValueError("terrace widths must be at least one in-plane period")
    b = int(st.boundary_step_layers)
    q = a_A / 4.0
    n = len(t)
    steps = []
    for k in range(n - 1):
        d = t[k + 1] - t[k]
        if d == 0:
            raise StaircaseError(f"terraces {k} and {k + 1} have the same height ({t[k]} layers): "
                                 f"there is no step between them; merge them into one terrace")
        if abs(d) not in _ALLOWED_STEP_LAYERS:
            raise StaircaseError(
                f"(d) step between terraces {k} and {k + 1} is {d:+d} layers = {d * q:+.4f} A: "
                f"only a/4 (1 layer, screw) and a/2 (2 layers, translation) steps are built")
        steps.append(dict(index=k, from_terrace=k, to_terrace=k + 1, delta_layers=d,
                          at_periodic_boundary=False))
    closing = t[0] - t[-1]
    net = (t[-1] - t[0]) + b
    if net != 0:
        kind = "down" if closing < 0 else "up"
        raise StaircaseError(
            f"(e) the staircase has a net height change of {net:+d} layers ({net * q:+.4f} A) "
            f"across the period: the declared boundary step is {b:+d} layers, but under the "
            f"periodic boundary perpendicular to the beam the terrace sequence {t} closes only "
            f"through a hidden {abs(closing)}-layer {kind}-step ({closing:+d} layers) at the cell "
            f"edge. A continuous staircase with a net height change needs a vicinal cell whose "
            f"periodic vector carries the height change; that cell is NOT IMPLEMENTED, so the "
            f"request is refused.")
    if closing != 0:
        if abs(closing) not in _ALLOWED_STEP_LAYERS:
            kind = "down" if closing < 0 else "up"
            raise StaircaseError(
                f"(e) the step at the periodic cell edge (last terrace -> first) is {closing:+d} "
                f"layers = {closing * q:+.4f} A, a hidden {abs(closing)}-layer {kind}-step: only "
                f"a/4 and a/2 steps are built. A staircase with a net height change needs a "
                f"vicinal cell (NOT IMPLEMENTED); request refused.")
        steps.append(dict(index=n - 1, from_terrace=n - 1, to_terrace=0, delta_layers=closing,
                          at_periodic_boundary=True))
    return steps


def assert_step_heights(measured_tops_A, st: Staircase, steps: list[dict],
                        a_A: float = A_SI_A, tol_A: float = POSITION_TOL_A) -> None:
    """(d)/(e) on the built atoms: every measured step (including the one at the periodic cell edge)
    equals the requested a/4 or a/2 height, and the measured closing step equals the declared one."""
    h = np.asarray(measured_tops_A, float)
    q = a_A / 4.0
    for s in steps:
        dh = h[s["to_terrace"]] - h[s["from_terrace"]]
        want = s["delta_layers"] * q
        if abs(dh - want) > tol_A or abs(abs(dh) - q * abs(s["delta_layers"])) > tol_A:
            raise StructureAssertionError(
                f"(d) measured step {s['index']} is {dh:+.9f} A, requested {want:+.9f} A")
        if round(abs(dh) / q) not in _ALLOWED_STEP_LAYERS:
            raise StructureAssertionError(f"(d) measured step {s['index']} is not a/4 or a/2")
    closing = h[0] - h[-1]
    if abs(closing - st.boundary_step_layers * q) > tol_A:
        raise StructureAssertionError(
            f"(e) measured step at the periodic cell edge {closing:+.9f} A != declared "
            f"{st.boundary_step_layers * q:+.9f} A")


# --------------------------------------------------------------------------------------------------
# Assertion (f): terrace relations measured on the built atoms
# --------------------------------------------------------------------------------------------------
_OPS = {
    "identity": np.eye(3),
    "Rz(+90)": np.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]),
    "Rz(180)": np.diag([-1.0, -1.0, 1.0]),
    "Rz(-90)": np.array([[0.0, 1.0, 0.0], [-1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]),
    "mirror(100)": np.diag([-1.0, 1.0, 1.0]),
    "mirror(010)": np.diag([1.0, -1.0, 1.0]),
    "mirror(110)": np.array([[0.0, -1.0, 0.0], [-1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]),
    "mirror(1-10)": np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]]),
}
_MIRROR_NORMALS = {"mirror(100)": (1, 0, 0), "mirror(010)": (0, 1, 0),
                   "mirror(110)": (1, 1, 0), "mirror(1-10)": (1, -1, 0)}
_SCREW_OPS = ("Rz(+90)", "Rz(-90)")


def is_diamond_symmetry(M: np.ndarray, t_crystal_A: np.ndarray, a_A: float = A_SI_A,
                        tol_A: float = POSITION_TOL_A) -> bool:
    """True if r -> M r + t maps the diamond lattice onto itself.

    The test of the calculator's ``screw_search``: the image of the 8-atom basis must coincide with
    the basis modulo the cubic cell.
    """
    img = DIAMOND_BASIS @ np.asarray(M, float).T + np.asarray(t_crystal_A, float) / a_A
    diff = img[:, None, :] - DIAMOND_BASIS[None, :, :]
    diff -= np.rint(diff)
    return bool(np.all(np.min(np.linalg.norm(diff, axis=-1), axis=1) * a_A <= tol_A))


def _net(a_A: float):
    """(001) surface net of the unreconstructed bulk: n1 = (a/2)[1,1,0], n2 = (a/2)[1,-1,0]."""
    N = 0.5 * a_A * np.array([[1.0, 1.0], [1.0, -1.0]])    # columns n1, n2 (crystal x, y)
    return N, np.linalg.inv(N)


def _layer_offsets(rc: np.ndarray, depth: np.ndarray, a_A: float, tol_A: float, who: str):
    """Per-depth (net offset mod 1, z) of a terrace; every layer must be a single net coset."""
    N, Ninv = _net(a_A)
    out = {}
    for d in np.unique(depth):
        sel = depth == d
        f = rc[sel, :2] @ Ninv.T
        diff = f - f[0]
        diff -= np.rint(diff)
        if np.max(np.linalg.norm(diff @ N.T, axis=1)) > tol_A:
            raise StructureAssertionError(f"(f) {who}: layer at depth {int(d)} is not one net coset")
        z = rc[sel, 2]
        if np.max(np.abs(z - z[0])) > tol_A:
            raise StructureAssertionError(f"(f) {who}: layer at depth {int(d)} is not planar")
        out[int(d)] = (f[0] % 1.0, float(z[0]))
    return out


def find_terrace_relations(rc_A: np.ndarray, depth_A: np.ndarray, rc_B: np.ndarray,
                           depth_B: np.ndarray, a_A: float = A_SI_A, grid: int = 8,
                           tol_A: float = POSITION_TOL_A) -> list[dict]:
    """Operations S(r) = M r + t mapping the top layers of terrace A onto those of terrace B.

    Inputs are built atoms in CRYSTAL coordinates (angstrom) with their depth below the terrace's own
    top layer (0 = top). M runs over the rotations about [001] (identity, +-90, 180 degrees) and the
    four mirrors containing [001]; t runs over an a/``grid`` grid in the plane (as in the
    calculator's ``screw_search``, grid 8) with t_z fixed by the top-layer heights. A candidate is
    accepted if EVERY image atom lands on the layer of B at the same depth, modulo the (001) net.
    Returns one entry per operation and translation class modulo the net; ``lattice_symmetry`` says
    whether the operation also maps the whole diamond lattice onto itself (``is_diamond_symmetry``).
    """
    N, Ninv = _net(a_A)
    offA = _layer_offsets(rc_A, depth_A, a_A, tol_A, "terrace A")
    offB = _layer_offsets(rc_B, depth_B, a_A, tol_A, "terrace B")
    if set(offA) != set(offB):
        raise StructureAssertionError("(f) the two terraces expose different depth ranges")
    dz = offB[0][1] - offA[0][1]
    fB = np.array([offB[int(d)][0] for d in depth_A])
    zB = np.array([offB[int(d)][1] for d in depth_A])
    found, seen = [], set()
    for name, M in _OPS.items():
        img0 = rc_A @ M.T
        for i in range(grid):
            for j in range(grid):
                t = np.array([i * a_A / grid, j * a_A / grid, dz])
                img = img0 + t
                if np.max(np.abs(img[:, 2] - zB)) > tol_A:
                    continue
                diff = img[:, :2] @ Ninv.T - fB
                diff -= np.rint(diff)
                if np.max(np.linalg.norm(diff @ N.T, axis=1)) > tol_A:
                    continue
                ft = t[:2] @ Ninv.T
                ft = ft - np.floor(ft + 0.5)            # representative in [-1/2, 1/2)
                key = (name, tuple(np.round(ft % 1.0, 6) % 1.0))
                if key in seen:
                    continue
                seen.add(key)
                t_rep = np.array([*(N @ ft), dz])
                found.append(dict(operation=name, t_crystal_A=t_rep,
                                  proper=name in ("identity", "Rz(+90)", "Rz(180)", "Rz(-90)"),
                                  lattice_symmetry=is_diamond_symmetry(M, t_rep, a_A, tol_A)))
    return found


def classify_relation(relations: list[dict], delta_layers: int, axis_from, axis_to,
                      a_A: float = A_SI_A, tol_A: float = POSITION_TOL_A) -> str:
    """(f): a/2 steps must be pure lattice translations, a/4 steps 4_1 screws (and not
    translations), with the top-layer back-bond axis unchanged or rotated by 90 degrees."""
    names = {r["operation"] for r in relations}
    pure = [r for r in relations if r["operation"] == "identity"]
    lattice_pure = [r for r in pure if r["lattice_symmetry"]
                    and is_fcc_translation(r["t_crystal_A"], a_A, tol_A)]
    screws = [r for r in relations if r["operation"] in _SCREW_OPS and r["lattice_symmetry"]]
    if abs(delta_layers) == 2:
        if not lattice_pure:
            raise StructureAssertionError("(f) a/2 step: no pure lattice translation maps the "
                                          "terraces")
        if names & set(_SCREW_OPS):
            raise StructureAssertionError("(f) a/2 step: a 90-degree screw also maps the terraces")
        if _axis_key(axis_from) != _axis_key(axis_to):
            raise StructureAssertionError("(f) a/2 step: top-layer back-bond axis changed")
        return "translation"
    if abs(delta_layers) == 1:
        if pure:
            raise StructureAssertionError("(f) a/4 step: a pure translation maps the terraces")
        if not screws:
            raise StructureAssertionError("(f) a/4 step: no 90-degree lattice screw maps the "
                                          "terraces")
        if _axis_key(axis_from) == _axis_key(axis_to):
            raise StructureAssertionError("(f) a/4 step: top-layer back-bond axis did not rotate")
        return "screw"
    raise StructureAssertionError(f"(f) step of {delta_layers} layers is not a/4 or a/2")


def _measure_backbond_axes(layer, terrace, tops, pairs, frame, a_A, tol_A):
    """Top-layer back-bond axis of each terrace, from the built bonds (crystal frame)."""
    i, j, _, vec = pairs
    vec_c = frame.to_crystal(vec)
    q = a_A / 4.0
    axes = []
    for k, top in enumerate(tops):
        sel = (terrace[i] == k) & (layer[i] == top) & (layer[j] == top - 1)
        if not np.any(sel):
            raise StructureAssertionError(f"(f) terrace {k}: no top-layer back-bond found")
        v = vec_c[sel]
        if (np.max(np.abs(v[:, 2] + q)) > tol_A or np.max(np.abs(np.abs(v[:, 0]) - q)) > tol_A
                or np.max(np.abs(np.abs(v[:, 1]) - q)) > tol_A):
            raise StructureAssertionError(f"(f) terrace {k}: back-bonds are not diamond bonds")
        sgn = np.sign(v[:, 0] * v[:, 1])
        if not (np.all(sgn > 0) or np.all(sgn < 0)):
            raise StructureAssertionError(f"(f) terrace {k}: top-layer back-bonds on two axes")
        axes.append((1, 1, 0) if sgn[0] > 0 else (1, -1, 0))
    return axes


# --------------------------------------------------------------------------------------------------
# Builder
# --------------------------------------------------------------------------------------------------
def _termination_option(termination: str) -> dict:
    if termination == "bulk":
        return dict(value="bulk", label="ASSUMPTION B3",
                    note="unreconstructed bulk truncation of the diamond lattice")
    if termination == "dimer_2x1":
        raise NotImplementedError(
            "Si(001) 2x1 dimer reconstruction: NOT IMPLEMENTED. No source for the dimer geometry "
            "(dimer bond length, vertical and lateral displacements, buckling, subsurface "
            "relaxation) has been read or recorded in docs/source_map.tsv or docs/references.bib, "
            "and these values must not be invented (spec section 4.2; ASSUMPTION B3 keeps the "
            "bulk termination). Read a Si(001)-(2x1) structure determination, add its source-map "
            "row, then implement this option with the sourced parameters.")
    raise ValueError(f"termination must be 'bulk' (ASSUMPTION B3) or 'dimer_2x1' "
                     f"(NOT IMPLEMENTED), got {termination!r}")


def _overlayer_option(overlayer, vacuum_above_A: float) -> dict:
    if overlayer is None:
        return dict(value=None, label="ASSUMPTION B7",
                    note="clean surface; the real surface is ion-milled (PROJECT_INPUT item 12) "
                         "and carries an oxide/damage layer that this structure omits")
    if not isinstance(overlayer, OverlayerSpec):
        raise TypeError("overlayer must be an OverlayerSpec or None (explicit clean surface, "
                        "ASSUMPTION B7)")
    _check_label(overlayer.label, "overlayer (PROJECT_INPUT item 12)")
    if not isinstance(overlayer.material, str) or not overlayer.material.strip():
        raise ValueError("overlayer.material is required")
    T = float(overlayer.thickness_A)
    rho = float(overlayer.density_g_cm3)
    if not (np.isfinite(T) and T > 0.0):
        raise ValueError("overlayer.thickness_A must be a positive number (PROJECT_INPUT item 12)")
    if not (np.isfinite(rho) and rho > 0.0):
        raise ValueError("overlayer.density_g_cm3 must be positive (PROJECT_INPUT item 12)")
    if vacuum_above_A < T:
        raise ValueError(f"vacuum_above_A = {vacuum_above_A} A cannot hold the declared "
                         f"{T} A overlayer")
    return dict(value="declared_region", material=overlayer.material, thickness_A=T,
                density_g_cm3=rho, label=overlayer.label, project_input="item 12",
                region="conformal: from the top atomic-layer plane of each terrace to that plane "
                       "+ thickness_A (conformality is an ASSUMPTION)",
                atomistic_content="NOT IMPLEMENTED: a random-network amorphous SiO2/Si model "
                                  "needs a sourced structure; no overlayer atoms are placed",
                atoms_placed=0)


def build_si001_terraces(*, azimuth_uvw, azimuth_label: str, staircase: Staircase,
                         edge_periods: int, substrate_layers: int,
                         first_terrace_backbond_uvw, termination: str,
                         overlayer: OverlayerSpec | None,
                         vacuum_above_A: float) -> Si001Structure:
    """Build a bulk-terminated Si(001) terrace staircase and run assertions (a) to (g).

    Every argument is required (keyword-only, no defaults):

    azimuth_uvw, azimuth_label   beam azimuth, PROJECT_INPUT item 8 ([110] or [100] families), with
                                 its evidence label (PROJECT_INPUT..., TEST_ONLY..., ASSUMPTION...)
    staircase                    :class:`Staircase` (terrace heights on the a/4 grid, widths, edge
                                 orientation relative to the beam, declared boundary step)
    edge_periods                 cell length along the step edges, in in-plane periods
    substrate_layers             number of (001) layers of the lowest terrace (>= 4), bottom at x=0
    first_terrace_backbond_uvw   [1,1,0] or [1,-1,0]: top-layer back-bond axis of terrace 0 (fixes
                                 which of the two screw-related terrace types terrace 0 is)
    termination                  'bulk' (ASSUMPTION B3) or 'dimer_2x1' (raises NotImplementedError)
    overlayer                    :class:`OverlayerSpec` (PROJECT_INPUT item 12) or None (explicit
                                 clean surface, ASSUMPTION B7)
    vacuum_above_A               vacuum above the highest top layer inside the (non-periodic) x box
    """
    a = float(A_SI_A)
    q = a / 4.0
    _check_label(azimuth_label, "azimuth (PROJECT_INPUT item 8)")
    az = tuple(int(v) for v in azimuth_uvw)
    if tuple(azimuth_uvw) != az and not np.allclose(np.asarray(azimuth_uvw, float), az):
        raise ValueError("azimuth_uvw must be integer indices")
    frame = surface_frame(NORMAL_HKL, az)          # refuses an azimuth out of the surface plane
    family = next((f for f, s in _AZIMUTHS.items() if az in s), None)
    if family is None:
        raise ValueError(f"azimuth {az}: PROJECT_INPUT item 8 allows only the [110] or [100] "
                         f"families for Si(001) (in the (001) surface plane)")
    checks.assert_frame(frame, NORMAL_HKL)                                   # (g)

    opt_term = _termination_option(termination)
    vacuum_above_A = float(vacuum_above_A)
    if not (np.isfinite(vacuum_above_A) and vacuum_above_A > 0.0):
        raise ValueError("vacuum_above_A must be positive")
    opt_over = _overlayer_option(overlayer, vacuum_above_A)
    steps = validate_staircase(staircase, a)                                 # (d), (e) request
    if int(edge_periods) != edge_periods or edge_periods < 1:
        raise ValueError("edge_periods must be a positive integer")
    if int(substrate_layers) != substrate_layers or substrate_layers < _MIN_SUBSTRATE_LAYERS:
        raise ValueError(f"substrate_layers must be an integer >= {_MIN_SUBSTRATE_LAYERS} (the "
                         f"terrace-relation check compares the top four layers)")
    edge_periods, substrate_layers = int(edge_periods), int(substrate_layers)
    axis0 = _axis_key(first_terrace_backbond_uvw)

    # --- geometry of the periodic cell --------------------------------------------------------
    p = a / np.sqrt(2.0) if family == "<110>" else a          # in-plane lattice period along y, z
    atoms_per_layer_per_cell = 1 if family == "<110>" else 2   # (001) layer density 2/a^2
    s_ax, e_ax = (1, 2) if staircase.edges == "parallel" else (2, 1)
    widths = np.array(staircase.terrace_widths, dtype=np.int64)
    L = np.zeros(3)
    L[s_ax] = float(widths.sum()) * p
    L[e_ax] = float(edge_periods) * p
    bounds = np.concatenate([[0], np.cumsum(widths)]).astype(float) * p
    t_rel = np.array(staircase.terrace_layers, dtype=np.int64)
    tops = t_rel - t_rel.min() + substrate_layers - 1          # slab layer index of each top
    # crystal layer n3 = l + c0; choose c0 so terrace 0 has the requested back-bond axis
    c0 = 0 if backbond_axis_of_crystal_layer(tops[0]) == axis0 else 1
    origin = np.array([-c0 * q, 0.0, 0.0])                     # slab position of crystal origin
    x_top = float(tops.max()) * q
    L[0] = x_top + vacuum_above_A

    # --- one continuous lattice ---------------------------------------------------------------
    corners = np.array([[x, y, z] for x in (-q, x_top + q) for y in (-p, L[1] + p)
                        for z in (-p, L[2] + p)])
    corners_c = frame.to_crystal(corners - origin)
    n = diamond_sites_quarter(corners_c.min(axis=0), corners_c.max(axis=0), a)
    rc = n.astype(float) * q
    rs = frame.to_slab(rc) + origin
    layer = n[:, 2] - c0                                         # exact integer layer index
    tol = WINDOW_TOL_A
    in_win = ((rs[:, 1] >= -tol) & (rs[:, 1] < L[1] - tol)
              & (rs[:, 2] >= -tol) & (rs[:, 2] < L[2] - tol))
    terr = np.searchsorted(bounds[1:] - tol, rs[:, s_ax], side="right")
    terr = np.clip(terr, 0, len(widths) - 1)
    keep = in_win & (layer >= 0) & (layer <= tops[terr])
    rs, rc, layer, terr = rs[keep], rc[keep], layer[keep], terr[keep]
    rs[:, 1:][np.abs(rs[:, 1:]) < tol] = 0.0                     # snap boundary rows to 0
    order = np.lexsort((rs[:, 1], rs[:, 2], rs[:, 0]))
    rs, rc, layer, terr = rs[order], rc[order], layer[order], terr[order]
    per = [None, float(L[1]), float(L[2])]

    # --- assertions ---------------------------------------------------------------------------
    passed = ["(g) frame right-handed, x = outward normal [001], beam azimuth in the surface"]
    checks.assert_on_lattice_sites(rs, frame, origin, a)                      # (a)
    passed.append("(a) every atom on a site of one bulk diamond lattice")
    checks.assert_half_open_window(rs[:, 1], L[1], "y")                        # (b)
    checks.assert_half_open_window(rs[:, 2], L[2], "z")
    per_terrace_expected = atoms_per_layer_per_cell * edge_periods * widths * (tops + 1)
    counts = np.bincount(terr, minlength=len(widths))
    if not np.array_equal(counts, per_terrace_expected):
        raise StructureAssertionError(f"(b) per-terrace atom counts {counts.tolist()} != "
                                      f"expected {per_terrace_expected.tolist()}")
    expected = int(per_terrace_expected.sum())
    checks.assert_no_duplicates_and_count(rs, per, expected)
    passed.append("(b) half-open window, no duplicates under the PBC, atom count as expected")
    interior = (layer >= 1) & (layer <= tops.min() - 1)
    pairs = checks.assert_min_distance_and_coordination(rs, per, a, interior)  # (c)
    passed.append("(c) minimum distance = a*sqrt(3)/4; interior atoms 4-coordinated")
    measured_tops = np.array([rs[terr == k, 0].max() for k in range(len(widths))])
    if np.max(np.abs(measured_tops - tops * q)) > POSITION_TOL_A:
        raise StructureAssertionError("(d) measured terrace tops differ from the requested layers")
    assert_step_heights(measured_tops, staircase, steps, a)                   # (d), (e)
    passed.append("(d) step heights a/4 or a/2 as requested (measured on the atoms)")
    passed.append("(e) staircase continuous under the periodic boundary (no net height change)")
    axes = _measure_backbond_axes(layer, terr, tops, pairs, frame, a, POSITION_TOL_A)
    if axes[0] != axis0:
        raise StructureAssertionError(f"(f) terrace 0 back-bond axis {axes[0]} != requested "
                                      f"{axis0}")
    for s in steps:                                                          # (f)
        A, B = s["from_terrace"], s["to_terrace"]
        selA = (terr == A) & (layer >= tops[A] - 3)
        selB = (terr == B) & (layer >= tops[B] - 3)
        rel = find_terrace_relations(rc[selA], tops[A] - layer[selA], rc[selB],
                                     tops[B] - layer[selB], a)
        kind = classify_relation(rel, s["delta_layers"], axes[A], axes[B], a)
        mirrors = [r["operation"] for r in rel if r["operation"] in _MIRROR_NORMALS
                   and r["lattice_symmetry"]
                   and int(np.dot(_MIRROR_NORMALS[r["operation"]], az)) == 0]
        chosen = [r for r in rel if r["lattice_symmetry"] and r["operation"] ==
                  ("identity" if kind == "translation" else "Rz(+90)")]
        if not chosen:
            chosen = [r for r in rel if r["operation"] in _SCREW_OPS and r["lattice_symmetry"]]
        best = min(chosen, key=lambda r: float(np.linalg.norm(r["t_crystal_A"][:2])))
        s.update(
            type=kind,
            position_A=float(bounds[s["index"] + 1] % L[s_ax]),
            axis="y" if s_ax == 1 else "z",
            height_A=float(s["delta_layers"] * q),
            measured_height_A=float(measured_tops[B] - measured_tops[A]),
            direction=("up" if s["delta_layers"] > 0 else "down") + " along +"
                      + ("y" if s_ax == 1 else "z (the beam direction)"),
            upper_terrace_upstream=(bool(s["delta_layers"] < 0) if s_ax == 2 else None),
            relation=dict(
                verified_on_atoms=True,
                operation=best["operation"],
                t_crystal_A=best["t_crystal_A"].tolist(),
                t_slab_A=frame.to_slab(best["t_crystal_A"]).tolist(),
                operations_found=sorted({r["operation"] for r in rel}),
                incidence_plane_mirror_operations=sorted(set(mirrors)),
                incidence_plane_mirror_note=(
                    "DERIVED_HERE symmetry fact measured on the atoms: a mirror (or glide) whose "
                    "plane contains the beam azimuth and the normal maps one terrace onto the "
                    "other; its consequence for the dynamical reflectivity is NOT asserted here"),
                model_assumption_B4=("applies far from the riser (pure translation)"
                                     if kind == "translation" else
                                     "does NOT apply (4_1 screw-related terraces)"),
            ))
    passed.append("(f) a/2 terraces related by a pure lattice translation, a/4 terraces by a "
                  "90-degree screw (measured on the atoms)")

    # --- metadata -----------------------------------------------------------------------------
    terrace_map = []
    for k in range(len(widths)):
        ax = axes[k]
        ax_slab = frame.to_slab(np.array(ax, float) / np.sqrt(2.0))
        terrace_map.append(dict(
            index=k, s_range_A=[float(bounds[k]), float(bounds[k + 1])],
            width_periods=int(widths[k]), top_layer_relative=int(t_rel[k]),
            top_layer_index=int(tops[k]), top_height_A=float(tops[k] * q),
            crystal_layer_n3=int(tops[k] + c0),
            top_layer_backbond_axis_crystal=list(ax),
            top_layer_backbond_axis_slab=ax_slab.tolist(),
            backbond_angle_to_beam_deg=float(np.degrees(np.arctan2(abs(ax_slab[1]),
                                                                   abs(ax_slab[2])))),
            n_atoms=int(counts[k]),
            continuous_with_terrace_0_across_boundary=bool(
                k == len(widths) - 1 and len(widths) > 1 and staircase.boundary_step_layers == 0),
        ))
    cell = np.diag(L)
    pos_hash = hashlib.sha256(np.ascontiguousarray(rs, dtype="<f8").tobytes()).hexdigest()
    metadata = dict(
        schema="reflection_holo.structure.si001/1",
        builder="reflection_holo.structure.si001.build_si001_terraces",
        package_version=reflection_holo.__version__,
        units="angstrom",
        surface=dict(hkl=list(NORMAL_HKL), outward_normal="[001]",
                     label="PROJECT_INPUT item 11 (Si(001), supplied by Ali 2026-09-22)"),
        azimuth=dict(uvw=list(az), family=family, label=azimuth_label, project_input="item 8"),
        frame=dict(convention="x = outward normal, z = beam azimuth, y = z x x "
                              "(docs/physics_conventions.md)",
                   x_hat_crystal=frame.x_hat.tolist(), y_hat_crystal=frame.y_hat.tolist(),
                   z_hat_crystal=frame.z_hat.tolist(), crystal_origin_slab_A=origin.tolist()),
        lattice=dict(a_A=a, a_label="ASSUMPTION B2", basis="constants.DIAMOND_BASIS (SM02)",
                     layer_spacing_A=q, nearest_neighbour_A=nearest_neighbour_distance_A(a),
                     in_plane_period_A=float(p), one_continuous_lattice=True),
        cell=dict(vectors_A=cell.tolist(), pbc=[False, True, True],
                  vacuum_above_A=vacuum_above_A,
                  note="x is not periodic; bottom atomic layer at x = 0; no vacuum below the "
                       "crystal; y and z are lattice periods"),
        staircase=dict(edges=staircase.edges, staircase_axis="y" if s_ax == 1 else "z",
                       edge_axis="y" if e_ax == 1 else "z",
                       terrace_layers=[int(v) for v in t_rel],
                       terrace_widths_periods=[int(v) for v in widths],
                       boundary_step_layers=int(staircase.boundary_step_layers),
                       net_height_change_layers=0),
        terrace_map=terrace_map,
        steps=steps,
        options=dict(
            termination=opt_term,
            dimer_reconstruction=dict(value="not enabled", status="NOT IMPLEMENTED: no Si(001)-"
                                      "(2x1) dimer geometry source has been read"),
            overlayer=opt_over,
            riser_relaxation=dict(value="none", label="ASSUMPTION",
                                  note="spec 4.2 'step-riser relaxation none'; no "
                                       "model_assumptions row yet; B4 notes the riser region"),
        ),
        substrate_layers=substrate_layers, edge_periods=edge_periods,
        atom_count=int(rs.shape[0]), expected_atom_count=expected,
        tolerances_A=dict(position=POSITION_TOL_A, window=WINDOW_TOL_A,
                          duplicate_distance=checks.DUPLICATE_DIST_A),
        assertions_passed=passed,
        positions_sha256=pos_hash,
    )
    if opt_over["value"] == "declared_region":
        opt_over["per_terrace_x_range_A"] = [[float(tops[k] * q),
                                              float(tops[k] * q + opt_over["thickness_A"])]
                                             for k in range(len(widths))]
    return Si001Structure(positions_A=rs, species=np.full(rs.shape[0], "Si"), cell_A=cell,
                          pbc=(False, True, True), frame=frame, layer_index=layer,
                          terrace_index=terr, crystal_origin_slab_A=origin, metadata=metadata)
