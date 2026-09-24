"""Continuum oxide overlayer in the multislice engine (report E4; model: structure.oxide, after L8
section 8 as corrected by E9 M1-M5).

``ContinuumOxidePotential(base, oxide=spec)`` adds, to the crystal potential ``base``
(AtomicPotential, ContinuumTerracePotential or ContinuumPeriodicPotential), the continuum layers of
the cell's recorded stack (forward.cell: build_reflection_cell for a structure built with the
ContinuumOxideSpec, or build_continuum_oxide_cell):

    V_layer(x) = (V_ox + i V'_ox) [E(x; x_t, w_v) - E(x; x_i, w_i)]
               + (V_a + i V'_a) [E(x; x_i, w_i) - E(x; x_c, w_i)]          (a-Si, if t_a > 0)
    E(x; x0, w) = erfc((x - x0) / (sqrt(2) w)) / 2

per terrace, following the surface (never a function of x alone: E6 m12, E9 m5). Sampling: point-
sampled at the pixel centres for w > 0 (like the harmonics of ContinuumPeriodicPotential); w = 0
(sharp; only with the TEST_ONLY flags of structure.oxide, both edges being graded over >= 0.5 A
otherwise: E9 M4, audit A8 m5) is the fraction of
the pixel [x_j - dx/2, x_j + dx/2] below x0, i.e. the cell-averaged convention of
ContinuumTerracePotential. Grid assertion (a priori, DERIVED_HERE): every graded edge needs
dx <= w, so that the first alias of the sampled Gaussian gradient has a relative amplitude
exp(-2 pi^2 (w/dx)^2) <= 2.7e-9.

Terraces with step edges PARALLEL to the beam (y strips): the layer of each terrace is weighted by
its cell-averaged y fraction (as the continuum crystal); TRANSVERSE edges (z strips; atomic cells):
every slice carries the layer of the terrace whose z range it overlaps, weighted by the overlap
(the terrace boundaries are slice boundaries: dz divides the lattice period along the beam). Only
the crystal's z range [crystal_start_z_A, length_z_A) carries the layer (the entrance vacuum does
not). Continuum crystal: with w_i = 0 the crystal part is the base potential itself (bit for bit);
with w_i > 0 the crystal fill is graded with the same E(x; x_c, w_i) so that crystal and layer add
to a continuous profile.

Mean inner potential (orchestrator decision B32, unchanged): ``mean_inner_potential_V`` returns the
CRYSTAL's (the Kirkland IAM 13.903 V for an atomic cell, the declared V0 for a continuum crystal);
the glancing angle, the refraction angles of the band and geometry assertions and the pipeline's MIP
check use it, as without the layer. The layer changes (recorded by ``overlayer_setup`` in every
ExitWave): (i) the internal angle inside the layer (added to the band assertion), (ii) the
vacuum-referenced phase of each terrace by 2 (k'_ox - k) (x_t - H) + 2 k'_ox (H - x_i) (+ a-Si)
(E9 section 3; common-mode for a conformal layer), (iii) the amplitude by exp(-2 Im k'_ox t) in+out
(the zero-loss MODEL value of E9 M1, not a bound). For an atomic base the independent-atom value of
SiO2 at the declared density, n_SiO2 (F_Si(0) + 2 F_O(0)), is recorded for comparison with V_ox
(E9 out:161-171: 10.3394 V at 2.20 g/cm^3); it is not used.
"""
from __future__ import annotations

import math

import numpy as np

from reflection_holo.geometry.refraction import k_perp_in_layer_per_A, theta_int_from_ext_rad
from reflection_holo.structure import oxide as ox

_ERFC = np.frompyfunc(math.erfc, 1, 1)
SAMPLING_RULE = ("graded edges point-sampled at the pixel centres, dx <= w asserted (first alias "
                 "of the sampled Gaussian gradient exp(-2 pi^2 (w/dx)^2) <= 2.7e-9); w = 0 "
                 "cell-averaged (ContinuumTerracePotential convention)")
MIP_TREATMENT = (
    "the crystal's mean inner potential sets the glancing angle and every refraction angle of the "
    "band and geometry assertions (B32, unchanged by the layer); the layer adds: the internal "
    "angle inside it (in the band assertion), the vacuum-referenced phase 2 (k'_ox - k)(x_t - H) + "
    "2 k'_ox (H - x_i) (+ a-Si) per terrace (common-mode for a conformal layer, E9 section 3 item "
    "1), and the in+out zero-loss attenuation exp(-2 Im k'_ox t) (a model value, E9 M1)")


