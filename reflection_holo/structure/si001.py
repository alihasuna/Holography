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
* an a/4 (single-layer) step joins terraces related by the diamond 4_1 and 4_3 screws (a 90 degree
  rotation about [001] plus a translation with ``t . n_hat = a/4``) and by the two <100> d-glides,
  never by a translation; the top-layer back-bond axis (and the dimer-row direction, were a
  reconstruction enabled) rotates by 90 degrees. At an exact <100> azimuth the d-glide whose plane
  contains the beam and the normal fixes k_in and k_out, so B4 applies for bulk-terminated terraces
  (C2 section 1; SM26); at <110> no operation fixes the beam, and B4 does not apply (dynamical
  residual delta, model_assumptions open question 3). ``b4_statement`` records this per step from
  the operations measured on the atoms (audit A2 m3).

Both relations are verified numerically on the built atoms by :func:`find_terrace_relations`, which
generalises the calculator's ``screw_search`` (90 degree rotations times translations on an a/8
grid, tested modulo the lattice) from the 8-atom basis to the atoms of two built terraces.

Options, each recorded with its label in ``metadata["options"]``: bulk termination (ASSUMPTION B3);
the Si(001) dimer reconstructions p(2x1)s, p(2x1)a, p(2x2) and c(4x2) of Ramstad, Brocks and Kelly
1995 Tables III-IV (SECTION_READ; T = 0 geometries, their use at the specimen temperature is an
ASSUMPTION) and the "p(2x1)a flip-flop ensemble" (ASSUMPTION B37, a model choice, not a source), all
in ``reconstruction.py``; amorphous SiO2/damage overlayer (thickness and density are PROJECT_INPUT
item 12, required; declared region only, atomistic content NOT IMPLEMENTED); step-riser relaxation
none (ASSUMPTION).

With a reconstruction, assertions (a) to (g) run unchanged on the IDEAL sites (the bulk truncation
that is then reconstructed); the reconstructed atoms are checked by (r1) to (r6)
(``_assert_reconstruction``): displacements only in the five tabulated layers of complete dimer
cells; every dimer's bond length and buckling equal to the table's; one dimer-bond axis per terrace,
normal to its top-layer back-bond axis, hence rotated by 90 degrees across every a/4 step and not
across an a/2 step (measured on the built atoms); no collision (minimum distance, over every
configuration of the flip-flop ensemble); the bulk interior below the reconstructed layers
unchanged and 4-coordinated.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np

import reflection_holo
from reflection_holo.constants import DIAMOND_BASIS
from reflection_holo.geometry.frames import SurfaceFrame, surface_frame
from reflection_holo.io.labels import require_evidence_label

from . import checks
from . import reconstruction as recon
from .checks import POSITION_TOL_A, WINDOW_TOL_A, StructureAssertionError
from .lattice import (diamond_sites_quarter, is_fcc_translation, nearest_neighbour_distance_A,
                      neighbour_pairs)

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
    # reconstructed terminations only: ideal sites, displacements, flip-flop cells (reconstruction.py)
    reconstruction: "recon.ReconstructionRecord | None" = None

    @property
    def n_atoms(self) -> int:
        return int(self.positions_A.shape[0])

    @property
    def periodic_lengths_A(self):
        return [None if not p else float(self.cell_A[k, k]) for k, p in enumerate(self.pbc)]


# --------------------------------------------------------------------------------------------------
# Assertions (d) and (e): the staircase request
# --------------------------------------------------------------------------------------------------
def validate_staircase(st: Staircase, a_A: float) -> list[dict]:
    """Refuse staircases that are not continuous under the periodic boundary or whose steps are not
    a/4 or a/2; return the step list (including a non-zero step at the periodic cell edge).
    a_A: the lattice parameter (required; the builder's labelled argument)."""
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
    braw = st.boundary_step_layers
    if isinstance(braw, bool) or not isinstance(braw, (int, np.integer, float, np.floating)) \
            or int(braw) != braw:
        raise ValueError(f"boundary_step_layers must be an integer number of a/4 layers, got {braw!r}")
    b = int(braw)
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
                        a_A: float, tol_A: float = POSITION_TOL_A) -> None:
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


def is_diamond_symmetry(M: np.ndarray, t_crystal_A: np.ndarray, a_A: float,
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
                           depth_B: np.ndarray, a_A: float, grid: int = 8,
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
                      a_A: float, tol_A: float = POSITION_TOL_A) -> str:
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


