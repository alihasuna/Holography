"""Hologram formation and reconstruction round trip on a known field."""

import numpy as np

from reflection_holo import holography as H


def test_roundtrip_recovers_phase_and_amplitude():
    nx, ny, dx, dy = 64, 512, 0.5, 0.4
    y = dy * np.arange(ny)
    phi = 2.0 * np.exp(-((y - 100) / 12) ** 2) - 0.85 * ((y > 40) & (y < 70))  # bump + step
    amp = 1 - 0.3 * np.exp(-((y - 100) / 8) ** 2)
    lp = lambda f, r: np.fft.ifft(np.fft.fft(f) * (np.abs(np.fft.fftfreq(ny, dy)) < r))  # noqa: E731
    obj = lp(amp * np.exp(1j * phi), 0.06)  # objective aperture: band-limited object wave
    psi = np.broadcast_to(obj, (nx, ny))
    qc = (0.0, 50 / (ny * dy))  # 0.244 /A carrier along y, on the FFT grid
    I = H.form_hologram(psi, dx, dy, qc, 1.0)
    I0 = H.form_hologram(np.ones((nx, ny)), dx, dy, qc, 1.0)
    w, q = H.reconstruct(I, I0, dx, dy, radius=0.1)
    assert np.allclose(q, (0.0, -qc[1]))
    # carrier 0.244 > 3 x 0.06: sidebands do not overlap the centre band, so the recovery is exact
    np.testing.assert_allclose(w[nx // 2], obj, atol=1e-9)
