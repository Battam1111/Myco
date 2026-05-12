"""tests/unit/verbs/intake/test_intake.py — v0.6.0 intake verb (NEW)."""

from __future__ import annotations

from myco.ingestion.intake import intake_directory


def test_intake_module_import():
    """intake module is importable and callable."""
    assert callable(intake_directory)


def test_intake_signature_v0_6_0():
    """intake_directory accepts v0.6.0 contract: path + filter + max + dry_run + strict."""
    import inspect

    sig = inspect.signature(intake_directory)
    assert "path" in sig.parameters
    assert "filter_pattern" in sig.parameters
    assert "max_count" in sig.parameters
    assert "dry_run" in sig.parameters
    assert "strict" in sig.parameters
