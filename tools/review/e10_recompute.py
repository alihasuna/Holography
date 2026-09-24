"""E10 review of L9 (docs/agent_reports/L9_microscope_detector.md): independent recomputation of every
detector number L9 derives, written without reusing L9's scripts.

Sections (every number is printed):
  A  inputs quoted from the sources (Paton et al. 2021 = D6, Table 1, p. 5; D6 Eq. (1), p. 3)
  B  independent digitisation of D6 Fig. 8(a),(b) (embedded raster xref 246, p. 7) if the PDF and pymupdf
     are available, else the frozen E10 values (printed as such); validation against the square-pixel
     sinc curves and Table 1; comparison with L9's digitisation (tools/lit/l9/digitise_paton_fig8.out)
  C  functional form of the MTF: D6 fits the edge-spread function with ONE error function (Eq. (1)), so its
     MTF is a Gaussian by construction; Gaussian and stretched-exponential fits; Table-1-only Gaussian
  D  fringe-contrast factor MTF(q_c) versus pixels per fringe
  E  phase-noise factor: derivation and numbers; the alternatives that are NOT correct
  F  Monte Carlo check of sigma_phi = sqrt(2) / (mu sqrt(N DQE(q_c))) with a compound-Poisson counting
     detector whose MTF, NPS and DQE are measured independently (flat fields)
  G  finite Hann sideband mask: effective DQE over the mask (2-D, isotropic D6 curves)
  H  demo processing B29 (minimum empty-hologram visibility 0.5) against the detector MTF, with and without
     the B38 plasmon-loss factor
  I  demo configuration arithmetic (B23, B28): what 8 pixels per fringe requires
  J  asymmetric sideband weighting by the MTF (not removed by division by the empty hologram)
  K  L9's remaining numbers (NNPS, 1/sin theta, magnifications, spans, counters, I3.6)

Run: python tools/review/e10_recompute.py [path/to/Paton2021.pdf]
(pymupdf is needed only for section B; it is not in the project venv.)"""
import math
import os
import sys

import numpy as np

print("E10 recompute, interpreter:", sys.executable, "numpy", np.__version__)

# ------------------------------------------------------------------------------------------------ A
print("\n=== A. Inputs quoted from the sources")
TABLE1_SI_200 = dict(MTF_N=0.01, DQE0=0.80, DQE_halfN=0.17, DQE_N=0.00)   # D6 Table 1, p. 5, 200 keV, Si
print("D6 Table 1 (p. 5), 200 keV, Si, low threshold:", TABLE1_SI_200)
print("D6 Eq. (1) (p. 3): ESF_fit(x) = A/2 (1 + erf((mu - x)/sigma)); MTF = |FT(d ESF_fit/dx)|")
print("  => MTF(w) = exp(-(pi sigma w)^2) exactly (a Gaussian), for every threshold and energy")
PITCH_UM = 55.0                                  # D1, D8
OMEGA_N = 0.5                                    # cycles/pixel (D6 sec. 3: 1/(2 x pitch))
print(f"pitch {PITCH_UM} um; omega_N = {OMEGA_N} cycles/pixel = {1e3 / (2 * PITCH_UM):.3f} cycles/mm")

# L9 digitisation (tools/lit/l9/digitise_paton_fig8.out), for comparison only
L9_W = np.round(np.arange(0.0, 1.0001, 0.05), 2)
L9_MTF_NAVY = [None, 0.983, 0.951, 0.896, 0.823, 0.738, 0.647, 0.554, 0.463, 0.372, 0.297, 0.228, 0.175,
               0.13, 0.094, 0.069, 0.05, 0.035, 0.024, 0.018, 0.014]
L9_DQE_RED = [0.8, 0.748, 0.757, 0.67, 0.613, 0.544, 0.46, 0.377, 0.302, 0.231, 0.171, 0.125, 0.086,
              0.058, 0.037, 0.028, 0.022, None, None, None, None]

# ------------------------------------------------------------------------------------------------ B
print("\n=== B. Independent digitisation of D6 Fig. 8(a),(b)")
PDF = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
    "E10_PATON_PDF",
    "/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/e10/pdf/Paton2021_gla.pdf")

