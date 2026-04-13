# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.2.x   | ✅ Active support |
| < 0.2   | ❌ No longer supported |

## Scope

Myco is a local CLI tool and Python library that operates entirely on your filesystem. It does not:
- Make network requests (except `myco migrate` which may call external services if you configure it)
- Store credentials or personal data
- Run code from user-supplied inputs
- Expose network endpoints

## Reporting a Vulnerability

**Do not** open a public GitHub issue for security vulnerabilities.

Instead, please open a [private GitHub Security Advisory](https://github.com/Battam1111/Myco/security/advisories/new) via the Security tab.

Please include:
- Description of the vulnerability
- Steps to reproduce
- Impact assessment
- Any suggested mitigation

You will receive an acknowledgment within 48 hours. We aim to release a patch within 14 days for confirmed vulnerabilities.

## Security Considerations for Users

Since Myco manages knowledge files that are read by AI agents:

1. **Review wiki/ contents before making a project public** — wiki pages may contain business logic, credentials references, or internal details.
2. **_canon.yaml is not a secrets manager** — do not store API keys or passwords there.
3. **MYCO.md hot-zone is agent-readable** — treat it like a public system prompt.
4. **docs/primordia/ craft debates** may contain strategic thinking you want to keep private.

## Responsible Disclosure

We follow a 90-day disclosure timeline. Once a fix is released, we will publish a CVE (if applicable) and credit the reporter.