B4_TRANSLATION = "applies far from the riser (pure translation)"
B4_A4_100 = ("B4 applies for the specular beam (and, with the in-plane glide term, for other beams "
             "in the incidence plane) of a plane wave on bulk-terminated terraces (d-glide in the "
             "incidence plane); it does not apply to beams leaving the incidence plane, a 2x1 "
             "reconstruction or an overlayer; the azimuthal spread is not analysed "
             "(SM26, C2, E4 M1)")
B4_A4_110 = ("does not apply (dynamical residual delta, not forced to vanish by symmetry (value "
             "unknown); open question 3)")
B4_A4_OTHER = "does not apply"

def b4_statement(kind: str, azimuth_uvw, incidence_plane_operations) -> str:
    """Whether model_assumptions B4 (dynamical reflection phase cancels between the terraces) holds
    for a step, from its measured relation (audit A2 m3; C2 section 1; SM26).

    kind "translation" (a/2): B4 applies far from the riser. kind "screw" (a/4): at an exact <100>
    azimuth AND with an incidence-plane glide measured on the atoms, B4 applies for the specular beam
    (and, with the in-plane glide term, for other beams in the incidence plane) of a plane wave on
    bulk-terminated terraces, not for beams leaving the incidence plane, a 2x1 reconstruction or an
    overlayer, and the azimuthal spread is not analysed (review E4 M1); at <110> it does not apply
    (the dynamical residual delta is not forced to vanish by symmetry, value unknown, open
    question 3); at any other azimuth, or without the measured glide, it does not apply. The caveats of B4 (riser region,
    2x1 reconstruction, overlayer, strain, azimuthal misalignment to first order) are stated in
    docs/model_assumptions.md and are not re-asserted here.
    """
    if kind == "translation":
        return B4_TRANSLATION
    if kind != "screw":
        raise ValueError(f"kind must be 'translation' or 'screw', got {kind!r}")
    az = tuple(int(v) for v in azimuth_uvw)
    if az in _AZIMUTHS["<100>"]:
        return B4_A4_100 if list(incidence_plane_operations) else B4_A4_OTHER
    if az in _AZIMUTHS["<110>"]:
        return B4_A4_110
    return B4_A4_OTHER


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
TERMINATIONS = ("bulk",) + recon.RECONSTRUCTIONS


def _termination_option(termination: str) -> dict:
    if termination == "bulk":
        return dict(value="bulk", label="ASSUMPTION B3",
                    note="unreconstructed bulk truncation of the diamond lattice")
    if termination in recon.STATIC_RECONSTRUCTIONS:
        return dict(value=termination, label=recon.STATIC_LABEL,
                    note=f"static {termination} dimer reconstruction of the five outermost layers "
                         f"of every terrace (R1 T = 0 LDA geometry; at room temperature the "
                         f"dimers flip-flop and c(4x2) order appears only below 205 K, L7 "
                         f"section 1.2)")
    if termination == recon.FLIPFLOP:
        return dict(value=termination, label=recon.FLIPFLOP_LABEL,
                    note="the structure's positions are ONE member of the ensemble (every cell in "
                         "the Table III state); a run must draw the configuration of every "
                         "realisation (forward.dimer_ensemble.DimerFlipFlopPotential)",
                    ensemble=True)
    if termination == "dimer_2x1":
        raise NotImplementedError(
            "termination 'dimer_2x1' is NOT IMPLEMENTED as a generic option: the sourced Si(001) "
            "reconstructions differ in dimer bond length, buckling and subsurface relaxation "
            "(source: Ramstad, Brocks and Kelly 1995, Tables III-IV, SECTION_READ; L7 section 1.4), "
            "and the choice between them must not be invented by the builder. Request one of "
            f"{recon.RECONSTRUCTIONS} explicitly, or 'bulk' (ASSUMPTION B3).")
    raise ValueError(f"termination must be 'bulk' (ASSUMPTION B3) or one of the reconstructions "
                     f"{recon.RECONSTRUCTIONS}, got {termination!r}")


B4_RECON_TRANSLATION = ("applies far from the riser: the reconstructed layers of the two terraces "
                        "are related by the pure lattice translation (up to an in-plane shift of "
                        "the pattern) to R1's printed precision, measured on the atoms")
