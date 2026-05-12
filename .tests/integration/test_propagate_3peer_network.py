"""End-to-end federation test for ``myco propagate``'s **N-peer
fan-out** (v0.7.10) against three real checked-in fixture substrates.

Background: v0.5.x-v0.7.5 ``myco propagate`` accepted a single
``dst_root: Path`` and federated to a single downstream peer. The L0
P5 mycelium-graph promise spans federated substrates *plural*, so
v0.7.10 generalises the verb's contract to N peers via the new
``dst_roots: list[Path] | Path`` keyword while preserving the legacy
``dst_root=`` scalar shape (single-peer callers, including the v0.7.5
integration tests at ``test_propagate_to_fixture_peer.py``, continue
to work unchanged).

The contract this test pins:

- **Fan-out**: the same source-note set lands in EVERY peer's
  ``notes/raw/`` inbox.
- **Transactional across all peers**: a collision on any one peer,
  or a contract-MAJOR mismatch on any one peer's canon, raises
  ``ContractError`` BEFORE any writes — none of the peers receive
  partial output.
- **Backwards compat**: ``dst_root=Path(...)`` still works; passing
  ``dst_roots=Path(...)`` (a bare scalar in the new keyword) is sugar
  for a 1-element list.
- **Payload**: the v0.7.10 ``payload["dst_roots"]`` tuple is always
  present; the legacy ``payload["dst_root"]`` is kept as the FIRST
  peer's path for callers that pre-date the bump.

Fixtures (one canon-shape, three identities):

- ``tests/integration/fixtures/peer_substrate/``     — substrate_id ``peer-fixture``
- ``tests/integration/fixtures/peer_substrate_b/``   — substrate_id ``peer-fixture-b``
- ``tests/integration/fixtures/peer_substrate_c/``   — substrate_id ``peer-fixture-c``

The autouse ``_clean_all_peer_inboxes`` fixture wipes every peer's
``notes/raw/`` (preserving each peer's ``.gitkeep``) before AND after
each test, so the checked-in artifacts are always git-clean between
runs and a partial-write regression in one test cannot pollute the
fixture for the next.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from myco.circulation.propagate import propagate
from myco.core.canon import Canon, load_canon
from myco.core.context import MycoContext
from myco.core.errors import ContractError
from myco.digestion.assimilate import reflect
from myco.digestion.pipeline import parse_note
from myco.germination import bootstrap
from myco.ingestion.eat import append_note

# v0.8.5 — under pytest-xdist with `--dist=loadgroup`, this file
# and `test_propagate_to_fixture_peer.py` both write to the shared
# `peer_substrate/` on-disk fixture; they MUST run on the same
# worker to avoid the v0.8.3-class autouse-wipe race that previously
# tripped CI intermittently. The group name is shared by both files.
pytestmark = pytest.mark.xdist_group(name="peer_substrate_shared")

# ---------------------------------------------------------------------------
# Three peer fixtures + cleanup
# ---------------------------------------------------------------------------


_FIXTURES: Path = Path(__file__).resolve().parent / "fixtures"
PEER_A_ROOT: Path = _FIXTURES / "peer_substrate"
PEER_B_ROOT: Path = _FIXTURES / "peer_substrate_b"
PEER_C_ROOT: Path = _FIXTURES / "peer_substrate_c"

PEER_A_INBOX: Path = PEER_A_ROOT / "notes" / "raw"
PEER_B_INBOX: Path = PEER_B_ROOT / "notes" / "raw"
PEER_C_INBOX: Path = PEER_C_ROOT / "notes" / "raw"

ALL_PEERS: tuple[Path, ...] = (PEER_A_ROOT, PEER_B_ROOT, PEER_C_ROOT)
ALL_INBOXES: tuple[Path, ...] = (PEER_A_INBOX, PEER_B_INBOX, PEER_C_INBOX)


def _wipe_inbox(inbox: Path) -> None:
    """Remove every file under ``inbox`` except ``.gitkeep``.

    Each peer's ``.gitkeep`` MUST survive — it keeps the inbox
    directory tracked in git, so a fresh checkout doesn't lose the
    federation target. A test that accidentally wipes ``.gitkeep``
    would tip the next CI run into "missing inbox dir" territory.
    """
    if not inbox.is_dir():
        return
    for child in inbox.iterdir():
        if child.name == ".gitkeep":
            continue
        if child.is_file():
            child.unlink()


@pytest.fixture(autouse=True)
def _clean_all_peer_inboxes() -> Iterator[None]:
    """Wipe every fixture peer's inbox before and after each test.

    Fan-out tests can leave debris on multiple peers; this autouse
    fixture guarantees a clean slate for every test (including the
    transactional ones, where the test itself seeds + verifies a
    pre-existing collision file on a specific peer).
    """
    for inbox in ALL_INBOXES:
        _wipe_inbox(inbox)
    try:
        yield
    finally:
        for inbox in ALL_INBOXES:
            _wipe_inbox(inbox)


# ---------------------------------------------------------------------------
# Source-substrate helper
# ---------------------------------------------------------------------------


def _mk_src_ctx(root: Path, *, n_notes: int = 2) -> MycoContext:
    """Bootstrap a fresh source substrate at ``root`` and seed it with
    ``n_notes`` integrated notes via the real ingestion + digestion
    pipelines. Mirrors ``_mk_src_ctx`` in the single-peer integration
    test so both suites exercise the same authoring path.
    """
    bootstrap(project_dir=root, substrate_id="propagate-src-3peer")
    ctx = MycoContext.for_testing(root=root)
    for i in range(n_notes):
        append_note(ctx=ctx, content=f"3-peer integration finding {i}")
    reflect(ctx=ctx)
    return ctx


def _list_propagated_files(inbox: Path) -> list[Path]:
    """Return every ``*.md`` under ``inbox`` (so a stray ``.gitkeep`` —
    which is not a markdown file — is not counted)."""
    return sorted(inbox.glob("*.md"))


# ---------------------------------------------------------------------------
# Sanity: all three fixtures load
# ---------------------------------------------------------------------------


def test_three_peer_fixtures_load_with_distinct_ids() -> None:
    """Pre-flight: the three peer canons parse cleanly under the live
    kernel and report distinct substrate_ids. If this fails the rest
    of the suite is meaningless."""
    canon_a = load_canon(PEER_A_ROOT / "_canon.yaml")
    canon_b = load_canon(PEER_B_ROOT / "_canon.yaml")
    canon_c = load_canon(PEER_C_ROOT / "_canon.yaml")
    assert canon_a.substrate_id == "peer-fixture"
    assert canon_b.substrate_id == "peer-fixture-b"
    assert canon_c.substrate_id == "peer-fixture-c"
    # All three pin v0.7.5 contract — same MAJOR as the live src
    # kernel, different MINOR (compat warning is fine).
    for canon in (canon_a, canon_b, canon_c):
        assert canon.contract_version == "v0.7.5"


# ---------------------------------------------------------------------------
# Happy path: fan-out lands the SAME notes in ALL three peers
# ---------------------------------------------------------------------------


def test_propagate_fans_out_to_all_peers(tmp_path: Path) -> None:
    """Source has 2 integrated notes; peers a/b/c are all empty;
    after one ``propagate`` call, every peer's inbox holds both
    notes with identical stems and stamped frontmatter.
    """
    src_ctx = _mk_src_ctx(tmp_path / "src", n_notes=2)

    # Pre-condition: every peer's inbox is empty (autouse fixture wiped).
    for inbox in ALL_INBOXES:
        assert not _list_propagated_files(inbox)

    result = propagate(
        src_ctx=src_ctx,
        dst_roots=[PEER_A_ROOT, PEER_B_ROOT, PEER_C_ROOT],
        select="integrated",
        commit="cafef00d",
    )

    assert result.exit_code == 0
    # Total writes = 2 notes x 3 peers.
    assert result.payload["count"] == 6
    assert result.payload["src_substrate_id"] == "propagate-src-3peer"
    assert result.payload["dry_run"] is False

    # Each peer received exactly the 2 source notes (n_/d_ prefix
    # stripped per v0.5.8 fix).
    stems_per_peer: list[set[str]] = []
    for inbox in ALL_INBOXES:
        files = _list_propagated_files(inbox)
        assert len(files) == 2, f"peer {inbox} should have 2 notes, got {len(files)}"
        assert not any(f.name.startswith(("n_", "d_")) for f in files)
        # Every note carries the source-trace stamp.
        for path in files:
            note = parse_note(path.read_text(encoding="utf-8"))
            assert note.frontmatter["source"] == "propagate-src-3peer@cafef00d"
            assert note.frontmatter["ingest_state"] == "raw"
            assert note.frontmatter["stage"] == "raw"
            assert "propagated_at" in note.frontmatter
        stems_per_peer.append({f.name for f in files})

    # Every peer received the SAME stems — that's what "fan-out"
    # means. (The frontmatter timestamps tie them to a single now.)
    assert stems_per_peer[0] == stems_per_peer[1] == stems_per_peer[2]


# ---------------------------------------------------------------------------
# Transactional: a collision on peer_b leaves peer_a + peer_c untouched
# ---------------------------------------------------------------------------


def test_propagate_transactional_across_peers(tmp_path: Path) -> None:
    """Pre-stage a colliding file in peer_b's inbox. Propagate must
    raise ``ContractError`` (citing peer_b) and leave peer_a and
    peer_c COMPLETELY untouched — the verb is transactional across
    peers, not per-peer.
    """
    src_ctx = _mk_src_ctx(tmp_path / "src", n_notes=2)

    # Discover what stems the propagator will produce — we need to
    # plant a collision under one of those exact names.
    integrated_dir = src_ctx.substrate.paths.notes / "integrated"
    src_files = sorted(integrated_dir.glob("n_*.md"))
    assert len(src_files) == 2, "src setup should have 2 integrated notes"
    # The propagator strips the leading n_/d_; that's the dst stem.
    collide_name = src_files[0].name[len("n_") :]

    # Plant the collision exclusively on peer_b. peer_a and peer_c
    # remain pristine going in.
    pre_existing = PEER_B_INBOX / collide_name
    pre_existing.write_text("pre-existing peer_b content\n", encoding="utf-8")
    pre_existing_mtime = pre_existing.stat().st_mtime

    with pytest.raises(ContractError, match="collision"):
        propagate(
            src_ctx=src_ctx,
            dst_roots=[PEER_A_ROOT, PEER_B_ROOT, PEER_C_ROOT],
            commit="deadbeef",
        )

    # Peer_b's pre-existing file is untouched (verb refused to overwrite).
    assert pre_existing.read_text(encoding="utf-8") == "pre-existing peer_b content\n"
    assert pre_existing.stat().st_mtime == pre_existing_mtime
    # Peer_b did NOT receive the OTHER (non-colliding) note either —
    # one collision aborts the whole peer.
    other_name = src_files[1].name[len("n_") :]
    assert not (PEER_B_INBOX / other_name).exists()
    # Peer_a and peer_c are completely untouched: NO writes anywhere
    # (this is the cross-peer transactional contract).
    assert not _list_propagated_files(PEER_A_INBOX), (
        "peer_a should be untouched when peer_b collides — "
        "propagate must be transactional across all peers, not per-peer"
    )
    assert not _list_propagated_files(PEER_C_INBOX), (
        "peer_c should be untouched when peer_b collides — "
        "propagate must be transactional across all peers, not per-peer"
    )


# ---------------------------------------------------------------------------
# Mixed major versions: monkeypatch peer_b to v1.0; nothing gets written
# ---------------------------------------------------------------------------


def test_propagate_rejects_mixed_major_versions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A single peer with a contract-MAJOR mismatch poisons the whole
    fan-out: propagate raises ``ContractError`` and writes nothing
    to any peer (including the compatible ones).

    We don't mutate the checked-in fixture canons — instead we
    monkeypatch ``load_canon`` inside the propagate submodule so
    that peer_b's canon read returns a Canon with a bumped major.
    Peer_a and peer_c still load normally.
    """
    src_ctx = _mk_src_ctx(tmp_path / "src", n_notes=1)

    real_load_canon = load_canon
    peer_b_canon_path = (PEER_B_ROOT / "_canon.yaml").resolve()

    def fake_load_canon(path: Path) -> Canon:
        canon = real_load_canon(path)
        if path.resolve() == peer_b_canon_path:
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

    # Reach the submodule via sys.modules — the package re-exports
    # ``propagate`` (the function), which shadows the submodule for
    # attribute access. Patching ``load_canon`` on the submodule
    # swings the binding ``propagate()`` actually uses for canon reads.
    submodule = sys.modules["myco.circulation.propagate"]
    monkeypatch.setattr(submodule, "load_canon", fake_load_canon)

    with pytest.raises(ContractError, match="major mismatch"):
        propagate(
            src_ctx=src_ctx,
            dst_roots=[PEER_A_ROOT, PEER_B_ROOT, PEER_C_ROOT],
        )

    # No partial writes anywhere — the major mismatch was caught in
    # round 1a, before any source notes were even read.
    for inbox in ALL_INBOXES:
        assert not _list_propagated_files(inbox), (
            f"peer at {inbox} should be untouched; mixed-major must abort "
            f"BEFORE any writes"
        )


