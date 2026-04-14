"""Unit tests for hunger signal pipeline — covering Wave 46-59 additions."""

from pathlib import Path

import pytest
import yaml


@pytest.fixture
def signal_project(tmp_path):
    """Create a project for testing hunger signals."""
    (tmp_path / "_canon.yaml").write_text(
        "system:\n"
        "  contract_version: 'v0.43.0'\n"
        "  entry_point: MYCO.md\n"
        "  notes_schema:\n"
        "    dir: notes\n"
        "    terminal_statuses: [extracted, integrated]\n"
        "    dead_knowledge_threshold_days: 30\n"
        "    compression:\n"
        "      ripe_threshold: 5\n"
        "      ripe_age_days: 7\n"
        "      pressure_threshold: 2.0\n"
        "      gap_stale_days: 14\n"
        "  boot_reflex:\n"
        "    enabled: true\n"
        "    severity: HIGH\n"
        "    raw_backlog_threshold: 10\n"
        "    reflex_prefix: '[REFLEX HIGH]'\n"
        "    raw_exempt_sources: [bootstrap]\n"
        "    grandfather_ceiling_minor_versions: 5\n"
        "  inlet_triggers:\n"
        "    enabled: true\n"
        "    search_miss_threshold: 5\n"
        "    gap_threshold: 3\n"
        "    miss_state_file: '.myco_state/search_misses.yaml'\n",
        encoding="utf-8",
    )
    (tmp_path / "MYCO.md").write_text("# Myco\n")
    (tmp_path / "notes").mkdir()
    (tmp_path / ".myco_state").mkdir()
    (tmp_path / "log.md").write_text("# Log\n")
    return tmp_path


def _write_note(notes_dir, note_id, status, tags=None, created="2026-04-01"):
    content = (
        f"---\nid: {note_id}\nstatus: {status}\nsource: eat\n"
        f"tags: [{', '.join(tags or ['test'])}]\ncreated: {created}\n"
        f"last_touched: {created}\ndigest_count: 0\n"
        f"promote_candidate: false\nexcrete_reason: null\n---\n\nTest.\n"
    )
    (notes_dir / f"{note_id}.md").write_text(content)


def test_hunger_no_crash_on_empty_project(signal_project):
    """Empty project produces a hunger report without crashing."""
    from myco.notes import compute_hunger_report
    report = compute_hunger_report(signal_project)
    assert report.total == 0
    assert isinstance(report.signals, list)
    assert isinstance(report.actions, list)


def test_hunger_raw_backlog_signal(signal_project):
    """Exceeding raw backlog threshold produces REFLEX HIGH signal."""
    from myco.notes import compute_hunger_report
    notes = signal_project / "notes"
    for i in range(12):  # > threshold of 10
        _write_note(notes, f"n_20260401T00000{i:01d}_000{i:01d}", "raw",
                    created="2026-04-01")
    report = compute_hunger_report(signal_project)
    has_backlog = any("raw_backlog" in s for s in report.signals)
    assert has_backlog


def test_hunger_graph_orphans_signal(signal_project):
    """Graph orphans signal fires when orphan count > 10."""
    from myco.notes import compute_hunger_report
    # Create 15 unlinked doc files
    docs_dir = signal_project / "docs"
    docs_dir.mkdir()
    for i in range(15):
        (docs_dir / f"orphan_{i}.md").write_text(f"# Orphan {i}\n")
    report = compute_hunger_report(signal_project)
    has_orphan = any("graph_orphans" in s for s in report.signals)
    assert has_orphan


def test_hunger_cohort_staleness_signal(signal_project):
    """Cohort staleness fires for tags with only raw notes."""
    from myco.notes import compute_hunger_report
    notes = signal_project / "notes"
    for i in range(4):
        _write_note(notes, f"n_20260401T00000{i}_000{i}", "raw",
                    tags=["stale-topic"], created="2026-03-01")
    report = compute_hunger_report(signal_project)
    has_staleness = any("cohort_staleness" in s for s in report.signals)
    assert has_staleness


