"""
Myco Session Miner — extract eval examples from conversation history.

Wave C4: Mines Claude Code session transcripts (indexed by sessions.py)
for skill-relevant examples. Uses redact.py to strip secrets.
Produces structured EvalExample objects for skill evolution.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from myco.redact import redact_secrets


@dataclass
class EvalExample:
    """Structured evaluation example for skill scoring."""
    task_input: str          # What the user asked
    expected_behavior: str   # Rubric (not ground truth)
    difficulty: str = "medium"  # easy / medium / hard
    source_session: str = ""    # Session file it came from
    turn_index: int = 0        # Turn number in session


def mine_eval_examples(
    root: Path,
    skill_id: str,
    *,
    limit: int = 20,
    db_path: Optional[Path] = None,
) -> List[EvalExample]:
    """Mine session history for examples relevant to a skill.

    Searches the FTS5 session index for conversations mentioning the
    skill's key terms, extracts user/assistant pairs as eval examples,
    and redacts secrets.

    Args:
        root: Project root.
        skill_id: Skill name to search for (e.g., "metabolic-cycle").
        limit: Max examples to return.
        db_path: Override sessions.db path.

    Returns:
        List of EvalExample objects with redacted content.
    """
    from myco.sessions import search_sessions

    results = search_sessions(root, skill_id, limit=limit * 2, db_path=db_path)

    examples = []
    for r in results:
        if r["role"] != "user":
            continue
        # Pair with next assistant response if available
        task_input = redact_secrets(r.get("snippet", ""))
        if not task_input.strip():
            continue

        examples.append(EvalExample(
            task_input=task_input[:500],
            expected_behavior=f"Relevant to skill '{skill_id}': agent should follow skill protocol",
            difficulty="medium",
            source_session=r.get("session_file", ""),
            turn_index=r.get("turn_index", 0),
        ))

        if len(examples) >= limit:
            break

    return examples
