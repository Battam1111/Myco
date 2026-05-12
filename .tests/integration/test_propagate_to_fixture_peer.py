"""End-to-end federation test for ``myco propagate`` against a real
second substrate (the checked-in fixture peer).

Background: ``myco propagate`` has shipped for seven minor versions
(v0.5.x → v0.7.x) without a real cross-substrate test. The unit-test
suite at ``tests/unit/verbs/propagate/test_propagate.py`` exercises
the verb against ``tmp_path``-bootstrapped dst substrates, but a
*persisted, checked-in peer* exposes a different failure surface:

- the dst canon is authored by hand, not stamped by the live
  kernel, so canon-shape regressions surface here first;
- the peer's ``notes/raw/`` inbox must end clean after every test
  run so the fixture is reusable in CI;
- a real ``Path`` to a sibling directory exercises the Windows /
  POSIX path normalisation in ``propagate()`` end-to-end.

Fixture layout (``tests/integration/fixtures/peer_substrate/``):

- ``_canon.yaml`` — schema v2, contract v0.7.5, substrate_id
  ``peer-fixture``, write_surface allows ``notes/**``.
- ``MYCO.md`` — minimal entry point.
- ``notes/raw/.gitkeep`` — keeps the inbox dir tracked in git.

Every test in this module sets up its source substrate in
``tmp_path`` (so it is throwaway) and writes into the fixture peer.
The ``_clean_peer_inbox`` autouse fixture wipes any stamped notes
from ``peer_substrate/notes/raw/`` before AND after each test, so
the checked-in artifact is always git-clean between runs.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

# The function. ``myco.circulation`` re-exports ``propagate`` (the
# function) on the package namespace, which shadows the
# ``myco.circulation.propagate`` *submodule* for attribute lookups
# (i.e. ``import myco.circulation.propagate`` and ``from
# myco.circulation import propagate`` BOTH yield the function). The
# real submodule still lives in ``sys.modules`` after the import
# triggers it; we grab it from there in the major-mismatch test
# below.
from myco.circulation.traverse_propagate_cluster import propagate
from myco.core.canon import Canon, load_canon
from myco.core.identity_cluster import ContractError, MycoContext
from myco.digestion.cluster import parse_note, reflect
from myco.germination import bootstrap
from myco.ingestion.capture_cluster import append_note

# v0.8.5 — under pytest-xdist with `--dist=loadgroup`, this file
# and `test_propagate_3peer_network.py` both write to the shared
# `peer_substrate/` on-disk fixture; they MUST run on the same
# worker to avoid the v0.8.3-class autouse-wipe race that previously
# tripped CI intermittently. The group name is shared by both files.
pytestmark = pytest.mark.xdist_group(name="peer_substrate_shared")

# ---------------------------------------------------------------------------
# Fixture peer location + cleanup
# ---------------------------------------------------------------------------


PEER_ROOT: Path = Path(__file__).resolve().parent / "fixtures" / "peer_substrate"
PEER_INBOX: Path = PEER_ROOT / "notes" / "raw"


def _wipe_peer_inbox() -> None:
    """Remove every file under the peer's notes/raw/ except .gitkeep.

    The peer is a checked-in fixture; tests must never leave stamped
    notes behind, otherwise a second test run trips the propagate
    collision check and CI goes red on a clean main.
    """
    if not PEER_INBOX.is_dir():
        return
    for child in PEER_INBOX.iterdir():
        if child.name == ".gitkeep":
            continue
        if child.is_file():
            child.unlink()


@pytest.fixture(autouse=True)
def _clean_peer_inbox() -> Iterator[None]:
    """Ensure the fixture peer's inbox is empty before and after each test."""
    _wipe_peer_inbox()
    try:
        yield
    finally:
        _wipe_peer_inbox()


# ---------------------------------------------------------------------------
# Source-substrate helpers
# ---------------------------------------------------------------------------


def _mk_src_ctx(root: Path, *, n_notes: int = 2) -> MycoContext:
    """Bootstrap a fresh source substrate at ``root`` and seed it
    with ``n_notes`` integrated notes via the real ingestion +
    digestion pipelines.

    Mirrors the ``_seed_src`` helper in the unit-test suite so the
    integration test exercises the same authoring path the unit
    tests pin.
    """
    bootstrap(project_dir=root, substrate_id="propagate-src")
    ctx = MycoContext.for_testing(root=root)
    for i in range(n_notes):
        append_note(ctx=ctx, content=f"integration finding {i}")
    reflect(ctx=ctx)
    return ctx


