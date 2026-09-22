"""Nits of audit A2 (geometry and package-wide), each fixed with a regression test.

* SpecularCondition clipped an order beyond backscattering (n lambda / 2d > 1) to
  theta_int = theta_ext = pi/2 and reported it accessible (scratch script e8: order 300 of d_111);
  it now refuses;
* bare `assert` statements (stripped by python -O) guarded the frame construction; the package
  now uses explicit raises only.
"""
import ast
from pathlib import Path

import numpy as np
import pytest

from reflection_holo.constants import A_SI_A
from reflection_holo.geometry.specular import SpecularCondition

PKG = Path(__file__).resolve().parents[2] / "reflection_holo"


def test_order_beyond_backscattering_is_refused():
    d111 = A_SI_A / np.sqrt(3.0)
    with pytest.raises(ValueError, match="backscattering"):
        SpecularCondition(d111, 300, 200.0, 12.0)
    sc = SpecularCondition(d111, 200, 200.0, 12.0)          # still below backscattering
    assert sc.accessible and sc.theta_int < np.pi / 2


def test_no_bare_assert_in_the_package():
    found = [f"{p.relative_to(PKG.parent)}:{n.lineno}" for p in sorted(PKG.rglob("*.py"))
             for n in ast.walk(ast.parse(p.read_text())) if isinstance(n, ast.Assert)]
    assert found == []
