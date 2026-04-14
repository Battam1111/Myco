"""
Myco observe_turn — Agent reflex arc (Wave 57 / Wave 2).

Purpose:
    Give the Agent a single, cheap MCP call to invoke after every user
    turn. We inspect the turn text and return a list of suggested
    tool calls (eat / scent / verify / digest). The Agent either
    executes them directly or skips them; either way, the decision
    surface is reduced to "look at suggestions, pick the obvious ones".

Design philosophy (vision_closure_craft §Wave 2):
    - Pure pattern-matching, zero LLM calls, <1ms latency.
    - Conservative: we'd rather miss a signal than produce a false eat.
    - Every suggestion has a concrete `suggested_call` string the Agent
      can paste-and-run. No protocol reasoning required on the Agent side.

This is the minimal "Agent introspection" hook — the guardrail that
turns Myco from "protocol to remember" into "action sitting in the tool
response, ready to click".
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional


# --------------------------------------------------------------------------
# Heuristic pattern library
# --------------------------------------------------------------------------

# Preference / decision markers — strong eat signal.
_DECISION_PATTERNS = [
    r"\b(decid(?:e|ed|ing)|agree(?:d)?|let'?s go with|we will|going to use|choose|picked)\b",
    r"\b(I want|I prefer|I need|I'd rather|make sure)\b",
    r"\b(from now on|always|never)\b",
    r"(决定|同意|选择|使用|我想|我需要|必须|永远|再也不|采用)",  # zh
    r"\b(don'?t|do not)\s+\w+\s+(again|anymore|ever)",
]

# Shorthand / acronym / nickname introduction — eat as vocabulary.
_VOCAB_PATTERNS = [
    r"\bcall(?:ing|ed)?\s+it\s+['\"]?(\w{2,})['\"]?",
    r"\bshort(?:\s+for|hand)\s+['\"]?(\w+)['\"]?",
    r"\baka\s+(\w+)",
    r"\b(\w+)\s+(?:means|stands for|refers to)\s+",
    r"(\w+)\s*(?:代表|就是|简称|缩写)",  # zh
]

# Unfamiliar-term / gap markers — scent signal.
_SCENT_PATTERNS = [
    r"\bwhat\s+(?:is|are)\s+([A-Z][\w\-]{2,})",
    r"\bhow\s+does\s+(\w{3,})\s+work",
    r"\bsearch\s+for\s+([\"'][^\"']+[\"'])",
    r"\blook\s+(?:up|into)\s+(\w+)",
    r"\b(research|investigate|explore)\s+(\w+)",
    r"(查一下|调研|了解一下)\s*(\w+)",  # zh
]

# Freshness-dependent claims — verify signal.
_VERIFY_PATTERNS = [
    r"\blatest\s+version\b",
    r"\bas\s+of\s+(?:today|now|\d{4})",
    r"\bcurrent(?:ly)?\s+(?:stable|supported|deprecated)",
    r"\bis\s+it\s+still\b",
    r"\bstill\s+(?:works|true|valid|accurate)",
    r"(最新|当前|还能用|仍然|是否还)",  # zh
]

# Completion / decision-done markers — potential digest signal (nudge raw→extracted).
_DIGEST_PATTERNS = [
    r"\b(done|finished|shipped|merged|deployed)\b",
    r"(完成|搞定|推送了)",  # zh
    r"\bthat\s+works\b",
    r"\bgood\s+(?:to\s+go|enough)\b",
]


def _match_any(text: str, patterns: List[str]) -> bool:
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            return True
    return False


def _extract_topics(text: str, patterns: List[str]) -> List[str]:
    topics: List[str] = []
    for p in patterns:
        for m in re.finditer(p, text, re.IGNORECASE):
            if m.groups():
                for g in m.groups():
                    if g and len(g) >= 3 and g.lower() not in {"the", "and", "for", "are", "work"}:
                        topics.append(g.strip("\"' "))
    # Dedupe, preserve order
    seen = set()
    out = []
    for t in topics:
        if t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
    return out[:3]


# --------------------------------------------------------------------------
# Main API
# --------------------------------------------------------------------------

def observe_turn(
    user_turn_text: str,
    *,
    root: Optional[Path] = None,
    previous_assistant_text: str = "",
) -> Dict[str, Any]:
    """Analyze a user turn and return reflex suggestions.

    Returns shape:
        {
          "should_eat":    bool,
          "should_scent":  bool,
          "should_verify": bool,
          "should_digest": bool,
          "suggested_calls": [
              {"tool": "myco_eat", "args": {...}, "reason": "...", "priority": "recommended"},
              ...
          ],
          "reasons": [str, ...],
          "turn_length": int,
          "confidence": "low" | "medium" | "high",
        }

    Never raises. Empty / trivial input returns an empty suggestion set.
    """
    text = (user_turn_text or "").strip()
    result = {
        "should_eat": False,
        "should_scent": False,
        "should_verify": False,
        "should_digest": False,
        "suggested_calls": [],
        "reasons": [],
        "turn_length": len(text),
        "confidence": "low",
    }
    if len(text) < 8:
        return result

    suggestions: List[Dict[str, Any]] = []
    reasons: List[str] = []

    # -- EAT signals ------------------------------------------------------
    if _match_any(text, _DECISION_PATTERNS):
        result["should_eat"] = True
        reasons.append("Turn contains a decision or preference marker.")
        preview = text[:200] + ("…" if len(text) > 200 else "")
        suggestions.append({
            "tool": "myco_eat",
            "args": {
                "content": preview,
                "tags": ["decision", "auto-observed"],
                "source": "chat",
            },
            "reason": "Preserve user decision / preference as a raw note.",
            "priority": "recommended",
        })

    vocab_topics = _extract_topics(text, _VOCAB_PATTERNS)
    if vocab_topics:
        result["should_eat"] = True
        reasons.append(f"Turn introduces vocabulary: {', '.join(vocab_topics)}.")
        suggestions.append({
            "tool": "myco_eat",
            "args": {
                "content": text[:300],
                "tags": ["vocabulary", "auto-observed"],
                "source": "chat",
            },
            "reason": "Capture newly-introduced terminology.",
            "priority": "recommended",
        })

    # -- SCENT signals ----------------------------------------------------
    scent_topics = _extract_topics(text, _SCENT_PATTERNS)
    if scent_topics:
        result["should_scent"] = True
        for topic in scent_topics[:2]:
            reasons.append(f"Turn asks about unfamiliar topic: {topic}.")
            suggestions.append({
                "tool": "myco_scent",
                "args": {"topic": topic},
                "reason": f"User referenced '{topic}' — forage before answering.",
                "priority": "recommended",
            })

    # -- VERIFY signals ---------------------------------------------------
    if _match_any(text, _VERIFY_PATTERNS):
        result["should_verify"] = True
        reasons.append("Turn mentions freshness-dependent claim.")
        suggestions.append({
            "tool": "myco_verify",
            "args": {"scope": "time_sensitive", "limit": 5},
            "reason": "User referenced 'latest' / 'current' — revalidate time_sensitive notes.",
            "priority": "recommended",
        })

    # -- DIGEST signals ---------------------------------------------------
    if _match_any(text, _DIGEST_PATTERNS):
        result["should_digest"] = True
        reasons.append("Turn signals a completed/settled state.")
        suggestions.append({
            "tool": "myco_digest",
            "args": {"note_id": "auto", "to_status": "extracted"},
            "reason": "User marked something done — promote related raw notes.",
            "priority": "optional",
        })

    # -- Confidence band --------------------------------------------------
    if len(suggestions) >= 2:
        result["confidence"] = "high"
    elif len(suggestions) == 1:
        result["confidence"] = "medium"

    result["suggested_calls"] = suggestions
    result["reasons"] = reasons
    return result