# frozen output of the E10 run of 2026-09-24 (used only if the PDF or pymupdf is missing)
FROZEN = {
    ("a", "square_pixel"): [None, None, None, 0.994, 0.985, 0.976, 0.965, 0.952, 0.936, 0.919, 0.901, 0.881,
                            0.858, 0.835, 0.81, 0.786, 0.759, 0.729, 0.699, 0.669, 0.641],
    ("a", "TH0_58.3keV"): [None, 0.981, 0.953, 0.9, 0.826, 0.741, 0.65, 0.556, 0.464, 0.376, 0.297, 0.23, 0.175,
                           0.13, 0.095, 0.07, 0.048, 0.035, 0.023, 0.017, 0.013],
    ("a", "TH0_117.1keV"): [0.999, 0.997, 0.989, 0.978, 0.96, 0.939, 0.913, 0.882, 0.849, 0.813, 0.773, 0.733,
                            0.692, 0.649, 0.605, 0.566, 0.524, 0.482, 0.441, 0.4, 0.365],
    ("b", "square_pixel"): [0.999, 0.998, 0.994, 0.982, 0.969, 0.95, 0.927, 0.904, 0.875, 0.845, 0.811, 0.774,
                            0.736, 0.699, 0.659, 0.617, 0.576, 0.533, 0.49, 0.448, None],
    ("b", "TH0_12.4keV"): [0.787, 0.748, 0.755, 0.669, 0.612, 0.54, 0.459, 0.376, 0.3, 0.23, 0.168, 0.121,
                           0.082, 0.056, 0.036, 0.026, None, None, None, None, None],
    ("b", "TH0_58.3keV"): [None, 0.61, 0.576, 0.511, 0.432, 0.355, 0.276, 0.204, 0.147, 0.101, 0.065, 0.041,
                           0.03, 0.023, None, None, None, None, None, None, None],
    ("b", "TH0_117.1keV"): [0.025, 0.023, 0.022, 0.022, 0.022, 0.022, 0.022, 0.02, 0.019, 0.017, 0.016, 0.015,
                            0.013, 0.013, 0.013, 0.012, 0.012, 0.01, 0.01, 0.01, None],
}
DENSE = None


def _load_raster(pdf_path):
    import pymupdf
    d = pymupdf.open(pdf_path)
    pix = pymupdf.Pixmap(d, 246)
    A = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
    return A.astype(float)


def _classes(A):
    R, G, B = A[..., 0], A[..., 1], A[..., 2]
    return {"square_pixel": (B > 200) & (R > 70) & (R < 210) & (G > 140) & (G < 235) & (B - R > 40),
            "TH0_117.1keV": (G - R > 60) & (G - B > 50),
            "TH0_12.4keV": (R - G > 60) & (R - B > 30) & (R < 220),
            "TH0_58.3keV": (B - R > 25) & (B - G > 20) & (B < 150)}


def _groups(frac, off, thr=0.3):
    idx = [i for i in range(len(frac)) if frac[i] > thr]
    g = []
    for i in idx:
        if g and i - g[-1][-1] <= 2:
            g[-1].append(i)
        else:
            g.append([i])
    return [float(np.mean(x)) + off for x in g]


def _calibrate(A):
    """Axes from the black spines (x = 0 at the left spine, y = 0 at the bottom spine) jointly with the
    light-grey grid lines (0.2 spacing)."""
    mx, mn = A.max(2), A.min(2)
    dark = (mx - mn < 30) & (mx < 140)
    grey = (mx - mn < 20) & (mx >= 150) & (mx <= 240)
    H, W = mx.shape
    top = H // 2
    cf = dark[:top].mean(0)
    sc = _groups(cf, 0, thr=0.5)
    l_a, r_a, l_b, r_b = sc[:4]
    rf = dark[:top, int(l_a) + 3:int(r_a) - 2].mean(1)
    bottom = float(np.mean([i for i in range(top) if rf[i] > 0.9]))
    grow = [g for g in _groups(grey[:top, int(l_a) + 3:int(r_a) - 2].mean(1), 0) if 80 < g < bottom - 10]
    yfit = np.polyfit(grow + [bottom], [1.0, 0.8, 0.6, 0.4, 0.2][:len(grow)] + [0.0], 1)
    cal = {"bottom": bottom, "grid_rows": grow, "y": yfit}
    for name, (l, r) in {"a": (l_a, r_a), "b": (l_b, r_b)}.items():
        gc = [g for g in _groups(grey[60:int(bottom) - 1, int(l) + 3:int(r) - 2].mean(0), int(l) + 3)
              if l + 20 < g < r - 20][:4]
        xfit = np.polyfit(gc + [l], [0.2, 0.4, 0.6, 0.8, 0.0], 1)
        cal[name] = {"spines": (l, r), "grid_cols": gc, "x": xfit, "x_right_spine": float(np.polyval(xfit, r))}
    return cal


