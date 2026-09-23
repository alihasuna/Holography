"""Height map of a surface feature from ONE reconstructed hologram phase (agent T2; DERIVED_HERE).

Convention (docs/physics_conventions.md, ``quantification.height``): exp(+i(k.r - omega t)); the
phase of a surface point relative to the flat reference surface is Delta_phi = -(k_out - k_in).h n_hat,
so h = -Delta_phi lambda / (2 pi (sin theta_in + sin theta_out)) = -Delta_phi / s with external
angles and the vacuum wavelength; h > 0 above the flat surface. Wrap period h_2pi = 2 pi / s.

A single hologram gives the phase modulo 2 pi. Heights are therefore returned only where the phase
can be UNWRAPPED from the flat reference surface along paths on which the true phase changes by less
than pi per pixel (Itoh condition, docs/03 section 4). The reliability map combines:

  data criteria (what an experiment has):
    * the reconstruction marks the pixel valid and its object amplitude, relative to the
      empty-hologram object amplitude, is at least ``min_relative_amplitude`` (B29);
    * every wrapped phase difference to a 4-neighbour that passes the amplitude test is at most
      ``max_phase_step_rad`` (< pi; a margin below the Itoh limit for noise);
  model criteria (from the ray-traced BUILT geometry; a simulation-only check, like the terrace
  regions of the staircase path; experimental data would need a rocking series instead):
    * the pixel traces to a lit surface point (not shadowed, not a riser face, not below the surface,
      not outside the field of view);
    * the built phase -s h(source) differs by less than pi from that of every lit 4-neighbour (a
      sharp a/4 step is 1.78 wraps at the demo angle: its wrapped jump looks like a -0.165 A step
      and passes every data criterion, so only the geometry can reject it);
    * no blocked-view (hidden) surface lies between the sources of along-beam neighbours.
Pixels passing all criteria are unwrapped (``reconstruction.sideband.unwrap_itoh_raster``, regions
with independent 2 pi offsets). The flat reference is the set of reliable pixels whose source lies
on the flat surrounding surface, eroded by the margin (``margin_px``, the B29 rule "three resolution
elements from any unusable pixel"), within the unwrap region holding most of them; its median
unwrapped phase is the zero. A height is MEASURABLE where the pixel lies in that region and its
margin box contains only reliable pixels. Everything else is masked with a reason code
(``REASONS``).

Uncertainty: sigma_h^2 = (sigma_phi / s)^2 + (h sigma_s / s)^2 per pixel, sigma_phi the MEASURED
per-pixel phase scatter on the flat reference (B16: measured, not guessed), sigma_s from the common
angle calibration (``angle_errors="common"``, audit A3 M3); the standard error of the reference
median is reported separately (a common offset of the whole map).
"""
from __future__ import annotations

import math

import numpy as np

from reflection_holo.geometry.specular import wrap_to_pi
from reflection_holo.quantification.height import (sensitivity_rad_per_A,
                                                    sensitivity_uncertainty_rad_per_A,
                                                    wrap_period_A)
from reflection_holo.reconstruction.sideband import unwrap_itoh_raster

REASONS = {
    "measurable": 0,
    "not_lit": 1,                  # shadow, riser face, below surface, outside the field of view
    "weak_or_invalid": 2,          # reconstruction invalid, or amplitude below the minimum
    "data_phase_step": 3,          # wrapped neighbour difference above max_phase_step_rad
    "model_phase_step": 4,         # built phase changes by >= pi between neighbouring sources
    "hidden_strip": 5,             # a blocked-view strip lies between neighbouring sources
    "within_margin": 6,            # reliable, but closer than the margin to an unreliable pixel
    "not_connected": 7,            # reliable, not in the unwrap region of the flat reference
}


def _neighbour_flags(values: np.ndarray, ok: np.ndarray, bad_pair) -> np.ndarray:
    """True for pixels with at least one 4-neighbour pair (both ``ok``) for which
    bad_pair(v_a, v_b) holds."""
    out = np.zeros(values.shape, dtype=bool)
    for ax in (0, 1):
        a = [slice(None)] * 2
        b = [slice(None)] * 2
        a[ax] = slice(None, -1)
        b[ax] = slice(1, None)
        a, b = tuple(a), tuple(b)
        pair = ok[a] & ok[b]
        flag = np.zeros(pair.shape, dtype=bool)
        flag[pair] = bad_pair(values[a][pair], values[b][pair])
        out[a] |= flag
        out[b] |= flag
    return out


def data_phase_steps(phase_wrapped: np.ndarray, ok: np.ndarray, max_phase_step_rad: float
                     ) -> np.ndarray:
    """Pixels with a wrapped phase difference above ``max_phase_step_rad`` to an ``ok`` neighbour."""
    if not (0.0 < float(max_phase_step_rad) < math.pi):
        raise ValueError("max_phase_step_rad must lie in (0, pi)")
    return _neighbour_flags(np.asarray(phase_wrapped, float), np.asarray(ok, bool),
                            lambda u, v: np.abs(wrap_to_pi(v - u)) > max_phase_step_rad)


