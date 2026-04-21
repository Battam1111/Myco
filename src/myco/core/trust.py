"""Trust-boundary sanitisation helpers.

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

from typing import Final

__all__ = [
    "strip_controls",
    "flatten_newlines",
    "safe_frontmatter_field",
    "markdown_inline_safe",
]


#: C0 control characters (U+0000–U+001F) except for the three that are
#: legitimate in text streams (tab, LF, CR). C1 extended controls
#: (U+0080–U+009F) and the DEL (U+007F) are also stripped since they
#: are almost never intended and appear most often in prompt-injection
#: attempts via ANSI escape sequences.
_CONTROL_CHARS: Final[frozenset[str]] = frozenset(
    chr(c)
    for c in (
        list(range(0x00, 0x09))
        + [0x0B, 0x0C]
        + list(range(0x0E, 0x20))
        + [0x7F]
        + list(range(0x80, 0xA0))
    )
)


#: Meta-characters that activate markdown rendering (links, code,
#: headings, lists, emphasis, images). Escaping these with a leading
#: backslash ensures the wrapped string embeds as *text* rather than
#: re-interpreted markdown.
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
    return s.replace("\r\n", replacement).replace("\n", replacement).replace(
        "\r", replacement
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
        sanitised = sanitised[: max_len - 1] + "\u2026"
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
