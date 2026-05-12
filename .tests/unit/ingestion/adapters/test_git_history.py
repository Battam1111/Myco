"""Tests for the git-history adapter (one IngestResult per commit).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Adapters", and L0 P2 (永恒吞噬). A repo's history is a stream of
decisions and frictions; each commit is its own ingestible record.

These tests pin the contract for the v0.7.x git-history adapter:

* ``can_handle`` — accepts only ``<repo>/.git`` directly, or a
  working tree containing both ``.git/`` and a ``.git-history``
  marker file. Rejects everything else.
* ``ingest`` — emits one IngestResult per commit, capped at
  :data:`MAX_COMMITS`. Failed-stub on every former silent-skip
  path: missing git binary, subprocess timeout, nonzero git exit
  status (corrupt ``.git``), empty repo, cap-hit truncation.
* Author email / subject / body / strict-ISO date round-trip
  exactly through the NUL-separated parser, including unicode and
  multi-line bodies (merge commits, conventional-commit footers).

The tests use real ``git init`` + ``git commit`` against a tmp_path
fixture rather than mocking subprocess — that way the parser's
contract with git is exercised end-to-end. Two tests (cap-truncation
and timeout) intentionally mock ``subprocess.run`` because creating
a 1500-commit fixture would be slow and a real timeout is racy.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from myco.ingestion.adapters.git_history import (
    MARKER_FILENAME,
    MAX_COMMITS,
    GitHistoryAdapter,
)

# Skip the entire module on any host without git on PATH. The user's
# host (Windows) has git 2.39.2, but CI on a stripped-down container
# might not — we'd rather skip than emit cryptic failures.
_GIT = shutil.which("git")
pytestmark = pytest.mark.skipif(_GIT is None, reason="git binary not available on PATH")


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


def _git_env() -> dict[str, str]:
    """Return an env dict that lets ``git commit`` work without the
    user's global config (no ``user.name`` / ``user.email`` set).

    Sets author + committer identity, an empty HOME so the user's
    ``~/.gitconfig`` can't leak in, ``GIT_TERMINAL_PROMPT=0`` so any
    accidental credential prompt fails fast instead of hanging, and
    ``GIT_CONFIG_NOSYSTEM=1`` to skip system config too.
    """
    return {
        **os.environ,
        "GIT_AUTHOR_NAME": "Test Author",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test Author",
        "GIT_COMMITTER_EMAIL": "test@example.com",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_CONFIG_NOSYSTEM": "1",
        # Empty HOME so global ~/.gitconfig doesn't override our
        # explicit env vars on hosts that have one (Windows users
        # typically do).
        "HOME": "",
        # Ditto for Windows-style HOME.
        "USERPROFILE": "",
    }


def _run_git(repo: Path, *args: str, env: dict[str, str] | None = None) -> None:
    """Run a git command against ``repo`` synchronously. Raises on
    nonzero exit so test setup failures don't masquerade as logic
    bugs in the adapter."""
    subprocess.run(
        [_GIT, *args],
        cwd=str(repo),
        env=env or _git_env(),
        check=True,
        capture_output=True,
        timeout=20,
    )


def _make_repo(
    root: Path,
    commits: list[tuple[str, str]] | None = None,
) -> Path:
    """Initialise a git repo at ``root`` with the given commits.

    ``commits`` is a list of ``(filename, message)`` pairs; each pair
    creates the named file with one-line content and commits it with
    the given message. Default: a single commit so callers can ask
    for a non-empty repo with one line.

    Returns ``root`` for fluent chaining.
    """
    root.mkdir(parents=True, exist_ok=True)
    # Use --initial-branch so this works on hosts where git's default
    # branch name is configured to something we can't predict.
    _run_git(root, "init", "--initial-branch=main", "--quiet")
    if commits is None:
        commits = [("README.md", "initial commit")]
    for filename, message in commits:
        (root / filename).write_text(f"content for {message}\n", encoding="utf-8")
        _run_git(root, "add", filename)
        _run_git(root, "commit", "-m", message, "--quiet")
    return root


# ---------------------------------------------------------------------------
# can_handle
# ---------------------------------------------------------------------------


def test_can_handle_dot_git_directory(tmp_path: Path) -> None:
    """``<repo>/.git`` is the canonical opt-in shape."""
    repo = _make_repo(tmp_path / "repo")
    assert GitHistoryAdapter().can_handle(str(repo / ".git")) is True


def test_can_handle_git_dir_with_marker(tmp_path: Path) -> None:
    """A working tree with a ``.git-history`` marker file opts in."""
    repo = _make_repo(tmp_path / "repo")
    (repo / MARKER_FILENAME).write_text("", encoding="utf-8")
    assert GitHistoryAdapter().can_handle(str(repo)) is True


def test_can_handle_rejects_non_git_dir(tmp_path: Path) -> None:
    """A plain directory with no ``.git/`` and no marker is rejected.

    Without this guard, the adapter would happily run git in any tmp
    dir and emit a single "fatal: not a git repository" failed-stub
    on every directory ingest — code_repo's job, not ours."""
    plain = tmp_path / "not-a-repo"
    plain.mkdir()
    (plain / "hello.txt").write_text("hi\n", encoding="utf-8")
    assert GitHistoryAdapter().can_handle(str(plain)) is False


