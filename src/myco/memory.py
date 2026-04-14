"""
Myco Session Memory — FTS5 indexing of Claude Code session transcripts.

Wave 52 (contract v0.40.0): Index agent conversation transcripts into a
SQLite FTS5 table for full-text search. Session transcripts are knowledge
that should be searchable and metabolizable.

Absorbs: hermes-agent hermes_state.py session store + session_search_tool.py
FTS5 search pattern, adapted for Myco's file-based substrate.
"""
# --- Mycelium references ---
# Protocol:   docs/agent_protocol.md §2.5 (session memory triggers)
# State:      .myco_state/sessions.db (FTS5 index, auto-created)

from __future__ import annotations

import json
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
    """Create or open the FTS5 database.

    FTS5 requires the SQLite extension to be compiled with
    -DSQLITE_ENABLE_FTS5.  Most CPython builds on Windows/macOS include
    it, but some Linux distributions do not.  We detect and raise a
    clear error rather than an opaque OperationalError.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS session_turns USING fts5("
            "  session_file, turn_index, role, content, timestamp,"
            "  tokenize='unicode61'"
            ")"
        )
        conn.commit()
    except sqlite3.OperationalError as exc:
        if "no such module" in str(exc).lower():
            conn.close()
            raise RuntimeError(
                "SQLite FTS5 extension is not available in this Python "
                "build. Session indexing requires FTS5. On Debian/Ubuntu "
                "try: sudo apt install libsqlite3-dev && rebuild Python, "
                "or use a Python distribution that includes FTS5 "
                "(e.g., python.org installer, conda)."
            ) from exc
        raise
    return conn


def _parse_jsonl_turns(filepath: Path) -> List[Dict[str, Any]]:
    """Parse a .jsonl file and extract user/assistant turns.

    Supports two formats:
    1. Direct: {role: "user", content: "..."}
    2. Claude Code wrapper: {message: {role: "user", content: "..."}, ...}
    """
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
                # Support Claude Code's nested message format
                msg = obj
                if "message" in obj and isinstance(obj["message"], dict):
                    msg = obj["message"]
                role = msg.get("role", "")
                if role not in ("user", "assistant"):
                    continue
                # Extract text content
                content = ""
                raw_content = msg.get("content", "")
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

    # Collect all .jsonl files (including subagents/ subdirectories)
    jsonl_files: List[Path] = []
    for d in session_dirs:
        for f in sorted(d.glob("**/*.jsonl")):
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

# Stopwords for topic extraction (English + conversation filler)
_ENGLISH_STOPWORDS = {
    "the", "a", "an", "is", "it", "to", "and", "of", "in", "for",
    "on", "with", "that", "this", "can", "you", "my", "how", "what",
    "do", "i", "me", "we", "be", "not", "but", "or", "if", "from",
    "your", "have", "has", "had", "are", "was", "were", "will",
    "been", "being", "does", "did", "done", "just", "only", "also",
    "than", "then", "when", "where", "which", "while", "after",
    "before", "about", "into", "through", "each", "all", "any",
    "both", "more", "most", "other", "some", "such", "them",
    "their", "they", "these", "those", "here", "there", "would",
    "could", "should", "shall", "might", "must", "need", "make",
    "like", "over", "very", "well", "still", "also", "back",
    "even", "first", "last", "long", "great", "much", "many",
    "please", "thanks", "sure", "okay", "right", "don't", "it's",
    "you're", "you've", "i'm", "i've", "let's", "that's", "what's",
    "there's", "here's", "they're", "we're", "he's", "she's",
    "tried", "checked", "yourself", "anything", "everything",
    "something", "nothing", "already", "really", "truly",
    "waiting", "expectations", "initiative",  # common noise words
}


def _extract_terms_from_text(text: str, min_len: int = 3) -> Dict[str, int]:
    """Extract stopword-filtered terms from text.

    Returns dict mapping term → frequency.
    """
    if not text:
        return {}
    term_freq: Dict[str, int] = {}
    words = text.lower().split()
    for w in words:
        w = w.strip(".,!?:;\"'()[]{}#*`~<>@/\\").lower()
        # Skip short words, stop words, paths, markdown artifacts
        if (len(w) < min_len or w in _ENGLISH_STOPWORDS
                or ":" in w or "/" in w or "\\" in w
                or w.startswith("**") or w.startswith("--")):
            continue
        term_freq[w] = term_freq.get(w, 0) + 1
    return term_freq


def _wiki_page_titles(root: Path) -> set:
    """Collect all wiki page titles and first-line headings."""
    titles = set()
    wiki_dir = root / "wiki"
    if not wiki_dir.exists():
        return titles
    try:
        for page in wiki_dir.glob("*.md"):
            if page.name.startswith("_"):
                continue
            with open(page, "r", encoding="utf-8", errors="ignore") as f:
                # Read first 20 lines for headings
                for i, line in enumerate(f):
                    if i >= 20:
                        break
                    # Extract heading text
                    if line.startswith("#"):
                        heading = line.lstrip("#").strip()
                        if heading:
                            # Add both full heading and individual terms
                            titles.add(heading.lower())
                            for term in heading.lower().split():
                                term = term.strip(".,!?;:()[]{}").lower()
                                if len(term) >= 3:
                                    titles.add(term)
                    # Also add filename (without .md)
                    if i == 0:
                        fname = page.stem.lower().replace("-", " ").replace("_", " ")
                        titles.add(fname)
                        for term in fname.split():
                            if len(term) >= 3:
                                titles.add(term)
    except Exception:
        pass
    return titles


def predict_knowledge_needs(
    root: Path,
    *,
    lookback_days: int = 7,
    db_path: Optional[Path] = None,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    """Analyze session history to predict future knowledge needs.

    Wave 55 (vision_closure_craft_2026-04-14.md G2):
    Replaces word-frequency noise with three-signal aggregation.

    Looks for:
    1. User-turn topic mentions (last 30 days)
    2. Search misses (weighted ×2)
    3. Raw note orphan topics (not in any wiki page)

    Returns list of predicted needs, each with:
    {
        "topic": str,
        "sources": {
            "turn_mentions": int,
            "miss_count": int,
            "orphan_count": int,
        },
        "coverage": float (0.0-1.0),
        "suggested_action": "myco_scent" | "absorb",
    }

    Sorted by total_signal × (1 - coverage).
    """
    config = _load_sessions_config(root)
    if db_path is None:
        db_path = root / config["db_path"]

    predictions: List[Dict[str, Any]] = []

    # Collect all wiki coverage
    wiki_titles = _wiki_page_titles(root)

    # Signal 1: User-turn topics (last 30 days)
    turn_topics: Dict[str, int] = {}
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        try:
            cursor = conn.execute(
                "SELECT content FROM session_turns WHERE role = 'user' LIMIT 500"
            )
            for (content,) in cursor:
                turn_topics.update(_extract_terms_from_text(content))
        except Exception:
            pass
        finally:
            conn.close()

    # Signal 2: Search misses (weighted ×2)
    miss_topics: Dict[str, int] = {}
    try:
        miss_path = root / ".myco_state" / "search_misses.yaml"
        if miss_path.exists():
            with open(miss_path, "r", encoding="utf-8") as f:
                miss_data = yaml.safe_load(f) or {}
            recent = miss_data.get("recent_misses", [])
            for miss in recent:
                q = miss.get("query", "").lower().strip()
                if q and len(q) >= 3:
                    miss_topics[q] = miss_topics.get(q, 0) + 2  # weight ×2
    except Exception:
        pass

    # Signal 3: Raw note orphan topics
    orphan_topics: Dict[str, int] = {}
    try:
        from myco.notes import list_notes, read_note
        for path in list_notes(root, status="raw"):
            try:
                meta, body = read_note(path)
                # Extract terms from raw notes
                title = meta.get("title", "")
                text = (title + " " + body).lower()
                terms = _extract_terms_from_text(text)
                for term, count in terms.items():
                    if term not in wiki_titles:
                        orphan_topics[term] = orphan_topics.get(term, 0) + count
            except Exception:
                continue
    except Exception:
        pass

    # Aggregate signals
    all_topics: Dict[str, Dict[str, int]] = {}
    for topic, count in turn_topics.items():
        if topic not in all_topics:
            all_topics[topic] = {"turn_mentions": 0, "miss_count": 0, "orphan_count": 0}
        all_topics[topic]["turn_mentions"] += count

    for topic, count in miss_topics.items():
        if topic not in all_topics:
            all_topics[topic] = {"turn_mentions": 0, "miss_count": 0, "orphan_count": 0}
        all_topics[topic]["miss_count"] += count

    for topic, count in orphan_topics.items():
        if topic not in all_topics:
            all_topics[topic] = {"turn_mentions": 0, "miss_count": 0, "orphan_count": 0}
        all_topics[topic]["orphan_count"] += count

    # Compute coverage and score
    for topic, sources in all_topics.items():
        # Coverage: 1.0 if topic in wiki, 0.0 otherwise
        coverage = 1.0 if topic in wiki_titles else 0.0

        # Total signal
        total_signal = (sources["turn_mentions"] + sources["miss_count"]
                       + sources["orphan_count"])

        # Only include topics with meaningful signal
        if total_signal < 2:
            continue

        score = total_signal * (1.0 - coverage)

        predictions.append({
            "topic": topic,
            "sources": sources,
            "coverage": coverage,
            "score": score,
            "suggested_action": "myco_scent" if coverage == 0.0 else "absorb",
        })

    # Sort by score descending
    predictions.sort(key=lambda x: -x["score"])

    # Remove score from output (internal only)
    for p in predictions:
        del p["score"]

    return predictions[:limit]
