"""Dimer flip-flop ensemble for the multislice engine (model_assumptions B37; report E2).

MODEL CHOICE, NOT A SOURCE. At room temperature the Si(001) dimers flip-flop (c(4x2) order only
below 205 K; L7 section 1.2). ``structure.reconstruction`` builds the "p(2x1)a flip-flop ensemble":
every complete dimer cell has two states, the p(2x1)a displacements of Ramstad, Brocks and Kelly
1995 Table III and their mirror image (buckling reversed). This module draws, for EVERY
realisation, the state of every cell independently with probability 1/2, from the generator the
engine seeds with [seed, realisation] (the frozen-phonon generator: the states are drawn first,
then the thermal displacements), and hands the configuration to the atomic potential. The elastic
average is therefore an ensemble average taken after squaring, like the frozen-phonon average
(docs/05; the pipeline averages hologram intensities over realisations).

``DimerFlipFlopPotential`` wraps a ``forward.multislice.AtomicPotential`` (not modified; agent E1
owns potentials.py): per realisation it builds the cell's atom positions of the drawn configuration
and calls the unchanged ``AtomicPotential.realise`` on a view of the potential whose ``cell`` is the
per-realisation cell. It requires frozen phonons (the engine seeds a generator only for a potential
with frozen phonons, and the flip-flop is a room-temperature model: thermal displacements at the same
specimen temperature, model_assumptions B35).

Recorded per realisation (ExitWave.metadata["potential"]["realised"]["dimer_flip_flop"]): number of
cells, number reversed, SHA-256 of the packed state vector and the packed states themselves (hex).
"""
from __future__ import annotations

import dataclasses
import hashlib

import numpy as np

from reflection_holo.structure.reconstruction import FLIPFLOP, FLIPFLOP_LABEL

_MAP_TOL_A = 1e-9


class _PerRealisationView:
    """The wrapped potential with a per-realisation cell (every other attribute delegated)."""

    def __init__(self, base, cell):
        self._base = base
        self.cell = cell

    def __getattr__(self, name):
        return getattr(self._base, name)


