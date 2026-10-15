"""
constants.py
============
Physical constants, Si crystal parameters, detector calibration,
and CL3 beam tilt calibration matrix for the HF-3300 at 200 kV.
"""

import numpy as np

# ── fundamental constants ─────────────────────────────────────────────────────
HBAR = 1.054571817e-34      # J s
M_E = 9.1093837015e-31      # kg (electron rest mass)
E_CHARGE = 1.602176634e-19  # C
C_LIGHT = 2.99792458e8      # m/s
M_E_EV = 510998.950         # eV/c^2 (electron rest mass energy)

# ── beam parameters at 200 kV ────────────────────────────────────────────────
VOLTAGE_KV = 200.0
VOLTAGE_V = VOLTAGE_KV * 1e3

# relativistic wavelength: lambda = h / sqrt(2 m_0 eV (1 + eV / 2 m_0 c^2))
LAMBDA_200KV = 0.025079     # Angstroms (relativistic)
K_200KV = 2 * np.pi / LAMBDA_200KV  # 250.5 A^-1

# relativistic correction
RELATIVISTIC_GAMMA = 1.0 + VOLTAGE_V * E_CHARGE / (M_E * C_LIGHT**2)  # 1.3914
RELATIVISTIC_MASS = M_E * RELATIVISTIC_GAMMA

# ── Si diamond cubic structure ────────────────────────────────────────────────
SI_LATTICE_PARAM = 5.43102  # Angstroms (room temperature)
SI_UNIT_CELL_VOLUME = SI_LATTICE_PARAM**3  # 160.18 A^3

# 8 atom positions in conventional cell (fractional coordinates)
# FCC basis: (0,0,0), (1/2,1/2,0), (1/2,0,1/2), (0,1/2,1/2)
# + diamond shift (1/4,1/4,1/4) for each
SI_ATOM_POSITIONS = np.array([
    [0.00, 0.00, 0.00],
    [0.50, 0.50, 0.00],
    [0.50, 0.00, 0.50],
    [0.00, 0.50, 0.50],
    [0.25, 0.25, 0.25],
    [0.75, 0.75, 0.25],
    [0.75, 0.25, 0.75],
    [0.25, 0.75, 0.75],
])

# Debye-Waller B factor for Si at 300 K
SI_DEBYE_WALLER_B = 0.4632  # A^2

# Mean inner potential
SI_MEAN_INNER_POTENTIAL_V = 12.0   # Volts (real part)
SI_ABSORPTIVE_POTENTIAL_V = 0.9    # Volts (imaginary part, approximate)

# Electron scattering factor parameterization for Si
# Peng, Ren, Dudarev, Whelan, Acta Cryst. A52, 257 (1996)
# f_e(s) = sum_i a_i * exp(-b_i * s^2), s = |G|/(4*pi) = sin(theta)/lambda
SI_SCATTERING_A = np.array([2.1293, 2.5333, 0.8349, 0.3216, 0.0862])
SI_SCATTERING_B = np.array([57.7748, 16.4756, 2.8796, 0.3860, 0.0120])

# ── [110] zone axis coordinate system ────────────────────────────────────────
# z_hat = beam direction = [110]/sqrt(2)
# x_hat = [1-10]/sqrt(2)  (horizontal on detector)
# y_hat = z x x = [0,0,-1] -> use [001] with sign convention
ZONE_AXIS = np.array([1, 1, 0], dtype=float)
ZA_Z = ZONE_AXIS / np.linalg.norm(ZONE_AXIS)          # [110]/sqrt(2)
ZA_X = np.array([1, -1, 0], dtype=float) / np.sqrt(2)  # [1-10]/sqrt(2)
ZA_Y = np.cross(ZA_Z, ZA_X)                             # [001] or [00-1]

# Cleaved surface normal (outward, pointing away from crystal).
# The beam is along [110]. The cleaved edge exposes a {111} plane.
# Two {111} variants are parallel to [110]: (1-11) and (-11-1).
# The CL3 beam tilt (BTX=-814, BTY=135) pushes k_i such that
# k_i . [1,-1,1] > 0, meaning the beam moves TOWARD the [1,-1,1]
# direction. For the beam to enter the crystal, the crystal must be
# on the [1,-1,1] side, so the OUTWARD normal (toward vacuum) is
# [-1,1,-1]/sqrt(3).
SURFACE_NORMAL = np.array([-1, 1, -1], dtype=float) / np.sqrt(3)

# verification: beam direction [110] is IN the surface plane
_VERIFY_ORTHOGONAL = np.dot(ZA_Z, SURFACE_NORMAL)
assert abs(_VERIFY_ORTHOGONAL) < 1e-10, (
    f"Surface normal not perpendicular to zone axis: dot = {_VERIFY_ORTHOGONAL}"
)

# ── detector parameters ───────────────────────────────────────────────────────
DETECTOR_SHAPE = (256, 256)
DETECTOR_CENTER = (128.0, 128.0)
PIXEL_SIZE_UM = 55.0         # Merlin/Medipix3 pixel pitch
CAMERA_LENGTH_MM = 500.0
ANGULAR_SCALE = 0.110        # mrad/pixel at CL=500 mm

# ── CL3 beam tilt calibration ────────────────────────────────────────────────
# from beam_tilt_calibration_formulas.pdf, Eqs. 21-26
# theta = A @ (BT - BT_ref) + b
# where theta = (theta_x, theta_y) in mrad, BT = (BTX, BTY) in DAC units
BT_REFERENCE = np.array([-67.0, -444.0])  # (BTX_ref, BTY_ref) DAC
BT_CALIBRATION_MATRIX = np.array([
    [-0.027097, +0.057162],
    [-0.056622, -0.027624],
])  # mrad per DAC unit
BT_CALIBRATION_OFFSET = np.array([-0.178, +0.431])  # mrad
