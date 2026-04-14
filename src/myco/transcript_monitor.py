"""
Myco transcript monitor — passive session ingest (Wave 58 / Wave 3).

Purpose:
    Sample the running session's transcript periodically, extract
    decisions / preferences / new vocabulary, and auto-eat them as raw
    notes. The user never has to remember "save this" — the substrate
    does it.

Contract:
    - Pure-Python pattern extraction (no LLM calls, <5ms per sample).
    - Idempotent: dedupe by content hash against recent notes in
      .myco_state/transcript_ingested.json.
    - Never raises; always returns a structured dict.
    - Respects .myco_state/transcript_monitor.off  (opt-out sentinel).

Activation paths:
    1. Direct MCP tool: myco_ingest_transcript(transcript_chunks=[…])
    2. Host hook: hosts/{cowork,claude_code}.py invokes during idle tick.

The monitor consumes transcript *chunks* (dicts with role/text); it
never touches host-specific storage directly. The host is responsible
for sourcing transcript frames.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


SENTINEL_OFF = "transcript_monitor.off"
STATE_FILE = "transcript_ingested.json"
STATE_DIR = ".myco_state"

# Patterns reused/extended from observe_turn — kept independent so we
# can tune them separately (transcripts are multi-turn; user-turn
# observer is single-turn).
_DECISION_RE = re.compile(
    r"\b(decid(?:e|ed|ing)|agreed?|let'?s\s+go\s+with|going to use|"
    r"picked|selected|chose|conclude that|the plan is|"
    r"决定|同意|选择|使用|采用)\b",
    re.IGNORECASE,
)
_PREFERENCE_RE = re.compile(
    r"\b(I\s+prefer|I\s+want|I'd\s+rather|from\s+now\s+on|"
    r"always|never|make\s+sure|"
    r"我想|我需要|我更喜欢|永远|再也不|必须)\b",
    re.IGNORECASE,
)
_VOCAB_RE = re.compile(
    r"(?:call(?:ing|ed)?\s+(?:it|this)|aka|short\s+for|"
    r"stands\s+for|简称为|代号|叫做)\s+['\"]?([\w\-]{2,})['\"]?",
    re.IGNORECASE,
)
_ROOT_CAUSE_RE = re.compile(
    r"\b(root\s+cause|turns\s+out|the\s+bug\s+was|"
    r"fixed\s+by|the\s+problem\s+is|原因是|问题出在|修复了)\b",
    re.IGNORECASE,
)


def is_disabled(root: Path) -> bool:
    return (Path(root) / STATE_DIR / SENTINEL_OFF).exists()


def _load_state(root: Path) -> Dict[str, Any]:
    sf = Path(root) / STATE_DIR / STATE_FILE
    if not sf.exists():
        return {"hashes": [], "last_run": None, "count": 0}
    try:
        return json.loads(sf.read_text(encoding="utf-8"))
    except Exception:
        return {"hashes": [], "last_run": None, "count": 0}


def _save_state(root: Path, state: Dict[str, Any]) -> None:
    d = Path(root) / STATE_DIR
    d.mkdir(parents=True, exist_ok=True)
    (d / STATE_FILE).write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _hash_chunk(text: str) -> str:
    return hashlib.sha1(text.strip().encode("utf-8", errors="replace")).hexdigest()[:16]


def _classify_chunk(text: str) -> Optional[Dict[str, Any]]:
    """Return {kind, tags, preview} if the chunk is eat-worthy, else None."""
    t = text.strip()
    if len(t) < 24:
        return None

    tags: List[str] = ["auto", "transcript"]
    kind: Optional[str] = None

    if _DECISION_RE.search(t):
        tags.append("decision")
        kind = "decision"
    elif _PREFERENCE_RE.search(t):
        tags.append("preference")
        kind = "preference"
    elif _ROOT_CAUSE_RE.search(t):
        tags.append("root-cause")
        kind = "root-cause"
    elif _VOCAB_RE.search(t):
        tags.append("vocabulary")
        kind = "vocabulary"

    if not kind:
        return None

    return {
        "kind": kind,
        "tags": tags,
        "preview": t[:400] + ("…" if len(t) > 400 else ""),
    }


def ingest_transcript(
    root: Path,
    chunks: List[Dict[str, Any]],
    *,
    max_eat: int = 5,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Process transcript chunks, auto-eat the classifiable ones.

    Args:
        chunks: List of {"role": "user"|"assistant", "text": str, ...}.
        max_eat: Upper bound on eats per call (protects against bursts).
        dry_run: If True, do not write notes; return what would be eaten.

    Returns:
        {
          "scanned": int,
          "classified": int,
          "ate": int,
          "skipped_duplicate": int,
          "disabled": bool,
          "new_note_ids": [...],
          "errors": [...],
        }
    """
    result: Dict[str, Any] = {
        "scanned": 0,
        "classified": 0,
        "ate": 0,
        "skipped_duplicate": 0,
        "disabled": False,
        "new_note_ids": [],
        "errors": [],
    }

    root = Path(root).resolve()
    if not (root / "_canon.yaml").exists():
        result["errors"].append("not a Myco project")
        return result

    if is_disabled(root):
        result["disabled"] = True
        return result

    state = _load_state(root)
    known = set(state.get("hashes") or [])
    eats = 0

    for ch in (chunks or []):
        result["scanned"] += 1
        text = str(ch.get("text") or "").strip()
        role = str(ch.get("role") or "user")
        if not text:
            continue
        # Only user turns and assistant explicit decisions.
        if role not in {"user", "assistant"}:
            continue

        classified = _classify_chunk(text)
        if not classified:
            continue
        result["classified"] += 1

        h = _hash_chunk(text)
        if h in known:
            result["skipped_duplicate"] += 1
            continue

        if eats >= max_eat:
            continue

        if dry_run:
            result["new_note_ids"].append(f"dry-run:{classified['kind']}:{h}")
            eats += 1
            known.add(h)
            continue

        try:
            from myco.notes import write_note
            note_path = write_note(
                root,
                classified["preview"],
                tags=classified["tags"],
                source="chat",
                status="raw",
                title=(
                    f"[{classified['kind']}] transcript "
                    f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
                ),
            )
            result["new_note_ids"].append(note_path.stem)
            eats += 1
            known.add(h)
        except Exception as e:
            result["errors"].append(f"eat failed ({classified['kind']}): {e}")

    result["ate"] = eats

    # Persist state — keep last 500 hashes to bound file size.
    state["hashes"] = list(known)[-500:]
    state["last_run"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    state["count"] = int(state.get("count", 0)) + eats
    try:
        _save_state(root, state)
    except Exception as e:
        result["errors"].append(f"state save: {e}")

    return result
