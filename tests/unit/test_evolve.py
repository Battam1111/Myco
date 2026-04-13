"""Unit tests for myco.evolve — skill evolution (Wave C1-C3)."""

from pathlib import Path
import pytest


@pytest.fixture
def skill_file(tmp_path):
    """Create a test skill file."""
    content = (
        "---\n"
        "name: test-skill\n"
        "description: A test skill\n"
        "---\n\n"
        "## Steps\n"
        "1. Do thing A\n"
        "2. Do thing B\n"
        "3. Verify result\n"
    )
    path = tmp_path / "test-skill.md"
    path.write_text(content)
    return path


def test_parse_skill(skill_file):
    """parse_skill extracts frontmatter and body."""
    from myco.evolve import parse_skill
    v = parse_skill(skill_file)
    assert v.meta["name"] == "test-skill"
    assert "Do thing A" in v.body


def test_serialize_roundtrip(skill_file):
    """parse → serialize → parse preserves content."""
    from myco.evolve import parse_skill, serialize_skill
    v1 = parse_skill(skill_file)
    text = serialize_skill(v1)
    # Write back and re-parse
    skill_file.write_text(text)
    v2 = parse_skill(skill_file)
    assert v1.meta == v2.meta
    assert v1.body.strip() == v2.body.strip()


def test_gate_frontmatter_preserved():
    """Gate rejects when frontmatter changes."""
    from myco.evolve import SkillVariant, gate_frontmatter_preserved
    old = SkillVariant(meta={"name": "a"}, body="test")
    new_ok = SkillVariant(meta={"name": "a"}, body="changed")
    new_bad = SkillVariant(meta={"name": "b"}, body="test")
    assert gate_frontmatter_preserved(old, new_ok) is None
    assert gate_frontmatter_preserved(old, new_bad) is not None


def test_gate_no_secret_leak():
    """Gate rejects when body contains secrets."""
    from myco.evolve import SkillVariant, gate_no_secret_leak
    clean = SkillVariant(meta={}, body="normal instructions")
    dirty = SkillVariant(meta={}, body="api_key: sk-abc123456789012345678901")
    assert gate_no_secret_leak(clean) is None
    assert gate_no_secret_leak(dirty) is not None


def test_check_gates_all_pass(skill_file):
    """All gates pass for a valid mutation."""
    from myco.evolve import parse_skill, SkillVariant, check_gates
    old = parse_skill(skill_file)
    new = SkillVariant(meta=dict(old.meta), body=old.body + "\n4. Extra step")
    failures = check_gates(old, new)
    assert failures == []


