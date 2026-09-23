"""Slice potentials, physical absorption, numerical absorbers, frozen phonons.

Every slice potential is a projected potential V_p(x, y) in V A over the slice [i dz, (i+1) dz);
its imaginary part is the PHYSICAL absorption (PROJECT_INPUT item 21). The NUMERICAL absorbers are
added separately by the engine (``absorber_profile_V``). The engine applies
t = exp(+i sigma V_p) exp(-sigma W(x) dz), band-limits t, and acts at the slice centre (symmetric
split step), so an atom's potential acts at z = (i + 1/2) dz.

Atomic potential (docs/05 4.3 item 6): independent-atom model, INFINITE projection of each atom into
the slice that contains it, built in Fourier space on the grid:

    V_p(r) = (1 / (dx dy)) IFFT2[ sum_s F_s(f^2) sum_{j in s, slice} exp(-2 pi i f.r_j) ],

F_s(f^2) = abTEM 1.0.10 ``KirklandParametrization().projected_scattering_factor(symbol)(f^2)``,
the 2D Fourier transform of the infinite projected potential in V A^3 (f in cycles/A); the
construction is the one recommended in report D3 section 8. Parameterisation: KIRKLAND only
(orchestrator decision after D3: abTEM's Kirkland table equals Kirkland's computem table for Si bit
for bit; abTEM's Lobato table differs from Lobato's MULTEM table, D3 F5). Provenance: the abTEM
source is SECTION_READ (report D3; this repository also checked the function against abTEM's
real-space ``projected_potential`` by a Hankel transform, and a slice against a FRESH
``ScatteringFactorProjectionIntegrals("kirkland").integrate_on_grid`` in tests/forward); the
parameterisation itself (Kirkland's fit, book B06) is NOT read by us (SM17): UNVERIFIED. The exact
phase factors place each atom at its continuous position (no bilinear delta spreading or sinc
correction as in abTEM integrals.py:467-505). abTEM (GPL-3.0-or-later) is an OPTIONAL dependency,
imported lazily; no abTEM code or table is copied into this repository.
Mean inner potential of the potential actually used (``mean_inner_potential_V``; 13.903 V for
Kirkland Si at a = 5.4309 A, D3 F16) is recorded in every ExitWave; it is the independent-atom
value, not the sourced V0 (12.0 V ASSUMPTION B1; PROJECT_INPUT item 20); no correction to a sourced
V0 is applied (a modelling decision left open by D3 blocker 5).
Slice assignment rule (documented, deterministic): slice i holds the atoms with
i dz - 1e-9 A <= z < (i + 1) dz - 1e-9 A (an atom on a boundary goes to the downstream slice);
the z-position error of an atom is |z - (i + 1/2) dz| <= dz/2 and is recorded. Infinite projection
within the slice is an approximation (no sub-slice sampling of the potential along z).

Physical absorption: model "proportional", V_imag = ratio * V_real of the crystal potential, with
ratio and its label REQUIRED (PROJECT_INPUT item 21); ratio = 0 must be stated explicitly with the
label ASSUMPTION (no absorption; model_assumptions B6 is then not represented).

Numerical absorbers: W(x) = W0 p(u), u in [0, 1] from the inner edge to the box boundary,
p = sin^2(pi u / 2), u^2 or u^3; W0 and the profile REQUIRED; label NUMERICAL (not physical): they
emulate the semi-infinite crystal and prevent wrap-around through the periodic x boundary.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass

import numpy as np

from reflection_holo.io.labels import require_evidence_label

NUMERICAL_LABEL = "NUMERICAL (not physical): absorbing boundary of the reflection cell"
ABSORBER_PROFILES = ("sin2", "quadratic", "cubic")
PARAMETERISATIONS = {"kirkland": "KirklandParametrization"}   # orchestrator decision after D3
ABTEM_COMMIT = "164e644f (tag v1.0.10; report D3 F1)"
_LABELS = ("PROJECT_INPUT", "ASSUMPTION", "TEST_ONLY")
_SLICE_EPS_A = 1e-9


@dataclass(frozen=True)
class NumericalAbsorber:
    """Numerical imaginary potential at the bulk side and the top of the box (both required)."""
    strength_V: float
    profile: str

    def __post_init__(self):
        if self.profile not in ABSORBER_PROFILES:
            raise ValueError(f"absorber profile must be one of {ABSORBER_PROFILES}")
        if not (np.isfinite(self.strength_V) and self.strength_V > 0):
            raise ValueError("absorber strength_V must be finite and > 0 (V)")

    def describe(self) -> dict:
        return dict(strength_V=float(self.strength_V), profile=self.profile, label=NUMERICAL_LABEL,
                    formula="W(x) = W0 p(u); u = 0 at the inner edge, 1 at the box boundary")


def _profile(u, name):
    u = np.clip(u, 0.0, 1.0)
    if name == "sin2":
        return np.sin(0.5 * np.pi * u) ** 2
    if name == "quadratic":
        return u**2
    return u**3


def absorber_profile_V(grid, cell, absorber: NumericalAbsorber) -> np.ndarray:
    """W(x) in V on the grid's x coordinates (pixel centres), bulk side and top of the box."""
    lay = cell.metadata["layout"]
    x = grid.x_A()
    b0, b1 = lay["bulk_absorber_x_A"]
    t0, t1 = lay["top_absorber_x_A"]
    W = np.zeros_like(x)
    inb = x < b1
    W[inb] = _profile((b1 - x[inb]) / (b1 - b0), absorber.profile)
    intop = x > t0
    W[intop] = _profile((x[intop] - t0) / (t1 - t0), absorber.profile)
    return absorber.strength_V * W


