"""Blocked structure-factor exponentials (H7's proposed memory reduction, applied in E1 wave 2a):
the potential must be NUMERICALLY IDENTICAL (bit for bit) to the code before the change.

Reference: `_projected_before` is a verbatim copy of `_RealisedAtomic.projected` before the change
(exponentials formed over all rows at once). The blocked path is forced on small grids by setting
potentials.EXP_BLOCK_ROWS small (monkeypatch), so that every slice below goes through blocks with
remainders. Checks: the phase factors alone; several slices of a realised potential (complex64 and
complex128, r = 0 and 0.1, static and frozen phonons); a full small run (exit waves). Criterion:
byte equality (no tolerance). The reflection-geometry assertions are bypassed with monkeypatch for
the full run (the cell is 3 periods long, as in test_memory_model; the numerics do not depend on
them)."""
import numpy as np
import pytest

pytest.importorskip("abtem")

import reflection_holo.forward.multislice.engine as engine  # noqa: E402
import reflection_holo.forward.multislice.potentials as potentials  # noqa: E402
from reflection_holo.forward.multislice import run_realisation  # noqa: E402
from reflection_holo.forward.multislice.backend import get_backend  # noqa: E402
from reflection_holo.forward.multislice.grid import make_grid  # noqa: E402
from test_memory_model import Q, _case, _cell_100  # noqa: E402


def _projected_before(self, i):
    """VERBATIM copy of _RealisedAtomic.projected before the blocked exponentials (reference)."""
    be, xp = self.be, self.be.xp
    a, b = self.starts[i], self.starts[i + 1]
    if a == b:
        return xp.zeros(self.grid.shape, dtype=be.complex_dtype)
    acc = None
    for Zs, F in self.F.items():
        sel = self.Z[a:b] == Zs
        if not np.any(sel):
            continue
        # phase arguments in float64 (2 pi f x reaches ~2e3 rad; float32 would err by ~1e-4
        # rad), exponentials cast to the working precision afterwards
        pos = be.asarray(self.xyz[a:b][sel], dtype=np.float64)
        Ex = xp.exp(-2j * np.pi * (self.fx64[:, None] * pos[None, :, 0])).astype(be.complex_dtype)
        Ey = xp.exp(-2j * np.pi * (self.fy64[:, None] * pos[None, :, 1])).astype(be.complex_dtype)
        S = (Ex @ Ey.T) * F
        acc = S if acc is None else acc + S
    V = be.ifft2(acc).real * be.real_dtype(self.norm)
    if self.ratio:
        return (V * (1.0 + 1j * self.ratio)).astype(be.complex_dtype)
    return V.astype(be.complex_dtype)


@pytest.fixture(scope="module")
def cell():
    return _cell_100(2, 3, depth=36.0, vac=30.0)            # 576 x 84 px, as test_memory_model


@pytest.mark.parametrize("block", [1, 7, 16, 1000])
@pytest.mark.parametrize("dtype", [np.complex64, np.complex128])
def test_phase_factors_blocked_equal_unblocked(monkeypatch, block, dtype):
    rng = np.random.default_rng(3)
    f = np.fft.fftfreq(5003, 0.13)
    p = rng.uniform(0.0, 400.0, 37)
    ref = np.exp(-2j * np.pi * (f[:, None] * p[None, :])).astype(dtype)
    monkeypatch.setattr(potentials, "EXP_BLOCK_ROWS", block)
    got = potentials._phase_factors(np, f, p, dtype)
    assert got.dtype == ref.dtype and got.shape == ref.shape
    assert got.tobytes() == ref.tobytes()


@pytest.mark.parametrize("precision,ratio,phonons", [("complex64", 0.1, False),
                                                     ("complex128", 0.0, False),
                                                     ("complex64", 0.0, True)])
def test_slices_bit_identical_with_blocks(cell, monkeypatch, precision, ratio, phonons):
    monkeypatch.setattr(potentials, "EXP_BLOCK_ROWS", 16)   # nx = 576, ny = 84: both blocked
    pot, _, params = _case(cell, precision=precision, ratio=ratio, phonons=phonons)
    grid = make_grid(cell, nx=params.nx, ny=params.ny)
    assert grid.nx > 32 and grid.ny > 32
    be = get_backend("numpy", precision, 2)
    N = int(round(cell.length_z_A / Q))
    rng = np.random.default_rng([7, 0]) if phonons else None
    rl = pot.realise(grid=grid, dz_A=Q, n_slices=N, backend=be, rng=rng)
    nonempty = [i for i in range(N) if rl.slice_key(i) is None]
    assert len(nonempty) >= 4
    for i in nonempty[:3] + nonempty[-2:]:
        new = rl.projected(i)
        old = _projected_before(rl, i)
        assert new.dtype == old.dtype and new.tobytes() == old.tobytes()


def test_full_run_bit_identical_with_blocks(cell, monkeypatch):
    monkeypatch.setattr(engine, "check_reflection_geometry",
                        lambda *a, **k: {"label": "BYPASSED (cell too short; numerics only)"})
    pot, beam, params = _case(cell, precision="complex64", ratio=0.1, phonons=False)
    monkeypatch.setattr(potentials, "EXP_BLOCK_ROWS", 16)
    new = run_realisation(cell, potential=pot, beam=beam, params=params, realisation=0, seed=None)
    monkeypatch.setattr(potentials._RealisedAtomic, "projected", _projected_before)
    old = run_realisation(cell, potential=pot, beam=beam, params=params, realisation=0, seed=None)
    assert new.psi.tobytes() == old.psi.tobytes()


def test_default_block_is_used_only_where_it_saves_memory():
    """Unblocked up to 2 * EXP_BLOCK_ROWS rows (32 m n <= cb m n + 32 B n there for cb <= 16)."""
    assert potentials.EXP_BLOCK_ROWS == 1024
    for cb in (8, 16):
        for m in (100, 2048, 2049, 24000):
            n = 1000
            e = engine._exp_stage_B(m, n, cb)
            assert e == (32 * m * n if m <= 2048 else cb * m * n + 32 * 1024 * n)
            assert e <= 32 * m * n
    # H7's example (2a_a2 row: ny = 24 000, n = 15 211, complex64): the complex128 transient of
    # Ey falls from 32 ny n = 11.7 GB to 32 x 1024 x n = 0.50 GB
    n = 15211
    assert 32 * 24000 * n / 1e9 == pytest.approx(11.68, abs=0.01)
    assert (engine._exp_stage_B(24000, n, 8) - 8 * 24000 * n) / 1e9 == pytest.approx(0.498,
                                                                                      abs=0.001)
