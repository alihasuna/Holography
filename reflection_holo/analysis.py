"""Extraction of complex reflectivities and image waves from exit waves."""
from __future__ import annotations

import numpy as np

from .beams import kz_minus_k


def fourier_coefficients(psi, grid):
    """c(qx, qy) with psi(x, y) = sum c exp(2 pi i (qx x + qy y)), absolute x, y."""
    psi = np.asarray(psi)
    C = np.fft.fft2(psi) / (grid.Nx * grid.Ny)
    return C * np.exp(-2j * np.pi * (grid.qx[:, None] * grid.x0 + grid.qy[None, :] * grid.y0))


def smooth_window(x, x_lo, ramp_lo, x_hi, ramp_hi):
    """1 on [x_lo, x_hi], cos^2 ramps of the given widths outside, 0 beyond."""
    x = np.asarray(x, float)
    w = np.ones_like(x)
    lo = x < x_lo
    w[lo] = np.cos(0.5 * np.pi * np.clip((x_lo - x[lo]) / ramp_lo, 0, 1)) ** 2
    hi = x > x_hi
    w[hi] = np.cos(0.5 * np.pi * np.clip((x[hi] - x_hi) / ramp_hi, 0, 1)) ** 2
    return w


def specular_reflectivity(exit_wave, grid, a_in, z_exit, lam, x_ref, window,
                          rel_threshold=1e-3):
    """Complex specular reflection coefficient r(theta) referred to the plane x_ref.

    r(q) = c_R(q, 0) exp(-i (kz - k) z_exit) / a(-q) * exp(4 pi i q x_ref), q > 0,
    where c_R are the coefficients of the windowed exit wave and a the incident
    coefficients at z = 0 (DERIVED_HERE, docs/08 appendix A).  Returned only where
    |a(-q)| > rel_threshold max|a|.
    """
    psi = np.asarray(exit_wave) * window[:, None]
    C = fourier_coefficients(psi, grid)
    qx = grid.qx
    # index of -q for every q on the grid
    Nx = grid.Nx
    idx_neg = (-np.arange(Nx)) % Nx
    a_neg = a_in[idx_neg]
    amax = np.abs(a_in).max()
    sel = (qx > 0) & (np.abs(a_neg) > rel_threshold * amax)
    q = qx[sel]
    c0 = C[sel, 0]
    prop = np.exp(-1j * kz_minus_k(q**2, lam) * z_exit)
    r = c0 * prop / a_neg[sel] * np.exp(4j * np.pi * q * x_ref)
    up = (qx > 0)
    down = (qx < 0)
    P_up_spec = np.sum(np.abs(C[up, 0]) ** 2)
    P_down = np.sum(np.abs(C[down, :]) ** 2)
    P_up_all = np.sum(np.abs(C[up, :]) ** 2)
    return dict(
        q=q, theta=np.arcsin(q * lam), r=r, weight=np.abs(a_neg[sel]) / amax,
        P_up_specular_rod=float(P_up_spec), P_up_all=float(P_up_all),
        P_down_in_window=float(P_down),
        C=C,
    )


def rod_intensities(C, grid, n_rods, Py):
    """|c(q, qy)|^2 summed over the rods qy = m / Py for m = -n_rods..n_rods.

    Returns (m, I[m, qx]) for qx > 0; qy values off the rod lattice (diffuse) are
    summed into a separate array."""
    qy = grid.qy
    m_of = np.rint(qy * Py).astype(int)
    on = np.isclose(qy * Py, m_of, atol=1e-6)
    up = grid.qx > 0
    ms = np.arange(-n_rods, n_rods + 1)
    I = np.zeros((len(ms), up.sum()))
    for k, m in enumerate(ms):
        cols = np.nonzero(on & (m_of == m))[0]
        if len(cols):
            I[k] = np.sum(np.abs(C[up][:, cols]) ** 2, axis=1)
    diffuse = np.sum(np.abs(C[up][:, ~on]) ** 2, axis=1)
    return ms, grid.qx[up], I, diffuse