# ---------------------------------------------------------------------------
# Backwards compat: legacy dst_root=Path(...) shape still works
# ---------------------------------------------------------------------------


def test_propagate_single_peer_backwards_compat(tmp_path: Path) -> None:
    """Pass ``dst_root=Path(...)`` — the legacy v0.5.x-v0.7.5 shape —
    and verify the v0.7.10 implementation handles it identically to a
    1-element ``dst_roots`` list. This is the contract the existing
    5 single-peer tests at ``test_propagate_to_fixture_peer.py``
    rely on; the N-peer generalisation must NOT break it.
    """
    src_ctx = _mk_src_ctx(tmp_path / "src", n_notes=2)

    # Legacy keyword shape: a bare Path under dst_root=.
    result = propagate(
        src_ctx=src_ctx,
        dst_root=PEER_A_ROOT,
        commit="legacy01",
    )
    assert result.exit_code == 0
    assert result.payload["count"] == 2  # 2 notes x 1 peer
    # The legacy scalar field is still in the payload.
    assert result.payload["dst_root"] == str(PEER_A_ROOT.resolve())
    # The new tuple is also present and contains exactly the one peer.
    assert result.payload["dst_roots"] == (str(PEER_A_ROOT.resolve()),)
    # Only peer_a received writes.
    assert len(_list_propagated_files(PEER_A_INBOX)) == 2
    assert not _list_propagated_files(PEER_B_INBOX)
    assert not _list_propagated_files(PEER_C_INBOX)


