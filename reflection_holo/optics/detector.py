"""Detector: magnification and pixel mapping, gain and Poisson dose (docs/05 section 5 items 2, 6).

Inputs (all REQUIRED, no defaults):
* PROJECT_INPUT item 5: the physical detector pixel pitch (um, both axes) and the magnification M,
  and the specimen-referred image pixel size (both axes) of CFG-B's ``image_pixel_size``; the two
  must agree (pitch / M = image pixel, relative 1e-9) or the call fails;
* PROJECT_INPUT item 6: dose (mean electrons per detector pixel per hologram), gain (counts per
  electron) and the MTF ("none" is the only implemented value: an ideal detector);
* a region of interest (pixels on each axis) and its alignment ("centre": the ROI centre on the
  centre of the projected exit-plane grid; "field_of_view": on the centre of the image of the
  terraces, an interval of image-plane u given by the caller), and an explicit integer noise seed.

Pixel mapping: the specimen-referred detector pixel is p = pitch / M on each axis, in the image
plane perpendicular to k_out. Axis 0 of the detector is the along-beam (foreshortened) axis, axis 1
the perpendicular one; the surface sampling along the beam is p / sin(theta) (stated with the grid).
The complex dark-field image is resampled onto the detector pixel centres by band-limited (DFT)
interpolation of the image grid, separately along each axis (exact for a wave band-limited below the
Nyquist frequency of the image grid and periodic over it; the objective aperture makes it
band-limited). Detector pixels must lie inside the projected field (no periodic wrap is ever used)
and the aperture band must lie below the detector Nyquist frequency (else aliasing: refused). The
resampling samples the wave at pixel centres; pixel integration and the MTF are NOT IMPLEMENTED.

Noise: counts = gain * Poisson(dose * I / mean(I)) with ``numpy.random.default_rng(seed)``, one
generator for the list of holograms in the order given (``optics.hologram.apply_poisson_noise``, then
the gain). No readout noise, no drift (drift is a coherent envelope loss, NOT IMPLEMENTED).
"""
from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

from reflection_holo.io.labels import require_evidence_label
from reflection_holo.optics.fields import Grid, Hologram, Wave
from reflection_holo.optics.hologram import apply_poisson_noise
from reflection_holo.optics.projection import IMAGE_AXES, ProjectedImage

ALIGNMENTS = ("centre", "field_of_view")
MTFS = ("none",)
_LABELS = ("PROJECT_INPUT", "ASSUMPTION", "TEST_ONLY")
_REL_TOL = 1e-9