@dataclass(frozen=True)
class PhysicalAbsorption:
    """Imaginary part of the crystal potential (PROJECT_INPUT item 21). No default exists."""
    model: str
    ratio: float
    label: str

    def __post_init__(self):
        if self.model != "proportional":
            raise ValueError("only model='proportional' (V_imag = ratio * V_real) is implemented")
        if not (np.isfinite(self.ratio) and self.ratio >= 0):
            raise ValueError("absorption ratio must be finite and >= 0")
        require_evidence_label(self.label, "physical absorption (PROJECT_INPUT item 21)",
                               accepted=_LABELS, qualified=True)
        if self.ratio == 0 and not self.label.startswith(("ASSUMPTION", "TEST_ONLY")):
            raise ValueError("zero physical absorption must carry the label ASSUMPTION (or "
                             "TEST_ONLY in tests)")

    def describe(self) -> dict:
        return dict(model=self.model, ratio=float(self.ratio), label=self.label,
                    formula="V_imag(r) = ratio * V_real(r) (crystal potential only)",
                    project_input="item 21")


@dataclass(frozen=True)
class FrozenPhonons:
    """Uncorrelated Gaussian displacements, rms per Cartesian axis (required, labelled)."""
    rms_displacement_A: float
    label: str

    def __post_init__(self):
        if not (np.isfinite(self.rms_displacement_A) and self.rms_displacement_A > 0):
            raise ValueError("rms_displacement_A must be finite and > 0")
        require_evidence_label(self.label, "frozen-phonon rms displacement", accepted=_LABELS,
                               qualified=True)

    def describe(self) -> dict:
        return dict(model="independent Gaussian displacements (Einstein model)",
                    rms_displacement_per_axis_A=float(self.rms_displacement_A), label=self.label,
                    ensemble_rule="intensities are averaged AFTER squaring (after hologram "
                                  "formation), never the complex waves")


def _import_abtem():
    """Lazy optional import of abTEM's parameterisations (GPL-3.0-or-later; report D3 section 6)."""
    try:
        import abtem
        from abtem import parametrizations as ap
    except ImportError as exc:                                 # pragma: no cover
        raise ImportError(
            "the atomic potential needs the optional dependency abTEM 1.0.10 for the Kirkland "
            "parameterisation functions: venv/bin/pip install abtem==1.0.10 (GPL-3.0-or-later; "
            "report D3)") from exc
    if abtem.__version__ != "1.0.10":
        raise ImportError(f"abTEM {abtem.__version__} found; the provenance (report D3) is for "
                          f"1.0.10 only")
    return ap, abtem.__version__


