"""bump verb: mutate canon + append contract_changelog entry.

MAJOR 9 (v0.5): the first code path in Myco that *mutates* a
post-genesis ``_canon.yaml``. Operates in two shapes:

- ``myco molt --contract <new_version>`` — change
  ``_canon.yaml::contract_version`` (and ``synced_contract_version``,
  held in lockstep) to ``<new_version>``, then append a section to
  ``docs/contract_changelog.md`` describing the molt.
- ``myco molt --contract <new_version> --dry-run`` — preview only,
  writes nothing.

Write strategy: **line-level regex patch** on the known top-level
``contract_version:`` and ``synced_contract_version:`` fields. We do
NOT round-trip through ``pyyaml.safe_dump`` because pyyaml does not
preserve comments, key order, or the schema-annotation header that
``_canon.yaml`` relies on (per L1 ``canon_schema.md`` rule 1 — no
narrative comments, but the schema annotation on line 2 IS retained
structural metadata).

Post-write validation: re-invoke :func:`myco.core.canon.load_canon`
on the mutated file; abort and restore the original text on any
``CanonSchemaError``.

Governing manifest: ``docs/architecture/L3_IMPLEMENTATION/command_manifest.md``
(governance-verbs section, v0.5 — per v0.5.0 craft §R13, no new L2
surface.md was created; governance-verbs content lives at L3).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import date as _date

from myco.core.canon import load_canon
from myco.core.context import MycoContext, Result
from myco.core.errors import CanonSchemaError, ContractError, UsageError

__all__ = ["run"]


#: Minimal version-string shape accepted by ``bump --contract``.
#:
#: Matches ``v0.5.0``, ``v0.5.0-alpha.1``, ``v0.5.0.dev``, ``0.5.0``.
#: Intentionally permissive — Myco's ``ContractVersion`` class handles
#: strict parsing elsewhere; this bound keeps typos out of the canon.
_VERSION_RE = re.compile(r"^v?\d+\.\d+\.\d+(?:[-.][A-Za-z0-9]+(?:\.[A-Za-z0-9]+)*)?$")


def _patch_canon_field(text: str, field: str, new_value: str) -> str:
    """Regex-replace a top-level scalar field in ``_canon.yaml``.

    Matches a line of the shape ``<field>: "<value>"`` at column 0.
    Raises ``ContractError`` if the field is not found — callers
    should not invoke this for optional fields without checking first.
    """
    pattern = re.compile(
        rf'^(?P<prefix>{re.escape(field)}:\s*)(?P<q>["\'])[^"\']*(?P=q)\s*$',
        re.MULTILINE,
    )
    if not pattern.search(text):
        raise ContractError(
            f"bump: could not locate top-level {field!r} line in _canon.yaml"
        )
    return pattern.sub(rf'\g<prefix>"{new_value}"', text, count=1)


def _insert_changelog_entry(text: str, new_section: str) -> str:
    """Insert ``new_section`` above the newest existing ``## v``
    heading in ``docs/contract_changelog.md``.

    The file structure is: intro header, ``---`` divider, entries
    newest-first. We find the first ``^## v`` line and insert the new
    section immediately before it, separated by a ``---`` fence.
    """
    match = re.search(r"^## v[^\n]*$", text, re.MULTILINE)
    if not match:
        # Empty changelog (only the header). Append after the header's
        # trailing ``---`` divider.
        divider_match = re.search(r"^---\s*$", text, re.MULTILINE)
        if divider_match:
            idx = divider_match.end()
            return text[:idx] + "\n\n" + new_section.rstrip() + "\n"
        return text.rstrip() + "\n\n" + new_section.rstrip() + "\n"
    idx = match.start()
    return text[:idx] + new_section.rstrip() + "\n\n---\n\n" + text[idx:]


def _render_changelog_section(*, new_version: str, old_version: str, today: str) -> str:
    return (
        f"## {new_version} - {today} - Contract molt via `myco molt`\n\n"
        f"Replaces `{old_version}` at `_canon.yaml::contract_version`. "
        f"Issued via the `myco molt --contract {new_version}` agent-\n"
        f"callable verb. `synced_contract_version` is updated in\n"
        f"lockstep.\n\n"
        f"### What changed\n\n"
        f"(Fill in: which R1-R7 rules, subsystem definitions, exit-code\n"
        f"grammar, lint-dimension semantics, or command manifest shapes\n"
        f"changed. `myco molt` only records the version; the authoring\n"
        f"agent is responsible for this narrative.)\n\n"
        f"### Break from {old_version}\n\n"
        f"(Fill in: backward-compatibility note. If none, say so explicitly.)\n"
    )


def run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    raw = args.get("contract")
    if not raw:
        raise UsageError(
            "bump: --contract <new_version> is required at v0.5 "
            "(package/schema variants will land in later releases)"
        )
    new_version = str(raw).strip()
    if not _VERSION_RE.match(new_version):
        raise UsageError(
            f"bump: contract version {new_version!r} does not match the "
            f"expected shape (e.g. `v0.5.0`, `v0.5.0-alpha.1`, `v0.5.0.dev`)."
        )

    dry_run = bool(args.get("dry_run", False))
    today = str(args.get("date") or _date.today().isoformat())

    canon_path = ctx.substrate.paths.canon
    changelog_path = ctx.substrate.root / "docs" / "contract_changelog.md"

    if not canon_path.is_file():
        raise ContractError(f"bump: canon not found at {canon_path}")

    original_canon = canon_path.read_text(encoding="utf-8")
    old_version = str(ctx.substrate.canon.contract_version)

    if old_version == new_version:
        raise UsageError(
            f"bump: contract_version is already {new_version!r}; nothing to do"
        )

    patched_canon = _patch_canon_field(original_canon, "contract_version", new_version)
    # synced_contract_version moves in lockstep at v0.5 (see doctrine
    # note in surface.md governance-verbs appendix). If the field is
    # absent, skip silently — some downstream substrates may not track
    # sync drift.
    try:
        patched_canon = _patch_canon_field(
            patched_canon, "synced_contract_version", new_version
        )
        synced_touched = True
    except ContractError:
        synced_touched = False

    if dry_run:
        return Result(
            exit_code=0,
            payload={
                "dry_run": True,
                "old_version": old_version,
                "new_version": new_version,
                "synced_touched": synced_touched,
                "canon_path": str(canon_path.relative_to(ctx.substrate.root)),
                "changelog_path": str(changelog_path.relative_to(ctx.substrate.root)),
                "canon_preview_head": "\n".join(patched_canon.splitlines()[:12]),
            },
        )

    # Commit canon change; validate by re-reading. Restore original on
    # any parse error — we must not leave the substrate in a half-
    # valid state.
    canon_path.write_text(patched_canon, encoding="utf-8", newline="\n")
    try:
        load_canon(canon_path)
    except CanonSchemaError as exc:
        canon_path.write_text(original_canon, encoding="utf-8", newline="\n")
        raise ContractError(
            f"bump: post-write validation failed; canon restored. "
            f"Underlying error: {exc}"
        ) from exc

    # Append changelog entry. If the changelog file doesn't exist,
    # create it with a minimal header so the entry is readable.
    if changelog_path.exists():
        original_changelog = changelog_path.read_text(encoding="utf-8")
    else:
        changelog_path.parent.mkdir(parents=True, exist_ok=True)
        original_changelog = (
            "# Contract Changelog\n\n"
            "Append-only record of contract-version bumps.\n\n"
            "Format: one section per `contract_version`, newest first.\n\n"
            "---\n"
        )

    new_section = _render_changelog_section(
        new_version=new_version, old_version=old_version, today=today
    )
    patched_changelog = _insert_changelog_entry(original_changelog, new_section)
    changelog_path.write_text(patched_changelog, encoding="utf-8", newline="\n")

    # v0.5.8 P0 FIX (Lens 2 P0-9): increment waves.current. The field
    # was declared as monotonic-incrementing in L1 versioning.md but
    # never written by any code path since v0.4.0. molt is the right
    # writer: every molt is a wave boundary. Silent no-op if the
    # canon doesn't carry a waves.current line (pre-v0.5.x).
    waves_touched = False
    try:
        current_text = canon_path.read_text(encoding="utf-8")
        waves_pattern = re.compile(
            r"^(?P<prefix>\s*current:\s*)(?P<n>\d+)\s*$",
            re.MULTILINE,
        )
        m = waves_pattern.search(current_text)
        if m is not None:
            new_n = int(m.group("n")) + 1
            new_text = (
                current_text[: m.start("n")] + str(new_n) + current_text[m.end("n") :]
            )
            canon_path.write_text(new_text, encoding="utf-8", newline="\n")
            waves_touched = True
    except (OSError, ValueError):
        pass

    return Result(
        exit_code=0,
        payload={
            "dry_run": False,
            "old_version": old_version,
            "new_version": new_version,
            "synced_touched": synced_touched,
            "waves_touched": waves_touched,
            "canon_path": str(canon_path.relative_to(ctx.substrate.root)),
            "changelog_path": str(changelog_path.relative_to(ctx.substrate.root)),
        },
    )
