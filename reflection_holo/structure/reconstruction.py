"""Si(001) dimer reconstructions on the terraces of the staircase builder (spec docs/05 section 4.2).

Source (the only one used for any displacement here): A. Ramstad, G. Brocks and P. J. Kelly,
"Theoretical study of the Si(100) surface reconstruction", Phys. Rev. B 51, 14504-14523 (1995)
[RAMSTAD1995], called R1 below: Table III (p. 14516; p(2x1)s and p(2x1)a) and Table IV (p. 14517;
p(2x2) and c(4x2)), SECTION_READ, transcribed in docs/agent_reports/L7_surface_realism.md section 1.4;
every one of the 160 entries was checked against the rendered pages by the reviewer E6
(docs/agent_reports/E6_literature_review.md section 1; E6 section 8 "exactly as transcribed").
tests/structure/test_si001_reconstruction.py re-parses the L7 table and compares it with the tables
below entry by entry.

R1's frame (Table III caption): ideal positions R_klm = (k sqrt2, l sqrt2, m) a/4 with a = 5.431 A;
x along the dimer bond, y along the dimer row, z outward (z < 0 into the bulk); displacements in A
for the five outermost layers (m = 0 .. -4); layers 6 and deeper stay at bulk sites (R1 relaxed five
layers per side). In Table III all dy = 0 (R1: "only of order 10^-5 A").

Mapping onto the repository lattice (DERIVED_HERE; lattice.py, diamond sites in a/4 units):
* the top layer of a terrace is crystal layer n3; its bonds to the layer below project on the
  back-bond axis b_axis = [1,-1,0] (n3 even) or [1,1,0] (n3 odd) (``si001.
  backbond_axis_of_crystal_layer``). R1's layer-2 atoms sit at l = 1, i.e. one R1 unit
  u = a sqrt2 / 4 along y from the top-layer atoms, so R1's y (the dimer row) is the back-bond axis
  and R1's x (the dimer bond) is the other <110> axis. The dimer-row direction therefore follows the
  top layer's parity: it rotates by 90 degrees across every a/4 step and not across an a/2 step, as
  observed (Zandvliet, Rev. Mod. Phys. 72, 593 (2000) [ZANDVLIET2000], p. 594; L7 section 1.2);
* x_hat_R = d_vec / sqrt2 with d_vec = [1,1,0] or [1,-1,0] (sign convention: positive crystal-x
  component, the same for every terrace, so that terraces of the same orientation carry the same
  buckling orientation); y_hat_R = [001] x x_hat_R (right-handed, z = outward normal [001]);
* an atom at integer a/4 site n has R1 indices k = (n - n_O).d_vec / 2, l = (n - n_O).b_vec / 2,
  m = n3 - n3_top (integers for every diamond site; asserted), relative to a top-layer origin atom O
  chosen per terrace (``_choose_origin``). Tested on the R1 index set: every Table III/IV (k, l, m)
  is a diamond site in this map.

Periodicity of the displacement pattern in R1 units (k, l) (DERIVED_HERE from the cells of R1's
tables; L7 1.4 "Cell vectors"): p(2x1) (4, 0), (0, 2); p(2x2) (4, 0), (0, 4); c(4x2) primitive (4, 2),
(0, 4) (neighbouring dimer rows in antiphase). Table lookup: p(2x1) (k mod 4, l mod 2, m); p(2x2)
(k mod 4, l mod 4, m); c(4x2) with j = floor(k / 4): (k - 4 j, (l - 2 j) mod 4, m).

Dimer cells and step edges: every terrace is cut into the p(2x1) cells of R1 Table III, one dimer
(k = 4K and 4K + 2, l = 2L, m = 0) and the eight atoms of layers 2-5 listed with it
(k in [4K, 4K + 3], l in [2L, 2L + 1]). A cell is COMPLETE if both dimer atoms are top-layer atoms of
the terrace (partners are searched through the periodic boundaries of the builder's cell). Atoms of
complete cells take the tabulated displacement; atoms of INCOMPLETE cells (at a step edge whose
dimer partner is on the other side of the riser, which is unavoidable for step edges along <100>)
keep their bulk sites: ASSUMPTION, an extension of the builder's "step-riser relaxation none" (R1
gives no geometry for an unpaired edge atom, and none is invented). Their number is recorded.

Room temperature (L7 section 1.2): the dimers flip-flop; c(4x2) order appears only below 205 +- 3 K
(Shirasawa, Mizuno, Tochihara, JPS 2006, p. 865, SECTION_READ in L7). R1's geometries are T = 0 LDA
geometries (R1 p. 14518: "should only be compared with geometries determined experimentally at low
temperature"). Options:
* "p(2x1)s", "p(2x1)a", "p(2x2)", "c(4x2)": the static geometry of the named table (sourced; using
  a T = 0 geometry for a room-temperature specimen is an ASSUMPTION, model_assumptions B3);
* "p(2x1)a flip-flop ensemble": MODEL CHOICE, NOT A SOURCE (ASSUMPTION B37). Each dimer cell takes,
  independently and with probability 1/2, either the p(2x1)a displacements of Table III or their
  mirror image through the cell's (dimer-bond-normal) mid-plane x_R = u, i.e. the buckling reversed:
  d'(k, l, m) = diag(-1, 1, 1) d((2 - k) mod 4, l, m). The signs are drawn per realisation from the
  engine's seeded generator (forward.dimer_ensemble), so the elastic average is an ensemble average
  taken after squaring, like frozen phonons. Not modelled: correlations between neighbouring dimers
  (R4 reports 2-D Ising critical behaviour of the order-disorder transition, so the real room-
  temperature surface has short-range antiphase correlation along the rows), the subsurface
  relaxation of a mixed neighbourhood (each subsurface atom follows the state of its own cell), and
  the time scale of the flip-flop against the exposure.

This module only reads the ideal sites; every tolerance is stated here.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np

from .checks import POSITION_TOL_A, StructureAssertionError
from .lattice import neighbour_pairs

SOURCE = ("Ramstad, Brocks and Kelly, Phys. Rev. B 51, 14504 (1995) [RAMSTAD1995], Table III "
          "(p. 14516) and Table IV (p. 14517), SECTION_READ; transcribed in docs/agent_reports/"
          "L7_surface_realism.md section 1.4 and checked entry by entry by E6")
A_R1_A = 5.431                     # R1's lattice parameter (Table III caption)
RECONSTRUCTED_DEPTH = 5            # R1 tabulates layers m = 0 .. -4
TABLE_PRECISION_A = 0.001          # R1 prints the displacements to 0.001 A
DIMER_SEARCH_CUTOFF_A = 3.0        # top-layer pairs closer than this are dimers (unpaired 3.84 A)
RELATION_TOL_A = TABLE_PRECISION_A + 1e-9   # two independently rounded entries differ <= 0.001 A

P2X1S, P2X1A, P2X2, C4X2 = "p(2x1)s", "p(2x1)a", "p(2x2)", "c(4x2)"
FLIPFLOP = "p(2x1)a flip-flop ensemble"
STATIC_RECONSTRUCTIONS = (P2X1S, P2X1A, P2X2, C4X2)
RECONSTRUCTIONS = STATIC_RECONSTRUCTIONS + (FLIPFLOP,)
FLIPFLOP_LABEL = ("ASSUMPTION B37: p(2x1)a flip-flop ensemble, a MODEL CHOICE and not a source: "
                  "each dimer cell of R1 Table III takes the p(2x1)a displacements or their mirror "
                  "image (buckling reversed) with probability 1/2, independently, drawn per "
                  "realisation from the seeded generator; geometry " + SOURCE)
STATIC_LABEL = ("SECTION_READ geometry: " + SOURCE + "; T = 0 LDA geometry used for the specimen "
                "temperature: ASSUMPTION (model_assumptions B3)")
EDGE_RULE = ("ASSUMPTION (extends 'step-riser relaxation none'): atoms of a dimer cell whose two "
             "dimer atoms are not both top-layer atoms of the terrace (step edges) keep their bulk "
             "sites; R1 gives no geometry for an unpaired edge atom and none is invented")

# R1 Table III (p. 14516): (k, l, m) -> (p(2x1)s dx, dz, p(2x1)a dx, dz), A; dy = 0.
_TABLE_III = {
    (0, 0, 0): (0.805, -0.524, 1.162, -0.921),
    (2, 0, 0): (-0.805, -0.524, -0.534, -0.213),
    (0, 1, -1): (0.075, -0.141, 0.066, -0.141),
    (2, 1, -1): (-0.075, -0.141, -0.099, -0.112),
    (1, 1, -2): (0.000, -0.216, 0.031, -0.240),
    (3, 1, -2): (0.000, 0.005, -0.025, -0.003),
    (1, 0, -3): (0.000, -0.139, -0.013, -0.155),
    (3, 0, -3): (0.000, 0.002, -0.005, 0.002),
    (0, 0, -4): (-0.022, -0.040, -0.042, -0.044),
    (2, 0, -4): (0.022, -0.040, 0.022, -0.040),
}
# R1 Table IV (p. 14517): (k, l, m) -> (p(2x2) dx, dy, dz, c(4x2) dx, dy, dz), A.
_TABLE_IV = {
    (0, 0, 0): (0.992, 0.000, -0.832, 0.989, 0.000, -0.789),
    (2, 0, 0): (-0.688, 0.000, -0.094, -0.685, 0.000, -0.055),
    (0, 2, 0): (0.675, 0.000, -0.076, 0.675, 0.000, -0.045),
    (2, 2, 0): (-1.010, 0.000, -0.829, -1.001, 0.000, -0.788),
    (0, 1, -1): (0.105, 0.119, -0.101, 0.108, 0.120, -0.079),
    (2, 1, -1): (-0.118, -0.112, -0.109, -0.120, -0.117, -0.086),
    (0, 3, -1): (0.105, -0.118, -0.101, 0.108, -0.119, -0.079),
    (2, 3, -1): (-0.118, 0.113, -0.109, -0.120, 0.117, -0.086),
    (1, 1, -2): (-0.011, 0.001, -0.237, -0.009, 0.001, -0.223),
    (3, 1, -2): (-0.003, 0.002, 0.050, -0.003, 0.020, 0.066),
    (1, 3, -2): (-0.011, 0.000, -0.237, -0.009, 0.000, -0.223),
    (3, 3, -2): (-0.003, -0.002, 0.050, -0.003, -0.020, 0.066),
    (1, 0, -3): (0.024, 0.000, -0.160, 0.006, 0.000, -0.153),
    (3, 0, -3): (0.037, 0.000, 0.037, -0.005, 0.000, 0.069),
    (1, 2, -3): (-0.031, 0.000, -0.164, -0.011, 0.000, -0.155),
    (3, 2, -3): (-0.048, 0.000, 0.034, -0.006, 0.000, 0.028),
    (0, 0, -4): (-0.012, 0.000, -0.039, -0.041, 0.000, -0.023),
    (2, 0, -4): (0.066, 0.000, -0.030, 0.039, 0.000, -0.040),
    (0, 2, -4): (-0.074, 0.000, -0.031, -0.045, 0.000, -0.038),
    (2, 2, -4): (0.007, 0.000, -0.041, 0.037, 0.000, -0.023),
}


def _tables() -> dict:
    out = {P2X1S: {}, P2X1A: {}, P2X2: {}, C4X2: {}}
    for key, (sx, sz, ax, az) in _TABLE_III.items():
        out[P2X1S][key] = (sx, 0.0, sz)
        out[P2X1A][key] = (ax, 0.0, az)
    for key, v in _TABLE_IV.items():
        out[P2X2][key] = tuple(v[:3])
        out[C4X2][key] = tuple(v[3:])
    return out


TABLES = _tables()
TABLE_OF = {P2X1S: P2X1S, P2X1A: P2X1A, P2X2: P2X2, C4X2: C4X2, FLIPFLOP: P2X1A}
# periodicity of the displacement pattern in R1 units (k, l), rows = lattice vectors
PATTERN_LATTICE = {P2X1S: ((4, 0), (0, 2)), P2X1A: ((4, 0), (0, 2)), FLIPFLOP: ((4, 0), (0, 2)),
                   P2X2: ((4, 0), (0, 4)), C4X2: ((4, 2), (0, 4))}
# the dimers of each table: (first atom (k, l), second atom (k, l)), m = 0
DIMERS_OF = {P2X1S: (((0, 0), (2, 0)),), P2X1A: (((0, 0), (2, 0)),),
             P2X2: (((0, 0), (2, 0)), ((0, 2), (2, 2))), C4X2: (((0, 0), (2, 0)), ((0, 2), (2, 2)))}
# values printed by R1 (text pp. 14516-14517 and Fig. 18; L7 section 1.2), per dimer of DIMERS_OF
PRINTED_R1 = {
    P2X1S: dict(dimer_bond_A=(2.23,), buckling_deg=(None,), bond_digits=2, angle_digits=None),
    P2X1A: dict(dimer_bond_A=(2.26,), buckling_deg=(18.3,), bond_digits=2, angle_digits=1),
    P2X2: dict(dimer_bond_A=(2.28, 2.28), buckling_deg=(18.9, 19.3), bond_digits=2,
               angle_digits=1),
    C4X2: dict(dimer_bond_A=(2.29, 2.29), buckling_deg=(18.7, 18.9), bond_digits=2,
               angle_digits=1),
}
PRINTED_R1_LOCATOR = ("R1 pp. 14516-14517 and Fig. 18 (L7 section 1.2): p(2x1)s dimer 2.23 A; "
                      "p(2x1)a 2.26 A, 18.3 deg; p(2x2) 2.28 A, 18.9 and 19.3 deg; c(4x2) 2.29 A, "
                      "18.7 and 18.9 deg")


class ReconstructionError(ValueError):
    """A reconstruction cannot be built on the requested cell (refused, not approximated)."""


def _reduce(name: str, k, l, m):
    """Table key of R1 indices (vectorised over numpy int arrays)."""
    t = TABLE_OF[name]
    k = np.asarray(k)
    l = np.asarray(l)
    if t in (P2X1S, P2X1A):
        return np.mod(k, 4), np.mod(l, 2), np.asarray(m)
    if t == P2X2:
        return np.mod(k, 4), np.mod(l, 4), np.asarray(m)
    j = np.floor_divide(k, 4)
    return k - 4 * j, np.mod(l - 2 * j, 4), np.asarray(m)


def table_displacements(name: str, k, l, m, mirrored: bool = False) -> np.ndarray:
    """R1 displacements (dx, dy, dz) in A in R1's frame for integer indices (arrays); ``mirrored``
    gives the buckling-reversed state of the flip-flop model (module docstring). Raises if an index
    triple is not a site of the table's cell (a bookkeeping error, never approximated)."""
    t = TABLE_OF[name]
    if mirrored and t != P2X1A:
        raise ValueError("only the p(2x1)a flip-flop model has a mirrored state")
    kk, ll, mm = _reduce(name, k, l, m)
    if mirrored:
        kk = np.mod(2 - kk, 4)
    tab = TABLES[t]
    out = np.zeros((kk.size, 3))
    for i, key in enumerate(zip(kk.ravel().tolist(), ll.ravel().tolist(), mm.ravel().tolist())):
        v = tab.get(key)
        if v is None:
            raise StructureAssertionError(f"R1 index {key} (reduced) is not a site of the "
                                          f"{t} table: frame bookkeeping error")
        out[i] = v
    if mirrored:
        out[:, 0] = -out[:, 0]
    return out


