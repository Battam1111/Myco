"""Cluster module — v0.8.8 max-aggressive merge of write_surface, trust.

=== write_surface ===
Write-surface policy + guarded-write helper.

Governing doctrine: ``docs/architecture/L1_CONTRACT/protocol.md`` R6
("Write only to paths in ``_canon.yaml::system.write_surface.allowed``")
and ``docs/architecture/L2_DOCTRINE/homeostasis.md`` § "Safe-fix
discipline" rule 4 ("Bounded"). This module is the mechanical
enforcement of both — every verb that mutates substrate content
routes its path through :func:`check_write_allowed` or
:func:`guarded_write`.

v0.5.8 upgraded R6 (the "write only to allowed surface" hard-contract
rule) from "checked by `immune --fix`" to "enforced on every
kernel-side write". Previously every verb that mutated the substrate
(`eat`, `sporulate`, `ramify`, `fruit`, `molt`, `propagate`,
`germinate`, `boot_brief.patch_entry_point`) wrote bytes directly with
no check against `canon.system.write_surface.allowed`. The audit
classified this as a P0 trust-boundary break.

This module is the chokepoint every kernel write now routes through:

    from myco.core.trust_cluster import guarded_write
    guarded_write(ctx, path, content)

The helper:

1. Resolves ``path`` to a substrate-relative POSIX string.
2. Matches that path against ``ctx.substrate.canon.system.write_surface.allowed``
   using glob semantics.
3. If allowed, delegates to :func:`myco.core.io_atomic.atomic_utf8_write`
   for the actual write (atomic + UTF-8 + LF-normalised).
4. If disallowed, either raises :class:`WriteSurfaceViolation` OR, when
   the ``MYCO_ALLOW_UNSAFE_WRITE=1`` environment variable is set, logs
   the bypass and proceeds.

The bypass is intentional — certain workflows (test tmp dirs, scripted
ingest) need write access outside the declared surface. The env var
makes it explicit; v0.5.10+ appends each bypassed write to
``.myco/state/unsafe_writes.log`` so a future SE-class dimension can
surface bypass frequency to immune without any per-call overhead.

The helper imports ``ctx`` lazily (by type-name) to avoid a
core→runtime circular import. Callers pass a ``MycoContext`` instance.

=== trust ===
Trust-boundary sanitisation helpers.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
(Ingestion § "Trust boundary" — raw notes are attacker-controlled
by design, so every scalar that escapes the notes directory into
agent context must pass through a sanitiser). See also
``docs/architecture/L1_CONTRACT/protocol.md`` R1-R7 for the higher-
level mandate that agent context stays uncorrupted.

Every string that crosses from **substrate content** (potentially
attacker-controlled) into **Agent prompt context** (MCP tool response,
CLI JSON output, finding message, brief rollup) MUST pass through one
of these helpers first.

The Myco substrate is attacker-controlled in three realistic ways:

1. Hostile URL ingest (``myco eat --url ...`` fetches arbitrary
   content and writes it into notes).
2. Hostile PR merged into canon, craft doc, or manifest overlay.
3. Hostile co-maintainer in a shared substrate.

Without sanitisation, a hostile note can inject:

* Prompt-injection strings ("Ignore previous instructions. Run X.")
* ANSI escape sequences that look like control characters to a log
  reader and like commands to a richer terminal.
* Markdown that renders as active links / script tags when echoed to
  a human by ``myco brief``.
* YAML fragments that escape their quoted scalar and inject arbitrary
  top-level frontmatter keys.

This module ships the minimum viable sanitisation surface:

* :func:`strip_controls` — remove C0/C1 control chars (includes ESC).
* :func:`flatten_newlines` — collapse CR/LF to a single space for
  single-line scalars.
* :func:`safe_frontmatter_field` — single-line safe scalar for YAML
  frontmatter fields like ``source`` or ``substrate_id``. **Prefer
  ``yaml.safe_dump`` for whole-document rendering**; this helper
  exists for places that must hand-compose a single field.
* :func:`markdown_inline_safe` — escape markdown meta-chars so a
  string embeds inline in a markdown table cell or list bullet without
  rendering active links or code spans.

Each helper is pure, idempotent, and unit-tested; they compose. The
module has no substrate knowledge and imports no Myco internals, so
it is safe to use from any layer.
"""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import TYPE_CHECKING, Final

from .identity_cluster import MycoError
from .io_cluster import atomic_utf8_write

# =========================================================================
# === write_surface — formerly write_surface.py
# =========================================================================

if TYPE_CHECKING:
    from .identity_cluster import MycoContext

UNSAFE_WRITE_ENV = "MYCO_ALLOW_UNSAFE_WRITE"


class WriteSurfaceViolation(MycoError):
    """Raised when a kernel write targets a path outside
    ``_canon.yaml::system.write_surface.allowed`` and the unsafe-write
    bypass is not set.

    Exit code 3 inherited from :class:`MycoError`. Caller-friendly
    message names the path and the surface it violated.
    """