def edge_profile(x_A, x0_A: float, w_A: float, dx_A: float) -> np.ndarray:
    """E(x; x0, w) = erfc((x - x0)/(sqrt(2) w))/2 point-sampled (w > 0), or the fraction of the pixel
    [x - dx/2, x + dx/2] below x0 (w = 0, cell-averaged; ContinuumTerracePotential's convention)."""
    x = np.asarray(x_A, dtype=np.float64)
    if w_A > 0.0:
        u = (x - x0_A) / (math.sqrt(2.0) * w_A)
        return 0.5 * _ERFC(u).astype(np.float64)          # math.erfc (no scipy dependency)
    return np.clip((x0_A - (x - 0.5 * dx_A)) / dx_A, 0.0, 1.0)


def _y_fraction(grid, Ly: float, y0: float, y1: float) -> np.ndarray:
    """Cell-averaged fraction of every y pixel inside [y0, y1) (periodic; as
    potentials._continuum_crystal_fraction)."""
    y = grid.y_A()
    if grid.ny == 1:
        return np.array([(y1 - y0) / Ly])
    lo = y - 0.5 * grid.dy_A
    hi = y + 0.5 * grid.dy_A
    out = np.zeros_like(y)
    for sh in (-Ly, 0.0, Ly):
        out += np.clip(np.minimum(hi, y1 + sh) - np.maximum(lo, y0 + sh), 0, None)
    return out / grid.dy_A