def reference_dimers(name: str, a_A: float) -> list[dict]:
    """Dimer bond length and buckling angle of each dimer of the table, computed from the table on
    the ideal lattice with lattice parameter a_A (DERIVED_HERE; the builder's dimers must equal
    these, and they are compared with R1's printed values in the tests)."""
    t = TABLE_OF[name]
    u = a_A * np.sqrt(2.0) / 4.0
    out = []
    for (k1, l1), (k2, l2) in DIMERS_OF[t]:
        d1 = np.array(TABLES[t][(k1, l1, 0)])
        d2 = np.array(TABLES[t][(k2, l2, 0)])
        r = np.array([(k2 - k1) * u, (l2 - l1) * u, 0.0]) + d2 - d1
        horiz = float(np.hypot(r[0], r[1]))
        out.append(dict(atoms=[[k1, l1, 0], [k2, l2, 0]], bond_A=float(np.linalg.norm(r)),
                        buckling_deg=float(np.degrees(np.arctan2(abs(r[2]), horiz))),
                        down_atom=[k1, l1, 0] if d1[2] < d2[2] else [k2, l2, 0]))
    return out


def rounding_bound(name: str, a_A: float) -> list[dict]:
    """Worst-case effect of R1's 0.001 A rounding of the four tabulated displacements (dx and dz of
    both dimer atoms) and of the lattice-parameter difference |a_A - 5.431 A| on each dimer's bond
    length and buckling angle (first-order propagation, DERIVED_HERE). Used to compare the built
    dimers with R1's printed bond lengths and angles, which are themselves rounded."""
    out = []
    for ref in reference_dimers(name, a_A):
        b = ref["bond_A"]
        th = np.radians(ref["buckling_deg"])
        h, v = b * np.cos(th), b * np.sin(th)
        dh = 2 * TABLE_PRECISION_A / 2 + abs(a_A - A_R1_A) * np.sqrt(2.0) / 2.0
        dv = 2 * TABLE_PRECISION_A / 2
        out.append(dict(bond_A=float((h * dh + v * dv) / b),
                        buckling_deg=float(np.degrees((v * dh + h * dv) / b ** 2))))
    return out


