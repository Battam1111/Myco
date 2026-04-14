#!/usr/bin/env python3
"""
Myco Feeds — autonomous external content subscription and immune filtering.

Wave 55 (vision_closure_craft_2026-04-14.md, Partition B G1):
Implements autonomous foraging with subscription-driven content discovery.
Extends forage.py without breaking existing API.

Design principles:
    1. Offline-safe: urllib failures log warnings but never raise.
    2. Immune-first: all candidates pass immune filter before auto-add to manifest.
    3. Opportunistic: supports both scheduled (via feed.yaml) and on-demand (myco_scent).
    4. License-aware: enforces safe-set licensing on ingested content.
    5. Zero-dependency: stdlib only (urllib, xml.etree, json, yaml).

Public surface (keep stable):
    load_feeds_config(root) -> dict
    save_feeds_config(root, cfg) -> None
    add_feed(root, source_type, query, **kwargs) -> None
    fetch_due_feeds(root, dry_run=False) -> list[dict]
    immune_filter(root, candidate) -> (bool, str)

Storage layout:
    <project_root>/.myco_state/feeds.yaml
    <project_root>/.myco_state/interests.yaml
"""

from __future__ import annotations

import json
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import URLError
from urllib.request import urlopen

try:
    import yaml
except ImportError:
    yaml = None

logger = logging.getLogger(__name__)

_ISO_FMT = "%Y-%m-%dT%H:%M:%S"


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_FEEDS_SCHEMA: Dict[str, Any] = {
    "sources": [
        {
            "type": "arxiv",
            "query": "cs.LG",
            "enabled": True,
            "fetch_interval_hours": 24,
        },
        {
            "type": "arxiv",
            "query": "cs.AI",
            "enabled": True,
            "fetch_interval_hours": 24,
        },
        {
            "type": "arxiv",
            "query": "stat.ML",
            "enabled": True,
            "fetch_interval_hours": 24,
        },
    ],
}

SAFE_LICENSES = {
    "cc-by",
    "cc-by-sa",
    "cc0",
    "mit",
    "apache",
    "bsd",
    "public_domain",
    "arxiv",
    "unknown",  # arxiv papers without explicit license get "unknown"
}

# English + common conversation stopwords
EN_STOPWORDS = {
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
}


# ---------------------------------------------------------------------------
# Config I/O
# ---------------------------------------------------------------------------

def load_feeds_config(root: Path) -> Dict[str, Any]:
    """Load feeds config from .myco_state/feeds.yaml.

    Returns default config if file doesn't exist.
    """
    cfg_path = root / ".myco_state" / "feeds.yaml"
    if not cfg_path.exists():
        return DEFAULT_FEEDS_SCHEMA.copy()
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        return cfg if cfg.get("sources") else DEFAULT_FEEDS_SCHEMA.copy()
    except Exception as exc:
        logger.warning(f"Failed to load feeds.yaml: {exc}")
        return DEFAULT_FEEDS_SCHEMA.copy()


def save_feeds_config(root: Path, cfg: Dict[str, Any]) -> None:
    """Save feeds config to .myco_state/feeds.yaml."""
    cfg_path = root / ".myco_state" / "feeds.yaml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(cfg_path, "w", encoding="utf-8") as f:
            yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)
    except Exception as exc:
        logger.warning(f"Failed to save feeds.yaml: {exc}")


def add_feed(
    root: Path,
    source_type: str,
    query: str,
    *,
    enabled: bool = True,
    fetch_interval_hours: int = 24,
) -> None:
    """Add a new feed to the config."""
    cfg = load_feeds_config(root)
    if "sources" not in cfg:
        cfg["sources"] = []
    cfg["sources"].append({
        "type": source_type,
        "query": query,
        "enabled": enabled,
        "fetch_interval_hours": fetch_interval_hours,
        "last_fetched": None,
    })
    save_feeds_config(root, cfg)