def potential_mean_inner_potential_V(potential) -> float:
    """Mean inner potential (V) of the potential ACTUALLY USED by the engine: the independent-atom
    value for AtomicPotential (13.903 V, Kirkland Si), the declared V0 for a continuum potential.
    The pipeline computes its refraction angles with this value to stay consistent with the
    exit waves (orchestrator decision 5 after D3)."""
    return float(potential.mean_inner_potential_V())


def _sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


class AtomicPotential:
    """Independent-atom projected potential of a ReflectionCell (module docstring)."""
    kind = "atomic"

    def __init__(self, cell, *, parameterisation: str, physical_absorption: PhysicalAbsorption,
                 frozen_phonons: FrozenPhonons | None, static_lattice_label: str | None):
        if parameterisation not in PARAMETERISATIONS:
            raise ValueError(f"parameterisation must be one of {tuple(PARAMETERISATIONS)} "
                             f"(Lobato refused: abTEM's lobato.json differs from Lobato's MULTEM "
                             f"table, report D3 F5)")
        if not isinstance(physical_absorption, PhysicalAbsorption):
            raise TypeError("physical_absorption must be a PhysicalAbsorption (item 21)")
        if frozen_phonons is None:
            require_evidence_label(static_lattice_label, "static lattice (no frozen phonons)",
                                   accepted=_LABELS, qualified=True)
        elif static_lattice_label is not None:
            raise ValueError("static_lattice_label is only for frozen_phonons=None")
        if cell.metadata.get("kind") != "atomic" or len(cell.Z) == 0:
            raise ValueError("AtomicPotential needs an atomic ReflectionCell")
        ap, abtem_version = _import_abtem()
        self.cell = cell
        self.name = parameterisation
        self.absorption = physical_absorption
        self.frozen_phonons = frozen_phonons
        self.static_lattice_label = static_lattice_label
        self._param = getattr(ap, PARAMETERISATIONS[parameterisation])()
        self._symbols = {14: "Si", 8: "O"}
        base = os.path.dirname(ap.__file__)
        data = os.path.join(base, "data", f"{parameterisation}.json")
        self._prov = dict(
            kind="independent-atom model, infinite projection per slice, Fourier-space "
                 "construction with exact structure factors",
            parameterisation=parameterisation,
            parameterisation_class=PARAMETERISATIONS[parameterisation],
            function="projected_scattering_factor(symbol)(f^2), f in cycles/A, V A^3",
            abtem_version=abtem_version, abtem_commit=ABTEM_COMMIT,
            abtem_licence="GPL-3.0-or-later (optional dependency, imported lazily; no code or "
                          "table copied)",
            source_files=[os.path.join(base, "__init__.py"),
                          os.path.join(base, "functions", f"{parameterisation}.py")],
            data_file=data, data_file_sha256=_sha256(data),
            provenance_label="SECTION_READ of abTEM 1.0.10 source (report D3); the function is "
                             "called, not re-implemented",
            parameterisation_label="UNVERIFIED: the parameterisation itself (its paper and fit) "
                                   "is not read by us (SM17)",
            slice_assignment=("slice i holds atoms with i dz - 1e-9 A <= z < (i+1) dz - 1e-9 A; "
                              "each atom's infinite projection acts at the slice centre"),
        )

    def scattering_factor(self, Z: int, f2):
        fn = self._param.projected_scattering_factor(self._symbols[int(Z)])
        return np.asarray(fn(np.asarray(f2, dtype=np.float64)), dtype=np.float64)

    def mean_inner_potential_V(self) -> float:
        """V0 implied by the parameterisation for bulk diamond Si: (8 / a^3) F_Si(0), DERIVED_HERE
        (neutral free atoms; bonding is not included). Compared with the sourced V0 in metadata."""
        if set(np.unique(self.cell.Z)) != {14}:
            raise NotImplementedError("mean inner potential implemented for Si only")
        a = float(self.cell.metadata["structure"]["lattice"]["a_A"])
        return float(8.0 / a**3 * self.scattering_factor(14, np.array([0.0]))[0])

    def provenance(self) -> dict:
        d = dict(self._prov)
        d["mean_inner_potential_V"] = self.mean_inner_potential_V()
        d["mean_inner_potential_note"] = (
            "DERIVED_HERE: 8/a^3 * F_Si(0) for bulk diamond Si with the cell's lattice parameter; "
            "compare with V0 = 12.0 V (ASSUMPTION B1) and 12.53 V (DFT, SECTION_READ, not "
            "adopted); PROJECT_INPUT item 20 is the sourced value (docs/05 4.3 item 6; SM17)")
        d["physical_absorption"] = self.absorption.describe()
        d["frozen_phonons"] = (self.frozen_phonons.describe() if self.frozen_phonons else
                               dict(model="static lattice", label=self.static_lattice_label))
        return d

    def realise(self, *, grid, dz_A: float, n_slices: int, backend, rng):
        return _RealisedAtomic(self, grid, dz_A, n_slices, backend, rng)


