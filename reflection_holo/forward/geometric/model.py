"""Geometric-phase reflection model (docs/05 section 4.5): the fast engine of the pipeline.

Label carried by every output: "geometric model, no dynamical amplitude, B4 scope applies".

What it computes (DERIVED_HERE; source map SM03, SM07; model_assumptions B4, B9, B13):

* The SPECULAR reflected beam only (theta_out = theta_in, k_out = k (sin theta, 0, cos theta) in the
  slab frame of ``reflection_holo.geometry.frames``: x outward normal, y in-plane transverse, z beam
  azimuth). No incident, transmitted or non-specular beam, no dynamical amplitude: every terrace
  reflects with the same declared amplitude |A|.
* The phase of the wave reflected by terrace k is ``-(k_out - k_in).R_k`` (SM03, exp(+ik.r)
  convention), with R_k = H_0 x_hat + the sum of the translation parts of the step relations
  MEASURED ON THE ATOMS by the structure builder (``relation.t_slab_A``) from terrace 0 to k. For a
  lattice-translation (a/2) step this is translation covariance (exact far from the riser). For a
  single-layer (a/4) step it holds only inside the B4 scope (specular beam of a plane wave at an
  exact <100> azimuth, bulk-terminated terraces, no overlayer; SM26); for the specular beam
  q = k_out - k_in is along x_hat, so only the normal component of the screw translation (a/4)
  enters. a/4 steps outside that scope are REFUSED (``OutsideB4ScopeError``), as are overlayers,
  other terminations and non-plane-wave illumination.
* Visibility by ray tracing: every exit-plane point (x, y) of the declared plane z = L (the
  downstream end of the field of view) is traced back along -k_out to the first surface it meets.
  A point on a terrace top is lit only if ``quantification.shadow.shadow_masks`` says it is
  illuminated at theta_in (the illumination shadow of length h/tan(theta_in) behind a riser whose
  upper terrace is upstream); a ray that meets a riser face carries no specular wave; the
  blocked-view strip of length h/tan(theta_out) in front of a riser whose upper terrace is
  downstream is never reached by a backward ray, and shadow.py's visibility of every traced source
  is asserted (the two computations must agree). Risers are vertical at the terrace-boundary
  coordinate (B13). The staircase continues periodically upstream of the field of view (for the
  illumination shadows that reach into it); nothing exists downstream of the exit plane.
* Invisibility (``g.R`` integer, SM03) is detected and recorded for every translation step.

Status codes of the ray trace (``STATUS``): 0 lit terrace top, 1 terrace top in the illumination
shadow, 2 riser face, 3 below the local surface (inside the crystal at the exit plane; not
modelled), 4 source upstream of the field of view.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV, TWO_PI
from reflection_holo.forward.contracts import ExitWave
from reflection_holo.geometry import projection
from reflection_holo.geometry.specular import beam_wavevectors_slab
from reflection_holo.geometry.wavelength import k_ang_per_A, wavelength_A
from reflection_holo.io.labels import require_evidence_label
from reflection_holo.quantification.invisibility import detect_invisibility
from reflection_holo.quantification.shadow import shadow_masks
from reflection_holo.structure.si001 import B4_A4_100, B4_TRANSLATION

GEOMETRIC_LABEL = "geometric model, no dynamical amplitude, B4 scope applies"
ENGINE_NAME = "reflection_holo.forward.geometric"
EXIT_PLANE = "exit plane z = L_z (no further propagation)"
STATUS = {"lit": 0, "illumination_shadow": 1, "riser": 2, "below_surface": 3,
          "outside_field_of_view": 4}
_LABEL_PREFIXES = ("PROJECT_INPUT", "ASSUMPTION", "TEST_ONLY")
_HEIGHT_TOL_A = 1e-9


class OutsideB4ScopeError(ValueError):
    """The geometric model is not valid for this structure or illumination (B4 scope; SM26)."""


@dataclass(frozen=True)
class GeometricParams:
    """Numerical settings of the geometric engine (no docs/06 item; all required, no defaults).

    exit_plane_pixel_A      (dx, dy) sampling of the exit plane, A
    n_y                     number of exit-plane samples along y
    x_margin_A              vacuum margin below the lowest and above the highest exit-plane ray, A
    periods_along_beam      staircase periods laid along the beam (transverse edges) or cell
                            lengths along the beam (parallel edges) forming the field of view
    reflectivity_amplitude  |A| of every terrace (no dynamical amplitude; > 0)
    invisibility_tol_cycles tolerance on |g.R - n| for the invisibility flag (>= 0)
    """
    exit_plane_pixel_A: tuple[float, float]
    n_y: int
    x_margin_A: float
    periods_along_beam: int
    reflectivity_amplitude: float
    invisibility_tol_cycles: float

    def __post_init__(self):
        d = tuple(float(v) for v in self.exit_plane_pixel_A)
        if len(d) != 2 or not all(np.isfinite(v) and v > 0 for v in d):
            raise ValueError(f"exit_plane_pixel_A must be two positive numbers, got "
                             f"{self.exit_plane_pixel_A!r}")
        object.__setattr__(self, "exit_plane_pixel_A", d)
        for name in ("n_y", "periods_along_beam"):
            v = getattr(self, name)
            if isinstance(v, bool) or int(v) != v or int(v) < 1:
                raise ValueError(f"{name} must be a positive integer, got {v!r}")
            object.__setattr__(self, name, int(v))
        if self.n_y < 2:
            raise ValueError("n_y must be >= 2")
        for name, lo in (("x_margin_A", 0.0), ("reflectivity_amplitude", 0.0)):
            v = float(getattr(self, name))
            if not (np.isfinite(v) and v > lo):
                raise ValueError(f"{name} must be finite and > {lo}, got {v!r}")
            object.__setattr__(self, name, v)
        t = float(self.invisibility_tol_cycles)
        if not (np.isfinite(t) and t >= 0):
            raise ValueError("invisibility_tol_cycles must be finite and >= 0")
        object.__setattr__(self, "invisibility_tol_cycles", t)


@dataclass(frozen=True)
class TerraceModel:
    """Terrace map of one period of a built Si(001) staircase, as the geometric model uses it.

    edges            "transverse" (profile along z, the beam) or "parallel" (profile along y)
    period_A         staircase period along its axis (z for transverse, y for parallel edges)
    starts_A         start of each terrace along that axis, in [0, period)
    heights_A        top-layer height of each terrace (slab x), A
    R_A              (n_terraces, 3) vector R_k (slab frame): H_0 x_hat + translation parts of the
                     measured step relations from terrace 0 to k (module docstring)
    R_period_A       sum of the translation parts over one full period (x component 0)
    edge_length_A    cell length along the step edges (the builder's periodic length)
    steps            the builder's step records (type, height, position, relation, B4 statement)
    options          the builder's options record (termination, overlayer)
    """
    edges: str
    period_A: float
    starts_A: tuple
    heights_A: tuple
    R_A: np.ndarray
    R_period_A: np.ndarray
    edge_length_A: float
    steps: tuple
    options: dict
    azimuth_uvw: tuple
    positions_sha256: str

    @property
    def n_terraces(self) -> int:
        return len(self.heights_A)


def terrace_model_from_structure(structure) -> TerraceModel:
    """TerraceModel from a ``reflection_holo.structure.Si001Structure`` (or anything with the
    builder's ``metadata`` and ``cell_A``). The translation parts of the step relations are the
    ones measured on the built atoms; their normal components must equal the terrace height
    differences (checked)."""
    md = structure.metadata
    st = md["staircase"]
    tm = md["terrace_map"]
    edges = st["edges"]
    s_ax = 2 if edges == "transverse" else 1
    e_ax = 1 if edges == "transverse" else 2
    cell = np.asarray(structure.cell_A, float)
    period = float(cell[s_ax, s_ax])
    starts = tuple(float(t["s_range_A"][0]) for t in tm)
    heights = tuple(float(t["top_height_A"]) for t in tm)
    n = len(tm)
    R = np.zeros((n, 3))
    R[0, 0] = heights[0]
    by_from = {s["from_terrace"]: s for s in md["steps"] if not s["at_periodic_boundary"]}
    for k in range(n - 1):
        s = by_from.get(k)
        if s is None or s["to_terrace"] != k + 1:
            raise ValueError(f"builder metadata: no step from terrace {k} to {k + 1}")
        R[k + 1] = R[k] + np.asarray(s["relation"]["t_slab_A"], float)
    R_period = R[-1] - R[0]
    closing = [s for s in md["steps"] if s["at_periodic_boundary"]]
    if closing:
        R_period = R_period + np.asarray(closing[0]["relation"]["t_slab_A"], float)
    if np.max(np.abs(R[:, 0] - np.asarray(heights))) > _HEIGHT_TOL_A:
        raise ValueError("builder metadata: normal components of the step relations do not equal "
                         "the terrace height differences")
    if abs(R_period[0]) > _HEIGHT_TOL_A:
        raise ValueError("builder metadata: the staircase has a net height change per period")
    return TerraceModel(edges=edges, period_A=period, starts_A=starts, heights_A=heights,
                        R_A=R, R_period_A=R_period, edge_length_A=float(cell[e_ax, e_ax]),
                        steps=tuple(md["steps"]), options=dict(md["options"]),
                        azimuth_uvw=tuple(md["azimuth"]["uvw"]),
                        positions_sha256=str(md.get("positions_sha256")))


def require_b4_scope(model: TerraceModel, *, illumination: str, beam: str) -> list[dict]:
    """Refuse (OutsideB4ScopeError) what the geometric model cannot represent; return one record
    per step with the B4 statement that applies.

    illumination must be "plane_wave" (partial-coherence ensembles are not implemented here, and
    the effect of an azimuthal spread on a/4 steps is not analysed, B4); beam must be "specular".
    Refused: an a/4 (screw) step whose builder B4 statement is not the <100> in-scope statement
    (e.g. a <110> azimuth: dynamical residual delta, open question 3); any declared overlayer (B4,
    B12: the geometric model has no overlayer and B4 excludes one); any termination other than
    bulk (B3).
    """
    if illumination != "plane_wave":
        raise OutsideB4ScopeError(
            f"illumination {illumination!r}: the geometric model computes one plane-wave "
            f"realisation only; partial-coherence ensembles are not implemented here and the "
            f"effect of an azimuthal spread on a/4 steps is not analysed (model_assumptions B4)")
    if beam != "specular":
        raise OutsideB4ScopeError(f"beam {beam!r}: the geometric model returns the specular beam "
                                  f"only")
    term = model.options.get("termination", {}).get("value")
    if term != "bulk":
        raise OutsideB4ScopeError(f"termination {term!r}: only the bulk termination (B3) is in "
                                  f"the B4 scope")
    over = model.options.get("overlayer", {}).get("value")
    if over is not None:
        raise OutsideB4ScopeError(
            "an overlayer is declared: the geometric model has no overlayer and B4 does not apply "
            "to one (model_assumptions B4, B12)")
    out = []
    for s in model.steps:
        b4 = s["relation"]["model_assumption_B4"]
        if s["type"] == "screw" and b4 != B4_A4_100:
            raise OutsideB4ScopeError(
                f"a/4 step {s['index']} (terraces {s['from_terrace']} -> {s['to_terrace']}, "
                f"azimuth {list(model.azimuth_uvw)}): B4 {b4}. The geometric phase is not valid "
                f"for it; use a dynamical engine and report the phase difference, not a height "
                f"(docs/05 sections 0 item 3 and 4.5; SM26)")
        if s["type"] == "translation" and b4 != B4_TRANSLATION:
            raise OutsideB4ScopeError(f"step {s['index']}: unexpected B4 statement {b4!r}")
        out.append(dict(step=s["index"], type=s["type"], height_A=s["height_A"],
                        model_assumption_B4=b4))
    return out


# --------------------------------------------------------------------------------------------------
# Profile along the ray and the ray trace
# --------------------------------------------------------------------------------------------------
def _field_terraces(model: TerraceModel, periods: int):
    """Terraces of the field of view along z (transverse edges): starts, ends, heights, terrace
    index within the period, period index."""
    P = model.period_A
    st, en, H, kk, pp = [], [], [], [], []
    n = model.n_terraces
    for p in range(periods):
        for k in range(n):
            a = p * P + model.starts_A[k]
            b = p * P + (model.starts_A[k + 1] if k + 1 < n else P)
            st.append(a)
            en.append(b)
            H.append(model.heights_A[k])
            kk.append(k)
            pp.append(p)
    return (np.asarray(st), np.asarray(en), np.asarray(H), np.asarray(kk, dtype=np.int64),
            np.asarray(pp, dtype=np.int64))


def _illumination_profile(model: TerraceModel, periods: int, theta_in: float):
    """(edges, h_start, heights_after) over the field of view plus enough upstream periods for the
    longest illumination shadow (the staircase continues periodically upstream)."""
    span = max(model.heights_A) - min(model.heights_A)
    up = max(1, int(math.ceil(projection.shadow_length_A(span, theta_in) / model.period_A))) \
        if span > 0 else 1
    st, _, H, _, _ = _field_terraces(model, periods + up)
    st = st - up * model.period_A
    return st[1:], float(H[0]), H[1:]


def trace_exit_points(model: TerraceModel, x_A, y_A, *, field_length_A: float, periods: int,
                      theta_in_ext_rad: float, theta_out_ext_rad: float) -> dict:
    """Ray trace of exit-plane points (x_A, y_A) (broadcast arrays) at z = field_length_A back
    along -k_out (module docstring). Returns arrays: status (int8, STATUS codes), source_z_A (NaN
    unless the ray meets a terrace top), source_terrace (index within the period, -1 if none),
    source_period (-1 if none), and the shadow.py masks at the traced sources."""
    x = np.asarray(x_A, float)
    y = np.asarray(y_A, float)
    x, y = np.broadcast_arrays(x, y)
    L = float(field_length_A)
    t_out = math.tan(theta_out_ext_rad)
    status = np.full(x.shape, STATUS["outside_field_of_view"], dtype=np.int8)
    src_z = np.full(x.shape, np.nan)
    src_k = np.full(x.shape, -1, dtype=np.int64)
    src_p = np.full(x.shape, -1, dtype=np.int64)
    if model.edges == "transverse":
        st, en, H, kk, pp = _field_terraces(model, periods)
        if abs(en[-1] - L) > 1e-9:
            raise ValueError("field_length_A does not match the terrace layout")
        active = x >= H[-1]
        status[~active] = STATUS["below_surface"]
        for k in range(len(H) - 1, -1, -1):
            zh = L - (x - H[k]) / t_out
            hit = active & (zh >= st[k])
            status[hit] = STATUS["lit"]
            src_z[hit] = zh[hit]
            src_k[hit] = kk[k]
            src_p[hit] = pp[k]
            active &= ~hit
            if k > 0 and H[k - 1] > H[k]:
                X = x - (L - st[k]) * t_out           # ray height at the riser
                riser = active & (X < H[k - 1])
                status[riser] = STATUS["riser"]
                active &= ~riser
        # remaining active rays pass above z = 0: their source is upstream of the field of view
        edges, h0, after = _illumination_profile(model, periods, theta_in_ext_rad)
    elif model.edges == "parallel":
        P = model.period_A
        u = np.mod(y, P)
        k_of = np.searchsorted(np.asarray(model.starts_A), u, side="right") - 1
        Hy = np.asarray(model.heights_A)[k_of]
        below = x < Hy
        zh = L - (x - Hy) / t_out
        hit = (~below) & (zh >= 0.0)
        status[below] = STATUS["below_surface"]
        status[hit] = STATUS["lit"]
        src_z[hit] = zh[hit]
        src_k[hit] = k_of[hit]
        src_p[hit] = 0
        edges, h0, after = np.zeros(0), 0.0, np.zeros(0)
    else:
        raise ValueError(f"edges must be 'transverse' or 'parallel', got {model.edges!r}")
    lit = status == STATUS["lit"]
    ill = np.ones(x.shape, dtype=bool)
    vis = np.ones(x.shape, dtype=bool)
    if np.any(lit) and model.edges == "transverse":
        zl = src_z[lit]
        uz, inv = np.unique(zl, return_inverse=True)
        m = shadow_masks(uz, edges_A=edges, h_start_A=h0, heights_after_A=after,
                         theta_in_ext_rad=theta_in_ext_rad, theta_out_ext_rad=theta_out_ext_rad)
        ill[lit] = m.illuminated[inv]
        vis[lit] = m.visible[inv]
        if not np.all(vis[lit]):
            raise RuntimeError("ray trace and quantification.shadow.shadow_masks disagree: a traced "
                               "source is not visible (blocked-view strip); geometry error")
        shadowed = lit & ~ill
        status[shadowed] = STATUS["illumination_shadow"]
    return dict(status=status, source_z_A=src_z, source_terrace=src_k, source_period=src_p,
                illuminated=ill, visible=vis)


# --------------------------------------------------------------------------------------------------
# The engine
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class GeometricRun:
    """Exit wave plus the ray-trace record of the geometric engine."""
    exit_wave: ExitWave
    trace: dict
    x_A: np.ndarray
    y_A: np.ndarray
    field_length_A: float
    record: dict = field(default_factory=dict)


def field_length_A(model: TerraceModel, periods: int) -> float:
    """Length of the field of view along the beam (A)."""
    return float(periods * (model.period_A if model.edges == "transverse" else model.edge_length_A))


def geometric_exit_wave(model: TerraceModel, *, energy_keV: float, theta_in_ext_rad: float,
                        theta_label: str, params: GeometricParams, illumination: str,
                        beam: str) -> GeometricRun:
    """Specular reflected wave on the exit plane z = L of the field of view (module docstring).

    energy_keV must be 200 (PROJECT_INPUT item 1); theta_in_ext_rad with its evidence label
    (PROJECT_INPUT item 7, or a registered ASSUMPTION); illumination "plane_wave" and beam
    "specular" (anything else is refused, ``require_b4_scope``).
    """
    if float(energy_keV) != BEAM_ENERGY_SUPPLIED_KEV:
        raise ValueError(f"beam energy {energy_keV} keV refused: {BEAM_ENERGY_SUPPLIED_KEV:g} keV "
                         f"(PROJECT_INPUT item 1)")
    require_evidence_label(theta_label, "glancing angle (PROJECT_INPUT item 7)",
                           accepted=_LABEL_PREFIXES, qualified=True)
    th = float(theta_in_ext_rad)
    if not (np.isfinite(th) and 0.0 < th < 0.5 * np.pi):
        raise ValueError(f"theta_in_ext_rad must lie in (0, pi/2), got {theta_in_ext_rad!r}")
    if not isinstance(params, GeometricParams):
        raise TypeError("params must be a GeometricParams")
    b4 = require_b4_scope(model, illumination=illumination, beam=beam)
    th_out = th                                            # specular beam
    k = k_ang_per_A(energy_keV)
    lam = wavelength_A(energy_keV)
    k_in, k_out = beam_wavevectors_slab(th, th_out, k)
    q = k_out - k_in
    periods = params.periods_along_beam
    L = field_length_A(model, periods)
    dx, dy = params.exit_plane_pixel_A
    H = np.asarray(model.heights_A)
    x_lo = float(H.min()) - params.x_margin_A
    x_hi = float(H.max()) + L * math.tan(th_out) + params.x_margin_A
    nx = int(math.ceil((x_hi - x_lo) / dx)) + 1
    x = x_lo + dx * np.arange(nx)
    y = dy * np.arange(params.n_y)
    q_band = math.sin(th_out) / lam                          # carrier along x, cycles/A
    if q_band >= 0.5 / dx:
        raise ValueError(f"exit-plane pixel dx = {dx} A cannot sample the reflected carrier "
                         f"sin(theta)/lambda = {q_band:.4f} cycles/A (Nyquist {0.5 / dx:.4f})")
    X, Y = np.meshgrid(x, y, indexing="ij")
    tr = trace_exit_points(model, X, Y, field_length_A=L, periods=periods, theta_in_ext_rad=th,
                           theta_out_ext_rad=th_out)
    lit = tr["status"] == STATUS["lit"]
    # R_k of each lit source (terrace k in period p): R_k + p R_period
    Rk = model.R_A[np.clip(tr["source_terrace"], 0, None)] \
        + tr["source_period"].clip(0, None)[..., None] * model.R_period_A
    terrace_phase = -(Rk @ q)
    carrier = k_out[0] * X                    # exp(i k_out,z z) omitted: envelope convention
    psi = np.zeros(X.shape, dtype=np.complex128)
    psi[lit] = params.reflectivity_amplitude * np.exp(1j * (carrier[lit] + terrace_phase[lit]))
    steps = []
    for s in model.steps:
        rec = dict(index=s["index"], from_terrace=s["from_terrace"], to_terrace=s["to_terrace"],
                   type=s["type"], height_A=s["height_A"], position_A=s["position_A"],
                   at_periodic_boundary=s["at_periodic_boundary"],
                   upper_terrace_upstream=s.get("upper_terrace_upstream"),
                   model_assumption_B4=s["relation"]["model_assumption_B4"],
                   step_phase_rad=float(-(np.asarray(s["relation"]["t_slab_A"]) @ q)))
        if model.edges == "transverse":
            L_sh = projection.shadow_length_A(abs(s["height_A"]), th if s["upper_terrace_upstream"]
                                              else th_out)
            rec["strip"] = ("illumination_shadow (downstream of the riser, theta_in)"
                            if s["upper_terrace_upstream"] else
                            "blocked_view (upstream of the riser, theta_out)")
            rec["nominal_strip_length_A"] = L_sh
        if s["type"] == "translation":
            inv = detect_invisibility(q / TWO_PI, s["relation"]["t_slab_A"],
                                      tol_cycles=params.invisibility_tol_cycles)
            rec["invisibility"] = dict(g_dot_R_cycles=inv.g_dot_R, nearest_integer=inv.nearest_integer,
                                       distance_cycles=inv.distance_cycles, invisible=inv.invisible,
                                       tol_cycles=params.invisibility_tol_cycles)
        else:
            rec["invisibility"] = ("not applicable: screw-related terraces; inside the B4 scope "
                                   "the specular phase is -q.t with t the incidence-plane glide")
        steps.append(rec)
    metadata = dict(
        engine=ENGINE_NAME, label=GEOMETRIC_LABEL,
        beam="specular (0,0) rod: k_out = k (sin theta_out, 0, cos theta_out), theta_out = theta_in",
        illumination="plane wave, one realisation",
        k_in_rad_per_A=k_in.tolist(), k_out_rad_per_A=k_out.tolist(), q_rad_per_A=q.tolist(),
        wavelength_A=lam, theta_out_ext_rad=th_out, theta_label=theta_label,
        reflectivity_amplitude=params.reflectivity_amplitude,
        reflectivity_label="no dynamical amplitude: one declared |A| for every terrace",
        terrace_heights_A=list(model.heights_A), terrace_R_A=model.R_A.tolist(),
        R_period_A=model.R_period_A.tolist(),
        terrace_phase_rad=[float(-(r @ q)) for r in model.R_A],
        phase_formula="-(k_out - k_in).R_k (SM03, exp(+ik.r)); R_k from the relations measured "
                      "on the atoms",
        field_of_view=dict(edges=model.edges, periods_along_beam=periods, length_along_beam_A=L,
                           upstream="staircase continues periodically upstream (illumination)",
                           downstream="nothing downstream of the exit plane"),
        steps=steps, b4=b4, status_codes=dict(STATUS),
        maps=dict(status=tr["status"], source_z_A=tr["source_z_A"],
                  source_terrace=tr["source_terrace"], source_period=tr["source_period"]),
        precision="complex128", propagation="none (geometric rays; no hidden propagation)",
        z_phase_convention="the constant exp(i k_out,z z_A) on the plane is omitted (envelope with "
                           "respect to propagation along z, as in multislice); the transverse "
                           "carrier exp(i k_out,x x) is included",
        band_limit="none (analytic wave point-sampled at pixel centres)",
        structure_positions_sha256=model.positions_sha256,
        params=dict(exit_plane_pixel_A=list(params.exit_plane_pixel_A), n_y=params.n_y,
                    x_margin_A=params.x_margin_A, periods_along_beam=periods,
                    invisibility_tol_cycles=params.invisibility_tol_cycles),
    )
    ew = ExitWave(psi=psi, dx_A=dx, dy_A=dy, x0_A=float(x[0]), y0_A=0.0, plane=EXIT_PLANE, z_A=L,
                  energy_keV=float(energy_keV), theta_in_ext_rad=th, realisation=0, seed=None,
                  metadata=metadata)
    return GeometricRun(exit_wave=ew, trace=tr, x_A=x, y_A=y, field_length_A=L,
                        record=dict(n_lit=int(lit.sum()),
                                    n_by_status={name: int((tr["status"] == c).sum())
                                                 for name, c in STATUS.items()}))
