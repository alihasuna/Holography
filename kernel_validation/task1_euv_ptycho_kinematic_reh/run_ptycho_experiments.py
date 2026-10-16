"""Reflection ptychography experiments (SIMULATED data). Writes ptycho_results.npz / .json"""
import numpy as np, json, time
from numpy.fft import fft2, ifft2, fftshift, ifftshift
from scipy.signal import fftconvolve
import refl_ptycho as rp

g = rp.Geometry(); bx = 2; N = g.N
Ps = rp.surface_probe(g)                                   # true probe (defocus + trefoil, exact tilted-plane)
rng = np.random.default_rng(3); sy, sx, ny, nx = 9, 26, 13, 6
pos = [(5 + i*sy + int(rng.integers(-2, 3)), 2*((5 + j*sx + int(rng.integers(-3, 4)))//2)) for i in range(ny) for j in range(nx)]
My = max(p[0] for p in pos) + N + 5; Mx = max(p[1] for p in pos) + N + 6; Mx += Mx % 2
O, h, feat = rp.make_surface(My, Mx, g)
data, clean = rp.simulate(O, Ps, pos, g, return_clean=True)       # 5e6 counts / pattern, Poisson
posR = [(y, x//bx) for y, x in pos]; shapeR = (My, Mx//bx); PsR = Ps[:, ::bx]

def to_M(maskN_c, shape):
    FY, FX = np.meshgrid(np.fft.fftfreq(shape[0], g.d), np.fft.fftfreq(shape[1], g.d), indexing='ij')
    iy = np.round(FY*N*g.d).astype(int) + N//2; ix = np.round(FX*N*g.d).astype(int) + N//2
    v = (iy >= 0) & (iy < N) & (ix >= 0) & (ix < N); out = np.zeros(shape, bool); out[v] = maskN_c[iy[v], ix[v]]; return out
covN = rp.coverage_mask((N, N), g); supP = fftshift(np.abs(fft2(Ps)) > 1e-2*np.abs(fft2(Ps)).max())
objM = to_M(fftconvolve(fftshift(covN).astype(float), supP[::-1, ::-1].astype(float), 'same') > 0.5, O.shape)
objM &= np.abs(np.fft.fftfreq(O.shape[1], g.d))[None, :] < 1/(2*bx*g.d)
Ot_R = rp.lowpass(O, objM)[:, ::bx]                         # band-limited truth on recon grid (d, 2d)
covR = rp.coverage_mask(shapeR, g, bx=bx)                   # directly measured band (metric band)
ill = np.zeros(shapeR)
for (y0, x0) in posR: ill[y0:y0+N, x0:x0+N//bx] += np.abs(PsR)**2
roi = ill > 0.25*ill.max()

I0, m0 = rp.resample(clean, g, bx=bx)
y0, x0 = posR[30]; F = fftshift(np.abs(fft2(ifftshift(PsR*Ot_R[y0:y0+N, x0:x0+N//bx]))))
s = (np.sqrt(I0[30])[m0]*F[m0]).sum()/(F[m0]**2).sum()
Ptrue = PsR*s; Pg = rp.surface_probe(g, zf=6e-6, trefoil=0.0)[:, ::bx]*s   # init: defocus +20 %, no trefoil
ref_sum = clean.sum((1, 2)).mean()

def core(Or):
    return rp.compare(rp.lowpass(Ot_R, covR), rp.lowpass(Or, covR), roi)[0]
def recon(Idat, mode="tpc", theta=None, P0=Pg, known=False, alpha=0.15, beta=0.15, n_iter=400, seed=0):
    I, m = rp.resample(Idat, g, theta=theta, mode=mode, bx=bx)
    P0 = P0*np.sqrt(Idat.sum((1, 2)).mean()/ref_sum)
    Or, Pr, err = rp.ptycho_recon(I, m, posR, shapeR, P0, n_iter=n_iter, alpha=alpha, beta=beta,
                                  probe_start=999 if known else 5, seed=seed)
    return Or, Pr, err

R = {}; IMG = {}; t0 = time.time()
# (a) mapping model and algorithm, blind probe, 3 seeds
for lab, kw in {"TPC + rPIE": dict(), "linear foreshortening + rPIE": dict(mode="linear"),
                "TPC + ePIE": dict(alpha=1.0, beta=1.0)}.items():
    R[lab] = []
    for sd in range(3):
        Or, Pr, err = recon(data, seed=sd, **kw)
        R[lab].append(dict(core=core(Or), full=rp.compare(Ot_R, Or, roi)[0], err=err.tolist()))
        if sd == 0: IMG[lab] = rp.compare(Ot_R, Or, roi)[1]; IMG[lab + " probe"] = Pr
    print(lab, [round(r['core'], 3) for r in R[lab]], round(time.time()-t0), flush=True)
# (b) incidence-angle mis-calibration
R['sweep'] = []
for dt in [-2, -1, -0.5, -0.25, -0.1, 0, 0.1, 0.25, 0.5, 1, 2]:
    for sd in range(2):
        Or, Pr, err = recon(data, theta=g.theta + np.deg2rad(dt), seed=sd, n_iter=300)
        R['sweep'].append(dict(dt=dt, seed=sd, data_err=float(err[-1]), core=core(Or)))
    print('sweep', dt, R['sweep'][-1], flush=True)
# (c) dose
R['dose'] = []
for c in [1e4, 1e5, 1e6, 5e6, 5e7, np.inf]:
    for sd in range(3):
        dd = clean if np.isinf(c) else rp.simulate(O, Ps, pos, g, counts=c, seed=100+sd)
        for known in [True, False]:
            Or, Pr, err = recon(dd, P0=Ptrue if known else Pg, known=known, seed=sd)
            R['dose'].append(dict(counts=float(c) if np.isfinite(c) else None, seed=sd, known=known, core=core(Or)))
    print('dose', c, [round(r['core'], 3) for r in R['dose'][-6:]], round(time.time()-t0), flush=True)

json.dump(R, open('ptycho_results.json', 'w'))
np.savez_compressed('ptycho_results.npz', O=O, h=h, Ot_R=Ot_R, roi=roi, Ps=Ps, Ptrue=Ptrue, Pg=Pg,
                    data30=data[30], I30=rp.resample(data, g, bx=bx)[0][30], m0=m0, covR=covR,
                    pos=np.array(pos), d=g.d, bx=bx, **{k.replace(' ', '_').replace('+', 'p'): v for k, v in IMG.items()})
print('done', round(time.time()-t0))