B4_RECON_A4_100 = ("B4 applies for the specular beam (and, with the in-plane glide term, for other "
                   "beams in the incidence plane) of a plane wave on these STATIC reconstructed "
                   "terraces: the incidence-plane glide maps the reconstructed layers of one "
                   "terrace onto the other (up to an in-plane shift of the pattern) to R1's "
                   "printed precision, measured on the atoms; not for beams leaving the incidence "
                   "plane; the riser (not relaxed) and the azimuthal spread are not analysed")
B4_RECON_ENSEMBLE = ("applies to the ENSEMBLE AVERAGE only (DERIVED_HERE): the operation fixing the "
                     "beam maps every cell state of one terrace onto a cell state of the other "
                     "(measured on the atoms) and each state has probability 1/2 independently, so "
                     "the ensemble of one terrace is the image of the other's; a single "
                     "realisation is not symmetric (finite-ensemble residual of the coherent "
                     "average)")
B4_RECON_NOT = ("does not apply: no operation fixing the beam maps the reconstructed layers of one "
                "terrace onto the other (measured on the atoms); report the dynamical phase "
                "difference, not a height")


def _b4_reconstructed(rec, s, ops, az, *, quarter, layer, terr, tops, frame, a_A):
    """B4 statement of a step between reconstructed terraces from the measured relations."""
    A, B = s["from_terrace"], s["to_terrace"]
    measured = []
    for name, t in ops:
        M = _OPS[name]
        pairs = [(0, 0)] + ([(0, 1), (1, 0), (1, 1)] if rec.mirror_displacement_A is not None
                            else [])
        for sa, sb in pairs:
            r = recon.reconstruction_relation(rec, quarter=quarter, layer=layer, terrace=terr,
                                              tops=tops, frame=frame, A=A, B=B, M=M,
                                              t_crystal_A=t, a_A=a_A, state_A=sa, state_B=sb)
            measured.append(dict(operation=name, **r))
    if s["type"] == "screw" and tuple(az) not in _AZIMUTHS["<100>"]:
        return (B4_A4_110 if tuple(az) in _AZIMUTHS["<110>"] else B4_A4_OTHER), measured
    if not measured:
        return B4_RECON_NOT, measured
    if rec.mirror_displacement_A is None:
        ok = any(m["holds"] for m in measured)
        if not ok:
            return B4_RECON_NOT, measured
        return (B4_RECON_TRANSLATION if s["type"] == "translation" else B4_RECON_A4_100), measured
    # flip-flop: every state of A must map onto some state of B under one operation
    for name in {m["operation"] for m in measured}:
        mm = [m for m in measured if m["operation"] == name]
        if all(any(m["holds"] for m in mm if m["state_A"] == sa) for sa in (0, 1)):
            return B4_RECON_ENSEMBLE, measured
    return B4_RECON_NOT, measured


def _terrace_groups(t_rel) -> list[list[int]]:
    """Terraces forming one physical terrace: the single terrace of a flat cell, and terraces 0 and
    n - 1 when they have the same height (joined across the periodic cell edge)."""
    n = len(t_rel)
    if n == 1:
        return [[0]]
    if int(t_rel[0]) == int(t_rel[-1]):
        return [[0, n - 1]] + [[k] for k in range(1, n - 1)]
    return [[k] for k in range(n)]


def step_edge_type(delta_layers: int, upper_row_axis_crystal, edge_axis_crystal) -> str:
    """Zandvliet 2000 (p. 594) step names on reconstructed terraces: S (single, a/4) or D (double,
    a/2), A if the step edge runs along the dimer rows of the UPPER terrace, B if normal to them;
    a step edge along <100> (45 degrees to both) is neither (a sequence of kinks)."""
    row = np.asarray(upper_row_axis_crystal, float)
    e = np.asarray(edge_axis_crystal, float)
    c = abs(float(row @ e)) / (np.linalg.norm(row) * np.linalg.norm(e))
    kind = "S" if abs(delta_layers) == 1 else "D"
    if abs(c - 1.0) < 1e-9:
        return kind + "A"
    if c < 1e-9:
        return kind + "B"
    return (f"{kind}-type step with a <100> edge (45 deg to the dimer rows): neither "
            f"{kind}A nor {kind}B")