def test_can_handle_rejects_working_tree_without_marker(tmp_path: Path) -> None:
    """A working tree (with ``.git/``) but NO marker file is rejected
    so code_repo gets the directory as expected. The marker file is
    the explicit opt-in."""
    repo = _make_repo(tmp_path / "repo")
    assert GitHistoryAdapter().can_handle(str(repo)) is False


def test_can_handle_rejects_file(tmp_path: Path) -> None:
    """A regular file is never claimed (directory-scope adapter)."""
    f = tmp_path / "stray.git"
    f.write_text("not really a git dir\n", encoding="utf-8")
    assert GitHistoryAdapter().can_handle(str(f)) is False


def test_can_handle_rejects_dot_git_lookalike(tmp_path: Path) -> None:
    """A directory named ``.git`` but missing ``HEAD`` is rejected
    (e.g. an empty placeholder a user accidentally created)."""
    fake = tmp_path / ".git"
    fake.mkdir()
    assert GitHistoryAdapter().can_handle(str(fake)) is False


# ---------------------------------------------------------------------------
# ingest — happy path
# ---------------------------------------------------------------------------


def test_ingest_emits_one_result_per_commit(tmp_path: Path) -> None:
    """A 3-commit repo → 3 ok IngestResults (cap not hit)."""
    repo = _make_repo(
        tmp_path / "repo",
        commits=[
            ("a.txt", "first"),
            ("b.txt", "second"),
            ("c.txt", "third"),
        ],
    )
    results = list(GitHistoryAdapter().ingest(str(repo / ".git")))
    assert len(results) == 3
    assert all(r.status == "ok" for r in results)
    # Most recent commit first per ``git log`` default ordering.
    subjects = [r.metadata["subject"] for r in results]
    assert subjects == ["third", "second", "first"]
    assert all(r.metadata["kind"] == "git-commit" for r in results)
    assert all(len(r.metadata["commit_sha"]) == 40 for r in results)


def test_ingest_extracts_author_email_subject_body(tmp_path: Path) -> None:
    """Author name / email / subject / body all round-trip correctly."""
    repo = _make_repo(tmp_path / "repo", commits=[])
    # Commit with a multi-line body so we can pin %B parsing.
    (repo / "feature.py").write_text("def f(): ...\n", encoding="utf-8")
    _run_git(repo, "add", "feature.py")
    _run_git(
        repo,
        "commit",
        "-m",
        "feat: add f",
        "-m",
        "Long-form body explaining\nwhy f exists.",
        "--quiet",
    )
    results = list(GitHistoryAdapter().ingest(str(repo / ".git")))
    assert len(results) == 1
    md = results[0].metadata
    assert md["author_name"] == "Test Author"
    assert md["author_email"] == "test@example.com"
    assert md["subject"] == "feat: add f"
    # %B is subject + blank + body; body field carries the whole thing.
    body = results[0].body
    assert "feat: add f" in body
    assert "Long-form body explaining" in body
    assert "why f exists." in body


def test_ingest_iso_date_parses_correctly(tmp_path: Path) -> None:
    """``%aI`` produces strict ISO 8601 with timezone offset.

    We don't pin the exact value (it depends on commit time) but
    we DO pin the shape: ``YYYY-MM-DDTHH:MM:SS±HH:MM`` or ``Z``.
    """
    import re

    repo = _make_repo(tmp_path / "repo")
    results = list(GitHistoryAdapter().ingest(str(repo / ".git")))
    assert len(results) == 1
    iso = results[0].metadata["author_date_iso"]
    # Strict ISO 8601 with offset. Permits Z, +HH:MM, or -HH:MM.
    pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})$"
    assert re.match(pattern, iso), f"not strict ISO 8601: {iso!r}"


