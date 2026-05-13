"""Cluster module — v0.8.8 pass-4 merge of boot_brief, hunger, eat.

=== boot_brief ===
Maintain a marker-delimited signals block in the entry-point file.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Hunger + boot brief" (the signals block hunger writes on R1).

The entry-point (``MYCO.md`` or ``CLAUDE.md``) carries an
agent-visible "signals" block wedged between HTML-comment markers::

    <!-- BEGIN MYCO SIGNALS -->
    (rendered signals here)
    <!-- END MYCO SIGNALS -->

``patch_entry_point`` inserts the block on first call and replaces its
content on subsequent calls. Idempotent: same input → same output.

=== hunger ===
``myco hunger`` — compose substrate hunger report.

Stage B.4 wires two locally-computable signals (contract_drift,
raw_backlog) and leaves ``reflex_signals`` as an empty seam for
Stage B.8's homeostasis dimensions to populate. ``--execute`` patches
the entry-point signals block via ``boot_brief``.

v0.5.3 adds a ``local_plugins`` block — a terse summary of what
substrate-local plugins are loaded so the agent sees extensibility
state on every boot. History: ``docs/contract_changelog.md``
§ v0.5.3.

=== eat ===
``myco eat`` — append a raw note.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Ingestion is cheap and permissive" (L0 principle 2 realised).

Per L2 ingestion.md: cheap, permissive, loss-preserving. Content is
never rejected on shape; rejection is reserved for write-surface
violations + empty-input + multi-intake-mode conflicts.

v0.5.8:
* Switched frontmatter rendering from a hand-rolled f-string to
  ``yaml.safe_dump`` so hostile ``source`` / ``tags`` values cannot
  inject arbitrary YAML keys (P0 prompt-injection fix).
* Added explicit validation that exactly one of
  ``--content`` / ``--path`` / ``--url`` is supplied, with
  ``UsageError`` instead of silently producing empty notes or
  silently dropping ``--content`` when ``--path`` is also passed.
* Same-second filename collisions now use atomic ``O_EXCL`` create
  so concurrent ``eat`` calls can't silently overwrite each other
  (P0 concurrency fix).
* Merged tags are sorted for deterministic note output across
  processes.
"""

from __future__ import annotations

# NOTE: patch_entry_point is now defined below in this same cluster (formerly boot_brief.py).
import os
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml

from myco.boundary.surface.manifest import load_manifest_with_overlay
from myco.core.identity_cluster import ContractError, MycoContext, Result, UsageError
from myco.core.io_cluster import atomic_utf8_write, bounded_read_text
from myco.core.trust_cluster import check_write_allowed

# =========================================================================
# === boot_brief — formerly boot_brief.py
# =========================================================================

BEGIN_MARKER = "<!-- BEGIN MYCO SIGNALS -->"

END_MARKER = "<!-- END MYCO SIGNALS -->"


def render_signals_block(signals: dict[str, object]) -> str:
    """Render the marker-wrapped signals block from a mapping.

    Lines are emitted as ``- key: value`` bullets in insertion order.
    An empty mapping still produces a well-formed (but empty) block.
    """
    lines = [BEGIN_MARKER]
    if signals:
        for key, value in signals.items():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- (no signals)")
    lines.append(END_MARKER)
    return "\n".join(lines)


def patch_entry_point(*, ctx: MycoContext, signals: dict[str, object]) -> Path:
    """Insert or replace the signals block in the entry-point file.

    Returns the path written.

    Raises:
        ContractError: if the entry-point is missing, or if its markers
            are malformed (two BEGINs, BEGIN without END, etc.).
    """
    entry_name = ctx.substrate.canon.entry_point
    path = ctx.substrate.root / entry_name
    if not path.is_file():
        raise ContractError(
            f"entry-point {entry_name!r} not found at {ctx.substrate.root}"
        )
    text = bounded_read_text(path)
    block = render_signals_block(signals)
    new_text = _apply_block(text, block)
    check_write_allowed(ctx, path, verb="hunger:patch_entry_point")
    atomic_utf8_write(path, new_text)
    return path


def _apply_block(text: str, block: str) -> str:
    begin_count = text.count(BEGIN_MARKER)
    end_count = text.count(END_MARKER)
    if begin_count > 1 or end_count > 1:
        raise ContractError(
            "entry-point signals block corrupt: multiple BEGIN/END markers"
        )
    if (begin_count == 0) != (end_count == 0):
        raise ContractError(
            "entry-point signals block corrupt: BEGIN without END (or vice versa)"
        )
    if begin_count == 0:
        sep = "" if text.endswith("\n\n") else "\n" if text.endswith("\n") else "\n\n"
        return text + sep + block + "\n"
    start = text.index(BEGIN_MARKER)
    end = text.index(END_MARKER) + len(END_MARKER)
    if end <= start:
        raise ContractError(
            "entry-point signals block corrupt: END appears before BEGIN"
        )
    return text[:start] + block + text[end:]