def _trace(A, cal, panel, cname):
    """Follow the class pixels column by column (nearest run to the previous column's run)."""
    m = _classes(A)[cname].copy()
    m[0:125, 770:1005] = False                          # legend box of panel (b)
    l, r = cal[panel]["spines"]
    bot = int(round(cal["bottom"])) + 3
    out, prev, miss = {}, None, 0
    for c in range(int(l) + 2, int(r)):
        ys = np.where(m[50:bot, c])[0] + 50
        if ys.size == 0:
            miss += 1
            continue
        runs = np.split(ys, np.where(np.diff(ys) > 2)[0] + 1)
        cents = [float(np.mean(rr)) for rr in runs]
        lens = [len(rr) for rr in runs]
        if prev is None or miss > 10:
            k = int(np.argmax(lens))
            if lens[k] < 4:
                miss += 1
                continue
        else:
            k = int(np.argmin([abs(cc - prev) for cc in cents]))
            if abs(cents[k] - prev) > 25:
                miss += 1
                continue
        prev, miss = cents[k], 0
        out[float(np.polyval(cal[panel]["x"], c))] = float(np.polyval(cal["y"], cents[k]))
    return out


def _sample(tr, xs, hw=0.006):
    keys = np.array(sorted(tr))
    vals = np.array([tr[k] for k in sorted(tr)])
    res = []
    for x in xs:
        sel = np.abs(keys - x) <= hw
        res.append(round(float(np.median(vals[sel])), 3) if sel.any() else None)
    return res


W21 = [round(0.05 * i, 2) for i in range(21)]
DIG = dict(FROZEN)
source = "FROZEN (E10 run of 2026-09-24; PDF or pymupdf not available here)"
try:
    A = _load_raster(PDF)
    cal = _calibrate(A)
    print("calibration: bottom spine row", cal["bottom"], "grid rows (1.0..0.2)", cal["grid_rows"],
          "y(row) =", np.round(cal["y"], 6))
    for p in ("a", "b"):
        print(f"  panel {p}: spines {cal[p]['spines']}, grid cols {cal[p]['grid_cols']}, x(col) =",
              np.round(cal[p]["x"], 6), f"right spine at x = {cal[p]['x_right_spine']:.4f}")
    DENSE = {}
    for key in FROZEN:
        tr = _trace(A, cal, *key)
        DENSE[key] = tr
        DIG[key] = _sample(tr, W21)
    source = f"digitised now from {PDF}"
except Exception as exc:  # noqa: BLE001 - the fallback is printed
    print("digitisation skipped:", type(exc).__name__, exc)
print("curves:", source)
print("w/w_N:", W21)
for key in FROZEN:
    print(f"  Fig. 8({key[0]}) {key[1]:13s}:", DIG[key])

sinc = lambda w: float(np.sinc(w / 2.0))           # square pixel presampling MTF, w in omega_N units
print("validation against the square-pixel curves (D6 p. 4: MTF = sinc, DQE = sinc^2):")
for w in (0.25, 0.5, 0.75, 0.95, 1.0):
    i = W21.index(w)
    a, b = DIG[("a", "square_pixel")][i], DIG[("b", "square_pixel")][i]
    print(f"  w = {w:.2f}: MTF digitised {a}, sinc {sinc(w):.3f}; DQE digitised {b}, sinc^2 {sinc(w) ** 2:.3f}")
mtf_navy = DIG[("a", "TH0_58.3keV")]
dqe_red = DIG[("b", "TH0_12.4keV")]
print("validation against Table 1: MTF(w_N) digitised", mtf_navy[20], "(Table 0.01);",
      "DQE(0) digitised", dqe_red[0], "(Table 0.80; the curve is noisy below 0.1 w_N);",
      "DQE(0.5 w_N) digitised", dqe_red[10], "(Table 0.17)")
dm = [abs(a - b) for a, b in zip(mtf_navy, L9_MTF_NAVY) if a is not None and b is not None]
dd = [abs(a - b) for a, b in zip(dqe_red, L9_DQE_RED) if a is not None and b is not None]
print(f"E10 vs L9 digitisation: max |diff| MTF (58.3 keV) {max(dm):.3f} over {len(dm)} points; "
      f"DQE (12.4 keV) {max(dd):.3f} over {len(dd)} points (largest at w = 0, the noisy end)")
dd_no0 = [abs(a - b) for a, b in zip(dqe_red[1:], L9_DQE_RED[1:]) if a is not None and b is not None]
print(f"  DQE excluding w = 0: max |diff| {max(dd_no0):.3f}")