class _RealisedAtomic:
    def __init__(self, pot: AtomicPotential, grid, dz, n_slices, be, rng):
        cell = pot.cell
        xyz = np.array(cell.atoms_xyz_A, dtype=np.float64)
        if pot.frozen_phonons is not None:
            if rng is None:
                raise ValueError("frozen phonons need a seeded generator")
            xyz = xyz + rng.normal(0.0, pot.frozen_phonons.rms_displacement_A, xyz.shape)
        z = xyz[:, 2]
        idx = np.floor((z + _SLICE_EPS_A) / dz).astype(np.int64)
        if idx.min() < 0 or idx.max() >= n_slices:
            raise ValueError("atoms outside [0, L_z): cannot assign them to slices")
        order = np.argsort(idx, kind="stable")
        self.idx_sorted = idx[order]
        self.xyz = xyz[order]
        self.Z = np.asarray(cell.Z)[order]
        self.starts = np.searchsorted(self.idx_sorted, np.arange(n_slices + 1))
        off = np.abs(z - (idx + 0.5) * dz)
        self.be, self.grid, self.pot = be, grid, pot
        f2 = grid.fx()[:, None] ** 2 + grid.fy()[None, :] ** 2
        self.F = {int(Zs): be.asarray(pot.scattering_factor(Zs, f2), dtype=be.real_dtype)
                  for Zs in np.unique(self.Z)}
        self.fx64 = be.asarray(grid.fx(), dtype=np.float64)
        self.fy64 = be.asarray(grid.fy(), dtype=np.float64)
        self.norm = 1.0 / (grid.dx_A * grid.dy_A)
        self.ratio = float(pot.absorption.ratio)
        self.metadata = dict(n_atoms=int(len(z)), max_atom_offset_from_slice_centre_A=float(off.max()),
                             mean_atom_offset_from_slice_centre_A=float(off.mean()),
                             atoms_within_1e_6_A_of_a_boundary=int(np.count_nonzero(
                                 np.abs(z / dz - np.rint(z / dz)) * dz < 1e-6)),
                             displaced=pot.frozen_phonons is not None,
                             displaced_positions_sha256=hashlib.sha256(
                                 np.ascontiguousarray(xyz, "<f8").tobytes()).hexdigest())

    def slice_key(self, i):
        return "empty" if self.starts[i] == self.starts[i + 1] else None

    def projected(self, i):
        be, xp = self.be, self.be.xp
        a, b = self.starts[i], self.starts[i + 1]
        if a == b:
            return xp.zeros(self.grid.shape, dtype=be.complex_dtype)
        acc = None
        for Zs, F in self.F.items():
            sel = self.Z[a:b] == Zs
            if not np.any(sel):
                continue
            # phase arguments in float64 (2 pi f x reaches ~2e3 rad; float32 would err by ~1e-4
            # rad), exponentials cast to the working precision afterwards
            pos = be.asarray(self.xyz[a:b][sel], dtype=np.float64)
            Ex = xp.exp(-2j * np.pi * (self.fx64[:, None] * pos[None, :, 0])).astype(be.complex_dtype)
            Ey = xp.exp(-2j * np.pi * (self.fy64[:, None] * pos[None, :, 1])).astype(be.complex_dtype)
            S = (Ex @ Ey.T) * F
            acc = S if acc is None else acc + S
        V = be.ifft2(acc).real * be.real_dtype(self.norm)
        if self.ratio:
            return (V * (1.0 + 1j * self.ratio)).astype(be.complex_dtype)
        return V.astype(be.complex_dtype)