def _assert_reconstruction(rec, *, layer, terr, tops, steps, axes, frame, per, a_A, groups):
    """(r1) to (r6) on the reconstructed atoms (module docstring). Returns the records."""
    name = rec.name
    group_of_terrace = np.empty(len(tops), np.int64)
    for gi, g in enumerate(groups):
        group_of_terrace[g] = gi
    group_of_atom = group_of_terrace[terr]
    pos = rec.ideal_positions_A + rec.displacement_A
    depth = tops[terr] - layer
    moved = np.linalg.norm(rec.displacement_A, axis=1) > 0
    if np.any(moved & ((depth < 0) | (depth >= recon.RECONSTRUCTED_DEPTH))):
        raise StructureAssertionError("(r1) an atom below the five tabulated layers was displaced")
    if np.any(moved & (rec.cell_index < 0)):
        raise StructureAssertionError("(r1) an atom outside every complete dimer cell was displaced")
    if rec.mirror_displacement_A is not None and np.any(
            (np.linalg.norm(rec.mirror_displacement_A, axis=1) > 0) & (rec.cell_index < 0)):
        raise StructureAssertionError("(r1) mirror state defined outside the complete cells")
    top_mask = depth == 0
    refs = recon.reference_dimers(name, a_A)
    states = [(pos, "the structure's configuration")]
    if rec.mirror_displacement_A is not None:
        states.append((rec.ideal_positions_A + rec.mirror_displacement_A,
                       "every cell buckling-reversed"))
    dim = None
    for p_state, what in states:
        m = recon.measure_dimers(p_state, top_mask, group_of_atom, per, frame)
        if len(m["i"]) != rec.n_cells:
            raise StructureAssertionError(
                f"(r3) {what}: {len(m['i'])} top-layer pairs closer than "
                f"{recon.DIMER_SEARCH_CUTOFF_A} A, expected one per complete cell ({rec.n_cells})")
        paired = top_mask & (rec.cell_index >= 0)
        if np.any(m["partners_per_atom"][paired] != 1) or np.any(
                m["partners_per_atom"][top_mask & ~paired] != 0):
            raise StructureAssertionError(f"(r3) {what}: a top-layer atom is not in exactly the "
                                          f"dimer of its cell")
        for b, th in zip(m["bond_A"], m["buckling_deg"]):
            if not any(abs(b - r["bond_A"]) <= recon.POSITION_TOL_A
                       and abs(th - r["buckling_deg"]) <= 1e-6 for r in refs):
                raise StructureAssertionError(
                    f"(r3) {what}: dimer bond {b:.6f} A / buckling {th:.6f} deg differs from the "
                    f"{name} table's dimers {[(r['bond_A'], r['buckling_deg']) for r in refs]}")
        if dim is None:
            dim = m
    # (r4) one dimer-bond axis per terrace, normal to the top-layer back-bond axis
    measured_axes = {}
    for k in range(len(tops)):
        got = dim["per_terrace_axes"].get(int(group_of_terrace[k]), [])
        if len(got) != 1:
            raise StructureAssertionError(f"(r4) terrace {k}: dimer-bond axes {got} (need one)")
        ax = (1, 1, 0) if got[0] == "[1,1,0]" else (1, -1, 0)
        if _axis_key(ax) == _axis_key(axes[k]):
            raise StructureAssertionError(f"(r4) terrace {k}: dimer bond parallel to the top-layer "
                                          f"back-bond axis {axes[k]}")
        measured_axes[k] = ax
    step_rec = []
    for s in steps:
        A, B = s["from_terrace"], s["to_terrace"]
        rotated = _axis_key(measured_axes[A]) != _axis_key(measured_axes[B])
        if abs(s["delta_layers"]) == 1 and not rotated:
            raise StructureAssertionError(f"(r4) a/4 step {s['index']}: dimer rows not rotated")
        if abs(s["delta_layers"]) == 2 and rotated:
            raise StructureAssertionError(f"(r4) a/2 step {s['index']}: dimer rows rotated")
        step_rec.append((s["index"], rotated))
    # (r5) no collision (reconstruction.assert_no_collision; every flip-flop configuration)
    out = dict(collision=recon.assert_no_collision(rec, group_of_atom, per, a_A))
    # the repository's existing duplicate criterion (assertion (b)) on the reconstructed positions
    checks.assert_no_duplicates_and_count(pos, per, len(pos))
    # (r6) bulk interior below every reconstructed layer: unchanged and 4-coordinated at d_nn
    d_nn = nearest_neighbour_distance_A(a_A)
    interior = (layer >= 1) & (layer <= int(tops.min()) - recon.RECONSTRUCTED_DEPTH - 1)
    if np.any(interior):
        i, _, d, _ = neighbour_pairs(pos, per, 1.05 * d_nn)
        ok = np.abs(d - d_nn) <= POSITION_TOL_A
        coord = np.bincount(i[ok], minlength=len(pos))
        anyc = np.bincount(i, minlength=len(pos))
        bad = interior & ((coord != 4) | (anyc != 4))
        if np.any(bad):
            raise StructureAssertionError(f"(r6) {int(bad.sum())} bulk-interior atom(s) not "
                                          f"4-coordinated at d_nn after the reconstruction")
        out["interior_atoms_checked"] = int(interior.sum())
    else:
        out["interior_atoms_checked"] = 0
        out["interior_note"] = ("no layer lies below the reconstructed depth of the lowest "
                                "terrace and above the bottom layer; (r6) not applicable")
    out.update(measured_dimer_axes_crystal={int(k): list(v) for k, v in measured_axes.items()},
               measured_dimers=dict(
                   n=int(len(dim["i"])),
                   bond_A=sorted({round(float(b), 6) for b in dim["bond_A"]}),
                   buckling_deg=sorted({round(float(b), 6) for b in dim["buckling_deg"]})),
               step_rotation=[dict(step=i, dimer_rows_rotated_90_deg=bool(r)) for i, r in step_rec])
    return out