# ---------------------------------------------------------------------------
# no_excretion signal + lifetime excretion counter
# ---------------------------------------------------------------------------

def test_no_excretion_fires_when_no_excretions_ever(signal_project):
    """no_excretion signal fires when >=20 notes and zero lifetime excretions."""
    from myco.notes import compute_hunger_report
    notes = signal_project / "notes"
    for i in range(25):
        _write_note(notes, f"n_20260401T0000{i:02d}_{i:04x}", "raw")
    report = compute_hunger_report(signal_project)
    has_no_excretion = any("no_excretion" in s for s in report.signals)
    assert has_no_excretion


def test_no_excretion_suppressed_by_lifetime_counter(signal_project):
    """no_excretion signal does NOT fire when lifetime counter > 0,
    even if zero excreted notes exist on disk."""
    from myco.notes import compute_hunger_report, increment_excretion_counter
    notes = signal_project / "notes"
    # 25 raw notes, zero excreted on disk
    for i in range(25):
        _write_note(notes, f"n_20260401T0000{i:02d}_{i:04x}", "raw")
    # Record that excretions happened in the past (notes since deleted)
    increment_excretion_counter(signal_project, count=3)
    report = compute_hunger_report(signal_project)
    has_no_excretion = any("no_excretion" in s for s in report.signals)
    assert not has_no_excretion, (
        "no_excretion signal should be suppressed when lifetime_excretions > 0"
    )


def test_no_excretion_suppressed_by_on_disk_excreted(signal_project):
    """no_excretion signal does NOT fire when excreted notes exist on disk."""
    from myco.notes import compute_hunger_report
    notes = signal_project / "notes"
    for i in range(24):
        _write_note(notes, f"n_20260401T0000{i:02d}_{i:04x}", "raw")
    # One excreted note on disk
    eid = "n_20260401T000099_00ff"
    content = (
        f"---\nid: {eid}\nstatus: excreted\nsource: eat\n"
        f"tags: [test]\ncreated: 2026-04-01\nlast_touched: 2026-04-01\n"
        f"digest_count: 0\npromote_candidate: false\n"
        f"excrete_reason: test excretion\n---\n\nExcreted.\n"
    )
    (notes / f"{eid}.md").write_text(content)
    report = compute_hunger_report(signal_project)
    has_no_excretion = any("no_excretion" in s for s in report.signals)
    assert not has_no_excretion


def test_excretion_counter_read_write(signal_project):
    """read/increment_excretion_counter round-trips correctly."""
    from myco.notes import read_excretion_counter, increment_excretion_counter
    # Initially zero
    state = read_excretion_counter(signal_project)
    assert state["lifetime_excretions"] == 0
    assert state["last_excretion"] is None
    # Increment by 1
    state = increment_excretion_counter(signal_project)
    assert state["lifetime_excretions"] == 1
    assert state["last_excretion"] is not None
    # Increment by 5
    state = increment_excretion_counter(signal_project, count=5)
    assert state["lifetime_excretions"] == 6
    # Persists on re-read
    state = read_excretion_counter(signal_project)
    assert state["lifetime_excretions"] == 6


def test_update_note_increments_excretion_counter(signal_project):
    """update_note auto-increments excretion counter on status -> excreted."""
    from myco.notes import update_note, read_excretion_counter
    notes = signal_project / "notes"
    nid = "n_20260401T000000_0000"
    _write_note(notes, nid, "raw")
    note_path = notes / f"{nid}.md"
    update_note(note_path, status="excreted", excrete_reason="test")
    state = read_excretion_counter(signal_project)
    assert state["lifetime_excretions"] == 1


# ---------------------------------------------------------------------------
# skill_degradation signal
# ---------------------------------------------------------------------------

def _add_evolution_config(canon_path, enabled=True, stale_days=7):
    """Patch _canon.yaml to include evolution config."""
    import yaml as _yaml
    canon = _yaml.safe_load(canon_path.read_text(encoding="utf-8")) or {}
    canon.setdefault("system", {})["evolution"] = {
        "enabled": enabled,
        "stale_active_threshold_days": stale_days,
    }
    canon_path.write_text(_yaml.dump(canon, default_flow_style=False),
                          encoding="utf-8")


