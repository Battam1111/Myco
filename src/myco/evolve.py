"""
Myco Skill Evolution — metadata-preserving mutations with constraint gates.

Wave C1-C3: Absorbed from hermes-agent-self-evolution patterns.
- C1: SkillVariant dataclass, mutate_skill(), diff_variants()
- C2: HARD_GATES constraint system, secret redaction
- C3: Multi-dimensional scoring with LLM-as-judge

Design principle (Bitter Lesson): Myco provides scaffolding, Agent provides
intelligence via llm_fn callable. Myco never calls an LLM directly.
"""
# --- Mycelium references ---
# Engine spec:  docs/evolution_engine.md (full design, constraint gates, scoring)
# Output dir:   skills/.evolved/ (mutated skill variants land here)
# Absorption:   docs/primordia/hermes_absorption_craft (C1-C3 lineage)

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

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


def mutate_skill(
    skill_path: Path,
    mutation_prompt: str,
    *,
    llm_fn: Callable[[str], str],
) -> SkillVariant:
    """Create a mutated variant of a skill using Agent intelligence.

    Args:
        skill_path: Path to the skill file.
        mutation_prompt: What to change about the skill.
        llm_fn: Agent-provided callable that takes a prompt and returns text.
            Myco never calls LLMs directly (Bitter Lesson compliance).

    Returns:
        New SkillVariant with preserved metadata and mutated body.
    """
    original = parse_skill(skill_path)

    prompt = (
        f"You are evolving a Myco skill. Preserve ALL YAML frontmatter exactly.\n"
        f"Only modify the markdown body below the frontmatter.\n\n"
        f"Current body:\n{original.body}\n\n"
        f"Mutation request: {mutation_prompt}\n\n"
        f"Output ONLY the new body (no frontmatter, no fences):"
    )

    new_body = llm_fn(prompt)

    return SkillVariant(
        meta=dict(original.meta),  # Preserve metadata immutably
        body=new_body.strip(),
        parent_hash=original.content_hash,
        generation=original.generation + 1,
    )


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
# C3: Multi-dimensional scoring
# ---------------------------------------------------------------------------

SCORING_DIMENSIONS = ["clarity", "completeness", "conciseness", "correctness"]


@dataclass
class EvalResult:
    """Result of evaluating a skill variant."""
    scores: Dict[str, float]   # dimension -> 0.0-1.0
    feedback: Dict[str, str]   # dimension -> textual feedback
    composite: float = 0.0     # weighted composite score

    def __post_init__(self):
        if self.scores and not self.composite:
            weights = {"clarity": 0.2, "completeness": 0.3,
                       "conciseness": 0.2, "correctness": 0.3}
            self.composite = sum(
                self.scores.get(d, 0.0) * weights.get(d, 0.25)
                for d in SCORING_DIMENSIONS
            )


def evaluate_variant(
    variant: SkillVariant,
    examples: List[Dict[str, str]],
    *,
    llm_fn: Callable[[str], str],
) -> EvalResult:
    """Evaluate a variant against examples using Agent as judge.

    Args:
        variant: The skill variant to evaluate.
        examples: List of {task_input, expected_behavior} dicts.
        llm_fn: Agent-provided callable for LLM-as-judge evaluation.

    Returns:
        EvalResult with per-dimension scores and feedback.
    """
    prompt = (
        f"Rate this skill on 4 dimensions (0.0-1.0).\n\n"
        f"Skill body:\n{variant.body[:2000]}\n\n"
        f"Test examples:\n"
    )
    for ex in examples[:3]:
        prompt += f"- Input: {ex.get('task_input', '')[:200]}\n"
        prompt += f"  Expected: {ex.get('expected_behavior', '')[:200]}\n"
    prompt += (
        f"\nRate each dimension and explain:\n"
        f"clarity: [0.0-1.0] [explanation]\n"
        f"completeness: [0.0-1.0] [explanation]\n"
        f"conciseness: [0.0-1.0] [explanation]\n"
        f"correctness: [0.0-1.0] [explanation]\n"
    )

    response = llm_fn(prompt)

    # Parse response — best-effort extraction
    scores = {}
    feedback = {}
    for dim in SCORING_DIMENSIONS:
        match = re.search(rf"{dim}:\s*([\d.]+)\s*(.*)", response, re.IGNORECASE)
        if match:
            try:
                scores[dim] = min(1.0, max(0.0, float(match.group(1))))
            except ValueError:
                scores[dim] = 0.5
            feedback[dim] = match.group(2).strip()
        else:
            scores[dim] = 0.5
            feedback[dim] = "not evaluated"

    return EvalResult(scores=scores, feedback=feedback)


# ---------------------------------------------------------------------------
# E3: Cross-instance skill transfer (horizontal gene transfer)
# ---------------------------------------------------------------------------

def export_evolved_skill(
    variant: SkillVariant,
    *,
    source_project: str = "",
    evolution_metrics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Package an evolved skill into an upstream-compatible bundle.

    The receiving instance evaluates the skill against its local context
    via LLM-as-judge before absorbing. Good mutations spread across Myco
    instances — this is horizontal gene transfer.

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


def import_evolved_skill(
    bundle: Dict[str, Any],
    target_dir: Path,
    *,
    llm_fn: Optional[Callable[[str], str]] = None,
    relevance_threshold: float = 0.6,
) -> Optional[Path]:
    """Import an evolved skill from another instance.

    Evaluates relevance before writing. Returns skill path if accepted,
    None if rejected.
    """
    if bundle.get("type") != "evolved_skill":
        return None

    variant = SkillVariant(
        meta=bundle.get("meta", {}),
        body=bundle.get("body", ""),
        parent_hash=bundle.get("parent_hash"),
        generation=bundle.get("generation", 0),
    )

    # Evaluate relevance if llm_fn available
    if llm_fn:
        prompt = (
            f"Is this skill relevant to the current project?\n\n"
            f"Skill: {variant.meta.get('name', 'unknown')}\n"
            f"Description: {variant.meta.get('description', '')}\n"
            f"Body preview: {variant.body[:300]}\n\n"
            f"Rate relevance 0.0-1.0. Output ONLY a number:"
        )
        try:
            score = float(llm_fn(prompt).strip().split()[0])
            if score < relevance_threshold:
                return None
        except (ValueError, IndexError):
            pass  # proceed with import on evaluation failure

    # Write skill
    name = variant.meta.get("name", "imported-skill")
    skill_dir = target_dir / "skills"
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skill_dir / f"{name}.md"
    skill_path.write_text(serialize_skill(variant), encoding="utf-8")
    return skill_path
