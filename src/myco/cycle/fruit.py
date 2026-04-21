"""craft verb: scaffold a new three-round primordia doc.

MAJOR 9 (v0.5): elevates "craft" from a markdown-social-convention to
a real agent-callable verb. Given a ``--topic <slug>`` (and optional
``--kind`` tag), writes a new file at::

    docs/primordia/<slug>_craft_<YYYY-MM-DD>.md

with the three-round skeleton (claim / self-rebuttal / revision /
counter-rebuttal / reflection) pre-structured. The agent fills in
each section; the immune kernel (a future dimension CR1) verifies
the body shape meets the protocol floor.

Refuses to overwrite an existing file. Emits the final path in the
Result payload so the caller can open it.

Governing manifest: ``docs/architecture/L3_IMPLEMENTATION/command_manifest.md``
(governance-verbs section, v0.5 — per v0.5.0 craft §R13, no new L2
surface.md was created; the governance-verbs content lives at L3
alongside the rest of the verb surface). Legacy reference: the
pre-rewrite ``craft_protocol.md`` under ``legacy_v0_3/``.
"""

from __future__ import annotations

import re
import string
from collections.abc import Mapping
from datetime import date as _date
from importlib.resources import files as _pkg_files

from myco.core.context import MycoContext, Result
from myco.core.errors import ContractError, UsageError
from myco.core.io_atomic import atomic_utf8_write
from myco.core.write_surface import check_write_allowed

__all__ = ["run"]


_SLUG_RE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")


def _slugify(raw: str) -> str:
    """Normalize ``raw`` to a craft-slug shape.

    Accepts human-written phrases ("Schema forward-compat") and emits
    ``schema_forward_compat``. Rejects slugs that cannot be made
    conforming (e.g. bare digits, punctuation-only).
    """
    lowered = raw.strip().lower()
    # Replace any non-alnum with underscores, collapse runs, trim.
    normalized = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    # Ensure leading char is a letter.
    if not normalized or not normalized[0].isalpha():
        raise UsageError(
            f"craft: topic {raw!r} does not yield a valid slug. "
            f"Topic must start with a letter and contain letters, "
            f"digits, spaces, or underscores."
        )
    if not _SLUG_RE.match(normalized):
        raise UsageError(
            f"craft: derived slug {normalized!r} does not match the "
            f"craft-slug pattern [a-z][a-z0-9_]*."
        )
    return normalized


def _title_case(slug: str) -> str:
    """Turn ``schema_forward_compat`` into ``Schema Forward Compat``."""
    return " ".join(part.capitalize() for part in slug.split("_"))


def _load_template() -> str:
    return (
        _pkg_files("myco.cycle.templates")
        .joinpath("fruit.md.tmpl")
        .read_text(encoding="utf-8")
    )


def run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Manifest handler: scaffold a primordia craft doc.

    Writes ``docs/primordia/<slug>_craft_<date>.md`` with the
    three-round skeleton (claim → rebuttal → revision → counter →
    convergence). Refuses to overwrite; agent fills in each section.
    """
    topic_raw = args.get("topic")
    if not topic_raw:
        raise UsageError("craft: --topic is required")

    slug = _slugify(str(topic_raw))
    kind = str(args.get("kind") or "design").strip() or "design"
    today = str(args.get("date") or _date.today().isoformat())

    primordia_dir = ctx.substrate.root / "docs" / "primordia"
    primordia_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{slug}_craft_{today}.md"
    target = primordia_dir / filename
    if target.exists():
        raise ContractError(
            f"craft: refusing to overwrite existing {target}. "
            f"Either edit it directly or rename it."
        )

    template = string.Template(_load_template())
    body = template.safe_substitute(
        topic=str(topic_raw),
        slug=slug,
        kind=kind,
        date=today,
        title=_title_case(slug),
    )
    # v0.5.8 guarded rollout: fruit writes craft docs under
    # ``docs/primordia/``; verify the target is in-surface before emit.
    check_write_allowed(ctx, target, verb="fruit")
    atomic_utf8_write(target, body)

    return Result(
        exit_code=0,
        payload={
            "path": str(target.relative_to(ctx.substrate.root)),
            "slug": slug,
            "kind": kind,
            "date": today,
            "rounds": 3,
            "status": "DRAFT",
        },
    )
