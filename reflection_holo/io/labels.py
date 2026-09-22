"""Evidence labels and the package's one evidence-label checker.

The seven evidence labels (io.config module docstring; docs/05 sections 0 and 3):
    METADATA_VERIFIED, SECTION_READ, REPRODUCED, PROJECT_INPUT, ASSUMPTION, DERIVED_HERE, UNVERIFIED
and TEST_ONLY for a value that stands in for a missing input in tests only (io.config refuses it
from any configuration file).

``require_evidence_label`` is used by io.config (configuration parameters, exact labels) and by
structure/ (labelled arguments such as "PROJECT_INPUT item 8" or "TEST_ONLY: stands in for ...").
This module imports only the standard library, so any module can use it without importing the
configuration loader or yaml.
Source map: no row (software requirement, docs/05 sections 0 and 3); evidence label: not
applicable (no physical claim).
"""
from __future__ import annotations

EVIDENCE_LABELS = ("METADATA_VERIFIED", "SECTION_READ", "REPRODUCED", "PROJECT_INPUT",
                   "ASSUMPTION", "DERIVED_HERE", "UNVERIFIED")
TEST_ONLY_LABEL = "TEST_ONLY"
KNOWN_LABELS = EVIDENCE_LABELS + (TEST_ONLY_LABEL,)


def require_evidence_label(label, what: str, *, accepted, qualified: bool,
                           error: type[Exception] = ValueError) -> str:
    """Return ``label`` unchanged if it is an accepted evidence label; otherwise raise ``error``.

    label      the label to check; it must be a non-blank string.
    what       what the label belongs to, used at the start of the error message.
    accepted   the labels allowed at this call site: a non-empty subset of KNOWN_LABELS.
    qualified  False: the label must EQUAL one of ``accepted``. Used for configuration parameters,
               whose source is a separate field.
               True: the label must START with one of ``accepted`` and may carry qualifying
               text, e.g. "PROJECT_INPUT item 8", "ASSUMPTION B3", "TEST_ONLY: stands in for
               PROJECT_INPUT item 7". Used for labelled arguments of in-memory calls.
    error      the exception class to raise: ValueError or a subclass (io.config uses ConfigError).
    Every error message starts with ``what`` and contains the word "label".
    """
    acc = tuple(accepted)
    if not acc or any(a not in KNOWN_LABELS for a in acc):
        raise ValueError(f"accepted must be a non-empty subset of {KNOWN_LABELS}, "
                         f"got {accepted!r}")
    if not isinstance(label, str) or not label.strip():
        raise error(f"{what}: an evidence label string is required, got {label!r}")
    if qualified:
        if not label.startswith(acc):
            raise error(f"{what}: label {label!r} must start with one of {acc}")
    elif label not in acc:
        raise error(f"{what}: label {label!r} is not one of {acc}")
    return label
