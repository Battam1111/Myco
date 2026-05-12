#!/usr/bin/env python3
"""Seed the substrate-wide auto-evolve tracking GitHub issue (v0.6.14+).

The autopoietic loop (v0.6.14 § "Cycle 自起 fruit—winnow—molt 闭环") uses
a single GitHub issue as the consensus point for `vetoed_intent` comments
posted by `.github/workflows/auto_revert.yml`. The issue is created
once per substrate and its number is recorded in
`_canon.yaml::system.governance.auto_evolve_tracking_issue_id`.

This script is **one-shot**: run it once when first enabling the
autopoietic loop on a Myco substrate. Subsequent runs are no-ops
(detect the field is already set and refuse to overwrite).

Why a single tracking issue instead of one issue per veto: a single
long-lived issue keeps the comment thread navigable for the maintainer
(grep-friendly, single watch subscription) and avoids polluting the
issue tracker with N closed issues per N vetos. The thread also
preserves veto reasoning across releases.

Idempotency: safe to run any number of times. The script:
  1. Reads canon to get the current value.
  2. If non-null, exits 0 with a notice (no-op).
  3. If null, creates the issue via `gh issue create`, captures the
     issue number, writes back to canon.
  4. Verifies the canon write succeeded.

Governing doctrine: docs/architecture/L2_DOCTRINE/cycle.md
Governing craft: docs/primordia/v0_6_14_cycle_autostart_fruit_winnow_molt_loop_craft_2026-04-29.md
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
# v0.8.5 — canon moved to .myco/canon.yaml at v0.8.4; fall back to the
# legacy root path for downstream substrates that haven't migrated.
_CANON_NEW = REPO_ROOT / ".myco" / "canon.yaml"
_CANON_LEGACY = REPO_ROOT / "_canon.yaml"
CANON_PATH = _CANON_NEW if _CANON_NEW.is_file() else _CANON_LEGACY

ISSUE_TITLE = "Auto-evolve tracking issue (v0.6.14+ Cycle 自起 fruit—winnow—molt 闭环)"
ISSUE_BODY = """\
This is the substrate-wide tracking issue for the **autopoietic kernel-evolution loop**
introduced at v0.6.14. See:

- Governing doctrine: [`docs/architecture/L2_DOCTRINE/cycle.md`](../tree/main/docs/architecture/L2_DOCTRINE/cycle.md) § "Cycle 自起 fruit—winnow—molt 闭环 (v0.6.14+)"
- Governing craft: [`docs/primordia/v0_6_14_cycle_autostart_fruit_winnow_molt_loop_craft_2026-04-29.md`](../tree/main/docs/primordia/v0_6_14_cycle_autostart_fruit_winnow_molt_loop_craft_2026-04-29.md)

## How this issue is used

`.github/workflows/auto_revert.yml` posts a `vetoed_intent` comment to this issue every time
an auto-craft PR (branch prefix `fruiting/`) is closed-without-merge by the owner. Each
comment carries a JSON blob with the auto-craft slug, PR number, branch ref, and timestamp.

The next `myco senesce` invocation (in any session) reads new comments via `gh CLI`,
parses the JSON blobs, and writes `vetoed_at: <ISO timestamp>` into matching entries of
`canon.governance.last_winnowed_proposals[]`.

## Do not close this issue

Closing this issue breaks the consensus point. If the loop is being decommissioned,
flip `canon.governance.auto_propose_enabled: false` instead of closing the issue.

## Do not delete comments