def _overlayer_option(overlayer, vacuum_above_A: float) -> dict:
    if overlayer is None:
        return dict(value=None, label="ASSUMPTION B7",
                    note="clean surface; the real surface is ion-milled (PROJECT_INPUT item 12) "
                         "and carries an oxide/damage layer that this structure omits")
    if not isinstance(overlayer, OverlayerSpec):
        raise TypeError("overlayer must be an OverlayerSpec or None (explicit clean surface, "
                        "ASSUMPTION B7)")
    require_evidence_label(overlayer.label, "overlayer (PROJECT_INPUT item 12)",
                           accepted=LABEL_PREFIXES, qualified=True)
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
                         vacuum_above_A: float, lattice_parameter_A: float,
                         lattice_parameter_label: str) -> Si001Structure:
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
    termination                  'bulk' (ASSUMPTION B3); a static reconstruction 'p(2x1)s',
                                 'p(2x1)a', 'p(2x2)', 'c(4x2)' (R1 Tables III-IV); or
                                 'p(2x1)a flip-flop ensemble' (ASSUMPTION B37); 'dimer_2x1' is
                                 refused as ambiguous (NotImplementedError)
    overlayer                    :class:`OverlayerSpec` (PROJECT_INPUT item 12) or None (explicit
                                 clean surface, ASSUMPTION B7)
    vacuum_above_A               vacuum above the highest top layer inside the (non-periodic) x box
    lattice_parameter_A, lattice_parameter_label
                                 the lattice parameter (A) and its evidence label, e.g.
                                 reflection_holo.constants.A_SI_A with "ASSUMPTION B2", or a
                                 configuration's value with its label (audit A2 m6; never
                                 hard-coded)
    """
    require_evidence_label(lattice_parameter_label, "lattice parameter (model_assumptions B2)",
                           accepted=LABEL_PREFIXES, qualified=True)
    a = float(lattice_parameter_A)
    if not (np.isfinite(a) and a > 0.0):
        raise ValueError(f"lattice_parameter_A must be finite and > 0, got {lattice_parameter_A!r}")
    q = a / 4.0
    require_evidence_label(azimuth_label, "azimuth (PROJECT_INPUT item 8)",
                           accepted=LABEL_PREFIXES, qualified=True)
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
    b4_ops = {}
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
        b4_ops[s["index"]] = [(r["operation"], r["t_crystal_A"]) for r in rel
                              if r["lattice_symmetry"] and (
                                  r["operation"] in mirrors if kind == "screw"
                                  else r["operation"] == "identity")]
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
                    "other; its consequence for the reflectivity is model_assumption_B4 "
                    "(C2 section 1.3; SM26)"),
                model_assumption_B4=b4_statement(kind, az, mirrors),
            ))
    passed.append("(f) a/2 terraces related by a pure lattice translation, a/4 terraces by a "
                  "90-degree screw (measured on the atoms)")

    # --- reconstruction of the five outermost layers of every terrace (reconstruction.py) ------
    rec = None
    recon_checks = None
    if termination != "bulk":
        if opt_over["value"] is not None:
            raise NotImplementedError("a reconstruction under a declared overlayer is NOT "
                                      "IMPLEMENTED (a buried interface is not a clean surface)")
        rec = recon.build_reconstruction(
            termination, ideal_positions_A=rs, quarter=np.rint(rc / q).astype(np.int64),
            layer=layer, terrace=terr, tops=tops, c0=c0, frame=frame, origin=origin, a_A=a, L=L,
            s_ax=s_ax, e_ax=e_ax, groups=_terrace_groups(t_rel))
        recon_checks = _assert_reconstruction(rec, layer=layer, terr=terr, tops=tops, steps=steps,
                                              axes=axes, frame=frame, per=per, a_A=a,
                                              groups=_terrace_groups(t_rel))
        passed += [
            "(a)-(g) above were run on the ideal (bulk-truncated) sites before reconstruction",
            "(r1) displacements only in the five tabulated layers of complete dimer cells",
            "(r2) composition and atom count unchanged by the reconstruction",
            "(r3) every dimer (measured on the atoms) has the table's bond length and buckling",
            "(r4) one dimer-bond axis per terrace, normal to its back-bond axis: rotated by 90 deg "
            "across every a/4 step, not across a/2 steps (measured on the atoms)",
            "(r5) terrace interiors: no distance shorter than the table's shortest dimer bond; "
            "everywhere: no collision (>= 0.9 d_nn), no duplicate (assertion (b) criterion)"
            + (", in every configuration of the flip-flop ensemble" if rec.mirror_displacement_A
               is not None else ""),
            "(r6) bulk interior below the reconstructed layers unchanged and 4-coordinated"]
        e_axis_crystal = frame.to_crystal(np.eye(3)[e_ax])
        for s in steps:
            A, B = s["from_terrace"], s["to_terrace"]
            upper = B if s["delta_layers"] > 0 else A
            row = rec.metadata["terraces"][upper]["dimer_row_axis_crystal"]
            rot = {r["step"]: r["dimer_rows_rotated_90_deg"]
                   for r in recon_checks["step_rotation"]}
            s["reconstruction"] = dict(
                termination=termination,
                dimer_rows_rotated_90_deg=bool(rot[s["index"]]),
                dimer_bond_axis_from=rec.metadata["terraces"][A]["dimer_bond_axis_crystal"],
                dimer_bond_axis_to=rec.metadata["terraces"][B]["dimer_bond_axis_crystal"],
                upper_terrace=int(upper),
                step_type_zandvliet=step_edge_type(s["delta_layers"], row, e_axis_crystal),
                source="Zandvliet 2000 [ZANDVLIET2000] p. 594 (SA/SB), p. 600 (only DB double "
                       "steps observed); rotation measured on the built atoms, (r4)")
            b4, measured = _b4_reconstructed(rec, s, b4_ops[s["index"]], az,
                                             quarter=np.rint(rc / q).astype(np.int64),
                                             layer=layer, terr=terr, tops=tops, frame=frame, a_A=a)
            s["relation"]["model_assumption_B4"] = b4
            s["relation"]["reconstruction_relations"] = measured
            s["relation"]["model_assumption_B4_note"] = (
                "assertion (f) and the operations above are found on the IDEAL sites; "
                "reconstruction_relations says whether each operation fixing the beam also maps "
                "the reconstructed layers (measured on the displaced atoms, R1's printed "
                "precision 0.001 A)")
        rs = rec.ideal_positions_A + rec.displacement_A

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
        if rec is not None:
            terrace_map[-1].update(
                reconstruction=rec.metadata["terraces"][k],
                top_atom_height_A=float(rs[terr == k, 0].max()),
                top_height_note="top_height_A is the ideal top-layer plane (a/4 grid); the "
                                "reconstructed atoms lie below it (top_atom_height_A)")
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
        lattice=dict(a_A=a, a_label=lattice_parameter_label, basis="constants.DIAMOND_BASIS (SM02)",
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
            dimer_reconstruction=(
                dict(value="not enabled", status="NOT ENABLED: bulk termination requested "
                     "(ASSUMPTION B3); sourced reconstructions available: "
                     + ", ".join(recon.RECONSTRUCTIONS) + " (reconstruction.py)")
                if rec is None else dict(value=termination, status="ENABLED",
                                         **{k: v for k, v in rec.metadata.items()
                                            if k != "terraces"},
                                         checks=recon_checks)),
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
                          terrace_index=terr, crystal_origin_slab_A=origin, metadata=metadata,
                          reconstruction=rec)
