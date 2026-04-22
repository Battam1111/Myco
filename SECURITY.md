# Security Policy

Myco is a cognitive substrate that agents read + write on behalf of
a human operator. That makes three attack surfaces load-bearing:

1. **Ingestion** (`myco eat --path`, `--url`): content an agent
   points at is absorbed into the substrate's raw notes. Hostile
   content could try to plant prompt-injection strings,
   credential-bearing files, or pathological inputs.
2. **Canon + write-surface**: every agent-writable path is declared
   in `_canon.yaml::system.write_surface.allowed`. A kernel that
   bypasses this declaration is a silent trust boundary break.
3. **Extensibility seams**: `.myco/plugins/` (per-substrate) and
   `src/myco/symbionts/` (per-host) are load-import points. A
   hostile plugin could smuggle in capabilities the kernel's
   doctrine forbids.

This policy describes how Myco defends each and how to report
regressions.

## Supported versions

Myco is on rapid 0.5.x cadence. Only the latest minor receives
security fixes. Older minors get advisory notes in the changelog.

| Version | Supported |
|---------|-----------|
| 0.5.x (latest) | ✅ |
| 0.4.x | ⚠️ advisory only |
| ≤ 0.3.x | ❌ (pre-rewrite, frozen) |

## What Myco defends against mechanically

Landed in v0.5.8 + v0.5.9 + v0.5.10. All enforced without
human-in-loop in the happy path:

- **Write-surface discipline (R6)**: eight substrate-mutating verbs
  (`eat`, `sporulate`, `digest`, `assimilate`, `fruit`, `ramify`,
  `molt`, `boot_brief`) call `check_write_allowed` before any
  write; paths outside the declared surface raise
  `WriteSurfaceViolation` (exit 3). Override via
  `MYCO_ALLOW_UNSAFE_WRITE=1` is explicit + auditable.
- **Credential-file denylist**: `.env*`, `id_rsa*`, `*.pem`,
  `*.key`, `.npmrc`, `.netrc`, `.pypirc`, `credentials*`,
  `secrets*`, `*.p12`, `*.pfx` are refused by the text adapter
  regardless of extension.
- **Adapter size caps**: 10 MB cap on every ingestion adapter
  (`text_file`, `pdf_reader`, `html_reader`, `tabular`,
  `url_fetcher`). A malicious 5 GB file cannot OOM the process.
- **SSRF guard in `url_fetcher`**: scheme allowlist (http/https
  only; no `file://`, `gopher://`, `data:`); hostname DNS-resolved
  and rejected if it maps to loopback / link-local / private /
  multicast / reserved IPs. Redirect targets re-validated at
  every hop.
- **HTTP response byte-cap**: streaming fetch aborts at 10 MB,
  even if `Content-Length` was missing / lied. No single URL
  response can exceed the cap.
- **YAML-injection safety**: `eat._render_note` uses
  `yaml.safe_dump`; every substrate-derived scalar (tags, source)
  passes `trust.safe_frontmatter_field` first (strips control
  chars, flattens newlines).
- **MCP pulse sanitisation**: `substrate_id` and
  `contract_version` flow through `safe_frontmatter_field` before
  entering any agent's context (strips ANSI escapes, caps length).
- **Atomic writes**: every kernel write uses
  `atomic_utf8_write` (temp file + `os.fsync` + `os.replace`).
  Concurrent readers never see a torn file; crash-between-write
  can't leave a half-written canon.
- **Bounded reads**: every substrate read (canon / notes / graph
  / plugin source) routes through `bounded_read_text` (10 MB
  default cap). Oversized reads raise `MycoError` pre-read.
- **TOCTOU-safe note creation**: `eat.append_note` uses
  `os.open(..., O_WRONLY | O_CREAT | O_EXCL)` in a collision-retry
  loop. Concurrent `eat` calls with identical timestamps cannot
  overwrite each other.
- **Windows reserved-name guard**: `germinate` rejects
  `substrate_id` / `entry_point` names that match Windows reserved
  device names (`CON` / `PRN` / `AUX` / `NUL` / `COM1-9` /
  `LPT1-9`). Writing to these paths silently black-holes content
  on Windows; pre-v0.5.8 this was a silent loss path.
- **MP1 + MP2 LLM-boundary enforcement**: mechanical lint refuses
  kernel (MP1) and plugin (MP2) imports of 31 known LLM provider
  SDKs. Opt-out requires `canon.system.no_llm_in_substrate: false`
  + a contract-bumping `molt` (governance visible).

## What Myco does NOT defend against

Explicit non-goals — documented so integrators don't rely on
Myco for checks it doesn't perform:

- **Arbitrary code execution inside plugins**: if a substrate
  author installs a `.myco/plugins/` module, that module runs
  with the kernel's full privileges. MF2 checks shape, not
  semantics; MP2 checks provider imports, not arbitrary
  behaviour. Vet your plugins.
- **Cross-substrate trust**: `propagate` writes into a downstream
  substrate's `notes/raw/`. It does not verify the downstream
  substrate's authenticity; if you push to a malicious dst, you
  leak the pushed notes. Validate destinations.
- **Secret redaction at ingest**: the credential-file denylist
  stops obvious cases (`.env`, `id_rsa`), but a hostile string
  containing `OPENAI_API_KEY=sk-...` inside a regular Markdown
  file IS absorbed verbatim. Use pre-commit hooks / secret
  scanners upstream of `myco eat`.
- **Full sandboxing of agent-driven writes**: R6 prevents writes
  outside the declared surface; it does not prevent the agent
  from deleting or corrupting content inside the surface.
  Version-control your substrate (git) as the last line of
  defence.

## Reporting a vulnerability

**Preferred**: open a [GitHub Security Advisory](https://github.com/Battam1111/Myco/security/advisories/new)
(the Security tab's "Report a vulnerability" button). This keeps
the report private until a fix ships.

**Fallback** (if you can't use the advisory flow): email the
maintainer address listed in the repo's `pyproject.toml`
`[project].authors` block.

**Do NOT** open a public issue for a vulnerability. A public
issue before a fix ships lets every substrate-on-network be
exploited before upgrade is possible.

## Response expectations

- **Acknowledgement**: within 7 days.
- **Triage verdict** (accept / decline / need-more-info): within
  14 days.
- **Fix release cadence**:
  - Critical (active exploitation, kernel-write bypass,
    substrate-wipe vector) → patch release within 7 days of
    triage.
  - High (data-leak, DoS, boundary violation) → patch release
    in the next minor (≤ 21 days).
  - Medium / low → next minor release on normal cadence.

## Credit

Every disclosed + fixed vulnerability is credited by name (or
pseudonym of the reporter's choice) in `docs/contract_changelog.md`
for the version that lands the fix, and in the corresponding
GitHub Security Advisory. If the reporter prefers anonymity,
we respect that.

## Governance trail

- Every security-related doctrine change passes through the
  same `fruit` (3-round craft) + `molt` (contract bump) loop as
  any other contract edit. No silent tightening of the security
  boundary.
- `docs/primordia/v0_5_8_discipline_enforcement_craft_2026-04-21.md`
  documented the R6 mechanical-enforcement landing + the
  credential/SSRF/size-cap hardening. Future security crafts
  live under `docs/primordia/` with the same shape.