Each comment is a permanent veto record for an auto-craft. Deletion of comments
desyncs the senesce reaper from the historical record.
"""


def read_canon_field(field_path: list[str]) -> str | None:
    """Return the value of a YAML field at field_path, or None if not found.

    Avoids importing pyyaml (which would force the script to run inside
    the editable install). This is a tiny one-shot script; greedy grep is enough.
    """
    canon_text = CANON_PATH.read_text(encoding="utf-8")
    # field_path = ["system", "governance", "auto_evolve_tracking_issue_id"]
    # We just look for a top-level (2-space-indented under system, 4-space under
    # governance) match. The canon file is hand-curated YAML; this regex is
    # tied to its known indentation convention.
    field = field_path[-1]
    pattern = re.compile(rf"^\s*{re.escape(field)}:\s*(.+?)\s*$", re.MULTILINE)
    match = pattern.search(canon_text)
    if match is None:
        return None
    raw = match.group(1).strip()
    if raw in ("null", "~", ""):
        return None
    return raw.strip("\"'")


def write_canon_field(field: str, new_value: str) -> None:
    """Replace the value of `field:` in canon with `new_value` (a YAML scalar).

    Preserves indentation + everything else. Field must already exist in canon.
    """
    canon_text = CANON_PATH.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"^(\s*{re.escape(field)}:\s*)(null|~|\".*?\"|'.*?'|\S+)\s*$", re.MULTILINE
    )
    new_canon, count = pattern.subn(rf"\g<1>{new_value}", canon_text)
    if count == 0:
        raise RuntimeError(f"Could not find field `{field}:` in canon; aborting write")
    if count > 1:
        raise RuntimeError(
            f"Field `{field}:` matched {count} lines in canon; refusing to write ambiguously"
        )
    CANON_PATH.write_text(new_canon, encoding="utf-8")


def gh_issue_create(title: str, body: str) -> int:
    """Create a GitHub issue via `gh CLI` and return its number."""
    result = subprocess.run(
        [
            "gh",
            "issue",
            "create",
            "--title",
            title,
            "--body",
            body,
            "--label",
            "auto-evolve-tracker",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        # Label may not exist; retry without label.
        result = subprocess.run(
            ["gh", "issue", "create", "--title", title, "--body", body],
            capture_output=True,
            text=True,
            check=True,
        )
    # `gh issue create` prints the issue URL on stdout; extract the number.
    url = result.stdout.strip()
    match = re.search(r"/issues/(\d+)$", url)
    if match is None:
        raise RuntimeError(f"Could not parse issue number from `gh` output: {url!r}")
    return int(match.group(1))


def main() -> int:
    print(f"[seed_auto_evolve_tracking_issue] reading canon at {CANON_PATH}")
    current = read_canon_field(
        ["system", "governance", "auto_evolve_tracking_issue_id"]
    )
    if current is not None:
        print(
            f"[seed_auto_evolve_tracking_issue] auto_evolve_tracking_issue_id is already "
            f"set to {current!r}; no-op. To re-seed, manually flip the canon field "
            f"back to null first (and confirm you want to abandon the existing issue's "
            f"vetoed_intent comment thread)."
        )
        return 0

    print(
        "[seed_auto_evolve_tracking_issue] creating tracking issue via `gh issue create` ..."
    )
    try:
        issue_number = gh_issue_create(ISSUE_TITLE, ISSUE_BODY)
    except (subprocess.CalledProcessError, RuntimeError) as exc:
        print(
            f"[seed_auto_evolve_tracking_issue] FAILED to create issue: {exc}",
            file=sys.stderr,
        )
        return 2

    print(f"[seed_auto_evolve_tracking_issue] created issue #{issue_number}")
    print(
        f"[seed_auto_evolve_tracking_issue] writing canon: governance.auto_evolve_tracking_issue_id = {issue_number}"
    )
    try:
        write_canon_field("auto_evolve_tracking_issue_id", str(issue_number))
    except RuntimeError as exc:
        print(
            f"[seed_auto_evolve_tracking_issue] FAILED to write canon: {exc}\n"
            f"  Issue #{issue_number} was created on GitHub but canon was not updated.\n"
            f"  Manually edit _canon.yaml to set auto_evolve_tracking_issue_id: {issue_number}",
            file=sys.stderr,
        )
        return 3

    # Verify
    after = read_canon_field(["system", "governance", "auto_evolve_tracking_issue_id"])
    if after != str(issue_number):
        print(
            f"[seed_auto_evolve_tracking_issue] WARN: post-write canon shows {after!r} (expected {issue_number})",
            file=sys.stderr,
        )
        return 4

    print(
        f"[seed_auto_evolve_tracking_issue] OK — tracking issue #{issue_number} seeded into canon"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
