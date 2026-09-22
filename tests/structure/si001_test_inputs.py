"""Shared TEST_ONLY inputs and helpers for tests/structure (not a test module).

Every value standing in for a PROJECT_INPUT is labelled TEST_ONLY and never appears in configs/."""
from pathlib import Path

import numpy as np

from reflection_holo.structure import Staircase, build_si001_terraces

AZIMUTH_LABEL = "TEST_ONLY: stands in for PROJECT_INPUT item 8 (beam azimuth)"
THETA_LABEL = "TEST_ONLY: stands in for PROJECT_INPUT item 7 (external glancing angle)"
OVERLAYER_LABEL = "TEST_ONLY: stands in for PROJECT_INPUT item 12 (overlayer)"
FEATURE_LABEL = "TEST_ONLY: stands in for PROJECT_INPUT item 13 (pattern geometry)"

# docs/03 section 4: "At 22.5 mrad (a round illustrative angle ...)" -- TEST_ONLY angle
THETA_22P5_MRAD = 22.5e-3

REPO_ROOT = Path(__file__).resolve().parents[2]


def build(staircase, azimuth=(1, 1, 0), edge_periods=2, substrate_layers=5,
          backbond=(1, 1, 0), overlayer=None, termination="bulk", vacuum_above_A=10.0):
    """Test helper: every builder argument is passed explicitly."""
    return build_si001_terraces(azimuth_uvw=azimuth, azimuth_label=AZIMUTH_LABEL,
                                staircase=staircase, edge_periods=edge_periods,
                                substrate_layers=substrate_layers,
                                first_terrace_backbond_uvw=backbond, termination=termination,
                                overlayer=overlayer, vacuum_above_A=vacuum_above_A)


def brute_force_pairs(pos, Ly, Lz, cutoff):
    """Independent O(N^2) minimum-image pair search (y, z periodic), for cross-checks."""
    d = pos[:, None, :] - pos[None, :, :]
    d[..., 1] -= Ly * np.rint(d[..., 1] / Ly)
    d[..., 2] -= Lz * np.rint(d[..., 2] / Lz)
    r = np.linalg.norm(d, axis=-1)
    np.fill_diagonal(r, np.inf)
    return r