# --------------------------------------------------------------------------------------------------
# Construction on the builder's terraces
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class ReconstructionRecord:
    """The reconstructed layers of one built structure (slab frame, angstrom).

    ideal_positions_A   bulk-lattice sites (the truncation checked by assertions (a) to (g))
    displacement_A      displacement applied to every atom (zero outside complete cells); for the
                        flip-flop ensemble this is the table state of every cell
    mirror_displacement_A  flip-flop only: the buckling-reversed state of every atom's cell
    cell_index          (N,) index 0 .. n_cells - 1 of the complete dimer cell of each atom, -1
                        for atoms at bulk sites
    n_cells             number of complete dimer cells (independent flip-flop variables)
    """
    name: str
    ideal_positions_A: np.ndarray
    displacement_A: np.ndarray
    mirror_displacement_A: np.ndarray | None
    cell_index: np.ndarray
    n_cells: int
    metadata: dict

    def positions_for(self, flips) -> np.ndarray:
        """Positions of one flip-flop configuration: flips[c] = 1 reverses the buckling of cell
        c (mirror state), 0 keeps the Table III state. Static reconstructions accept None only."""
        if self.mirror_displacement_A is None:
            if flips is not None:
                raise ValueError(f"{self.name} is static: no flip-flop configuration")
            return self.ideal_positions_A + self.displacement_A
        f = np.asarray(flips)
        if f.shape != (self.n_cells,) or not np.all((f == 0) | (f == 1)):
            raise ValueError(f"flips must be {self.n_cells} values 0 or 1")
        use = np.zeros(len(self.cell_index), bool)
        inc = self.cell_index >= 0
        use[inc] = f[self.cell_index[inc]] == 1
        disp = np.where(use[:, None], self.mirror_displacement_A, self.displacement_A)
        return self.ideal_positions_A + disp