def image_wave_on_plane(C_up, qx_up, qy, lam, z_exit, z_s, x_ref, y0=0.0):
    """Reflected vacuum wave continued to the points (x_ref, y, z_s).

    psi(x_ref, y, z) = sum_{q>0, qy} c(q, qy) exp(2 pi i (q x_ref + qy y))
                        exp(i (kz(q, qy) - k)(z - z_exit)).
    Returns the image as an array (len(z_s), Ny) on the y grid (inverse FFT in y).
    C_up: coefficients for the q > 0 rows (n_q, Ny) in FFT order along qy.
    """
    z_s = np.asarray(z_s, float)
    nq, Ny = C_up.shape
    out = np.zeros((len(z_s), Ny), complex)
    for j in range(Ny):
        ph = kz_minus_k(qx_up**2 + qy[j] ** 2, lam)
        M = np.exp(1j * np.outer(z_s - z_exit, ph)) * np.exp(2j * np.pi * qx_up * x_ref)[None, :]
        out[:, j] = M @ C_up[:, j]
    # out[:, j] is the coefficient of exp(2 pi i qy_j y) (absolute y); synthesise
    # on the grid y_n = y0 + n dy
    out = out * np.exp(2j * np.pi * qy * y0)[None, :]
    return np.fft.ifft(out, axis=1) * Ny


# ---------------------------------------------------------------------------
# virtual detector line (horizontal plane x = x_det above the incident beam)
# ---------------------------------------------------------------------------

def kz_of_q(q, lam):
    """kz = 2 pi sqrt(1/lambda^2 - q^2) [rad/A] for a vacuum component (qx = q)."""
    return 2.0 * np.pi * np.sqrt(1.0 / lam**2 - np.asarray(q, float) ** 2)


def _fourier_z(f_z, z, kappa):
    dz = z[1] - z[0]
    F = np.empty(len(kappa), complex)
    for s in range(0, len(kappa), 256):
        M = np.exp(-1j * np.outer(kappa[s:s + 256], z))
        F[s:s + 256] = (M @ f_z) * dz
    return F


def updown(G1, G2, phi1, phi2):
    """Up- and down-going amplitudes from two detector lines.

    G_j = U exp(i phi_j) + D exp(-i phi_j) with phi_j = K_x x_j (DERIVED_HERE):
      U = (G2 e^{i phi2} - G1 e^{i phi1}) / (e^{2 i phi2} - e^{2 i phi1}),
      D = (G2 e^{-i phi2} - G1 e^{-i phi1}) / (e^{-2 i phi2} - e^{-2 i phi1}).
    The denominator has modulus 2 |sin(K_x (x2 - x1))|; the line spacing is chosen
    so that K_x (x2 - x1) < pi for every angle of interest."""
    e1, e2 = np.exp(1j * phi1), np.exp(1j * phi2)
    U = (G2 * e2 - G1 * e1) / (e2**2 - e1**2)
    D = (G2 / e2 - G1 / e1) / (1 / e2**2 - 1 / e1**2)
    return U, D


def vdp_reflectivity(f1, f2, z, q, lam, x1, x2, x_ref, A_in_neg):
    """Specular reflection coefficient from the two-line virtual-detector record.

    f1, f2: records of the y-averaged (ky = 0) wave on the lines x = x1, x2 at the
        planes z (uniform spacing; the records vanish at both ends).
    q: normal spatial frequencies (cycles/A, > 0) at which r is wanted.
    A_in_neg: incident spectral DENSITY A(-q) (= Lx * a(-q) for grid coefficients).

    For the vacuum field psi(x, z) = int dq [B(q) e^{2 pi i q x} + D(q) e^{-2 pi i q x}]
    exp(i kappa(q) z), kappa = kz - k (B up-going, D down-going), the Fourier integral
    F_j(kappa) = int f_j(z) exp(-i kappa z) dz gives G_j = F_j (2 pi q / kz)
    = B e^{2 pi i q x_j} + D e^{-2 pi i q x_j}; B follows from two lines (updown), and
    r(q; x_ref) = B(q) / A(-q) * exp(4 pi i q x_ref)   (DERIVED_HERE, docs/08 app. A).
    Returns r, the down-going amplitude relative to the incident, D/A(-q), and the
    single-line estimate (line 1 alone, assuming D = 0) for diagnostics.
    """
    q = np.asarray(q, float)
    z = np.asarray(z, float)
    dz = z[1] - z[0]
    if not np.allclose(np.diff(z), dz, rtol=1e-9, atol=1e-9):
        raise ValueError("virtual-detector planes must be uniformly spaced")
    kz = kz_of_q(q, lam)
    kappa = kz - 2.0 * np.pi / lam
    jac = 2.0 * np.pi * q / kz
    G1 = _fourier_z(f1, z, kappa) * jac
    G2 = _fourier_z(f2, z, kappa) * jac
    B, D = updown(G1, G2, 2 * np.pi * q * x1, 2 * np.pi * q * x2)
    ref = np.exp(4j * np.pi * q * x_ref)
    single = G1 * np.exp(-2j * np.pi * q * x1) / A_in_neg * ref
    return B / A_in_neg * ref, D / A_in_neg, single


