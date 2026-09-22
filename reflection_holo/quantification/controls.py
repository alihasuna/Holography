"""No-step control (docs/05 section 5 item 8: "no-step control on every dataset").

Evidence DERIVED_HERE. Two regions of a reconstructed phase map that are known to lie on the same
flat terrace (or a dataset with no step) must give a phase difference compatible with zero. The
comparison uses circular statistics (medians about the circular mean), excludes invalid pixels
(for example shadowed strips, reflection_holo.quantification.shadow) and requires an explicit
tolerance. Calculator check T25 is the hologram-level no-step control (owned by the optics and
reconstruction agent); this helper is the quantification-level control applied to any phase map.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from reflection_holo.geometry.specular import wrap_to_pi


@dataclass(frozen=True)
class NoStepControlResult:
    """Result of no_step_control (source map: no row; docs/05 section 5 item 8; DERIVED_HERE)."""
    delta_rad: float          # wrapped median(B) - median(A)
    sigma_rad: float          # standard error of delta (1.2533 std / sqrt(n) per region)
    tolerance_rad: float
    passed: bool              # |delta| <= tolerance
    n_a: int
    n_b: int


def _circular_median(p: np.ndarray) -> tuple[float, float]:
    centre = float(np.angle(np.mean(np.exp(1j * p))))
    d = wrap_to_pi(p - centre)
    med = float(np.median(d))
    spread = float(np.std(wrap_to_pi(d - med)))
    return centre + med, spread


def no_step_control(phase_map_rad, mask_a, mask_b, *, valid_mask, tolerance_rad: float
                    ) -> NoStepControlResult:
    """Phase difference between two regions that must show no step.

    phase_map_rad: reconstructed (wrapped or unwrapped) phase; mask_a, mask_b: boolean masks of the
    two regions (non-empty, disjoint); valid_mask: boolean mask of usable pixels (e.g. the shadow
    mask) or None, stated explicitly; tolerance_rad: required pass threshold on |delta|.
    Source map: no row (requirement of docs/05 section 5 item 8); evidence DERIVED_HERE.
    """
    p = np.asarray(phase_map_rad, dtype=float)
    a = np.asarray(mask_a, dtype=bool)
    b = np.asarray(mask_b, dtype=bool)
    if a.shape != p.shape or b.shape != p.shape:
        raise ValueError("masks must have the shape of the phase map")
    if valid_mask is not None:
        v = np.asarray(valid_mask, dtype=bool)
        if v.shape != p.shape:
            raise ValueError("valid_mask must have the shape of the phase map")
        a = a & v
        b = b & v
    if np.any(a & b):
        raise ValueError("the two control regions overlap")
    if not a.any() or not b.any():
        raise ValueError("a control region is empty after masking")
    if not (np.isfinite(tolerance_rad) and tolerance_rad > 0):
        raise ValueError("tolerance_rad must be positive")
    med_a, sd_a = _circular_median(p[a])
    med_b, sd_b = _circular_median(p[b])
    na, nb = int(a.sum()), int(b.sum())
    se = float(np.hypot(1.2533 * sd_a / np.sqrt(na), 1.2533 * sd_b / np.sqrt(nb)))
    delta = wrap_to_pi(med_b - med_a)
    return NoStepControlResult(delta_rad=float(delta), sigma_rad=se, tolerance_rad=float(tolerance_rad),
                               passed=bool(abs(delta) <= tolerance_rad), n_a=na, n_b=nb)