class ContinuumOxidePotential:
    """Crystal potential plus the continuum oxide of the cell's recorded stack (module docstring).

    base   AtomicPotential, ContinuumTerracePotential or ContinuumPeriodicPotential of a cell built
           with the continuum oxide (the cell's layout["overlayer"] must exist)
    oxide  the structure.oxide.ContinuumOxideSpec with which the structure/cell was built (its hash
           is asserted against the cell's record: geometry and potential cannot diverge)
    """

    def __init__(self, base, *, oxide):
        cell = getattr(base, "cell", None)
        if cell is None:
            raise TypeError("base must be a potential of this package (with .cell)")
        lay = cell.metadata.get("layout") or {}
        ov = lay.get("overlayer")
        if ov is None or ov.get("model") != ox.MODEL_NAME:
            raise ValueError("the cell carries no continuum oxide (build it with a structure built "
                             "with structure.oxide.ContinuumOxideSpec, or with "
                             "forward.cell.build_continuum_oxide_cell)")
        rec = ox.validate_spec(oxide)
        if ox.spec_sha256(oxide) != ov["spec_sha256"]:
            raise ValueError("the ContinuumOxideSpec differs from the one the cell was built with "
                             "(spec_sha256 mismatch): geometry and potential would diverge")
        kind = getattr(base, "kind", None)
        if kind not in ("atomic", "continuum"):
            raise TypeError(f"base potential kind {kind!r} is not supported")
        if kind == "continuum" and not hasattr(base, "fill"):
            raise TypeError("a continuum base must be ContinuumTerracePotential or "
                            "ContinuumPeriodicPotential")
        self.base, self.cell, self.kind = base, cell, kind
        self.spec, self.params, self.layout = oxide, rec, ov
        self.frozen_phonons = getattr(base, "frozen_phonons", None)
        self.absorption = getattr(base, "absorption", None)

    # -- the engine's interface --------------------------------------------------------------
    def mean_inner_potential_V(self) -> float:
        return float(self.base.mean_inner_potential_V())

    def band_harmonics_per_A(self) -> dict:
        f = getattr(self.base, "band_harmonics_per_A", None)
        return dict(f()) if f is not None else {}

    def scattering_factor(self, Z, f2):
        return self.base.scattering_factor(Z, f2)

    def iam_sio2_mean_inner_potential_V(self) -> float | None:
        """n_SiO2 (F_Si(0) + 2 F_O(0)) of the base's parameterisation at the declared density
        (atomic base only; E9 out:161-171), else None."""
        if self.kind != "atomic":
            return None
        z = np.array([0.0])
        F = float(self.base.scattering_factor(14, z)[0]) + 2.0 * float(
            self.base.scattering_factor(8, z)[0])
        return float(ox.sio2_formula_units_per_A3(self.params["density_g_cm3"]) * F)

    def overlayer_setup(self, *, grid, energy_keV: float, theta_in_ext_rad: float,
                        theta_out_ext_rad: float) -> dict:
        """Grid assertion and the record of what the layer changes (module docstring); called by
        engine.reflection_setup before the band assertion. Raises ValueError if a graded edge is
        not resolved (dx > w)."""
        p = self.params
        widths = {"vacuum_edge_width_A": p["vacuum_edge_width_A"],
                  "interface_width_A": p["interface_width_A"]}
        for name, w in widths.items():
            if w > 0.0 and grid.dx_A > w * (1.0 + 1e-12):
                raise ValueError(
                    f"continuum oxide: {name} = {w} A is not resolved by dx = {grid.dx_A:.6f} A "
                    f"(dx <= w required: {SAMPLING_RULE})")
        V, Vi = p["V_real_V"], p["V_imag_V"]
        th_ox_in = theta_int_from_ext_rad(theta_in_ext_rad, energy_keV, V)
        th_ox_out = theta_int_from_ext_rad(theta_out_ext_rad, energy_keV, V)
        kp = k_perp_in_layer_per_A(theta_in_ext_rad, energy_keV, V, Vi)
        out = dict(
            model=ox.MODEL_NAME, spec_sha256=self.layout["spec_sha256"],
            conformal=bool(self.layout["conformal"]),
            internal_angle_in_layer_in_rad=float(th_ox_in),
            internal_angle_in_layer_out_rad=float(th_ox_out),
            k_perp_in_layer_per_A=[kp.real, kp.imag],
            sampling=SAMPLING_RULE, dx_A=float(grid.dx_A), edge_widths_A=widths,
            mean_inner_potential_treatment=MIP_TREATMENT,
            crystal_mean_inner_potential_V=self.mean_inner_potential_V(),
            V_real_V=V, V_imag_V=Vi,
            iam_sio2_at_declared_density_V=self.iam_sio2_mean_inner_potential_V(),
            iam_note=("independent-atom value n_SiO2 (F_Si + 2 F_O) of the base parameterisation "
                      "at the declared density, recorded for comparison with V_ox (E9 out:161-171); "
                      "not used" if self.kind == "atomic" else
                      "not computed (continuum crystal: no parameterisation)"),
            zero_loss_note="exp(-2 Im k'_perp t) in+out is a MODEL value, not a bound (E9 M1); "
                           "not to be multiplied with B38")
        if p["amorphous_si_thickness_A"] > 0:
            out["internal_angle_in_amorphous_si_in_rad"] = float(theta_int_from_ext_rad(
                theta_in_ext_rad, energy_keV, p["amorphous_si_V_real_V"]))
        return out

    def provenance(self) -> dict:
        d = dict(self.base.provenance())
        d["overlayer"] = dict(
            kind="continuum oxide layer following the surface (report E4; structure.oxide)",
            parameters={k: v for k, v in self.params.items()},
            spec_sha256=self.layout["spec_sha256"], conformal=bool(self.layout["conformal"]),
            per_terrace=self.layout["per_terrace"], sampling=SAMPLING_RULE,
            formula="(V + iV') [E(x; x_t, w_v) - E(x; x_i, w_i)] (+ a-Si between x_c and x_i); "
                    "E(x; x0, w) = erfc((x - x0)/(sqrt(2) w))/2",
            mean_inner_potential_treatment=MIP_TREATMENT,
            not_represented=ox.NOT_REPRESENTED)
        return d

    # -- construction ------------------------------------------------------------------------
    def _terrace_layer_profile(self, st: dict, x, dx) -> np.ndarray:
        p = self.params
        wv, wi = p["vacuum_edge_width_A"], p["interface_width_A"]
        Ut = complex(p["V_real_V"], p["V_imag_V"])
        prof = Ut * (edge_profile(x, st["top_x_A"], wv, dx)
                     - edge_profile(x, st["interface_x_A"], wi, dx))
        if p["amorphous_si_thickness_A"] > 0:
            Ua = complex(p["amorphous_si_V_real_V"], p["amorphous_si_V_imag_V"])
            prof = prof + Ua * (edge_profile(x, st["interface_x_A"], wi, dx)
                                - edge_profile(x, st["crystal_boundary_x_A"], wi, dx))
        return prof

    def _continuum_crystal(self, grid) -> np.ndarray:
        """Crystal part of a continuum base: the base itself for w_i = 0; graded otherwise."""
        wi = self.params["interface_width_A"]
        if wi == 0.0:
            return np.asarray(self.base.complex_potential(grid), dtype=np.complex128)
        x = grid.x_A()
        r = float(self.base.absorption.ratio)
        prof = (self.base.profile_V(x) if hasattr(self.base, "profile_V")
                else np.full(x.shape, float(self.base.mean_inner_potential_V())))
        out = np.zeros(grid.shape, dtype=np.complex128)
        for t in self.cell.metadata["terraces"]:
            y0, y1 = t["range_A"]
            e = edge_profile(x, t["surface_x_A"], wi, grid.dx_A)
            out += (prof * e * (1.0 + 1j * r))[:, None] * _y_fraction(grid, self.cell.extent_y_A,
                                                                       y0, y1)[None, :]
        return out

    def layer_arrays(self, grid, *, dz_A: float, n_slices: int):
        """(arrays, weights): complex arrays in V, (nx, ny) for terraces along y and (nx, 1) per
        terrace for terraces along z (uniform in y, broadcast), and the per-slice weight of each
        (A of overlap), so that the slice's projected potential is sum_g arrays[g] weights[i, g].
        Memory beyond the crystal potential: one complex (nx, ny) array (terraces along y) or
        n_terraces x nx (along z), built here in complex128 (accumulator + one product): both in
        engine.memory_model (argument ``overlayer``; audit A8 m3, tracemalloc-checked in
        tests/forward/test_memory_model.py)."""
        x = grid.x_A()
        dx = grid.dx_A
        c = self.cell
        z0, z1 = float(c.crystal_start_z_A), float(c.length_z_A)
        i = np.arange(n_slices)
        lo, hi = i * dz_A, (i + 1) * dz_A
        crystal_overlap = np.clip(np.minimum(hi, z1) - np.maximum(lo, z0), 0.0, dz_A)
        terr = c.metadata["terraces"]
        axis = self.layout["staircase_axis"]
        if axis == "y" or len(terr) == 1:
            arr = np.zeros(grid.shape, dtype=np.complex128)
            for t in terr:
                prof = self._terrace_layer_profile(t["oxide"], x, dx)
                if axis == "y":
                    fy = _y_fraction(grid, c.extent_y_A, *t["range_A"])
                else:
                    fy = np.ones(grid.ny)
                arr += prof[:, None] * fy[None, :]
            if self.kind == "continuum":
                arr = arr + self._continuum_crystal(grid)
            return [arr], crystal_overlap[:, None]
        if self.kind == "continuum":
            raise ValueError("a continuum cell has terraces along y only")
        arrays, weights = [], []
        for t in terr:                                   # transverse edges: terraces along z
            za, zb = t["range_A"]
            w = np.clip(np.minimum(hi, min(zb, z1)) - np.maximum(lo, max(za, z0)), 0.0, dz_A)
            prof = self._terrace_layer_profile(t["oxide"], x, dx)
            arrays.append(prof[:, None])                 # uniform in y: (nx, 1), broadcast
            weights.append(w)
        W = np.stack(weights, axis=1)
        covered = W.sum(axis=1)
        if np.max(np.abs(covered - crystal_overlap)) > 1e-9:
            raise ValueError("continuum oxide: the terraces' z ranges do not tile the crystal's z "
                             "range slice by slice")
        return arrays, W

    def realise(self, *, grid, dz_A: float, n_slices: int, backend, rng):
        base_r = (self.base.realise(grid=grid, dz_A=dz_A, n_slices=n_slices, backend=backend,
                                    rng=rng) if self.kind == "atomic" else None)
        arrays, W = self.layer_arrays(grid, dz_A=dz_A, n_slices=n_slices)
        return _RealisedOxide(base_r, arrays, W, backend, grid, self)