# =========================================================================
# === hunger — formerly hunger.py
# =========================================================================


@dataclass(frozen=True)
class LocalPluginsSummary:
    """Terse view of the substrate-local plugin surface.

    v0.5.4 added :attr:`count_by_kind` to match the v0.5.3 CHANGELOG
    promise that the payload breaks the count down per registration
    kind. The flat ``count`` is retained for backward compatibility.
    """

    count: int
    errors: tuple[str, ...]
    overlay_verbs: tuple[str, ...]
    count_by_kind: Mapping[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        """JSON-safe view for the hunger payload + MCP/CLI rendering."""
        return {
            "count": self.count,
            "count_by_kind": dict(self.count_by_kind),
            "errors": list(self.errors),
            "overlay_verbs": list(self.overlay_verbs),
        }


@dataclass(frozen=True)
class HungerReport:
    """A typed view of the hunger state."""

    contract_drift: bool
    raw_backlog: int
    reflex_signals: tuple[str, ...]
    advice: tuple[str, ...]
    local_plugins: LocalPluginsSummary = field(
        default_factory=lambda: LocalPluginsSummary(
            count=0, errors=(), overlay_verbs=()
        )
    )

    def as_dict(self) -> dict[str, object]:
        """JSON-safe view for the hunger payload + MCP/CLI rendering."""
        return {
            "contract_drift": self.contract_drift,
            "raw_backlog": self.raw_backlog,
            "reflex_signals": list(self.reflex_signals),
            "advice": list(self.advice),
            "local_plugins": self.local_plugins.as_dict(),
        }


def _summarize_local_plugins(ctx: MycoContext) -> LocalPluginsSummary:
    """Compute the count/errors/overlay_verbs triple for the hunger report.

    v0.5.22: count **substrate-local** plugins only. Delegates to
    ``graft._collect_plugins`` and filters by its ``scope`` field so
    kernel built-ins don't appear as "local" (which was the
    pre-v0.5.22 bug that showed "32 local plugins" on every fresh
    substrate). See ``docs/contract_changelog.md::v0.5.22``.

    - ``count``: total substrate-local plugins (dimensions + adapters
      + schema_upgraders + overlay_verbs whose source file lives under
      ``<root>/.myco/plugins/`` or is the overlay manifest itself).
    - ``errors``: whatever ``Substrate.local_plugin_errors`` captured
      at load time plus any enumeration failures here.
    - ``overlay_verbs``: names of verbs contributed by the overlay.
    """
    from myco.cycle.canon_cluster import _collect_plugins

    errors = list(ctx.substrate.local_plugin_errors)
    by_kind: dict[str, int] = {
        "dimension": 0,
        "adapter": 0,
        "schema_upgrader": 0,
        "overlay_verb": 0,
    }
    overlay_verbs: list[str] = []
    try:
        for entry in _collect_plugins(ctx):
            if entry.get("scope") != "substrate":
                continue
            kind = entry.get("kind")
            if kind in by_kind:
                by_kind[kind] += 1
            if kind == "overlay_verb":
                overlay_verbs.append(str(entry.get("name", "")))
    except Exception as exc:
        errors.append(f"local-plugin enumeration failed: {exc}")
    try:
        load_manifest_with_overlay(ctx.substrate.root)
    except Exception as exc:
        errors.append(f"manifest overlay parse failed: {exc}")
    count = sum(by_kind.values())
    return LocalPluginsSummary(
        count=count,
        errors=tuple(errors),
        overlay_verbs=tuple(overlay_verbs),
        count_by_kind=dict(by_kind),
    )


def compose_hunger_report(ctx: MycoContext) -> HungerReport:
    """Assemble the hunger report from substrate state.

    - ``contract_drift``: True iff canon's ``contract_version`` !=
      ``synced_contract_version`` (when the latter is set).
    - ``raw_backlog``: count of ``notes/raw/*.md`` files.
    - ``reflex_signals``: empty at B.4; populated by B.8 dimensions.
    - ``advice``: human-readable nudges derived from the above.
    """
    canon = ctx.substrate.canon
    synced = canon.synced_contract_version
    contract_drift = bool(synced) and synced != canon.contract_version
    raw_dir = ctx.substrate.paths.notes / "raw"
    if raw_dir.is_dir():
        raw_backlog = sum(1 for p in raw_dir.glob("*.md") if p.is_file())
    else:
        raw_backlog = 0
    reflex_signals: tuple[str, ...] = ()
    advice_parts: list[str] = []
    if contract_drift:
        advice_parts.append(
            f"contract drifted: canon={canon.contract_version}, synced={synced}; run `myco assimilate` to reconcile (or `myco molt --contract <version>` to publish a new contract)"
        )
    if raw_backlog > 0:
        advice_parts.append(f"raw_backlog={raw_backlog}; consider `myco assimilate`")
    if not advice_parts:
        advice_parts.append("substrate quiet; no action required")
    local_plugins = _summarize_local_plugins(ctx)
    if local_plugins.errors:
        advice_parts.append(
            "substrate-local plugin errors present; run `myco graft --validate`"
        )
    return HungerReport(
        contract_drift=contract_drift,
        raw_backlog=raw_backlog,
        reflex_signals=reflex_signals,
        advice=tuple(advice_parts),
        local_plugins=local_plugins,
    )


def hunger_run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Manifest handler: compose the report and optionally patch entry-point."""
    execute = bool(args.get("execute", False))
    report = compose_hunger_report(ctx)
    entry_point_path: str | None = None
    if execute:
        signals = {
            "contract_drift": report.contract_drift,
            "raw_backlog": report.raw_backlog,
            "advice": "; ".join(report.advice),
        }
        path = patch_entry_point(ctx=ctx, signals=signals)
        entry_point_path = str(path)
    return Result(
        exit_code=0,
        payload={
            "report": report.as_dict(),
            "execute": execute,
            "entry_point_patched": entry_point_path,
        },
    )


# =========================================================================
# === eat — formerly eat.py
# =========================================================================

_SLUG_RE = re.compile("[^a-z0-9]+")

_SLUG_MAX = 40


def _url_adapter_rejection_reason(target: str) -> str | None:
    """Return the SSRF / scheme rejection reason when ``target`` looks
    like a URL the ``UrlFetcher`` adapter would have handled but
    refused, or ``None`` if the target doesn't look like a URL (or
    the adapter module isn't importable).

    v0.5.22 UX fix for the class of errors where ``find_adapter``
    returns ``None`` because ``UrlFetcher.can_handle`` silently
    returned ``False`` after ``_validate_url`` raised. Previously the
    user only saw "No adapter can handle 'https://…'" with no hint
    that the SSRF guard was the real gate — especially confusing on
    corporate networks / VPNs where a public hostname can legitimately
    resolve to a CGNAT / benchmark / private IP.
    """
    # v0.8.8 max-aggressive: web_cluster excreted; URL ingestion is no
    # longer a core surface. URL-shaped targets fall through to the
    # generic "no adapter" branch upstream.
    del target
    return None


@dataclass(frozen=True)
class EatOutcome:
    """Typed result of a successful eat."""

    path: Path
    captured_at: datetime
    tags: tuple[str, ...]
    source: str


def append_note(
    *,
    ctx: MycoContext,
    content: str,
    tags: Sequence[str] = (),
    source: str = "agent",
    now: datetime | None = None,
) -> EatOutcome:
    """Append ``content`` as a raw note under ``notes/raw/``.

    Auto-creates ``notes/`` and ``notes/raw/`` if either is missing
    (per craft R5 — ingestion is cheap and permissive).

    Filename: ``<UTC_ISO>_<slug>.md``. Collisions resolved by suffix
    ``_2``, ``_3``, ….
    """
    now = now or datetime.now(timezone.utc)
    notes_dir = ctx.substrate.paths.notes
    raw_dir = notes_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    slug = _slugify(content)
    base_name = f"{stamp}_{slug}" if slug else stamp
    tags_t = tuple(str(t) for t in tags)
    body = _render_note(captured_at=now, tags=tags_t, source=source, content=content)
    path = raw_dir / f"{base_name}.md"
    check_write_allowed(ctx, path, verb="eat")
    counter = 2
    while True:
        try:
            fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            try:
                with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(body)
            except BaseException:
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    pass
                raise
            break
        except FileExistsError:
            path = raw_dir / f"{base_name}_{counter}.md"
            counter += 1
            if counter > 10000:
                raise UsageError(
                    "eat: unable to find a unique filename after 10000 attempts; is notes/raw/ accepting writes?"
                )
    return EatOutcome(path=path, captured_at=now, tags=tags_t, source=source)


def eat_run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Manifest handler: append a note and return a Result.

    Three intake modes (mutually exclusive):

    1. ``--content "..."`` — literal string, written verbatim.
    2. ``--path ./file-or-dir`` — dispatched through the adapter
       registry. A single file produces one note; a directory
       produces one note per ingestible file inside it.
    3. ``--url https://...`` — fetched and dispatched by the URL
       adapter (requires ``httpx`` from ``[adapters]`` extras).

    The adapter populates ``source`` with the real provenance
    (file path, URL, repo root) instead of the default ``"agent"``.
    """
    content = args.get("content")
    path_arg = args.get("path")
    url_arg = args.get("url")
    raw_tags = args.get("tags") or ()
    if not isinstance(raw_tags, (list, tuple)):
        raw_tags = ()
    tags = [str(t) for t in raw_tags]
    source = str(args.get("source", "agent"))
    _content_supplied = bool(content and str(content))
    _path_supplied = bool(path_arg)
    _url_supplied = bool(url_arg)
    _mode_count = (
        (1 if _content_supplied else 0)
        + (1 if _path_supplied else 0)
        + (1 if _url_supplied else 0)
    )
    if _mode_count == 0:
        raise UsageError(
            "eat: must pass one of --content '<text>' | --path <file-or-dir> | --url <url>. Pass --content '' explicitly only if you really want an empty note."
        )
    if _mode_count > 1:
        raise UsageError(
            "eat: --content, --path, and --url are mutually exclusive; pass only one."
        )
    if path_arg or url_arg:
        target = str(path_arg or url_arg)
        from myco.ingestion.adapters import find_adapter

        adapter = find_adapter(target)
        if adapter is None:
            extra_reason = _url_adapter_rejection_reason(target)
            base_error = f"No adapter can handle {target!r}."
            if extra_reason:
                error_msg = f"{base_error} URL adapter refused: {extra_reason}."
            else:
                error_msg = f"{base_error} Install 'myco[adapters]' for PDF, HTML, and URL support, or point at a text/code file."
            return Result(exit_code=2, payload={"error": error_msg})
        results = adapter.ingest(target)
        outcomes = []
        skipped: list[dict[str, str]] = []
        for r in results:
            if getattr(r, "status", "ok") == "failed":
                reason = getattr(r, "failure_reason", "") or "unknown"
                src = r.source or target
                print(f"[adapter-skip] {src}: {reason}", file=sys.stderr)
                skipped.append({"source": src, "failure_reason": reason})
                continue
            merged_tags = tuple(sorted(set(tags) | set(r.tags)))
            outcome = append_note(
                ctx=ctx, content=r.body, tags=merged_tags, source=r.source or source
            )
            outcomes.append(
                {
                    "path": str(outcome.path),
                    "captured_at": outcome.captured_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "title": r.title,
                    "source": r.source,
                }
            )
        return Result(
            exit_code=0,
            payload={
                "adapter": adapter.name,
                "notes_created": len(outcomes),
                "notes": outcomes,
                "skipped": skipped,
            },
        )
    outcome = append_note(
        ctx=ctx, content=str(content or ""), tags=tuple(tags), source=source
    )
    return Result(
        exit_code=0,
        payload={
            "path": str(outcome.path),
            "captured_at": outcome.captured_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tags": outcome.tags,
            "source": outcome.source,
        },
    )


def _slugify(text: str) -> str:
    """Produce a filesystem-safe slug from the first line of ``text``."""
    first_line = (text.splitlines() or [""])[0].strip().lower()
    slug = _SLUG_RE.sub("-", first_line).strip("-")
    return slug[:_SLUG_MAX]


def _render_note(
    *, captured_at: datetime, tags: tuple[str, ...], source: str, content: str
) -> str:
    """Render a raw note's frontmatter + body.

    v0.5.8 P0 fix: uses ``yaml.safe_dump`` to render the frontmatter
    dict. Previously hand-rolled with f-string interpolation, which
    allowed a hostile ``source`` value (e.g. from ``eat --url
    http://evil.tld/x``) to inject arbitrary top-level YAML keys by
    embedding ``"\\n...\\n"`` in the quoted scalar.

    The ``source`` and tag values are also sanitised via
    :func:`myco.core.trust.safe_frontmatter_field` so control
    characters and newlines never reach the YAML serialiser in the
    first place (defense-in-depth against a yaml.safe_dump edge case
    where a carefully-crafted scalar still survives).
    """
    from myco.core.trust_cluster import safe_frontmatter_field

    stamp = captured_at.strftime("%Y-%m-%dT%H:%M:%SZ")
    body = content.rstrip("\n") + "\n"
    frontmatter: dict[str, object] = {
        "captured_at": stamp,
        "tags": [safe_frontmatter_field(str(t)) for t in tags],
        "source": safe_frontmatter_field(str(source)),
        "stage": "raw",
    }
    rendered = yaml.safe_dump(
        frontmatter, default_flow_style=False, allow_unicode=True, sort_keys=True
    )
    return f"---\n{rendered}---\n{body}"
