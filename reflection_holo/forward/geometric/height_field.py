"""Geometric-phase reflection model for a general surface height field h(y, z) (agent T2).

Label carried by every output: "geometric model, no dynamical amplitude, B4 scope applies" (the
same engine label as ``forward.geometric.model``; docs/05 section 4.5).

Frame: the slab frame of ``reflection_holo.geometry.frames`` (x outward normal, y in-plane transverse,
z beam azimuth); heights h are x_rel = x - x_surface of the flat surrounding surface (0), in A.

What it computes (DERIVED_HERE; source map SM03, SM07; model_assumptions B4, B9, B13):

* The SPECULAR reflected beam only, of ONE plane wave (theta_out = theta_in = the EXTERNAL glancing
  angle, refraction included in its value through the pipeline's rule, B19; vacuum wavelength):
  k_out = k (sin theta, 0, cos theta). Every surface point reflects with the same declared
  amplitude |A| (no dynamical amplitude) and the geometric phase
        phi(y, z) = -(k_out - k_in).(h(y, z) x_hat) = -2 k sin(theta_ext) h(y, z),
  because q = k_out - k_in is along x_hat for the specular beam (only the normal component of the
  relation between two terraces enters).
* Surface model along the beam, declared (``HeightField.profile``):
  "piecewise_constant": cells of length dz with vertical risers between them (B13). With
  ``layer_spacing_A`` = a/4 the heights must be integer multiples of a/4: the ideal top atomic layer
  (for the half torus: ``structure.shapes.HalfTorus.layer_height_A``). Terraces differing by an odd
  number of layers are related by the Fd-3m d-glide / 4_1 screw, those differing by an even number by
  a lattice translation; at an exact <100> azimuth every such pair is inside the B4 scope for the
  specular beam of a plane wave on bulk-terminated terraces (docs/03 section 2, C2 section 1). The
  relation is NOT measured on atoms here (the atomistic builder must assert it); a/4-odd layers at
  any other azimuth are REFUSED (``OutsideB4ScopeError``). B4 is exact for infinite terraces and
  violated near risers: terraces narrower than a few nm (every flank terrace of the demo torus) are
  outside that premise; the geometric model ignores it (label).
  "piecewise_linear": a continuous surface (vertices every dz, linear between). It is not a lattice
  surface and B4 does not apply; accepted only for a TEST_ONLY geometry (tests of the ray tracer
  and of the height map).
* Visibility by exact ray tracing of that surface model, per y column (for the specular beam each
  ray stays in its plane of constant y): an exit-plane point (x, y) on the plane z = L is traced back
  along -k_out to the first surface it meets. A surface point is SHADOWED if some upstream point
  z' < z has h(y, z') > h(y, z) + (z - z') tan(theta_in), BLOCKED if some downstream point z' > z has
  h(y, z') > h(y, z) + (z' - z) tan(theta_out) (``quantification.shadow.height_field_corner_maxima``,
  the same running maxima; every traced source is asserted visible). A blocked point is never the
  first surface a backward ray meets, so it is not imaged; a riser face met by a backward ray carries
  no specular wave. Upstream of z = z_start the surface continues flat at the declared level (0);
  nothing exists downstream of the exit plane.

Status codes (``STATUS`` of ``forward.geometric.model``): 0 lit surface, 1 surface in the
illumination shadow, 2 riser face, 3 below the local surface at the exit plane, 4 source upstream of
the field of view.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np

from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV
from reflection_holo.forward.contracts import ExitWave
from reflection_holo.forward.geometric.model import (ENGINE_NAME, EXIT_PLANE, GEOMETRIC_LABEL,
                                                     STATUS, OutsideB4ScopeError)
from reflection_holo.geometry.specular import beam_wavevectors_slab
from reflection_holo.geometry.wavelength import k_ang_per_A, wavelength_A
from reflection_holo.io.labels import require_evidence_label
from reflection_holo.quantification.shadow import (HEIGHT_FIELD_PROFILES,
                                                   height_field_corner_maxima)
from reflection_holo.structure.si001 import B4_A4_100, B4_TRANSLATION

_LABEL_PREFIXES = ("PROJECT_INPUT", "ASSUMPTION", "TEST_ONLY")
_EPS_A = 1e-9
_LAYER_TOL_A = 1e-9
_CHUNK_COLUMNS = 96            # columns traced together (memory only; results do not depend on it)
_AZ_100 = {(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)}
B4_HEIGHT_FIELD_100 = (
    "a/4 layers at an exact <100> azimuth: " + B4_A4_100 + "; the terrace relation (Fd-3m d-glide in "
    "the incidence plane for an odd number of layers, lattice translation for an even number) is the "
    "bulk symmetry of C2 section 1, NOT measured on atoms in this path (the atomistic builder must "
    "assert it); exact for infinite terraces, violated near risers (terraces narrower than a few nm "
    "are outside that premise; ignored by the geometric model)")
B4_HEIGHT_FIELD_EVEN = ("even numbers of a/4 layers only (lattice-translation steps): "
                        + B4_TRANSLATION)
B4_CONTINUOUS = ("continuous surface: not a lattice surface, B4 does not apply; TEST_ONLY geometry "
                 "for the ray tracer and the height map (geometric-optics phase -2 k sin(theta) h)")


@dataclass(frozen=True)
class HeightField:
    """Surface h(y, z) of the field of view, in the slab frame (module docstring). No defaults.

    height_fn         h(y, z) in A for broadcast arrays y, z (A); the flat surrounding surface is 0
    profile           "piecewise_constant" or "piecewise_linear" (module docstring)
    layer_spacing_A   the atomic layer spacing the heights are quantised to (a/4 on Si(001)) for
                      "piecewise_constant"; None for "piecewise_linear"
    z_start_A         upstream end of the field of view (the surface continues flat upstream)
    field_length_A    length of the field along the beam; the exit plane is z_start + field_length
    surface_dz_A      cell length (constant) or vertex spacing (linear) along the beam; must divide
                      field_length_A
    upstream_level_A  height of the flat surface upstream of z_start
    description       what the surface is (recorded)
    label, source     evidence label (PROJECT_INPUT / ASSUMPTION Bxx / TEST_ONLY ...) and source of
                      the geometry (PROJECT_INPUT item 13 for a patterned feature)
    """
    height_fn: Callable[[np.ndarray, np.ndarray], np.ndarray]
    profile: str
    layer_spacing_A: float | None
    z_start_A: float
    field_length_A: float
    surface_dz_A: float
    upstream_level_A: float
    description: str
    label: str
    source: str

    def __post_init__(self):
        if not callable(self.height_fn):
            raise TypeError("height_fn must be callable h(y, z)")
        if self.profile not in HEIGHT_FIELD_PROFILES:
            raise ValueError(f"profile must be one of {HEIGHT_FIELD_PROFILES}, got {self.profile!r}")
        if self.profile == "piecewise_constant":
            ls = self.layer_spacing_A
            if ls is None or not (np.isfinite(float(ls)) and float(ls) > 0):
                raise ValueError("a piecewise_constant height field needs layer_spacing_A > 0 (the "
                                 "atomic layer spacing its heights are quantised to)")
            object.__setattr__(self, "layer_spacing_A", float(ls))
        elif self.layer_spacing_A is not None:
            raise ValueError("layer_spacing_A applies to piecewise_constant height fields only")
        for name in ("z_start_A", "upstream_level_A"):
            v = float(getattr(self, name))
            if not np.isfinite(v):
                raise ValueError(f"{name} must be finite")
            object.__setattr__(self, name, v)
        for name in ("field_length_A", "surface_dz_A"):
            v = float(getattr(self, name))
            if not (np.isfinite(v) and v > 0):
                raise ValueError(f"{name} must be finite and > 0")
            object.__setattr__(self, name, v)
        n = self.field_length_A / self.surface_dz_A
        if abs(n - round(n)) > 1e-9 * max(1.0, n) or round(n) < 2:
            raise ValueError(f"surface_dz_A = {self.surface_dz_A} must divide field_length_A = "
                             f"{self.field_length_A} into at least 2 cells")
        for name in ("description", "label", "source"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} must be a non-empty string")
        require_evidence_label(self.label, "height-field geometry (PROJECT_INPUT item 13)",
                               accepted=_LABEL_PREFIXES, qualified=True)

    @property
    def n_cells(self) -> int:
        return int(round(self.field_length_A / self.surface_dz_A))

    @property
    def z_end_A(self) -> float:
        return self.z_start_A + self.n_cells * self.surface_dz_A

    def z_points_A(self) -> np.ndarray:
        """Evaluation points along the beam: cell centres (constant) or vertices (linear)."""
        n, dz, z0 = self.n_cells, self.surface_dz_A, self.z_start_A
        if self.profile == "piecewise_constant":
            return z0 + (np.arange(n) + 0.5) * dz
        return z0 + np.arange(n + 1) * dz

    def sample(self, y_A) -> np.ndarray:
        """Heights (len(y), n_points) at the evaluation points of each column y."""
        y = np.asarray(y_A, dtype=float).reshape(-1)
        z = self.z_points_A()
        h = np.asarray(self.height_fn(y[:, None], z[None, :]), dtype=float)
        h = np.broadcast_to(h, (y.size, z.size)).astype(float, copy=True)
        if not np.all(np.isfinite(h)):
            raise ValueError("height_fn returned non-finite heights")
        if self.profile == "piecewise_constant":
            n = (h - self.upstream_level_A) / self.layer_spacing_A
            if np.max(np.abs(n - np.round(n)), initial=0.0) * self.layer_spacing_A > _LAYER_TOL_A:
                raise ValueError("piecewise_constant heights must be integer multiples of "
                                 "layer_spacing_A above the flat level (atomic top layers)")
        return h

    def as_record(self) -> dict:
        return dict(profile=self.profile, layer_spacing_A=self.layer_spacing_A,
                    z_start_A=self.z_start_A, z_end_A=self.z_end_A,
                    field_length_A=self.field_length_A, surface_dz_A=self.surface_dz_A,
                    n_cells=self.n_cells, upstream_level_A=self.upstream_level_A,
                    description=self.description, label=self.label, source=self.source,
                    upstream="flat surface at upstream_level_A continues upstream of z_start",
                    downstream="nothing downstream of the exit plane z_end",
                    risers=("vertical at the cell boundaries (B13; at most dz/2 from the true "
                            "terrace boundary)" if self.profile == "piecewise_constant" else
                            "none (continuous surface)"))


@dataclass(frozen=True)
class HeightFieldParams:
    """Numerical settings of the height-field engine (no docs/06 item; all required, no defaults).

    exit_plane_pixel_A      (dx, dy) sampling of the exit plane, A
    n_y                     exit-plane samples along y (y = j dy, j = 0 .. n_y - 1)
    x_margin_A              vacuum margin below the lowest and above the highest exit-plane ray, A
    reflectivity_amplitude  |A| of every surface point (no dynamical amplitude; > 0)
    """
    exit_plane_pixel_A: tuple[float, float]
    n_y: int
    x_margin_A: float
    reflectivity_amplitude: float

    def __post_init__(self):
        d = tuple(float(v) for v in self.exit_plane_pixel_A)
        if len(d) != 2 or not all(np.isfinite(v) and v > 0 for v in d):
            raise ValueError(f"exit_plane_pixel_A must be two positive numbers, got "
                             f"{self.exit_plane_pixel_A!r}")
        object.__setattr__(self, "exit_plane_pixel_A", d)
        v = self.n_y
        if isinstance(v, bool) or int(v) != v or int(v) < 2:
            raise ValueError(f"n_y must be an integer >= 2, got {v!r}")
        object.__setattr__(self, "n_y", int(v))
        for name in ("x_margin_A", "reflectivity_amplitude"):
            v = float(getattr(self, name))
            if not (np.isfinite(v) and v > 0):
                raise ValueError(f"{name} must be finite and > 0, got {v!r}")
            object.__setattr__(self, name, v)


def require_b4_scope_height_field(field_: HeightField, *, azimuth_uvw, termination: str,
                                  overlayer, illumination: str, beam: str,
                                  layer_index_parity: str) -> dict:
    """Refuse what the height-field model cannot represent (module docstring); return the B4
    record. ``layer_index_parity``: "any" if the field has terraces differing by an odd number of
    layers (a/4 steps), "even" if every height is an even multiple of the layer spacing."""
    if illumination != "plane_wave":
        raise OutsideB4ScopeError(
            f"illumination {illumination!r}: the geometric model computes one plane-wave "
            f"realisation only; the effect of an azimuthal spread on a/4 steps is not analysed (B4)")
    if beam != "specular":
        raise OutsideB4ScopeError(f"beam {beam!r}: the geometric model returns the specular beam only")
    if termination != "bulk":
        raise OutsideB4ScopeError(f"termination {termination!r}: only the bulk termination (B3) is "
                                  f"in the B4 scope")
    if overlayer is not None:
        raise OutsideB4ScopeError("an overlayer is declared: the geometric model has no overlayer "
                                  "and B4 does not apply to one (model_assumptions B4, B12)")
    az = tuple(int(v) for v in azimuth_uvw)
    if field_.profile == "piecewise_linear":
        if not field_.label.startswith("TEST_ONLY"):
            raise OutsideB4ScopeError("a continuous (piecewise_linear) surface is not a lattice "
                                      "surface: accepted only as a TEST_ONLY geometry")
        return dict(statement=B4_CONTINUOUS, azimuth_uvw=list(az))
    if layer_index_parity not in ("any", "even"):
        raise ValueError("layer_index_parity must be 'any' or 'even'")
    if layer_index_parity == "even":
        return dict(statement=B4_HEIGHT_FIELD_EVEN, azimuth_uvw=list(az))
    if az not in _AZ_100:
        raise OutsideB4ScopeError(
            f"a/4 terraces (odd layer differences) at azimuth {list(az)}: B4 does not apply "
            f"(dynamical residual delta at <110>, open question 3; nothing established elsewhere). "
            f"The geometric phase is not valid; use a dynamical engine (docs/05 sections 0 item 3 "
            f"and 4.5; SM26)")
    return dict(statement=B4_HEIGHT_FIELD_100, azimuth_uvw=list(az))


# --------------------------------------------------------------------------------------------------
# Ray trace
# --------------------------------------------------------------------------------------------------
def _trace_chunk(field_: HeightField, x: np.ndarray, y: np.ndarray, t_in: float, t_out: float):
    H = field_.sample(y)                                        # (C, n_pts)
    c = height_field_corner_maxima(H, z_start_A=field_.z_start_A, dz_A=field_.surface_dz_A,
                                   profile=field_.profile, upstream_level_A=field_.upstream_level_A,
                                   theta_in_ext_rad=math.atan(t_in),
                                   theta_out_ext_rad=math.atan(t_out))
    z, L, W, V = c["z_eval_A"], c["z_end_A"], c["W_up_A"], c["V_down_A"]
    dz, z0 = field_.surface_dz_A, field_.z_start_A
    C, npts = H.shape
    nx = x.size
    if field_.profile == "piecewise_constant":
        zlo = z0 + np.arange(npts) * dz
        key = H + (L - zlo)[None, :] * t_out                    # x of the upstream end of each cell
    else:
        key = H + (L - z)[None, :] * t_out                      # x of each vertex
    M = np.maximum.accumulate(key[:, ::-1], axis=1)[:, ::-1]    # non-increasing along z
    j = np.empty((nx, C), dtype=np.int64)
    for i in range(C):
        j[:, i] = np.searchsorted(-M[i], -x, side="right") - 1  # largest j with M_j >= x
    X = np.broadcast_to(x[:, None], (nx, C))
    cols = np.broadcast_to(np.arange(C)[None, :], (nx, C))
    status = np.full((nx, C), STATUS["outside_field_of_view"], dtype=np.int8)
    zs = np.full((nx, C), np.nan)
    hs = np.full((nx, C), np.nan)
    ill = np.zeros((nx, C), dtype=bool)
    has = j >= 0
    jj = np.clip(j, 0, npts - 1)
    hj = H[cols, jj]
    if field_.profile == "piecewise_constant":
        zhi = z0 + (jj + 1) * dz
        bot = hj + (L - zhi) * t_out
        top_hit = has & (X >= bot - _EPS_A)
        last = jj == npts - 1
        riser = has & ~top_hit & ~last
        below = has & ~top_hit & last
        zsrc = L - (X - hj) / t_out
        hsrc = hj
    else:
        last = jj == npts - 1
        below = has & last & (X < hj - _EPS_A)
        top_hit = has & ~below
        riser = np.zeros_like(has)
        j1 = np.clip(jj + 1, 0, npts - 1)
        k0 = key[cols, jj]
        k1 = key[cols, j1]
        den = np.where(last, 1.0, k0 - k1)
        frac = np.where(last, 0.0, np.clip((k0 - X) / np.where(den > 0, den, 1.0), 0.0, 1.0))
        zsrc = z[jj] + frac * dz
        hsrc = hj + frac * (H[cols, j1] - hj)
    status[riser] = STATUS["riser"]
    status[below] = STATUS["below_surface"]
    zs[top_hit] = zsrc[top_hit]
    hs[top_hit] = hsrc[top_hit]
    w_src = hsrc + zsrc * t_in
    ill[top_hit] = (W[cols, jj] <= w_src + _EPS_A)[top_hit]
    vis_ok = (V[cols, jj] <= X + _EPS_A) | ~top_hit
    if not np.all(vis_ok):
        raise RuntimeError("height-field ray trace and quantification.shadow.height_field_corner_"
                           "maxima disagree: a traced source is not visible; geometry error")
    status[top_hit & ill] = STATUS["lit"]
    status[top_hit & ~ill] = STATUS["illumination_shadow"]
    # hidden (blocked-view) surface between the sources of consecutive rows
    hidden_pt = ~(V <= H + (L - z)[None, :] * t_out + _EPS_A)   # not visible evaluation points
    cum = np.concatenate([np.zeros((C, 1), dtype=np.int64), np.cumsum(hidden_pt, axis=1)], axis=1)
    src = np.where(top_hit, jj, -1)
    hid = np.zeros((nx, C), dtype=bool)
    if nx > 1:
        a, b = src[:-1], src[1:]
        ok = (a >= 0) & (b >= 0)
        lo, hi = np.minimum(a, b), np.maximum(a, b)
        cnt = cum[cols[:-1], np.clip(hi, 0, npts)] - cum[cols[:-1], np.clip(lo + 1, 0, npts)]
        pair = ok & (hi - lo > 1) & (cnt > 0)
        hid[:-1] |= pair
        hid[1:] |= pair
    return dict(status=status, source_z_A=zs, source_h_A=hs, source_index=np.where(has, jj, -1),
                illuminated=ill, hidden_neighbour=hid, hmin=float(H.min()), hmax=float(H.max()))


def trace_height_field(field_: HeightField, x_A, y_A, *, theta_in_ext_rad: float,
                       theta_out_ext_rad: float) -> dict:
    """Ray trace of the exit-plane points (x_A[i], y_A[j]) on the plane z = field_.z_end_A back along
    -k_out (module docstring). ``x_A`` and ``y_A`` are 1-D; every output is (len(x), len(y)):
    status (int8, STATUS codes), source_z_A and source_h_A (NaN unless the ray meets the surface top),
    source_index (cell or vertex index, -1 if none), illuminated, and hidden_neighbour (True where
    blocked-view surface lies between the source of this row and that of row i-1 or i+1: the image
    skips a hidden strip there)."""
    for th in (theta_in_ext_rad, theta_out_ext_rad):
        if not (np.isfinite(th) and 0.0 < th < 0.5 * np.pi):
            raise ValueError("glancing angles must lie in (0, pi/2) rad")
    x = np.asarray(x_A, dtype=float)
    y = np.asarray(y_A, dtype=float)
    if x.ndim != 1 or y.ndim != 1 or x.size < 1 or y.size < 1:
        raise ValueError("x_A and y_A must be non-empty 1-D arrays")
    t_in, t_out = math.tan(theta_in_ext_rad), math.tan(theta_out_ext_rad)
    keys = ("status", "source_z_A", "source_h_A", "source_index", "illuminated", "hidden_neighbour")
    out: dict[str, Any] = {}
    hmin, hmax = np.inf, -np.inf
    for s in range(0, y.size, _CHUNK_COLUMNS):
        r = _trace_chunk(field_, x, y[s:s + _CHUNK_COLUMNS], t_in, t_out)
        hmin, hmax = min(hmin, r["hmin"]), max(hmax, r["hmax"])
        for k in keys:
            if k not in out:
                out[k] = np.empty((x.size, y.size), dtype=r[k].dtype)
            out[k][:, s:s + _CHUNK_COLUMNS] = r[k]
    out["height_range_A"] = (hmin, hmax)
    return out


def height_range_A(field_: HeightField, y_A) -> tuple[float, float]:
    """(min, max) of the sampled heights over the columns y_A."""
    y = np.asarray(y_A, dtype=float).reshape(-1)
    lo, hi = np.inf, -np.inf
    for s in range(0, y.size, _CHUNK_COLUMNS):
        H = field_.sample(y[s:s + _CHUNK_COLUMNS])
        lo, hi = min(lo, float(H.min())), max(hi, float(H.max()))
    return lo, hi


# --------------------------------------------------------------------------------------------------
# The engine
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class HeightFieldRun:
    """Exit wave plus the ray-trace record of the height-field engine."""
    exit_wave: ExitWave
    trace: dict
    x_A: np.ndarray
    y_A: np.ndarray
    field: HeightField
    record: dict = field(default_factory=dict)


def height_field_exit_wave(field_: HeightField, *, energy_keV: float, theta_in_ext_rad: float,
                           theta_label: str, params: HeightFieldParams, b4: dict) -> HeightFieldRun:
    """Specular reflected wave of the height field on the exit plane z = z_end (module docstring).

    energy_keV must be 200 (PROJECT_INPUT item 1); theta_in_ext_rad with its evidence label
    (PROJECT_INPUT item 7 or a registered ASSUMPTION); ``b4``: the record returned by
    ``require_b4_scope_height_field`` (the caller runs the scope check first)."""
    if float(energy_keV) != BEAM_ENERGY_SUPPLIED_KEV:
        raise ValueError(f"beam energy {energy_keV} keV refused: {BEAM_ENERGY_SUPPLIED_KEV:g} keV "
                         f"(PROJECT_INPUT item 1)")
    require_evidence_label(theta_label, "glancing angle (PROJECT_INPUT item 7)",
                           accepted=_LABEL_PREFIXES, qualified=True)
    th = float(theta_in_ext_rad)
    if not (np.isfinite(th) and 0.0 < th < 0.5 * np.pi):
        raise ValueError(f"theta_in_ext_rad must lie in (0, pi/2), got {theta_in_ext_rad!r}")
    if not isinstance(params, HeightFieldParams):
        raise TypeError("params must be a HeightFieldParams")
    if not isinstance(field_, HeightField):
        raise TypeError("field_ must be a HeightField")
    if not (isinstance(b4, dict) and "statement" in b4):
        raise ValueError("b4 must be the record of require_b4_scope_height_field")
    th_out = th
    k = k_ang_per_A(energy_keV)
    lam = wavelength_A(energy_keV)
    k_in, k_out = beam_wavevectors_slab(th, th_out, k)
    q = k_out - k_in
    dx, dy = params.exit_plane_pixel_A
    y = dy * np.arange(params.n_y)
    hmin, hmax = height_range_A(field_, y)
    L = field_.z_end_A
    span = L - field_.z_start_A
    x_lo = min(hmin, field_.upstream_level_A) - params.x_margin_A
    x_hi = max(hmax, field_.upstream_level_A) + span * math.tan(th_out) + params.x_margin_A
    nx = int(math.ceil((x_hi - x_lo) / dx)) + 1
    x = x_lo + dx * np.arange(nx)
    q_band = math.sin(th_out) / lam
    if q_band >= 0.5 / dx:
        raise ValueError(f"exit-plane pixel dx = {dx} A cannot sample the reflected carrier "
                         f"sin(theta)/lambda = {q_band:.4f} cycles/A (Nyquist {0.5 / dx:.4f})")
    tr = trace_height_field(field_, x, y, theta_in_ext_rad=th, theta_out_ext_rad=th_out)
    lit = tr["status"] == STATUS["lit"]
    psi = np.zeros((nx, params.n_y), dtype=np.complex128)
    Xl = np.broadcast_to(x[:, None], psi.shape)[lit]
    psi[lit] = params.reflectivity_amplitude * np.exp(
        1j * (k_out[0] * Xl - q[0] * tr["source_h_A"][lit]))
    counts = {name: int((tr["status"] == c).sum()) for name, c in STATUS.items()}
    metadata = dict(
        engine=ENGINE_NAME + ".height_field", label=GEOMETRIC_LABEL,
        beam="specular (0,0) rod: k_out = k (sin theta_out, 0, cos theta_out), theta_out = theta_in",
        illumination="plane wave, one realisation",
        k_in_rad_per_A=k_in.tolist(), k_out_rad_per_A=k_out.tolist(), q_rad_per_A=q.tolist(),
        wavelength_A=lam, theta_out_ext_rad=th_out, theta_label=theta_label,
        reflectivity_amplitude=params.reflectivity_amplitude,
        reflectivity_label="no dynamical amplitude: one declared |A| for every surface point",
        phase_formula="-(k_out - k_in).(h(y, z) x_hat) = -2 k sin(theta_ext) h per surface point "
                      "(SM03, exp(+ik.r); external angles, vacuum wavelength)",
        height_field=field_.as_record(), height_range_A=[hmin, hmax],
        field_of_view=dict(length_along_beam_A=span, z_start_A=field_.z_start_A, z_end_A=L,
                           upstream="flat surface continues upstream",
                           downstream="nothing downstream of the exit plane"),
        b4=b4, status_codes=dict(STATUS), status_counts=counts,
        precision="complex128", propagation="none (geometric rays; no hidden propagation)",
        z_phase_convention="the constant exp(i k_out,z z_A) on the plane is omitted (envelope with "
                           "respect to propagation along z, as in multislice); the transverse "
                           "carrier exp(i k_out,x x) is included",
        band_limit="none (analytic wave point-sampled at pixel centres)",
        params=dict(exit_plane_pixel_A=list(params.exit_plane_pixel_A), n_y=params.n_y,
                    x_margin_A=params.x_margin_A))
    ew = ExitWave(psi=psi, dx_A=dx, dy_A=dy, x0_A=float(x[0]), y0_A=0.0, plane=EXIT_PLANE, z_A=L,
                  energy_keV=float(energy_keV), theta_in_ext_rad=th, realisation=0, seed=None,
                  metadata=metadata)
    return HeightFieldRun(exit_wave=ew, trace=tr, x_A=x, y_A=y, field=field_,
                          record=dict(n_lit=int(lit.sum()), n_by_status=counts))
