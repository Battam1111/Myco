"""Adapter for git commit history (one IngestResult per commit).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Adapters". Realises L0 P2 (永恒吞噬) at the commit-record grain:
a repo's history is a stream of decisions and frictions — each
commit is its own ingestible "fragment", not a side-effect of the
file tree. :class:`CodeRepoAdapter` already eats the working tree;
this adapter eats the *story* of how the tree got that way, so
downstream digestion can score, quote, or branch on a single commit
rather than treating the repo as one opaque blob.

Detection (opt-in):

The cleanest signal we found is the user *literally pointing at the
``.git/`` metadata directory*. Three rounds of craft:

* Round 1 — extension hint (``.gitlog``) is fragile (users don't
  rename real ``.git`` dirs) and a marker file (``.git-history``)
  pollutes the working tree.
* Round 2 — refuted ``.git``-only: feared collisions with arbitrary
  ``.git``-named folders, but ``can_handle`` re-checks for the
  canonical ``HEAD`` file, so a placeholder named ``.git`` won't
  spuriously match.
* Round 3 — concluded: **``path == <repo>/.git``** is the primary
  opt-in. It's intent-revealing (the user typing ``.git`` is
  explicitly asking for commit metadata, not file contents), it
  needs no setup, and it cleanly separates from
  :class:`CodeRepoAdapter` (which eats the working tree at
  ``<repo>``). Belt-and-suspenders: also accept a marker file
  ``.git-history`` placed *inside* a working tree, so power users
  can do ``touch myrepo/.git-history`` and then
  ``myco eat --path myrepo``.

Security posture:

* ``cwd=path`` for the git invocation; never string-concat into a
  shell. ``shell=False`` is explicit, args are a list.
* :func:`shutil.which` resolves the git binary; missing git → a
  failed-stub, not a raw exception.
* 30-second subprocess timeout (``timeout=30``) caps the cost of
  a hostile or pathological repo; on timeout, failed-stub.
* ``--max-count=1000`` caps the per-call output at 1000 most recent
  commits. If the cap is hit (1001+ commits exist), an extra
  failed-stub is appended explaining the truncation. Prevents an
  attacker-planted million-commit fixture from OOM'ing the parser.
* Output uses NUL (``\\x00``) field separators and a literal ``END``
  record terminator so commit messages containing arbitrary
  whitespace, newlines, or unicode can't confuse the parser. Git's
  ``--pretty=format:`` lets us pick our own delimiters; NUL is the
  one byte git guarantees never appears in commit content.
"""

from __future__ import annotations

import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path

from .protocol import Adapter, IngestResult

#: Maximum commits emitted per ``ingest`` call. Mirrors the size-cap
#: discipline of the other adapters: a million-commit fixture would
#: otherwise force a million IngestResults through the writer.
MAX_COMMITS: int = 1000

#: Subprocess wall-clock cap (seconds). A hostile or pathological
#: repo (corrupt pack, runaway fsck, reflog the size of the moon)
#: must not block ingestion indefinitely.
GIT_TIMEOUT_SECONDS: int = 30

#: Marker filename — placing this empty file in a working tree opts
#: that working tree into commit-history ingestion (alternative to
#: pointing at ``.git`` directly).
MARKER_FILENAME: str = ".git-history"

#: Git pretty-format delimiter. NUL byte cannot appear in commit
#: content, so it's safe as a field separator inside one record.
_FIELD_SEP: str = "\x00"

#: Per-record terminator. ``END`` followed by a NUL is our
#: end-of-record marker; we use ``-z`` so git also separates records
#: with NUL, but the explicit ``END`` lets us tolerate empty bodies
#: without ambiguity.
_RECORD_END: str = "END"

#: ``--pretty=format:`` template. Fields in order:
#: 1. ``%H`` full commit SHA
#: 2. ``%aI`` author date in strict ISO 8601
#: 3. ``%aN`` author name (respecting .mailmap)
#: 4. ``%aE`` author email (respecting .mailmap)
#: 5. ``%s`` subject line
#: 6. ``%B`` raw body (subject + blank + message body)
#: 7. literal ``END`` terminator
#:
#: Fields are joined with NUL (``%x00``); git's ``-z`` flag also
#: separates records with NUL, so the layout is:
#:   ``<sha>\x00<date>\x00<name>\x00<email>\x00<subj>\x00<body>\x00END\x00``
_PRETTY_FORMAT: str = "%H%x00%aI%x00%aN%x00%aE%x00%s%x00%B%x00" + _RECORD_END