# ------------------------------------------------------------------------------------------------ C
print("\n=== C. Functional form of the 200 keV Si MTF")
w = np.array([x for x, v in zip(W21, mtf_navy) if v is not None and 0.05 <= x <= 0.95])
m = np.array([v for x, v in zip(W21, mtf_navy) if v is not None and 0.05 <= x <= 0.95])
# (1) Gaussian, linear least squares on MTF (grid search + refinement), MTF(0) = 1 fixed
g0 = np.linspace(0.40, 0.50, 20001)
sse = [np.sum((m - np.exp(-(w / a) ** 2)) ** 2) for a in g0]
w0_lin = float(g0[int(np.argmin(sse))])
# (2) as L9 (least squares on -ln MTF, through the origin), for comparison, same points > 0.03
sel = m > 0.03
w0_log = float(np.sqrt(np.sum(w[sel] ** 4) / np.sum(-np.log(m[sel]) * w[sel] ** 2)))
# (3) stretched exponential exp(-(w/a)^n), 2 parameters, linear least squares (grid)
best = (1e9, None, None)
for n in np.linspace(1.5, 2.5, 201):
    for a in np.linspace(0.40, 0.50, 401):
        s = np.sum((m - np.exp(-(w / a) ** n)) ** 2)
        if s < best[0]:
            best = (s, a, n)
print(f"Gaussian fit, linear LSQ (0.05-0.95 w_N, {w.size} pts): w0 = {w0_lin:.4f} w_N, rms residual "
      f"{math.sqrt(min(sse) / w.size):.4f}")
print(f"Gaussian fit, L9 method (log LSQ, MTF > 0.03): w0 = {w0_log:.4f} w_N")
print(f"stretched exponential: a = {best[1]:.4f} w_N, n = {best[2]:.3f}, rms residual "
      f"{math.sqrt(best[0] / w.size):.4f} (n = 2 is a Gaussian)")
res = m - np.exp(-(w / w0_lin) ** 2)
print("residuals (digitised - Gaussian, linear fit):", [f"{x:.2f}:{r:+.3f}" for x, r in zip(w, res)])
for name, w0 in (("linear LSQ", w0_lin), ("L9 log LSQ", w0_log)):
    q0 = OMEGA_N * w0                                   # cycles/pixel
    s_psf = 1.0 / (math.sqrt(2.0) * math.pi * q0)       # MTF = exp(-2 pi^2 s^2 q^2)
    s_erf = math.sqrt(2.0) * s_psf                      # D6 Eq. (1): MTF = exp(-(pi sigma q)^2)
    print(f"  {name}: q0 = {q0:.4f} cycles/px; Gaussian PSF s.d. {s_psf:.3f} px = {s_psf * PITCH_UM:.1f} um;"
          f" D6 Eq. (1) erf width sigma = {s_erf:.3f} px = {s_erf * PITCH_UM:.1f} um;"
          f" MTF(w_N) = {math.exp(-(1 / w0) ** 2):.4f}")
# Table-1-only Gaussian: MTF(w) = MTF_N^(w^2), MTF_N in [0.005, 0.015) (rounding of 0.01)
print("Table-1-only Gaussian (D6 Eq. (1) + MTF(w_N) = 0.01, rounding interval [0.005, 0.015)):")
for wq in (0.25, 0.5):
    print(f"  w = {wq}: MTF = {0.01 ** (wq ** 2):.3f} (range {0.005 ** (wq ** 2):.3f} - {0.015 ** (wq ** 2):.3f})")
s_from_table = math.sqrt(math.log(1 / 0.01)) / (math.sqrt(2.0) * math.pi * OMEGA_N)
print(f"  implied Gaussian PSF s.d. from MTF(w_N) = 0.01: {s_from_table:.3f} px "
      f"(range {math.sqrt(math.log(1 / 0.015)) / (math.sqrt(2) * math.pi * OMEGA_N):.3f} - "
      f"{math.sqrt(math.log(1 / 0.005)) / (math.sqrt(2) * math.pi * OMEGA_N):.3f} px)")
g117 = np.array([v for v in DIG[("a", "TH0_117.1keV")][1:]])
w117 = np.array(W21[1:])
a117 = float(np.sqrt(np.sum(w117 ** 4) / np.sum(-np.log(g117) * w117 ** 2)))
print(f"117.1 keV curve, Gaussian log-LSQ: w0 = {a117:.3f} w_N, max |resid| "
      f"{np.max(np.abs(g117 - np.exp(-(w117 / a117) ** 2))):.3f} (also Gaussian by construction)")

# ------------------------------------------------------------------------------------------------ D
print("\n=== D. Fringe-contrast factor MTF(q_c) (p pixels per fringe: w = 2/p in w_N units)")


def interp(curve, x):
    xs = [a for a, v in zip(W21, curve) if v is not None]
    vs = [v for v in curve if v is not None]
    return float(np.interp(x, xs, vs)) if xs[0] <= x <= xs[-1] else float("nan")