def _keys(n: np.ndarray) -> np.ndarray:
    off = 1 << 20
    n = np.asarray(n, np.int64) + off
    if n.size and (n.min() < 0 or n.max() >= 2 * off):
        raise ValueError("site coordinates exceed the key range")
    return (n[..., 0] << 42) | (n[..., 1] << 21) | n[..., 2]


def _wrap_quarter(n: np.ndarray, frame, origin, a_A: float, L) -> np.ndarray:
    """Integer a/4 crystal sites wrapped into the builder's periodic (y, z) window."""
    q = a_A / 4.0
    r = frame.to_slab(np.asarray(n, float) * q) + origin
    for ax in (1, 2):
        r[:, ax] = np.mod(r[:, ax], L[ax])
        r[np.abs(r[:, ax] - L[ax]) < 1e-6, ax] = 0.0
    return np.rint(frame.to_crystal(r - origin) / q).astype(np.int64)


def dimer_frame(n3_top: int):
    """(d_vec, b_vec) in a/4 crystal units for a top layer n3 (module docstring)."""
    from .si001 import backbond_axis_of_crystal_layer
    b_axis = backbond_axis_of_crystal_layer(n3_top)
    d_vec = np.array([1, 1, 0]) if tuple(b_axis) == (1, -1, 0) else np.array([1, -1, 0])
    b_vec = np.cross(np.array([0, 0, 1]), d_vec)
    return d_vec.astype(np.int64), b_vec.astype(np.int64)


def _kl(dn: np.ndarray, d_vec, b_vec):
    kd = dn[:, 0] * d_vec[0] + dn[:, 1] * d_vec[1]
    lb = dn[:, 0] * b_vec[0] + dn[:, 1] * b_vec[1]
    if np.any(kd % 2) or np.any(lb % 2):
        raise StructureAssertionError("R1 indices are not integers: frame bookkeeping error")
    return kd // 2, lb // 2


