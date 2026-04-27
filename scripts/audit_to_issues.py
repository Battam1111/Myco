#!/usr/bin/env python3
"""audit_to_issues.py — v0.5.8 audit findings → GitHub issues (v0.6.0).

Per craft v0.6.0 §M.2 / §F9. Parses
``notes/integrated/n_2026042*_v0-5-8-iter*.md`` for P0-XX-NN finding
labels, generates ``gh issue create`` commands for each.

Three-batch staging (§F9 / §A4):

- batch-1: 26 P0 issues (LANDED at v0.6.0+24h)
- batch-2: 50 P1 issues (LANDED at v0.6.0+1w)
- batch-3: 60 P1 issues (LANDED at v0.6.0+2w)

Resume / dedup / rate-limit budget:

- ``--resume-from <issue_number>``: skip first N already-created issues
- ``--rate-limit-budget <int>``: hard cap on issues created in one
  invocation (default 80, the GitHub content-generation rate limit
  per minute).
- Dedup: each issue's title is hashed; ``.myco_state/audit_issues_seen.json``
  records hashes already submitted across runs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

DEFAULT_RATE_LIMIT_BUDGET = 80

LENS_PATTERN = re.compile(r"P([0-9])-([A-Z]+(?:-\d+)?)-(\d+)\b")


def discover_audit_notes(root: Path) -> list[Path]:
    integrated = root / "notes" / "integrated"
    if not integrated.is_dir():
        return []
    return sorted(integrated.glob("n_2026042*_v0-5-8-iter*.md"))


def extract_findings(note_path: Path) -> list[dict[str, str]]:
    try:
        text = note_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    findings: list[dict[str, str]] = []
    for match in LENS_PATTERN.finditer(text):
        priority = f"P{match.group(1)}"
        lens = match.group(2)
        idx = match.group(3)
        ident = f"{priority}-{lens}-{idx}"
        # Extract the line containing the finding for body excerpt.
        line_start = text.rfind("\n", 0, match.start()) + 1
        line_end = text.find("\n", match.end())
        line = text[line_start : line_end if line_end > -1 else len(text)].strip()
        findings.append(
            {
                "ident": ident,
                "priority": priority,
                "lens": lens.split("-")[0],
                "title": f"[v0.5.8 Audit] {ident} {line[:60]}",
                "body": line,
                "source": note_path.name,
            }
        )
    return findings


def title_hash(title: str) -> str:
    return hashlib.sha256(title.encode("utf-8")).hexdigest()[:16]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume-from", type=int, default=0)
    parser.add_argument(
        "--rate-limit-budget", type=int, default=DEFAULT_RATE_LIMIT_BUDGET
    )
    parser.add_argument("--batch", choices=["1", "2", "3", "all"], default="all")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    notes = discover_audit_notes(root)
    if not notes:
        print(
            "[audit_to_issues] no v0.5.8 audit notes found in notes/integrated/",
            file=sys.stderr,
        )
        return 1

    findings: list[dict[str, str]] = []
    for note in notes:
        findings.extend(extract_findings(note))
    # Dedup by ident.
    seen_idents: set[str] = set()
    deduped: list[dict[str, str]] = []
    for f in findings:
        if f["ident"] in seen_idents:
            continue
        seen_idents.add(f["ident"])
        deduped.append(f)

    # Filter by batch.
    p0 = [f for f in deduped if f["priority"] == "P0"]
    p1 = [f for f in deduped if f["priority"] == "P1"]
    if args.batch == "1":
        chosen = p0[: args.rate_limit_budget]
    elif args.batch == "2":
        chosen = p1[:50]
    elif args.batch == "3":
        chosen = p1[50:110]
    else:
        chosen = (p0 + p1)[: args.rate_limit_budget]

    # Resume handling.
    seen_path = root / ".myco_state" / "audit_issues_seen.json"
    seen_hashes: set[str] = set()
    if seen_path.is_file():
        try:
            seen_hashes = set(json.loads(seen_path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            pass

    created = 0
    for f in chosen[args.resume_from :]:
        if created >= args.rate_limit_budget:
            print(
                f"[audit_to_issues] rate-limit budget reached: {created}",
                file=sys.stderr,
            )
            break
        h = title_hash(f["title"])
        if h in seen_hashes:
            continue
        cmd = (
            f"gh issue create "
            f'--title "{f["title"]}" '
            f'--body "{f["body"]}\\n\\nSource: {f["source"]}\\nDim proposal: TBD" '
            f'--label "audit-v0.5.8" '
            f'--label "severity-{f["priority"]}" '
            f'--label "lens-{f["lens"].lower()}"'
        )
        if args.dry_run:
            print(f"[audit_to_issues] DRY-RUN: {cmd}")
        else:
            print(cmd)
        seen_hashes.add(h)
        created += 1
        # Backoff.
        if not args.dry_run:
            time.sleep(0.8)

    # Persist seen.
    seen_path.parent.mkdir(parents=True, exist_ok=True)
    seen_path.write_text(json.dumps(sorted(seen_hashes), indent=2), encoding="utf-8")
    print(
        f"[audit_to_issues] generated {created} issue commands; cumulative seen={len(seen_hashes)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
