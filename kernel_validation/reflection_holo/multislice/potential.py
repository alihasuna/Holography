"""Complex projected potential per beam-perpendicular slice (rung R2, item 2a).

Geometry (CONTRACT): x is the beam axis and slices are perpendicular to x. Each
slice is a (z, y) array of shape (nz, ny). z is the OUTWARD surface normal
(vacuum at +z) and y is the in-surface transverse direction.

Equations and their evidence
----------------------------
E1  f_e(q) = sum_i a_i/(q^2+b_i) + sum_i c_i exp(-d_i q^2), with q in cycles/A.
    SECTION_READ [kirkland_appC p.8, Eq. C.15]; Si row [kirkland_appC p.12].
    q is the Fourier variable of exp(2 pi i q.r) in Eq. C.5 [kirkland_appC p.6].
E2  Projected potential of one slice built in Fourier space:
        V_z(q) = (h^2 / (2 pi m0 e)) * f_e(|q|) * T(q) * exp(-2 pi i q.r_j)
        V_z(r) = (1/A) sum_q V_z(q) exp(+2 pi i q.r)
    The prefactor h^2/(2 pi m0 e) = 2 pi e a0 (card: a0 = 0.5292 A, e = 14.4 V A,
    [kirkland_appC p.6, p.11]) is DERIVED_HERE from exact constants (47.877 V A^2).
    The printed value 47.86, with the rest mass m0, is Kirkland Eq. 6.10 [kirkland_ch06 p.7;
    Kirkland 2020 printed p.149], SECTION_READ (reflib kirkland2020:p158:b2, both readers
    and the PDF text layer agree). 47.86 is 0.037 % below the exact value: the book rounds.
    numpy's forward FFT has exp(-2 pi i) (repo conventions), so an atom at r_j carries
    exp(-2 pi i q.r_j) here. DERIVED_HERE.
    The m/m0 factor is NOT in V; it enters only through sigma (constants.interaction_constant).
    The construction is periodic over the grid (FFT): atoms must NOT be added again as images.
E3  Real-space reference, used only in tests: Eq. C.20 with K0 [kirkland_appC p.11].
E4  Debye-Waller factor: T(q) = exp(-B s^2) with s = q/2, an AMPLITUDE factor on f_e
    [peng_ch13 Eq. 13.52, p.11; Peng 2004 printed p.437]. s = q/2 is DERIVED_HERE from the
    two Fourier conventions: Kirkland's q is the variable of exp(2 pi i q.r) [Kirkland 2020
    Eq. C.5, printed p.288], so |q| = 1/d; Peng's s = g/(4 pi) = sin(theta)/lambda with
    exp(-i g.r), g = 2 pi/d [Peng 2004 Eq. 13.31 and text, printed p.432, p.448], so s = 1/(2d).
    REPRODUCED: Peng Table 13.3 Si f(s) [printed p.450] equals Kirkland f_e(q = 2s) to about
    1 % for 0 <= s <= 1.5 1/A, while q = s is off by a factor 2-3. Kirkland's prose
    "q = sin(alpha)/lambda ... alpha is the scattering semi-angle" [printed p.287] would give
    q = s and contradicts his Eqs. C.3/C.5: do not use it.
E5  Frozen phonons: per-Cartesian-axis variance <u_x^2> = B/(8 pi^2). DERIVED_HERE from
    B = 8 pi^2 <u^2> with <u^2> the per-axis mean [peng_ch13 Eqs. 13.50-13.51, p.10-11].
E6  Absorptive part: Peng form i*a_Im*exp(-(b_Im + B/2) s^2) [peng_ch13 p.21, Eq. 13.87].
    NO Si parameters exist on the card [peng_ch13 p.20]: constants.ABSORPTION_MODEL is
    status MISSING and any use raises MissingProjectInput (even with accept_assumptions,
    because no placeholder parameters exist). A caller may supply the 'proportional'
    model (ASSUMPTION) explicitly, with accept_assumptions=True.
E7  Transmission t = exp(i sigma v). With complex v = V + iW and W > 0, |t| = exp(-sigma W)
    < 1, so W > 0 attenuates under exp(+i k.r). DERIVED_HERE.
E8  Minimum slice thickness about 1 A for full-projection potentials. UNVERIFIED (Kirkland
    ch.6 card not attached in this integration set); kept as a warning only.
E9  Potential band-limited to 2/3 of k_max, k_max = min(1/(2dy), 1/(2dz)). Kirkland 2/3 rule,
    SECTION_READ: "set the maximum spatial frequency (or bandwidth) of both functions to be
    2/3 of the maximum sampling frequency"; the limit "appears as a circle" [Kirkland 2020
    Sect. 6.8, printed p.177, reflib kirkland2020:c282; k_max Eq. 6.92, printed p.176].
    Kirkland applies it to the wave and the transmission function; applying it to V as
    well is a repository choice (DERIVED_HERE: t = exp(i sigma v) is then band-limited too).
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import special
from scipy.integrate import trapezoid

from reflection_holo.constants import (
    ABSORPTION_MODEL,
    KIRKLAND_SI,
    interaction_constant,
    wavelength,
)
from reflection_holo import project_inputs as _pi

# Exact SI-2019 constants and CODATA-2018 m_e c^2 (physics_conventions.md). SECTION_READ.
_H = 6.62607015e-34          # J s
_E = 1.602176634e-19         # C
_C = 299792458.0             # m/s
_MEC2_EV = 510998.950        # eV
_M0 = _MEC2_EV * _E / _C**2  # kg

#: h^2/(2 pi m0 e) = 2 pi e a0, in V*A^2. DERIVED_HERE from exact constants (~47.877).
PREF_V_A2: float = _H**2 / (2.0 * np.pi * _M0 * _E) * 1e20
KIRKLAND_CH06_PREFACTOR_PRINTED: float = 47.86   # Kirkland Eq. 6.10, printed p.149 (SECTION_READ, E2)
KIRKLAND_FIT_QMAX: float = 12.0                  # 1/A, SECTION_READ [kirkland_appC p.7]
MIN_SLICE_A: float = 1.0                         # A, UNVERIFIED (see E8)

_VERIFIED_LABELS = {"SECTION_READ", "REPRODUCED", "DERIVED_HERE"}
_ORDER12 = ("a1", "b1", "a2", "b2", "a3", "b3", "c1", "d1", "c2", "d2", "c3", "d3")


@dataclass
class Grid:
    """(z, y) sampling grid of one beam-perpendicular slice. Arrays have shape (nz, ny).

    Lengths in A; z increases toward vacuum. Pixel centres at y0 + i*dy, z0 + j*dz.
    Periodic in both directions (FFT). Label: DERIVED_HERE (data container).
    """
    ny: int
    nz: int
    dy: float
    dz: float
    y0: float = 0.0
    z0: float = 0.0

    def __post_init__(self) -> None:
        if self.ny < 1 or self.nz < 1:
            raise ValueError("ny, nz must be >= 1")
        if self.dy <= 0 or self.dz <= 0:
            raise ValueError("dy, dz must be > 0 (A)")

    @property
    def y(self) -> np.ndarray:
        return self.y0 + self.dy * np.arange(self.ny)

    @property
    def z(self) -> np.ndarray:
        return self.z0 + self.dz * np.arange(self.nz)

    @property
    def area(self) -> float:
        return self.ny * self.dy * self.nz * self.dz

    def freqs(self) -> tuple[np.ndarray, np.ndarray]:
        """Return (qz[nz,1], qy[1,ny]) in cycles/A, in numpy FFT order."""
        qz = np.fft.fftfreq(self.nz, self.dz)[:, None]
        qy = np.fft.fftfreq(self.ny, self.dy)[None, :]
        return qz, qy

    def q2(self) -> np.ndarray:
        qz, qy = self.freqs()
        return qz**2 + qy**2

    @property
    def kmax(self) -> float:
        """Isotropic sampling limit min(1/2dy, 1/2dz) in cycles/A."""
        return min(1.0 / (2 * self.dy), 1.0 / (2 * self.dz))


def bandwidth_mask(grid: Grid, fraction: float | None = 2.0 / 3.0) -> np.ndarray:
    """Boolean mask |q| < fraction * k_max (largest inscribed circle).

    With fraction=None only the unpaired Nyquist rows and columns are removed,
    which keeps real functions real.
    """
    qz, qy = grid.freqs()
    if fraction is None:
        m = np.ones((grid.nz, grid.ny), dtype=bool)
        if grid.nz % 2 == 0 and grid.nz > 1:
            m[grid.nz // 2, :] = False
        if grid.ny % 2 == 0 and grid.ny > 1:
            m[:, grid.ny // 2] = False
        return m
    return np.sqrt(qz**2 + qy**2) < fraction * grid.kmax


def _val(v: Any) -> float:
    return float(getattr(v, "value", v))


def kirkland_coefficients(entry: dict | None = None) -> dict[str, np.ndarray]:
    """Parse a Kirkland Appendix C row into arrays a, b, c, d (each of length 3).

    Units: a 1/A, b 1/A^2, c A, d A^2 [kirkland_appC p.9]. Printed row order
    a1 b1 a2 b2 / a3 b3 c1 d1 / c2 d2 c3 d3 [kirkland_appC p.9, p.12].
    Accepted dict layouts: {'a','b','c','d'}; {'a1',...,'d3'}; or a 12-value list under
    'row'/'params'/'parameters'/'values'/'coefficients'. Label: SECTION_READ (values from
    constants.KIRKLAND_SI).
    """
    entry = KIRKLAND_SI if entry is None else entry
    if all(k in entry for k in ("a", "b", "c", "d")):
        a, b, c, d = (np.array([_val(x) for x in entry[k]], float) for k in ("a", "b", "c", "d"))
    elif all(k in entry for k in _ORDER12):
        v = {k: _val(entry[k]) for k in _ORDER12}
        a = np.array([v["a1"], v["a2"], v["a3"]])
        b = np.array([v["b1"], v["b2"], v["b3"]])
        c = np.array([v["c1"], v["c2"], v["c3"]])
        d = np.array([v["d1"], v["d2"], v["d3"]])
    else:
        row = None
        for key in ("row", "params", "parameters", "values", "coefficients"):
            if key in entry:
                row = entry[key]
                break
        if isinstance(row, dict):
            return kirkland_coefficients(row)
        if row is None or len(row) != 12:
            raise KeyError(
                "KIRKLAND_SI layout not recognised: need keys a,b,c,d or a1..d3 or a "
                "12-value printed row [kirkland_appC p.12]")
        r = [_val(x) for x in row]
        a = np.array([r[0], r[2], r[4]])
        b = np.array([r[1], r[3], r[5]])
        c = np.array([r[6], r[8], r[10]])
        d = np.array([r[7], r[9], r[11]])
    for name, arr in (("a", a), ("b", b), ("c", c), ("d", d)):
        if arr.shape != (3,) or np.any(arr <= 0):
            raise ValueError(f"Kirkland '{name}' must be 3 positive values [kirkland_appC p.9]")
    return {"a": a, "b": b, "c": c, "d": d}


def fe_kirkland(q: np.ndarray | float, coeffs: dict | None = None) -> np.ndarray:
    """Electron scattering factor f_e(q) in A, q in cycles/A. SECTION_READ [kirkland_appC p.8,
    Eq. C.15]. Fit valid for q < 12/A [kirkland_appC p.7]; do not extrapolate."""
    co = kirkland_coefficients() if coeffs is None else coeffs
    q2 = np.asarray(q, float)[..., None] ** 2
    return (np.sum(co["a"] / (q2 + co["b"]), axis=-1)
            + np.sum(co["c"] * np.exp(-co["d"] * q2), axis=-1))


def projected_atom_realspace(r: np.ndarray | float, coeffs: dict | None = None) -> np.ndarray:
    """Projected atomic potential v_z(r) in V*A for an undisplaced atom (no DW).

    SECTION_READ [kirkland_appC p.11, Eq. C.20]:
        4 pi^2 a0 e sum a_i K0(2 pi r sqrt b_i) + 2 pi^2 a0 e sum (c_i/d_i) exp(-pi^2 r^2/d_i),
    with 2 pi e a0 = PREF_V_A2. Logarithmically singular at r = 0. Tests only.
    """
    co = kirkland_coefficients() if coeffs is None else coeffs
    r = np.asarray(r, float)[..., None]
    yuk = np.sum(co["a"] * special.k0(2 * np.pi * r * np.sqrt(co["b"])), axis=-1)
    gau = np.sum(co["c"] / co["d"] * np.exp(-np.pi**2 * r**2 / co["d"]), axis=-1)
    return 2 * np.pi * PREF_V_A2 * yuk + np.pi * PREF_V_A2 * gau


def resolve_absorption_model(model: dict | None = None, accept_assumptions: bool = False) -> dict:
    """Validate the absorptive-potential model and return {'name', 'params'}.

    Supported names:
      'peng_gaussian'  f_im(s) = sum_j a_j exp(-(b_j + B/2) s^2), s = q/2, a in A, b in A^2.
                       Form SECTION_READ [peng_ch13 p.21, Eq. 13.87]; Si PARAMETERS NOT IN
                       THE DOCUMENT [peng_ch13 p.20].
      'proportional'   W(q) = kappa * V(q). ASSUMPTION, contradicted by Peng ch.13
                       (own q dependence and B/2 smearing [peng_ch13 p.17, p.21]).
    A model with status 'MISSING' or parameters None ALWAYS raises MissingProjectInput
    (there is no placeholder to accept: repo item 21). A label outside
    {SECTION_READ, REPRODUCED, DERIVED_HERE} raises MissingProjectInput unless
    accept_assumptions=True; if accepted it is recorded in USED_ASSUMPTIONS and printed.
    """
    m = ABSORPTION_MODEL if model is None else model
    if not isinstance(m, dict):
        raise TypeError("absorption model must be a dict with name, parameters, label, source")
    name = str(m.get("name", "")).lower()
    label = str(m.get("label", "UNVERIFIED")).upper()
    raw_params = m.get("parameters", m.get("params"))
    if str(m.get("status", "")).upper() == "MISSING" or raw_params is None:
        raise _pi.MissingProjectInput(
            f"absorption model '{name}' has no parameters (status {m.get('status')}; "
            f"source: {m.get('source')}). Si absorptive parameters are NOT IN the Peng ch.13 "
            "card [p.20] (repo item 21). Supply them, call with absorption=False, or pass an "
            "explicit model such as {'name': 'proportional', 'parameters': {'fraction': f}, "
            "'label': 'ASSUMPTION'} with accept_assumptions=True.")
    params = raw_params or {}
    if name in ("", "none"):
        raise _pi.MissingProjectInput("absorption=True but the absorption model has no name.")
    if name == "proportional":
        kappa = _val(params.get("fraction", params.get("kappa", np.nan)))
        if not np.isfinite(kappa) or kappa < 0:
            raise ValueError("proportional absorption needs parameters['fraction'] >= 0")
        parsed: dict = {"kappa": kappa}
    elif name == "peng_gaussian":
        a = np.array([_val(x) for x in params["a"]], float)
        b = np.array([_val(x) for x in params["b"]], float)
        if a.shape != b.shape or np.any(b < 0):
            raise ValueError("peng_gaussian needs equal-length a (A) and b (A^2 >= 0)")
        parsed = {"a": a, "b": b}
    else:
        raise ValueError(f"unknown absorption model '{name}'")
    if label not in _VERIFIED_LABELS:
        if not accept_assumptions:
            raise _pi.MissingProjectInput(
                f"absorption model '{name}' has label {label} (source: {m.get('source')}). "
                "It is not verified by any card. Pass accept_assumptions=True to use it.")
        rec = {"id": "absorption_model",
               "value": {"name": name, **{k: (v.tolist() if isinstance(v, np.ndarray) else v)
                                          for k, v in parsed.items()}},
               "label": label, "source": m.get("source")}
        used = getattr(_pi, "USED_ASSUMPTIONS", None)
        if used is not None and rec not in used:
            used.append(rec)
            print(f"ASSUMPTION used: absorption_model = {rec['value']} (label {label})")
    return {"name": name, "params": parsed}


def _fe_absorptive(q: np.ndarray, fe_real_dw: np.ndarray, B: float, model: dict) -> np.ndarray:
    if model["name"] == "proportional":
        return model["params"]["kappa"] * fe_real_dw
    s2 = (q / 2.0) ** 2
    a, b = model["params"]["a"], model["params"]["b"]
    return np.sum(a * np.exp(-(b + B / 2.0) * s2[..., None]), axis=-1)


def _coeffs_for(Zval: int, scattering_params: dict | None) -> dict:
    if scattering_params is not None and Zval in scattering_params:
        return kirkland_coefficients(scattering_params[Zval])
    if Zval == 14:
        return kirkland_coefficients()
    raise KeyError(
        f"No scattering-factor row for Z={Zval} in constants (only Si, Z=14). H and O rows "
        "are on [kirkland_appC p.11] but are out of this rung's scope; pass scattering_params.")


def _check_slice(dx_slice: float) -> None:
    if not dx_slice > 0:
        raise ValueError("dx_slice must be > 0 (A)")
    if dx_slice < MIN_SLICE_A:
        warnings.warn(
            f"dx_slice = {dx_slice} A < 1 A: the full-projection potential is questionable "
            "below about 1 A (Kirkland rule; UNVERIFIED in this card set)", UserWarning, stacklevel=3)


def projected_potential(atoms_yz: np.ndarray, Z: np.ndarray, grid: Grid, dw_B: float | np.ndarray,
                        dx_slice: float, *, absorption: bool = True,
                        absorption_model: dict | None = None, accept_assumptions: bool = False,
                        scattering_params: dict | None = None,
                        bandwidth: float | None = 2.0 / 3.0) -> np.ndarray:
    """Complex projected potential V + iW (V*A) of the atoms in one slice, shape (nz, ny).

    atoms_yz: (n, 2) array of [y, z] positions in A, projected fully along x (E2).
    Z: atomic numbers. dw_B: Debye-Waller B in A^2 (0 with frozen-phonon displacements).
    absorption=True requires a validated absorption model (E6); otherwise
    MissingProjectInput is raised. Set absorption=False for a real potential.
    The result is periodic over the grid; do not add periodic images (E2).
    Labels: SECTION_READ (E1, E4), DERIVED_HERE (FFT sign and normalisation).
    """
    _check_slice(dx_slice)
    atoms = np.asarray(atoms_yz, float).reshape(-1, 2)
    n = atoms.shape[0]
    out_shape = (grid.nz, grid.ny)
    if n == 0:
        return np.zeros(out_shape, complex)
    Zarr = np.broadcast_to(np.asarray(Z, int), (n,)).copy()
    Barr = np.broadcast_to(np.asarray(dw_B, float), (n,)).copy()
    if np.any(Barr < 0):
        raise ValueError("Debye-Waller B must be >= 0")
    model = resolve_absorption_model(absorption_model, accept_assumptions) if absorption else None

    if bandwidth is None:
        # Keep the unpaired Nyquist row/column with half weight on +q_N and -q_N, i.e. their real
        # (cosine) part. Dropping them (previous behaviour) removed a (-1)^j stripe of amplitude
        # ~ (2 pi e a0 / A) * sum_q f_e(sqrt(q^2 + q_N^2)) through each atom, because f_e falls only
        # as 1/q^2 (Lorentzian terms, kirkland_appC Eq. C.15). Fix 2026-10-16 (orchestrator), test
        # test_fourier_vs_realspace_C20. Label: DERIVED_HERE.
        mask = np.ones((grid.nz, grid.ny), dtype=bool)
    else:
        mask = bandwidth_mask(grid, bandwidth)
    qz, qy = grid.freqs()
    q2 = qz**2 + qy**2
    q = np.sqrt(q2)
    qmax_used = float(q[mask].max()) if mask.any() else 0.0
    if qmax_used > KIRKLAND_FIT_QMAX:
        warnings.warn(f"retained q up to {qmax_used:.2f}/A exceeds the Kirkland fit range 12/A "
                      "[kirkland_appC p.7]", UserWarning, stacklevel=2)

    yrel = atoms[:, 0] - grid.y0
    zrel = atoms[:, 1] - grid.z0
    Xre = np.zeros(out_shape, complex)
    Xim = np.zeros(out_shape, complex)
    for Zval, Bval in sorted(set(zip(Zarr.tolist(), Barr.tolist()))):
        sel = (Zarr == Zval) & (Barr == Bval)
        co = _coeffs_for(int(Zval), scattering_params)
        Ez = np.exp(-2j * np.pi * qz[:, 0][:, None] * zrel[sel][None, :])   # (nz, m)
        Ey = np.exp(-2j * np.pi * qy[0, :][:, None] * yrel[sel][None, :])   # (ny, m)
        if bandwidth is None:
            if grid.nz % 2 == 0 and grid.nz > 1:
                Ez[grid.nz // 2, :] = np.cos(2 * np.pi * qz[grid.nz // 2, 0] * zrel[sel])
            if grid.ny % 2 == 0 and grid.ny > 1:
                Ey[grid.ny // 2, :] = np.cos(2 * np.pi * qy[0, grid.ny // 2] * yrel[sel])
        S = Ez @ Ey.T
        fe_dw = fe_kirkland(q, co) * np.exp(-Bval * q2 / 4.0)              # E1 * E4, s = q/2
        Xre += fe_dw * S
        if model is not None:
            Xim += _fe_absorptive(q, fe_dw, Bval, model) * S
    norm = PREF_V_A2 / (grid.dy * grid.dz)
    V = np.fft.ifft2(Xre * mask).real * norm
    W = np.fft.ifft2(Xim * mask).real * norm if model is not None else 0.0
    return V + 1j * W


def absorber_profile(grid: Grid, z_top: float, strength_V: float, shape: str = "cos2",
                     dx_slice: float | None = None) -> np.ndarray:
    """Graded imaginary absorber (returned as i*W*dx, in V*A) on the bulk side, z0..z_top.

    W(z) = strength_V * p(xi), xi = (z_top - z)/(z_top - z0) in [0, 1]:
      'cos2'   p = sin^2(pi xi/2): zero value and slope at z_top (default)
      'linear' p = xi
      'step'   p = 1 below z_top (sensitivity demonstration only)
    W >= 0 attenuates (E7). dx_slice is REQUIRED (V*A needs the slice length).
    Label: ASSUMPTION (numerical device); reflection tested in tests/test_propagate.py.
    """
    if dx_slice is None:
        raise TypeError("absorber_profile needs dx_slice (A): the CONTRACT promises V*A, which "
                        "requires the slice thickness (see NOTES_B.md, deviations)")
    if strength_V < 0:
        raise ValueError("absorber strength must be >= 0 V (W > 0 attenuates)")
    zb = grid.z0
    if not (zb < z_top <= zb + grid.nz * grid.dz):
        raise ValueError("z_top must lie inside the grid, above its bottom edge")
    z = grid.z
    xi = np.clip((z_top - z) / (z_top - zb), 0.0, 1.0)
    below = z < z_top
    if shape == "cos2":
        p = np.sin(0.5 * np.pi * xi) ** 2
    elif shape == "linear":
        p = xi.copy()
    elif shape == "step":
        p = below.astype(float)
    else:
        raise ValueError(f"unknown absorber shape '{shape}'")
    p = np.where(below, p, 0.0)
    return 1j * (strength_V * p * dx_slice)[:, None] * np.ones((1, grid.ny))


def absorber_round_trip(strength_V: float, z_extent: float, theta_int: float, E_eV: float,
                        shape: str = "cos2", n: int = 4001) -> dict:
    """Stationary (WKB) attenuation through the absorber, design aid. DERIVED_HERE (NOTES_B E10):
    k_z^2(z) = (K sin theta_int)^2 + i 4 pi sigma W(z)/lambda; I = integral of Im k_z dz."""
    lam = wavelength(E_eV)
    sig = interaction_constant(E_eV)
    k = 2 * np.pi / lam * np.sin(theta_int)
    xi = np.linspace(0, 1, n)
    p = {"cos2": np.sin(0.5 * np.pi * xi) ** 2, "linear": xi, "step": np.ones_like(xi)}[shape]
    kz = np.sqrt(k**2 + 1j * 4 * np.pi * sig * strength_V * p / lam)
    I = z_extent * trapezoid(kz.imag, xi)
    return {"I": float(I), "one_way_amplitude": float(np.exp(-I)),
            "round_trip_intensity": float(np.exp(-4 * I))}


def frozen_phonon_displacements(n_atoms: int, B: float | np.ndarray,
                                rng: np.random.Generator | int | None) -> np.ndarray:
    """Gaussian thermal displacements (n_atoms, 3) in A, columns (x, y, z) of the slab frame.

    Per-axis variance B/(8 pi^2) (E5, DERIVED_HERE). rng must be explicit.
    Use dw_B=0 in projected_potential when displacements are applied.
    """
    if rng is None:
        raise ValueError("pass an explicit numpy Generator or integer seed")
    rng = np.random.default_rng(rng) if not isinstance(rng, np.random.Generator) else rng
    Barr = np.broadcast_to(np.asarray(B, float), (n_atoms,))
    if np.any(Barr < 0):
        raise ValueError("B must be >= 0")
    std = np.sqrt(Barr / (8 * np.pi**2))
    return rng.normal(size=(n_atoms, 3)) * std[:, None]


def transmission_function(V_proj_complex: np.ndarray, sigma: float) -> np.ndarray:
    """t = exp(i sigma v), complex v (V*A), sigma in rad/(V*A). Im v > 0 gives |t| < 1 (E7)."""
    return np.exp(1j * sigma * np.asarray(V_proj_complex))


@dataclass
class SlicePotential:
    """Complex projected potential of one slice (V*A): real part from Kirkland parameters with
    DW damping; imaginary part from the absorption model; plus an optional absorber dict
    {'z_top', 'strength_V', 'shape'}. Labels as in projected_potential/absorber_profile."""
    grid: Grid
    atoms_yz: np.ndarray
    Z: np.ndarray
    dw_B: float | np.ndarray
    dx_slice: float
    absorption: bool = True
    absorption_model: dict | None = None
    accept_assumptions: bool = False
    absorber: dict | None = None
    bandwidth: float | None = 2.0 / 3.0

    def projected(self) -> np.ndarray:
        V = projected_potential(self.atoms_yz, self.Z, self.grid, self.dw_B, self.dx_slice,
                                absorption=self.absorption, absorption_model=self.absorption_model,
                                accept_assumptions=self.accept_assumptions, bandwidth=self.bandwidth)
        if self.absorber:
            V = V + absorber_profile(self.grid, dx_slice=self.dx_slice, **self.absorber)
        return V

    def transmission(self, sigma: float) -> np.ndarray:
        return transmission_function(self.projected(), sigma)


def _main() -> None:  # prints every number quoted in NOTES_B.md for this module
    from reflection_holo.constants import A_SI
    E0 = _pi.get("E0")
    co = kirkland_coefficients()
    fe0 = float(fe_kirkland(0.0, co))
    a = _val(A_SI)
    v0_iam = PREF_V_A2 * 8 * fe0 / a**3
    print(f"PREF h^2/(2 pi m0 e)        = {PREF_V_A2:.4f} V*A^2 (printed 47.86, rel diff "
          f"{PREF_V_A2 / KIRKLAND_CH06_PREFACTOR_PRINTED - 1:+.2e})")
    print(f"f_e^Si(0) Kirkland           = {fe0:.4f} A")
    print(f"v_z^Si(r=0.1 A) Eq. C.20     = {float(projected_atom_realspace(0.1, co)):.1f} V*A")
    print(f"V0 (IAM, 8 atoms / a^3)      = {v0_iam:.2f} V  (a = {a} A)")
    print(f"sigma(E0={E0:.0f} eV)          = {interaction_constant(E0):.6e} rad/(V*A)")
    for th in (8.4e-3, 18.5e-3, 27.7e-3):
        r = absorber_round_trip(10.0, 60.0, th, E0)
        print(f"absorber 10 V / 60 A cos2, theta_int={th*1e3:.1f} mrad: round-trip intensity "
              f"{r['round_trip_intensity']:.2e}")


if __name__ == "__main__":
    _main()