def _in_lattice(v, basis) -> bool:
    B = np.array(basis, float).T
    c = np.linalg.solve(B, np.asarray(v, float))
    return bool(np.all(np.abs(c - np.rint(c)) < 1e-9))


def _pattern_vector(vec_slab, frame, a_A, d_vec, b_vec):
    q = a_A / 4.0
    nf = frame.to_crystal(np.asarray(vec_slab, float)) / q
    n = np.rint(nf).astype(np.int64)
    if np.max(np.abs(nf - n)) > 1e-6:
        raise StructureAssertionError("periodic vector is not a lattice translation")
    k, l = _kl(n[None, :], d_vec, b_vec)
    return int(k[0]), int(l[0])


def _complete_cells(n_top, key_top, n_O, d_vec, b_vec, frame, origin, a_A, L):
    """For a candidate origin: complete-cell first atoms (indices into n_top) and partner indices."""
    k, _ = _kl(n_top - n_O, d_vec, b_vec)
    first = np.nonzero(np.mod(k, 4) == 0)[0]
    partner_sites = _wrap_quarter(n_top[first] + 2 * d_vec, frame, origin, a_A, L)
    pk = _keys(partner_sites)
    order = np.argsort(key_top)
    pos = np.searchsorted(key_top[order], pk)
    pos = np.clip(pos, 0, len(order) - 1)
    found = key_top[order][pos] == pk
    return first[found], order[pos[found]]


