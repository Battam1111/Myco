"""
Myco Proactive Discovery — gap-driven knowledge acquisition.

Wave D1: Detects knowledge gaps from hunger signals and provides structured
context for the Agent to search, evaluate, and ingest external knowledge.
The Agent uses its intelligence (web search, evaluation) — Myco provides
the scaffolding (gap detection, candidate structure, ingestion pipeline).

This is the "proactive metabolism" organ: the organism doesn't wait for
food to arrive, it senses hunger and goes hunting.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


@dataclass
class DiscoveryCandidate:
    """A candidate piece of external knowledge to potentially ingest."""
    topic: str              # What knowledge gap this fills
    search_query: str       # Suggested search query for the Agent
    relevance_threshold: float = 0.6  # Minimum relevance to ingest
    source_signal: str = ""  # Which hunger signal triggered this
    status: str = "pending"  # pending / evaluated / ingested / rejected


def detect_knowledge_gaps(root: Path) -> List[Dict[str, Any]]:
    """Detect knowledge gaps from cohort analysis + search miss history.

    Returns structured gap descriptions that the Agent can act on.
    """
    gaps = []

    # 1. Cohort gaps (tags with only unprocessed notes)
    try:
        from myco.cohorts import gap_detection
        cohort_gaps = gap_detection(root)
        for g in cohort_gaps:
            if g.get("total", 0) >= 2:
                gaps.append({
                    "type": "cohort_gap",
                    "topic": g["tag"],
                    "description": f"Tag '{g['tag']}' has {g['total']} notes but "
                                   f"none are extracted/integrated",
                    "suggested_query": f"{g['tag']} best practices methodology",
                    "priority": g["total"],
                })
    except Exception:
        pass

    # 2. Search misses (queries that returned zero results)
    try:
        import yaml
        miss_path = root / ".myco_state" / "search_misses.yaml"
        if miss_path.exists():
            with open(miss_path, "r", encoding="utf-8") as f:
                miss_data = yaml.safe_load(f) or {}
            recent = miss_data.get("recent_misses", [])
            for miss in recent[-5:]:  # Last 5 misses
                query = miss.get("query", "")
                if query:
                    gaps.append({
                        "type": "search_miss",
                        "topic": query,
                        "description": f"Search for '{query}' returned zero results",
                        "suggested_query": query,
                        "priority": 1,
                    })
    except Exception:
        pass

    # Sort by priority descending
    gaps.sort(key=lambda x: -x.get("priority", 0))
    return gaps


def create_discovery_candidates(gaps: List[Dict[str, Any]]) -> List[DiscoveryCandidate]:
    """Convert knowledge gaps into discovery candidates for the Agent."""
    candidates = []
    for gap in gaps:
        candidates.append(DiscoveryCandidate(
            topic=gap["topic"],
            search_query=gap.get("suggested_query", gap["topic"]),
            source_signal=gap.get("type", "unknown"),
        ))
    return candidates


def evaluate_candidate(
    candidate: DiscoveryCandidate,
    content_summary: str,
    *,
    llm_fn: Optional[Callable[[str], str]] = None,
) -> float:
    """Evaluate a discovery candidate's relevance.

    If llm_fn is provided, uses Agent intelligence for evaluation.
    Otherwise returns a default score.
    """
    if llm_fn is None:
        return 0.5  # Default: uncertain

    prompt = (
        f"Rate the relevance of this content to the knowledge gap.\n\n"
        f"Knowledge gap: {candidate.topic}\n"
        f"Content summary: {content_summary[:500]}\n\n"
        f"Rate relevance from 0.0 (irrelevant) to 1.0 (highly relevant).\n"
        f"Output ONLY a number:"
    )
    response = llm_fn(prompt)
    try:
        score = float(response.strip().split()[0])
        return min(1.0, max(0.0, score))
    except (ValueError, IndexError):
        return 0.5


def ingest_candidate(
    root: Path,
    candidate: DiscoveryCandidate,
    content: str,
    *,
    tags: Optional[List[str]] = None,
) -> Optional[Path]:
    """Ingest a discovery candidate through the myco inlet pipeline.

    Returns the path of the created note, or None on failure.
    """
    try:
        from myco.notes import write_note
        all_tags = [candidate.topic, "discovery", candidate.source_signal]
        if tags:
            all_tags.extend(tags)

        path = write_note(
            root,
            content,
            tags=all_tags,
            source="inlet",
        )
        candidate.status = "ingested"
        return path
    except Exception:
        candidate.status = "rejected"
        return None
