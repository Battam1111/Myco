"""Small shared utilities for Myco. Avoid growing this file into a grab-bag —
only put things here that are genuinely needed in 3+ places.
"""
from __future__ import annotations
from datetime import datetime


def get_date() -> str:
    """Return today's date as ISO-8601 (YYYY-MM-DD)."""
    return datetime.now().strftime("%Y-%m-%d")
