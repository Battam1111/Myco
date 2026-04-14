"""
Myco reflex chains — inter-tool auto-linkage (Wave 57 / Wave 2).

Three chains, each composing two tools so the Agent needs only a single
entry point:

    eat      → supersede_detect   (mark near-duplicate older notes as
                                   superseded_by the fresh note)
    verify   → rescent             (when a verify marks a note contradicted,
                                   auto-queue a scent on its topic)
    hunger   → scent               (for each semantic_gap signal in hunger,
                                   auto-run a shallow scent and attach
                                   results to the hunger response)

Each function is pure and returns a small dict so the caller (usually
an MCP tool handler) can merge it into the user-facing JSON response.
Reflex chains are safe-by-default: they never raise — errors become
structured entries in the returned dict.
"""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional


# --------------------------------------------------------------------------
# Utilities
# --------------------------------------------------------------------------

_STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "from", "into", "are",
    "was", "were", "have", "has", "had", "but", "not", "you", "your",
    "our", "their", "they", "them", "his", "her", "its", "per", "via",
    "like", "such", "than", "then", "also", "any", "all", "some", "one",
    "two", "will", "shall", "may", "can", "should", "could", "would",
    "a", "an", "of", "to", "in", "on", "as", "is", "it", "by", "be",
}


def _tokenize(text: str) -> List[str]:
    tokens = re.findall(r"[A-Za-z\u4e00-\u9fff][\w\-]{1,}", text.lower())
    return [t for t in tokens if t not in _STOPWORDS and len(t) >= 2]


def _jaccard(a: List[str], b: List[str]) -> float:
    if not a or not b:
        return 0.0
    sa, sb = set(a), set(b)
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 0.0