def build_reconstruction(name: str, *, ideal_positions_A, quarter, layer, terrace, tops, c0,
                         frame, origin, a_A, L, s_ax, e_ax, groups) -> ReconstructionRecord:
    """Displacements of the reconstruction ``name`` on the built terraces (module docstring).

    quarter: (N, 3) integer a/4 crystal coordinates of the ideal sites; layer, terrace: builder
    arrays; tops: top layer index per terrace; c0: crystal layer offset (n3 = layer + c0);
    groups: lists of terrace indices forming one physical terrace (terraces 0 and n-1 joined across
    the periodic cell edge when their heights are equal, or the single terrace of a flat cell)."""
    if name not in RECONSTRUCTIONS:
        raise ValueError(f"unknown reconstruction {name!r}")
    t = TABLE_OF[name]
    pos = np.asarray(ideal_positions_A, float)
    N = pos.shape[0]
    disp = np.zeros((N, 3))
    mdisp = np.zeros((N, 3)) if name == FLIPFLOP else None
    cell = np.full(N, -1, np.int64)
    first_atom_of_cell: list[int] = []
    terr_records = {}
    n_cells = 0
    lat = PATTERN_LATTICE[name]
    for g in groups:
        top = int(tops[g[0]])
        if any(int(tops[k]) != top for k in g):
            raise StructureAssertionError("terrace group with different top layers")
        n3 = top + int(c0)
        d_vec, b_vec = dimer_frame(n3)
        # periodicity of the pattern along the edge axis (and along the staircase axis if the group
        # spans the periodic cell edge)
        need = [("edge", e_ax)]
        wrapped_s = len(g) > 1 or len(tops) == 1
        if wrapped_s:
            need.append(("staircase", s_ax))
        for what, ax in need:
            v = np.zeros(3)
            v[ax] = L[ax]
            kl = _pattern_vector(v, frame, a_A, d_vec, b_vec)
            if not _in_lattice(kl, lat):
                raise ReconstructionError(
                    f"{name}: the periodic cell length along the {what} axis "
                    f"({'y' if ax == 1 else 'z'}, {L[ax]:.6f} A = ({kl[0]}, {kl[1]}) in R1 units "
                    f"along the dimer bond and the dimer row of terrace(s) {list(g)}) is not a "
                    f"lattice vector of the {name} pattern (lattice {lat} in R1 units): the "
                    f"reconstruction would be discontinuous at the periodic boundary. Choose a "
                    f"cell length that is a multiple of the reconstruction period along that axis.")
        sel_g = np.isin(terrace, g)
        top_idx = np.nonzero(sel_g & (layer == top))[0]
        n_top = quarter[top_idx]
        key_top = _keys(n_top)
        # origin candidates: the top atom with the smallest (s, e), and the registry shifted by two
        # R1 units along the dimer bond; the one with more complete cells is used (tie: the first)
        ps = pos[top_idx]
        o0 = int(np.lexsort((np.round(ps[:, e_ax], 6), np.round(ps[:, s_ax], 6)))[0])
        best = None
        for shift in (0, 2):
            n_O = n_top[o0] + shift * d_vec
            f_idx, p_idx = _complete_cells(n_top, key_top, n_O, d_vec, b_vec, frame, origin, a_A,
                                           L)
            if best is None or len(f_idx) > len(best[1]):
                best = (n_O, f_idx, p_idx, shift)
        n_O, f_idx, p_idx, shift = best
        if len(f_idx) == 0:
            raise ReconstructionError(
                f"{name}: terrace(s) {list(g)} carry no complete dimer (top layer too narrow): "
                f"refused")
        # cell of every atom of the group within the reconstructed depth
        sub = np.nonzero(sel_g & (layer <= top) & (layer >= top - (RECONSTRUCTED_DEPTH - 1)))[0]
        dn = quarter[sub] - n_O
        k, l = _kl(dn, d_vec, b_vec)
        m = layer[sub] - top
        K = np.floor_divide(k, 4)
        Lc = np.floor_divide(l, 2)
        first_sites = n_O[None, :] + (4 * K)[:, None] * d_vec[None, :] \
            + (2 * Lc)[:, None] * b_vec[None, :]
        first_sites[:, 2] = n_O[2]
        fk = _keys(_wrap_quarter(first_sites, frame, origin, a_A, L))
        complete_keys = key_top[f_idx]
        order = np.argsort(complete_keys)
        loc = np.clip(np.searchsorted(complete_keys[order], fk), 0, max(len(order) - 1, 0))
        ok = complete_keys[order][loc] == fk
        cell_local = order[loc]                      # index into f_idx
        ids = np.full(len(sub), -1, np.int64)
        ids[ok] = n_cells + cell_local[ok]
        cell[sub] = ids
        first_atom_of_cell.extend(top_idx[f_idx].tolist())
        sub_ok = sub[ok]
        dxyz = table_displacements(name, k[ok], l[ok], m[ok])
        d_hat = frame.to_slab(d_vec / np.sqrt(2.0))
        b_hat = frame.to_slab(b_vec / np.sqrt(2.0))
        x_hat = frame.to_slab(np.array([0.0, 0.0, 1.0]))
        basis = np.stack([d_hat, b_hat, x_hat])        # rows: slab vectors of R1 x, y, z
        disp[sub_ok] = dxyz @ basis
        if mdisp is not None:
            mdisp[sub_ok] = table_displacements(name, k[ok], l[ok], m[ok], mirrored=True) @ basis
        n_top_all = len(top_idx)
        n_paired = 2 * len(f_idx)
        for kk in g:
            terr_records[int(kk)] = dict(
                group=[int(v) for v in g], top_layer_index=top, crystal_layer_n3=n3,
                dimer_bond_axis_crystal=d_vec.tolist(), dimer_row_axis_crystal=b_vec.tolist(),
                dimer_bond_axis_slab=d_hat.tolist(), dimer_row_axis_slab=b_hat.tolist(),
                origin_site_quarter=[int(v) for v in n_O], registry_shift_R1_units=int(shift),
                complete_dimer_cells=int(len(f_idx)), top_layer_atoms=int(n_top_all),
                unpaired_top_atoms_at_bulk_sites=int(n_top_all - n_paired),
                atoms_at_bulk_sites_within_reconstructed_depth=int(np.count_nonzero(~ok)),
                dimer_row_angle_to_beam_deg=float(np.degrees(np.arctan2(abs(b_hat[1]),
                                                                        abs(b_hat[2])))))
        n_cells += len(f_idx)
    meta = dict(name=name, table=t, source=SOURCE,
                label=FLIPFLOP_LABEL if name == FLIPFLOP else STATIC_LABEL,
                frame_rule="R1 x = dimer bond = the <110> axis normal to the top layer's back-bond "
                           "axis, sign: positive crystal-x component; R1 y = [001] x R1 x (dimer "
                           "row, parallel to the back-bond axis); R1 z = outward normal [001]",
                reconstructed_depth_layers=RECONSTRUCTED_DEPTH, edge_rule=EDGE_RULE,
                pattern_lattice_R1_units=[list(v) for v in lat],
                reference_dimers=reference_dimers(name, a_A),
                printed_R1=dict(PRINTED_R1[t], locator=PRINTED_R1_LOCATOR),
                n_complete_cells=int(n_cells), terraces=terr_records,
                max_displacement_A=float(np.max(np.linalg.norm(disp, axis=1))) if N else 0.0,
                lattice_parameter_note=(
                    f"R1's displacements (A, computed at a = {A_R1_A} A) are added to the sites of "
                    f"the repository lattice a = {a_A} A (relative difference "
                    f"{abs(a_A - A_R1_A) / A_R1_A:.1e}; E6 n3)"),
                first_atom_of_cell_sha256=hashlib.sha256(
                    np.asarray(first_atom_of_cell, "<i8").tobytes()).hexdigest())
    return ReconstructionRecord(name=name, ideal_positions_A=pos.copy(), displacement_A=disp,
                                mirror_displacement_A=mdisp, cell_index=cell, n_cells=int(n_cells),
                                metadata=meta)


