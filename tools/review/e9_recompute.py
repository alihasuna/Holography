#!/usr/bin/env python
"""E9 review: independent recomputation of the numbers in docs/agent_reports/L8_oxide_plasma.md.

Written by agent E9 (2026-09-24) WITHOUT opening L8's own scripts (scratchpad l8/l8_numbers.py,
l8/analyse_asio2.py). Every number quoted by docs/agent_reports/E9_oxide_review.md is printed here.

Usage:
    venv/bin/python tools/review/e9_recompute.py [ZENODO_DIR] > tools/review/e9_recompute_output.txt

ZENODO_DIR (optional) holds members extracted by E9 from Zenodo 10.5281/zenodo.10419194
`results.zip` (HTTP range requests, CRC-32 checked against the zip directory):
    ace_4.in.data   = results/SiO2/ace/4.in.data        (SHA-256 b45ffe7d...8794d)
    hybrid.out.data = results/SiO2/hybrid/hybrid.out.data (SHA-256 2d11ced0...6ac28)
Without it, section O (structure statistics) is skipped.

Conventions: docs/physics_conventions.md (CODATA 2018, exact SI-2019 constants, relativistic
wavelength, exact relativistic refraction Delta, glancing angles, exp(+i k.r)). Glancing angle
16.1347 mrad = the repository's (0,0,8) value (ASSUMPTION B32). Lengths in A unless stated.
Sections:
  A constants; B absorptive potential V' = 1/(2 sigma Lambda); C refraction into the oxide;
  D attenuation of the specular beam by a continuum oxide (and a-Si); E phase terms (conformal,
  planarising, top-surface-only and GROWN-oxide thickness differences, thresholds);
  F Si consumed per oxide thickness; G Kirkland IAM mean inner potential of SiO2;
  H Yamamura-Tawara sputter thresholds; I tiling satellites of a periodic amorphous tile;
  J Si IMFP -> V'; K Lee et al. 2000 phase check; L E9 figure readings (Kitajima Fig. 16,
  Robinson Fig. 4); M thickness-route arithmetic; N Fresnel reflection at the layer surfaces;
  O Zenodo structure statistics; P combination with B38 (surface-plasmon zero-loss fraction).
"""
import math
import sys
import json
import os

import numpy as np

# ---------------------------------------------------------------- A. constants
H = 6.62607015e-34          # J s (exact)
E = 1.602176634e-19         # C (exact)
C = 299792458.0             # m/s (exact)
ME = 9.1093837015e-31       # kg (CODATA 2018)
MEC2 = 510998.95000         # eV (CODATA 2018)
NA = 6.02214076e23          # 1/mol (exact)
K_F = H ** 2 / (2 * math.pi * ME * E) * 1e20   # h^2/(2 pi m0 e) in V A^2 (f_e(0) in A -> integral of V in V A^3)

# atomic weights (IUPAC standard values; the 5th digit is not significant for any conclusion)
M_SI, M_O, M_AR = 28.0855, 15.9994, 39.948
M_SIO2 = M_SI + 2 * M_O
A_SI = 5.4309               # A (ASSUMPTION B2)
THETA = 16.1347e-3          # rad, (0,0,8) external glancing angle (ASSUMPTION B32)


def wavelength_A(T_eV):
    TJ = T_eV * E
    return H * C / math.sqrt(TJ * (TJ + 2 * ME * C ** 2)) * 1e10


def sigma_per_VA(T_eV):
    lam_m = wavelength_A(T_eV) * 1e-10
    gamma = 1 + T_eV / MEC2
    return 2 * math.pi * gamma * ME * E * lam_m / H ** 2 * 1e-10   # rad / (V A)


def delta_exact(V, T_eV):
    """(k_int^2 - k^2)/k^2, exact relativistic, V in volts (may be complex), T in eV."""
    return V * (2 * (T_eV + MEC2) + V) / (T_eV * (T_eV + 2 * MEC2))


T = 200e3
LAM = wavelength_A(T)
K = 2 * math.pi / LAM
SIG = sigma_per_VA(T)
KPERP = K * math.sin(THETA)


def kperp_in(V, Vi=0.0):
    """Surface-normal wavevector inside a layer of potential V + i Vi (vacuum parallel k conserved)."""
    d = delta_exact(complex(V, Vi), T)
    return K * np.sqrt(complex(math.sin(THETA) ** 2) + d)


