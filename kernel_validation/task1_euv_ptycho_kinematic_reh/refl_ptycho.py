"""
Reflection-geometry ptychography: forward model + reconstruction (SIMULATED DATA ONLY).

Geometry (sample frame): surface z=0, plane of incidence = xz.
  incident  k_in  = k ( sin t, 0, -cos t )          t = angle of incidence from the surface normal
  specular  e3    = ( sin t, 0,  cos t )            detector normal, detector at distance L
  detector  e1    = ( cos t, 0, -sin t ),  e2 = (0,1,0)
Exit-surface field (2D / thin-surface approximation):  psi_s(x,y) = P_s(x,y) O(x,y)
  O(x,y) = r(x,y) exp(i 2 k h(x,y) cos t)   (local reflectivity x height phase)
Far field at detector pixel (X,Y):  Psi(X,Y) = FT[psi_s](f_x, f_y)
  f_x = [ (X cos t + L sin t)/R - sin t ] / lam ,  f_y = Y/(R lam),  R = sqrt(X^2+Y^2+L^2)
  ("tilted-plane" mapping; paraxial limit f_x ~ X cos t/(lam L) -> foreshortening only)
"""
import numpy as np
from numpy.fft import fft2, ifft2, fftshift, ifftshift
from scipy.ndimage import map_coordinates