def vdp_spectrum(rec1, rec2, x1, x2, z, lam, grid, theta_max, qy_max_mrad=None, pad=2,
                 xp=np, min_sin=0.05):
    """Up-going 2D spectrum of the two-line detector record over (kappa, qy).

    rec1, rec2: (n_planes, Ny) records on the lines x1, x2.  For each line
    S_j(kappa, qy) = int dz [(1/Ny) sum_y rec_j exp(-2 pi i qy y)] exp(-i kappa z)
    (FFT with zero padding, phase referred to absolute z).  The up-going part U with
    field U exp(i K_x x) exp(i kappa z + 2 pi i qy y), K_x = sqrt(k^2 - (k + kappa)^2
    - (2 pi qy)^2), follows from updown(); components with |sin(K_x (x2 - x1))| <
    min_sin (exit angles within about a milliradian of the surface) are set to zero.
    Returned restricted to the total angle arccos(1 + kappa/k) <= theta_max and to
    |qy| lambda <= qy_max: spec_kappa (rad/A, increasing), spec_qy (cycles/A),
    spectrum = U (complex64, field amplitude referred to x = 0), spec_z0_A.
    The record holds kappa < 0 only (one-sided band; positive FFT frequencies are
    mapped to their negative aliases).  rec may live on the GPU (xp = cupy)."""
    n, Ny = rec1.shape
    dz = float(z[1] - z[0])
    npad = int(2 ** np.ceil(np.log2(pad * n)))
    cols = np.arange(Ny)
    if qy_max_mrad is not None:
        cols = np.nonzero(np.abs(grid.qy) * lam <= qy_max_mrad * 1e-3)[0]
    kap = 2.0 * np.pi * np.fft.fftfreq(npad, dz)
    period = 2.0 * np.pi / dz
    kap = np.where(kap > 0, kap - period, kap)
    k = 2.0 * np.pi / lam
    kap_min = -k * (1.0 - np.cos(theta_max))
    sel = np.nonzero((kap <= 0) & (kap >= kap_min))[0]
    order = sel[np.argsort(kap[sel])]
    S = []
    for rec in (rec1, rec2):
        Sy = xp.fft.fft(rec, axis=1)[:, xp.asarray(cols)] / Ny
        Sz = xp.fft.fft(Sy, n=npad, axis=0) * dz
        Ssel = Sz[xp.asarray(order)] * xp.asarray(np.exp(-1j * kap[order] * z[0]))[:, None]
        S.append(np.asarray(Ssel.get() if hasattr(Ssel, "get") else Ssel))
        del Sy, Sz, Ssel
    qy = grid.qy[cols]
    Kx2 = k**2 - (k + kap[order])[:, None] ** 2 - (2 * np.pi * qy)[None, :] ** 2
    Kx = np.sqrt(np.clip(Kx2, 0, None))
    U, D = updown(S[0], S[1], Kx * x1, Kx * x2)
    bad = (Kx2 <= 0) | (np.abs(np.sin(Kx * (x2 - x1))) < min_sin)
    U[bad] = 0.0
    D[bad] = 0.0
    return dict(spec_kappa=kap[order], spec_qy=qy, spec_z0_A=float(z[0]),
                spectrum=U.astype(np.complex64),
                spectrum_down_to_up_power=float(np.sum(np.abs(D) ** 2) / max(np.sum(np.abs(U) ** 2), 1e-300)))