def pr(label, value, fmt='{:.6g}', unit=''):
    if isinstance(value, (list, tuple)):
        s = ', '.join(fmt.format(v) for v in value)
    else:
        s = fmt.format(value)
    print(f'  {label}: {s}{(" " + unit) if unit else ""}')


def section(t):
    print()
    print('=' * 100)
    print(t)
    print('=' * 100)


def main(zdir=None):
    print('tools/review/e9_recompute.py - E9 review of L8 (oxide overlayer); all lengths in A unless stated')
    section('A. Constants (CODATA 2018 / SI-2019; docs/physics_conventions.md)')
    pr('lambda(200 keV)', LAM, '{:.8f}', 'A')
    pr('k = 2 pi/lambda', K, '{:.4f}', 'rad/A')
    pr('sigma(200 keV)', SIG, '{:.7e}', 'rad V^-1 A^-1')
    pr('K_F = h^2/(2 pi m0 e)', K_F, '{:.5f}', 'V A^2')
    pr('theta (B32)', THETA * 1e3, '{:.4f}', 'mrad')
    pr('k_perp = k sin(theta)', KPERP, '{:.5f}', 'rad/A')
    pr('path factor 2/sin(theta)', 2 / math.sin(THETA), '{:.3f}')
    pr('2 k sigma (k_perp^2 shift per volt)', 2 * K * SIG, '{:.6f}', 'A^-2 V^-1')
    pr('k^2 Delta per volt (exact, at 10.34 V)/10.34', K ** 2 * delta_exact(10.34, T) / 10.34, '{:.6f}', 'A^-2 V^-1')

    section('B. Electronic absorptive potential V\' = 1/(2 sigma Lambda) and r = V\'/V0 (L8 1.3, 8)')
    lams = {'Lee 2000 a-SiO2, no obj. aperture (178 nm)': 1780.0,
            'Iakoubovskii 2008 SiO2 (crystalline) x 1.1 (170.5 nm)': 1550.0 * 1.1,
            'Iakoubovskii 2008 SiO2 (crystalline, 155 nm)': 1550.0,
            'Lee 2000 lower 1-sigma (174 nm)': 1740.0, 'Lee 2000 upper 1-sigma (182 nm)': 1820.0}
    vp = {}
    for name, L in lams.items():
        vp[name] = 1 / (2 * SIG * L)
        pr(f"V' for Lambda = {L:.1f} A [{name}]", vp[name], '{:.4f}', 'V')
    for V0 in (10.1, 10.34, 10.8, 11.5):
        rs = [1 / (2 * SIG * L) / V0 for L in (1780.0, 1705.0, 1550.0)]
        pr(f"r = V'/V0 at V0 = {V0} V for Lambda = 1780 / 1705 / 1550 A", rs, '{:.4f}')
    pr("r at the nominal 0.40 V / 10.34 V", 0.40 / 10.34, '{:.4f}')
    pr("r range 0.385 V/11.5 V .. 0.443 V/10.1 V", [0.385 / 11.5, 0.443 / 10.1], '{:.4f}')

    section('C. Refraction into the oxide (exact relativistic Delta; parallel k conserved)')
    for V in (10.0, 10.1, 10.34, 10.8, 11.5, 11.9, 12.0, 13.6, 13.903):
        d = delta_exact(V, T)
        s2 = (math.sin(THETA) ** 2 + d) / (1 + d)
        kp = kperp_in(V).real
        pr(f'V = {V:6.3f} V: Delta, theta_in (mrad), k\'_perp (1/A), 2/sin(theta_in)',
           [d, math.asin(math.sqrt(s2)) * 1e3, kp, 2 / math.sqrt(s2)], '{:.6g}')

    section('D. Specular attenuation by a continuum layer, in + out (L8 3.3: "0.20-0.29 at 2 nm")')
    print('  intensity factor exp(-path/Lambda); path = 2t/sin(theta) (no refraction) or 2t/sin(theta_in);')
    print('  the "complex k" column is exp(-4 Im(k\'_perp) t) with k\'_perp for V + iV\' (exact form).')
    for t_nm in (1.0, 1.5, 2.0, 3.0):
        t = t_nm * 10
        for L in (1550.0, 1705.0, 1780.0):
            Vi = 1 / (2 * SIG * L)
            row = [math.exp(-2 * t / math.sin(THETA) / L)]
            for V in (10.1, 10.34, 11.5):
                d = delta_exact(V, T)
                s = math.sqrt((math.sin(THETA) ** 2 + d) / (1 + d))
                row.append(math.exp(-2 * t / s / L))
            row.append(math.exp(-4 * kperp_in(10.34, Vi).imag * t))
            pr(f't = {t_nm} nm, Lambda = {L:.0f} A: I(no refr.), I(V=10.1), I(10.34), I(11.5), I(complex k, 10.34 V)',
               row, '{:.4f}')
    # summary ranges
    for t_nm in (1.0, 2.0, 3.0):
        t = t_nm * 10
        refr = []
        for L in (1550.0, 1705.0, 1780.0):
            for V in (10.1, 11.5):
                d = delta_exact(V, T)
                s = math.sqrt((math.sin(THETA) ** 2 + d) / (1 + d))
                refr.append(math.exp(-2 * t / s / L))
        amorph = []
        for L in (1705.0, 1780.0):
            for V in (10.1, 11.5):
                d = delta_exact(V, T)
                s = math.sqrt((math.sin(THETA) ** 2 + d) / (1 + d))
                amorph.append(math.exp(-2 * t / s / L))
        norefr = [math.exp(-2 * t / math.sin(THETA) / L) for L in (1550.0, 1780.0)]
        pr(f't = {t_nm} nm: range with refraction (Lambda 1550-1780, V 10.1-11.5)', [min(refr), max(refr)], '{:.3f}')
        pr(f't = {t_nm} nm: range with refraction, amorphous Lambda only (1705-1780)', [min(amorph), max(amorph)], '{:.3f}')
        pr(f't = {t_nm} nm: range without refraction (Lambda 1550-1780)', [min(norefr), max(norefr)], '{:.3f}')
        pr(f't = {t_nm} nm: amplitude range with refraction', [math.sqrt(min(refr)), math.sqrt(max(refr))], '{:.3f}')
        pr(f't = {t_nm} nm: 1/intensity (reduction factor), with refraction', [1 / max(refr), 1 / min(refr)], '{:.2f}')
    print('  a-Si under the oxide, Lambda(Si) = 1450 A (Iakoubovskii Table I value for c-Si):')
    for t_nm in (1.0, 2.0, 3.0, 5.0):
        t = t_nm * 10
        row = [math.exp(-2 * t / math.sin(THETA) / 1450.0)]
        for V in (11.9, 13.6):
            d = delta_exact(V, T)
            s = math.sqrt((math.sin(THETA) ** 2 + d) / (1 + d))
            row.append(math.exp(-2 * t / s / 1450.0))
        pr(f'a-Si t = {t_nm} nm: I(no refr.), I(V = 11.9 V), I(V = 13.6 V)', row, '{:.4f}')
    print('  O1 (Lee 2000 p. 1130) validity of the bulk IMFP picture: t/Lambda > 0.1 (below it surface excitations')
    print('  are significant). Layer thickness normal to the surface over Lambda:')
    for t_nm in (1.0, 2.0, 3.0):
        pr(f't = {t_nm} nm: t/Lambda for Lambda = 1780 / 1550 A', [t_nm * 10 / 1780.0, t_nm * 10 / 1550.0], '{:.4f}')

    section('E. Phase consequences for the step measurement (E6 M4 formalism; exp(+ikr); magnitudes)')
    h4, h2 = A_SI / 4, A_SI / 2
    h4_l8 = 5.431 / 4
    pr('a/4, a/2 (a = 5.4309 A, B2)', [h4, h2], '{:.6f}', 'A')
    pr('conformal (or no) layer: step phase 2 k_perp h for a/4, a/2', [2 * KPERP * h4, 2 * KPERP * h2], '{:.4f}', 'rad')
    pr('same with a = 5.431 A (L7/L8 value)', [2 * KPERP * h4_l8, 2 * KPERP * 5.431 / 2], '{:.4f}', 'rad')
    pr('wrap period lambda/(2 sin theta)', LAM / (2 * math.sin(THETA)), '{:.4f}', 'A')
    for V in (10.0, 10.1, 10.34, 10.8, 11.5, 13.903):
        kp = kperp_in(V).real
        top = 2 * (kp - KPERP)
        proj = 2 * SIG * V / math.sin(THETA)
        pr(f'V = {V:6.3f}: top-surface term 2(k\'-k) (rad/A), projected 2 sigma V/sin (rad/A), apparent height per A',
           [top, proj, top / (2 * KPERP)], '{:.4f}')
        pr(f'V = {V:6.3f}: planarising a/4 phase 2 k\' h (a=5.4309 / 5.431), excess over conformal (rad), apparent height excess (A)',
           [2 * kp * h4, 2 * kp * h4_l8, 2 * (kp - KPERP) * h4, (kp - KPERP) * h4 / KPERP], '{:.4f}')
    print('  GROWN oxide: a thickness difference dt between two terraces consumes f*dt more Si (the interface')
    print('  drops by f*dt) and raises the top by (1-f)*dt. Extra step phase = [2 k\' - 2 k (1-f)] dt;')
    print('  apparent height per A of oxide = f + (k\'/k - 1). f from section F.')
    for f in (0.4215, 0.4416, 0.4618):
        for V in (10.1, 10.34, 11.5):
            kp = kperp_in(V).real
            per = 2 * kp - 2 * KPERP * (1 - f)
            app = per / (2 * KPERP)
            pr(f'f = {f}, V = {V}: rad per A of dt, apparent A per A, dt for 0.01 rad (A), dt for 0.1 A height (A)',
               [per, app, 0.01 / per, 0.1 / app], '{:.5f}')
    print('  top-surface-only variation (deposited layer, density change, contamination; interface fixed):')
    for V in (10.1, 10.34, 11.5):
        kp = kperp_in(V).real
        per = 2 * (kp - KPERP)
        pr(f'V = {V}: dt for 0.01 rad (A), dt for 0.1 A apparent height (A)', [0.01 / per, 0.1 / (per / (2 * KPERP))], '{:.5f}')
    print('  one extra CONSUMED Si layer (a/4) on one terrace: oxide dt = (a/4)/f; interface step changes by a/4;')
    for f in (0.4416,):
        dt = h4 / f
        for V in (10.34,):
            kp = kperp_in(V).real
            pr(f'f = {f}, V = {V}: dt (A), top-surface shift (1-f)dt (A), extra phase (rad), in units of the a/4 phase',
               [dt, (1 - f) * dt, (2 * kp - 2 * KPERP * (1 - f)) * dt, (2 * kp - 2 * KPERP * (1 - f)) * dt / (2 * KPERP * h4)],
               '{:.4f}')
    print('  number of Si layers consumed under a conformal oxide, 0.4416 t_ox/(a/4):')
    for t_nm in (1.0, 1.5, 2.0, 3.0):
        pr(f't_ox = {t_nm} nm: consumed depth (A), layers', [0.4416 * t_nm * 10, 0.4416 * t_nm * 10 / h4], '{:.3f}')

    section('F. Si consumed per oxide thickness (Si atoms conserved; L8 3.3 "0.44 t_ox")')
    rho_si = 8 * M_SI / NA / (A_SI * 1e-8) ** 3
    rho_si_l8 = 8 * M_SI / NA / (5.431e-8) ** 3
    pr('rho(c-Si) at a = 5.4309 / 5.431 A', [rho_si, rho_si_l8], '{:.4f}', 'g/cm^3')
    for rho in (2.07, 2.10, 2.18, 2.183, 2.20, 2.27, 2.28, 2.30, 2.311):
        f = (rho / M_SIO2) / (rho_si / M_SI)
        pr(f'rho_ox = {rho}: f = d_Si/t_ox, volume expansion 1/f, interface drop and top rise for 2 nm (A)',
           [f, 1 / f, 20 * f, 20 * (1 - f)], '{:.4f}')

    section('G. Kirkland independent-atom mean inner potential of SiO2 (abTEM 1.0.10 parameter table)')
    import abtem
    pdir = os.path.join(os.path.dirname(abtem.__file__), 'parametrizations', 'data', 'kirkland.json')
    table = json.load(open(pdir))
    print(f'  abTEM version {abtem.__version__}; table {pdir}')
    f0 = {}
    for el in ('Si', 'O'):
        p = np.array(table[el])      # rows: a_i, b_i, c_i, d_i (Kirkland 2010 App. C ordering a1 b1 a2 b2 ... as rows)
        a, b, c, d = p
        f0[el] = float(np.sum(a / b) + np.sum(c))
        pr(f'{el}: a = {a.tolist()}, b = {b.tolist()}, c = {c.tolist()}, d = {d.tolist()}; f_e(0) = sum a/b + sum c', f0[el], '{:.7f}', 'A')
        pr(f'{el}: integral of V d^3r = K_F f_e(0)', K_F * f0[el], '{:.4f}', 'V A^3')
    # black-box checks: abTEM's own function at k = 0, and a real-space radial integral of abTEM's V(r)
    from abtem.parametrizations import KirklandParametrization
    kp_ = KirklandParametrization()
    for el in ('Si', 'O'):
        fk = kp_.scattering_factor(el)(np.array([0.0]))[0]
        V = kp_.potential(el)
        r = np.concatenate([np.linspace(1e-6, 0.05, 20001), np.linspace(0.05, 40.0, 400001)[1:]])
        integ = np.trapezoid(4 * np.pi * r ** 2 * V(r), r)
        pr(f'{el}: abTEM scattering_factor(k=0) (black box), abTEM potential radial integral (V A^3)', [fk, integ], '{:.5f}')
    per_fu = K_F * (f0['Si'] + 2 * f0['O'])
    pr('K_F (f_Si + 2 f_O) per SiO2 formula unit', per_fu, '{:.4f}', 'V A^3')
    for rho in (2.07, 2.10, 2.18, 2.183, 2.20, 2.27, 2.30, 2.311):
        n = rho / M_SIO2 * NA * 1e-24
        pr(f'rho = {rho}: n_SiO2 (1/A^3), V0(IAM)', [n, n * per_fu], '{:.5f}')
    n220 = 2.20 / M_SIO2 * NA * 1e-24
    pr('dV0/drho (V per g/cm^3) and for +-0.1 g/cm^3', [n220 * per_fu / 2.20, 0.1 * n220 * per_fu / 2.20], '{:.4f}')
    pr('Si check: 8 K_F f_Si / a^3 (a = 5.4309 A; B32 13.903 V)', 8 * K_F * f0['Si'] / A_SI ** 3, '{:.4f}', 'V')
    pr('measured a-SiO2: 10.1 +- 0.6 V (Wang 1997 via C02 p. 772), 11.5 +- 0.3 V (Lee 2000 p. 1131); difference, combined 1-sigma, ratio',
       [11.5 - 10.1, math.hypot(0.6, 0.3), (11.5 - 10.1) / math.hypot(0.6, 0.3)], '{:.3f}')
    pr('IAM(2.20) minus 10.1 V and minus 11.5 V', [n220 * per_fu - 10.1, n220 * per_fu - 11.5], '{:.3f}', 'V')

    section('H. Yamamura-Tawara threshold (NIFS-DATA-23 p. 7 Eq. (18), p. 8 Eq. (19), Table 1 p. 14: U_s(Si) = 4.63 eV)')
    US = 4.63

    def eth(m1, m2, us):
        g = 4 * m1 * m2 / (m1 + m2) ** 2
        return (6.7 / g if m1 >= m2 else (1 + 5.7 * m1 / m2) / g) * us, g
    for name, m1 in (('Ar', M_AR), ('O', M_O), ('O (M = 16.00)', 16.00), ('Ar (M = 39.95)', 39.95)):
        e_, g = eth(m1, M_SI, US)
        pr(f'{name} on Si: gamma, E_th', [g, e_], '{:.4f}', '(E_th in eV)')
    e_o, _ = eth(M_O, M_SI, US)
    pr('O2+ ion splitting into two O at equal energy: threshold per ion 2 E_th(O)', 2 * e_o, '{:.2f}', 'eV')

    section('I. Periodic tiling of an amorphous cube of side L (L8 5.3: "0.195 mrad inside the 3 mrad aperture")')
    for L in (128.716, 168.390, 10.8577):
        trans = LAM / L
        # period ALONG the beam (in-plane, z): theta_out^2 + phi_out^2 = theta^2 + 2 n lambda / L (small angles)
        r1 = math.sqrt(THETA ** 2 + 2 * LAM / L)
        pr(f'L = {L} A: transverse (across-beam) rod spacing lambda/L (mrad); along-beam n=-1 Laue circle radius (mrad), '
           f'its closest approach to the specular spot (mrad); n=+1 exists?',
           [trans * 1e3, r1 * 1e3, (r1 - THETA) * 1e3, float(THETA ** 2 - 2 * LAM / L > 0)], '{:.4f}')
    # along-beam period that brings the n=-1 circle within 3 mrad of the specular spot
    pr('along-beam period L above which the n=-1 circle enters a 3 mrad aperture (A)',
       2 * LAM / ((THETA + 3e-3) ** 2 - THETA ** 2), '{:.1f}')
    pr('H2 transverse cell width 86.9 A (16 x a/sqrt2 x ...): own rod spacing lambda/W (mrad)', LAM / 86.9 * 1e3, '{:.4f}')

    section('J. Si inelastic MFP -> V\' (L8 1.3 cross-check of B6 (ii))')
    for L, lab in ((1450.0, 'c-Si total, Iakoubovskii Table I (calibration value)'), (1680.0, 'c-Si plasmon part, Iakoubovskii Table I'),
                   (1050.0, 'Mendis 2019 plasmon MFP as stated by Mendis 2024 (UNVERIFIED)'), (830.0, 'Malis estimate in Mendis 2024')):
        pr(f"Lambda = {L:.0f} A [{lab}]: V'", 1 / (2 * SIG * L), '{:.4f}', 'V')

    section('K. Lee et al. 2000 phase check (p. 1131: 2.73 pi at t = 113 nm, holography at 300 kV)')
    s300 = sigma_per_VA(300e3) * 10
    pr('sigma(300 keV)', s300, '{:.6e}', 'rad V^-1 nm^-1')
    pr('sigma U t for U = 11.5 V, t = 113 nm (rad, units of pi)', [s300 * 11.5 * 113, s300 * 11.5 * 113 / math.pi], '{:.4f}')
    pr('U implied by 2.73 pi at 113 nm', 2.73 * math.pi / (s300 * 113), '{:.3f}', 'V')

    section('L. E9 figure readings (E9 digitisation of the rendered figures; DERIVED_HERE, reading uncertainty stated)')
    kit = {'a (200 W)': (1.45, 3.42), 'b (300 W)': (2.26, 4.01), 'c (500 W)': (2.71, 4.01)}
    print('  Kitajima 1994 Fig. 16 (p. 823), delta-Delta in degrees at 600 s and at ~9900 s; reading +-0.1 deg:')
    for k_, (a6, a99) in kit.items():
        pr(f'curve {k_}: dD(600 s), dD(9900 s), fraction, bound on thickness at 600 s if linear (nm, x <1.5 nm)',
           [a6, a99, a6 / a99, 1.5 * a6 / a99], '{:.3f}')
    rob = [(0.20, -8.2), (0.42, -10.1), (0.94, -7.6), (1.31, -9.4), (1.98, -6.9), (2.97, -9.0), (3.98, -5.7),
           (6.01, -5.4), (7.97, -4.7), (9.99, -4.05), (11.93, -1.35), (15.95, -2.4)]
    print('  Robinson et al. 2004 Fig. 4 (p. 372), change in apparent thickness (A) vs minutes; reading +-0.3 A:')
    print('   ' + '; '.join(f'{t:.2f} min {d:+.2f}' for t, d in rob))
    early = [d for t, d in rob if t < 3.5]
    pr('early points (0.2-3 min): min, max', [min(early), max(early)], '{:.2f}', 'A')
    pr('growth at 10 min relative to early min/max (A)', [-4.05 - min(early), -4.05 - max(early)], '{:.2f}')
    pr('growth at 12 and 16 min relative to early min/max (A)', [-1.35 - min(early), -1.35 - max(early), -2.4 - min(early), -2.4 - max(early)], '{:.2f}')

    section('M. Oxide-thickness routes after the 10 min clean (L8 2.3 and 8)')
    pr('XPS thermal-oxide-equivalent route: native 0.5-1.0 nm (Morita Fig. 1) + plasma 0.4-1.0 nm', [0.5 + 0.4, 1.0 + 1.0], '{:.1f}', 'nm')
    pr('same with the n-Si subset 0.5-0.8 nm', [0.5 + 0.4, 0.8 + 1.0], '{:.1f}', 'nm')
    pr('ellipsometric route: native 1.6-1.9 nm (Robinson p. 370) + plasma 0.4-1.0 nm', [1.6 + 0.4, 1.9 + 1.0], '{:.1f}', 'nm')
    pr('union of both routes, midpoint', [0.9, 2.9, (0.9 + 2.9) / 2], '{:.2f}', 'nm')
    pr('P4-only plasma growth (0.4-0.6 nm) on the XPS route', [0.5 + 0.4, 1.0 + 0.6], '{:.1f}', 'nm')

    section('N. Specular Fresnel reflection of the continuum layer itself (vacuum/oxide and oxide/Si steps)')
    for Vox in (10.1, 10.34, 11.5):
        k1 = KPERP
        k2 = kperp_in(Vox).real
        k3 = kperp_in(13.903).real
        r12 = (k1 - k2) / (k1 + k2)
        r23 = (k2 - k3) / (k2 + k3)
        pr(f'V_ox = {Vox}: r(vac/ox), |r|^2, r(ox/Si at 13.903 V), |r|^2, (1-r12^2)^2', [r12, r12 ** 2, r23, r23 ** 2, (1 - r12 ** 2) ** 2], '{:.5f}')

    section('O. Zenodo 10.5281/zenodo.10419194 structures (E9 extraction; minimum-image, all Si atoms)')
    if zdir and os.path.isdir(zdir):
        from scipy.spatial import cKDTree
        for fname in ('ace_4.in.data', 'hybrid.out.data'):
            path = os.path.join(zdir, fname)
            if not os.path.exists(path):
                print(f'  {fname}: not found in {zdir}')
                continue
            lines = open(path).read().splitlines()
            natoms = int(next(l for l in lines if l.strip().endswith('atoms')).split()[0])
            lo_hi = [l.split()[:2] for l in lines if l.strip().endswith(('xlo xhi', 'ylo yhi', 'zlo zhi'))]
            lo = np.array([float(x[0]) for x in lo_hi]); hi = np.array([float(x[1]) for x in lo_hi])
            tilt = [l for l in lines if 'xy xz yz' in l]
            im = lines.index(next(l for l in lines if l.startswith('Masses')))
            masses = {}
            j = im + 1
            while not lines[j].strip():
                j += 1
            while lines[j].strip():
                t_, m_ = lines[j].split()[:2]; masses[int(t_)] = float(m_); j += 1
            ia = lines.index(next(l for l in lines if l.startswith('Atoms')))
            j = ia + 1
            while not lines[j].strip():
                j += 1
            data = np.array([list(map(float, l.split()[:5])) for l in lines[j:j + natoms]])
            typ = data[:, 1].astype(int); pos = data[:, 2:5]
            Lb = hi - lo
            vol = float(np.prod(Lb))
            mass = sum(masses[t_] * np.sum(typ == t_) for t_ in masses)
            rho = mass / NA / (vol * 1e-24)
            o_t = min(masses, key=lambda t_: masses[t_]); si_t = max(masses, key=lambda t_: masses[t_])
            nO, nSi = int(np.sum(typ == o_t)), int(np.sum(typ == si_t))
            print(f'  {fname}: {natoms} atoms, masses {masses}, tilt lines {len(tilt)}, box {Lb.tolist()} A')
            pr('N_Si, N_O, O/Si, density (g/cm^3)', [nSi, nO, nO / nSi, rho], '{:.5g}')
            wrapped = (pos - lo) % Lb
            tO = cKDTree(wrapped[typ == o_t], boxsize=Lb)
            si = wrapped[typ == si_t]
            for rc in (1.9, 2.0, 2.2, 2.4):
                nb = tO.query_ball_point(si, rc, return_length=True)
                frac4 = float(np.mean(nb == 4))
                pr(f'Si-O cutoff {rc} A: mean coordination, fraction fourfold, fraction 3, fraction 5',
                   [float(np.mean(nb)), frac4, float(np.mean(nb == 3)), float(np.mean(nb == 5))], '{:.4f}')
            dd, _ = tO.query(si, k=4)
            pr('mean and s.d. of the 4 nearest Si-O distances (A)', [float(dd.mean()), float(dd.std())], '{:.4f}')
            n = nSi / (vol)  # per A^3
            V0 = (nSi * K_F * f0['Si'] + nO * K_F * f0['O']) / vol
            pr('IAM V0 of this model (V)', V0, '{:.4f}')
    else:
        print('  skipped (no ZENODO_DIR given)')

    section('P. Combination with B38 (surface-plasmon zero-loss fraction exp(-1.246) of E6/B38)')
    zl_sp = math.exp(-1.246)
    pr('B38 zero-loss fraction (clean Si(111)7x7 transfer, not an oxide-covered surface)', zl_sp, '{:.4f}')
    for Iox in (0.24, 0.27, 0.29):
        pr(f'product with an oxide factor {Iox}', zl_sp * Iox, '{:.4f}')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None)