class ContinuumTerracePotential:
    """Constant potential V0 in the terraces of a continuum cell (cell.build_continuum_cell), for
    the refraction-only rungs of the validation ladder. surface_profile "sharp": each pixel carries
    the fraction of its area [x_j - dx/2, x_j + dx/2] x [y_m - dy/2, y_m + dy/2] inside the crystal
    (cell average); the slice straddling the front face carries its overlap fraction along z."""
    kind = "continuum"

    def __init__(self, cell, *, V0_V: float, V0_label: str,
                 physical_absorption: PhysicalAbsorption, surface_profile: str):
        if cell.metadata.get("kind") != "continuum":
            raise ValueError("ContinuumTerracePotential needs a continuum cell")
        require_evidence_label(V0_label, "mean inner potential V0 (PROJECT_INPUT item 20)",
                               accepted=_LABELS, qualified=True)
        if not (np.isfinite(V0_V) and V0_V > 0):
            raise ValueError("V0_V must be finite and > 0")
        if surface_profile != "sharp":
            raise ValueError("surface_profile must be 'sharp' (cell-averaged step)")
        if not isinstance(physical_absorption, PhysicalAbsorption):
            raise TypeError("physical_absorption must be a PhysicalAbsorption (item 21)")
        self.cell, self.V0, self.V0_label = cell, float(V0_V), V0_label
        self.absorption, self.surface_profile = physical_absorption, surface_profile

    def mean_inner_potential_V(self) -> float:
        return self.V0

    def provenance(self) -> dict:
        return dict(kind="continuum constant-potential terraces (no atoms)", V0_V=self.V0,
                    V0_label=self.V0_label, surface_profile="sharp, cell-averaged per pixel",
                    physical_absorption=self.absorption.describe(),
                    frozen_phonons=dict(model="not applicable (no atoms)"))

    def fill(self, grid) -> np.ndarray:
        x = grid.x_A()
        y = grid.y_A()
        Ly = self.cell.extent_y_A
        out = np.zeros(grid.shape)
        for t in self.cell.metadata["terraces"]:
            s = t["surface_x_A"]
            fxv = np.clip((s - (x - 0.5 * grid.dx_A)) / grid.dx_A, 0.0, 1.0)
            y0, y1 = t["range_A"]
            if grid.ny == 1:
                fyv = np.array([(y1 - y0) / Ly])
            else:
                lo = y - 0.5 * grid.dy_A
                hi = y + 0.5 * grid.dy_A
                fyv = np.zeros_like(y)
                for sh in (-Ly, 0.0, Ly):
                    fyv += np.clip(np.minimum(hi, y1 + sh) - np.maximum(lo, y0 + sh), 0, None)
                fyv /= grid.dy_A
            out += fxv[:, None] * fyv[None, :]
        return out

    def realise(self, *, grid, dz_A: float, n_slices: int, backend, rng):
        return _RealisedContinuum(self, grid, dz_A, n_slices, backend)


class _RealisedContinuum:
    def __init__(self, pot, grid, dz, n_slices, be):
        c = pot.cell
        z0, z1 = float(c.crystal_start_z_A), float(c.length_z_A)
        i = np.arange(n_slices)
        self.overlap = np.clip(np.minimum((i + 1) * dz, z1) - np.maximum(i * dz, z0), 0.0, dz)
        v = pot.V0 * (1.0 + 1j * pot.absorption.ratio)
        self.base = be.asarray(pot.fill(grid) * v, dtype=be.complex_dtype)
        self.be = be
        self.grid = grid
        self.metadata = dict(front_face_z_A=z0, slices_with_partial_overlap=int(np.count_nonzero(
            (self.overlap > 0) & (self.overlap < dz - 1e-12))))

    def slice_key(self, i):
        return ("continuum", round(float(self.overlap[i]), 12))

    def projected(self, i):
        return self.base * self.be.real_dtype(self.overlap[i])