def vdp_pattern(spec, lam, bin_mrad, theta_max_mrad):
    """Reflected intensity map |S|^2 binned in the normal exit angle theta_x
    (bin width bin_mrad up to theta_max_mrad) for every stored qy column: the RHEED
    pattern (rods on the qy lattice, diffuse intensity between them).  Intensity is
    summed over kappa with weight dkappa/(2 pi)."""
    kap = spec["spec_kappa"]
    qy = spec["spec_qy"]
    S2 = np.abs(spec["spectrum"].astype(np.complex128)) ** 2
    k = 2.0 * np.pi / lam
    Kx2 = k**2 - (k + kap)[:, None] ** 2 - (2 * np.pi * qy)[None, :] ** 2
    thx = np.arcsin(np.sqrt(np.clip(Kx2, 0, None)) / k) * 1e3
    nb = int(round(theta_max_mrad / bin_mrad))
    idx = np.clip((thx / bin_mrad).astype(int), 0, nb)
    dk = kap[1] - kap[0]
    out = np.zeros((nb + 1, len(qy)))
    for j in range(len(qy)):
        out[:, j] = np.bincount(idx[:, j], weights=S2[:, j] * (Kx2[:, j] > 0), minlength=nb + 1)
    return (out[:nb] * dk / (2 * np.pi)).astype(np.float32)


def truncation_bound(f, z, q, lam, A_in_neg, segment_planes=1000):
    """Estimated error of r(q) from stopping the march while the detector record
    still carries a decaying tail (long-lived surface resonances).

    The record beyond the last plane is modelled as successive copies of the last
    segment, each scaled by rho = rms(last segment)/rms(previous segment) (geometric
    continuation, rho < 1).  The missing Fourier integral is then
    F_last(kappa) rho/(1 - rho); converted to r units with the same Jacobian and
    incident density as vdp_reflectivity.  Segment length min(segment_planes, n/4).
    Returns (bound array, rho).  A non-decaying tail (rho >= 0.98) gives 50 F_last.
    This is an estimate, validated on the smoke validation (docs/08 section 3.3)."""
    f = np.asarray(f)
    z = np.asarray(z, float)
    n = len(f)
    seg = max(2, min(int(segment_planes), n // 4))
    last, prev = f[n - seg:], f[n - 2 * seg: n - seg]
    rho = float(np.sqrt(np.mean(np.abs(last) ** 2) / max(np.mean(np.abs(prev) ** 2), 1e-300)))
    kz = kz_of_q(q, lam)
    kappa = kz - 2.0 * np.pi / lam
    F_last = _fourier_z(last, z[n - seg:], kappa)
    fac = rho / (1.0 - rho) if rho < 0.98 else 50.0
    return np.abs(F_last) * fac * (2.0 * np.pi * np.asarray(q) / kz) / np.abs(A_in_neg), rho


def vdp_angle_resolved(rec1, rec2, x1, x2, z, theta, lam, grid, cols, A_in_neg, xp=np):
    """Exact plane-wave response rho(theta, qy) of a structure that is uniform along
    the beam, from the two-line detector records (n_planes, Ny) (DERIVED_HERE,
    docs/08 appendix A13).

    kappa is conserved, so incidence at angle theta (kappa_theta) excites only the
    outgoing components at the same kappa.  For every qy column the records are
    Fourier transformed at exactly kappa_theta, separated into up/down parts with
    K_x(kappa_theta, qy), and normalised with the Jacobian and density of the
    INCIDENT component: rho = U (2 pi q / kz) / A(-q).  The reflected field at the
    surface plane is then r(y; theta) = sum_qy rho(theta, qy) exp(2 pi i qy y).
    Returns rho as a (n_theta, n_cols) complex array."""
    theta = np.asarray(theta, float)
    q = np.sin(theta) / lam
    kz = kz_of_q(q, lam)
    kap = kz - 2.0 * np.pi / lam
    dz = float(z[1] - z[0])
    k = 2.0 * np.pi / lam
    Ny = rec1.shape[1]
    cg = xp.asarray(cols)
    E = xp.asarray(np.exp(-1j * np.outer(kap, np.asarray(z, float))) * dz)
    G = []
    for rec in (rec1, rec2):
        Sy = xp.fft.fft(rec, axis=1)[:, cg] / Ny
        Gj = E @ Sy
        G.append(np.asarray(Gj.get() if hasattr(Gj, "get") else Gj))
    qy = grid.qy[cols]
    Kx = np.sqrt(np.clip(k**2 - (k + kap)[:, None] ** 2 - (2 * np.pi * qy)[None, :] ** 2, 0, None))
    U, _ = updown(G[0], G[1], Kx * x1, Kx * x2)
    U[Kx == 0] = 0.0
    return U * (2.0 * np.pi * q / kz / A_in_neg)[:, None]