# ---------------------------------------------------------------------------
# Payload contract: the new dst_roots tuple is always present
# ---------------------------------------------------------------------------


def test_propagate_payload_dst_roots_field_present(tmp_path: Path) -> None:
    """The v0.7.10 payload contract: ``dst_roots`` is a tuple of
    resolved peer-path strings, in input order. Also verify the
    backwards-compat scalar ``dst_root`` is the FIRST peer's path
    (so legacy callers reading ``payload["dst_root"]`` keep working).
    """
    src_ctx = _mk_src_ctx(tmp_path / "src", n_notes=1)

    result = propagate(
        src_ctx=src_ctx,
        dst_roots=[PEER_A_ROOT, PEER_B_ROOT, PEER_C_ROOT],
        commit="payload1",
    )
    assert result.exit_code == 0

    dst_roots = result.payload["dst_roots"]
    assert isinstance(dst_roots, tuple)
    assert len(dst_roots) == 3
    # Order is preserved — first input peer is first in the tuple.
    assert dst_roots == (
        str(PEER_A_ROOT.resolve()),
        str(PEER_B_ROOT.resolve()),
        str(PEER_C_ROOT.resolve()),
    )
    # The legacy scalar mirrors the FIRST peer for back-compat.
    assert result.payload["dst_root"] == dst_roots[0]
    # Sanity: 1 note x 3 peers = 3 writes.
    assert result.payload["count"] == 3
    assert len(result.payload["propagated"]) == 3
