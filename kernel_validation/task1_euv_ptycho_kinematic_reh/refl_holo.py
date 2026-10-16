"""
Off-axis reflection electron holography (REH) in an REM / Bragg-reflection geometry (SIMULATED DATA ONLY).

Surface frame: x = in-surface along the beam azimuth, y = in-surface transverse, z = surface normal.
Image plane (object-referred): xi = x sin(tB) (foreshortened), eta = y.
Kinematic reflected object wave:  o = A(x,y) exp(i phi),   phi = 2 k_eff u_z(x,y) sin(tB + dt)
  -> lattice step h = n d_hkl at exact Bragg (dt=0):  phi = 2 pi n  (phase-invisible)
  -> off-Bragg:  phi_step = 2 pi n + 2 k h cos(tB) dt  (mod 2 pi)
Hologram (biprism):  I = |o + r|^2 blurred by detector MTF, fringe visibility mu (partial coherence),
                     Poisson noise with N0 electrons / pixel.
"""
import numpy as np
from numpy.fft import fft2, ifft2, fftshift, ifftshift

def electron_wavelength(V):
    h, m, e, c = 6.62607015e-34, 9.1093837015e-31, 1.602176634e-19, 2.99792458e8
    return h / np.sqrt(2 * m * e * V * (1 + e * V / (2 * m * c**2)))