def _posix(p: Path) -> str:
    """Normalise ``p.resolve()`` to POSIX separators (Lens 10 P1-C)."""
    return str(p.resolve()).replace("\\", "/")


def _resolve_git_dir(target: Path) -> Path | None:
    """Return the canonical ``.git`` directory for ``target``.

    Two acceptance shapes:

    1. ``target`` itself is ``.git`` — i.e. it's a directory named
       ``.git`` whose ``HEAD`` is a regular file. Catches the explicit
       ``myco eat --path /repo/.git`` invocation.
    2. ``target`` is a working tree containing both a ``.git/`` and
       a marker file :data:`MARKER_FILENAME`. Catches the
       ``touch myrepo/.git-history`` opt-in.

    Returns the absolute ``.git`` directory on match, ``None`` on
    miss. Never raises.
    """
    if not target.is_dir():
        return None
    # Shape 1: target IS .git.
    if target.name == ".git":
        head = target / "HEAD"
        if head.is_file():
            return target
        return None
    # Shape 2: target is a working tree with a marker file.
    marker = target / MARKER_FILENAME
    git_dir = target / ".git"
    if marker.is_file() and git_dir.is_dir() and (git_dir / "HEAD").is_file():
        return git_dir
    return None


def _parse_commit_records(stdout: str) -> list[dict[str, str]] | None:
    """Split ``stdout`` from ``git log -z --pretty=format:...`` into
    a list of commit-record dicts.

    The on-the-wire layout per commit is::

        <sha>\\x00<date>\\x00<name>\\x00<email>\\x00<subj>\\x00<body>\\x00END

    and ``-z`` separates commits with another ``\\x00``. Splitting
    the whole stream on NUL gives a flat token list; we walk it in
    7-token windows. A short / malformed trailing window is dropped
    silently — it's transport noise, not a commit. Returns ``None``
    when the input stream is empty so the caller can emit a
    failed-stub IngestResult per the v0.7.3 AD1 mechanical/HIGH
    discipline.
    """
    if not stdout:
        return None
    tokens = stdout.split(_FIELD_SEP)
    records: list[dict[str, str]] = []
    i = 0
    n = len(tokens)
    while i + 6 < n:
        sha = tokens[i]
        date = tokens[i + 1]
        name = tokens[i + 2]
        email = tokens[i + 3]
        subject = tokens[i + 4]
        body = tokens[i + 5]
        end_marker = tokens[i + 6]
        if end_marker.strip() != _RECORD_END:
            # Out of sync — skip ahead one token and re-search rather
            # than emit gibberish. In practice this only fires if the
            # git binary returned an unexpected format.
            i += 1
            continue
        if not sha:
            i += 7
            continue
        records.append(
            {
                "commit_sha": sha,
                "author_date_iso": date,
                "author_name": name,
                "author_email": email,
                "subject": subject,
                "body": body,
            }
        )
        i += 7
    return records


def _failed_stub(
    *,
    title: str,
    source: str,
    reason: str,
    metadata: dict | None = None,
) -> IngestResult:
    """Construct a v0.7.3 AD1-closure failed-stub IngestResult."""
    return IngestResult(
        title=title,
        body="",
        source=source,
        status="failed",
        failure_reason=reason,
        metadata=metadata or {},
    )