@dataclass(frozen=True)
class DetectorSpec:
    """Declared detector (PROJECT_INPUT items 5 and 6). Every field is required.

    pixel_pitch_um        (along_beam, perpendicular) physical pixel pitch, um
    magnification         M (> 0)
    image_pixel_size_A    (along_beam, perpendicular) specimen-referred image pixel, A; must equal
                          pitch / M
    roi_shape             (n_along_beam, n_perpendicular) detector pixels simulated
    alignment             "centre"
    dose_e_per_px         mean electrons per pixel per hologram (> 0)
    gain_counts_per_e     counts per electron (> 0)
    mtf                   "none" (ideal detector; anything else is not implemented)
    label_item5, label_item6  evidence labels of the item-5 and item-6 values
    """
    pixel_pitch_um: tuple[float, float]
    magnification: float
    image_pixel_size_A: tuple[float, float]
    roi_shape: tuple[int, int]
    alignment: str
    dose_e_per_px: float
    gain_counts_per_e: float
    mtf: str
    label_item5: str
    label_item6: str

    def __post_init__(self):
        for name in ("pixel_pitch_um", "image_pixel_size_A"):
            v = tuple(float(a) for a in getattr(self, name))
            if len(v) != 2 or not all(np.isfinite(a) and a > 0 for a in v):
                raise ValueError(f"{name} must be two positive numbers (both axes), got "
                                 f"{getattr(self, name)!r}")
            object.__setattr__(self, name, v)
        for name in ("magnification", "dose_e_per_px", "gain_counts_per_e"):
            v = float(getattr(self, name))
            if not (np.isfinite(v) and v > 0):
                raise ValueError(f"{name} must be finite and > 0, got {getattr(self, name)!r}")
            object.__setattr__(self, name, v)
        roi = tuple(self.roi_shape)
        if len(roi) != 2 or any(isinstance(n, bool) or int(n) != n or int(n) < 2 for n in roi):
            raise ValueError(f"roi_shape must be two integers >= 2, got {self.roi_shape!r}")
        object.__setattr__(self, "roi_shape", (int(roi[0]), int(roi[1])))
        if self.alignment not in ALIGNMENTS:
            raise ValueError(f"alignment must be one of {ALIGNMENTS}, got {self.alignment!r}")
        if self.mtf not in MTFS:
            raise NotImplementedError(f"detector MTF {self.mtf!r}: NOT IMPLEMENTED (only 'none')")
        require_evidence_label(self.label_item5, "detector pixel size and magnification "
                               "(PROJECT_INPUT item 5)", accepted=_LABELS, qualified=True)
        require_evidence_label(self.label_item6, "detector dose and gain (PROJECT_INPUT item 6)",
                               accepted=_LABELS, qualified=True)
        for a in (0, 1):
            p = self.pixel_pitch_um[a] * 1.0e4 / self.magnification
            if abs(p - self.image_pixel_size_A[a]) > _REL_TOL * self.image_pixel_size_A[a]:
                raise ValueError(
                    f"item 5 inconsistent on axis {IMAGE_AXES[a]}: pitch / M = "
                    f"{self.pixel_pitch_um[a]} um / {self.magnification:g} = {p:.9g} A, but the "
                    f"declared image pixel size is {self.image_pixel_size_A[a]:.9g} A")

    @property
    def pixel_A(self) -> tuple[float, float]:
        """Specimen-referred detector pixel (image plane), A: pitch / M."""
        return (self.pixel_pitch_um[0] * 1.0e4 / self.magnification,
                self.pixel_pitch_um[1] * 1.0e4 / self.magnification)

    def grid(self) -> Grid:
        return Grid(shape=self.roi_shape, pixel_size_A=self.pixel_A, axes=IMAGE_AXES,
                    plane="detector, specimen-referred image-plane coordinates (plane "
                          "perpendicular to k_out)")

    def as_record(self, theta_ext_rad: float | None = None) -> dict:
        rec = dict(pixel_pitch_um=list(self.pixel_pitch_um), magnification=self.magnification,
                   image_pixel_size_A=list(self.image_pixel_size_A), pixel_A=list(self.pixel_A),
                   roi_shape=list(self.roi_shape), alignment=self.alignment,
                   dose_e_per_px=self.dose_e_per_px, gain_counts_per_e=self.gain_counts_per_e,
                   mtf=self.mtf, readout_noise="none", pixel_integration="NOT IMPLEMENTED "
                   "(point sampling at pixel centres)", label_item5=self.label_item5,
                   label_item6=self.label_item6)
        if theta_ext_rad is not None:
            rec["surface_pixel_along_beam_A"] = self.pixel_A[0] / math.sin(theta_ext_rad)
        return rec


@dataclass(frozen=True, eq=False)
class DetectorPlacement:
    """Image-plane coordinates (u along the beam, y perpendicular) of the detector pixel centres."""
    u_A: np.ndarray
    y_A: np.ndarray
    record: dict = field(default_factory=dict)


def place_detector(image: ProjectedImage, spec: DetectorSpec, *,
                   field_of_view_u_A: tuple[float, float] | None) -> DetectorPlacement:
    """Pixel-centre coordinates of the ROI ("centre": ROI centre on the centre of the projected
    exit-plane grid; "field_of_view": on the centre of ``field_of_view_u_A``, required then).
    Refuses an ROI that is not inside the projected field on both axes."""
    p = spec.pixel_A
    n0, n1 = spec.roi_shape
    if spec.alignment == "field_of_view":
        if field_of_view_u_A is None:
            raise ValueError("alignment 'field_of_view' needs the image-plane interval of the "
                             "terraces (field_of_view_u_A)")
        uc = 0.5 * (float(field_of_view_u_A[0]) + float(field_of_view_u_A[1]))
    else:
        if field_of_view_u_A is not None:
            raise ValueError("field_of_view_u_A is only for alignment 'field_of_view'")
        uc = 0.5 * (image.image_u_A[0] + image.image_u_A[-1])
    yc = 0.5 * (image.y_A[0] + image.y_A[-1])
    u = uc + (np.arange(n0) - 0.5 * (n0 - 1)) * p[0]
    y = yc + (np.arange(n1) - 0.5 * (n1 - 1)) * p[1]
    for name, v, lo, hi in (("along_beam", u, image.image_u_A[0], image.image_u_A[-1]),
                            ("perpendicular", y, image.y_A[0], image.y_A[-1])):
        if v[0] < lo - 1e-9 or v[-1] > hi + 1e-9:
            raise ValueError(f"detector ROI along {name} spans [{v[0]:.3f}, {v[-1]:.3f}] A, outside "
                             f"the projected field [{lo:.3f}, {hi:.3f}] A: enlarge the engine field "
                             f"or reduce the ROI (no periodic wrap is used)")
    return DetectorPlacement(u_A=u, y_A=y, record=dict(
        alignment=spec.alignment, field_of_view_u_A=(None if field_of_view_u_A is None else
                                                     [float(v) for v in field_of_view_u_A]),
        u_first_A=float(u[0]), u_last_A=float(u[-1]),
        y_first_A=float(y[0]), y_last_A=float(y[-1]),
        field_u_A=[float(image.image_u_A[0]), float(image.image_u_A[-1])],
        field_y_A=[float(image.y_A[0]), float(image.y_A[-1])]))