class REHGeometry:
    def __init__(self, V=200e3, a=0.5431e-9, hkl=(4, 4, 4), n=1024, pix=0.25e-9):
        self.lam = electron_wavelength(V); self.k = 2 * np.pi / self.lam
        self.d_hkl = a / np.sqrt(sum(i * i for i in hkl))
        self.tB = np.arcsin(self.lam / (2 * self.d_hkl))
        self.n, self.pix = n, pix                       # image (object-referred) pixel along xi and eta
        self.d111 = a / np.sqrt(3)
        e = (np.arange(n) - n // 2) * pix
        self.ETA, self.XI = np.meshgrid(e, e, indexing="ij")   # rows = eta (=y), cols = xi
        self.X = self.XI / np.sin(self.tB); self.Y = self.ETA  # surface coordinates of each image pixel

def surface_model(G, seed=0):
    """height / displacement field u_z(x,y) [m] and reflected amplitude A(x,y)."""
    rng = np.random.default_rng(seed)
    X, Y = G.X, G.Y
    # monatomic (d111) steps running roughly along y, meandering; descending staircase along +x
    uz = np.zeros_like(X); A = np.ones_like(X)
    xs = np.linspace(-6e-6, 6e-6, 4)
    for x0 in xs:
        mx = x0 + 0.6e-6 * np.sin(2 * np.pi * Y / 180e-9 + rng.uniform(0, 6.28))
        uz -= G.d111 * (X > mx)
        A *= 1 - 0.5 * np.exp(-((X - mx) / 0.25e-6) ** 2)          # step contrast (amplitude)
    # emergent screw-type dislocation with surface-normal Burgers component b_z = d111 at (x,y)=(2e-6, -40 nm)
    xc, yc = 1.0e-6, -40e-9
    ang = np.arctan2((Y - yc), (X - xc) * np.sin(G.tB))           # angle in (approximately isotropic) image metric
    uz += G.d111 * (ang + np.pi) / (2 * np.pi) * 1.0
    uz -= G.d111 * ((X > xc) & (Y > yc)) * 0                      # (helicoid already carries the terminating step)
    A *= 1 - 0.7 * np.exp(-(((X - xc) * np.sin(G.tB)) ** 2 + (Y - yc) ** 2) / (4e-9) ** 2)
    # buried dislocation line along x at y = +60 nm, depth D: illustrative antisymmetric surface undulation
    D, amp = 15e-9, 8e-12
    yy = Y - 60e-9
    und = amp * 2 * yy * D / (yy**2 + D**2)
    uz += und
    A *= 1 - 0.15 * np.exp(-(yy / D) ** 2)                        # strain (diffraction) contrast
    return uz, A, und

def object_wave(G, uz, A, dtheta=0.0):
    phi = 2 * G.k * uz * np.sin(G.tB + dtheta)
    return A * np.exp(1j * phi), phi

def make_hologram(G, o, carrier=(0.0, 0.25), carrier_angle_deg=20.0, mu=0.35, N0=200.0,
                  mtf_sigma=0.7, dist_amp=0.6, seed=0, noise=True):
    """carrier given as fringe frequency in cycles/pixel (|q_c|); returns hologram and ideal sideband."""
    n = G.n
    qc = carrier[1]; th = np.deg2rad(carrier_angle_deg)
    qy, qx = qc * np.cos(th), qc * np.sin(th)
    qy, qx = np.round(qy * n) / n, np.round(qx * n) / n            # integer carrier -> no residual ramp
    jj, ii = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    # reference: tilted plane wave with slow biprism / lens distortion phase
    dist = dist_amp * ((ii - n / 2) ** 2 - 0.5 * (jj - n / 2) ** 2) / (n / 2) ** 2
    r = np.exp(2j * np.pi * (qy * jj + qx * ii) + 1j * dist)
    I = np.abs(o) ** 2 + 1 + 2 * mu * np.real(o * np.conj(r))
    I0 = 2 + 2 * mu * np.real(np.conj(r))                          # empty (reference) hologram, o = 1
    # detector MTF (Gaussian)
    f = np.fft.fftfreq(n); FY, FX = np.meshgrid(f, f, indexing="ij")
    MTF = np.exp(-2 * (np.pi * mtf_sigma) ** 2 * (FX ** 2 + FY ** 2))
    blur = lambda a: np.real(ifft2(fft2(a) * MTF))
    I, I0 = blur(I), blur(I0)
    rng = np.random.default_rng(seed)
    scale = N0 / 2.0                                               # mean counts / px ~ N0
    if noise:
        H = rng.poisson(np.clip(I * scale, 0, None)).astype(float)
        H0 = rng.poisson(np.clip(I0 * scale, 0, None)).astype(float)
    else:
        H, H0 = I * scale, I0 * scale
    mtf_c = np.exp(-2 * (np.pi * mtf_sigma) ** 2 * (qx ** 2 + qy ** 2))
    return H, H0, dict(qy=qy, qx=qx, mtf_c=mtf_c)

def reconstruct(H, H0, info, rmask_frac=1/3, edge=0.15):
    """Fourier sideband method (Takeda et al. 1982; Lehmann & Lichte 2002).
    returns complex wave (object / reference-normalised), mask area fraction."""
    n = H.shape[0]
    f = np.fft.fftfreq(n); FY, FX = np.meshgrid(f, f, indexing="ij")
    qc = np.hypot(info['qy'], info['qx']); R = rmask_frac * qc
    rr = np.hypot(FY - (-info['qy']), FX - (-info['qx']))          # sideband carrying  o * conj(r) -> at -q
    w = 1 / (1 + (rr / R) ** 20)                                   # soft (Butterworth) aperture
    def sb(Hh):
        S = fft2(Hh - Hh.mean()) * w
        S = np.roll(S, (int(round(info['qy'] * n)), int(round(info['qx'] * n))), axis=(0, 1))
        return ifft2(S)
    psi = sb(H) / sb(H0)                                           # reference-hologram normalisation
    return psi, w.mean()

def phase_noise_theory(N_res, mu_eff, with_ref=True):
    """sigma_phi = sqrt(2/(mu^2 N)) per resolution element (Lichte & Lehmann); x sqrt2 if reference hologram
    has the same dose (independent noise)."""
    s = np.sqrt(2.0 / (mu_eff ** 2 * N_res))
    return s * (np.sqrt(2) if with_ref else 1.0)
