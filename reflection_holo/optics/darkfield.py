"""Dark-field selection of one reflected beam in k-space (docs/05 section 5 item 1; docs/03 section 1).

"Dark-field" means that the image is formed from ONE selected reflected beam: the objective aperture,
of semi-angle alpha (PROJECT_INPUT item 4, REQUIRED, no default), is centred on the direction of the
selected beam k_out. Only the specular beam is implemented (k_out = k (sin theta_out, 0,
cos theta_out) in the slab frame: x outward normal, y transverse, z beam azimuth).

Procedure (DERIVED_HERE; numpy FFT sign, exp(+ik.r) convention, docs/physics_conventions.md):

1. Fourier transform of the exit-plane wave psi(x, y) on its declared grid (pixel sizes and origin
   read from the ExitWave and asserted). A Fourier component (q_x, q_y) (cycles/A) is the plane
   wave of direction d = (lambda q_x, lambda q_y, sqrt(1 - lambda^2 |q|^2)) (evanescent components,
   lambda |q| >= 1, are blocked).
2. Aperture: pass the components whose direction lies within alpha of k_out, i.e.
   angle(d, k_out_hat) = 2 asin(|d - k_out_hat| / 2) <= alpha (exact angular disc, not a paraxial
   disc). The disc must lie inside the band the wave can carry: the Nyquist band of the grid, and
   the engine's declared band limit if its metadata gives one (``band_limit_cycles_per_A``).
3. Demodulation: multiply by exp(-2 pi i q_out x) with q_out = sin(theta_out)/lambda (cycles/A) at
   the ABSOLUTE exit-plane coordinate x = x0_A + i dx_A, i.e. remove the transverse carrier of k_out.
   The constant phase exp(i k_z z) of the plane is not touched (the engine declares its convention;
   a constant is common to object and empty holograms).

The aperture centre, radius, number of passing bins, the demodulation frequency and the engine's
band limit are recorded with the result.

Azimuthally tilted illumination (convergence member, report E3): an exit wave whose metadata
carries ``bloch`` (forward.multislice.illumination) is the Bloch envelope u of the physical wave
u exp(2 pi i f_y y). The aperture stays FIXED in the microscope (centred on the central k_out given by
the caller); it is applied to the physical directions (lambda q_x, lambda (q_y + f_y), ...) of the
envelope's components, and the selected wave is returned as an envelope with the same f_y
(``record["bloch_fy_per_A"]``; the caller multiplies by exp(2 pi i f_y y) after any periodic
resampling). For f_y = 0 (no ``bloch`` record) the computation is unchanged.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from reflection_holo.constants import BEAM_ENERGY_SUPPLIED_KEV
from reflection_holo.forward.contracts import ExitWave
from reflection_holo.geometry.wavelength import wavelength_A
from reflection_holo.io.labels import require_evidence_label
from reflection_holo.optics.fields import Grid, Wave

SELECTABLE_BEAMS = ("specular",)
_LABELS = ("PROJECT_INPUT", "ASSUMPTION", "TEST_ONLY")


@dataclass(frozen=True)
class DarkFieldAperture:
    """Objective aperture of the dark-field image (PROJECT_INPUT item 4). No defaults.

    semi_angle_rad  aperture semi-angle alpha (rad), > 0
    beam            the reflected beam it selects; only "specular" is implemented
    label           evidence label (PROJECT_INPUT ..., ASSUMPTION B.., TEST_ONLY ...)
    """
    semi_angle_rad: float
    beam: str
    label: str

    def __post_init__(self):
        a = float(self.semi_angle_rad)
        if not (np.isfinite(a) and 0.0 < a < 0.5 * np.pi):
            raise ValueError(f"semi_angle_rad must lie in (0, pi/2), got {self.semi_angle_rad!r}")
        object.__setattr__(self, "semi_angle_rad", a)
        if self.beam not in SELECTABLE_BEAMS:
            raise NotImplementedError(f"beam {self.beam!r}: only {SELECTABLE_BEAMS} is implemented")
        require_evidence_label(self.label, "objective aperture (PROJECT_INPUT item 4)",
                               accepted=_LABELS, qualified=True)


@dataclass(frozen=True, eq=False)
class DarkFieldResult:
    """Demodulated dark-field wave on the exit-plane grid (axes x, y) with its origin."""
    wave: Wave
    x0_A: float
    y0_A: float
    z_A: float
    theta_out_ext_rad: float
    energy_keV: float
    record: dict = field(default_factory=dict)


def validate_exit_wave(ew: ExitWave, *, energy_keV: float, theta_in_ext_rad: float,
                       rtol_angle: float = 0.0) -> None:
    """Assert what the pipeline reads from an ExitWave: a 2-D complex array, finite positive pixel
    sizes and finite origins READ FROM THE WAVE, a declared plane, the beam energy (200 keV) and
    the glancing angle actually used (equal to the requested one to ``rtol_angle``)."""
    if not isinstance(ew, ExitWave):
        raise TypeError(f"expected an ExitWave, got {type(ew).__name__}")
    psi = np.asarray(ew.psi)
    if psi.ndim != 2 or not np.iscomplexobj(psi) or min(psi.shape) < 2:
        raise ValueError(f"ExitWave.psi must be a 2-D complex array (x, y); got {psi.dtype} "
                         f"{psi.shape}")
    if not np.all(np.isfinite(psi)):
        raise ValueError("ExitWave.psi has non-finite values")
    for name in ("dx_A", "dy_A"):
        v = getattr(ew, name)
        if v is None or not (np.isfinite(float(v)) and float(v) > 0):
            raise ValueError(f"ExitWave.{name} must be a finite positive pixel size, got {v!r}")
    for name in ("x0_A", "y0_A", "z_A"):
        v = getattr(ew, name)
        if v is None or not np.isfinite(float(v)):
            raise ValueError(f"ExitWave.{name} must be finite, got {v!r}")
    if not isinstance(ew.plane, str) or not ew.plane.strip():
        raise ValueError("ExitWave.plane must declare the plane of the wave")
    if float(ew.energy_keV) != BEAM_ENERGY_SUPPLIED_KEV or float(energy_keV) != BEAM_ENERGY_SUPPLIED_KEV:
        raise ValueError(f"beam energy {ew.energy_keV} keV refused: {BEAM_ENERGY_SUPPLIED_KEV:g} keV "
                         f"(PROJECT_INPUT item 1)")
    th, want = float(ew.theta_in_ext_rad), float(theta_in_ext_rad)
    if not abs(th - want) <= rtol_angle * abs(want):
        raise ValueError(f"ExitWave was computed at theta_in = {th!r} rad, the run requests "
                         f"{want!r} rad")
    if ew.realisation is None or int(ew.realisation) != ew.realisation:
        raise ValueError("ExitWave.realisation must be an integer")


def _directions(nx: int, ny: int, dx: float, dy: float, lam: float, fy_shift: float = 0.0):
    qx = np.fft.fftfreq(nx, dx)
    qy = np.fft.fftfreq(ny, dy) + fy_shift          # physical frequencies of a Bloch envelope
    QX, QY = np.meshgrid(qx, qy, indexing="ij")
    s2 = (lam * QX) ** 2 + (lam * QY) ** 2
    prop = s2 < 1.0
    dz = np.sqrt(np.where(prop, 1.0 - s2, 0.0))
    return QX, QY, lam * QX, lam * QY, dz, prop


def select_dark_field(exit_wave: ExitWave, aperture: DarkFieldAperture, *, energy_keV: float,
                      theta_out_ext_rad: float) -> DarkFieldResult:
    """Aperture centred on k_out and demodulation of its carrier (module docstring).

    theta_out_ext_rad is the external exit angle of the selected beam (for the specular beam, the
    glancing angle of incidence; PROJECT_INPUT item 7), required.
    """
    if not isinstance(aperture, DarkFieldAperture):
        raise TypeError("aperture must be a DarkFieldAperture (PROJECT_INPUT item 4)")
    th = float(theta_out_ext_rad)
    if not (np.isfinite(th) and 0.0 < th < 0.5 * np.pi):
        raise ValueError(f"theta_out_ext_rad must lie in (0, pi/2), got {theta_out_ext_rad!r}")
    validate_exit_wave(exit_wave, energy_keV=energy_keV, theta_in_ext_rad=exit_wave.theta_in_ext_rad)
    lam = wavelength_A(energy_keV)
    psi = np.asarray(exit_wave.psi, dtype=np.complex128)
    nx, ny = psi.shape
    dx, dy = float(exit_wave.dx_A), float(exit_wave.dy_A)
    alpha = aperture.semi_angle_rad
    q_out = math.sin(th) / lam
    bloch = (exit_wave.metadata or {}).get("bloch") if exit_wave.metadata else None
    fb = 0.0 if not bloch else float(bloch["fy_per_A"])
    if not math.isfinite(fb):
        raise ValueError("the exit wave's Bloch frequency must be finite")
    # band checks: the aperture disc must be representable on the grid (for a Bloch envelope the
    # aperture sits at native q_y = -f_y)
    q_hi_x = math.sin(th + alpha) / lam
    q_hi_y = abs(fb) + math.sin(alpha) / lam
    if q_hi_x >= 0.5 / dx or q_hi_y >= 0.5 / dy:
        raise ValueError(f"the aperture (centre {q_out:.4f} cycles/A, semi-angle {alpha * 1e3:.3f} "
                         f"mrad) reaches ({q_hi_x:.4f}, {q_hi_y:.4f}) cycles/A, beyond the Nyquist "
                         f"band ({0.5 / dx:.4f}, {0.5 / dy:.4f}) of the exit-plane grid")
    band = exit_wave.metadata.get("band_limit_cycles_per_A") if exit_wave.metadata else None
    if isinstance(band, (int, float)) and not isinstance(band, bool):
        if math.hypot(q_hi_x, 0.0) >= float(band) or q_hi_y >= float(band):
            raise ValueError(f"the aperture reaches {q_hi_x:.4f} cycles/A, beyond the engine's "
                             f"declared band limit {float(band):.4f} cycles/A")
    QX, QY, dxl, dyl, dzl, prop = _directions(nx, ny, dx, dy, lam, fb)
    kx, kz = math.sin(th), math.cos(th)
    chord = np.sqrt((dxl - kx) ** 2 + dyl ** 2 + (dzl - kz) ** 2)
    ang = 2.0 * np.arcsin(np.clip(0.5 * chord, 0.0, 1.0))
    passed = prop & (ang <= alpha)
    n_pass = int(passed.sum())
    if n_pass == 0:
        raise ValueError("no Fourier component of the exit-plane grid lies inside the aperture")
    F = np.fft.fft2(psi)
    w = np.fft.ifft2(np.where(passed, F, 0.0))
    x = float(exit_wave.x0_A) + dx * np.arange(nx)
    w = w * np.exp(-2j * np.pi * q_out * x)[:, None]
    power_in = float(np.sum(np.abs(F) ** 2))
    power_pass = float(np.sum(np.abs(F[passed]) ** 2))
    grid = Grid(shape=(nx, ny), pixel_size_A=(dx, dy), axes=("x", "y"),
                plane=f"{exit_wave.plane}; dark-field selected ({aperture.beam}) and demodulated")
    record = dict(
        beam=aperture.beam, semi_angle_rad=alpha, label=aperture.label,
        aperture_centre_cycles_per_A=[q_out, 0.0],
        aperture_centre_direction_slab=[kx, 0.0, kz],
        aperture_definition="angle(d, k_out_hat) <= alpha, d the unit direction of each Fourier "
                            "component; evanescent components blocked",
        aperture_radius_paraxial_cycles_per_A=math.sin(alpha) / lam,
        n_bins_passed=n_pass, n_bins_total=int(nx * ny),
        fraction_of_power_passed=(power_pass / power_in) if power_in > 0 else None,
        demodulation="multiplied by exp(-2 pi i q_out x), x absolute exit-plane coordinate; "
                     "exp(i k_z z) untouched",
        demodulation_frequency_cycles_per_A=q_out,
        engine_band_limit_cycles_per_A=band, wavelength_A=lam, theta_out_ext_rad=th,
        bloch_fy_per_A=fb,
        bloch_note=("the selected wave is the Bloch envelope of an azimuthally tilted member: the "
                    "physical wave is this times exp(2 pi i bloch_fy_per_A y)" if fb else
                    "no azimuthal tilt"),
        exit_plane_grid=dict(shape=[nx, ny], dx_A=dx, dy_A=dy, x0_A=float(exit_wave.x0_A),
                             y0_A=float(exit_wave.y0_A), z_A=float(exit_wave.z_A),
                             plane=exit_wave.plane))
    wave = Wave(w, grid, f"dark-field wave ({aperture.beam}), realisation {exit_wave.realisation}",
                int(exit_wave.realisation), {"dark_field": record})
    return DarkFieldResult(wave=wave, x0_A=float(exit_wave.x0_A), y0_A=float(exit_wave.y0_A),
                           z_A=float(exit_wave.z_A), theta_out_ext_rad=th,
                           energy_keV=float(energy_keV), record=record)


def aperture_record(result: DarkFieldResult) -> dict[str, Any]:
    """The recorded aperture (docs/05 section 5 item 1)."""
    return dict(result.record)