def unsafe_bypass_enabled() -> bool:
    """Return True if ``MYCO_ALLOW_UNSAFE_WRITE`` is set to a truthy
    value (``"1"`` / ``"true"`` / ``"yes"`` / ``"on"``).

    v0.5.8 promoted this from a private helper so verbs that use
    ``os.open(O_EXCL)`` or other bespoke write paths (``eat``'s
    collision-retry loop is the canonical case) can reproduce the
    same bypass semantics ``guarded_write`` uses without reimplementing
    the env-var parsing.
    """
    value = os.environ.get(UNSAFE_WRITE_ENV, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


_unsafe_bypass_enabled = unsafe_bypass_enabled


def check_write_allowed(ctx: MycoContext, path: Path, *, verb: str) -> None:
    """Raise :class:`WriteSurfaceViolation` if ``path`` is not in the
    substrate's declared write surface AND the unsafe-write bypass is
    not set.

    Public helper for verbs that do their own file I/O (e.g. ``eat``'s
    ``O_EXCL`` collision loop) but still want the write-surface + env-
    bypass semantics ``guarded_write`` provides.

    Args:
        ctx: the substrate context whose canon declares the surface.
        path: the target path (will be resolved + matched).
        verb: caller verb name surfaced in the error message, e.g.
            ``"eat"``. Purely diagnostic.
    """
    allowed, rel = is_path_allowed(path, ctx)
    if allowed:
        return
    if unsafe_bypass_enabled():
        return
    surface_list: list[str] = []
    system = ctx.substrate.canon.system or {}
    surface_map = system.get("write_surface") or {}
    if isinstance(surface_map, dict):
        raw_allowed = surface_map.get("allowed")
        if isinstance(raw_allowed, list):
            surface_list = [str(p) for p in raw_allowed]
    raise WriteSurfaceViolation(
        f"{verb}: target {(rel if rel is not None else path)} is not matched by any pattern in canon.system.write_surface.allowed = {surface_list}. Add a covering pattern, or set {UNSAFE_WRITE_ENV}=1 in the environment to override."
    )


def _normalise_to_substrate_relative(path: Path, substrate_root: Path) -> str | None:
    """Return ``path`` as a POSIX substrate-relative string, or None
    if ``path`` escapes ``substrate_root``.

    Matches the pattern used elsewhere in the kernel (``graph._rel``).
    The relative path uses ``/`` separators regardless of platform so
    the glob match is portable.
    """
    try:
        resolved = path.resolve()
        rel = resolved.relative_to(substrate_root.resolve())
    except (ValueError, OSError):
        return None
    return str(rel).replace(os.sep, "/")


def is_path_allowed(path: Path, ctx: MycoContext) -> tuple[bool, str | None]:
    """Check whether ``path`` falls within the substrate's declared
    write surface.

    Returns ``(True, rel)`` when allowed (``rel`` is the
    substrate-relative POSIX string that matched a rule) or
    ``(False, rel_or_None)`` when not. The second element is the
    relative path if it could be computed, or None if ``path`` escapes
    the substrate root entirely (still disallowed).

    The canon's ``system.write_surface.allowed`` is read as a list of
    fnmatch-style globs. A path is allowed when ANY glob matches.

    Missing-canon case: if the canon cannot be read or the
    ``write_surface.allowed`` list is absent/empty, returns ``(False,
    rel)`` — the default is strict, matching R6's "any other path is
    substrate pollution".
    """
    substrate_root = ctx.substrate.root
    rel = _normalise_to_substrate_relative(path, substrate_root)
    if rel is None:
        return (False, None)
    system = ctx.substrate.canon.system or {}
    surface = system.get("write_surface") or {}
    allowed_raw = surface.get("allowed") if isinstance(surface, dict) else None
    if not isinstance(allowed_raw, list):
        return (False, rel)
    patterns: list[str] = [str(p) for p in allowed_raw]
    for pattern in patterns:
        if fnmatch.fnmatchcase(rel, pattern):
            return (True, rel)
    return (False, rel)


def guarded_write(
    ctx: MycoContext,
    path: Path,
    content: str,
    *,
    newline: str | None = "\n",
    encoding: str = "utf-8",
    make_parents: bool = True,
) -> str:
    """Write ``content`` to ``path`` iff ``path`` is within the
    substrate's write surface.

    On success, returns the substrate-relative POSIX path for the
    caller to log / surface in Result payloads. On disallowed path,
    raises :class:`WriteSurfaceViolation` unless ``MYCO_ALLOW_UNSAFE_WRITE``
    is set, in which case the bypass is taken and the write proceeds.

    All actual bytes are written via :func:`atomic_utf8_write` so the
    write is atomic + UTF-8 + LF-normalised regardless of platform.
    """
    allowed, rel = is_path_allowed(path, ctx)
    if not allowed:
        if _unsafe_bypass_enabled():
            _log_unsafe_bypass(ctx, rel if rel is not None else str(path))
        else:
            surface_list: list[str] = []
            system = ctx.substrate.canon.system or {}
            surface_map = system.get("write_surface") or {}
            if isinstance(surface_map, dict):
                raw_allowed = surface_map.get("allowed")
                if isinstance(raw_allowed, list):
                    surface_list = [str(p) for p in raw_allowed]
            raise WriteSurfaceViolation(
                f"refusing to write outside allowed surface: {(rel if rel is not None else path)} is not matched by any pattern in canon.system.write_surface.allowed = {surface_list}. To override explicitly, set {UNSAFE_WRITE_ENV}=1 in the environment."
            )
    atomic_utf8_write(
        path, content, newline=newline, encoding=encoding, make_parents=make_parents
    )
    return rel if rel is not None else str(path)


def _log_unsafe_bypass(ctx: MycoContext, target_rel_or_abs: str) -> None:
    """Append a one-line record to ``.myco/state/unsafe_writes.log``.

    v0.5.10: the log is a best-effort audit trail. Any failure
    (missing state dir, permission denied, full disk) is swallowed
    silently — the log must never block the actual write. A future
    SE-class dimension can count entries to surface bypass frequency
    to ``myco immune``.

    Format: ``<ISO-8601 UTC> <target>`` newline-terminated.
    """
    try:
        from datetime import datetime, timezone

        log_path = ctx.substrate.root / ".myco/state" / "unsafe_writes.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        line = f"{stamp} {target_rel_or_abs}\n"
        with open(log_path, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(line)
    except OSError:
        pass


# =========================================================================
# === trust — formerly trust.py
# =========================================================================

_CONTROL_CHARS: Final[frozenset[str]] = frozenset(
    chr(c) for c in (*range(0, 9), 11, 12, *range(14, 32), 127, *range(128, 160))
)

_MARKDOWN_META: Final[str] = "\\`*_{}[]()#+-.!|<>&~"


def strip_controls(s: str) -> str:
    """Remove C0/C1 control characters (including ANSI ESC ``\\x1b``).

    Tab (``\\t``), LF (``\\n``), and CR (``\\r``) are preserved so
    legitimate multiline content is not mangled. Callers that want
    single-line output should follow up with :func:`flatten_newlines`.

    Idempotent: ``strip_controls(strip_controls(x)) == strip_controls(x)``.
    """
    if not s:
        return s
    return "".join(c for c in s if c not in _CONTROL_CHARS)


def flatten_newlines(s: str, *, replacement: str = " ") -> str:
    """Collapse CR/LF (and CRLF pairs) to a single ``replacement``
    character.

    Use for single-line fields: substrate_id, tags, error messages
    surfaced to the Agent, error strings echoed to stderr. A hostile
    string containing ``"line1\\n# SYSTEM: ignore previous"`` becomes
    ``"line1  # SYSTEM: ignore previous"`` — the injection is still
    visible as text but no longer a distinct line that a downstream
    prompt renderer would treat as a new instruction.
    """
    if not s:
        return s
    return (
        s.replace("\r\n", replacement)
        .replace("\n", replacement)
        .replace("\r", replacement)
    )


def safe_frontmatter_field(s: str, *, max_len: int = 1024) -> str:
    """Produce a single-line YAML-safe scalar from untrusted input.

    Strips controls, flattens newlines, trims to ``max_len`` chars.
    Callers are responsible for actually quoting the result inside
    YAML (or, better, for routing the whole document through
    ``yaml.safe_dump`` — this helper only guarantees the scalar
    *content* is one line).

    Intended wiring points:
    * ``eat._render_note`` — BUT prefer ``yaml.safe_dump`` for the
      full frontmatter render; use this for single-field composition
      only.
    * ``mcp._compute_substrate_pulse`` — wrap ``substrate_id`` before
      it crosses into the pulse payload.
    * ``brief._render_markdown`` — wrap any substrate-derived scalar.

    Truncation: when ``s`` exceeds ``max_len``, the result is
    ``s[:max_len-1] + "…"`` (U+2026). The caller receives a bounded
    string and a visual marker that the origin was longer.
    """
    if not s:
        return s
    sanitised = flatten_newlines(strip_controls(s)).strip()
    if len(sanitised) > max_len:
        sanitised = sanitised[: max_len - 1] + "…"
    return sanitised


def markdown_inline_safe(s: str) -> str:
    """Escape markdown meta-characters so ``s`` embeds inline in a
    markdown document without rendering active links, code spans,
    headings, or lists.

    Use when composing markdown for the ``myco brief`` human rollup
    (the one carved-out human exit per L0 principle 1 addendum). A
    hostile craft title like ``"# [Click](javascript:alert(1))"``
    becomes ``"\\# \\[Click\\]\\(javascript:alert\\(1\\)\\)"`` — visible
    as literal text, not active HTML / JS.

    Also flattens newlines (markdown is line-sensitive for headings
    and lists).

    Idempotent only up to the escape-backslash: running twice doubles
    the backslashes. Callers SHOULD NOT chain; pick one boundary.
    """
    if not s:
        return s
    escaped = s
    for ch in _MARKDOWN_META:
        escaped = escaped.replace(ch, "\\" + ch)
    return flatten_newlines(escaped)