class GitHistoryAdapter(Adapter):
    """Adapter for git commit history.

    Emits one :class:`IngestResult` per commit, capped at
    :data:`MAX_COMMITS`. Each result's ``metadata`` carries:

    * ``kind`` — always ``"git-commit"``
    * ``commit_sha`` — full 40-char hex SHA
    * ``author_name`` / ``author_email``
    * ``author_date_iso`` — strict ISO 8601 with timezone offset
    * ``subject`` — first line of the commit message
    * ``source_repo`` — POSIX-normalised absolute path of the repo

    The body of each result is the full ``%B`` (subject + blank +
    message body) so that downstream readers see the commit exactly
    as the author wrote it.

    Failure paths return a single failed-stub IngestResult per the
    v0.7.3 AD1-closure protocol. These include: git binary not on
    PATH, subprocess timeout (30s cap), nonzero exit status (e.g.
    corrupt ``.git/``), no commits in the repo, and the
    1000-commit-cap-hit truncation notice (appended *after* the ok
    results, so the agent sees both signal and skip).
    """

    @property
    def name(self) -> str:
        return "git-history"

    @property
    def extensions(self) -> frozenset[str]:
        # Directory-scope adapter, no file extension hook.
        return frozenset()

    def can_handle(self, target: str) -> bool:
        try:
            p = Path(target)
        except (TypeError, ValueError):
            return False
        return _resolve_git_dir(p) is not None

    def ingest(self, target: str) -> Sequence[IngestResult]:
        target_path = Path(target)
        git_dir = _resolve_git_dir(target_path)
        if git_dir is None:
            return [
                _failed_stub(
                    title=target_path.name or "git-history",
                    source=str(target_path),
                    reason=(
                        f"git-history adapter: {target!r} is not a .git "
                        f"directory and contains no {MARKER_FILENAME!r} "
                        "marker file in a working tree"
                    ),
                )
            ]
        # Run git from the parent (working-tree root) when we have one,
        # otherwise from the .git dir itself with --git-dir explicit.
        # Both forms work; the working-tree form lets users with bare
        # repos still ingest by pointing at the bare repo dir as ``.git``.
        repo_root = git_dir.parent if git_dir.name == ".git" else git_dir
        repo_root_posix = _posix(repo_root)

        git_bin = shutil.which("git")
        if git_bin is None:
            return [
                _failed_stub(
                    title=repo_root.name or "git-history",
                    source=repo_root_posix,
                    reason=(
                        "git-history adapter: 'git' binary not found on PATH; "
                        "install git or set PATH to include it"
                    ),
                )
            ]

        # Request one extra commit beyond the cap so we can detect
        # the truncation case explicitly. If git returns MAX_COMMITS+1
        # commits, the 1001st is dropped and a failed-stub is appended.
        max_count_arg = f"--max-count={MAX_COMMITS + 1}"
        cmd = [
            git_bin,
            "--git-dir",
            str(git_dir),
            "log",
            "--all",
            max_count_arg,
            "-z",
            f"--pretty=format:{_PRETTY_FORMAT}",
        ]
        try:
            completed = subprocess.run(
                cmd,
                cwd=str(git_dir),
                shell=False,
                capture_output=True,
                timeout=GIT_TIMEOUT_SECONDS,
                check=False,
                # Decode as UTF-8 with replacement so a single odd byte
                # in an ancient commit doesn't blow up the whole eat.
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired as exc:
            return [
                _failed_stub(
                    title=repo_root.name or "git-history",
                    source=repo_root_posix,
                    reason=(
                        f"git-history adapter: git log timed out after "
                        f"{GIT_TIMEOUT_SECONDS}s ({exc})"
                    ),
                )
            ]
        except OSError as exc:
            return [
                _failed_stub(
                    title=repo_root.name or "git-history",
                    source=repo_root_posix,
                    reason=f"git-history adapter: subprocess failed: {exc}",
                )
            ]
        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip()
            return [
                _failed_stub(
                    title=repo_root.name or "git-history",
                    source=repo_root_posix,
                    reason=(
                        f"git-history adapter: git log exited "
                        f"{completed.returncode}: {stderr or '(no stderr)'}"
                    ),
                )
            ]

        records = _parse_commit_records(completed.stdout or "")
        if not records:
            return [
                _failed_stub(
                    title=repo_root.name or "git-history",
                    source=repo_root_posix,
                    reason=(
                        "git-history adapter: repo has no commits "
                        "(or all commits filtered)"
                    ),
                )
            ]

        truncated = len(records) > MAX_COMMITS
        kept = records[:MAX_COMMITS]
        results: list[IngestResult] = []
        for idx, rec in enumerate(kept):
            sha = rec["commit_sha"]
            short = sha[:8] if len(sha) >= 8 else sha
            subject = rec["subject"] or "(no subject)"
            results.append(
                IngestResult(
                    title=f"{repo_root.name}-{short}-{subject[:40]}",
                    body=rec["body"] or rec["subject"] or "",
                    tags=["git-commit", "git-history"],
                    source=repo_root_posix,
                    metadata={
                        "kind": "git-commit",
                        "commit_sha": sha,
                        "author_name": rec["author_name"],
                        "author_email": rec["author_email"],
                        "author_date_iso": rec["author_date_iso"],
                        "subject": subject,
                        "source_repo": repo_root_posix,
                        "commit_index": idx,
                    },
                )
            )
        if truncated:
            results.append(
                _failed_stub(
                    title=f"{repo_root.name}-truncation-notice",
                    source=repo_root_posix,
                    reason=(
                        f"git-history adapter: commit cap hit "
                        f"({MAX_COMMITS}); older commits were not ingested"
                    ),
                    metadata={
                        "kind": "git-commit-truncation",
                        "source_repo": repo_root_posix,
                        "max_commits": MAX_COMMITS,
                    },
                )
            )
        return results
