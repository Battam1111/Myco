"""Tests for ``myco.genesis.bootstrap``."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from myco.core.errors import ContractError, UsageError
from myco.core.substrate import Substrate
from myco.genesis import DEFAULT_CONTRACT_VERSION, bootstrap

# --- happy path ------------------------------------------------------------


def test_bootstrap_creates_expected_files(tmp_path: Path) -> None:
    result = bootstrap(project_dir=tmp_path, substrate_id="test-sub")
    assert result.exit_code == 0
    assert (tmp_path / "_canon.yaml").is_file()
    assert (tmp_path / "MYCO.md").is_file()
    assert (tmp_path / ".myco_state" / "autoseeded.txt").is_file()
    assert (tmp_path / "notes").is_dir()
    assert (tmp_path / "docs").is_dir()


def test_bootstrap_payload_records_context(tmp_path: Path) -> None:
    result = bootstrap(project_dir=tmp_path, substrate_id="test-sub")
    assert result.payload["substrate_id"] == "test-sub"
    assert result.payload["dry_run"] is False
    assert "_canon.yaml" in result.payload["files_created"]
    assert "MYCO.md" in result.payload["files_created"]
    assert ".myco_state/autoseeded.txt" in result.payload["files_created"]
    assert "_canon.yaml" in result.payload["preview"]


def test_bootstrap_produces_loadable_substrate(tmp_path: Path) -> None:
    bootstrap(
        project_dir=tmp_path,
        substrate_id="loadable",
        tags=["foo", "bar"],
    )
    sub = Substrate.load(tmp_path)
    assert sub.canon.substrate_id == "loadable"
    assert sub.canon.tags == ("foo", "bar")
    assert sub.canon.entry_point == "MYCO.md"
    assert sub.canon.contract_version == DEFAULT_CONTRACT_VERSION
    assert sub.is_skeleton is True


def test_bootstrap_custom_entry_point(tmp_path: Path) -> None:
    bootstrap(
        project_dir=tmp_path,
        substrate_id="symbiont",
        entry_point="CLAUDE.md",
    )
    assert (tmp_path / "CLAUDE.md").is_file()
    assert not (tmp_path / "MYCO.md").exists()
    sub = Substrate.load(tmp_path)
    assert sub.canon.entry_point == "CLAUDE.md"


def test_bootstrap_respects_custom_contract_version(tmp_path: Path) -> None:
    bootstrap(
        project_dir=tmp_path,
        substrate_id="cv-test",
        contract_version="v0.4.0-beta.1",
    )
    sub = Substrate.load(tmp_path)
    assert sub.canon.contract_version == "v0.4.0-beta.1"


def test_bootstrap_stamps_generated_at(tmp_path: Path) -> None:
    now = datetime(2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc)
    bootstrap(project_dir=tmp_path, substrate_id="stamped", now=now)
    canon_text = (tmp_path / "_canon.yaml").read_text(encoding="utf-8")
    assert "2026-04-15T12:00:00Z" in canon_text


# --- dry-run ---------------------------------------------------------------


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    result = bootstrap(project_dir=tmp_path, substrate_id="dry", dry_run=True)
    assert result.exit_code == 0
    assert result.payload["dry_run"] is True
    assert result.payload["files_created"] == ()
    # No side effects on disk.
    assert not (tmp_path / "_canon.yaml").exists()
    assert not (tmp_path / "MYCO.md").exists()
    assert not (tmp_path / ".myco_state").exists()
    # But preview is still populated.
    assert "_canon.yaml" in result.payload["preview"]


# --- refusals --------------------------------------------------------------


def test_rejects_invalid_substrate_id_whitespace(tmp_path: Path) -> None:
    with pytest.raises(UsageError, match="invalid substrate_id"):
        bootstrap(project_dir=tmp_path, substrate_id="has space")


def test_rejects_invalid_substrate_id_leading_digit(tmp_path: Path) -> None:
    with pytest.raises(UsageError, match="invalid substrate_id"):
        bootstrap(project_dir=tmp_path, substrate_id="1abc")


def test_rejects_empty_substrate_id(tmp_path: Path) -> None:
    with pytest.raises(UsageError, match="invalid substrate_id"):
        bootstrap(project_dir=tmp_path, substrate_id="")


def test_allows_mixed_case_substrate_id(tmp_path: Path) -> None:
    result = bootstrap(project_dir=tmp_path, substrate_id="ASCC-research")
    assert result.exit_code == 0


def test_creates_missing_project_dir(tmp_path: Path) -> None:
    """v0.5.8 change: germinate auto-creates ``project_dir`` when
    missing (one-shot bootstrap, per Lens 14 W1 friction finding).
    Previously it raised ``UsageError: does not exist`` and forced
    the Agent to mkdir first."""
    target = tmp_path / "nope"
    assert not target.exists()
    result = bootstrap(project_dir=target, substrate_id="x")
    assert result.exit_code == 0
    assert target.is_dir()
    assert (target / "_canon.yaml").is_file()


def test_rejects_file_as_project_dir(tmp_path: Path) -> None:
    """When ``project_dir`` points to an existing non-directory file,
    ``mkdir(exist_ok=True)`` fails with FileExistsError which germinate
    converts to a clean UsageError."""
    f = tmp_path / "f"
    f.write_text("", encoding="utf-8")
    with pytest.raises(UsageError, match="cannot prepare project_dir"):
        bootstrap(project_dir=f, substrate_id="x")


def test_refuses_when_canon_already_exists(tmp_path: Path) -> None:
    bootstrap(project_dir=tmp_path, substrate_id="first")
    with pytest.raises(ContractError, match="already exists"):
        bootstrap(project_dir=tmp_path, substrate_id="second")


def test_refuses_when_partial_state(tmp_path: Path) -> None:
    # Marker present but canon absent → corruption / interrupted genesis.
    (tmp_path / ".myco_state").mkdir()
    (tmp_path / ".myco_state" / "autoseeded.txt").write_text("", encoding="utf-8")
    with pytest.raises(ContractError, match="partial genesis state"):
        bootstrap(project_dir=tmp_path, substrate_id="x")


def test_refuses_when_entry_point_preexists(tmp_path: Path) -> None:
    (tmp_path / "MYCO.md").write_text("# pre-existing\n", encoding="utf-8")
    with pytest.raises(ContractError, match="already exists"):
        bootstrap(project_dir=tmp_path, substrate_id="x")


# --- idempotency of directory creation ------------------------------------


def test_preexisting_notes_dir_ok(tmp_path: Path) -> None:
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes" / "keepme.md").write_text("kept\n", encoding="utf-8")
    bootstrap(project_dir=tmp_path, substrate_id="keep-notes")
    # Existing notes content untouched.
    assert (tmp_path / "notes" / "keepme.md").read_text(encoding="utf-8") == "kept\n"


# --- YAML flow list rendering ---------------------------------------------


def test_tags_render_as_flow_list(tmp_path: Path) -> None:
    bootstrap(
        project_dir=tmp_path,
        substrate_id="tg",
        tags=["alpha", "beta", "gamma"],
    )
    canon_text = (tmp_path / "_canon.yaml").read_text(encoding="utf-8")
    assert 'tags: ["alpha", "beta", "gamma"]' in canon_text


def test_empty_tags_render_empty_flow_list(tmp_path: Path) -> None:
    bootstrap(project_dir=tmp_path, substrate_id="notag")
    canon_text = (tmp_path / "_canon.yaml").read_text(encoding="utf-8")
    assert "tags: []" in canon_text


# --- v0.5.16: germinate auto-registers in ~/.myco/substrates.yaml ----------


def test_bootstrap_registers_substrate_in_global_registry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Successful bootstrap writes a row into ``~/.myco/substrates.yaml``."""
    from myco.core.registry import list_substrates

    # Redirect Path.home() to an isolated tmp dir so the real user
    # registry isn't touched.
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    project_dir = tmp_path / "project"
    project_dir.mkdir()
    bootstrap(project_dir=project_dir, substrate_id="reg-test")

    entries = list_substrates(home=fake_home)
    assert len(entries) == 1
    assert entries[0].substrate_id == "reg-test"
    assert entries[0].path == project_dir.resolve()


def test_bootstrap_dry_run_skips_registry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """--dry-run must NOT touch the registry (matches its "write
    nothing" contract)."""
    from myco.core.registry import list_substrates

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: fake_home))

    project_dir = tmp_path / "project"
    project_dir.mkdir()
    bootstrap(project_dir=project_dir, substrate_id="dry", dry_run=True)

    assert list_substrates(home=fake_home) == []
