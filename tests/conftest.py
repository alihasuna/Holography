"""Shared pytest configuration. Test-only parameter values must be labelled TEST_ONLY where they
stand in for a PROJECT_INPUT; they never appear in configs/.

Guard (audit A2 m8): tests write only to temporary directories. The repository's outputs/ tree is
snapshotted (relative path, size, mtime) before the session and compared after it; any change is
reported as an error of the session."""
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def _snapshot_outputs():
    out = REPO / "outputs"
    if not out.exists():
        return None
    return sorted((str(p.relative_to(out)), p.stat().st_size, p.stat().st_mtime_ns)
                  for p in out.rglob("*"))


@pytest.fixture(scope="session", autouse=True)
def repository_outputs_untouched():
    before = _snapshot_outputs()
    yield
    assert _snapshot_outputs() == before, "a test wrote into the repository's outputs/ directory"