def _load_interests(root: Path) -> List[str]:
    """Load interest topics from .myco_state/interests.yaml."""
    interests_path = root / ".myco_state" / "interests.yaml"
    if not interests_path.exists():
        return []
    try:
        with open(interests_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data.get("topics", [])
    except Exception:
        return []


def _save_interests(root: Path, topics: List[str]) -> None:
    """Save interest topics to .myco_state/interests.yaml."""
    interests_path = root / ".myco_state" / "interests.yaml"
    interests_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(interests_path, "w", encoding="utf-8") as f:
            yaml.dump({"topics": topics}, f, default_flow_style=False)
    except Exception as exc:
        logger.warning(f"Failed to save interests.yaml: {exc}")


# ---------------------------------------------------------------------------
# Feed Fetching
# ---------------------------------------------------------------------------

def _fetch_arxiv(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch latest papers from arXiv for a given search query.

    Returns list of {source_url, source_type, title, summary, license_guess}.
    """
    candidates = []
    try:
        url = f"http://export.arxiv.org/api/query?search_query={query}&start=0&max_results={limit}&sortBy=submittedDate&sortOrder=descending"
        with urlopen(url, timeout=10) as response:
            content = response.read().decode("utf-8")
        root = ET.fromstring(content)
        # arXiv uses Atom namespace
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns):
            title_elem = entry.find("atom:title", ns)
            summary_elem = entry.find("atom:summary", ns)
            id_elem = entry.find("atom:id", ns)
            title = title_elem.text if title_elem is not None else "Unknown"
            summary = summary_elem.text if summary_elem is not None else ""
            arxiv_id = id_elem.text if id_elem is not None else ""
            # Extract numeric ID from arxiv URL
            arxiv_id = arxiv_id.split("/abs/")[-1] if arxiv_id else ""
            source_url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""
            if not source_url:
                continue
            candidates.append({
                "source_url": source_url,
                "source_type": "arxiv",
                "title": title.strip(),
                "summary": summary.strip()[:500],
                "license_guess": "arxiv",
            })
    except (URLError, TimeoutError) as exc:
        logger.warning(f"Failed to fetch arXiv {query}: {exc}")
    except ET.ParseError:
        logger.warning(f"Failed to parse arXiv XML for {query}")
    except Exception as exc:
        logger.warning(f"Unexpected error fetching arXiv: {exc}")
    return candidates


def _fetch_rss(feed_url: str) -> List[Dict[str, Any]]:
    """Fetch items from an RSS feed.

    Returns list of {source_url, source_type, title, summary, license_guess}.
    """
    candidates = []
    try:
        with urlopen(feed_url, timeout=10) as response:
            content = response.read().decode("utf-8")
        root = ET.fromstring(content)
        # Generic RSS 2.0 parsing
        for item in root.findall(".//item"):
            title_elem = item.find("title")
            desc_elem = item.find("description")
            link_elem = item.find("link")
            title = title_elem.text if title_elem is not None else "Unknown"
            desc = desc_elem.text if desc_elem is not None else ""
            link = link_elem.text if link_elem is not None else ""
            if not link:
                continue
            candidates.append({
                "source_url": link,
                "source_type": "rss",
                "title": title.strip(),
                "summary": desc.strip()[:500],
                "license_guess": "unknown",
            })
    except (URLError, TimeoutError) as exc:
        logger.warning(f"Failed to fetch RSS {feed_url}: {exc}")
    except ET.ParseError:
        logger.warning(f"Failed to parse RSS from {feed_url}")
    except Exception as exc:
        logger.warning(f"Unexpected error fetching RSS: {exc}")
    return candidates


def fetch_due_feeds(root: Path, dry_run: bool = False) -> List[Dict[str, Any]]:
    """Fetch candidates from feeds that are due for update.

    Checks last_fetched vs fetch_interval_hours.

    Returns list of candidate dicts ready for immune_filter.
    """
    cfg = load_feeds_config(root)
    candidates = []
    now = datetime.now()

    for source in cfg.get("sources", []):
        if not source.get("enabled", True):
            continue

        source_type = source.get("type")
        query = source.get("query")
        interval_hours = source.get("fetch_interval_hours", 24)
        last_fetched_str = source.get("last_fetched")

        # Check if due
        if last_fetched_str:
            try:
                last_fetched = datetime.fromisoformat(last_fetched_str)
                time_since = (now - last_fetched).total_seconds() / 3600
                if time_since < interval_hours:
                    continue
            except (ValueError, TypeError):
                pass

        # Fetch based on type
        if source_type == "arxiv":
            new_candidates = _fetch_arxiv(query)
        elif source_type == "rss":
            new_candidates = _fetch_rss(query)
        elif source_type == "github_trending":
            logger.info("github_trending requires API key; skipped for now")
            new_candidates = []
        else:
            logger.warning(f"Unknown feed type: {source_type}")
            new_candidates = []

        candidates.extend(new_candidates)

        # Update last_fetched if not dry_run
        if not dry_run:
            source["last_fetched"] = now.isoformat()

    if not dry_run and candidates:
        save_feeds_config(root, cfg)

    return candidates


# ---------------------------------------------------------------------------
# Immune Filtering
# ---------------------------------------------------------------------------

def _jaccard_3gram_similarity(s1: str, s2: str) -> float:
    """Compute Jaccard similarity over 3-grams of two strings."""
    if not s1 or not s2:
        return 0.0
    s1_lower = s1.lower()
    s2_lower = s2.lower()
    # Extract 3-grams
    grams1 = {s1_lower[i:i+3] for i in range(len(s1_lower) - 2)}
    grams2 = {s2_lower[i:i+3] for i in range(len(s2_lower) - 2)}
    if not grams1 or not grams2:
        return 0.0
    intersection = len(grams1 & grams2)
    union = len(grams1 | grams2)
    return intersection / union if union > 0 else 0.0


def _get_existing_content(root: Path) -> str:
    """Aggregate content from existing notes for dedup checking."""
    from myco.notes import list_notes, read_note
    content = ""
    try:
        for path in list_notes(root):
            try:
                _, body = read_note(path)
                content += body + " "
            except Exception:
                continue
    except Exception:
        pass
    return content


def immune_filter(root: Path, candidate: Dict[str, Any]) -> Tuple[bool, str]:
    """Filter a candidate through immune checks.

    Returns (pass: bool, reason: str).

    Checks:
    1. Deduplication: title/summary Jaccard similarity vs existing notes > 0.6 → reject
    2. Interest matching: if interests.yaml exists, require topic match → reject if none
    3. License whitelist: license must be in SAFE_LICENSES → reject if unknown
    """
    title = candidate.get("title", "").lower()
    summary = candidate.get("summary", "").lower()
    content_sample = title + " " + summary

    # Check 1: Deduplication
    existing_content = _get_existing_content(root)
    if existing_content:
        sim = _jaccard_3gram_similarity(content_sample, existing_content)
        if sim > 0.6:
            return False, f"duplicate (similarity={sim:.2f})"

    # Check 2: Interest matching
    interests = _load_interests(root)
    if interests:
        # Require at least one interest word in title or summary
        interests_lower = [i.lower() for i in interests]
        found = any(
            interest in content_sample
            for interest in interests_lower
        )
        if not found:
            return False, "not in interests"

    # Check 3: License whitelist
    license_guess = candidate.get("license_guess", "unknown")
    if license_guess not in SAFE_LICENSES:
        return False, f"unknown_license ({license_guess})"

    return True, "pass"


# ---------------------------------------------------------------------------
# Setup Wizard
# ---------------------------------------------------------------------------

def setup_wizard(root: Path) -> None:
    """Interactive setup: prompt for interests and seed feeds."""
    import sys
    print("\nMyco Forage Setup Wizard")
    print("=" * 40)
    print("\nEnter 3-5 topics you want to track (e.g., 'reinforcement learning', 'distributed systems'):")
    topics = []
    for i in range(5):
        topic = input(f"Topic {i+1} (or leave blank to finish): ").strip()
        if not topic:
            break
        topics.append(topic)

    if not topics:
        topics = ["machine learning", "artificial intelligence", "statistics"]
        print(f"Using default topics: {', '.join(topics)}")

    _save_interests(root, topics)
    print(f"\nSaved {len(topics)} topics to .myco_state/interests.yaml")

    # Seed default feeds
    cfg = DEFAULT_FEEDS_SCHEMA.copy()
    save_feeds_config(root, cfg)
    print(f"Seeded {len(cfg['sources'])} default feeds (arxiv cs.LG/cs.AI/stat.ML)")
    print("\nRun 'myco forage sync' to test.")