# --------------------------------------------------------------------------------------------------
# Measurements on built atoms (used by the builder's assertions and by the tests)
# --------------------------------------------------------------------------------------------------
def measure_dimers(positions_A, top_mask, terrace, periodic_lengths_A, frame,
                   cutoff_A: float = DIMER_SEARCH_CUTOFF_A) -> dict:
    """Dimers identified geometrically on built atoms: pairs of top-layer atoms of the same terrace
    (``terrace``: terrace index, or terrace-group id when terraces 0 and n-1 are one terrace across
    the periodic edge) closer than ``cutoff_A`` under the periodic boundaries. Returns arrays (i, j, bond_A,
    buckling_deg, in-plane crystal axis key per pair) and the per-terrace axis set."""
    pos = np.asarray(positions_A, float)
    idx = np.nonzero(np.asarray(top_mask))[0]
    i, j, d, vec = neighbour_pairs(pos[idx], periodic_lengths_A, cutoff_A)
    keep = (i < j) & (np.asarray(terrace)[idx][i] == np.asarray(terrace)[idx][j])
    i, j, d, vec = idx[i[keep]], idx[j[keep]], d[keep], vec[keep]
    horiz = np.hypot(vec[:, 1], vec[:, 2])
    buck = np.degrees(np.arctan2(np.abs(vec[:, 0]), horiz))
    vc = frame.to_crystal(vec)
    axis = np.where(np.sign(vc[:, 0]) * np.sign(vc[:, 1]) > 0, 0, 1)   # 0: [110], 1: [1-10]
    ang = np.degrees(np.arctan2(np.abs(vc[:, 1]), np.abs(vc[:, 0])))
    per_terrace = {}
    for t in np.unique(np.asarray(terrace)[idx]):
        sel = np.asarray(terrace)[i] == t
        per_terrace[int(t)] = sorted({("[1,1,0]", "[1,-1,0]")[a] for a in axis[sel]})
    counts = np.bincount(np.concatenate([i, j]), minlength=len(pos)) if len(i) else \
        np.zeros(len(pos), np.int64)
    return dict(i=i, j=j, bond_A=d, buckling_deg=buck, axis=axis, in_plane_angle_deg=ang,
                per_terrace_axes=per_terrace, partners_per_atom=counts)


COLLISION_FRACTION_OF_DNN = 0.9   # numerical criterion (not a sourced bound), see pair_distance_minima


def pair_distance_minima(rec: ReconstructionRecord, group_of_atom, periodic_lengths_A,
                         cutoff_A: float = 3.0) -> dict:
    """Minimum interatomic distances of the reconstructed structure, split into
    * INTERIOR pairs (both atoms in complete dimer cells of the same terrace group): these
      neighbourhoods reproduce the source's own periodic geometry, so no distance may be shorter
      than the table's shortest dimer bond (asserted exactly by the builder, (r5));
    * RISER/EDGE pairs (any other pair: atoms of two terraces at a riser, or an atom at a bulk site
      next to a reconstructed one): each terrace carries its own table and the riser is not
      relaxed (ASSUMPTION), so a bond across the boundary can be compressed; these are recorded
      and asserted only against the collision criterion COLLISION_FRACTION_OF_DNN x d_nn.
    For the flip-flop ensemble the minima are taken over EVERY configuration: a pair distance
    depends only on the states of the pair's own cells (two states if they share a cell, four
    otherwise), so the minimum over those states is exact. Pairs are searched within ``cutoff_A`` +
    twice the largest displacement of the ideal sites."""
    ideal = rec.ideal_positions_A
    states = [rec.displacement_A] + ([rec.mirror_displacement_A]
                                     if rec.mirror_displacement_A is not None else [])
    dmax = float(max(np.max(np.linalg.norm(d, axis=1)) for d in states)) if len(ideal) else 0.0
    i, j, _, vec = neighbour_pairs(ideal, periodic_lengths_A, cutoff_A + 2 * dmax)
    keep = i < j
    i, j, vec = i[keep], j[keep], vec[keep]
    c = rec.cell_index
    same = (c[i] == c[j]) & (c[i] >= 0)
    g = np.asarray(group_of_atom)
    interior = (c[i] >= 0) & (c[j] >= 0) & (g[i] == g[j])
    best = np.full(len(i), np.inf)
    for si in range(len(states)):
        for sj in range(len(states)):
            dist = np.linalg.norm(vec + states[sj][j] - states[si][i], axis=1)
            allowed = ~same | (si == sj)
            best = np.where(allowed, np.minimum(best, dist), best)
    out = dict(interior_min_A=float(best[interior].min()) if np.any(interior) else None,
               riser_edge_min_A=float(best[~interior].min()) if np.any(~interior) else None,
               n_configurations=("all 2^n_cells" if len(states) == 2 else 1))
    return out, (i, j, best, interior)


def assert_no_collision(rec: ReconstructionRecord, group_of_atom, periodic_lengths_A,
                        a_A: float) -> dict:
    """(r5) Interior pairs: nothing shorter than the table's shortest dimer bond (exact, tolerance
    POSITION_TOL_A). All pairs: nothing shorter than COLLISION_FRACTION_OF_DNN x d_nn (a stated
    numerical criterion: a bond compressed by more than 10 % of d_nn, 0.11 A shorter than the
    shortest Si-Si bond in R1's geometries, is treated as a collision and refused rather than
    passed to the engine). Returns the record, including the riser/edge compressions."""
    d_nn = a_A * np.sqrt(3.0) / 4.0
    shortest = min(r["bond_A"] for r in reference_dimers(rec.name, a_A))
    m, (i, j, best, interior) = pair_distance_minima(rec, group_of_atom, periodic_lengths_A)
    if m["interior_min_A"] is not None and m["interior_min_A"] < shortest - POSITION_TOL_A:
        raise StructureAssertionError(
            f"(r5) terrace interior: two atoms {m['interior_min_A']:.6f} A apart, shorter than the "
            f"{rec.name} table's own shortest distance {shortest:.6f} A")
    floor = COLLISION_FRACTION_OF_DNN * d_nn
    allmin = min(v for v in (m["interior_min_A"], m["riser_edge_min_A"]) if v is not None)
    if allmin < floor:
        k = int(np.argmin(best))
        raise StructureAssertionError(
            f"(r5) collision: atoms {int(i[k])} and {int(j[k])} come {allmin:.6f} A apart "
            f"(below {COLLISION_FRACTION_OF_DNN} d_nn = {floor:.6f} A)")
    comp = (~interior) & (best < shortest - POSITION_TOL_A)
    m.update(table_shortest_distance_A=shortest, collision_floor_A=floor,
             riser_edge_pairs_shorter_than_table_shortest=int(np.count_nonzero(comp)),
             riser_edge_largest_compression_of_dnn=(float(1.0 - best[comp].min() / d_nn)
                                                    if np.any(comp) else 0.0),
             rule=("interior pairs (both atoms in complete cells of one terrace): >= the table's "
                   "shortest dimer bond, exact; every pair (every flip-flop configuration): >= "
                   f"{COLLISION_FRACTION_OF_DNN} d_nn (numerical collision criterion). Bonds "
                   "across a riser or next to an edge atom at its bulk site may be compressed "
                   "below the table's shortest bond: artefact of 'step-riser relaxation none' "
                   "(ASSUMPTION), recorded here"))
    return m



