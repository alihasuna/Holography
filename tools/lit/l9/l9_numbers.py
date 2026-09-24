"""DERIVED_HERE numbers for L9 section 5 (detector-model recommendations).
Inputs: digitised D6 Fig. 8 curves (l9/digitise_paton_fig8.out), D6 Table 1, pitch 55 um (D1, D8),
theta = 16.1347 mrad (docs/model_assumptions B32, the (0,0,8) demo angle)."""
import math
w   = [0.2, 0.25, 0.3, 0.4, 0.5, 0.6]
mtf = [0.815, 0.728, 0.638, 0.453, 0.288, 0.167]     # mean of TH0 12.4 / 58.3 keV curves
dqe = [0.613, 0.544, 0.460, 0.302, 0.171, 0.086]     # TH0 12.4 keV
dqe0 = 0.80                                          # Table 1
print('NNPS(w) = DQE(0) MTF^2 / DQE  (D6 Eq. (6) rearranged):')
for a, m, d in zip(w, mtf, dqe):
    print(f'  w = {a:.2f} omega_N: NNPS = {dqe0*m*m/d:.3f}')
pitch_um = 55.0
theta = 16.1347e-3
print(f'1/sin(theta) = {1/math.sin(theta):.2f}')
for s_A, ppf in ((2.0, 8), (2.0, 4), (10.0, 8), (50.0, 8)):
    M = ppf * pitch_um * 1e4 / s_A          # pitch in A / (s/ppf)
    p_A = pitch_um * 1e4 / M
    print(f'carrier {s_A:5.1f} A at {ppf} px/fringe: M = {M:.3g}, specimen pixel {p_A:.3f} A, '
          f'surface along beam per pixel {p_A/math.sin(theta):.2f} A, 256 px span along beam {256*p_A/math.sin(theta)/1e4:.3f} um, '
          f'perpendicular {256*p_A/1e4:.4f} um')
# demo B23 translated to a 55 um pitch
print(f'B23 image pixel 0.5 A with 55 um pitch needs M = {55e4/0.5:.3g} (B23 states 15 um and M = 3.0e5)')
# phase-noise factors
for ppf in (4, 5, 6, 8, 10):
    a = 2/ppf
    d = [x for x in zip(w, dqe)]
    # linear interpolation in w
    import numpy as np
    D = float(np.interp(a, w, dqe)); Mt = float(np.interp(a, w, mtf))
    print(f'{ppf:2d} px/fringe: MTF {Mt:.3f}, DQE {D:.3f}, phase-noise factor vs ideal counting detector 1/sqrt(DQE) = {1/math.sqrt(D):.2f}')
# counts-per-frame budget
for bits in (6, 12, 24):
    print(f'{bits}-bit counter max per frame: {2**bits-1}')