def test_ingest_handles_unicode_in_commit_messages(tmp_path: Path) -> None:
    """Unicode (CJK + emoji) in subjects and bodies survives the
    NUL-separated wire protocol and the UTF-8 decode step."""
    repo = _make_repo(tmp_path / "repo", commits=[])
    (repo / "i18n.txt").write_text("hello\n", encoding="utf-8")
    _run_git(repo, "add", "i18n.txt")
    subject = "feat(初始化): 添加菌丝触手 🍄"
    body = "L2 doctrine 增补:\n• 永恒吞噬\n• 菌丝网络 🌐"
    _run_git(
        repo,
        "commit",
        "-m",
        subject,
        "-m",
        body,
        "--quiet",
    )
    results = list(GitHistoryAdapter().ingest(str(repo / ".git")))
    assert len(results) == 1
    assert results[0].metadata["subject"] == subject
    assert "添加菌丝触手" in results[0].body
    assert "永恒吞噬" in results[0].body
    assert "🍄" in results[0].body
    assert "🌐" in results[0].body


def test_ingest_handles_merge_commits(tmp_path: Path) -> None:
    """A merge commit's ``%B`` (subject + body) is captured intact.

    We create a side branch, commit on it, switch back to main, and
    merge with ``--no-ff`` to force a merge commit. The resulting
    history has 3 commits: initial, side, merge. The merge commit's
    body lists the parents (when --no-ff and a default merge
    message), which is what we want to preserve."""
    repo = _make_repo(tmp_path / "repo")  # initial commit on main
    _run_git(repo, "checkout", "-b", "side", "--quiet")
    (repo / "side.txt").write_text("from side\n", encoding="utf-8")
    _run_git(repo, "add", "side.txt")
    _run_git(repo, "commit", "-m", "side commit", "--quiet")
    _run_git(repo, "checkout", "main", "--quiet")
    # --no-ff forces a merge commit even when fast-forward is possible.
    _run_git(
        repo,
        "merge",
        "--no-ff",
        "side",
        "-m",
        "Merge branch 'side'",
        "--quiet",
    )
    results = list(GitHistoryAdapter().ingest(str(repo / ".git")))
    # Initial + side + merge = 3 commits.
    assert len(results) == 3
    subjects = [r.metadata["subject"] for r in results]
    assert "Merge branch 'side'" in subjects
    assert "side commit" in subjects
    assert "initial commit" in subjects


def test_ingest_marker_file_path_works(tmp_path: Path) -> None:
    """Pointing at a working tree with a ``.git-history`` marker
    works and routes through git_dir = <tree>/.git internally."""
    repo = _make_repo(
        tmp_path / "repo", commits=[("a.txt", "alpha"), ("b.txt", "bravo")]
    )
    (repo / MARKER_FILENAME).write_text("", encoding="utf-8")
    results = list(GitHistoryAdapter().ingest(str(repo)))
    # The marker file IS in the working tree, so git log sees it as
    # untracked but does not produce a commit for it. We expect only
    # the 2 commits we made.
    ok_results = [r for r in results if r.status == "ok"]
    assert len(ok_results) == 2
    assert {r.metadata["subject"] for r in ok_results} == {"alpha", "bravo"}


# ---------------------------------------------------------------------------
# ingest — failure paths (failed-stub contract)
# ---------------------------------------------------------------------------


def test_ingest_empty_repo_returns_failed_stub(tmp_path: Path) -> None:
    """A freshly-initialised repo with zero commits → single failed-stub."""
    repo = tmp_path / "empty"
    repo.mkdir()
    _run_git(repo, "init", "--initial-branch=main", "--quiet")
    results = list(GitHistoryAdapter().ingest(str(repo / ".git")))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "no commits" in results[0].failure_reason.lower()


def test_ingest_corrupt_git_dir_returns_failed_stub(tmp_path: Path) -> None:
    """A ``.git`` directory whose ``HEAD`` references a missing ref
    (or whose object store is truncated) → failed-stub.

    We simulate corruption by zeroing out the ``HEAD`` file after
    ``can_handle`` would have accepted the path. That means the adapter
    must gracefully handle a nonzero exit from ``git log``.
    """
    repo = _make_repo(tmp_path / "repo")
    head = repo / ".git" / "HEAD"
    # HEAD must still exist for can_handle to pass, but we replace its
    # content with garbage so git log fails.
    head.write_text("ref: refs/heads/does-not-exist\n", encoding="utf-8")
    # Also nuke the refs dir so even fallback can't find anything.
    refs = repo / ".git" / "refs"
    if refs.is_dir():
        shutil.rmtree(refs)
    results = list(GitHistoryAdapter().ingest(str(repo / ".git")))
    assert len(results) == 1
    assert results[0].status == "failed"
    # Either the nonzero-exit branch or the no-commits branch can
    # legitimately fire here (depending on git version's tolerance).
    reason = results[0].failure_reason.lower()
    assert "git log" in reason or "no commits" in reason