if DENSE is not None:
    dn = DENSE[("a", "TH0_58.3keV")]
    kx = np.array(sorted(dn)); kv = np.array([dn[k] for k in sorted(dn)])
    def mtf_dig(x):
        return float(np.interp(x, kx, kv))
    dr = DENSE[("b", "TH0_12.4keV")]
    rx = np.array(sorted(dr)); rv = np.array([dr[k] for k in sorted(dr)])
    def dqe_dig(x):
        sel = np.abs(rx - x) <= 0.02                     # +-0.02 w_N median (the DQE trace is noisy)
        return float(np.median(rv[sel]))
else:
    def mtf_dig(x):
        return interp(mtf_navy, x)
    def dqe_dig(x):
        return interp(dqe_red, x)
MTF_G = lambda x: math.exp(-(x / w0_lin) ** 2)
print(" p  | w/w_N | MTF digitised (58.3 keV curve) | Gaussian fit | Table-1 Gaussian [range] | square-pixel sinc")
for p in (3, 4, 5, 6, 8, 10, 12, 16, 17, 20):
    x = 2.0 / p
    print(f" {p:2d} | {x:.3f} | {mtf_dig(x):.3f} | {MTF_G(x):.3f} | {0.01 ** (x * x):.3f} "
          f"[{0.005 ** (x * x):.3f}, {0.015 ** (x * x):.3f}] | {sinc(x):.3f}")
print("(the 12.4 keV MTF curve lies under the 58.3 keV curve, which is drawn on top; its visible edge reads"
      " 0.28 at 0.5 w_N, i.e. the L9 'mean of the two' 0.288 is biased low by the occlusion)")

# ------------------------------------------------------------------------------------------------ E
print("\n=== E. Phase noise with a detector of given MTF and DQE")
print("""Derivation (DERIVED_HERE). Incident electrons per pixel n(r) = nbar [1 + mu cos(2 pi q_c.r + phi)]
(mu = incident, specimen-plane contrast). Output counts d_j: mean g nbar [1 + mu MTF(q_c) cos(...)],
noise power spectrum NPS(q) (digital, aliasing included). Sideband estimate over M pixels:
c = (1/M) sum_j d_j exp(-2 pi i q_c.r_j):  <c> = g nbar mu MTF(q_c) e^{i phi} / 2,  var(c) = NPS(q_c) / M,
split equally between the two quadratures. Hence
  sigma_phi = sqrt(NPS(q_c) / (2M)) / (g nbar mu MTF(q_c) / 2).
With D6 Eq. (3), DQE(q) = g^2 nbar MTF(q)^2 / NPS(q):
  sigma_phi = sqrt(2) / (mu sqrt(M nbar DQE(q_c))) = sqrt(2) / (mu sqrt(N DQE(q_c))),  N = M nbar incident.
The MTF cancels when mu is the INCIDENT contrast: relative to a DQE = 1 detector at the same dose the factor
is 1/sqrt(DQE(q_c)); it is NOT 1/(MTF sqrt(DQE)). Written with the MEASURED contrast mu_m = mu MTF(q_c)
and the measured counts N_c = g N (what an experimentalist reads off the hologram):
  sigma_phi = sqrt(2) / (mu_m sqrt(N_c)) * sqrt(g NNPS(q_c) / DQE(0)),   NNPS = NPS / NPS(0).""")
print(" p  | DQE(q_c) dig. | 1/sqrt(DQE) | vs ideal square pixel sqrt(sinc^2/DQE) | wrong: 1/MTF | wrong: 1/(MTF sqrt(DQE)) | sqrt(NNPS/DQE0)")
for p in (4, 5, 6, 8, 10, 12, 16):
    x = 2.0 / p
    D = dqe_dig(x)
    M_ = mtf_dig(x)
    nnps = 0.80 * M_ * M_ / D
    print(f" {p:2d} | {D:.3f} | {1 / math.sqrt(D):.2f} | {math.sqrt(sinc(x) ** 2 / D):.2f} | {1 / M_:.2f} | "
          f"{1 / (M_ * math.sqrt(D)):.2f} | {math.sqrt(nnps / 0.80):.3f}")
print(f"Table 1 only, 4 px/fringe: DQE(0.5 w_N) = 0.17 -> 1/sqrt = {1 / math.sqrt(0.17):.3f} "
      f"(rounding interval [0.165, 0.175): {1 / math.sqrt(0.175):.3f} - {1 / math.sqrt(0.165):.3f})")

# ------------------------------------------------------------------------------------------------ F
print("\n=== F. Monte Carlo check of the phase-noise formula (1-D compound-Poisson counting detector)")