def _title_sim(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


# --------------------------------------------------------------------------
# Chain 1: eat → supersede_detect
# --------------------------------------------------------------------------

def detect_supersede_candidates(
    root: Path,
    new_note_id: str,
    *,
    title_threshold: float = 0.75,
    body_threshold: float = 0.5,
    max_results: int = 3,
) -> Dict[str, Any]:
    """Look for older raw/extracted notes that the new note likely supersedes.

    Strategy:
        1. Read new note frontmatter + first ~500 chars of body.
        2. Tokenize title and body; scan all OTHER notes in notes/.
        3. For each candidate with title-sim ≥ title_threshold OR
           body-Jaccard ≥ body_threshold AND same project, append to list.
        4. Excludes notes already superseded / excreted / session-end
           summaries.

    Returns:
        {
          "new_note_id": str,
          "supersedes": [
              {"note_id": str, "title": str, "title_sim": float,
               "body_jaccard": float, "reason": str},
              ...
          ],
          "applied": bool,       # True if caller asked us to write back
          "errors": [str, ...],
        }
    """
    from myco.notes import list_notes, read_note, update_note, id_to_filename

    result: Dict[str, Any] = {
        "new_note_id": new_note_id,
        "supersedes": [],
        "applied": False,
        "errors": [],
    }

    try:
        new_path = Path(root) / "notes" / id_to_filename(new_note_id)
        if not new_path.exists():
            result["errors"].append(f"note not found: {new_note_id}")
            return result
        new_meta, new_body = read_note(new_path)
    except Exception as e:
        result["errors"].append(f"read new note: {e}")
        return result

    new_title = (new_meta.get("title") or _first_heading(new_body) or "").strip()
    new_tokens = _tokenize(new_body[:1000])
    new_project = new_meta.get("project")
    if not new_title and not new_tokens:
        return result  # nothing to compare against

    candidates: List[Dict[str, Any]] = []
    for p in list_notes(root):
        try:
            meta, body = read_note(p)
        except Exception:
            continue
        nid = meta.get("id")
        if not nid or nid == new_note_id:
            continue
        if meta.get("status") in {"excreted"}:
            continue
        if meta.get("superseded_by"):
            continue
        if "session-end" in (meta.get("tags") or []):
            continue
        # Same-project comparison only (cross-project comparisons fire
        # colony/cross_project rather than supersede).
        if new_project and meta.get("project") and meta.get("project") != new_project:
            continue

        cand_title = (meta.get("title") or _first_heading(body) or "").strip()
        tsim = _title_sim(new_title, cand_title) if new_title and cand_title else 0.0
        bjac = _jaccard(new_tokens, _tokenize(body[:1000]))

        if tsim >= title_threshold or bjac >= body_threshold:
            reason_parts = []
            if tsim >= title_threshold:
                reason_parts.append(f"title similarity {tsim:.2f}")
            if bjac >= body_threshold:
                reason_parts.append(f"body overlap {bjac:.2f}")
            candidates.append({
                "note_id": nid,
                "title": cand_title[:80],
                "title_sim": round(tsim, 3),
                "body_jaccard": round(bjac, 3),
                "reason": ", ".join(reason_parts),
            })

    # Rank by combined score and cap.
    candidates.sort(
        key=lambda c: c["title_sim"] * 0.6 + c["body_jaccard"] * 0.4,
        reverse=True,
    )
    result["supersedes"] = candidates[:max_results]
    return result


def apply_supersede(
    root: Path,
    new_note_id: str,
    old_note_ids: List[str],
) -> Dict[str, Any]:
    """Write supersedes / superseded_by links between new and old notes."""
    from myco.notes import read_note, update_note, id_to_filename

    result: Dict[str, Any] = {"applied": [], "errors": []}
    new_path = Path(root) / "notes" / id_to_filename(new_note_id)
    if not new_path.exists():
        result["errors"].append(f"new note not found: {new_note_id}")
        return result

    try:
        new_meta, _ = read_note(new_path)
        existing = list(new_meta.get("supersedes") or [])
        merged = list(dict.fromkeys(existing + list(old_note_ids)))
        update_note(new_path, supersedes=merged)
    except Exception as e:
        result["errors"].append(f"update new note: {e}")
        return result

    for oid in old_note_ids:
        try:
            op = Path(root) / "notes" / id_to_filename(oid)
            if op.exists():
                update_note(op, superseded_by=new_note_id)
                result["applied"].append(oid)
        except Exception as e:
            result["errors"].append(f"update {oid}: {e}")
    return result


def _first_heading(body: str) -> Optional[str]:
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("#"):
            return s.lstrip("#").strip()
        if s:
            return s[:80]
    return None


# --------------------------------------------------------------------------
# Chain 2: verify → rescent
# --------------------------------------------------------------------------

def verify_to_scent(
    root: Path,
    note_id: str,
    verify_outcome: str,
    *,
    execute: bool = False,
) -> Dict[str, Any]:
    """When a verify marks a note `contradicted`, queue a scent on its topic.

    Args:
        note_id: The note that was verified.
        verify_outcome: one of {"ok", "unchanged", "contradicted", "unknown"}.
        execute: if True, actually run a scent; otherwise just return the
                 suggested_call so the Agent can decide.

    Returns:
        {"triggered": bool, "topic": str, "suggested_call": str,
         "scent_result": dict | None, "errors": [...]}
    """
    result: Dict[str, Any] = {
        "triggered": False,
        "topic": None,
        "suggested_call": None,
        "scent_result": None,
        "errors": [],
    }

    if verify_outcome not in {"contradicted", "unknown"}:
        return result  # no rescent needed

    try:
        from myco.notes import read_note, id_to_filename
        note_path = Path(root) / "notes" / id_to_filename(note_id)
        if not note_path.exists():
            result["errors"].append(f"note not found: {note_id}")
            return result
        meta, body = read_note(note_path)
    except Exception as e:
        result["errors"].append(f"read: {e}")
        return result

    tags = meta.get("tags") or []
    title = meta.get("title") or _first_heading(body) or ""
    topic = None
    for t in tags:
        if t not in {"auto", "auto-observed", "session-end", "decision", "vocabulary"}:
            topic = t
            break
    if not topic and title:
        topic = " ".join(title.split()[:4])
    if not topic:
        result["errors"].append("no topic inferrable")
        return result

    result["triggered"] = True
    result["topic"] = topic
    result["suggested_call"] = f"myco_scent(topic='{topic}')"

    if execute:
        # Direct execution of scent would require invoking the MCP tool's
        # async handler. Reflex chains stay sync+pure by design — we
        # return the `suggested_call` and let the Agent execute it.
        result["scent_result"] = {
            "note": "execute=True defers to Agent — run suggested_call",
        }

    return result


# --------------------------------------------------------------------------
# Chain 3: hunger → scent (shallow)
# --------------------------------------------------------------------------

def hunger_to_scent(
    root: Path,
    hunger_report: Any,
    *,
    max_topics: int = 3,
    execute: bool = False,
) -> Dict[str, Any]:
    """For each semantic_gap / scent-worthy action in a HungerReport, propose
    (or execute) a shallow scent.

    Args:
        hunger_report: dict or HungerReport.to_dict() output.
        max_topics:    upper bound on auto-triggered scents.
        execute:       run scent; otherwise just return suggestions.

    Returns:
        {"scents": [{"topic": str, "suggested_call": str,
                     "result": dict | None}, ...],
         "errors": [...]}
    """
    result: Dict[str, Any] = {"scents": [], "errors": []}
    try:
        actions = []
        if hasattr(hunger_report, "actions"):
            actions = getattr(hunger_report, "actions") or []
        elif isinstance(hunger_report, dict):
            actions = hunger_report.get("actions") or []
    except Exception as e:
        result["errors"].append(f"read hunger: {e}")
        return result

    topics: List[str] = []
    for act in actions:
        if not isinstance(act, dict):
            continue
        if act.get("verb") == "scent":
            t = (act.get("args") or {}).get("topic")
            if t and t not in topics:
                topics.append(t)

    for topic in topics[:max_topics]:
        item: Dict[str, Any] = {
            "topic": topic,
            "suggested_call": f"myco_scent(topic='{topic}')",
            "result": None,
        }
        if execute:
            item["result"] = {"note": "execute=True defers to Agent — run suggested_call"}
        result["scents"].append(item)
    return result