class DimerFlipFlopPotential:
    """AtomicPotential of a flip-flop ensemble structure (module docstring)."""
    kind = "atomic"

    def __init__(self, base, structure):
        rec = getattr(structure, "reconstruction", None)
        if rec is None or rec.name != FLIPFLOP:
            raise ValueError(f"DimerFlipFlopPotential needs a structure built with termination "
                             f"{FLIPFLOP!r}")
        if getattr(base, "kind", None) != "atomic":
            raise TypeError("DimerFlipFlopPotential wraps an atomic potential")
        if base.frozen_phonons is None:
            raise ValueError(
                "the flip-flop ensemble needs frozen phonons: the engine seeds a generator per "
                "realisation only for a potential with frozen phonons, and the flip-flop is a "
                "room-temperature model (thermal displacements at the same specimen temperature, "
                "model_assumptions B35; PROJECT_INPUT item 23)")
        cell = base.cell
        md = structure.metadata
        tops = np.array([t["top_height_A"] for t in md["terrace_map"]], float)
        lay = cell.metadata["layout"]
        bottom = float(tops.min()) - float(lay["depth_below_A"])
        ent = float(lay["entrance_vacuum_z_A"])
        xs = np.asarray(structure.positions_A, float)
        keep = xs[:, 0] >= bottom - 1e-6               # forward.cell.build_reflection_cell's rule
        shift = np.array([-bottom, 0.0, ent])
        static = xs[keep] + shift
        if static.shape != np.asarray(cell.atoms_xyz_A).shape or np.max(
                np.abs(static - np.asarray(cell.atoms_xyz_A))) > _MAP_TOL_A:
            raise ValueError("the reflection cell's atoms are not the structure's atoms (cell "
                             "built from another structure or with another rule)")
        moved = np.linalg.norm(rec.displacement_A[keep], axis=1) + np.linalg.norm(
            rec.mirror_displacement_A[keep], axis=1) > 0
        near_cut = np.abs(rec.ideal_positions_A[keep][:, 0] - bottom) < 1.0
        if np.any(moved & near_cut):
            raise ValueError("reconstructed atoms within 1 A of the cell's bottom cut: increase "
                             "depth_below_A")
        if np.count_nonzero(np.linalg.norm(rec.displacement_A[~keep], axis=1)) or \
                np.count_nonzero(np.linalg.norm(rec.mirror_displacement_A[~keep], axis=1)):
            raise ValueError("reconstructed atoms were cut from the reflection cell")
        self.base = base
        self.structure = structure
        self._ideal = rec.ideal_positions_A[keep] + shift
        self._d0 = rec.displacement_A[keep]
        self._d1 = rec.mirror_displacement_A[keep]
        self._cell_index = rec.cell_index[keep]
        self.n_cells = int(rec.n_cells)

    # --- attributes the engine reads ----------------------------------------------------------
    @property
    def cell(self):
        return self.base.cell

    @property
    def frozen_phonons(self):
        return self.base.frozen_phonons

    def mean_inner_potential_V(self) -> float:
        """Unchanged by the displacements (8/a^3 F(0) of the independent-atom model)."""
        return self.base.mean_inner_potential_V()

    def describe_ensemble(self) -> dict:
        return dict(model=FLIPFLOP, label=FLIPFLOP_LABEL, n_cells=self.n_cells,
                    draw=("per realisation, each cell independently: state 1 (buckling reversed, "
                          "mirror image of R1 Table III p(2x1)a) with probability 1/2, from the "
                          "engine's generator seeded with [seed, realisation], drawn BEFORE the "
                          "frozen-phonon displacements"),
                    ensemble_rule="intensities averaged after squaring, like frozen phonons",
                    not_modelled=("correlations between dimers (2-D Ising order-disorder, R4), "
                                  "relaxation of mixed neighbourhoods, flip-flop time scale"))

    def provenance(self) -> dict:
        d = dict(self.base.provenance())
        d["dimer_flip_flop"] = self.describe_ensemble()
        return d

    # --- per-realisation configuration ------------------------------------------------------
    def positions_for(self, flips) -> np.ndarray:
        f = np.asarray(flips)
        if f.shape != (self.n_cells,) or not np.all((f == 0) | (f == 1)):
            raise ValueError(f"flips must be {self.n_cells} values 0 or 1")
        use = np.zeros(len(self._cell_index), bool)
        inc = self._cell_index >= 0
        use[inc] = f[self._cell_index[inc]] == 1
        return self._ideal + np.where(use[:, None], self._d1, self._d0)

    def realise(self, *, grid, dz_A: float, n_slices: int, backend, rng):
        if rng is None:
            raise ValueError("the flip-flop ensemble needs the engine's seeded generator")
        flips = rng.integers(0, 2, size=self.n_cells).astype(np.uint8)
        xyz = self.positions_for(flips)
        md = dict(self.base.cell.metadata)
        md["atoms_sha256_note"] = "per-realisation flip-flop configuration (dimer_ensemble)"
        cell = dataclasses.replace(self.base.cell, atoms_xyz_A=xyz, metadata=md)
        view = _PerRealisationView(self.base, cell)
        realised = type(self.base).realise(view, grid=grid, dz_A=dz_A, n_slices=n_slices,
                                           backend=backend, rng=rng)
        packed = np.packbits(flips)
        realised.metadata["dimer_flip_flop"] = dict(
            model=FLIPFLOP, n_cells=self.n_cells, n_reversed=int(flips.sum()),
            states_packbits_hex=packed.tobytes().hex(),
            states_sha256=hashlib.sha256(packed.tobytes()).hexdigest(),
            configuration_positions_sha256=hashlib.sha256(
                np.ascontiguousarray(xyz, "<f8").tobytes()).hexdigest())
        return realised
