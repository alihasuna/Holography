"""Grazing-incidence multislice with a symmetric (Strang-type) splitting.

Each atomic plane at z_p carries the projected potential of the slab
[z_p - dz/2, z_p + dz/2]; the wave is propagated exactly between planes with
P(q) = exp(i (kz(q) - k) dz) (kz = 2 pi sqrt(1/lambda^2 - q^2)) and transmitted at
each plane.  Waves are band-limited by the anti-aliasing mask in every propagator.
Exit waves are returned on DECLARED planes z_exit (one per batch element), obtained
by propagating from the last plane before z_exit by the remaining distance.
"""
from __future__ import annotations

import time

import numpy as np

from .beams import kz_minus_k


class Propagator:
    def __init__(self, grid, lam, xp, dtype, kind="exact"):
        self.g, self.lam, self.xp, self.dtype, self.kind = grid, lam, xp, dtype, kind
        self._cache = {}
        self._q2 = grid.q2
        self._band = grid.band

    def __call__(self, dz):
        key = round(float(dz), 9)
        P = self._cache.get(key)
        if P is None:
            if self.kind == "exact":
                ph = kz_minus_k(self._q2, self.lam) * dz
            elif self.kind == "fresnel":
                ph = -np.pi * self.lam * self._q2 * dz
            else:
                raise ValueError(self.kind)
            P = self.xp.asarray((np.exp(1j * ph) * self._band).astype(self.dtype))
            if len(self._cache) < 64:
                self._cache[key] = P
        return P


def propagate(psi, P, xp):
    return xp.fft.ifft2(xp.fft.fft2(psi, axes=(-2, -1)) * P, axes=(-2, -1))


def run_multislice(psi0, plane_z, transmission, z_exit, propagator, xp,
                   record_rows=None, z_min=None, tail_tol=None, tail_window=400,
                   check_every=200, side_view_every=0, side_view_bin=4, progress=None):
    """March the batch psi0 (B, Nx, Ny) through the planes.

    plane_z: increasing z positions of the planes (all > 0, entrance plane z = 0).
    transmission(i): transmission function of plane i (Nx, Ny), shared by the batch.
    z_exit: (B,) last plane position of each element (a hard cap).
    record_rows: optional (B, n_rows) x-indices; the wave on those rows is recorded
        after every plane (the virtual detector); planes after an element has stopped
        are recorded as zeros.
    Adaptive stop (if tail_tol is given): an element stops at the first check (every
        check_every planes) after z >= z_min[b] at which the largest |y-mean record of
        row 0| over the last tail_window planes is below tail_tol times its largest
        value so far.  Otherwise it stops at z_exit[b].
    Returns (exits (B, Nx, Ny) at the stop plane of each element, records
             (B, n_rows, n_planes, Ny) or None, z_stop (B,), side_view or None, stats).
    """
    B, Nx, Ny = psi0.shape
    z_exit = np.asarray(z_exit, float)
    z_min = z_exit if z_min is None else np.asarray(z_min, float)
    psi = psi0.copy()
    active = np.arange(B)                  # original indices of the rows of psi
    exits = [None] * B
    z_stop = np.full(B, np.nan)
    rec = None
    if record_rows is not None:
        rows = np.asarray(record_rows)
        rec = xp.zeros((B, rows.shape[1], len(plane_z), Ny), dtype=psi0.dtype)
        rows_g = xp.asarray(rows)
        ymean = np.zeros((B, len(plane_z)))      # |y-mean of row 0| per plane (host)
        last_check = 0
    sv_z, sv_I = [], []
    t0 = time.time()
    n_done = 0
    for i, zp in enumerate(plane_z):
        psi = propagate(psi, propagator(zp - (plane_z[i - 1] if i else 0.0)), xp)
        psi *= transmission(i)[None, :, :]
        n_done += 1
        if rec is not None:
            idx = rows_g[xp.asarray(active)]                       # (n_active, n_rows)
            ar = xp.arange(len(active))[:, None]
            rec[xp.asarray(active)[:, None], xp.arange(rows.shape[1])[None, :], i, :] = psi[ar, idx, :]
        stop = np.zeros(len(active), bool)
        stop |= zp >= z_exit[active] - 1e-9
        if (tail_tol is not None and rec is not None and (i + 1) % check_every == 0):
            a = xp.abs(rec[xp.asarray(active), 0, last_check: i + 1, :].mean(axis=2))
            ymean[active, last_check: i + 1] = a.get() if hasattr(a, "get") else np.asarray(a)
            last_check = i + 1
            lo = max(0, i + 1 - tail_window)
            runmax = ymean[active, : i + 1].max(axis=1)
            recent = ymean[active, lo: i + 1].max(axis=1)
            ok = (zp >= z_min[active]) & (recent <= tail_tol * np.maximum(runmax, 1e-300))
            stop |= ok
        if stop.any():
            for j in np.nonzero(stop)[0]:
                b = active[j]
                exits[b] = psi[j]
                z_stop[b] = zp
            keep = np.nonzero(~stop)[0]
            psi = psi[xp.asarray(keep)] if len(keep) else psi[:0]
            active = active[keep]
        if len(active) == 0:
            break
        if side_view_every and i % side_view_every == 0:
            I = (xp.abs(psi) ** 2).mean(axis=2)
            nb = Nx // side_view_bin
            I = I[:, : nb * side_view_bin].reshape(I.shape[0], nb, side_view_bin).mean(-1)
            full = np.full((B, nb), np.nan, dtype=np.float32)
            full[active] = np.asarray(I.get() if hasattr(I, "get") else I, dtype=np.float32)
            sv_z.append(zp)
            sv_I.append(full)
        if progress is not None and (n_done % 2000 == 0):
            progress(n_done, len(plane_z), time.time() - t0)
    for j, b in enumerate(active):          # planes exhausted
        exits[b] = psi[j]
        z_stop[b] = plane_z[-1]
    stats = dict(planes_marched=n_done, seconds=time.time() - t0)
    sv = dict(z=np.array(sv_z), I=np.array(sv_I)) if sv_z else None
    return xp.stack(exits), rec, z_stop, sv, stats