def model_phase_steps(source_phase_rad: np.ndarray, lit: np.ndarray) -> np.ndarray:
    """Pixels whose built (unwrapped, geometric) source phase differs by pi or more from that of a
    lit 4-neighbour: a single hologram cannot unwrap across them."""
    return _neighbour_flags(np.asarray(source_phase_rad, float), np.asarray(lit, bool),
                            lambda u, v: np.abs(v - u) >= math.pi)


def box_all(mask: np.ndarray, m0: int, m1: int) -> np.ndarray:
    """True where the (2 m0 + 1) x (2 m1 + 1) box centred on the pixel is entirely True (outside the
    array counts as False); the rule of ``pipeline.quantify.box_erode``."""
    g = np.asarray(mask, dtype=bool)
    P = np.pad(g.astype(np.int64), ((m0, m0), (m1, m1)))
    S = np.zeros((P.shape[0] + 1, P.shape[1] + 1), dtype=np.int64)
    S[1:, 1:] = P.cumsum(0).cumsum(1)
    n0, n1 = g.shape
    a0, a1 = 2 * m0 + 1, 2 * m1 + 1
    win = (S[a0:a0 + n0, a1:a1 + n1] - S[:n0, a1:a1 + n1] - S[a0:a0 + n0, :n1] + S[:n0, :n1])
    return win == a0 * a1


def box_span(values: np.ndarray, valid: np.ndarray, m0: int, m1: int) -> np.ndarray:
    """max - min of ``values`` over the (2 m0 + 1) x (2 m1 + 1) box of each pixel; +inf where the
    box holds an invalid pixel or leaves the array."""
    v = np.asarray(values, float)
    ok = np.asarray(valid, bool) & np.isfinite(v)
    hi = np.where(ok, v, -np.inf)
    lo = np.where(ok, v, np.inf)
    for ax, m in ((0, m0), (1, m1)):
        if m == 0:
            continue
        pad = [(0, 0), (0, 0)]
        pad[ax] = (m, m)
        hp = np.pad(hi, pad, constant_values=-np.inf)
        lp = np.pad(lo, pad, constant_values=np.inf)
        wh = np.lib.stride_tricks.sliding_window_view(hp, 2 * m + 1, axis=ax)
        wl = np.lib.stride_tricks.sliding_window_view(lp, 2 * m + 1, axis=ax)
        hi, lo = wh.max(axis=-1), wl.min(axis=-1)
    span = hi - lo
    span[~box_all(ok, m0, m1)] = np.inf
    return span