# ---------------------------------------------------------------------------
# Sanity: the fixture loads
# ---------------------------------------------------------------------------


def test_fixture_peer_canon_loads() -> None:
    """Sanity check: the checked-in fixture parses cleanly under the
    live kernel. If this fails the rest of the suite is meaningless."""
    canon = load_canon(PEER_ROOT / "_canon.yaml")
    assert canon.substrate_id == "peer-fixture"
    assert canon.contract_version == "v0.7.5"
    # write_surface authorises notes/** so propagate can actually write.
    surface = canon.system.get("write_surface", {}).get("allowed", [])
    assert "notes/**" in surface


# ---------------------------------------------------------------------------
# Real propagate: integrated notes flow into the peer's raw inbox
# ---------------------------------------------------------------------------


def test_propagate_integrated_notes_to_peer_writes_raw_inbox(
    tmp_path: Path,
) -> None:
    """End-to-end happy path: propagate from a tmp source substrate
    into the checked-in peer fixture and assert the peer's inbox now
    contains stamped notes with correct provenance frontmatter."""
    src_ctx = _mk_src_ctx(tmp_path / "src", n_notes=2)

    result = propagate(
        src_ctx=src_ctx,
        dst_root=PEER_ROOT,
        select="integrated",
        commit="cafef00d",
    )

    assert result.exit_code == 0
    assert result.payload["count"] == 2
    assert result.payload["src_substrate_id"] == "propagate-src"
    assert result.payload["dry_run"] is False

    # The inbox now holds exactly the propagated files (the .gitkeep
    # is filtered out; n_/d_ prefixes were stripped per v0.5.8 fix).
    written = sorted(p for p in PEER_INBOX.glob("*.md"))
    assert len(written) == 2
    assert not any(p.name.startswith(("n_", "d_")) for p in written)

    # Every written note carries the source-trace frontmatter.
    for path in written:
        note = parse_note(path.read_text(encoding="utf-8"))
        assert note.frontmatter["source"] == "propagate-src@cafef00d"
        assert note.frontmatter["ingest_state"] == "raw"
        assert note.frontmatter["stage"] == "raw"
        assert "propagated_at" in note.frontmatter

    # The propagated paths in the payload are POSIX-style relative.
    propagated = result.payload["propagated"]
    assert all(p.startswith("notes/raw/") for p in propagated)
    assert len(propagated) == 2


# ---------------------------------------------------------------------------
# Dry-run: no writes, but the plan is reported
# ---------------------------------------------------------------------------


def test_propagate_dry_run_does_not_write(tmp_path: Path) -> None:
    """``dry_run=True`` must leave the peer's inbox untouched while
    still reporting the count and the plan paths."""
    src_ctx = _mk_src_ctx(tmp_path / "src", n_notes=2)

    # Pre-condition: inbox is empty (autouse fixture wiped it).
    assert not list(PEER_INBOX.glob("*.md"))

    result = propagate(
        src_ctx=src_ctx,
        dst_root=PEER_ROOT,
        select="integrated",
        commit="abc1234",
        dry_run=True,
    )

    # The plan was computed.
    assert result.payload["dry_run"] is True
    assert result.payload["count"] == 2
    assert len(result.payload["propagated"]) == 2
    assert all(p.startswith("notes/raw/") for p in result.payload["propagated"])

    # Nothing was actually written to the peer's inbox.
    assert not list(PEER_INBOX.glob("*.md"))


# ---------------------------------------------------------------------------
# Major-mismatch: ContractError, no writes
# ---------------------------------------------------------------------------


