"""Digitise Paton et al. 2021 (Ultramicroscopy 227, 113298; CC BY) Fig. 8(a),(b): 200 keV electrons,
Si-sensor Medipix3, single pixel mode. Source: embedded raster xref 246 on p. 7 of the Glasgow copy
(eprints.gla.ac.uk/240505/1/240505.pdf, sha256 555e925c...0e5). Axis calibration from the light-grey grid
lines (0.2 spacing) found by colour; curves traced by nearest-prototype colour, centroid per column.
DERIVED_HERE; expected accuracy about +-0.02 in value (line width ~6 px = 0.017)."""
import numpy as np, pymupdf
d = pymupdf.open('pdf/Paton2021_gla_AAM.pdf')
pix = pymupdf.Pixmap(d, 246)
A = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3].astype(float)
R, G, B = A[..., 0], A[..., 1], A[..., 2]
grey = (abs(R - G) < 12) & (abs(G - B) < 12) & (R > 150) & (R < 240)

def grid_positions(mask_1d_frac, thr=0.25):
    idx = np.where(mask_1d_frac > thr)[0]
    groups = [[idx[0]]]
    for a in idx[1:]:
        (groups[-1].append(a) if a - groups[-1][-1] <= 2 else groups.append([a]))
    return [float(np.mean(g)) for g in groups]

proto = {'navy_58keV': (5, 15, 70), 'darkred_12keV': (140, 15, 45), 'green_117keV': (0, 140, 20),
         'lightblue_squarepixel': (115, 187, 255)}
def cls(name, tol=70.0):
    p = np.array(proto[name], float)
    return np.sqrt(((A - p) ** 2).sum(2)) < tol

rows = grid_positions(grey[40:440, 90:460].mean(1)); rows = [r + 40 for r in rows]
ygrid = [r for r in rows if 85 < r < 440]   # expect y = 1.0, 0.8, 0.6, 0.4, 0.2, 0.0 (bottom spine)
print('y grid rows (1.0 ... 0.0):', np.round(ygrid, 1))
y_of = np.polyfit(ygrid, [1.0, 0.8, 0.6, 0.4, 0.2, 0.0], 1)
for name, (l, r) in {'a (MTF)': (84, 466), 'b (DQE)': (596, 976)}.items():
    cols = grid_positions(grey[60:436, l:r + 3].mean(0)); cols = [c + l for c in cols]
    xg = [c for c in cols if l + 20 < c < r - 20][:4]      # 0.2, 0.4, 0.6, 0.8
    x_fit = np.polyfit([0.2, 0.4, 0.6, 0.8], xg, 1)
    print(f'panel {name}: x grid cols {np.round(xg,1)} -> px(x) = {x_fit[0]:.1f} x + {x_fit[1]:.1f}')
    curves = {'a (MTF)': ['navy_58keV', 'darkred_12keV', 'green_117keV', 'lightblue_squarepixel'],
              'b (DQE)': ['navy_58keV', 'darkred_12keV', 'green_117keV', 'lightblue_squarepixel']}[name]
    for cname in curves:
        m = cls(cname)
        m[:85, :] = False; m[440:, :] = False
        res = []
        for f in np.round(np.arange(0.0, 1.0001, 0.05), 2):
            px = int(round(np.polyval(x_fit, f)))
            px = min(max(px, l + 4), r - 4)
            ys = np.where(m[:, px - 1:px + 2].any(1))[0]
            # keep the largest connected run (the curve), ignore legend and stray pixels
            if ys.size:
                runs = np.split(ys, np.where(np.diff(ys) > 3)[0] + 1)
                run = max(runs, key=len)
                res.append((float(f), round(float(np.polyval(y_of, run.mean())), 3)))
            else:
                res.append((float(f), None))
        print(f'  {cname}:', res)