def mc(q_c, mu, nbar, Mpix, s_px, pm, n_real, seed, phi0=0.3, flat=False):
    """Electrons Poisson on the continuous line (intensity 1 + mu cos), each makes m counts (P(m) = pm),
    each count displaced by N(0, s_px^2) and binned to its pixel (periodic line). Returns the counts."""
    rng = np.random.default_rng(seed)
    ms = np.arange(1, len(pm) + 1)
    out = np.empty((n_real, Mpix))
    mu_ = 0.0 if flat else mu
    for k in range(n_real):
        ncand = rng.poisson(nbar * Mpix * (1 + mu_))
        x = rng.uniform(0.0, Mpix, ncand)
        keep = rng.uniform(0.0, 1.0, ncand) < (1 + mu_ * np.cos(2 * np.pi * q_c * x + phi0)) / (1 + mu_)
        x = x[keep]
        mult = rng.choice(ms, size=x.size, p=pm)
        xc = np.repeat(x, mult) + s_px * rng.standard_normal(int(mult.sum()))
        out[k] = np.bincount(np.floor(xc).astype(np.int64) % Mpix, minlength=Mpix)
    return out


MPIX, NBAR, MU, SPX = 1024, 20.0, 0.8, 0.95
PM = np.array([0.45, 0.30, 0.15, 0.10])
Em = float(np.sum(np.arange(1, 5) * PM)); Em2 = float(np.sum(np.arange(1, 5) ** 2 * PM))
print(f"detector model: P(m=1..4) = {PM.tolist()}, E[m] = {Em:.3f}, E[m^2] = {Em2:.3f}, "
      f"E[m]^2/E[m^2] = {Em * Em / Em2:.4f}; count displacement s.d. {SPX} px; line of {MPIX} px; "
      f"nbar = {NBAR} e/px; incident contrast mu = {MU}")
