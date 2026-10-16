"""T-transmission-limit: kernel vs abTEM in plain transmission (Si [100] slab, normal incidence).

Run with: pytest -q tests/test_transmission_limit.py
The abTEM test is marked xfail with the reason if abTEM, ASE or the kernel cannot be imported. It is never
deleted.
"""
import importlib.util
import pathlib

import numpy as np
import pytest

_P = pathlib.Path(__file__).resolve().parents[1] / "validation" / "abtem_transmission.py"
_spec = importlib.util.spec_from_file_location("abtem_transmission", _P)
AT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(AT)


def test_slab_builder_diamond_cell():
    """External fact: the diamond conventional cell holds 8 atoms (conventions, structure factor over the
    8-atom cell). A [100] slab has 4 equally populated {100} planes per a, each 2 atoms per a^2.
    Every plane sits at the centre of its a/4 slice."""
    a = 5.431
    pos, slices, dx = AT.build_si_slab(a, n_cells_beam=3)
    assert pos.shape == (24, 3)
    assert len(slices) == 12 and all(len(s) == 2 for s in slices)
    frac = (pos[:, 0] % dx) / dx
    assert np.allclose(frac, 0.5)


def test_kernel_matches_abtem_transmission():
    """External reference: abTEM (independent multislice, Kirkland parameterisation) for identical atoms.

    Tolerances (ASSUMPTION; reason in NOTES_D.md):
    * 15 strongest beams: |I_k - I_a| <= 0.01 + 0.05 I_a.
    * Total intensity of both codes in [0.95, 1], Kirkland eqn 6.95 [p.41]."""
    try:
        import abtem  # noqa: F401
        import ase  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        pytest.xfail(f"abTEM/ASE not importable in this sandbox: {exc!r}")
    try:
        import reflection_holo.multislice.potential  # noqa: F401
        import reflection_holo.multislice.propagate  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        pytest.xfail(f"kernel modules not importable: {exc!r}")
    res = AT.run_comparison(verbose=True)
    assert res["beams_ok"], res
    assert res["flux_ok"], res
