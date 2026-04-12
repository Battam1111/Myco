"""Unit tests for myco.templates — template loading."""

import pytest


def test_fill_template_replaces_placeholders():
    """fill_template substitutes {{VAR}} with provided values."""
    from myco.templates import fill_template
    template = "Hello {{NAME}}, welcome to {{PROJECT}}."
    result = fill_template(template, {"NAME": "Agent", "PROJECT": "Myco"})
    assert result == "Hello Agent, welcome to Myco."


def test_fill_template_leaves_unknown_placeholders():
    """Unknown placeholders are left as-is."""
    from myco.templates import fill_template
    template = "{{KNOWN}} and {{UNKNOWN}}"
    result = fill_template(template, {"KNOWN": "yes"})
    assert "yes" in result
    assert "{{UNKNOWN}}" in result


def test_get_template_canon():
    """_canon.yaml template loads without error."""
    from myco.templates import get_template
    content = get_template("_canon.yaml")
    assert "system:" in content
    assert "synced_contract_version" in content
