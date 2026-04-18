"""Tests for the v0.5.5 MAJOR-B schema upgrader demo.

The demo upgrader under key ``"0"`` lets a canon with
``schema_version: "0"`` parse cleanly through the forward-compat
seam that v0.5.1 designed but never exercised end-to-end.
"""

from __future__ import annotations

import textwrap
import warnings
from pathlib import Path

import pytest

from myco.core.canon import load_canon, schema_upgraders


def test_v0_upgrader_is_registered() -> None:
    """v0.5.5 registers the demo upgrader unconditionally at module
    import time so production substrates with schema_version 0 (a
    version that never actually shipped) parse silently."""
    assert "0" in schema_upgraders
    assert callable(schema_upgraders["0"])


def test_v0_canon_parses_silently(tmp_path: Path) -> None:
    """A canon with ``schema_version: "0"`` goes through the demo
    upgrader and parses without a UserWarning. This exercises the
    full chain: load_canon → _apply_upgraders → upgrader returns
    mapping with known version → no warning → Canon dataclass
    populated."""
    canon_text = textwrap.dedent(
        """\
        schema_version: "0"
        contract_version: "v0.5.5"
        identity:
          substrate_id: "upgrader-demo"
          entry_point: "MYCO.md"
        system:
          hard_contract: {rule_count: 7}
        subsystems:
          germination:
            doc: "docs/architecture/L2_DOCTRINE/genesis.md"
        """
    )
    p = tmp_path / "_canon.yaml"
    p.write_text(canon_text, encoding="utf-8")

    with warnings.catch_warnings():
        warnings.simplefilter("error")  # any UserWarning would raise
        canon = load_canon(p)

    # After the upgrader runs, the canon carries the known version.
    assert canon.schema_version == "1"
    assert canon.substrate_id == "upgrader-demo"


def test_unknown_version_still_warns(
    tmp_path: Path, minimal_canon_text: str,
) -> None:
    """Versions without a registered upgrader still warn. Proves the
    demo doesn't accidentally silence other unknown versions."""
    p = tmp_path / "_canon.yaml"
    p.write_text(
        minimal_canon_text.replace('schema_version: "1"', 'schema_version: "999"'),
        encoding="utf-8",
    )
    with pytest.warns(UserWarning, match="schema_version"):
        canon = load_canon(p)
    assert canon.schema_version == "999"


def test_demo_upgrader_is_reversibly_removable() -> None:
    """The demo entry can be popped + re-registered without breaking
    the registry. Guards against the demo being accidentally removed
    by a test-isolation fixture."""
    original = schema_upgraders.pop("0")
    try:
        assert "0" not in schema_upgraders
    finally:
        schema_upgraders["0"] = original
    assert "0" in schema_upgraders
