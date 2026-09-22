"""Shadowed surface strips at grazing incidence (source map SM07; model_assumptions B9; docs/03 sec. 4).

Geometry (DERIVED_HERE, docs/physics_conventions.md): the beam travels along +z (the azimuth) and
descends towards the surface at the EXTERNAL glancing angle theta_ext. A surface point at (z, H(z))
is shadowed when an upstream surface point (z', H(z')), z' < z, lies above the incident ray through
it, i.e. when ``H(z') - (z - z') tan(theta_ext) > H(z)``. A step transverse to the beam whose upper
terrace is upstream (a step descending along the beam; SM07 and B9 call it an up-step, seen from the
shadowed terrace) therefore shadows a strip of length ``h / tan(theta_ext)`` behind it, unless the
next rise cuts the strip short. Step edges parallel to the beam cast no shadow along the beam.
The reflected beam leaves at the EXTERNAL exit angle theta_out; a surface point is in the
blocked-view strip when a downstream surface point (z', H(z')), z' > z, lies above the outgoing ray
through it, ``H(z') - (z' - z) tan(theta_out) > H(z)``. By the mirror z -> -z this is the
illumination condition of the mirrored profile (DERIVED_HERE; ``blocked_view_intervals``).

Terrace staircases (``terrace_shadow_strips``) return both strips of docs/03 section 4: the
illumination shadow ``h / tan(theta_in)`` behind (downstream of) a riser whose upper terrace is
upstream, and the blocked-view strip ``h / tan(theta_out)`` in front of (upstream of) a riser whose
upper terrace is downstream, where the beam reflected by the lower terrace is intercepted by the
riser. For the specular beam (theta_out = theta_in) the two lengths are equal. The masking decisions
are delegated to ``reflection_holo.quantification.shadow.shadow_masks``. That function is
evaluated between exact strip ends, so the intervals are exact. The exit angle is a required,
labelled argument.

Patterned features (``feature_shadow_intervals``, ``feature_shadow_mask``) have the same API: the
exit angle is required, and both strips are returned per transverse edge, with a field for each
strip alone. An edge whose upper side is downstream (mesa front, trench back wall) gets a
blocked-view strip in front of it; an edge whose upper side is upstream (mesa back, trench front
wall) gets an illumination shadow behind it. Their profiles have sloped sidewalls, which
``quantification.shadow.shadow_masks`` (vertical risers only) does not handle, so they are
ray-traced here, exactly for the piecewise-linear profile. Sloped (linear) edges, DERIVED_HERE
from that ray trace: a sidewall steeper than the ray that meets it (alpha > theta_in for a wall
falling along the beam, alpha > theta_out for a wall rising along the beam) lies inside its strip,
and the strip is measured from the TOP edge of the wall, length h / tan(theta), i.e.
h / tan(theta) - h / tan(alpha) beyond the foot. A sidewall at or below that angle casts no
strip (grazing counts as lit or visible). The two walls of one feature are compared with
different angles when theta_out != theta_in.

The features part implements the patterned mesas and trenches of PROJECT_INPUT item 13 as a height
profile with every geometric parameter REQUIRED; their atomistic realisation is NOT IMPLEMENTED.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from reflection_holo.geometry import projection
from reflection_holo.io.labels import require_evidence_label
from reflection_holo.quantification import shadow as quantification_shadow

from .si001 import LABEL_PREFIXES

_F_TOL_A = 1e-9          # tolerance on H + z tan(theta) when deciding shadowing (angstrom)
_BREAK_TOL_A = 1e-6      # candidate strip ends closer than this are merged (degenerate cases only)
_EXIT_ANGLE_WHAT = "external exit angle theta_out (item 7 for the specular beam)"


def _check_theta(theta_ext_rad: float, theta_label: str, *, name: str = "theta_ext_rad",
                 what: str = "external glancing angle (PROJECT_INPUT item 7)") -> float:
    require_evidence_label(theta_label, what, accepted=LABEL_PREFIXES, qualified=True)
    th = float(theta_ext_rad)
    if not (np.isfinite(th) and 0.0 < th < 0.5 * np.pi):
        raise ValueError(f"{name} must be in (0, pi/2), got {theta_ext_rad!r}")
    return th


def shadow_length_A(height_A: float, theta_ext_rad: float, theta_label: str) -> float:
    """Shadow length ``|h| / tan(theta_ext)`` of a transverse step of height h (SM07, B9), with the
    evidence label of theta_ext required (PROJECT_INPUT item 7).

    Labelled wrapper only: the value is computed by the canonical
    ``reflection_holo.geometry.projection.shadow_length_A`` (spec section 4.1, "shadow length
    h/tan(theta_ext)"); this module has no copy of the formula.
    """
    return projection.shadow_length_A(height_A, _check_theta(theta_ext_rad, theta_label))


# --------------------------------------------------------------------------------------------------
# Ray trace of a piecewise-linear profile
# --------------------------------------------------------------------------------------------------
def _merge(intervals, tol=_F_TOL_A):
    iv = sorted((float(a), float(b)) for a, b in intervals if b - a > tol)
    out: list[list[float]] = []
    for a, b in iv:
        if out and a <= out[-1][1] + tol:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out]


def shadowed_intervals(points, tan_theta: float):
    """Shadowed surface intervals [z0, z1) of a piecewise-linear height profile.

    ``points`` is a sequence of (z, H) with non-decreasing z; consecutive points at the same z form a
    vertical riser. The beam enters from z = -inf; nothing upstream of the first point is higher
    than it. Exact for the profile (sweep of the running maximum of H + z tan(theta)).
    """
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[1] != 2 or len(pts) < 2:
        raise ValueError("points must be a sequence of at least two (z, H) pairs")
    if np.any(np.diff(pts[:, 0]) < 0):
        raise ValueError("profile z coordinates must be non-decreasing")
    t = float(tan_theta)
    C = -np.inf
    out = []
    for k in range(len(pts) - 1):
        z0, H0 = pts[k]
        z1, H1 = pts[k + 1]
        f0, f1 = H0 + z0 * t, H1 + z1 * t
        if z1 > z0:
            if f1 >= f0:                          # surface faces the beam (or grazes it)
                if C > f0 + _F_TOL_A:
                    zs = z1 if f1 == f0 else z0 + (C - f0) / (f1 - f0) * (z1 - z0)
                    out.append((z0, min(zs, z1)))
            else:                                 # surface descends more steeply than the ray
                out.append((z0, z1))
        C = max(C, f0, f1)
    return _merge(out)


def periodic_shadowed_intervals(points_one_period, period_A: float, tan_theta: float):
    """Shadowed intervals of a profile periodic in z with period ``period_A``.

    ``points_one_period`` covers [0, period]; the next period restarts at its first point, so a
    height mismatch between the last and first points is a riser at the cell edge. The profile is
    unrolled over enough periods for the longest possible shadow; intervals are returned in
    [0, period], an interval crossing the cell edge appearing as [a, period) and [0, b).

    Floating point: the period offsets are accumulated, o_(k+1) = o_k + period. The end of period
    k, fl(period + o_k), is then bit-identical to the start of period k + 1, fl(0 + o_(k+1)), and
    since rounding is monotone the unrolled z is non-decreasing for any period. The earlier
    ``pts + k * period`` could break this by one ulp (e.g. period 0.2 A or 1-2 x P110). The end
    point, accepted by the existing check |z_end - period| <= _F_TOL_A (1e-9 A, unchanged), is
    placed exactly at the period, and so is any point in that accepted band above it. No new
    tolerance is introduced.
    """
    pts = np.asarray(points_one_period, dtype=float)
    Lp = float(period_A)
    if pts[0, 0] != 0.0 or abs(pts[-1, 0] - Lp) > _F_TOL_A:
        raise ValueError("points_one_period must start at z = 0 and end at z = period")
    if np.any(np.diff(pts[:, 0]) < 0):
        raise ValueError("profile z coordinates must be non-decreasing")
    z = np.minimum(pts[:, 0], Lp)
    z[-1] = Lp
    span = float(pts[:, 1].max() - pts[:, 1].min())
    reps = int(np.ceil(span / tan_theta / Lp)) + 2
    offsets = [0.0]
    for _ in range(reps - 1):
        offsets.append(offsets[-1] + Lp)
    unrolled = np.concatenate([np.column_stack([z + o, pts[:, 1]]) for o in offsets])
    last = offsets[-1]
    end = last + Lp                        # bit-identical to the final unrolled z
    out = []
    for a, b in shadowed_intervals(unrolled, tan_theta):
        lo, hi = max(a, last), min(b, end)
        if hi > lo:
            out.append((0.0 if lo == last else lo - last, Lp if hi == end else hi - last))
    return _merge(out)


def blocked_view_intervals(points, tan_theta_out: float):
    """Blocked-view surface intervals [z0, z1) of a piecewise-linear height profile (DERIVED_HERE).

    A surface point is blocked when a downstream surface point lies above the outgoing ray (rising
    along +z at theta_out) through it. The mirror z -> -z turns this into the illumination
    condition of the mirrored profile, so the result is ``shadowed_intervals`` of the mirrored
    profile at tan(theta_out), mirrored back. Nothing downstream of the last point may be higher
    than it. Exact for the profile. The blocked set is open at both ends; like the illumination
    intervals it is reported half-open, a difference of measure zero.
    """
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[1] != 2 or len(pts) < 2:
        raise ValueError("points must be a sequence of at least two (z, H) pairs")
    mirrored = np.column_stack([-pts[::-1, 0], pts[::-1, 1]])
    return _merge([(-b, -a) for a, b in shadowed_intervals(mirrored, tan_theta_out)])


def intervals_to_mask(intervals, coords_A, period_A: float | None = None) -> np.ndarray:
    """Boolean mask of coordinates inside any half-open interval [a, b) (wrapped if periodic)."""
    u = np.asarray(coords_A, dtype=float)
    if period_A is not None:
        u = np.mod(u, float(period_A))
    m = np.zeros(u.shape, dtype=bool)
    for a, b in intervals:
        m |= (u >= a) & (u < b)
    return m


# --------------------------------------------------------------------------------------------------
# Terrace staircases built by si001.build_si001_terraces
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class ShadowStrips:
    """Strips to mask on the surface, along the beam coordinate z of the slab frame (docs/03
    section 4). Intervals are half-open [a, b) in [0, period]; an interval crossing the cell edge
    appears as [a, period) and [0, b).

    illumination_intervals_A  illumination shadow at theta_in, behind (downstream of) a riser whose
                              upper terrace is upstream
    blocked_view_intervals_A  blocked-view strip at theta_out, in front of (upstream of) a riser
                              whose upper terrace is downstream
    intervals_A               the union of the two: every strip to mask
    theta_ext_rad, theta_label          incidence angle theta_in and its evidence label
    theta_out_ext_rad, theta_out_label  exit angle theta_out and its evidence label
    per_step                  one record per step (staircases) or per transverse edge on the line
                              (patterned features): which strip applies, its side, nominal extent
    period_A                  the cell period (staircases) or None (features, not periodic)
    """
    axis: str
    intervals_A: tuple
    illumination_intervals_A: tuple
    blocked_view_intervals_A: tuple
    period_A: float | None
    theta_ext_rad: float
    theta_label: str
    theta_out_ext_rad: float
    theta_out_label: str
    per_step: tuple
    note: str

    def mask(self, z_A) -> np.ndarray:
        """Every strip to mask (illumination shadow or blocked view)."""
        return intervals_to_mask(self.intervals_A, z_A, self.period_A)

    def illumination_mask(self, z_A) -> np.ndarray:
        return intervals_to_mask(self.illumination_intervals_A, z_A, self.period_A)

    def blocked_view_mask(self, z_A) -> np.ndarray:
        return intervals_to_mask(self.blocked_view_intervals_A, z_A, self.period_A)


def _periodic_terrace_strips(starts_A, tops_A, period_A: float, th_in: float, th_out: float):
    """Exact illumination-shadow and blocked-view intervals in [0, period] of a periodic,
    piecewise-constant terrace profile with vertical risers. Terrace k starts at starts_A[k] (with
    starts_A[0] = 0) and has top height tops_A[k].

    The masking decisions are made by ``quantification.shadow.shadow_masks``. The profile is
    unrolled over enough periods on both sides for the longest strip. The candidate strip ends in
    [0, period] are every riser and, for each riser corner and each lower terrace level,
    riser + dh / tan(theta_in) and riser - dh / tan(theta_out)
    (``geometry.projection.shadow_length_A``). The masks
    are evaluated at the midpoints between consecutive candidates. They are constant between
    candidates, so the intervals are exact, except where two candidates lie within _BREAK_TOL_A of
    each other.
    """
    starts = [float(v) for v in starts_A]
    tops = [float(v) for v in tops_A]
    Lp = float(period_A)
    if max(tops) == min(tops):
        return [], []
    span = max(tops) - min(tops)
    reach = max(projection.shadow_length_A(span, th_in), projection.shadow_length_A(span, th_out))
    reps = int(math.ceil(reach / Lp)) + 1
    edges, after = [], []
    for k in range(-reps, reps + 1):
        for z0, top in zip(starts, tops):
            edges.append(z0 + k * Lp)
            after.append(top)
    before = [tops[-1]] + after[:-1]
    levels = sorted(set(tops))
    cand = set()
    for e, hb, ha in zip(edges, before, after):
        cand.add(e)
        corner = max(hb, ha)
        for lv in levels:
            if lv < corner:
                cand.add(e + projection.shadow_length_A(corner - lv, th_in))
                cand.add(e - projection.shadow_length_A(corner - lv, th_out))
    pts = [0.0]
    for z in sorted(c for c in cand if _BREAK_TOL_A < c < Lp - _BREAK_TOL_A):
        if z - pts[-1] > _BREAK_TOL_A:
            pts.append(z)
    pts.append(Lp)
    mid = 0.5 * (np.asarray(pts[:-1]) + np.asarray(pts[1:]))
    m = quantification_shadow.shadow_masks(mid, edges_A=edges, h_start_A=tops[-1],
                                           heights_after_A=after, theta_in_ext_rad=th_in,
                                           theta_out_ext_rad=th_out)

    def runs(flags):
        return _merge([(a, b) for a, b, f in zip(pts[:-1], pts[1:], flags) if f])

    return runs(~m.illuminated), runs(~m.visible)


def terrace_shadow_strips(structure, theta_ext_rad: float, theta_label: str, *,
                          theta_out_ext_rad: float, theta_out_label: str) -> ShadowStrips:
    """Illumination shadow and blocked-view strips of a built Si(001) staircase (docs/03 section 4).

    theta_ext_rad, theta_label          external glancing angle of incidence theta_in (PROJECT_INPUT
                                        item 7) and its evidence label
    theta_out_ext_rad, theta_out_label  external exit angle theta_out and its evidence label (equal
                                        to theta_in for the specular beam; required, no default)
    The step riser is placed at the terrace boundary coordinate of the terrace map (the atomistic
    riser is one row wide). For edges parallel to the beam all lists are empty. Each per-step record
    gives the strip that applies: "illumination_shadow" (downstream of the riser, nominal length
    |h| / tan(theta_in)) when the upper terrace is upstream, "blocked_view" (upstream of the riser,
    nominal length |h| / tan(theta_out)) when it is downstream. Nominal means before any cut by a
    neighbouring rise; the intervals include those cuts.
    """
    th = _check_theta(theta_ext_rad, theta_label)
    th_out = _check_theta(theta_out_ext_rad, theta_out_label, name="theta_out_ext_rad",
                          what=_EXIT_ANGLE_WHAT)
    md = structure.metadata
    st = md["staircase"]
    Lz = float(structure.cell_A[2, 2])
    common = dict(axis="z", period_A=Lz, theta_ext_rad=th, theta_label=theta_label,
                  theta_out_ext_rad=th_out, theta_out_label=theta_out_label)
    if st["edges"] == "parallel":
        return ShadowStrips(intervals_A=(), illumination_intervals_A=(),
                            blocked_view_intervals_A=(), per_step=(),
                            note="step edges parallel to the beam: no shadow along the beam",
                            **common)
    tm = md["terrace_map"]
    ill, blk = _periodic_terrace_strips([t["s_range_A"][0] for t in tm],
                                        [t["top_height_A"] for t in tm], Lz, th, th_out)
    per_step = []
    for s in md["steps"]:
        h = abs(s["height_A"])
        pos = s["position_A"]
        if s["upper_terrace_upstream"]:
            L_in = projection.shadow_length_A(h, th)
            rec = dict(strip="illumination_shadow", strip_side="downstream of the riser",
                       strip_angle="theta_in", nominal_strip_A=(pos, pos + L_in),
                       nominal_shadow_length_A=L_in, nominal_blocked_view_length_A=0.0)
        else:
            L_out = projection.shadow_length_A(h, th_out)
            rec = dict(strip="blocked_view", strip_side="upstream of the riser (in front of it)",
                       strip_angle="theta_out", nominal_strip_A=(pos - L_out, pos),
                       nominal_shadow_length_A=0.0, nominal_blocked_view_length_A=L_out)
        per_step.append(dict(step=s["index"], position_A=pos, height_A=h,
                             upper_terrace_upstream=s["upper_terrace_upstream"], **rec))
    return ShadowStrips(intervals_A=tuple(_merge(list(ill) + list(blk))),
                        illumination_intervals_A=tuple(ill), blocked_view_intervals_A=tuple(blk),
                        per_step=tuple(per_step),
                        note="illumination shadow (theta_in) and blocked-view strip (theta_out), "
                             "docs/03 section 4; masks from quantification.shadow.shadow_masks; "
                             "riser at the terrace boundary coordinate",
                        **common)


# --------------------------------------------------------------------------------------------------
# Patterned features (PROJECT_INPUT item 13)
# --------------------------------------------------------------------------------------------------
@dataclass(frozen=True)
class EdgeProfile:
    """Edge profile of a patterned feature (PROJECT_INPUT item 13).

    kind 'vertical' (sidewall_angle_rad must be None) or 'linear' (sidewall_angle_rad required: the
    angle between the sidewall and the surface plane, in (0, pi/2)). Other profiles are NOT
    IMPLEMENTED.
    """
    kind: str
    sidewall_angle_rad: float | None


@dataclass(frozen=True)
class PatternedFeature:
    """A rectangular mesa or trench (PROJECT_INPUT item 13; every field required, no defaults).

    kind                 'mesa' (raised by height_A) or 'trench' (floor at -height_A)
    height_A             mesa height or trench depth, > 0
    lateral_dimensions_A (d1, d2): side lengths of the rectangle
    dimensions_at        'top' (mesa top face / trench opening) or 'base' (mesa foot / trench floor)
    orientation_deg      angle between side d1 and the beam azimuth; only 0 and 90 are implemented
    edge_profile         :class:`EdgeProfile`
    center_A             (y, z) of the rectangle centre in the slab frame
    label                evidence label (PROJECT_INPUT item 13 ..., TEST_ONLY ...)
    """
    kind: str
    height_A: float
    lateral_dimensions_A: tuple
    dimensions_at: str
    orientation_deg: float
    edge_profile: EdgeProfile
    center_A: tuple
    label: str


def _feature_geometry(f: PatternedFeature):
    require_evidence_label(f.label, "patterned feature (PROJECT_INPUT item 13)",
                           accepted=LABEL_PREFIXES, qualified=True)
    if f.kind not in ("mesa", "trench"):
        raise ValueError("kind must be 'mesa' or 'trench'")
    h = float(f.height_A)
    if not (np.isfinite(h) and h > 0.0):
        raise ValueError("height_A must be positive")
    d1, d2 = (float(v) for v in f.lateral_dimensions_A)
    if not (d1 > 0.0 and d2 > 0.0):
        raise ValueError("lateral dimensions must be positive")
    if f.dimensions_at not in ("top", "base"):
        raise ValueError("dimensions_at must be 'top' or 'base'")
    o = float(f.orientation_deg) % 180.0
    if o == 0.0:
        along, across = d1, d2
    elif o == 90.0:
        along, across = d2, d1
    else:
        raise NotImplementedError("feature orientations other than 0 or 90 degrees to the beam "
                                  "need a 2-D ray trace: NOT IMPLEMENTED")
    ep = f.edge_profile
    if not isinstance(ep, EdgeProfile):
        raise TypeError("edge_profile must be an EdgeProfile")
    if ep.kind == "vertical":
        if ep.sidewall_angle_rad is not None:
            raise ValueError("a vertical edge profile takes sidewall_angle_rad=None")
        run = 0.0
    elif ep.kind == "linear":
        al = ep.sidewall_angle_rad
        if al is None or not (0.0 < float(al) < 0.5 * np.pi):
            raise ValueError("a linear edge profile requires sidewall_angle_rad in (0, pi/2)")
        run = h / math.tan(float(al))
    else:
        raise NotImplementedError(f"edge profile {ep.kind!r}: NOT IMPLEMENTED")
    # half-lengths of the upper and lower faces (mesa: top/foot; trench: opening/floor)
    upper_is_top = (f.kind == "mesa")
    if f.dimensions_at == "top":
        # mesa: dims of top face (smaller); trench: dims of the opening (larger)
        small = (along, across) if upper_is_top else (along - 2 * run, across - 2 * run)
        big = (along + 2 * run, across + 2 * run) if upper_is_top else (along, across)
    else:
        small = (along - 2 * run, across - 2 * run) if upper_is_top else (along, across)
        big = (along, across) if upper_is_top else (along + 2 * run, across + 2 * run)
    if min(small) <= 0.0:
        raise ValueError("the sidewalls consume the whole feature: inconsistent dimensions")
    yc, zc = (float(v) for v in f.center_A)
    return dict(h=h, run=run, small=small, big=big, yc=yc, zc=zc, mesa=upper_is_top)


def feature_profile_along_beam(feature: PatternedFeature, y_A: float, margin_A: float):
    """Height profile H(z) of the feature on the line y = y_A, as (z, H) points, with flat margins
    of ``margin_A`` upstream and downstream. Surrounding surface at H = 0."""
    g = _feature_geometry(feature)
    h, run, zc = g["h"], g["run"], g["zc"]
    # 'big' is the outline at H = 0 (mesa foot, trench opening); the sidewalls are planes of the
    # same angle on all four sides, so on the line y = y_A the feature is a trapezoid of local
    # height hy (reduced where the line crosses a sloped side wall parallel to the beam)
    zb = 0.5 * g["big"][0]
    half_y = 0.5 * g["big"][1]
    dy = abs(float(y_A) - g["yc"])
    if dy >= half_y:
        return [(zc - zb - margin_A, 0.0), (zc + zb + margin_A, 0.0)]
    hy = h if run == 0.0 else min(h, h * (half_y - dy) / run)
    zi = zb - (hy / h) * run                   # half-length of the inner face at height +-hy
    sgn = 1.0 if g["mesa"] else -1.0
    return [(zc - zb - margin_A, 0.0), (zc - zb, 0.0), (zc - zi, sgn * hy), (zc + zi, sgn * hy),
            (zc + zb, 0.0), (zc + zb + margin_A, 0.0)]


def _feature_edge_records(profile, th_in: float, th_out: float) -> tuple:
    """Per-edge records of the transverse edges on one feature profile line (DERIVED_HERE; see the
    module docstring for the sloped-edge rule). Empty when the line misses the feature."""
    if len(profile) != 6:
        return ()
    recs = []
    for name, (za, Ha), (zb, Hb) in (("upstream", profile[1], profile[2]),
                                     ("downstream", profile[3], profile[4])):
        rising = Hb > Ha                                 # height increases along the beam
        hy = abs(Hb - Ha)
        z_top, z_foot = (zb, za) if rising else (za, zb)
        run = abs(zb - za)
        if rising:                                       # upper side downstream: blocked view
            th, strip, side, angle = (th_out, "blocked_view",
                                      "upstream of the edge (in front of it)", "theta_out")
        else:                                            # upper side upstream: illumination
            th, strip, side, angle = (th_in, "illumination_shadow",
                                      "downstream of the edge (behind it)", "theta_in")
        length = projection.shadow_length_A(hy, th)
        casts = run < length                             # tan(alpha) = hy/run > tan(theta)
        nominal = None
        if casts:
            nominal = (z_top - length, z_top) if rising else (z_top, z_top + length)
        recs.append(dict(edge=name, rising_along_beam=rising, upper_terrace_upstream=not rising,
                         strip=strip, strip_side=side, strip_angle=angle, height_A=hy,
                         top_edge_A=z_top, foot_A=z_foot, sidewall_run_A=run,
                         casts_strip=casts, sidewall_in_strip=bool(casts and run > 0.0),
                         nominal_strip_A=nominal, nominal_length_A=length if casts else 0.0))
    return tuple(recs)


def feature_shadow_intervals(feature: PatternedFeature, theta_ext_rad: float, theta_label: str,
                             y_A: float | None = None, *, theta_out_ext_rad: float,
                             theta_out_label: str) -> ShadowStrips:
    """Illumination shadow and blocked-view strips on the line y = y_A (default: the feature's
    centre line), as a :class:`ShadowStrips` with period_A None.

    theta_ext_rad, theta_label          external glancing angle of incidence (PROJECT_INPUT item 7)
    theta_out_ext_rad, theta_out_label  external exit angle (item 7: equal to the incidence angle
                                        for the specular beam); required, no default
    ``per_step`` holds one record per transverse edge crossed by the line (see the module docstring
    for the sloped-edge rule, DERIVED_HERE).
    """
    th = _check_theta(theta_ext_rad, theta_label)
    th_out = _check_theta(theta_out_ext_rad, theta_out_label, name="theta_out_ext_rad",
                          what=_EXIT_ANGLE_WHAT)
    g = _feature_geometry(feature)
    margin = (max(projection.shadow_length_A(g["h"], th),
                  projection.shadow_length_A(g["h"], th_out)) + g["big"][0] + 1.0)
    y = g["yc"] if y_A is None else float(y_A)
    prof = feature_profile_along_beam(feature, y, margin)
    ill = shadowed_intervals(prof, math.tan(th))
    blk = blocked_view_intervals(prof, math.tan(th_out))
    return ShadowStrips(axis="z", intervals_A=tuple(_merge(ill + blk)),
                        illumination_intervals_A=tuple(ill), blocked_view_intervals_A=tuple(blk),
                        period_A=None, theta_ext_rad=th, theta_label=theta_label,
                        theta_out_ext_rad=th_out, theta_out_label=theta_out_label,
                        per_step=_feature_edge_records(prof, th, th_out),
                        note="patterned feature: illumination shadow (theta_in) and blocked-view "
                             "strip (theta_out) on one line along the beam; exact ray trace of "
                             "the piecewise-linear profile (DERIVED_HERE)")


@dataclass(frozen=True, eq=False)
class FeatureShadowMasks:
    """Masks of a patterned feature on the grid (y_A[i], z_A[j]) of the slab frame, shape (ny, nz).

    mask               every strip to mask (union)
    illumination_mask  illumination shadow alone (theta_in)
    blocked_view_mask  blocked-view strip alone (theta_out)
    """
    mask: np.ndarray
    illumination_mask: np.ndarray
    blocked_view_mask: np.ndarray
    y_A: np.ndarray
    z_A: np.ndarray
    theta_ext_rad: float
    theta_label: str
    theta_out_ext_rad: float
    theta_out_label: str


def feature_shadow_mask(feature: PatternedFeature, theta_ext_rad: float, theta_label: str,
                        y_A, z_A, *, theta_out_ext_rad: float,
                        theta_out_label: str) -> FeatureShadowMasks:
    """Illumination-shadow and blocked-view masks on the grid (y_A[i], z_A[j]), shape (ny, nz),
    one ray-traced line per y (``feature_shadow_intervals``). Exit angle required, no default."""
    th = _check_theta(theta_ext_rad, theta_label)
    th_out = _check_theta(theta_out_ext_rad, theta_out_label, name="theta_out_ext_rad",
                          what=_EXIT_ANGLE_WHAT)
    y = np.asarray(y_A, float)
    z = np.asarray(z_A, float)
    ill = np.zeros((y.size, z.size), dtype=bool)
    blk = np.zeros((y.size, z.size), dtype=bool)
    for i, yi in enumerate(y):
        sh = feature_shadow_intervals(feature, th, theta_label, yi, theta_out_ext_rad=th_out,
                                      theta_out_label=theta_out_label)
        ill[i] = sh.illumination_mask(z)
        blk[i] = sh.blocked_view_mask(z)
    return FeatureShadowMasks(mask=ill | blk, illumination_mask=ill, blocked_view_mask=blk,
                              y_A=y, z_A=z, theta_ext_rad=th, theta_label=theta_label,
                              theta_out_ext_rad=th_out, theta_out_label=theta_out_label)
