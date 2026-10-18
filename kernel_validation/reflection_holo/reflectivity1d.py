"""One-beam (specular-rod-only) dynamical reflection solver for a laterally averaged complex potential.

ROLE: INDEPENDENT CHECK of the grazing-incidence multislice engine (rung R2, item 2f). It is NOT the engine.
It shares only the physical constants (`constants.wavelength`, `constants.interaction_constant`,
`constants.A_SI`, `constants.B_SI_300K`) and the atomic scattering factors with the kernel. The parameter
values are a local copy of the card row, and a test checks that copy against `constants.KIRKLAND_SI`.
The propagation algorithm, the potential construction (analytic lateral average) and the boundary
treatment (exact semi-infinite substrate instead of a graded absorber) are all independent of the kernel.

Equation solved (DERIVED_HERE from SECTION_READ premises; see NOTES_D.md section 1):

    psi''(z) + [k_z^2 + U(z)] psi(z) = 0,      U(z) = 2 K sigma [V(z) + i W(z)]      (Å^-2)

* Peng eqn 5.8 [card peng_ch05, p.10-11] with only the G = H = 0 rod retained. The card author INFERS this
  reduction ("one-rod case", p.28). Here it is DERIVED_HERE.
* U = 2 m e V / hbar^2 with relativistic m. Kirkland eqn 6.6-6.7 [card kirkland_ch06, p.6] gives
  U_cyc = sigma V/(pi lambda) in 1/lambda units, so angular U = 4 pi^2 U_cyc = 2 K sigma V. The repository
  convention is K_z,int^2 = K_z,vac^2 + 2 m e V0/hbar^2.
* z is the outward normal (vacuum at +z) and K = 2 pi / lambda (repository conventions).
* Vacuum field: psi = exp(-i k_z (z - z_ref)) + r exp(+i k_z (z - z_ref)). This is Peng 5.109
  [p.38] rewritten for an outward z axis.
* Continuity of psi and psi' holds at every slice boundary (Peng 5.58-5.59 [p.25]).
* Semi-infinite crystal: only waves that decay into the bulk are retained (Peng p.27, p.36). The substrate
  therefore carries only a downgoing wave, with Im q >= 0.
* Absorption sign: W > 0 attenuates. This follows from the exp(+ik.r) convention and the outgoing +i0
  Green's function (Peng ch13 [p.3]), and is consistent with the transmission function exp(i sigma (V+iW))
  having |t| < 1.

Evidence labels used in this module: SECTION_READ, REPRODUCED, ASSUMPTION, DERIVED_HERE, UNVERIFIED.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field

import numpy as np
from scipy.special import erfcx

from . import constants as C
from . import project_inputs as PI

# ----------------------------------------------------------------------------------------------------
# Container for rocking curves. Prefer the kernel's class so that results are interchangeable.
# ----------------------------------------------------------------------------------------------------
try:  # pragma: no cover - depends on the kernel builder
    from .multislice.reflectivity import RockingCurve  # type: ignore
except Exception:  # noqa: BLE001
    @dataclass
    class RockingCurve:  # type: ignore[no-redef]
        """Fallback with the CONTRACT field layout (theta_ext [rad], complex r, meta). Label: DERIVED_HERE."""
        theta_ext: np.ndarray
        r: np.ndarray
        meta: dict = field(default_factory=dict)

MissingProjectInput = getattr(PI, "MissingProjectInput", RuntimeError)

# ----------------------------------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------------------------------
_H = 6.62607015e-34          # J s, exact SI-2019 (repository conventions)
_M0 = 9.1093837015e-31       # kg, CODATA 2018 (repository conventions)
_QE = 1.602176634e-19        # C, exact SI-2019
_MEC2_EV = 510998.950        # eV, CODATA 2018 (repository conventions)

#: Prefactor h^2/(2 pi m0 e) = 2 pi a0 e in V*Å^2.
#: Kirkland eqn 6.10 [card kirkland_ch06, p.7] prints 47.86. Label: DERIVED_HERE from CODATA.
#: The match to the printed value is REPRODUCED in a test (tolerance 1e-3).
KIRKLAND_PREFACTOR_V_A2 = _H ** 2 / (2.0 * math.pi * _M0 * _QE) * 1e20

#: Si (Z = 14) row of Kirkland eqn C.15, transcribed from [card kirkland_appC, p.12], printed order
#: a1 b1 a2 b2 / a3 b3 c1 d1 / c2 d2 c3 d3 (layout p.9).
#: Units: a [Å^-1], b [Å^-2], c [Å], d [Å^2]. q = 1/d (cycles/Å). Label: SECTION_READ.
KIRKLAND_SI_CARD = {
    "a": (1.06543892e+000, 1.20143691e-001, 1.80915263e-001),
    "b": (1.04118455e+000, 6.87113368e+001, 8.87533926e-002),
    "c": (1.12065620e+000, 3.05452816e-002, 1.59963502e+000),
    "d": (3.70062619e+000, 2.14097897e-001, 9.99096638e+000),
    "chisq": 0.071667,
    "source": "card:kirkland_appC_scattering_factors [p.12, printed p.294]; form eqn C.15 [p.8]",
}

#: Peng Table 13.3 Si a_i (Å), used only as an independent cross-check of f_e(0) [card peng_ch13, p.24].
#: Label: SECTION_READ.
PENG_T13_3_SI_A = (0.0567, 0.3365, 0.8104, 2.4960, 2.1186)

#: Default absorptive/elastic ratio, used only if the caller accepts assumptions.
#: Label: ASSUMPTION / UNVERIFIED.
#: Si absorption parameters are NOT IN any supplied card (Peng ch13 p.20, ch05 D). Peng ch13 also warns
#: that W is not proportional to V (Contradictions item 2). The ratio is therefore a stand-in, and the
#: run fails loudly unless the caller supplies it or accepts it.
DEFAULT_W_OVER_V = 0.10

#: Tolerances for the T-1D-agreement harness. Label: ASSUMPTION. Reasons are in NOTES_D.md section 4.
AGREEMENT_TOL = {
    "peak_shift_over_fwhm": 0.25,
    "fwhm_rel": 0.25,
    "phase_resid_rad": 0.30,
    "amplitude_frac": 0.10,
}


def _record_assumption(name: str, value, reason: str) -> None:
    """Record a used assumption in project_inputs.USED_ASSUMPTIONS and print it.

    Label: DERIVED_HERE (repository rule).
    """
    lst = getattr(PI, "USED_ASSUMPTIONS", None)
    if lst is not None:
        lst.append({"id": name, "value": value, "reason": reason, "module": "reflectivity1d"})
    print(f"ASSUMPTION used: {name} = {value}  ({reason})")


# ----------------------------------------------------------------------------------------------------
# Scattering factor and laterally averaged single-atom potential
# ----------------------------------------------------------------------------------------------------
def fe_kirkland(q, params=KIRKLAND_SI_CARD):
    """Kirkland eqn C.15: f_e(q) = sum a/(q^2+b) + sum c exp(-d q^2), with q in cycles/Å and f_e in Å.

    Label: SECTION_READ [card kirkland_appC, p.8].
    """
    q2 = np.asarray(q, float) ** 2
    out = np.zeros_like(q2)
    for a, b in zip(params["a"], params["b"]):
        out = out + a / (q2 + b)
    for c, d in zip(params["c"], params["d"]):
        out = out + c * np.exp(-d * q2)
    return out


def fe0(params=KIRKLAND_SI_CARD) -> float:
    """f_e(0) = sum a/b + sum c (Å).

    The card author's INFERRED value is ~5.814 Å; this function recomputes it. Label: DERIVED_HERE.
    """
    return float(sum(a / b for a, b in zip(params["a"], params["b"])) + sum(params["c"]))


def _exp_abs_conv(z, kappa: float, sigma: float):
    """exp(-kappa|z|) convolved with a normalised Gaussian of standard deviation sigma.

    Closed form, DERIVED_HERE:
        0.5 exp(-z^2/2s^2) [erfcx(u1) + erfcx(u2)],
        u1 = (k s^2 - z)/(s sqrt2),  u2 = (k s^2 + z)/(s sqrt2),  with z >= 0.
    For u1 < 0 the identity erfc(u) = 2 - erfc(-u) is used to avoid overflow.
    A test checks this against numerical convolution.
    """
    z = np.abs(np.asarray(z, float))
    if sigma <= 0.0:
        return np.exp(-kappa * z)
    s2 = sigma * sigma
    g = np.exp(-z * z / (2.0 * s2))
    u1 = (kappa * s2 - z) / (sigma * math.sqrt(2.0))
    u2 = (kappa * s2 + z) / (sigma * math.sqrt(2.0))
    t2 = 0.5 * g * erfcx(u2)
    pos = u1 >= 0
    t1_pos = 0.5 * g * erfcx(np.maximum(u1, 0.0))
    expo = np.minimum(0.5 * kappa * kappa * s2 - kappa * z, 0.0)
    t1_neg = np.exp(expo) - 0.5 * g * erfcx(np.maximum(-u1, 0.0))
    return t2 + np.where(pos, t1_pos, t1_neg)


def atom_areal_profile(dz_rel, B: float, params=KIRKLAND_SI_CARD):
    """Laterally integrated potential of one atom, P(z) = integral of V(x,y,z) dx dy, in V*Å^2.

    Includes isotropic Debye-Waller smearing.

    DERIVED_HERE from the transform pair C.5/C.19 [card kirkland_appC, p.6, p.10]:
    * The lateral integral selects q_x = q_y = 0, so P(z) = 2 pi a0 e * integral f_e(q_z) exp(-2 pi i q_z z) dq_z.
    * Each Lorentzian term transforms to a pi/sqrt(b) exp(-2 pi sqrt(b)|z|).
    * Each Gaussian term transforms to c sqrt(pi/d) exp(-pi^2 z^2/d).
    * Debye-Waller: T = exp(-B s^2) with s = q/2 [Peng ch13 13.52, p.11; Peng 2004 printed p.437].
      s = q/2 is DERIVED_HERE from the Fourier conventions (Kirkland Eq. C.5, |q| = 1/d; Peng
      s = g/(4 pi), g = 2 pi/d) and REPRODUCED against Peng Table 13.3; see potential.py E4.
      This equals exp(-2 pi^2 sigma^2 q^2) with sigma^2 = B/(8 pi^2), the per-axis mean-square
      displacement [Peng ch13 13.50-13.51; ch14 eqn 14.3]. It is a Gaussian convolution in z: d -> d + B/4
      for the Gaussian terms, and _exp_abs_conv for the Lorentzian terms.
    * Integral of P dz = 2 pi a0 e f_e(0), because the Debye-Waller factor leaves g = 0 unchanged.
    """
    z = np.asarray(dz_rel, float)
    sigma = math.sqrt(max(B, 0.0) / (8.0 * math.pi ** 2))
    out = np.zeros_like(z)
    for a, b in zip(params["a"], params["b"]):
        kappa = 2.0 * math.pi * math.sqrt(b)
        out = out + a * math.pi / math.sqrt(b) * _exp_abs_conv(z, kappa, sigma)
    for c, d in zip(params["c"], params["d"]):
        dp = d + B / 4.0
        out = out + c * math.sqrt(math.pi / dp) * np.exp(-math.pi ** 2 * z * z / dp)
    return KIRKLAND_PREFACTOR_V_A2 * out


def atom_areal_profile_imag(dz_rel, B: float, a_im, b_im, scale: float = 1.0):
    """Absorptive analogue of atom_areal_profile, built from Peng-form Gaussians. Result in V*Å^2.

    Form: f_im(s) = sum a_im exp(-(b_im + B/2) s^2), with B/2 in the imaginary part
    [card peng_ch13 eqn 13.84/13.90, p.21-23; peng_ch05 5.127, p.46]. Label: SECTION_READ.
    In Kirkland q (s = q/2) this is c = a_im and d' = (b_im + B/2)/4. Label: DERIVED_HERE.
    The Si values of a_im and b_im are NOT IN any card. They must be supplied by the caller (UNVERIFIED).
    """
    z = np.asarray(dz_rel, float)
    out = np.zeros_like(z)
    for a, b in zip(a_im, b_im):
        dp = (b + B / 2.0) / 4.0
        out = out + scale * a * math.sqrt(math.pi / dp) * np.exp(-math.pi ** 2 * z * z / dp)
    return KIRKLAND_PREFACTOR_V_A2 * out


def beta_rel(E_eV: float) -> float:
    """v/c = sqrt(1 - gamma^-2), with gamma = 1 + E/(m_e c^2).

    Used for the absorption energy scaling of Peng 5.128 [card peng_ch05, p.46-47]. Label: SECTION_READ.
    """
    g = 1.0 + E_eV / _MEC2_EV
    return math.sqrt(1.0 - 1.0 / (g * g))


# ----------------------------------------------------------------------------------------------------
# Surfaces and atomic planes
# ----------------------------------------------------------------------------------------------------
def _hkl_of(obj):
    """Return the surface Miller indices from a geometry.Surface, a string or a tuple.

    Label: DERIVED_HERE.
    """
    if hasattr(obj, "hkl"):
        return tuple(int(v) for v in obj.hkl)
    if isinstance(obj, str):
        m = {"si001": (0, 0, 1), "si111": (1, -1, 1)}
        return m[obj.lower()]
    return tuple(int(v) for v in obj)


def surface_family(hkl) -> str:
    """Return '001' or '111'; any other family raises NotImplementedError (scope R2). Label: DERIVED_HERE."""
    s = tuple(sorted(abs(v) for v in hkl))
    if s == (0, 0, 1):
        return "001"
    if s == (1, 1, 1):
        return "111"
    raise NotImplementedError(f"surface {hkl}: only (001) and (111) families are in scope")


def rod_period(family: str, a: float) -> float:
    """Period of the averaged potential along the normal. Label: DERIVED_HERE.

    * (001): a/4.
    * (111): d111 = a/sqrt3.
    """
    return a / 4.0 if family == "001" else a / math.sqrt(3.0)


def rod_G(family: str, order: int, a: float) -> float:
    """|G| (rad/Å) of specular-rod order n. Label: DERIVED_HERE.

    * (001): (0,0,n), giving 2 pi n/a.
    * (111): (n,-n,n), giving 2 pi n sqrt3/a.
    """
    return 2.0 * math.pi * order / a if family == "001" else 2.0 * math.pi * order * math.sqrt(3.0) / a


def plane_list(family: str, a: float, z_min: float, z_top: float = 0.0):
    """Bulk-terminated atomic planes: (z positions [Å], areal densities [atoms/Å^2]).

    The outermost plane is at z_top and the crystal lies at z < z_top. Label: DERIVED_HERE from the
    diamond basis (fcc + (1/4,1/4,1/4)a):

    * (001): one plane every a/4, each with 2/a^2 atoms.
    * (1,-1,1): the fcc site bonds 3x to the basis plane at +d/4 and 1x to the plane at -3d/4.
      Tight bilayers are therefore {fcc, fcc + d/4}. A cleaved bulk-terminated surface keeps whole
      bilayers, so the planes are z_top - m d and z_top - m d - d/4, each with 4/(sqrt3 a^2) atoms.

    Check: both families give a bulk density of 8/a^3 (tested).
    """
    if family == "001":
        sp = a / 4.0
        n = int(math.ceil((z_top - z_min) / sp)) + 2
        z = z_top - sp * np.arange(n)
        w = np.full(n, 2.0 / a ** 2)
    else:
        d = a / math.sqrt(3.0)
        n = int(math.ceil((z_top - z_min) / d)) + 2
        m = np.arange(n)
        z = np.concatenate([z_top - m * d, z_top - m * d - d / 4.0])
        w = np.full(2 * n, 4.0 / (math.sqrt(3.0) * a ** 2))
    return z, w


def _cell_planes(cell):
    """Atom z positions and weights (1/area) from a kernel EdgeOnCell, so that both codes use the same atoms.

    Label: ASSUMPTION. Column 1 of each atoms_per_slice array is taken to be z, per the CONTRACT
    coordinate order (y, z). This can be overridden with cell.meta['atom_columns'] = ('y','z').
    The area is n_slices*dx * ny*dy.
    """
    cols = tuple(cell.meta.get("atom_columns", ("y", "z"))) if hasattr(cell, "meta") else ("y", "z")
    iz = cols.index("z")
    zs, Zs = [], []
    for atoms, Z in zip(cell.atoms_per_slice, cell.Z_per_slice):
        atoms = np.asarray(atoms, float)
        if atoms.size:
            zs.append(atoms[:, iz])
            Zs.append(np.asarray(Z))
    zs = np.concatenate(zs)
    Zs = np.concatenate(Zs)
    if not np.all(Zs == 14):
        raise NotImplementedError("1D check carries only the Si (Z=14) card row")
    area = cell.n_slices * cell.dx * cell.grid.ny * cell.grid.dy
    return zs, np.full(zs.shape, 1.0 / area)


def _resolve_absorption(absorption, accept_assumptions: bool, E_eV: float):
    """Turn the `absorption` argument into an absorption mode. Label: DERIVED_HERE.

    Accepted values:
    * False or 0: W = 0.
    * float: W = ratio * V. ASSUMPTION; Peng ch13 says W is not proportional to V.
    * dict(a_im=..., b_im=..., E_ref_eV=100e3): Peng 13.90 Gaussians, scaled by
      beta(E_ref)/beta(E) per Peng 5.128.
    * None or True: the absorption model is MISSING. This raises unless accept_assumptions=True, in which
      case DEFAULT_W_OVER_V is used and recorded.
    """
    if absorption is False or (isinstance(absorption, (int, float)) and not isinstance(absorption, bool)
                               and float(absorption) == 0.0):
        return ("none", None)
    if absorption is None or absorption is True:
        if not accept_assumptions:
            raise MissingProjectInput(
                "Si absorptive potential W(z) is NOT IN any supplied card (UNVERIFIED). Pass absorption="
                "False, a W/V ratio, or dict(a_im, b_im, E_ref_eV), or accept_assumptions=True to use "
                f"W/V = {DEFAULT_W_OVER_V} (ASSUMPTION).")
        _record_assumption("W_over_V_Si", DEFAULT_W_OVER_V,
                           "Si absorption parameters absent from cards; ratio model contradicts Peng ch13")
        return ("ratio", DEFAULT_W_OVER_V)
    if isinstance(absorption, dict):
        E_ref = float(absorption.get("E_ref_eV", 100e3))
        scale = beta_rel(E_ref) / beta_rel(E_eV)
        return ("peng", dict(a_im=tuple(absorption["a_im"]), b_im=tuple(absorption["b_im"]), scale=scale))
    return ("ratio", float(absorption))


def averaged_potential_z(cell_or_surface, grid_z, E_eV: float = 200e3, B: float | None = None,
                         a: float | None = None, absorption=None, accept_assumptions: bool = False,
                         z_top: float = 0.0, cutoff: float = 15.0) -> np.ndarray:
    """Laterally averaged complex potential V(z) + i W(z), in volts, on grid_z (Å).

    Args:
        cell_or_surface: a geometry.Surface, 'si001'/'si111', an hkl tuple, or a kernel EdgeOnCell.
        B: Debye-Waller B in Å^2. Default constants.B_SI_300K (the label is carried there; the value
            comes from Peng ch14 Table 14.2 [p.9]).
        a: lattice constant in Å. Default constants.A_SI.

    V(z) = sum_n rho_n P(z - z_n), with rho_n the areal density of plane n. Label: DERIVED_HERE
    (see atom_areal_profile). Atoms further than `cutoff` (15 Å) from a grid point are neglected.
    The neglected tail is below exp(-28) of the peak for the slowest Si Lorentzian.
    """
    z = np.asarray(grid_z, float)
    B = float(C.B_SI_300K.value) if B is None else float(B)
    a = float(C.A_SI.value) if a is None else float(a)
    mode, par = _resolve_absorption(absorption, accept_assumptions, E_eV)
    if hasattr(cell_or_surface, "atoms_per_slice"):
        zp, wp = _cell_planes(cell_or_surface)
    else:
        fam = surface_family(_hkl_of(cell_or_surface))
        zp, wp = plane_list(fam, a, float(z.min()) - cutoff, z_top)
    order = np.argsort(z)
    zs = z[order]
    Vr = np.zeros_like(zs)
    Vi = np.zeros_like(zs)
    for z0, w0 in zip(zp, wp):
        i0, i1 = np.searchsorted(zs, [z0 - cutoff, z0 + cutoff])
        if i1 <= i0:
            continue
        dzr = zs[i0:i1] - z0
        Vr[i0:i1] += w0 * atom_areal_profile(dzr, B)
        if mode == "peng":
            Vi[i0:i1] += w0 * atom_areal_profile_imag(dzr, B, par["a_im"], par["b_im"], par["scale"])
    if mode == "ratio":
        Vi = par * Vr
    out = np.empty(z.shape, complex)
    out[order] = Vr + 1j * Vi
    return out


def bulk_mean_potential(E_eV: float = 200e3, a: float | None = None, absorption=False,
                        accept_assumptions: bool = False) -> complex:
    """Mean inner potential of the isolated-atom superposition: 2 pi a0 e f_e(0) * 8/a^3 (V), plus i*mean(W).

    Label: DERIVED_HERE. The route is the one the Kirkland appC card INFERS from C.5 at q = 0 [p.6].
    Caveat: the isolated-atom model has a 5-10% error at q -> 0 [appC p.7]. This value (~13.9 V) is not
    the V0_SI = 12 V ASSUMPTION of constants.py; the difference is reported in NOTES_D.md.
    """
    a = float(C.A_SI.value) if a is None else float(a)
    mode, par = _resolve_absorption(absorption, accept_assumptions, E_eV)
    n = 8.0 / a ** 3
    vr = KIRKLAND_PREFACTOR_V_A2 * fe0() * n
    if mode == "none":
        vi = 0.0
    elif mode == "ratio":
        vi = par * vr
    else:
        vi = KIRKLAND_PREFACTOR_V_A2 * par["scale"] * sum(par["a_im"]) * n
    return complex(vr, vi)


# ----------------------------------------------------------------------------------------------------
# Solvers
# ----------------------------------------------------------------------------------------------------
def _beam(E_eV: float):
    """Return (K [rad/Å], 2 K sigma [Å^-2 per V]) from the constants module.

    Label: DERIVED_HERE (U = 2 K sigma V; see the module docstring).
    """
    lam = float(C.wavelength(E_eV))
    K = 2.0 * math.pi / lam
    return K, 2.0 * K * float(C.interaction_constant(E_eV))


def _qof(kz2, U):
    """Normal wavevector q = sqrt(k_z^2 + U), on the decaying branch Im q >= 0.

    Label: DERIVED_HERE (semi-infinite condition, Peng p.27/p.36).
    """
    q = np.sqrt(kz2 + U)
    return np.where(q.imag < 0, -q, q)


def reflect_1d(theta_ext, E_eV, Vz_complex, z, method: str = "transfer", z_ref: float = 0.0,
               V_sub=None, return_t: bool = False):
    """Complex specular reflection coefficient r(theta_ext) of a layered potential.

    Args:
        theta_ext: external glancing angle(s) in rad.
        Vz_complex: complex potential (V) at uniformly spaced slice centres z (ascending). Each sample
            represents a slice of thickness dz = z[1] - z[0].
        V_sub: potential of the semi-infinite substrate below z[0] - dz/2. Default: mean of the lowest
            quarter of the samples.
        z_ref: plane to which the phase of r is referred. psi_vac = exp(-ik(z-z_ref)) + r exp(+ik(z-z_ref)).
            Vacuum (V = 0) is assumed above z[-1] + dz/2.
        method:
            'transfer': Parratt-type recursion of rho = (up/down) amplitude ratio. It is bounded,
                |rho| <= 1 for W >= 0, and stable for any thickness.
            'matrix': 2x2 characteristic matrix on (psi, psi'). It is exact but numerically unstable for
                thick evanescent stacks, and is intended for tests. With return_t it also returns the
                transmitted flux fraction T = Re(q_sub)|t|^2/k_z.

    Derivation (DERIVED_HERE; continuity of psi and psi' per Peng 5.58-5.59 [p.25]):
        In a homogeneous layer psi = D (e^{-iqz} + rho e^{+iqz}), so rho(z+d) = rho(z) e^{2iqd}.
        Continuity of psi'/psi across an interface (lower -> upper) gives
        rho_u = (r + rho_l)/(1 + r rho_l), with r = (q_u - q_l)/(q_u + q_l).
    """
    th = np.atleast_1d(np.asarray(theta_ext, float))
    z = np.asarray(z, float)
    V = np.asarray(Vz_complex, complex)
    dz = float(z[1] - z[0])
    if not np.allclose(np.diff(z), dz, rtol=1e-6, atol=1e-12):
        raise ValueError("reflect_1d requires a uniform z grid")
    K, uconv = _beam(E_eV)
    U = uconv * V
    if V_sub is None:
        V_sub = V[: max(1, V.size // 4)].mean()
    U_sub = uconv * complex(V_sub)
    kz = (K * np.sin(th)).astype(complex)
    kz2 = kz * kz
    z_e = float(z[-1] + dz / 2.0)
    if method == "transfer":
        q_low = _qof(kz2, U_sub)
        rho = np.zeros_like(kz)
        U_prev = U_sub
        for Uj in U:
            if Uj != U_prev:
                q_up = _qof(kz2, Uj)
                rr = (q_up - q_low) / (q_up + q_low)
                rho = (rr + rho) / (1.0 + rr * rho)
                q_low = q_up
                U_prev = Uj
            rho = rho * np.exp(2j * q_low * dz)
        rr = (kz - q_low) / (kz + q_low)
        rho = (rr + rho) / (1.0 + rr * rho)
        r = rho * np.exp(2j * kz * (z_ref - z_e))
        if return_t:
            raise ValueError("return_t is only available with method='matrix'")
        return r if np.ndim(theta_ext) else r[0]
    if method == "matrix":
        q_s = _qof(kz2, U_sub)
        A = np.ones_like(kz)
        Bv = -1j * q_s
        for Uj in U:
            q = _qof(kz2, Uj)
            c = np.cos(q * dz)
            small = np.abs(q) < 1e-12
            s_over_q = np.where(small, dz, np.sin(q * dz) / np.where(small, 1.0, q))
            A, Bv = c * A + s_over_q * Bv, -q * np.sin(q * dz) * A + c * Bv
        t = 2.0 / (A + 1j * Bv / kz)
        rho = t * A - 1.0
        r = rho * np.exp(2j * kz * (z_ref - z_e))
        T = q_s.real * np.abs(t) ** 2 / kz.real
        if np.ndim(theta_ext) == 0:
            r, T = r[0], T[0]
        return (r, T) if return_t else r
    raise ValueError(f"unknown method {method!r}")


def rocking_curve_1d(surface, E_eV, thetas, dz: float = 0.01, depth: float = 500.0, vacuum: float = 8.0,
                     absorption=None, accept_assumptions: bool = False, B: float | None = None,
                     a: float | None = None, z_ref: float = 0.0, method: str = "transfer") -> RockingCurve:
    """One-beam rocking curve r(theta_ext) of a bulk-terminated Si(001) or Si(111) surface, or of a kernel cell.

    Geometry: the outermost atomic plane is at z = 0 and is also the default phase reference z_ref.
    The crystal extends to -depth, followed by a semi-infinite uniform substrate at the bulk mean
    potential. Vacuum extends above. Label: DERIVED_HERE.

    Defaults (ASSUMPTION; convergence is tested):
    * dz = 0.01 Å. The slice-thickness sensitivity is < 2e-3 in r (test_slice_convergence).
    * depth = 500 Å. With W = 0, finite depth produces thickness fringes outside the Darwin bands.
    """
    thetas = np.asarray(thetas, float)
    t0 = time.perf_counter()
    z = np.arange(-depth + dz / 2.0, vacuum, dz)
    V = averaged_potential_z(surface, z, E_eV=E_eV, B=B, a=a, absorption=absorption,
                             accept_assumptions=accept_assumptions)
    if hasattr(surface, "atoms_per_slice"):
        V_sub = V[: max(1, V.size // 4)].mean()
    else:
        # The absorption mode was resolved (and any assumption recorded) above; reuse its resolution.
        mode_abs = absorption
        if absorption is None or absorption is True:
            mode_abs = DEFAULT_W_OVER_V
        V_sub = bulk_mean_potential(E_eV, a=a, absorption=mode_abs)
    r = reflect_1d(thetas, E_eV, V, z, method=method, z_ref=z_ref, V_sub=V_sub)
    meta = {
        "solver": "reflectivity1d one-beam " + method,
        "dz": dz,
        "depth": depth,
        "vacuum": vacuum,
        "z_ref": z_ref,
        "V_sub": complex(V_sub),
        "V0_profile_mean": float(np.real(V_sub)),
        "B": float(C.B_SI_300K.value) if B is None else B,
        "absorption": repr(absorption),
        "elapsed_s": time.perf_counter() - t0,
        "labels": "DERIVED_HERE (equation), SECTION_READ (scattering factors), ASSUMPTION (dz, depth, W)",
    }
    return RockingCurve(theta_ext=thetas, r=np.asarray(r), meta=meta)


# ----------------------------------------------------------------------------------------------------
# Analysis helpers: peaks, kinematic angle, kernel-agreement metrics
# ----------------------------------------------------------------------------------------------------
def kinematic_external_angle(G: float, E_eV: float, V0: float) -> float:
    """Refraction-corrected kinematic external angle of a specular Bragg order (rad); NaN if inaccessible.

    Bragg inside the crystal: 2 K_int sin(theta_int) = |G| (Peng 5.75 with the internal wavelength, p.29).
    Tangential conservation (Peng 5.76) gives K^2 sin^2(theta_ext) = (G/2)^2 - U0, with U0 = 2 K sigma V0.
    Label: DERIVED_HERE.
    """
    K, uconv = _beam(E_eV)
    arg = 0.25 * G * G - uconv * V0
    return float("nan") if arg <= 0 else math.asin(math.sqrt(arg) / K)


def peak_metrics(theta, R) -> dict:
    """Peak of |r|^2: theta_peak, R_peak, and the left/right half-maximum crossings.

    Returns theta_peak, R_peak, fwhm, theta_center (midpoint of the crossings). The crossings are found
    by linear interpolation; NaN is returned where a crossing lies outside the window.
    Label: DERIVED_HERE.
    """
    theta = np.asarray(theta, float)
    R = np.asarray(R, float)
    i = int(np.argmax(R))
    half = 0.5 * R[i]
    left = right = float("nan")
    j = i
    while j > 0 and R[j] > half:
        j -= 1
    if R[j] <= half and j < i:
        left = theta[j] + (half - R[j]) * (theta[j + 1] - theta[j]) / (R[j + 1] - R[j])
    j = i
    while j < R.size - 1 and R[j] > half:
        j += 1
    if R[j] <= half and j > i:
        right = theta[j - 1] + (half - R[j - 1]) * (theta[j] - theta[j - 1]) / (R[j] - R[j - 1])
    return {"theta_peak": float(theta[i]), "R_peak": float(R[i]), "fwhm": right - left,
            "theta_center": 0.5 * (left + right), "theta_left": left, "theta_right": right}


def agreement_metrics(theta, r_kernel, r_1d, E_eV: float, frac: float = AGREEMENT_TOL["amplitude_frac"]) -> dict:
    """T-1D-agreement metrics between the kernel and the one-beam rocking curves. Label: DERIVED_HERE.

    * Peak position and FWHM: compared on |r|^2.
    * Phase: the reference planes of the two codes may differ by delta_z, and the arg r conventions by a
      constant phi0. Over angles where both |r|^2 exceed frac * max, the residual
      arg(r_k) - arg(r_1d) = phi0 + 2 k_z delta_z is fitted by least squares.
    * Returned: delta_z (to be reported), phi0, and the maximum wrapped residual.
    """
    theta = np.asarray(theta, float)
    rk = np.asarray(r_kernel, complex)
    r1 = np.asarray(r_1d, complex)
    Rk, R1 = np.abs(rk) ** 2, np.abs(r1) ** 2
    pk, p1 = peak_metrics(theta, Rk), peak_metrics(theta, R1)
    K, _ = _beam(E_eV)
    kz = K * np.sin(theta)
    mask = (R1 >= frac * R1.max()) & (Rk >= frac * Rk.max())
    out = {"kernel": pk, "one_beam": p1,
           "peak_shift": pk["theta_center"] - p1["theta_center"],
           "fwhm_rel": pk["fwhm"] / p1["fwhm"] - 1.0}
    if mask.sum() >= 3:
        dphi = np.unwrap(np.angle(rk[mask]) - np.angle(r1[mask]))
        A = np.column_stack([np.ones(mask.sum()), 2.0 * kz[mask]])
        coef, *_ = np.linalg.lstsq(A, dphi, rcond=None)
        resid = np.angle(np.exp(1j * (dphi - A @ coef)))
        out.update(phi0=float(coef[0]), delta_z_ref=float(coef[1]),
                   phase_resid_max=float(np.max(np.abs(resid))), n_phase_points=int(mask.sum()))
    else:
        out.update(phi0=float("nan"), delta_z_ref=float("nan"), phase_resid_max=float("nan"),
                   n_phase_points=int(mask.sum()))
    return out


# ----------------------------------------------------------------------------------------------------
# Script: prints every number quoted from this module in NOTES_D.md
# ----------------------------------------------------------------------------------------------------
def _main() -> None:  # pragma: no cover - script
    """Print the prefactor, f_e(0), Delta, theta_c, V0 of the superposition, and one-beam peak tables.

    Label: DERIVED_HERE.
    """
    E = 200e3
    K, uconv = _beam(E)
    print(f"Kirkland prefactor h^2/(2 pi m0 e) = {KIRKLAND_PREFACTOR_V_A2:.4f} V*A^2 (card prints 47.86)")
    print(f"f_e(0) Kirkland C.15 = {fe0():.4f} A ; Peng Table 13.3 sum a_i = {sum(PENG_T13_3_SI_A):.4f} A")
    for V0 in (12.0, 13.0):
        D = uconv * V0 / K ** 2
        thc = math.asin(math.sqrt(D / (1 + D)))
        print(f"V0 = {V0:.1f} V: Delta = {D:.4e}, theta_c = {1e3 * thc:.3f} mrad")
    V0p = bulk_mean_potential(E).real
    print(f"isolated-atom superposition V0 = {V0p:.3f} V (constants.V0_SI = {C.V0_SI.value} V, ASSUMPTION)")
    cases = [("si001", "001", 8), ("si001", "001", 12), ("si111", "111", 4)]
    for name, fam, n in cases:
        G = rod_G(fam, n, float(C.A_SI.value))
        tk = kinematic_external_angle(G, E, V0p)
        tk12 = kinematic_external_angle(G, E, float(C.V0_SI.value))
        th = np.linspace(tk - 1.0e-3, tk + 1.0e-3, 801)
        t0 = time.perf_counter()
        rc = rocking_curve_1d(name, E, th, absorption=False, depth=600.0)
        pm = peak_metrics(th, np.abs(rc.r) ** 2)
        th2 = np.linspace(pm["theta_center"] - 3 * pm["fwhm"], pm["theta_center"] + 3 * pm["fwhm"], 601)
        rc2 = rocking_curve_1d(name, E, th2, absorption=False, depth=600.0)
        pm2 = peak_metrics(th2, np.abs(rc2.r) ** 2)
        dt = time.perf_counter() - t0
        print(f"{name} order {n}: kinematic theta_ext(V0={V0p:.2f}) = {1e3 * tk:.4f} mrad, "
              f"(V0=12) = {1e3 * tk12:.4f} mrad | 1D W=0: centre {1e3 * pm2['theta_center']:.4f} mrad, "
              f"FWHM {1e3 * pm2['fwhm']:.4f} mrad, R_peak {pm2['R_peak']:.5f} | {dt:.1f} s for 1402 angles")
    rc = rocking_curve_1d("si001", E, np.linspace(14e-3, 18e-3, 100), absorption=DEFAULT_W_OVER_V)
    print(f"timing: 100-angle Si(001) one-beam curve, depth 500 A, dz 0.01 A: {rc.meta['elapsed_s']:.2f} s")


if __name__ == "__main__":  # pragma: no cover
    _main()