# ---------------- geometry ----------------
class Geometry:
    def __init__(self, lam=13.5e-9, theta_deg=70.0, L=30e-3, p=125e-6, N=128):
        self.lam, self.L, self.p, self.N = lam, L, p, N
        self.theta = np.deg2rad(theta_deg)
        self.d = lam * L / (N * p)              # reconstruction pixel (surface frame, isotropic)
        j = (np.arange(N) - N // 2) * p
        self.Y, self.X = np.meshgrid(j, j, indexing="ij")

    def det_to_f(self, X, Y, theta=None):
        t = self.theta if theta is None else theta
        R = np.sqrt(X**2 + Y**2 + self.L**2)
        fx = ((X * np.cos(t) + self.L * np.sin(t)) / R - np.sin(t)) / self.lam
        fy = Y / (R * self.lam)
        return fx, fy

    def f_to_det(self, fx, fy, theta=None):
        """inverse tilted-plane mapping; returns X, Y and validity mask"""
        t = self.theta if theta is None else theta
        ax = self.lam * fx + np.sin(t); ay = self.lam * fy
        s = 1 - ax**2 - ay**2
        ok = s > 0
        az = np.sqrt(np.clip(s, 0, None))
        a1 = ax * np.cos(t) - az * np.sin(t)     # alpha . e1
        a3 = ax * np.sin(t) + az * np.cos(t)     # alpha . e3
        ok &= (a3 > 1e-6) & (az > 0)
        X = self.L * a1 / np.where(ok, a3, 1); Y = self.L * ay / np.where(ok, a3, 1)
        return X, Y, ok

    def jacobian(self, theta=None, h=1e-7):
        fx1, fy1 = self.det_to_f(self.X + h, self.Y, theta); fx0, fy0 = self.det_to_f(self.X - h, self.Y, theta)
        fx2, fy2 = self.det_to_f(self.X, self.Y + h, theta); fx3, fy3 = self.det_to_f(self.X, self.Y - h, theta)
        J = np.abs((fx1 - fx0) * (fy2 - fy3) - (fx2 - fx3) * (fy1 - fy0)) / (4 * h * h)
        return J

    def recon_freqs(self, bx=1):
        """uniform surface-frequency grid of an (N x N/bx) window with pixels (d, bx*d)"""
        n, nx = self.N, self.N // bx
        fy = (np.arange(n) - n // 2) / (n * self.d)
        fx = (np.arange(nx) - nx // 2) / (nx * bx * self.d)
        FY, FX = np.meshgrid(fy, fx, indexing="ij")
        return FX, FY

# ---------------- probe on the tilted surface (exact angular spectrum) ----------------
def surface_probe(g, a_px=14.0, zf=5e-6, Nb=256, flat=False, trefoil=0.6):
    """Beam = soft circular aperture (radius a_px*d) with spherical (defocus) phase, defined in the
    beam-transverse plane through the sample centre. Evaluated on the tilted surface: for surface
    column x, u = x cos t (in-plane transverse), w = x sin t (propagation distance)."""
    N, d, t, lam = g.N, g.d, g.theta, g.lam
    du, dv = d * np.cos(t), d
    u = (np.arange(Nb) - Nb // 2) * du; v = (np.arange(Nb) - Nb // 2) * dv
    V, U = np.meshgrid(v, u, indexing="ij")
    r = np.sqrt(U**2 + V**2); a = a_px * d
    Pb = np.exp(-(r / a) ** 8).astype(complex)
    if not flat:
        Pb *= np.exp(1j * np.pi * r**2 / (lam * zf)) * np.exp(1j * trefoil * np.cos(3 * np.arctan2(V, U)) * (r / a) ** 3)
    k = 2 * np.pi / lam
    ku = 2 * np.pi * np.fft.fftfreq(Nb, du); kv = 2 * np.pi * np.fft.fftfreq(Nb, dv)
    KV, KU = np.meshgrid(kv, ku, indexing="ij")
    kz2 = k**2 - KU**2 - KV**2
    kw = np.where(kz2 > 0, np.sqrt(np.clip(kz2, 0, None)) - k, 0.0)
    A = fft2(Pb) * (kz2 > 0)
    Ps = np.zeros((N, N), complex)
    xs = (np.arange(N) - N // 2) * d
    for ix, x in enumerate(xs):
        w = x * np.sin(t)
        field = ifft2(A * np.exp(1j * kw * w))
        iu = Nb // 2 + (ix - N // 2)              # u = x cos t lands exactly on beam grid column
        Ps[:, ix] = field[Nb // 2 - N // 2: Nb // 2 + N // 2, iu]
    return Ps

# ---------------- test surface ----------------
def make_surface(My, Mx, g, ss=4, seed=1):
    rng = np.random.default_rng(seed)
    d = g.d
    yy, xx = np.meshgrid((np.arange(My * ss) + 0.5) / ss, (np.arange(Mx * ss) + 0.5) / ss, indexing="ij")
    feat = np.zeros_like(xx)
    # Siemens star (centre px), 36 spokes
    cy, cx, R = My * 0.30, Mx * 0.30, 42
    rr = np.hypot(yy - cy, xx - cx); ph = np.arctan2(yy - cy, xx - cx)
    feat[(rr < R) & (np.cos(18 * ph) > 0)] = 1
    # gratings: lines parallel to y (modulated along x) and parallel to x (modulated along y)
    for k, pitch_nm in enumerate([300, 200, 140]):
        P = pitch_nm * 1e-9 / d
        y0 = My * 0.62 + k * 0; x0 = Mx * 0.12 + k * 0.17 * Mx
        m = (yy > y0) & (yy < y0 + 30) & (xx > x0) & (xx < x0 + 0.13 * Mx)
        feat[m & (np.mod(xx - x0, P) < P / 2)] = 1
        y1 = My * 0.12 + k * 0.17 * My; x1 = Mx * 0.62
        m = (xx > x1) & (xx < x1 + 30) & (yy > y1) & (yy < y1 + 0.13 * My)
        feat[m & (np.mod(yy - y1, P) < P / 2)] = 1
    # ring
    rr2 = np.hypot(yy - My * 0.72, xx - Mx * 0.72)
    feat[(rr2 > 18) & (rr2 < 26)] = 1
    def down(a): return a.reshape(My, ss, Mx, ss).mean((1, 3))
    feat = down(feat)
    # smooth roughness (rms 0.4 nm) on the substrate
    nz = rng.standard_normal((My, Mx))
    fy = np.fft.fftfreq(My)[:, None]; fx = np.fft.fftfreq(Mx)[None, :]
    rough = np.real(ifft2(fft2(nz) * np.exp(-(fx**2 + fy**2) / (2 * 0.02**2))))
    rough *= 0.4e-9 / rough.std()
    h = 4e-9 * feat + rough                                  # height map [m]
    r = (0.35 * (1 - feat) + 0.60 * feat) * np.exp(1j * 0.8 * feat)   # material reflectivity
    k = 2 * np.pi / g.lam
    O = r * np.exp(1j * 2 * k * h * np.cos(g.theta))
    return O.astype(np.complex64), h, feat

# ---------------- forward model ----------------
def simulate(O, Ps, pos, g, counts=5e6, pad=4, seed=0, return_clean=False):
    N = g.N; Np = pad * N
    fx, fy = g.det_to_f(g.X, g.Y)
    J = g.jacobian(); J = J / J[N // 2, N // 2]
    cy = fy * Np * g.d + Np // 2; cx = fx * Np * g.d + Np // 2   # fractional indices on padded FFT grid
    rng = np.random.default_rng(seed)
    data, clean = [], []
    for (y0, x0) in pos:
        psi = Ps * O[y0:y0 + N, x0:x0 + N]
        big = np.zeros((Np, Np), complex); s = (Np - N) // 2
        big[s:s + N, s:s + N] = psi
        F = fftshift(fft2(ifftshift(big)))
        Fi = map_coordinates(F.real, [cy, cx], order=3) + 1j * map_coordinates(F.imag, [cy, cx], order=3)
        clean.append(np.abs(Fi) ** 2 * J)
    clean = np.array(clean)
    scale = counts / clean.sum((1, 2)).mean()
    clean *= scale
    data = rng.poisson(clean).astype(np.float32)
    return (data, clean) if return_clean else data

# ---------------- data -> reconstruction grid (tilted-plane correction) ----------------
def resample(data, g, theta=None, mode="tpc", bx=1, order=3):
    """Map detector intensities onto the uniform surface-frequency grid of the reconstruction.
    mode='tpc'     : exact inverse tilted-plane mapping with assumed angle theta
    mode='linear'  : paraxial anamorphic mapping X = lam L fx / cos t, Y = lam L fy (no curvature)"""
    t = g.theta if theta is None else theta
    FX, FY = g.recon_freqs(bx)
    if mode == "tpc":
        X, Y, ok = g.f_to_det(FX, FY, t)
        J = g.jacobian(t); J = J / J[g.N // 2, g.N // 2]
    else:
        X = g.lam * g.L * FX / np.cos(t); Y = g.lam * g.L * FY; ok = np.ones_like(X, bool)
        J = np.ones((g.N, g.N))
    J = np.ones_like(FX) if J is None else J
    jx = X / g.p + g.N // 2; jy = Y / g.p + g.N // 2
    ok &= (jx >= 0) & (jx <= g.N - 1) & (jy >= 0) & (jy <= g.N - 1)
    out = np.empty((len(data),) + FX.shape, np.float32)
    for i, I in enumerate(data):
        Ic = np.clip(map_coordinates(I / J, [jy, jx], order=order), 0, None)
        out[i] = np.where(ok, Ic, 0)
    return out, ok

def coverage_mask(shape, g, theta=None, bx=1):
    """which surface frequencies (grid of pixel (d, bx*d), unshifted FFT order) are measured"""
    t = g.theta if theta is None else theta
    n0, n1 = shape
    FY, FX = np.meshgrid(np.fft.fftfreq(n0, g.d), np.fft.fftfreq(n1, bx * g.d), indexing="ij")
    X, Y, ok = g.f_to_det(FX, FY, t)
    half = (g.N // 2) * g.p
    return ok & (np.abs(X) <= half) & (np.abs(Y) <= half)

# ---------------- rPIE / ePIE ----------------
def ptycho_recon(I, mask, pos, shapeO, P0, n_iter=150, alpha=0.15, beta=0.15,
                 probe_start=5, seed=0, O0=None, log_every=1):
    """rPIE (Maiden, Johnson & Li 2017). alpha=beta=1 reproduces ePIE (Maiden & Rodenburg 2009).
    Fourier-modulus constraint applied only where data exist (mask); unmeasured frequencies float."""
    rng = np.random.default_rng(seed)
    Ny, Nx = P0.shape
    O = np.ones(shapeO, np.complex64) if O0 is None else O0.astype(np.complex64).copy()
    P = P0.astype(np.complex64).copy()
    A = np.sqrt(I).astype(np.float32)
    msk = ifftshift(mask); A = np.array([ifftshift(a) for a in A])    # work in unshifted FFT order
    errs = []
    norm = (A**2)[:, msk].sum()
    for it in range(n_iter):
        e = 0.0
        for j in rng.permutation(len(pos)):
            y0, x0 = pos[j]
            Ov = O[y0:y0 + Ny, x0:x0 + Nx]
            psi = P * Ov
            F = fft2(psi, norm="ortho")
            aF = np.abs(F)
            e += ((aF[msk] - A[j][msk]) ** 2).sum()
            Fn = np.where(msk, A[j] * F / (aF + 1e-12), F)
            dpsi = ifft2(Fn, norm="ortho") - psi
            P2 = np.abs(P) ** 2; O2 = np.abs(Ov) ** 2
            O[y0:y0 + Ny, x0:x0 + Nx] = Ov + np.conj(P) * dpsi / ((1 - alpha) * P2 + alpha * P2.max())
            if it >= probe_start:
                P = P + np.conj(Ov) * dpsi / ((1 - beta) * O2 + beta * O2.max())
        errs.append(e / norm)
    return O, P, np.array(errs)

# ---------------- error metric (removes global complex scale + linear phase ramp ambiguity) -------------
def compare(Ot, Or, roi, up=8):
    """returns NRMSE after optimal gamma*exp(i2pi(a x + b y)) alignment of Or to Ot inside roi."""
    a = np.where(roi, np.conj(Ot) * Or, 0)
    n0, n1 = a.shape
    C = fft2(a, s=(up * n0, up * n1))
    k = np.unravel_index(np.argmax(np.abs(C)), C.shape)
    fy = (k[0] if k[0] < up * n0 / 2 else k[0] - up * n0) / (up * n0)
    fx = (k[1] if k[1] < up * n1 / 2 else k[1] - up * n1) / (up * n1)
    yy, xx = np.mgrid[0:n0, 0:n1]
    Or2 = Or * np.exp(-2j * np.pi * (fy * yy + fx * xx))
    gam = np.vdot(Or2[roi], Ot[roi]) / np.vdot(Or2[roi], Or2[roi])
    Oa = gam * Or2
    err = np.linalg.norm((Ot - Oa)[roi]) / np.linalg.norm(Ot[roi])
    return err, Oa

def lowpass(O, mask_full):
    return ifft2(fft2(O) * mask_full)