def _dft_interpolation_matrix(n_in: int, d_in: float, t_out: np.ndarray) -> np.ndarray:
    """Matrix E with E @ fft(f) = trigonometric interpolant of f (samples at j d_in) at t_out.
    The Nyquist term (even n) is taken as a cosine so that a real input stays real."""
    f = np.fft.fftfreq(n_in, d_in)
    E = np.exp(2j * np.pi * np.outer(np.asarray(t_out, float), f)) / n_in
    if n_in % 2 == 0:
        E[:, n_in // 2] = np.cos(2.0 * np.pi * f[n_in // 2] * np.asarray(t_out, float)) / n_in
    return E


def resample_to_detector(image: ProjectedImage, spec: DetectorSpec, *,
                         band_cycles_per_A: float,
                         field_of_view_u_A: tuple[float, float] | None = None
                         ) -> tuple[Wave, DetectorPlacement]:
    """Band-limited resampling of the projected complex image onto the detector pixel centres.

    band_cycles_per_A: the band of the wave (the aperture band sin(alpha)/lambda); it must lie below
    the detector Nyquist frequency on both axes (refused otherwise)."""
    if not isinstance(image, ProjectedImage):
        raise TypeError("image must be a ProjectedImage")
    B = float(band_cycles_per_A)
    if not (np.isfinite(B) and B > 0):
        raise ValueError("band_cycles_per_A must be finite and > 0")
    p = spec.pixel_A
    for a in (0, 1):
        if B >= 0.5 / p[a]:
            raise ValueError(f"the dark-field band {B:.4f} cycles/A is not below the detector "
                             f"Nyquist frequency {0.5 / p[a]:.4f} cycles/A on axis {IMAGE_AXES[a]}: "
                             f"the image would alias (item 5)")
    g = image.wave.grid
    if g.axes != IMAGE_AXES:
        raise ValueError(f"image axes must be {IMAGE_AXES}, got {g.axes}")
    placement = place_detector(image, spec, field_of_view_u_A=field_of_view_u_A)
    du, dy = g.pixel_size_A
    E0 = _dft_interpolation_matrix(g.shape[0], du, placement.u_A - image.image_u_A[0])
    E1 = _dft_interpolation_matrix(g.shape[1], dy, placement.y_A - image.y_A[0])
    F = np.fft.fft2(np.asarray(image.wave.data))
    out = E0 @ F @ E1.T
    rec = dict(method="band-limited DFT interpolation per axis (trigonometric polynomial of the "
                      "image grid) at the detector pixel centres",
               band_cycles_per_A=B, detector_nyquist_cycles_per_A=[0.5 / p[0], 0.5 / p[1]],
               placement=placement.record, detector=spec.as_record(image.theta_out_ext_rad),
               source_grid=g.as_record())
    meta = dict(copy.deepcopy({k: v for k, v in image.wave.metadata.items()}))
    meta["detector_resampling"] = rec
    wave = Wave(out, spec.grid(), image.wave.label.replace("projected dark-field image",
                                                           "object wave on the detector"),
                image.wave.realisation, meta)
    return wave, placement


def record_holograms(holograms: Sequence[Hologram], spec: DetectorSpec, *,
                     seed: int) -> list[Hologram]:
    """Poisson counting at the declared dose, then the gain (module docstring). The draw order is
    the order of ``holograms``; raw (noiseless) intensities are kept in ``noiseless_intensity``."""
    noisy = apply_poisson_noise(list(holograms), dose_e_per_px=spec.dose_e_per_px, seed=seed)
    out = []
    for h in noisy:
        meta = copy.deepcopy(h.metadata)
        meta["detector"]["gain_counts_per_e"] = spec.gain_counts_per_e
        meta["detector"]["counts"] = "gain * Poisson electrons"
        meta["detector"]["spec"] = spec.as_record()
        out.append(Hologram(h.intensity * spec.gain_counts_per_e, h.grid, h.content, meta,
                            h.noiseless_intensity))
    return out
