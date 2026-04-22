"""Unit tests for ``scripts/bump_version.py``.

The script is a release-time helper — it rewrites __init__.py,
plugin.json, CITATION.cff, and server.json in lockstep, then hands
off to ``myco molt``. This suite exercises the pure file-bumper
helpers against temporary copies, so we have confidence the regex
patterns and JSON shape manipulations match the real files' format
before release day.

Integration-layer (not unit) because the script isn't part of the
``myco`` package; it's a standalone tool and we import it by path.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from textwrap import dedent

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "bump_version.py"


@pytest.fixture(scope="module")
def bump():
    """Import ``scripts/bump_version.py`` as a module."""
    spec = importlib.util.spec_from_file_location("bump_version", SCRIPT)
    if spec is None or spec.loader is None:
        pytest.skip("could not load bump_version.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ------------------------------------------------------ __init__.py


def test_bump_pyversion_rewrites_version_literal(tmp_path: Path, bump) -> None:
    p = tmp_path / "init.py"
    p.write_text('"""docstring."""\n\n__version__ = "0.5.12"\n', encoding="utf-8")
    changes = bump._bump_pyversion(p, "0.5.13", dry_run=False)
    assert p.read_text(encoding="utf-8") == '"""docstring."""\n\n__version__ = "0.5.13"\n'
    assert any("0.5.12 → 0.5.13" in c for c in changes)


def test_bump_pyversion_idempotent(tmp_path: Path, bump) -> None:
    p = tmp_path / "init.py"
    p.write_text('__version__ = "0.5.13"\n', encoding="utf-8")
    changes = bump._bump_pyversion(p, "0.5.13", dry_run=False)
    assert any("already at 0.5.13" in c for c in changes)


def test_bump_pyversion_dry_run_leaves_file_untouched(tmp_path: Path, bump) -> None:
    p = tmp_path / "init.py"
    original = '__version__ = "0.5.12"\n'
    p.write_text(original, encoding="utf-8")
    bump._bump_pyversion(p, "0.5.13", dry_run=True)
    assert p.read_text(encoding="utf-8") == original


# -------------------------------------------------- plugin.json


def test_bump_plugin_json_preserves_other_keys(tmp_path: Path, bump) -> None:
    p = tmp_path / "plugin.json"
    p.write_text(
        json.dumps(
            {
                "name": "myco",
                "version": "0.5.12",
                "description": "x",
                "author": {"name": "B"},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    bump._bump_plugin_json(p, "0.5.13", dry_run=False)
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["version"] == "0.5.13"
    assert data["name"] == "myco"
    assert data["description"] == "x"
    assert data["author"] == {"name": "B"}


def test_bump_plugin_json_preserves_key_order(tmp_path: Path, bump) -> None:
    p = tmp_path / "plugin.json"
    p.write_text(
        json.dumps({"name": "myco", "version": "0.5.12", "description": "x"}, indent=2) + "\n",
        encoding="utf-8",
    )
    bump._bump_plugin_json(p, "0.5.13", dry_run=False)
    assert list(json.loads(p.read_text(encoding="utf-8"))) == ["name", "version", "description"]


# --------------------------------------------------- CITATION.cff


def test_bump_citation_updates_both_version_lines(tmp_path: Path, bump) -> None:
    p = tmp_path / "CITATION.cff"
    p.write_text(
        dedent(
            """\
            cff-version: 1.2.0
            title: "Example"
            version: "0.5.12"
            date-released: "2026-04-22"
            preferred-citation:
              type: software
              version: "0.5.12"
              year: 2026
            """
        ),
        encoding="utf-8",
    )
    bump._bump_citation_cff(p, "0.5.13", dry_run=False)
    text = p.read_text(encoding="utf-8")
    assert text.count('version: "0.5.13"') == 2
    assert '"0.5.12"' not in text


def test_bump_citation_preserves_other_fields(tmp_path: Path, bump) -> None:
    p = tmp_path / "CITATION.cff"
    original = dedent(
        """\
        cff-version: 1.2.0
        title: "Example Project"
        authors:
          - family-names: Smith
        version: "1.0.0"
        """
    )
    p.write_text(original, encoding="utf-8")
    bump._bump_citation_cff(p, "1.0.1", dry_run=False)
    text = p.read_text(encoding="utf-8")
    assert 'cff-version: 1.2.0' in text
    assert 'title: "Example Project"' in text
    assert 'family-names: Smith' in text
    assert 'version: "1.0.1"' in text


# ------------------------------------------------------ server.json


def test_bump_server_json_updates_root_and_package_versions(tmp_path: Path, bump) -> None:
    p = tmp_path / "server.json"
    p.write_text(
        json.dumps(
            {
                "name": "io.github.x/y",
                "version": "0.5.12",
                "packages": [
                    {"registryType": "pypi", "identifier": "y", "version": "0.5.12"}
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    bump._bump_server_json(p, "0.5.13", dry_run=False)
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["version"] == "0.5.13"
    assert data["packages"][0]["version"] == "0.5.13"


def test_bump_server_json_handles_multiple_packages(tmp_path: Path, bump) -> None:
    p = tmp_path / "server.json"
    p.write_text(
        json.dumps(
            {
                "name": "io.github.x/y",
                "version": "1.0.0",
                "packages": [
                    {"registryType": "pypi", "identifier": "y", "version": "1.0.0"},
                    {"registryType": "oci", "identifier": "y:1.0.0", "version": "1.0.0"},
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    bump._bump_server_json(p, "1.1.0", dry_run=False)
    data = json.loads(p.read_text(encoding="utf-8"))
    assert all(pkg["version"] == "1.1.0" for pkg in data["packages"])


# ------------------------------------------------------- semver helpers


def test_semver_regex_accepts_basic(bump) -> None:
    assert bump.SEMVER_RE.match("0.5.13") is not None
    assert bump.SEMVER_RE.match("10.20.30") is not None
    assert bump.SEMVER_RE.match("0.5.13-rc1") is not None
    assert bump.SEMVER_RE.match("0.5.13+build.1") is not None


def test_semver_regex_rejects_malformed(bump) -> None:
    assert bump.SEMVER_RE.match("0.5") is None
    assert bump.SEMVER_RE.match("v0.5.13") is None  # leading 'v' is stripped in main(), not here
    assert bump.SEMVER_RE.match("0.5.13.4") is None
    assert bump.SEMVER_RE.match("not-a-version") is None


def test_as_tuple_orders_correctly(bump) -> None:
    assert bump._as_tuple("0.5.12") < bump._as_tuple("0.5.13")
    assert bump._as_tuple("0.5.12") < bump._as_tuple("0.6.0")
    assert bump._as_tuple("0.9.99") < bump._as_tuple("1.0.0")
    assert bump._as_tuple("1.0.0") > bump._as_tuple("0.9.99")


# ------------------------------------------------------- live-file check


def test_script_knows_real_files_current_version(bump) -> None:
    """Guard: the repo's actual live files can be parsed by the script.

    Catches the case where someone reformats __init__.py or the JSON
    shape and the bumper silently stops matching.
    """
    v = bump._read_current_version()
    # Must be semver-shaped (stripped of any 'v' prefix already).
    assert bump.SEMVER_RE.match(v), f"__version__ {v!r} doesn't parse as semver"
