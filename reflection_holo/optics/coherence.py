"""Partial spatial coherence from the illumination convergence (PROJECT_INPUT item 3; report E3;
H2 N3; docs/05 section 5 item 4; docs/03 section 4; model_assumptions B10, B21).

The illumination is an INCOHERENT superposition of plane waves whose directions fill a source
distribution of semi-angle alpha around the central direction b0 (the condenser aperture seen from
the specimen). Each direction ("member") is an independent coherent calculation: one engine run
(forward.multislice.convergence) and one hologram |u_o,s + u_r,s|^2. The partially coherent hologram
is the WEIGHTED MEAN OF THE MEMBER INTENSITIES (after squaring, SM13), never of the waves:

    I(r) = sum_s w_s I_s(r),   sum_s w_s = 1.                                         (1)

Geometry (DERIVED_HERE; docs/physics_conventions.md frame: x outward normal, y transverse, z beam
azimuth; exp(+i k.r)). The central incident direction is b0 = (-sin th0, 0, cos th0). The member
offsets t = (t_a, t_b) are coordinates in the plane perpendicular to b0 with the unit vectors
e_a = (-cos th0, 0, -sin th0) (t_a > 0 INCREASES the glancing angle) and e_b = (0, 1, 0):

    u_s = sqrt(1 - t_a^2 - t_b^2) b0 + t_a e_a + t_b e_b                               (2)

exactly (unit vector). Its glancing angle is th_s = asin(-u_x) = asin(sqrt(1 - t^2) sin th0 +
t_a cos th0) and its y direction cosine u_y = t_b; the tilt of docs/physics_conventions.md is
(theta_x, theta_y) = lambda (q - q0) = (u_x + sin th0, t_b). The incident wavevector changes by
dk_s = k (u_s - b0); the specular outgoing direction is u_s with u_x reversed (parallel momentum
conserved), dk_out,s = k (mirror(u_s) - mirror(b0)).

Source profiles (a declared input, part of item 3) and quadratures (REQUIRED, recorded):

* "uniform_disc": uniform in the transverse plane inside |t| <= alpha (a round condenser aperture
  filled uniformly). Product rule: Gauss-Legendre in s = (|t|/alpha)^2 on [0, 1] with n_radial nodes
  (the area element is |t| d|t| dphi = alpha^2 ds dphi / 2, so s is uniform) times n_azimuthal
  equally spaced azimuths phi_m = 2 pi m / n_azimuthal (m = 0 is the incidence plane; the node set is
  symmetric under t_b -> -t_b). Weights w_j / (2 n_azimuthal), w_j the Gauss-Legendre weights on
  [-1, 1]; sum 1. Exact for every polynomial in (t_a, t_b) of total degree
  <= min(n_azimuthal - 1, 4 n_radial - 1) (DERIVED_HERE: the azimuthal rule is exact for
  trigonometric polynomials of degree < n_azimuthal; a monomial of even degree 2j with a
  non-vanishing azimuthal mean is s^j, integrated exactly for j <= 2 n_radial - 1).
* "uniform_line": uniform on the segment t = alpha xi (cos psi, sin psi), xi in [-1, 1] (a slit, or
  the one-dimensional top hat of the tests), psi = line_azimuth_rad measured from e_a towards e_b.
  Gauss-Legendre in xi with n_radial nodes, weights w_j / 2; exact for polynomials of degree
  <= 2 n_radial - 1 along the line.

Analytic coherence factors (DERIVED_HERE; van Cittert-Zernike for a flat incoherent source): if the
two interfering waves of member s differ only by the illumination phase dk_s . E, E an effective
separation perpendicular to b0, then the fringe term of (1) is multiplied by

    mu = sum_s w_s exp(i dk_s . E)  ->  2 J1(v) / v        (uniform disc),  v = k alpha |E|   (3)
                                   ->  sin(v) / v          (uniform line),  v = k alpha E.l  (4)

(3): with t = alpha rho (cos phi, sin phi), the disc mean of exp(i v rho cos(phi - psi)) is
int_0^1 2 rho J0(v rho) d rho = 2 J1(v)/v; (4): (1/2) int_-1^1 exp(i v xi) d xi = sin(v)/v.
A component E_par of E along b0 adds the phase -k (1 - sqrt(1 - t^2)) E_par ~ -kappa s with
kappa = k alpha^2 E_par / 2 (recorded, included in the error bound).

Quadrature error bound (DERIVED_HERE; recorded with every run; the declared quadrature is refused if
the bound exceeds the declared tolerance). For f = exp(i dk.E) with phase extent v and curvature
kappa:
  disc:  |Q - I| <= E_rad + E_az,
         E_az  = 2 sum_{p>=1} (v/2)^(p m) / (p m)!   (m = n_azimuthal; the equispaced rule aliases
                 the Fourier orders +-p m of exp(i v rho cos(phi - psi)) = sum_n i^n J_n(v rho)
                 e^(i n (phi - psi)) onto the mean, and |J_n(x)| <= (x/2)^n / n!),
         E_rad = C_n (2n)! M(R) / R^(2n) minimised over R > 0, the Gauss-Legendre remainder
                 (n!)^4 / ((2n + 1) ((2n)!)^3) f^(2n)(eta) on [0, 1] (n = n_radial) with the Cauchy
                 estimate |f^(2n)| <= (2n)! M(R) / R^(2n) for the radial integrand
                 h(s) = J0(v sqrt(s)) exp(-i kappa s), M(R) = I0(v sqrt(1 + R)) exp(kappa R)
                 (|J0(v sqrt(z))| <= I0(v sqrt|z|));
  line:  |Q - I| <= sqrt(2) C'_n (2n)! M(R) / R^(2n), C'_n = 2^(2n) (n!)^4 / ((2n + 1) ((2n)!)^3),
         M(R) = exp(v R + kappa (2 R + R^2)) (integrand exp(i (v xi - kappa xi^2)) on [-1, 1]).
A floating-point floor of 8 eps per member (double precision) is added to both bounds.
The same bound applies to any member-dependent phase that is linear in t with the same extent v,
e.g. the step phase of a terrace pair, whose derivative is (4 pi h / lambda) cos(theta) per radian
of glancing angle (docs/03 section 4): v_step = (4 pi h_max / lambda) cos(theta) alpha.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from reflection_holo.io.labels import require_evidence_label

SOURCE_PROFILES = ("uniform_disc", "uniform_line")
QUADRATURE_RULES = {
    "uniform_disc": ("product rule: Gauss-Legendre in s = (|t|/alpha)^2 on [0, 1] (n_radial nodes) "
                     "x n_azimuthal equally spaced azimuths phi_m = 2 pi m / n_azimuthal; weights "
                     "w_j / (2 n_azimuthal); DERIVED_HERE (module docstring)"),
    "uniform_line": ("Gauss-Legendre in xi = t/alpha on [-1, 1] along the declared line azimuth "
                     "(n_radial nodes); weights w_j / 2; DERIVED_HERE (module docstring)"),
}
_LABELS = ("PROJECT_INPUT", "ASSUMPTION", "TEST_ONLY")
MAX_SEMI_ANGLE_RAD = 0.01               # 10 mrad: far above any holography illumination (sanity)
ROUNDING_FLOOR_PER_MEMBER = 8 * float(np.finfo(float).eps)   # added to every bound (double precision)


# ------------------------------------------------------------------------------------------------
# Bessel functions (no scipy dependency): J_n(v) = (1/2pi) int_0^2pi cos(n tau - v sin tau) d tau.
# The trapezoid rule on M points of this periodic analytic integrand is exact up to the aliased
# orders J_{n +- p M}(v) (same argument as E_az above); M = 64 + 2 ceil(|v|) makes them < 1e-17 for
# |v| <= 200 (DERIVED_HERE; checked against scipy.special in tests/optics/test_coherence.py).
# ------------------------------------------------------------------------------------------------
def bessel_j(n: int, v) -> np.ndarray:
    """J_n(v) for integer n >= 0 and real v (array-valued), by the trapezoid rule above."""
    v = np.asarray(v, dtype=float)
    if not np.all(np.isfinite(v)) or np.any(np.abs(v) > 200.0):
        raise ValueError("bessel_j: |v| must be finite and <= 200")
    M = 64 + 2 * int(math.ceil(float(np.max(np.abs(v))) if v.size else 0.0))
    tau = 2.0 * np.pi * np.arange(M) / M
    return np.mean(np.cos(n * tau - v[..., None] * np.sin(tau)), axis=-1)


def disc_coherence_factor(v) -> np.ndarray:
    """2 J1(v)/v (1 at v = 0): coherence factor (3) of a uniform disc source, v = k alpha |E|."""
    v = np.asarray(v, dtype=float)
    out = np.empty_like(v)
    big = np.abs(v) >= 1.0
    out[big] = 2.0 * bessel_j(1, v[big]) / v[big]
    # |v| < 1: the power series sum_k (-1)^k (v/2)^(2k) / (k! (k+1)!) (dividing the trapezoid J1 by
    # a small v would amplify its absolute rounding); 14 terms leave < (1/2)^28/(14! 15!) ~ 1e-31
    x2 = (0.5 * v[~big]) ** 2
    acc = np.zeros_like(x2)
    term = np.ones_like(x2)
    for k in range(14):
        acc = acc + term
        term = -term * x2 / ((k + 1) * (k + 2))
    out[~big] = acc
    return out


def line_coherence_factor(v) -> np.ndarray:
    """sin(v)/v (1 at v = 0): coherence factor (4) of a uniform line (top-hat) source."""
    return np.sinc(np.asarray(v, dtype=float) / np.pi)


# ------------------------------------------------------------------------------------------------
# quadrature error bounds (module docstring)
# ------------------------------------------------------------------------------------------------
_R_GRID = np.geomspace(1e-2, 1e8, 8001)


def _log_gauss_constant(n: int, interval: str) -> float:
    """log of C_n (2n)!: [0,1]: (n!)^4/((2n+1)((2n)!)^2); [-1,1]/2: 2^(2n) (n!)^4/((2n+1)((2n)!)^2)."""
    lg = 4 * math.lgamma(n + 1) - math.log(2 * n + 1) - 2 * math.lgamma(2 * n + 1)
    return lg + (2 * n * math.log(2.0) if interval == "line" else 0.0)


def _log_i0(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    # log I0 via numpy's i0 below 700 (no overflow), asymptotic x - 0.5 log(2 pi x) above
    small = x < 700.0
    out = np.empty_like(x)
    out[small] = np.log(np.i0(x[small]))
    xl = x[~small]
    out[~small] = xl - 0.5 * np.log(2.0 * np.pi * xl) + np.log1p(1.0 / (8.0 * xl))
    return out


def radial_error_bound(n: int, v: float, kappa: float, profile: str) -> float:
    """Gauss-Legendre remainder bound (module docstring) for n nodes; minimised over R."""
    if v == 0.0 and kappa == 0.0:
        return 0.0                               # constant integrand: every rule is exact
    R = _R_GRID
    if profile == "uniform_disc":
        logM = _log_i0(abs(v) * np.sqrt(1.0 + R)) + abs(kappa) * R
        lc = _log_gauss_constant(n, "disc")
        extra = 0.0
    else:
        logM = abs(v) * R + abs(kappa) * (2.0 * R + R * R)
        lc = _log_gauss_constant(n, "line")
        extra = 0.5 * math.log(2.0)
    logb = lc + extra + np.min(logM - 2 * n * np.log(R))
    return float(min(2.0, math.exp(min(logb, 700.0))))


def azimuthal_error_bound(m: int, v: float) -> float:
    """E_az = 2 sum_{p>=1} min(1, (v/2)^(p m)/(p m)!) (module docstring); capped at 2."""
    v = abs(float(v))
    if v == 0.0:
        return 0.0
    total = 0.0
    p = 1
    while True:
        n = p * m
        lt = n * math.log(v / 2.0) - math.lgamma(n + 1) if v > 0 else -np.inf
        term = min(1.0, math.exp(lt)) if lt < 700 else 1.0
        total += 2.0 * term
        if (n > v and term < 1e-30) or total >= 2.0 or p > 100000:
            break
        p += 1
    return float(min(2.0, total))


def quadrature_error_bound(profile: str, n_radial: int, n_azimuthal: int | None, *,
                           phase_extent_rad: float, curvature_rad: float) -> float:
    """Bound on |quadrature - exact| of the source mean of exp(i dk.E) (module docstring).

    phase_extent_rad   v = k alpha |E_perp| (disc) or k alpha |E.l| (line), or the extent of any
                       member phase linear in t (e.g. v_step)
    curvature_rad      kappa = k alpha^2 |E_par| / 2 (0 if E is perpendicular to b0)"""
    if profile not in SOURCE_PROFILES:
        raise ValueError(f"source profile must be one of {SOURCE_PROFILES}, got {profile!r}")
    v, kap = float(phase_extent_rad), float(curvature_rad)
    if not (math.isfinite(v) and v >= 0 and math.isfinite(kap) and kap >= 0):
        raise ValueError("phase_extent_rad and curvature_rad must be finite and >= 0")
    b = radial_error_bound(int(n_radial), v, kap, profile)
    n_mem = int(n_radial)
    if profile == "uniform_disc":
        b += azimuthal_error_bound(int(n_azimuthal), v)
        n_mem *= int(n_azimuthal)
    # floating-point floor: each of the n_mem terms w_s exp(i phase_s) carries a rounding error of
    # a few ulp (phase, exp, product), and the sum adds one ulp per term: <= 8 eps per member
    return float(min(2.0, b + ROUNDING_FLOOR_PER_MEMBER * n_mem))


def minimal_quadrature(profile: str, *, phase_extent_rad: float, curvature_rad: float,
                       tolerance: float, max_members: int = 4096) -> dict:
    """The quadrature with the fewest members whose bound is <= tolerance (search over n_radial
    and n_azimuthal); raises if none has at most max_members members. Used to justify a declared
    quadrature (it is recorded next to it), never to choose one silently."""
    if not (math.isfinite(tolerance) and 0 < tolerance < 1):
        raise ValueError("tolerance must lie in (0, 1)")
    best = None
    if profile == "uniform_line":
        for n in range(1, max_members + 1):
            b = quadrature_error_bound(profile, n, None, phase_extent_rad=phase_extent_rad,
                                       curvature_rad=curvature_rad)
            if b <= tolerance:
                return dict(n_radial=n, n_azimuthal=None, members=n, bound=b)
        raise ValueError(f"no line quadrature with <= {max_members} members reaches {tolerance}")
    for nr in range(1, 257):
        br = radial_error_bound(nr, phase_extent_rad, curvature_rad, profile)
        if br > tolerance:
            continue
        for na in range(1, max_members // nr + 1):
            # the same bound as quadrature_error_bound (radial part computed once per n_radial)
            b = min(2.0, br + azimuthal_error_bound(na, phase_extent_rad)
                    + ROUNDING_FLOOR_PER_MEMBER * nr * na)
            if b <= tolerance:
                if best is None or nr * na < best["members"]:
                    best = dict(n_radial=nr, n_azimuthal=na, members=nr * na, bound=min(2.0, b))
                break
    if best is None:
        raise ValueError(f"no disc quadrature with <= {max_members} members reaches {tolerance}")
    return best


# ------------------------------------------------------------------------------------------------
# members and quadratures
# ------------------------------------------------------------------------------------------------
def _unit(v) -> np.ndarray:
    return np.asarray(v, dtype=float)


def central_direction(theta0_rad: float) -> np.ndarray:
    """b0 = (-sin th0, 0, cos th0)."""
    return np.array([-math.sin(theta0_rad), 0.0, math.cos(theta0_rad)])


def transverse_basis(theta0_rad: float) -> tuple[np.ndarray, np.ndarray]:
    """(e_a, e_b): e_a = (-cos th0, 0, -sin th0) increases the glancing angle, e_b = (0, 1, 0)."""
    return (np.array([-math.cos(theta0_rad), 0.0, -math.sin(theta0_rad)]),
            np.array([0.0, 1.0, 0.0]))


def mirror_x(u) -> np.ndarray:
    """Specular reflection at a surface with normal x: u_x -> -u_x."""
    u = np.asarray(u, dtype=float).copy()
    u[..., 0] = -u[..., 0]
    return u


def rotation_2theta(theta0_rad: float) -> np.ndarray:
    """R_y(2 th0), the rotation about y that maps b0 onto the specular direction mirror(b0): the
    compensation of a vacuum reference by a condenser-biprism pre-tilt of 2 theta_ext (B28)."""
    b = 2.0 * theta0_rad
    c, s = math.cos(b), math.sin(b)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


@dataclass(frozen=True)
class ConvergenceMember:
    """One incidence direction of a convergence ensemble. Every field is required.

    index        member index (0-based, as generated by ConvergenceQuadrature.members)
    t_a_rad      transverse offset in the incidence plane (t_a > 0 increases the glancing angle)
    t_b_rad      transverse offset along y (= the y direction cosine u_y)
    weight       quadrature weight (> 0; the weights of an ensemble sum to 1)"""
    index: int
    t_a_rad: float
    t_b_rad: float
    weight: float

    def __post_init__(self):
        if isinstance(self.index, bool) or int(self.index) != self.index or self.index < 0:
            raise ValueError(f"member index must be an integer >= 0, got {self.index!r}")
        for name in ("t_a_rad", "t_b_rad", "weight"):
            v = getattr(self, name)
            if isinstance(v, bool) or not math.isfinite(float(v)):
                raise ValueError(f"{name} must be finite, got {v!r}")
        if not float(self.weight) > 0:
            raise ValueError("weight must be > 0")
        if self.t_a_rad ** 2 + self.t_b_rad ** 2 >= 0.01:
            raise ValueError("transverse offset above 0.1 rad refused (paraxial convergence)")

    def direction(self, theta0_rad: float) -> np.ndarray:
        """u_s of equation (2) (unit vector, slab frame)."""
        b0 = central_direction(theta0_rad)
        ea, eb = transverse_basis(theta0_rad)
        t2 = self.t_a_rad ** 2 + self.t_b_rad ** 2
        return math.sqrt(1.0 - t2) * b0 + self.t_a_rad * ea + self.t_b_rad * eb

    def glancing_angle_rad(self, theta0_rad: float) -> float:
        """th_s = asin(-u_x) (the member's own external glancing angle)."""
        return float(math.asin(-self.direction(theta0_rad)[0]))

    def direction_cosine_y(self) -> float:
        return float(self.t_b_rad)

    def tilt_simulation_frame(self, theta0_rad: float) -> tuple[float, float]:
        """(theta_x, theta_y) = lambda (q - q0) of docs/physics_conventions.md (rad)."""
        u = self.direction(theta0_rad)
        return float(u[0] + math.sin(theta0_rad)), float(u[1])

    def dk_in(self, k_rad_per_A: float, theta0_rad: float) -> np.ndarray:
        """k (u_s - b0) (rad/A)."""
        return k_rad_per_A * (self.direction(theta0_rad) - central_direction(theta0_rad))

    def dk_out_specular(self, k_rad_per_A: float, theta0_rad: float) -> np.ndarray:
        """k (mirror(u_s) - mirror(b0)) (rad/A): the specular beam's wavevector change."""
        return mirror_x(self.dk_in(k_rad_per_A, theta0_rad))

    def as_record(self, theta0_rad: float) -> dict:
        tx, ty = self.tilt_simulation_frame(theta0_rad)
        return dict(index=int(self.index), t_a_rad=float(self.t_a_rad), t_b_rad=float(self.t_b_rad),
                    weight=float(self.weight),
                    glancing_angle_rad=self.glancing_angle_rad(theta0_rad),
                    direction_cosine_y=self.direction_cosine_y(),
                    tilt_simulation_frame_rad=[tx, ty],
                    direction=[float(a) for a in self.direction(theta0_rad)])


@dataclass(frozen=True)
class ConvergenceQuadrature:
    """Declared source distribution and quadrature of a convergence ensemble. Every field is
    required (no defaults); the quadrature is REFUSED if its error bound (module docstring) for the
    declared design phase extent exceeds the declared tolerance.

    semi_angle_rad        alpha, the illumination convergence semi-angle (PROJECT_INPUT item 3), > 0
    semi_angle_label      qualified evidence label ("PROJECT_INPUT item 3 ...", "ASSUMPTION B40 ...",
                          "TEST_ONLY ...")
    source_profile        "uniform_disc" | "uniform_line"
    n_radial              Gauss-Legendre nodes (in s for the disc, along the line)
    n_azimuthal           equally spaced azimuths (disc); None for the line
    line_azimuth_rad      direction of the line from e_a towards e_b (line); None for the disc
    design_phase_extent_rad  v_max: the largest phase extent the ensemble must integrate (the
                          coherence phase k alpha |E_perp| over the field and the step phase
                          (4 pi h_max/lambda) cos(theta) alpha; computed by the caller)
    design_curvature_rad  kappa = k alpha^2 |E_par| / 2 (0 if none)
    tolerance             largest accepted bound on the error of the ensemble mean of a unit phasor
    """
    semi_angle_rad: float
    semi_angle_label: str
    source_profile: str
    n_radial: int
    n_azimuthal: int | None
    line_azimuth_rad: float | None
    design_phase_extent_rad: float
    design_curvature_rad: float
    tolerance: float

    def __post_init__(self):
        a = self.semi_angle_rad
        if isinstance(a, bool) or not (math.isfinite(float(a)) and 0 < float(a) <= MAX_SEMI_ANGLE_RAD):
            raise ValueError(f"semi_angle_rad must lie in (0, {MAX_SEMI_ANGLE_RAD}] rad (a zero "
                             f"convergence is a plane wave: no ensemble), got {a!r}")
        require_evidence_label(self.semi_angle_label, "convergence semi-angle (PROJECT_INPUT item 3)",
                               accepted=_LABELS, qualified=True)
        if self.source_profile not in SOURCE_PROFILES:
            raise ValueError(f"source_profile must be one of {SOURCE_PROFILES}, got "
                             f"{self.source_profile!r}")
        for name in ("n_radial",) + (("n_azimuthal",) if self.source_profile == "uniform_disc"
                                     else ()):
            n = getattr(self, name)
            if isinstance(n, bool) or not isinstance(n, (int, np.integer)) or n < 1:
                raise ValueError(f"{name} must be an integer >= 1, got {n!r}")
        if self.source_profile == "uniform_disc":
            if self.line_azimuth_rad is not None:
                raise ValueError("line_azimuth_rad applies to the uniform_line profile only")
        else:
            if self.n_azimuthal is not None:
                raise ValueError("n_azimuthal applies to the uniform_disc profile only (None here)")
            psi = self.line_azimuth_rad
            if psi is None or isinstance(psi, bool) or not math.isfinite(float(psi)):
                raise ValueError("uniform_line needs a finite line_azimuth_rad")
        for name in ("design_phase_extent_rad", "design_curvature_rad"):
            v = getattr(self, name)
            if isinstance(v, bool) or not (math.isfinite(float(v)) and float(v) >= 0):
                raise ValueError(f"{name} must be finite and >= 0, got {v!r}")
        tol = self.tolerance
        if isinstance(tol, bool) or not (math.isfinite(float(tol)) and 0 < float(tol) < 1):
            raise ValueError(f"tolerance must lie in (0, 1), got {tol!r}")
        b = self.error_bound()
        if b > float(tol):
            mq = minimal_quadrature(self.source_profile, phase_extent_rad=self.design_phase_extent_rad,
                                    curvature_rad=self.design_curvature_rad, tolerance=float(tol))
            raise ValueError(
                f"declared quadrature ({self.source_profile}, n_radial = {self.n_radial}, "
                f"n_azimuthal = {self.n_azimuthal}) has the error bound {b:.3e} > tolerance "
                f"{float(tol):.3e} for the design phase extent v = "
                f"{self.design_phase_extent_rad:.4g} rad (kappa = {self.design_curvature_rad:.3g} "
                f"rad); the smallest quadrature that meets it is {mq} (declare it explicitly)")

    @property
    def n_members(self) -> int:
        return int(self.n_radial) * (int(self.n_azimuthal) if self.n_azimuthal else 1)

    def error_bound(self) -> float:
        return quadrature_error_bound(self.source_profile, int(self.n_radial),
                                      None if self.n_azimuthal is None else int(self.n_azimuthal),
                                      phase_extent_rad=float(self.design_phase_extent_rad),
                                      curvature_rad=float(self.design_curvature_rad))

    def polynomial_degree_exact(self) -> int:
        if self.source_profile == "uniform_disc":
            return int(min(int(self.n_azimuthal) - 1, 4 * int(self.n_radial) - 1))
        return 2 * int(self.n_radial) - 1

    def nodes(self) -> list[tuple[float, float, float]]:
        """[(t_a, t_b, weight)] in member order (radial index outer, azimuth inner)."""
        x, w = np.polynomial.legendre.leggauss(int(self.n_radial))
        a = float(self.semi_angle_rad)
        out = []
        if self.source_profile == "uniform_disc":
            na = int(self.n_azimuthal)
            for xj, wj in zip(x, w):
                r = a * math.sqrt(0.5 * (1.0 + xj))
                for m in range(na):
                    ph = 2.0 * math.pi * m / na
                    out.append((r * math.cos(ph), r * math.sin(ph), wj / (2.0 * na)))
        else:
            psi = float(self.line_azimuth_rad)
            for xj, wj in zip(x, w):
                out.append((a * xj * math.cos(psi), a * xj * math.sin(psi), wj / 2.0))
        return out

    def members(self) -> list[ConvergenceMember]:
        return [ConvergenceMember(index=i, t_a_rad=ta, t_b_rad=tb, weight=wt)
                for i, (ta, tb, wt) in enumerate(self.nodes())]

    def member(self, index: int) -> ConvergenceMember:
        ms = self.members()
        if isinstance(index, bool) or int(index) != index or not 0 <= int(index) < len(ms):
            raise ValueError(f"member index must lie in [0, {len(ms)}), got {index!r}")
        return ms[int(index)]

    def as_record(self, theta0_rad: float | None = None) -> dict:
        rec = dict(
            semi_angle_rad=float(self.semi_angle_rad), semi_angle_label=self.semi_angle_label,
            source_profile=self.source_profile, n_radial=int(self.n_radial),
            n_azimuthal=None if self.n_azimuthal is None else int(self.n_azimuthal),
            line_azimuth_rad=None if self.line_azimuth_rad is None else float(self.line_azimuth_rad),
            n_members=self.n_members, rule=QUADRATURE_RULES[self.source_profile],
            polynomial_degree_exact=self.polynomial_degree_exact(),
            design_phase_extent_rad=float(self.design_phase_extent_rad),
            design_curvature_rad=float(self.design_curvature_rad),
            tolerance=float(self.tolerance), error_bound=self.error_bound(),
            minimal_quadrature_for_the_design=minimal_quadrature(
                self.source_profile, phase_extent_rad=float(self.design_phase_extent_rad),
                curvature_rad=float(self.design_curvature_rad), tolerance=float(self.tolerance)),
            justification=("the number of directions is the declared (n_radial, n_azimuthal); it "
                           "is accepted only if the DERIVED_HERE error bound of the ensemble mean "
                           "of exp(i dk.E) for the design phase extent is <= the tolerance "
                           "(optics.coherence module docstring)"),
            analytic_limit=("2 J1(v)/v" if self.source_profile == "uniform_disc" else "sin(v)/v"))
        if theta0_rad is not None:
            rec["theta0_rad"] = float(theta0_rad)
            rec["members"] = [m.as_record(theta0_rad) for m in self.members()]
        return rec


# ------------------------------------------------------------------------------------------------
# illumination phases of a member (report E3 section 2)
# ------------------------------------------------------------------------------------------------
REFERENCE_PASSAGES_UNDER_CONVERGENCE = ("condenser_biprism_pretilt",)


def r1_reference_member_phase(member: ConvergenceMember, *, k_rad_per_A: float, theta0_rad: float,
                              exit_points_A: tuple, separation_A, aperture_passage: str
                              ) -> np.ndarray:
    """Phase dk_ref,s . (Q(r) - D0) of an R1 vacuum reference for member s (DERIVED_HERE, E3 2.3).

    The reference beam is split from the same source point and, for the condenser-biprism pre-tilt
    (B28, docs/05 section 5 item 3), travels parallel to the central specular beam: its wavevector
    change is dk_ref,s = R_y(2 th0) dk_in,s. Q(r) = (x, y, z) are the exit-plane points imaged at the
    detector pixels r (arrays of the detector shape) and D0 the separation, at the specimen, from the
    reference-arm point to the object-arm point that the biprism superposes (PROJECT_INPUT item 16);
    since dk_ref,s is perpendicular to the central outgoing direction to first order, D0 is defined
    modulo that direction. Other aperture passages (second aperture hole, no aperture) leave the
    reference inclined to the imaging axis, so its image-plane phase depends on the conjugate plane:
    NOT IMPLEMENTED under convergence (refused)."""
    if aperture_passage not in REFERENCE_PASSAGES_UNDER_CONVERGENCE:
        raise NotImplementedError(
            f"R1 reference passage {aperture_passage!r} under convergence: only "
            f"{REFERENCE_PASSAGES_UNDER_CONVERGENCE} is implemented (a reference inclined to the "
            f"imaging axis needs the conjugate plane of the imaging, not declared)")
    D0 = np.asarray(separation_A, dtype=float)
    if D0.shape != (3,) or not np.all(np.isfinite(D0)):
        raise ValueError("separation_A must be a finite 3-vector (x, y, z) in A (PROJECT_INPUT "
                         "item 16)")
    X, Y, Z = (np.asarray(a, dtype=float) for a in exit_points_A)
    dk = rotation_2theta(theta0_rad) @ member.dk_in(k_rad_per_A, theta0_rad)
    return dk[0] * (X - D0[0]) + dk[1] * (Y - D0[1]) + dk[2] * (Z - D0[2])


def flat_mirror_member_phase(member: ConvergenceMember, *, k_rad_per_A: float, theta0_rad: float,
                             exit_points_A: tuple, mirror_height_A: float) -> np.ndarray:
    """Phase of the specular wave of a flat mirror at height x_m for member s, relative to the
    central member, at the exit-plane points Q (DERIVED_HERE, E3 2.2): dk_out,s . Q +
    2 dk_in,s,x x_m (the incident phase at the reflection point plus the outgoing path). Used for
    the object branch of the EMPTY hologram (a flat region of the same surface)."""
    X, Y, Z = (np.asarray(a, dtype=float) for a in exit_points_A)
    dki = member.dk_in(k_rad_per_A, theta0_rad)
    dko = mirror_x(dki)
    return dko[0] * X + dko[1] * Y + dko[2] * Z + 2.0 * dki[0] * float(mirror_height_A)


def ensemble_coherence(members, phases) -> np.ndarray:
    """sum_s w_s exp(i phase_s): the complex coherence factor of the fringe term of (1) for member
    phases (scalars or arrays)."""
    acc = 0.0
    wsum = 0.0
    for m, ph in zip(members, phases):
        acc = acc + m.weight * np.exp(1j * np.asarray(ph, dtype=float))
        wsum += m.weight
    if abs(wsum - 1.0) > 1e-12:
        raise ValueError(f"member weights must sum to 1, got {wsum!r}")
    return acc