flat = mc(0.25, 0.0, NBAR, MPIX, SPX, PM, 3000, seed=11, flat=True)
g_meas = flat.mean() / NBAR
dflat = flat - flat.mean(0)
F = np.fft.fft(dflat, axis=1)
P = (np.abs(F) ** 2).mean(0) / MPIX                      # NPS(q) in counts^2 per pixel
freqs = np.fft.fftfreq(MPIX)
binned = flat.reshape(3000, MPIX // 64, 64).sum(2)       # NPS(0) from 64-px bins (D6 sec. 3 method)
nps0 = binned.var(axis=0, ddof=1).mean() / 64
binned256 = flat.reshape(3000, MPIX // 256, 256).sum(2)
nps0_256 = binned256.var(axis=0, ddof=1).mean() / 256
print(f"flat fields (3000): gain g = {g_meas:.4f} counts/e (E[m] = {Em:.3f}); NPS(0) from 64-px bins "
      f"{nps0:.2f}, from 256-px bins {nps0_256:.2f} (nbar E[m^2] = {NBAR * Em2:.2f}); DQE(0) = g^2 nbar / NPS(0) = "
      f"{g_meas ** 2 * NBAR / nps0:.4f} (64 px), {g_meas ** 2 * NBAR / nps0_256:.4f} (256 px); "
      f"L9 I3.3 E[m]^2/E[m^2] = {Em * Em / Em2:.4f}")
for q_c, p in ((0.25, 4), (0.125, 8)):
    kc = int(round(q_c * MPIX))
    band = [kc + d for d in range(-3, 4)]
    nps_qc = float(P[band].mean())
    real = mc(q_c, MU, NBAR, MPIX, SPX, PM, 3000, seed=100 + p)
    j = np.arange(MPIX) + 0.5                            # pixel centres
    c = (real * np.exp(-2j * np.pi * q_c * j)).mean(1)
    mtf_meas = 2 * abs(c.mean()) / (g_meas * NBAR * MU)
    mtf_model = math.exp(-2 * math.pi ** 2 * SPX ** 2 * q_c ** 2) * float(np.sinc(q_c))
    dqe_qc = g_meas ** 2 * NBAR * mtf_meas ** 2 / nps_qc
    dphi = np.angle(c * np.exp(-1j * 0.3))
    sig = float(dphi.std(ddof=1))
    Ntot = MPIX * NBAR
    pred = math.sqrt(2) / (MU * math.sqrt(Ntot * dqe_qc))
    ideal = math.sqrt(2) / (MU * math.sqrt(Ntot))
    wrong = ideal / (mtf_meas * math.sqrt(dqe_qc))
    naive = math.sqrt(2) / (MU * mtf_meas * math.sqrt(Ntot * g_meas))
    print(f" {p} px/fringe (q_c = {q_c} cycles/px): MTF measured {mtf_meas:.4f} (model {mtf_model:.4f}); "
          f"NPS(q_c) {nps_qc:.2f}; DQE(q_c) {dqe_qc:.4f}")
    print(f"   sigma_phi measured {sig:.5f} rad (3000 realisations, s.e. ~{sig / math.sqrt(2 * 2999):.5f}); "
          f"formula sqrt(2)/(mu sqrt(N DQE)) {pred:.5f} (ratio {sig / pred:.3f})")
    print(f"   ideal DQE = 1 value {ideal:.5f} -> measured/ideal {sig / ideal:.3f} vs 1/sqrt(DQE) "
          f"{1 / math.sqrt(dqe_qc):.3f}; the MTF-type scaling 1/(MTF sqrt(DQE)) would give {wrong:.5f} "
          f"(ratio {sig / wrong:.3f}); naive Poisson with measured contrast and counts {naive:.5f} "
          f"(ratio {sig / naive:.3f})")
# control: ideal point-sampling Poisson detector (the present record_holograms, gain 1)
rng = np.random.default_rng(7)
j = np.arange(MPIX) + 0.5
sigs = []
for q_c in (0.25, 0.125):
    lam = NBAR * (1 + MU * np.cos(2 * np.pi * q_c * j + 0.3))
    cc = np.array([(rng.poisson(lam) * np.exp(-2j * np.pi * q_c * j)).mean() for _ in range(3000)])
    sigs.append((q_c, float(np.angle(cc * np.exp(-0.3j)).std(ddof=1))))
print("control, point-sampled Poisson (DQE = 1, the present code):",
      [f"q_c {q}: measured {s:.5f}, formula {math.sqrt(2) / (MU * math.sqrt(MPIX * NBAR)):.5f}" for q, s in sigs])

# ------------------------------------------------------------------------------------------------ G
print("\n=== G. Effective DQE over a Hann disc mask of radius |q_c|/3 (B29), 2-D, isotropic D6 curves")
for p in (4, 8):
    qc = 1.0 / p
    R = qc / 3
    n = 401
    qx = np.linspace(-R, R, n)
    QX, QY = np.meshgrid(qx, qx, indexing="ij")
    rr = np.hypot(QX, QY)
    Wm = np.where(rr < R, 0.5 * (1 + np.cos(np.pi * rr / R)), 0.0)
    qabs = np.hypot(QX, QY + qc)                        # carrier along axis 1
    wabs = qabs / OMEGA_N
    mt = np.exp(-(wabs / w0_lin) ** 2)
    dq = np.vectorize(dqe_dig)(np.clip(wabs, 0.0, 0.74))
    nnps = 0.80 * mt ** 2 / np.maximum(dq, 1e-6)
    avg = float((Wm ** 2 * nnps).sum() / (Wm ** 2).sum())
    nnps_c = 0.80 * MTF_G(2 * qc) ** 2 / dqe_dig(2 * qc)
    dqe_eff = dqe_dig(2 * qc) * nnps_c / avg
    print(f" {p} px/fringe: mask spans {2 * (qc - R):.3f}-{2 * (qc + R):.3f} w_N; NNPS at q_c {nnps_c:.3f}, "
          f"Hann^2-weighted mean {avg:.3f}; DQE(q_c) {dqe_dig(2 * qc):.3f} -> effective {dqe_eff:.3f}; "
          f"phase-noise factor {1 / math.sqrt(dqe_dig(2 * qc)):.2f} -> {1 / math.sqrt(dqe_eff):.2f}")

# ------------------------------------------------------------------------------------------------ H
print("\n=== H. B29 minimum empty-hologram visibility V_min = 0.5 against the detector MTF")
print("measured visibility V = mu_inc * MTF(q_c) (the centre band has MTF(0) = 1); V >= 0.5 needs mu_inc >= 0.5/MTF")
EXP_N2 = 0.536                                        # B38: zero-loss amplitude exp(-n/2), R1 fringe factor
for p in (4, 5, 6, 8, 10, 12, 16, 17, 20):
    x = 2.0 / p
    Mg, Md = MTF_G(x), mtf_dig(x)
    print(f" {p:2d} px/fringe: MTF {Md:.3f} (Gaussian {Mg:.3f}); mu_inc needed {0.5 / Md:.3f}; "
          f"V at mu = 1: {Md:.3f} ({'pass' if Md >= 0.5 else 'FAIL'}); V with the B38 R1 factor 0.536: "
          f"{EXP_N2 * Md:.3f} ({'pass' if EXP_N2 * Md >= 0.5 else 'FAIL'})")
p_min_mu1 = 2.0 / (w0_lin * math.sqrt(math.log(2.0)))
p_min_b38 = 2.0 / (w0_lin * math.sqrt(-math.log(0.5 / EXP_N2)))
print(f"threshold (Gaussian fit): V >= 0.5 at mu = 1 needs p >= {p_min_mu1:.2f} px/fringe; "
      f"with the B38 factor 0.536 needs MTF >= {0.5 / EXP_N2:.4f}, i.e. p >= {p_min_b38:.1f} px/fringe")

# ------------------------------------------------------------------------------------------------ I
print("\n=== I. Demo configuration arithmetic (B23, B28)")
m0c2 = 510998.95  # eV
E = 200e3
lam = 12.398419843320026 / math.sqrt(E / 1e3 * (2 * m0c2 / 1e3 + E / 1e3))  # A, energies in keV
band = math.sin(3e-3) / lam
print(f"lambda(200 keV) = {lam:.6f} A; 3 mrad aperture band = {band:.4f} cycles/A")
print(f"B23/B28 now: pixel 0.5 A, carrier 2.0 A -> {2.0 / 0.5:.0f} px/fringe; q_c = {1 / 2.0:.3f} cycles/A, "
      f"mask |q_c|/3 = {1 / 2.0 / 3:.4f} cycles/A >= band {band:.4f}: {1 / 6 >= band}")
for label, pix, s in (("(a) keep carrier 2.0 A, pixel 0.25 A", 0.25, 2.0),
                      ("(b) keep pixel 0.5 A, carrier 4.0 A", 0.5, 4.0)):
    qc = 1 / s
    print(f" {label}: {s / pix:.0f} px/fringe; mask {qc / 3:.4f} cycles/A vs band {band:.4f}: "
          f"{'object band inside the mask' if qc / 3 >= band else 'object band NOT inside the mask (B28 rationale broken)'}; "
          f"M = {15e4 / pix:.3g} at 15 um pitch, {55e4 / pix:.3g} at 55 um; detector Nyquist {0.5 / pix:.2f} cycles/A")
print(f"largest carrier spacing keeping the 3 mrad band inside |q_c|/3: {1 / (3 * band):.3f} A; at 8 px/fringe "
      f"the pixel must then be <= {1 / (3 * band) / 8:.4f} A")
print(f"same field with pixel 0.25 A: ROI [512, 128] -> [{512 * 2}, {128 * 2}] ({4}x the detector pixels)")

# ------------------------------------------------------------------------------------------------ J
print("\n=== J. Asymmetric weighting of the sideband by the MTF (not removed by dividing by the empty hologram)")
for p in (4, 8):
    qc = 1.0 / p
    R = qc / 3
    lo = math.exp(-((qc - R) / (OMEGA_N * w0_lin)) ** 2) / math.exp(-(qc / (OMEGA_N * w0_lin)) ** 2)
    hi = math.exp(-((qc + R) / (OMEGA_N * w0_lin)) ** 2) / math.exp(-(qc / (OMEGA_N * w0_lin)) ** 2)
    print(f" {p} px/fringe: MTF(q_c - R)/MTF(q_c) = {lo:.3f}, MTF(q_c + R)/MTF(q_c) = {hi:.3f} "
          f"(ratio across the mask {lo / hi:.2f})")

# ------------------------------------------------------------------------------------------------ K
print("\n=== K. L9's remaining numbers")
wk = [0.2, 0.25, 0.3, 0.4, 0.5, 0.6]
print("NNPS = DQE(0) MTF^2 / DQE (D6 Eq. (6)):", [f"{x}: {0.80 * mtf_dig(x) ** 2 / dqe_dig(x):.3f}" for x in wk])
th = 16.1347e-3
print(f"1/sin(16.1347 mrad) = {1 / math.sin(th):.3f}")
for s, ppf in ((2.0, 8), (2.0, 4), (10.0, 8), (50.0, 8)):
    pix = s / ppf
    M_ = PITCH_UM * 1e4 / pix
    print(f" carrier {s} A at {ppf} px/fringe: pixel {pix:.4f} A, M = {M_:.4g}; along-beam surface per pixel "
          f"{pix / math.sin(th):.2f} A; 256 px: {256 * pix / math.sin(th) / 1e4:.3f} um along, "
          f"{256 * pix / 10:.1f} nm across")
print(f"B23 0.5 A pixel with a 55 um pitch: M = {PITCH_UM * 1e4 / 0.5:.3g}")
print("counter maxima:", {b: 2 ** b - 1 for b in (1, 6, 12, 24)})
print(f"I3.6: 256/8 = {256 / 8:.0f} fringes; resolution ~3 fringes = {3 * 8} px; 256/24 = {256 / 24:.1f} elements")
print(f"H1 brightness 2.9e8 - 2.9e9 A cm^-2 sr^-1 = {2.9e8 * 1e4:.2g} - {2.9e9 * 1e4:.2g} A m^-2 sr^-1")