def test_ingest_git_not_on_path_returns_failed_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``shutil.which("git")`` returning ``None`` → failed-stub naming
    the missing binary. Defensive case for stripped containers."""
    repo = _make_repo(tmp_path / "repo")
    # Patch the import inside the adapter module, not the top-level
    # shutil — the adapter does ``shutil.which("git")`` so we need
    # the module-level shutil reference patched.
    monkeypatch.setattr(
        "myco.ingestion.adapters.git_history.shutil.which",
        lambda name: None,
    )
    results = list(GitHistoryAdapter().ingest(str(repo / ".git")))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "not found" in results[0].failure_reason.lower()
    assert "git" in results[0].failure_reason.lower()


def test_ingest_subprocess_timeout_returns_failed_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A subprocess.TimeoutExpired raised by ``subprocess.run`` →
    single failed-stub mentioning the timeout, not a raised exception
    that crashes ``myco eat``."""
    repo = _make_repo(tmp_path / "repo")

    def _raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0] if args else "git", timeout=30)

    monkeypatch.setattr(
        "myco.ingestion.adapters.git_history.subprocess.run",
        _raise_timeout,
    )
    results = list(GitHistoryAdapter().ingest(str(repo / ".git")))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "timed out" in results[0].failure_reason.lower()


def test_ingest_truncates_at_1000_commits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Mocked subprocess emitting 1500 commits → 1000 ok results +
    1 failed-stub truncation notice. We don't make 1500 real commits
    (slow + flaky); we synthesize the wire format directly to exercise
    the truncation branch deterministically."""
    repo = _make_repo(tmp_path / "repo")

    # Build a 1500-record wire stream matching the adapter's
    # ``%H\\x00%aI\\x00%aN\\x00%aE\\x00%s\\x00%B\\x00END\\x00`` layout.
    n_synth = 1500
    parts: list[str] = []
    for i in range(n_synth):
        sha = f"{i:040x}"  # 40-char hex
        parts.extend(
            [
                sha,
                "2026-05-10T00:00:00+00:00",
                "Test Author",
                "test@example.com",
                f"subject {i}",
                f"subject {i}\n\nbody {i}",
                "END",
            ]
        )
    fake_stdout = "\x00".join(parts)

    class _FakeCompleted:
        returncode = 0
        stdout = fake_stdout
        stderr = ""

    def _fake_run(*args, **kwargs):
        return _FakeCompleted()

    monkeypatch.setattr("myco.ingestion.adapters.git_history.subprocess.run", _fake_run)
    results = list(GitHistoryAdapter().ingest(str(repo / ".git")))
    ok_results = [r for r in results if r.status == "ok"]
    failed_results = [r for r in results if r.status == "failed"]
    assert len(ok_results) == MAX_COMMITS
    assert len(failed_results) == 1
    assert "cap hit" in failed_results[0].failure_reason
    assert str(MAX_COMMITS) in failed_results[0].failure_reason
    # Ordering is preserved: first ok result is commit 0.
    assert ok_results[0].metadata["subject"] == "subject 0"
    assert ok_results[-1].metadata["subject"] == f"subject {MAX_COMMITS - 1}"


def test_ingest_target_not_a_git_dir_returns_failed_stub(tmp_path: Path) -> None:
    """A direct ``ingest`` call on a non-git directory (bypassing
    ``can_handle``) returns a failed-stub instead of crashing.
    Belt-and-suspenders defense per the v0.7.3 AD1 protocol."""
    plain = tmp_path / "plain"
    plain.mkdir()
    results = list(GitHistoryAdapter().ingest(str(plain)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "not a .git" in results[0].failure_reason.lower() or (
        "marker" in results[0].failure_reason.lower()
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


def test_git_history_adapter_registered() -> None:
    """The adapter is discoverable in the global registry, and
    registers BEFORE ``CodeRepoAdapter`` so a marker-file working tree
    routes to git-history rather than being slurped as a code repo."""
    from myco.ingestion.adapters import all_adapters
    from myco.ingestion.adapters.code_repo import CodeRepoAdapter as CR
    from myco.ingestion.adapters.git_history import GitHistoryAdapter as GH

    adapters = list(all_adapters())
    gh_idx = next((i for i, a in enumerate(adapters) if isinstance(a, GH)), -1)
    cr_idx = next((i for i, a in enumerate(adapters) if isinstance(a, CR)), -1)
    assert gh_idx >= 0, "GitHistoryAdapter not registered"
    assert cr_idx >= 0, "CodeRepoAdapter not registered"
    assert gh_idx < cr_idx, (
        f"GitHistoryAdapter (idx {gh_idx}) must register before "
        f"CodeRepoAdapter (idx {cr_idx}) so marker-file working trees "
        f"route to git-history not code-repo."
    )
