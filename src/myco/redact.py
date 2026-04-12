"""
Myco Secret Redaction — absorbed from hermes-agent redact.py patterns.

Wave C2: Detects potential secrets in text (API keys, tokens, passwords).
Used by evolve.py constraint gates to prevent secret leaks in skill mutations.
"""

from __future__ import annotations

import re

# Patterns absorbed from hermes-agent-self-evolution agent/redact.py
# Each pattern matches a common secret format.
_SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|apikey)\s*[:=]\s*\S{8,}"),
    re.compile(r"(?i)(secret|password|passwd|pwd)\s*[:=]\s*\S{6,}"),
    re.compile(r"(?i)(token|access_token|auth_token)\s*[:=]\s*\S{8,}"),
    re.compile(r"(?i)(bearer)\s+[A-Za-z0-9\-._~+/]+=*"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),           # OpenAI API keys
    re.compile(r"sk-ant-[A-Za-z0-9\-]{20,}"),      # Anthropic API keys
    re.compile(r"ghp_[A-Za-z0-9]{36,}"),            # GitHub PAT
    re.compile(r"gho_[A-Za-z0-9]{36,}"),            # GitHub OAuth
    re.compile(r"glpat-[A-Za-z0-9\-]{20,}"),        # GitLab PAT
    re.compile(r"xox[bpsar]-[A-Za-z0-9\-]{10,}"),   # Slack tokens
    re.compile(r"AKIA[0-9A-Z]{16}"),                # AWS access key
    re.compile(r"(?i)private[_-]?key\s*[:=]"),
    re.compile(r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----"),
    re.compile(r"(?i)(database_url|db_url|connection_string)\s*[:=]\s*\S{10,}"),
]


def contains_secret(text: str) -> bool:
    """Return True if text likely contains a secret."""
    for pattern in _SECRET_PATTERNS:
        if pattern.search(text):
            return True
    return False


def redact_secrets(text: str, replacement: str = "[REDACTED]") -> str:
    """Replace detected secrets with replacement string."""
    result = text
    for pattern in _SECRET_PATTERNS:
        result = pattern.sub(replacement, result)
    return result
