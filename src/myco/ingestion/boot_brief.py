"""Maintain a marker-delimited signals block in the entry-point file.

The entry-point (``MYCO.md`` or ``CLAUDE.md``) carries an
agent-visible "signals" block wedged between HTML-comment markers::

    <!-- BEGIN MYCO SIGNALS -->
    (rendered signals here)
    <!-- END MYCO SIGNALS -->

``patch_entry_point`` inserts the block on first call and replaces its
content on subsequent calls. Idempotent: same input → same output.
"""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.core.errors import ContractError

__all__ = [
    "BEGIN_MARKER",
    "END_MARKER",
    "render_signals_block",
    "patch_entry_point",
]

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


def patch_entry_point(
    *,
    ctx: MycoContext,
    signals: dict[str, object],
) -> Path:
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

    text = path.read_text(encoding="utf-8")
    block = render_signals_block(signals)
    new_text = _apply_block(text, block)
    path.write_text(new_text, encoding="utf-8")
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
        # First injection — append at end with a leading blank line.
        sep = "" if text.endswith("\n\n") else ("\n" if text.endswith("\n") else "\n\n")
        return text + sep + block + "\n"

    # Replace existing block.
    start = text.index(BEGIN_MARKER)
    end = text.index(END_MARKER) + len(END_MARKER)
    if end <= start:
        raise ContractError(
            "entry-point signals block corrupt: END appears before BEGIN"
        )
    return text[:start] + block + text[end:]
