"""Tests for ``PA1WriteSurfaceCoverage``."""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimensions.pa1_write_surface_coverage import (
    PA1WriteSurfaceCoverage,
)


def test_complete_coverage_no_finding(genesis_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=genesis_substrate)
    # v0.5.8: PA1 uses sample-path fnmatch coverage, so broad globs
    # like ``notes/**`` cover every notes-prefixed sample without
    # having to enumerate each one. Myco's own canon uses this
    # shape; declaring it here exercises the expected real-world
    # usage.
    object.__setattr__(
        ctx.substrate.canon,
        "system",
        {
            "write_surface": {
                "allowed": [
                    "notes/**",
                    "_canon.yaml",
                    "docs/**",
                ]
            }
        },
    )
    assert list(PA1WriteSurfaceCoverage().run(ctx)) == []


def test_missing_core_path_fires(genesis_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=genesis_substrate)
    # Only ``notes/raw`` covered; integrated, distilled, canon,
    # changelog each fire. (fnmatch sees ``notes/raw/*.md`` as
    # covering ``notes/raw/sample.md`` but nothing else.)
    object.__setattr__(
        ctx.substrate.canon,
        "system",
        {"write_surface": {"allowed": ["notes/raw/*.md"]}},
    )
    findings = list(PA1WriteSurfaceCoverage().run(ctx))
    # 4 of 5 samples uncovered (raw is covered).
    assert len(findings) == 4


def test_non_list_fires_high(genesis_substrate: Path) -> None:
    ctx = MycoContext.for_testing(root=genesis_substrate)
    object.__setattr__(
        ctx.substrate.canon,
        "system",
        {"write_surface": {"allowed": "not-a-list"}},
    )
    findings = list(PA1WriteSurfaceCoverage().run(ctx))
    assert len(findings) == 1
    assert findings[0].severity is Severity.HIGH
