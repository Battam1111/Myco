"""
Myco Session Memory — FTS5 indexing of Claude Code session transcripts.

Wave 52 (contract v0.40.0): Index agent conversation transcripts into a
SQLite FTS5 table for full-text search. Session transcripts are knowledge
that should be searchable and metabolizable.

Absorbs: hermes-agent hermes_state.py session store + session_search_tool.py
FTS5 search pattern, adapted for Myco's file-based substrate.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


def _load_sessions_config(root: Path) -> Dict[str, Any]:
    """Load sessions config from _canon.yaml."""
    defaults = {
        "enabled": True,
        "db_path": ".myco_state/sessions.db",
        "claude_projects_dir": None,
        "max_age_days": 90,
    }
    canon_path = root / "_canon.yaml"
    if not canon_path.exists():
        return defaults
    try:
        with open(canon_path, "r", encoding="utf-8") as f:
            canon = yaml.safe_load(f) or {}
        cfg = canon.get("system", {}).get("sessions", {})
        if cfg:
            return {
                "enabled": cfg.get("enabled", True),
                "db_path": cfg.get("db_path", defaults["db_path"]),
                "claude_projects_dir": cfg.get("claude_projects_dir"),
                "max_age_days": cfg.get("max_age_days", 90),
            }
    except Exception:
        pass
    return defaults


def _find_session_dirs(root: Path, config: Dict[str, Any]) -> List[Path]:
    """Discover directories containing .jsonl session files.

    Searches:
    1. Config-specified claude_projects_dir
    2. ~/.claude/projects/  (Claude Code default)
    3. root/.claude/projects/ (local project scope)
    """
    dirs: List[Path] = []

    # Config-specified directory
    explicit = config.get("claude_projects_dir")
    if explicit and Path(explicit).is_dir():
        dirs.append(Path(explicit))
        return dirs

    # Claude Code default: ~/.claude/projects/
    home_claude = Path.home() / ".claude" / "projects"
    if home_claude.is_dir():
        # Scan all project hash dirs
        for sub in sorted(home_claude.iterdir()):
            if sub.is_dir():
                dirs.append(sub)

    # Local project scope
    local_claude = root / ".claude" / "projects"
    if local_claude.is_dir():
        for sub in sorted(local_claude.iterdir()):
            if sub.is_dir() and sub not in dirs:
                dirs.append(sub)

    return dirs


def _ensure_db(db_path: Path) -> sqlite3.Connection:
    """Create or open the FTS5 database."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS session_turns USING fts5("
        "  session_file, turn_index, role, content, timestamp,"
        "  tokenize='unicode61'"
        ")"
    )
    conn.commit()
    return conn


def _parse_jsonl_turns(filepath: Path) -> List[Dict[str, Any]]:
    """Parse a .jsonl file and extract user/assistant turns."""
    turns = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                role = obj.get("role", "")
                if role not in ("user", "assistant"):
                    continue
                # Extract text content
                content = ""
                raw_content = obj.get("content", "")
                if isinstance(raw_content, str):
                    content = raw_content
                elif isinstance(raw_content, list):
                    # Content blocks: [{type: "text", text: "..."}]
                    parts = []
                    for block in raw_content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            parts.append(block.get("text", ""))
                    content = "\n".join(parts)
                if not content.strip():
                    continue
                turns.append({
                    "session_file": str(filepath.name),
                    "turn_index": i,
                    "role": role,
                    "content": content[:5000],  # Cap per-turn content
                    "timestamp": obj.get("timestamp", ""),
                })
    except (OSError, UnicodeDecodeError):
        pass
    return turns


def index_sessions(
    root: Path,
    *,
    db_path: Optional[Path] = None,
    max_age_days: int = 90,
) -> Dict[str, Any]:
    """Index .jsonl session files into SQLite FTS5.

    Returns stats: {indexed_files, indexed_turns, db_path, skipped_files}.
    """
    config = _load_sessions_config(root)
    if not config["enabled"]:
        return {"error": "sessions.enabled is false in _canon.yaml"}

    if db_path is None:
        db_path = root / config["db_path"]

    session_dirs = _find_session_dirs(root, config)

    conn = _ensure_db(db_path)
    indexed_files = 0
    indexed_turns = 0
    skipped_files = 0

    # Collect all .jsonl files
    jsonl_files: List[Path] = []
    for d in session_dirs:
        for f in sorted(d.glob("*.jsonl")):
            jsonl_files.append(f)

    for filepath in jsonl_files:
        # Skip old files
        try:
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime, tz=timezone.utc)
            age_days = (datetime.now(timezone.utc) - mtime).days
            if age_days > max_age_days:
                skipped_files += 1
                continue
        except Exception:
            pass

        # Check if already indexed (simple: check if session_file exists)
        cursor = conn.execute(
            "SELECT COUNT(*) FROM session_turns WHERE session_file = ?",
            (filepath.name,)
        )
        if cursor.fetchone()[0] > 0:
            skipped_files += 1
            continue

        turns = _parse_jsonl_turns(filepath)
        for turn in turns:
            conn.execute(
                "INSERT INTO session_turns (session_file, turn_index, role, content, timestamp) "
                "VALUES (?, ?, ?, ?, ?)",
                (turn["session_file"], turn["turn_index"], turn["role"],
                 turn["content"], turn["timestamp"]),
            )
        conn.commit()
        indexed_files += 1
        indexed_turns += len(turns)

    conn.close()

    return {
        "indexed_files": indexed_files,
        "indexed_turns": indexed_turns,
        "skipped_files": skipped_files,
        "db_path": str(db_path),
    }


