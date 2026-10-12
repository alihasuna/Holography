"""Validation metrics: NCC, phase-scale slope, residuals, registration, edge positions and widths (numpy only).

Runs in: em-holography (also importable in em-abtem).

NCC and slope follow gemicro's reconstruction scoring (score_ncc_vs_ground_truth, phase_scale_slope): NCC is
blind to a wrong phase scale (half the true phase scores 1.0), the least-squares slope of the reconstructed
phase against the truth is not.
"""

import numpy as np


def ncc(a, b, mask):
    """Zero-mean normalised cross-correlation (Pearson r) over mask."""
    x = a[mask] - a[mask].mean()
    y = b[mask] - b[mask].mean()
    d = np.sqrt((x * x).sum() * (y * y).sum())
    return float((x * y).sum() / d) if d > 0 else float("nan")


def slope_fit(rec, truth, mask):
    """rec ≈ slope · truth + intercept (least squares over mask)."""
    s, c = np.polyfit(truth[mask].ravel(), rec[mask].ravel(), 1)
    return float(s), float(c)


def residual(rec, truth, mask):
    """rec - truth with the mean offset over mask removed (both phases are relative)."""
    r = rec - truth
    return r - r[mask].mean()


def registration_shift(a, b):
    """Integer (dx, dy) that maximises the circular cross-correlation of a with b (0, 0 when registered)."""
    A = np.fft.fft2(a - a.mean())
    B = np.fft.fft2(b - b.mean())
    c = np.real(np.fft.ifft2(A * np.conj(B)))
    i = np.unravel_index(int(np.argmax(c)), c.shape)
    return [int(i[0]) if i[0] <= c.shape[0] // 2 else int(i[0] - c.shape[0]),
            int(i[1]) if i[1] <= c.shape[1] // 2 else int(i[1] - c.shape[1])]


def edge_mask(shape, sampling, margin_A):
    m = np.ones(shape, bool)
    nx = int(np.ceil(margin_A / sampling[0]))
    ny = int(np.ceil(margin_A / sampling[1]))
    if nx:
        m[:nx] = m[-nx:] = False
    if ny:
        m[:, :ny] = m[:, -ny:] = False
    return m


def band_limit_real(img, aperture):
    """Apply a (real, origin-centred) aperture to a real map: what the reconstruction aperture does to a phase."""
    return np.real(np.fft.ifft2(np.fft.fft2(img) * aperture))


def crossing(x, profile, level, lo, hi):
    """First x in [lo, hi] where profile crosses level (linear interpolation), or None."""
    sel = np.where((x >= lo) & (x <= hi))[0]
    if len(sel) < 2:
        return None
    p = profile[sel] - level
    s = np.where(np.sign(p[:-1]) * np.sign(p[1:]) <= 0)[0]
    if len(s) == 0:
        return None
    k = sel[s[0]]
    x0, x1, p0, p1 = x[k], x[k + 1], profile[k] - level, profile[k + 1] - level
    return float(x0 if p1 == p0 else x0 + (x1 - x0) * (-p0) / (p1 - p0))


def edge_analysis(x, profile, x_edge_guess, plateau_window, gap):
    """Surface edge of a profile that falls from a crystal plateau (x < edge) to vacuum (x > edge).

    Plateau and vacuum levels are medians over [guess - gap - window, guess - gap] and
    [guess + gap, guess + gap + window]; returns the 50 % crossing and the 10-90 % width."""
    pin = profile[(x >= x_edge_guess - gap - plateau_window) & (x <= x_edge_guess - gap)]
    pout = profile[(x >= x_edge_guess + gap) & (x <= x_edge_guess + gap + plateau_window)]
    if len(pin) < 2 or len(pout) < 2:
        return None
    hi, lo = float(np.median(pin)), float(np.median(pout))
    span = hi - lo
    if abs(span) < 1e-9:
        return None
    a, b = x_edge_guess - gap - plateau_window, x_edge_guess + gap + plateau_window
    x50 = crossing(x, profile, lo + 0.5 * span, a, b)
    x90 = crossing(x, profile, lo + 0.9 * span, a, b)
    x10 = crossing(x, profile, lo + 0.1 * span, a, b)
    width = None if (x10 is None or x90 is None) else abs(x10 - x90)
    return {"plateau": hi, "vacuum": lo, "step": span, "x50_A": x50, "width_10_90_A": width}