def test_propagate_major_mismatch_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A dst canon whose contract_version differs in MAJOR from src
    must raise ``ContractError`` and write nothing.

    We don't mutate the checked-in fixture canon — instead we
    monkeypatch ``load_canon`` inside ``myco.circulation.propagate``
    so it returns a Canon with a bumped major when the dst path is
    the fixture peer's _canon.yaml. The source's canon load (via
    ``MycoContext.substrate.canon``) is unaffected.
    """
    src_ctx = _mk_src_ctx(tmp_path / "src", n_notes=1)

    real_load_canon = load_canon
    fixture_canon_path = (PEER_ROOT / "_canon.yaml").resolve()

    def fake_load_canon(path: Path) -> Canon:
        canon = real_load_canon(path)
        if path.resolve() == fixture_canon_path:
            # Replace the dst canon's contract_version with a v1.x
            # value — same dataclass, just bumped major.
            return Canon(
                schema_version=canon.schema_version,
                contract_version="v1.0.0",
                identity=canon.identity,
                system=canon.system,
                subsystems=canon.subsystems,
                synced_contract_version=canon.synced_contract_version,
                versioning=canon.versioning,
                lint=canon.lint,
                commands=canon.commands,
                metrics=canon.metrics,
                waves=canon.waves,
                extras=canon.extras,
            )
        return canon

    # The submodule is in ``sys.modules`` from our top-of-file import.
    # We can't reach it via ``myco.circulation.propagate`` attribute
    # access — that name resolves to the re-exported function — so we
    # pull it out of ``sys.modules`` directly. Patching ``load_canon``
    # on the submodule swings the binding ``propagate()`` actually
    # uses for the dst-canon read.
    submodule = sys.modules["myco.circulation.traverse_propagate_cluster"]
    monkeypatch.setattr(submodule, "load_canon", fake_load_canon)

    with pytest.raises(ContractError, match="major mismatch"):
        propagate(src_ctx=src_ctx, dst_root=PEER_ROOT)

    # No partial writes: the inbox is still clean.
    assert not list(PEER_INBOX.glob("*.md"))


# ---------------------------------------------------------------------------
# Collision: ContractError, no partial writes
# ---------------------------------------------------------------------------


def test_propagate_collision_raises(tmp_path: Path) -> None:
    """If a target name already exists in the peer's inbox, propagate
    must raise ``ContractError`` BEFORE writing anything (the verb is
    transactional: collect → verify → write-all-or-raise).

    v0.8.3 hotfix: use a per-test tmp peer (cloned from the fixture
    template) instead of the shared `PEER_ROOT` to avoid xdist
    parallelism races where a sibling test's autouse cleanup wipes
    the shared inbox between this test's pre-write and propagate
    call. The sibling test's own _clean_peer_inbox autouse fixture
    runs against PEER_INBOX, NOT this test's tmp clone.
    """
    src_ctx = _mk_src_ctx(tmp_path / "src", n_notes=2)

    # Clone the fixture peer to a tmp dir so xdist parallel test
    # cleanup can't wipe our pre-written collision file mid-test.
    import shutil

    tmp_peer = tmp_path / "peer_substrate"
    shutil.copytree(PEER_ROOT, tmp_peer)
    tmp_peer_inbox = tmp_peer / "notes" / "raw"
    # Ensure the inbox is clean before this test's pre-write.
    for f in tmp_peer_inbox.glob("*.md"):
        f.unlink()

    # Pre-write a colliding file in our isolated tmp peer's inbox.
    integrated_dir = src_ctx.substrate.paths.notes / "integrated"
    src_files = sorted(integrated_dir.glob("n_*.md"))
    assert len(src_files) == 2, "src setup should have 2 integrated notes"
    # The propagator strips the n_ prefix; that's the dst filename.
    collide_name = src_files[0].name[len("n_") :]
    pre_existing = tmp_peer_inbox / collide_name
    pre_existing.write_text("pre-existing inbox content\n", encoding="utf-8")
    pre_existing_mtime = pre_existing.stat().st_mtime

    with pytest.raises(ContractError, match="collision"):
        propagate(src_ctx=src_ctx, dst_root=tmp_peer, commit="deadbeef")

    # Pre-existing content is unchanged.
    assert pre_existing.read_text(encoding="utf-8") == "pre-existing inbox content\n"
    assert pre_existing.stat().st_mtime == pre_existing_mtime
    # The non-colliding sibling was NOT written either — the verb is
    # transactional, so a single collision aborts the whole batch.
    other_name = src_files[1].name[len("n_") :]
    assert not (tmp_peer_inbox / other_name).exists()
