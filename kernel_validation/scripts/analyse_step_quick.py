"""Image formation, hologram and reconstruction for the quick step simulation (outputs/step_quick.npz).

Imaging (DERIVED_HERE): the vacuum part of the exit wave (G_y = 0 rod) is back-propagated in free space to
the plane x = x_step (objective focused on the step), an objective aperture of semi-angle ALPHA around the
specular direction is applied, and the carrier exp(+i K sin(theta) (z - z_s)) is removed. A ray reflected at
surface point x_hit appears in that plane at z = z_s + theta (x_step - x_hit), so the surface coordinate is
s = x_hit - x_step = -(z - z_s)/theta and the object-referred image coordinate along the beam is xi = -(z - z_s)
(foreshortened by sin theta).
Hologram (ASSUMPTION values; PROJECT_INPUT items 4-6, 16 are MISSING): vacuum plane-wave reference of the
incident amplitude, fringe period 4 px at 20 deg, coherence mu = 0.35, Gaussian MTF sigma 0.7 px, N0 = 500
e/px, pixel 0.5 nm object-referred, straight step (uniform along eta). Reconstruction: sideband method with
an empty-hologram reference (refl_holo.reconstruct).
"""
import sys, json, pathlib, types
import numpy as np

HERE = pathlib.Path(__file__).resolve().parents[1]
ALPHA = 1.0e-3            # objective-aperture semi-angle (rad), ASSUMPTION (PROJECT_INPUT 4)
PIX = 5.0                 # A, object-referred image pixel, ASSUMPTION (PROJECT_INPUT 5)


def object_wave(d, prof):
    z, zs, th, lam = d["z"], float(d["zs"]), float(d["theta"]), float(d["lam"])
    K = 2 * np.pi / lam; k0 = K * np.sin(th); dz = float(d["dz"])
    D = float(d["L"]) - float(d["x_step"])
    v = np.where(z > zs + 5.0, prof, 0)
    # zero-pad below the grid: the virtual image of the surface downstream of x_step lies at z < z_s,
    # down to z_s - theta (L - x_step); without padding it wraps through the periodic z boundary.
    n_pad = int(np.ceil((th * D + 300.0) / dz))
    v = np.concatenate([np.zeros(n_pad, complex), v]); z = np.concatenate([z[0] - dz * np.arange(n_pad, 0, -1), z])
    kz = 2 * np.pi * np.fft.fftfreq(len(z), dz)
    F = np.fft.fft(v) * np.exp(1j * kz ** 2 * D / (2 * K))          # back-propagate by D in vacuum
    F *= np.abs(kz - k0) < K * ALPHA                                  # objective aperture around specular
    psi = np.fft.ifft(F)
    o = psi * np.exp(-1j * k0 * (z - zs)) / (float(d["a_inc"]) * np.exp(-1j * k0 ** 2 * float(d["x_step"]) / (2 * K)))
    s = -(z - zs) / th
    return s, o


def main():
    d = np.load(HERE / "outputs" / "step_quick.npz")
    th, lam, h = float(d["theta"]), float(d["lam"]), float(d["step_height"])
    K = 2 * np.pi / lam
    s, of = object_wave(d, d["prof_flat"]); _, os_ = object_wave(d, d["prof_step"])
    dphi_inf = np.angle(np.exp(1j * 2 * K * np.sin(th) * h))
    illum = (s > -float(d["x_step"]) + 2000) & (s < float(d["x_end"]) - float(d["x_step"]))
    ratio = os_ / of
    up = illum & (s < -3000); dn = illum & (s > 0)
    print(f"exact asymptote dphi_inf = 2 K sin(theta) h mod 2pi = {dphi_inf:+.4f} rad")
    print(f"causality check, upstream of step: max|ratio-1| = {np.abs(ratio[up]-1).max():.2e}")
    for s0 in (2000, 5000, 10000, 15000, 20000, 24000):
        m = dn & (np.abs(s - s0) < 500)
        if m.any():
            rr = np.mean(ratio[m])
            print(f"  s = {s0/1e4:.1f} um downstream: |ratio| = {abs(rr):.3f}, arg ratio = {np.angle(rr):+.3f} rad,"
                  f" |o_flat|^2 = {np.mean(np.abs(of[m])**2):.3f}")
    # resample object waves onto the image grid (xi = s sin(theta)), straight step -> uniform along eta
    xi_all = s * np.sin(th)
    xi = np.arange(xi_all[illum].min(), xi_all[illum].max(), PIX)
    o_img = np.interp(xi, xi_all[::-1], os_[::-1].real) + 1j * np.interp(xi, xi_all[::-1], os_[::-1].imag)
    of_img = np.interp(xi, xi_all[::-1], of[::-1].real) + 1j * np.interp(xi, xi_all[::-1], of[::-1].imag)
    n = 1 << int(np.ceil(np.log2(len(xi))))
    pad = n - len(xi); o2 = np.pad(o_img, (0, pad), mode="edge"); f2 = np.pad(of_img, (0, pad), mode="edge")
    O = np.tile(o2[None, :], (n, 1)); OF = np.tile(f2[None, :], (n, 1))       # rows eta, cols xi
    sys.path.insert(0, str(HERE / "task1_euv_ptycho_kinematic_reh"))           # refl_holo.py (hologram + reconstruction)
    import refl_holo as rh
    G = types.SimpleNamespace(n=n)
    H, H0, info = rh.make_hologram(G, O, carrier=(0.0, 0.25), carrier_angle_deg=20.0, mu=0.35, N0=500.0,
                                   mtf_sigma=0.7, dist_amp=0.0, seed=3)
    psi, _ = rh.reconstruct(H, H0, info)
    Hf, H0f, infof = rh.make_hologram(G, OF, carrier=(0.0, 0.25), carrier_angle_deg=20.0, mu=0.35, N0=500.0,
                                      mtf_sigma=0.7, dist_amp=0.0, seed=4)
    psif, _ = rh.reconstruct(Hf, H0f, infof)
    rows = slice(n // 4, 3 * n // 4)
    rec = psi[rows, :len(xi)].mean(axis=0); recf = psif[rows, :len(xi)].mean(axis=0)
    sx = xi / np.sin(th)
    np.savez(HERE / "outputs" / "step_quick_analysis.npz", s=s, o_flat=of, o_step=os_, ratio=ratio, illum=illum,
             dphi_inf=dphi_inf, xi=xi, s_img=sx, o_img=o_img, of_img=of_img, H=H[:, :len(xi)], rec=rec, recf=recf,
             rec_map=psi[:, :len(xi)], params=json.dumps(dict(ALPHA=ALPHA, PIX=PIX, mu=0.35, N0=500, carrier_px=4,
             carrier_deg=20, mtf_sigma_px=0.7)))
    m = np.abs(o_img) > 0.2
    err = np.angle(rec[m] * np.conj(o_img[m])); err -= np.angle(np.mean(np.exp(1j * err)))
    print(f"hologram: {n}x{n} px, reconstructed phase vs true object phase: rms {np.sqrt(np.mean(err**2)):.3f} rad")
    print("saved outputs/step_quick_analysis.npz")


if __name__ == "__main__":
    main()
