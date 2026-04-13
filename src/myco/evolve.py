"""
Myco Skill Evolution — metadata-preserving mutations with constraint gates.

Wave C1-C2: Absorbed from hermes-agent-self-evolution patterns.
- C1: SkillVariant dataclass, diff_variants()
- C2: HARD_GATES constraint system, secret redaction

Design principle (Bitter Lesson): Myco provides scaffolding (parse, serialize,
gate checks), Agent provides intelligence via MCP tool layer.
"""
# --- Mycelium references ---
# Engine spec:  docs/evolution_engine.md (full design, constraint gates, scoring)
# Output dir:   skills/.evolved/ (mutated skill variants land here)
# Absorption:   docs/primordia/hermes_absorption_craft (C1-C3 lineage)

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# ---------------------------------------------------------------------------
# C1: Skill representation + mutations
# ---------------------------------------------------------------------------

@dataclass
class SkillVariant:
    """A skill version with immutable metadata and evolvable body."""
    meta: Dict[str, Any]       # YAML frontmatter (immutable across mutations)
    body: str                  # Markdown body (evolvable)
    parent_hash: Optional[str] = None  # SHA256 of parent variant
    generation: int = 0        # Mutation generation count

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(
            (yaml.dump(self.meta) + self.body).encode("utf-8")
        ).hexdigest()[:12]


def parse_skill(path: Path) -> SkillVariant:
    """Parse a SKILL.md-style file into a SkillVariant."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return SkillVariant(meta={}, body=text)

    parts = text.split("---", 2)
    if len(parts) < 3:
        return SkillVariant(meta={}, body=text)

    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        meta = {}

    body = parts[2].strip()
    return SkillVariant(meta=meta, body=body)


def serialize_skill(variant: SkillVariant) -> str:
    """Serialize a SkillVariant back to SKILL.md format."""
    meta_str = yaml.dump(variant.meta, default_flow_style=False, allow_unicode=True).strip()
    return f"---\n{meta_str}\n---\n\n{variant.body}\n"


def diff_variants(old: SkillVariant, new: SkillVariant) -> Dict[str, Any]:
    """Structured diff between two variants."""
    return {
        "meta_changed": old.meta != new.meta,
        "body_changed": old.body != new.body,
        "parent_hash": new.parent_hash,
        "generation": new.generation,
        "old_hash": old.content_hash,
        "new_hash": new.content_hash,
        "old_body_len": len(old.body),
        "new_body_len": len(new.body),
        "size_delta": len(new.body) - len(old.body),
    }


# ---------------------------------------------------------------------------
# C2: Constraint gates (hard reject, not soft score)
# ---------------------------------------------------------------------------

def gate_frontmatter_preserved(old: SkillVariant, new: SkillVariant) -> Optional[str]:
    """HARD GATE: frontmatter must not be altered by mutation."""
    if old.meta != new.meta:
        return f"frontmatter_changed: metadata must be preserved across mutations"
    return None


def gate_body_nonempty(new: SkillVariant) -> Optional[str]:
    """HARD GATE: body must not be empty."""
    if not new.body.strip():
        return "body_empty: mutation produced empty body"
    return None


def gate_no_secret_leak(new: SkillVariant) -> Optional[str]:
    """HARD GATE: body must not contain secrets."""
    from myco.redact import contains_secret
    if contains_secret(new.body):
        return "secret_leak: mutation body contains potential secrets"
    return None


def gate_size_growth(old: SkillVariant, new: SkillVariant, max_growth: float = 0.5) -> Optional[str]:
    """HARD GATE: body must not grow more than max_growth (50% default)."""
    if len(old.body) > 0:
        growth = (len(new.body) - len(old.body)) / len(old.body)
        if growth > max_growth:
            return f"size_growth: body grew {growth:.0%} (max {max_growth:.0%})"
    return None


HARD_GATES = [
    lambda old, new: gate_frontmatter_preserved(old, new),
    lambda old, new: gate_body_nonempty(new),
    lambda old, new: gate_no_secret_leak(new),
    lambda old, new: gate_size_growth(old, new),
]


def check_gates(old: SkillVariant, new: SkillVariant) -> List[str]:
    """Run all hard gates. Returns list of failure messages (empty = pass)."""
    failures = []
    for gate in HARD_GATES:
        result = gate(old, new)
        if result:
            failures.append(result)
    return failures


# ---------------------------------------------------------------------------
# E3: Skill export (portable bundle for archival/sharing)
# ---------------------------------------------------------------------------

def export_evolved_skill(
    variant: SkillVariant,
    *,
    source_project: str = "",
    evolution_metrics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Package an evolved skill into a portable bundle.

    Can be used for skill export, sharing, or archival. Good mutations
    can be manually transferred between Myco instances.

    Returns a bundle dict ready for serialization to YAML/JSON.
    """
    bundle = {
        "type": "evolved_skill",
        "version": "1.0",
        "meta": dict(variant.meta),
        "body": variant.body,
        "parent_hash": variant.parent_hash,
        "generation": variant.generation,
        "content_hash": variant.content_hash,
        "source_project": source_project,
    }
    if evolution_metrics:
        bundle["metrics"] = evolution_metrics
    return bundle


