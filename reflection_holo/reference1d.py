"""One-dimensional reflection references for the validation ladder (rungs 1 and 2).

For a potential that depends only on the normal coordinate x the stationary problem
separates; the normal part obeys phi'' + K(x)^2 phi = 0 with

  * "schroedinger": K^2 = Kx^2 + 2 k sigma (V + iW)   (relativistically corrected
    Schroedinger equation, first order in V/(T + m c^2));
  * "multislice":   K^2 = k^2 - (kz - sigma (V + iW))^2,  kz = sqrt(k^2 - Kx^2)
    (the dispersion of the split-step multislice with the exact propagator in the
    limit dz -> 0; it is what the multislice must reproduce exactly).

Kx = 2 pi |q| is the vacuum normal wavenumber.  The two forms differ by
(k - kz)/k ~ theta^2/2 and sigma V/(2k) ~ 2e-5 in U, i.e. negligibly at grazing
incidence; both are provided so that the residual can be stated.

Parratt recursion (DERIVED_HERE in docs/08_fir_simulation_campaign.md, appendix A):
X_j = (r_j + Y)/(1 + r_j Y), Y = X_{j+1} exp(2 i K_{j+1} d_{j+1}),
r_j = (K_j - K_{j+1})/(K_j + K_{j+1}), X_N = 0 for the semi-infinite bottom layer.
The reflection coefficient referred to the plane x_ref is X_0 exp(2 i K_0 (x_ref - x_top)).
"""
from __future__ import annotations

import numpy as np


def K_profile(Kx, k, sigma, Vc, model):
    """Normal wavenumber in each layer, Im K >= 0. Vc = V + iW (complex volts)."""
    Kx = np.asarray(Kx, float)[..., None]
    Vc = np.asarray(Vc, complex)[None, ...] if np.ndim(Kx) else np.asarray(Vc, complex)
    if model == "schroedinger":
        K2 = Kx**2 + 2.0 * k * sigma * Vc
    elif model == "multislice":
        kz = np.sqrt(k * k - Kx**2)
        K2 = k * k - (kz - sigma * Vc) ** 2
    else:
        raise ValueError(model)
    K = np.sqrt(K2.astype(complex))
    return np.where(K.imag < 0, -K, K)


def parratt(Kx, k, sigma, V_layers, d_layers, x_top, x_ref, model="schroedinger"):
    """Complex reflection coefficient r(Kx) referred to x_ref.

    V_layers: complex potential of layers ordered from the top: index 0 is the
    semi-infinite vacuum above x_top (must be 0), the last is the semi-infinite
    bottom; d_layers: thicknesses of layers 1..N-1 (len(V_layers) - 2 values).
    """
    Kx = np.atleast_1d(np.asarray(Kx, float))
    V = np.asarray(V_layers, complex)
    d = np.asarray(d_layers, float)
    if abs(V[0]) != 0:
        raise ValueError("top layer must be vacuum")
    if len(d) != len(V) - 2:
        raise ValueError("need len(V) - 2 thicknesses")
    K = K_profile(Kx, k, sigma, V, model)         # (nK, nL)
    X = np.zeros(len(Kx), complex)
    for j in range(len(V) - 2, -1, -1):
        Kj, Kn = K[:, j], K[:, j + 1]
        r = (Kj - Kn) / (Kj + Kn)
        Y = X * np.exp(2j * Kn * d[j]) if j + 1 <= len(d) else X
        X = (r + Y) / (1.0 + r * Y)
    K0 = K[:, 0]
    return X * np.exp(2j * K0 * (x_ref - x_top))


def transfer_matrix(Kx, k, sigma, V_layers, d_layers, x_top, x_ref, model="schroedinger"):
    """Independent 2x2 transfer-matrix solution; returns (r referred to x_ref, t, K)
    with t the down-going amplitude at the top of the bottom layer per unit incident
    amplitude at x_top.  Only for small, well-conditioned tests."""
    Kx = np.atleast_1d(np.asarray(Kx, float))
    V = np.asarray(V_layers, complex)
    d = np.asarray(d_layers, float)
    K = K_profile(Kx, k, sigma, V, model)
    rs, ts = [], []
    for i in range(len(Kx)):
        # state vector (phi, phi') at the current boundary, start at the bottom
        # with a pure down-going wave of unit amplitude: phi = exp(-iK x)
        KN = K[i, -1]
        state = np.array([1.0, -1j * KN], complex)
        for j in range(len(V) - 2, 0, -1):     # propagate up through layer j
            Kj = K[i, j]
            dj = d[j - 1]
            c, s = np.cos(Kj * dj), np.sin(Kj * dj)
            M = np.array([[c, s / Kj], [-Kj * s, c]], complex)
            state = M @ state
        K0 = K[i, 0]
        # phi = A exp(-iK0 (x-x_top)) + B exp(+iK0 (x-x_top)) at x = x_top
        A = 0.5 * (state[0] - state[1] / (1j * K0))
        B = 0.5 * (state[0] + state[1] / (1j * K0))
        rs.append(B / A * np.exp(2j * K0 * (x_ref - x_top)))
        ts.append(1.0 / A)
    return np.array(rs), np.array(ts), K


def fermi_step_R(K1, K2, a):
    """|r|^2 for V(x) = V0/(1 + exp(x/a)) (vacuum K1 above, K2 inside).

    R = [sinh(pi a (K2 - K1)) / sinh(pi a (K1 + K2))]^2.  Recalled from the standard
    textbook problem (Landau-Lifshitz, Quantum Mechanics, section 25), NOT read in
    this session: UNVERIFIED as a citation; used only as an extra cross-check of the
    Parratt solver, which is validated independently against the sharp-step Fresnel
    coefficient and the transfer-matrix solution.
    """
    return (np.sinh(np.pi * a * (K2 - K1)) / np.sinh(np.pi * a * (K1 + K2))) ** 2


def layers_from_profile(x, Vc, x_top):
    """Convert a sampled potential profile (x increasing, uniform spacing) into
    Parratt layers from the top downwards: each sample with x <= x_top becomes a
    layer of thickness dx centred on it.

    Returns (V_layers, d_layers, x_boundary) where V_layers includes the vacuum on
    top and the lowest sample as the semi-infinite bottom, and x_boundary is the
    actual top boundary of the stack (top sample + dx/2), which is the plane the
    Parratt ratio X_0 refers to.  The samples above the boundary must be vacuum.
    """
    x = np.asarray(x, float)
    Vc = np.asarray(Vc, complex)
    dx = x[1] - x[0]
    sel = np.nonzero(x <= x_top + 1e-12)[0][::-1]       # from the top down
    if np.any(np.abs(Vc[x > x[sel[0]] + 1e-12]) > 0):
        raise ValueError("potential above x_top is not zero")
    Vl = np.concatenate([[0.0], Vc[sel]])
    d = np.full(len(sel) - 1, dx)
    return Vl, d, float(x[sel[0]] + 0.5 * dx)