class _RealisedOxide:
    def __init__(self, base_r, arrays, W, be, grid, pot):
        self.base_r, self.W, self.be, self.grid = base_r, W, be, grid
        self.arrays = [be.asarray(a, dtype=be.complex_dtype) for a in arrays]
        md = dict(base_r.metadata) if base_r is not None else {}
        md["overlayer"] = dict(n_layer_arrays=len(arrays),
                               slices_with_layer=int(np.count_nonzero(W.sum(axis=1) > 0)),
                               layer_terms="projected potential = base + sum_g layer_g * overlap_g "
                                           "(A)")
        if pot.kind == "continuum":
            md.update(front_face_z_A=float(pot.cell.crystal_start_z_A),
                      slices_with_partial_overlap=int(np.count_nonzero(
                          (W[:, 0] > 0) & (W[:, 0] < W[:, 0].max() - 1e-12))))
            if hasattr(pot.base, "realised_harmonics") and pot.params["interface_width_A"] == 0.0:
                md["realised_harmonics_crystal_only"] = "not refitted with the layer present"
        self.metadata = md

    def slice_key(self, i):
        bk = self.base_r.slice_key(i) if self.base_r is not None else "no atoms"
        if bk is None:
            return None
        return (bk, tuple(round(float(w), 12) for w in self.W[i]))

    def projected(self, i):
        be, xp = self.be, self.be.xp
        out = (self.base_r.projected(i) if self.base_r is not None
               else xp.zeros(self.grid.shape, dtype=be.complex_dtype))
        for g, arr in enumerate(self.arrays):
            w = float(self.W[i, g])
            if w:
                out = out + arr * be.real_dtype(w)
        return out.astype(be.complex_dtype)
