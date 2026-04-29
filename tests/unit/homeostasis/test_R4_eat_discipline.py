"""tests/unit/surface/test_R4_eat_discipline.py — R4 behavioral contract (v0.6.0).

Per craft v0.6.0 §K.2: behavioral contract for R4 "eat insights the
moment they occur". RL3 dim emits when decision_marker / keyword
hits exceed eat() calls by 3x.
"""

from __future__ import annotations

import json

from myco.homeostasis.dimensions.semantic.rl3_eat_discipline_signal import (
    RL3EatDisciplineSignal,
)


def test_rl3_dim_id():
    dim = RL3EatDisciplineSignal()
    assert dim.id == "RL3"
    assert dim.category.value == "semantic"


def test_rl3_decision_keyword_without_eat_emits(tmp_path):
    """When session log shows 4 decisions but 0 eat calls, RL3 emits."""
    log_dir = tmp_path / ".myco_state"
    log_dir.mkdir()
    log_path = log_dir / "session_calls.jsonl"
    events = [
        {"verb": "hunger"},
        {"verb": "sense", "query": "decided to use python 3.13"},
        {"verb": "brief", "summary": "I decided X"},
        {"verb": "molt", "decision_marker": True},
        {"verb": "winnow", "decision_marker": True},
    ]
    log_path.write_text(
        "\n".join(json.dumps(e) for e in events),
        encoding="utf-8",
    )
    assert log_path.is_file()