def test_skill_degradation_fires_for_unevolved_old_skill(signal_project):
    """skill_degradation fires when a skill is old and never evolved."""
    import os
    import time
    from datetime import datetime, timedelta
    from myco.notes import detect_skill_degradation

    _add_evolution_config(signal_project / "_canon.yaml", enabled=True,
                          stale_days=7)

    skills = signal_project / "skills"
    skills.mkdir()
    skill_file = skills / "test-skill.md"
    skill_file.write_text("# Test Skill\n\nDoes things.\n")
    # Backdate the file mtime by 10 days.
    old_time = time.time() - (10 * 86400)
    os.utime(str(skill_file), (old_time, old_time))

    sigs = detect_skill_degradation(signal_project)
    assert len(sigs) == 1
    assert "skill_degradation" in sigs[0]
    assert "test-skill.md" in sigs[0]
    assert "myco_evolve" in sigs[0]


def test_skill_degradation_silent_when_evolved(signal_project):
    """skill_degradation does NOT fire for skills with evolved variants."""
    import os
    import time
    from myco.notes import detect_skill_degradation

    _add_evolution_config(signal_project / "_canon.yaml", enabled=True,
                          stale_days=7)

    skills = signal_project / "skills"
    skills.mkdir()
    skill_file = skills / "my-skill.md"
    skill_file.write_text("# My Skill\n")
    old_time = time.time() - (10 * 86400)
    os.utime(str(skill_file), (old_time, old_time))

    # Create an evolved variant.
    evolved = skills / ".evolved"
    evolved.mkdir()
    (evolved / "my-skill_gen1_abc123.md").write_text("# Evolved\n")

    sigs = detect_skill_degradation(signal_project)
    assert len(sigs) == 0


def test_skill_degradation_silent_when_young(signal_project):
    """skill_degradation does NOT fire for skills younger than threshold."""
    from myco.notes import detect_skill_degradation

    _add_evolution_config(signal_project / "_canon.yaml", enabled=True,
                          stale_days=7)

    skills = signal_project / "skills"
    skills.mkdir()
    # File created just now — mtime is today, age < 7 days.
    (skills / "new-skill.md").write_text("# Fresh\n")

    sigs = detect_skill_degradation(signal_project)
    assert len(sigs) == 0


def test_skill_degradation_silent_when_evolution_disabled(signal_project):
    """skill_degradation does NOT fire when evolution is disabled."""
    import os
    import time
    from myco.notes import detect_skill_degradation

    _add_evolution_config(signal_project / "_canon.yaml", enabled=False,
                          stale_days=7)

    skills = signal_project / "skills"
    skills.mkdir()
    skill_file = skills / "stale-skill.md"
    skill_file.write_text("# Stale\n")
    old_time = time.time() - (20 * 86400)
    os.utime(str(skill_file), (old_time, old_time))

    sigs = detect_skill_degradation(signal_project)
    assert len(sigs) == 0


def test_skill_degradation_wired_into_hunger_report(signal_project):
    """skill_degradation signals appear in compute_hunger_report and
    produce corresponding evolve actions."""
    import os
    import time
    from myco.notes import compute_hunger_report

    _add_evolution_config(signal_project / "_canon.yaml", enabled=True,
                          stale_days=7)

    skills = signal_project / "skills"
    skills.mkdir()
    skill_file = skills / "rusty-skill.md"
    skill_file.write_text("# Rusty\n")
    old_time = time.time() - (15 * 86400)
    os.utime(str(skill_file), (old_time, old_time))

    report = compute_hunger_report(signal_project)
    has_degradation = any("skill_degradation" in s for s in report.signals)
    assert has_degradation

    evolve_actions = [a for a in report.actions if a["verb"] == "evolve"]
    assert len(evolve_actions) == 1
    assert evolve_actions[0]["args"]["skill"] == "rusty-skill.md"