def height_map(*, phase_wrapped, amplitude_rel, valid, lit, source_phase_rad, hidden, flat_source,
               min_relative_amplitude: float, max_phase_step_rad: float, margin_px: tuple[int, int],
               min_region_px: int, a_eff_px: float, wavelength_A: float, theta_rad: float,
               sigma_theta_rad: float, sigma_wavelength_rel: float) -> dict:
    """Reliability map, unwrapping, flat reference and height map (module docstring). All
    arguments are required detector-sized arrays or declared numbers:

    phase_wrapped, amplitude_rel, valid   reconstruction (wrapped phase, |u_o| relative to the empty
                                          object amplitude, validity)
    lit                                   ray trace: the pixel's source is a lit surface point
    source_phase_rad                      built phase -s h(source) (NaN where not lit)
    hidden                                ray trace: hidden strip between along-beam neighbours
    flat_source                           the source lies on the flat surrounding surface
    a_eff_px                              effective resolution area of the sideband mask in pixels
                                          (pixels closer than a resolution element are correlated)
    """
    ph = np.asarray(phase_wrapped, float)
    amp = np.asarray(amplitude_rel, float)
    shape = ph.shape
    for name, arr in (("amplitude_rel", amp), ("valid", valid), ("lit", lit),
                      ("source_phase_rad", source_phase_rad), ("hidden", hidden),
                      ("flat_source", flat_source)):
        if np.shape(arr) != shape:
            raise ValueError(f"{name} must have the shape of the phase {shape}")
    lit = np.asarray(lit, bool)
    hidden = np.asarray(hidden, bool)
    flat_source = np.asarray(flat_source, bool)
    m0, m1 = (int(v) for v in margin_px)
    if m0 < 0 or m1 < 0:
        raise ValueError("margin_px must be non-negative")
    s = sensitivity_rad_per_A(wavelength_A=wavelength_A, theta_in_ext_rad=theta_rad,
                              theta_out_ext_rad=theta_rad)
    sig_s = sensitivity_uncertainty_rad_per_A(
        wavelength_A=wavelength_A, theta_in_ext_rad=theta_rad, theta_out_ext_rad=theta_rad,
        sigma_theta_in_rad=sigma_theta_rad, sigma_theta_out_rad=sigma_theta_rad,
        sigma_wavelength_rel=sigma_wavelength_rel, angle_errors="common")
    h2pi = wrap_period_A(wavelength_A=wavelength_A, theta_in_ext_rad=theta_rad,
                         theta_out_ext_rad=theta_rad)
    data_ok = (np.asarray(valid, bool) & np.isfinite(ph) & np.isfinite(amp)
               & (amp >= float(min_relative_amplitude)))
    steep = data_phase_steps(ph, data_ok, max_phase_step_rad)
    mstep = model_phase_steps(source_phase_rad, lit)
    reliable_data = lit & data_ok & ~steep & ~hidden
    reliable = reliable_data & ~mstep
    unwrapped, regions = unwrap_itoh_raster(ph, reliable, return_regions=True)
    # data-only unwrapping (what an experiment without the model check would get: aliased across
    # unresolved a/4 steps); reported for comparison, never as a height
    unwrapped_d, regions_d = unwrap_itoh_raster(ph, reliable_data, return_regions=True)
    flat_good = box_all(reliable & flat_source, m0, m1)
    rec = dict(sensitivity_rad_per_A=s, sigma_sensitivity_rad_per_A=sig_s, wrap_period_A=h2pi,
               min_relative_amplitude=float(min_relative_amplitude),
               max_phase_step_rad=float(max_phase_step_rad), margin_px=[m0, m1],
               min_region_px=int(min_region_px), n_unwrap_regions=int(regions.max()),
               model_step_limit_rad=math.pi,
               rule="h = -Delta_phi / s, Delta_phi = unwrapped phase - median over the flat "
                    "reference; s = (2 pi/lambda)(sin theta_in + sin theta_out)")
    code = np.full(shape, REASONS["not_connected"], dtype=np.int8)
    code[~lit] = REASONS["not_lit"]
    code[lit & ~data_ok] = REASONS["weak_or_invalid"]
    code[lit & data_ok & steep] = REASONS["data_phase_step"]
    code[lit & data_ok & ~steep & hidden] = REASONS["hidden_strip"]
    code[lit & data_ok & ~steep & ~hidden & mstep] = REASONS["model_phase_step"]
    out = dict(record=rec, data_ok=data_ok, data_phase_step=steep, model_phase_step=mstep,
               reliable=reliable, reliable_data=reliable_data, unwrapped=unwrapped,
               unwrap_regions=regions, flat_good=flat_good)
    ref_label = 0
    if flat_good.any():
        labels, counts = np.unique(regions[flat_good], return_counts=True)
        ref_label = int(labels[np.argmax(counts)])
    flat_ref = flat_good & (regions == ref_label) if ref_label > 0 else np.zeros(shape, bool)
    n_ref = int(flat_ref.sum())
    rec.update(reference_region_label=ref_label, n_flat_reference_px=n_ref,
               n_flat_good_px=int(flat_good.sum()))
    connected = (regions == ref_label) if ref_label > 0 else np.zeros(shape, bool)
    measurable = box_all(reliable, m0, m1) & connected
    code[reliable & connected & ~measurable] = REASONS["within_margin"]
    code[measurable] = REASONS["measurable"]
    out.update(flat_reference=flat_ref, connected=connected, measurable=measurable,
               reason_code=code)
    height = np.full(shape, np.nan)
    sigma_h = np.full(shape, np.nan)
    height_d = np.full(shape, np.nan)
    if n_ref < int(min_region_px):
        rec.update(reference="none", reason=f"flat reference of {n_ref} px below the minimum "
                                            f"{int(min_region_px)} px: no height")
        out.update(height_A=height, sigma_h_A=sigma_h, height_data_only_A=height_d)
        return out
    u_ref = unwrapped[flat_ref]
    phi0 = float(np.median(u_ref))
    sd = float(np.std(u_ref - phi0))
    height[measurable] = -(unwrapped[measurable] - phi0) / s
    sigma_h[measurable] = np.hypot(sd / s, np.abs(height[measurable]) * sig_s / s)
    # data-only map: the data-only region holding most flat-reference pixels, same zero rule
    lab_d, cnt_d = np.unique(regions_d[flat_ref], return_counts=True)
    ld = int(lab_d[np.argmax(cnt_d)])
    ref_d = flat_ref & (regions_d == ld)
    phi0_d = float(np.median(unwrapped_d[ref_d]))
    conn_d = regions_d == ld
    height_d[conn_d] = -(unwrapped_d[conn_d] - phi0_d) / s
    rec.update(reference="median unwrapped phase over the flat reference", reference_phase_rad=phi0,
               sigma_phase_px_rad=sd, sigma_phase_px_source="measured scatter of the unwrapped "
                                                            "phase over the flat reference",
               reference_offset_uncertainty_A=1.2533 * sd * math.sqrt(max(1.0, float(a_eff_px))
                                                                  / n_ref) / s,
               reference_offset_note="standard error of the reference median (correlated pixels: "
                                     "1.2533 sd sqrt(A_eff / n)), a common offset of the map",
               n_measurable_px=int(measurable.sum()),
               data_only_note="height_data_only_A: unwrapped over the DATA criteria only (no model "
                              "check), zero on the same flat reference: aliased across unresolved "
                              "a/4 steps (each reads -wrap(s a/4)/s); for comparison, never a "
                              "height")
    out.update(height_A=height, sigma_h_A=sigma_h, height_data_only_A=height_d,
               phi0_rad=phi0)
    return out