def reconstruction_relation(rec: ReconstructionRecord, *, quarter, layer, terrace, tops, frame,
                            A: int, B: int, M, t_crystal_A, a_A: float, state_A: int = 0,
                            state_B: int = 0) -> dict:
    """Does r -> M r + t (an operation of assertion (f), found on the IDEAL sites) also map the
    reconstructed layers of terrace A onto those of terrace B, up to an in-plane translation of
    B's pattern? (For the specular beam an in-plane translation does not matter: only t . n_hat
    enters exp(-i (k_out - k_in) . t), model_assumptions B4.) Measured on the displaced atoms: every
    atom of a complete cell of A is mapped by M r + t onto a site of B; M times its displacement is
    compared with the displacement that B's atoms of the same pattern class carry, after a
    translation (k0, l0) of B's pattern (even R1 units: lattice translations of the top layer).
    B's classes are read from B's atoms (``state_B`` = 1: B's buckling-reversed flip-flop state).
    Holds if the largest difference is <= RELATION_TOL_A (R1's printed precision). DERIVED_HERE."""
    q = a_A / 4.0
    Mi = np.rint(np.asarray(M, float)).astype(np.int64)
    tq = np.asarray(t_crystal_A, float) / q
    ti = np.rint(tq).astype(np.int64)
    if np.max(np.abs(tq - ti)) > 1e-6:
        raise StructureAssertionError("relation translation is not on the a/4 grid")
    tB = rec.metadata["terraces"][B]
    dB = np.array(tB["dimer_bond_axis_crystal"], np.int64)
    bB = np.array(tB["dimer_row_axis_crystal"], np.int64)
    oB = np.array(tB["origin_site_quarter"], np.int64)
    if (state_A or state_B) and rec.mirror_displacement_A is None:
        raise ValueError("state 1 exists only for the flip-flop ensemble")
    dispA = rec.displacement_A if state_A == 0 else rec.mirror_displacement_A
    dispB = rec.displacement_A if state_B == 0 else rec.mirror_displacement_A
    terrace = np.asarray(terrace)
    quarter = np.asarray(quarter, np.int64)
    top = np.asarray(tops)[terrace] - np.asarray(layer)
    selA = np.nonzero((terrace == A) & (rec.cell_index >= 0))[0]
    selB = np.nonzero((terrace == B) & (rec.cell_index >= 0))[0]

    def r1(v_slab):                                  # slab vector -> (dx, dy, dz) in B's frame
        c = frame.to_crystal(v_slab)
        return np.stack([c @ dB / np.sqrt(2.0), c @ bB / np.sqrt(2.0), c[..., 2]], axis=-1)

    kB, lB = _kl(quarter[selB] - oB, dB, bB)
    classes: dict = {}
    for key, v in zip(zip(*[a.tolist() for a in _reduce(rec.name, kB, lB, -top[selB])]),
                      r1(dispB[selB])):
        if key in classes and np.max(np.abs(classes[key] - v)) > RELATION_TOL_A:
            raise StructureAssertionError(f"terrace {B}: pattern class {key} not unique")
        classes.setdefault(key, v)
    img = quarter[selA] @ Mi.T + ti
    kA, lA = _kl(img - oB, dB, bB)
    mA = -top[selA]
    vA = r1(frame.to_slab(frame.to_crystal(dispA[selA]) @ Mi.T.astype(float)))
    best = None
    lat = PATTERN_LATTICE[rec.name]
    kper = 4 if lat == ((4, 0), (0, 2)) else 8
    for k0 in range(0, kper, 2):
        for l0 in range(0, 4, 2):
            keys = list(zip(*[a.tolist() for a in _reduce(rec.name, kA + k0, lA + l0, mA)]))
            if any(k not in classes for k in keys):
                continue
            dev = float(np.max(np.abs(np.array([classes[k] for k in keys]) - vA)))
            if best is None or dev < best[0]:
                best = (dev, k0, l0)
    if best is None:
        return dict(holds=False, max_deviation_A=None, note="no pattern translation matches")
    return dict(holds=bool(best[0] <= RELATION_TOL_A), max_deviation_A=best[0],
                pattern_translation_R1_units=[best[1], best[2]], tolerance_A=RELATION_TOL_A,
                atoms_compared=int(len(selA)), state_A=int(state_A), state_B=int(state_B))
