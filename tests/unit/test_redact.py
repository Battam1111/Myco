"""Unit tests for myco.redact — secret detection (Wave C2)."""


def test_contains_secret_api_key():
    from myco.redact import contains_secret
    assert contains_secret("api_key: sk-abc123456789012345678901")
    assert contains_secret("password: supersecret123")
    assert not contains_secret("This is normal text about APIs")


def test_contains_secret_github_pat():
    from myco.redact import contains_secret
    assert contains_secret("ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij")
    assert not contains_secret("github.com/user/repo")


def test_redact_replaces():
    from myco.redact import redact_secrets
    text = "Use api_key: sk-abc123456789012345678901 to authenticate"
    result = redact_secrets(text)
    assert "[REDACTED]" in result
    assert "sk-abc" not in result


def test_clean_text_unchanged():
    from myco.redact import redact_secrets
    text = "Normal instructions for the skill"
    assert redact_secrets(text) == text