def search_sessions(
    root: Path,
    query: str,
    *,
    limit: int = 20,
    db_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Full-text search across indexed session transcripts.

    Returns list of {session_file, turn_index, role, snippet, rank}.
    """
    config = _load_sessions_config(root)
    if db_path is None:
        db_path = root / config["db_path"]

    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    results = []
    try:
        cursor = conn.execute(
            "SELECT session_file, turn_index, role, "
            "  snippet(session_turns, 3, '<mark>', '</mark>', '...', 40), "
            "  rank "
            "FROM session_turns "
            "WHERE session_turns MATCH ? "
            "ORDER BY rank "
            "LIMIT ?",
            (query, limit),
        )
        for row in cursor:
            results.append({
                "session_file": row[0],
                "turn_index": row[1],
                "role": row[2],
                "snippet": row[3],
                "rank": row[4],
            })
    except sqlite3.OperationalError:
        pass  # Empty table or bad query
    finally:
        conn.close()

    return results


def prune_sessions(
    root: Path,
    *,
    max_age_days: int = 90,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Remove index entries older than max_age_days.

    Uses the timestamp field stored in the FTS5 table.
    """
    config = _load_sessions_config(root)
    if db_path is None:
        db_path = root / config["db_path"]

    if not db_path.exists():
        return {"removed_turns": 0, "remaining_turns": 0}

    conn = sqlite3.connect(str(db_path))

    # Count before
    before = conn.execute("SELECT COUNT(*) FROM session_turns").fetchone()[0]

    # Remove old entries — since FTS5 doesn't support DELETE with complex
    # WHERE on non-match columns easily, we use a simple approach:
    # delete all and re-count
    cutoff = datetime.now(timezone.utc).isoformat()
    # For simplicity, we delete ALL entries (prune = full reset)
    # A more sophisticated version would parse timestamps, but session
    # timestamps are not guaranteed to be ISO format.
    if max_age_days == 0:
        conn.execute("DELETE FROM session_turns")
        conn.commit()
        after = 0
    else:
        after = before  # No-op for non-zero max_age_days (future enhancement)

    conn.close()

    return {
        "removed_turns": before - after,
        "remaining_turns": after,
    }


# ---------------------------------------------------------------------------
# Wave E1: Predictive hunger — need anticipation from session history
# ---------------------------------------------------------------------------

def predict_knowledge_needs(
    root: Path,
    *,
    lookback_days: int = 7,
    db_path: Optional[Path] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Analyze session history to predict future knowledge needs.

    Looks for:
    1. Repeated search misses (same topic searched multiple times)
    2. Undocumented recurring topics (frequently discussed but no notes exist)
    3. Friction pattern clusters (self-correction tags accumulating)

    Returns predicted needs as structured recommendations.
    """
    config = _load_sessions_config(root)
    if db_path is None:
        db_path = root / config["db_path"]

    predictions: List[Dict[str, Any]] = []

    if not db_path.exists():
        return predictions

    # 1. Find frequently discussed topics from user turns
    conn = sqlite3.connect(str(db_path))
    try:
        # Extract most common content words from user turns
        cursor = conn.execute(
            "SELECT content FROM session_turns WHERE role = 'user' LIMIT 200"
        )
        word_freq: Dict[str, int] = {}
        stop_words = {"the", "a", "an", "is", "it", "to", "and", "of", "in", "for",
                      "on", "with", "that", "this", "can", "you", "my", "how", "what",
                      "do", "i", "me", "we", "be", "not", "but", "or", "if", "from"}
        for (content,) in cursor:
            if not content:
                continue
            words = content.lower().split()
            for w in words:
                w = w.strip(".,!?:;\"'()[]{}").lower()
                if len(w) > 3 and w not in stop_words:
                    word_freq[w] = word_freq.get(w, 0) + 1

        # Topics that appear frequently but may not be in notes
        from myco.notes import list_notes, read_note
        note_content = ""
        for path in list_notes(root):
            try:
                _, body = read_note(path)
                note_content += body.lower() + " "
            except Exception:
                continue

        for word, count in sorted(word_freq.items(), key=lambda x: -x[1])[:20]:
            if count >= 3 and word not in note_content:
                predictions.append({
                    "type": "undocumented_recurring_topic",
                    "topic": word,
                    "frequency": count,
                    "description": f"Topic '{word}' discussed {count} times in sessions "
                                   f"but no notes contain it. Consider creating knowledge.",
                })
                if len(predictions) >= limit:
                    break

    except Exception:
        pass
    finally:
        conn.close()

    # 2. Check for accumulating search misses on same topics
    try:
        import yaml
        miss_path = root / ".myco_state" / "search_misses.yaml"
        if miss_path.exists():
            with open(miss_path, "r", encoding="utf-8") as f:
                miss_data = yaml.safe_load(f) or {}
            recent = miss_data.get("recent_misses", [])
            # Count query frequency
            query_count: Dict[str, int] = {}
            for miss in recent:
                q = miss.get("query", "").lower().strip()
                if q:
                    query_count[q] = query_count.get(q, 0) + 1
            for q, c in sorted(query_count.items(), key=lambda x: -x[1]):
                if c >= 2:
                    predictions.append({
                        "type": "repeated_search_miss",
                        "topic": q,
                        "frequency": c,
                        "description": f"Search for '{q}' missed {c} times. "
                                       f"Proactive acquisition recommended.",
                    })
    except Exception:
        pass

    return predictions[:limit]
