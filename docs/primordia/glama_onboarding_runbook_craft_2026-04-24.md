---
type: craft
topic: Glama onboarding runbook
slug: glama_onboarding_runbook
kind: operational
date: 2026-04-24
rounds: 3
craft_protocol_version: 1
status: LANDED
---

# Glama Onboarding Runbook — Craft

> **Date**: 2026-04-24
> **Layer**: L3 (implementation-facing operational procedure) with L0 doctrinal bearing on "Only For Agent" / "Eternal Evolution".
> **Upward**: L1 contract §R6 (write-surface covers `glama.json`); L2 `extensibility.md` §per-host axis (Glama as a discovery + scoring host).
> **Governs**: `glama.json` at repo root, README Glama badge, `docs/primordia/glama_onboarding_runbook_craft_2026-04-24.md` (self).

This craft is the **operational runbook** for getting Myco (or any
substrate descendant) onto Glama's MCP server registry with a clean
A-level quality score. It is "landed-before-written" — the real
onboarding happened on 2026-04-23/24; this document reconstructs the
three-round debate that *would* have saved six iterations if the
maintainer had read it first.

Cross-ref substrate note: [notes/integrated/n_20260424T070557Z_glama-mcp-registry-onboarding-runbook-20.md](../../notes/integrated/n_20260424T070557Z_glama-mcp-registry-onboarding-runbook-20.md)

---

## Round 1 — 主张 (claim)

**Claim (C):** An MCP server's Glama onboarding is a **four-step mechanical
sequence** whose happy path is:

1. **Badge in README first.** Embed `![Glama score](https://glama.ai/mcp/servers/<owner>/<repo>/badges/score.svg)` even *before* the listing exists. Placeholder SVG (HTTP 404 with `content-type: image/svg+xml`) serves until a scored listing replaces it; same URL, auto-updates.
2. **Submit via the authenticated "Add MCP Server" button on `/mcp/servers`.** NOT `/submit`, NOT `/add`, NOT `/mcp/servers/submit` — all of those redirect to SPA search queries. The button is client-rendered and only visible after GitHub OAuth login.
3. **Claim via glama.json (two-field minimum)** OR let personal-account GitHub OAuth auto-associate. Commit `{"$schema": "https://glama.ai/mcp/schemas/server.json", "maintainers": ["<github-username>"]}` for explicit in-repo ownership of record.
4. **Pass the build-and-scan via Admin panel.** Provide Build steps that install the MCP server into the generated scan container; accept Glama's default CMD (`["mcp-proxy", "--", "<executable>"]`). The scan passes when `mcp-proxy` can spawn the MCP server on stdio and the server responds to `initialize` + `list_tools`.

**Load-bearing claim this stands on:** once those four steps complete, the
`has-glama` label on `punkpeye/awesome-mcp-servers` PRs auto-applies via
the Check Glama Link workflow, merging becomes the maintainer's routine
review-queue action, and downstream discovery (Glama's 22k+ server
search) treats the server as first-class.

## Round 1.5 — 自我反驳 (self-rebuttal)

- **T1 — "Glama auto-scrapes; explicit submission is redundant."** The MCP Registry already holds `io.github.Battam1111/myco`; why should I have to separately sign up to Glama? Many server-authors never see their repo on Glama at all without action.
- **T2 — "glama.json looks like a metadata file but Glama ignores almost every field you'd add."** If the file's only job is `maintainers`, why call it `glama.json` at all? Why not a workflow-level claim the same way DockerHub / npm does?
- **T3 — "Glama's Dockerfile generator makes our repo's own Dockerfile pointless."** The v0.5.13 Dockerfile we shipped (with `io.modelcontextprotocol.server.name` label) does not participate in Glama's scan at all. Glama builds a different `debian:bookworm-slim` + uv + mcp-proxy image. So what was our Dockerfile for?
- **T4 — "Default Build step `['uv sync']` is hostile to non-uv repos."** Glama's panel assumes `uv sync` works, which requires `uv.lock`. Most Python MCP servers (including ours, using hatchling) have no `uv.lock`. First scan fails with non-obvious error. Bad default.
- **T5 — "PEP 668 externally-managed fix (`--break-system-packages`) feels like a hack."** Normally you'd install into a venv. Using `--break-system-packages` in production documentation looks bad; a new agent reading this runbook might generalize the pattern to their own system Python and regret it.
- **T6 — "Glama's categorization is a black box with no escape hatch in file form."** It auto-tagged Myco as "Knowledge & Memory" — directly contradicting Myco's L0 principle 1 ("cognitive substrate, not memory tool"). Every MCP server whose positioning diverges from the automated classifier's heuristics will have the same problem; no `glama.json` field covers category override.

## Round 2 — 修正 (revision)

- **R1 (addresses T1).** **Tension survives.** The MCP Registry and Glama
  are distinct systems with independent scope. MCP Registry is a
  package-identifier namespace (tells clients how to install). Glama is
  a scoring + discovery + OCI-build-scanning registry (tells humans
  which server to pick). The duplication is real and annoying, but
  justified by the different SLA: MCP Registry inherits trust from
  GitHub OIDC; Glama actively runs code in a container and assigns
  quality grades. They are not interchangeable. **Revision:** accept the
  duplication; document both submission surfaces in parallel.

- **R2 (addresses T2).** The minimal-`glama.json` design is deliberate.
  Glama's blog explicitly states: *"a very simple glama.json file will
  contain just two properties: $schema and maintainers."* The file is
  an ownership marker + refresh trigger, nothing more. Categorization,
  description, icon — all live on the Glama dashboard because they need
  cross-server moderation. **Revision:** land `glama.json` at repo root
  with exactly two fields; reject the temptation to add `categories` /
  `description` / `tags` (they are silently dropped). Document the
  dashboard-only path for metadata override.

- **R3 (addresses T3).** Our repo's Dockerfile serves a different host:
  **MCP clients that resolve OCI-registryType packages** (Glama is OCI-
  aware but builds its own; other registries + clients consume
  pre-built images). The v0.5.13 Dockerfile's
  `io.modelcontextprotocol.server.name` label is the namespace-
  verification marker for those clients. It is NOT waste; it is
  orthogonal. **Revision:** accept two Dockerfiles (ours for OCI
  namespace verification, Glama's for its own scan) without trying to
  unify.

- **R4 (addresses T4).** The `uv sync` default is a pytest-style
  "convention over configuration" bet — it optimizes for uv-native
  repos (which Glama expects to be the dominant Python MCP server
  shape going forward). For non-uv repos like ours, the correct
  override is
  `["uv pip install --system --break-system-packages 'myco[mcp]'"]`.
  **Revision:** document the override as the canonical Build step for
  hatchling / setuptools MCP servers. Add a check to future
  ramify-generated `pyproject.toml` templates: if Glama onboarding is
  wanted, either add a `uv.lock` OR plan for the pip override.

- **R5 (addresses T5).** **Tension survives (in a principled way).** The
  `--break-system-packages` flag is not inherently bad; it is bad only
  when used on a user's *own* Debian system. Inside an ephemeral
  throwaway container spun up once by Glama's scanner and destroyed
  after the grade is recorded, the flag is the *documented* escape
  hatch per pip + uv docs. The generalizability worry is real — we must
  flag this as a Docker-only pattern in this runbook and link to the
  upstream rationale. **Revision:** accept the flag with a scoped
  warning: never use outside `debian:*-slim` or equivalent minimal
  images running as root in ephemeral CI / scan containers.

- **R6 (addresses T6).** **Tension survives.** Glama's category
  classifier is a black box and the dashboard-only override is the only
  escape. Myco was auto-tagged `knowledge-and-memory` + `agent-
  orchestration` — the first is factually wrong per our L0 principle 1.
  There is no file-based fix. **Revision:** add a scheduled
  follow-up (post-PR-merge) to visit the Glama dashboard and flip the
  category to `agent-orchestration` + `developer-tools`. Record the
  override in this craft so the next release's onboarding doesn't
  silently regress.

## Round 2.5 — 再驳 (counter-rebuttal)

Second-order tensions surfaced by the revisions:

- **T7 (new, from R4):** The `--break-system-packages` override is
  session-specific — if Glama ever changes the default base image
  from `debian:bookworm-slim` to something without PEP 668, the flag
  becomes redundant but harmless. Future-proof?
- **T8 (new, from R5):** The runbook is written as an imperative "do
  these steps" — but the steps are guarded by Glama's own evolving UI.
  If punkpeye rewrites the dashboard tomorrow, the `/mcp/servers` →
  "Add MCP Server" wording dies. How stable is this surface?

Responses:

- **T7 response.** Harmless-redundant is fine. The flag costs nothing
  when the system Python isn't externally-managed (uv silently
  proceeds). Keeping it in the runbook protects against regressions
  in either direction.
- **T8 response.** The runbook is **operationally time-scoped**: it is
  accurate as of 2026-04-24, and will age. We anchor the stable
  surface (the Glama JSON-schema URL, the `mcp-proxy@6.4.3` npm
  package name, the `has-glama` label) and mark the UI-text guidance
  as "as observed" — future maintainers grep the schema URL + npm
  package name; the UI text is documentation-grade advisory only.
  **Revision:** include explicit "as-observed" timestamps on each
  UI-text reference.

## Round 3 — 反思 (reflection and decision)

- **F1: Ship `glama.json` at repo root with exactly two fields.**
  `{"$schema": "https://glama.ai/mcp/schemas/server.json", "maintainers": ["Battam1111"]}`. Nothing else. Unknown fields are silently dropped per the schema's implicit open shape, but adding them introduces false expectations.
- **F2: Document the correct Admin panel Build steps override.** For hatchling / setuptools Python MCP servers: `["uv pip install --system --break-system-packages '<package>[<mcp-extras>]'"]`. For uv-native repos: leave `["uv sync"]` default.
- **F3: Keep the repo Dockerfile (not Glama's scan Dockerfile) under our control.** The `io.modelcontextprotocol.server.name` label is load-bearing for OCI clients; do not remove. The fact that Glama generates its own scan image is fine — the two Dockerfiles serve different hosts.
- **F4: Escalate the `knowledge-and-memory` category mis-tag to the Glama dashboard** via manual web UI edit. Schedule: post-PR-merge, before end of sprint. Target: `agent-orchestration` + `developer-tools`.
- **F5: Mark this runbook as operationally time-scoped.** Anchor references that are stable (schema URL, npm package pin, label text) vs references that are fragile (UI button labels, page layout descriptions). The fragile references carry "as-observed 2026-04-24" stamps.

### What this craft revealed

- **Glama is not MCP Registry.** The duplication is structurally
  justified by different SLA commitments (identity verification vs
  code-running quality grading).
- **Minimal-schema files can be load-bearing.** `glama.json` has one
  required field and enables a discovery surface with ~22k servers.
  Simplicity is the feature, not a limitation.
- **PEP 668 is not a bug; it's a Debian policy surfacing in places it
  wasn't anticipated.** Scanner containers legitimately override it.
- **Categorization by ML classifier is the wrong primitive for
  positioning a cognitive substrate.** "Knowledge & Memory" and
  "cognitive substrate" are not the same category; the difference is
  doctrinal (L0 principle 1). Any future Glama-like host that doesn't
  expose category override will mis-categorize Myco the same way.
  This is a signal, not a bug — we should anticipate and budget for it.
- **The awesome-list PR gate is bot-driven + label-keyed.** Once the
  Glama side scored A, the `has-glama` label auto-applied and the PR
  flipped to MERGEABLE without human review — the bot itself did the
  transition. Future ecosystems should adopt this pattern.

## Deliverables

- **`glama.json`** at repo root — two-field ownership marker. (LANDED 2026-04-24.)
- **README / README_zh / README_ja** — Glama score badge. (LANDED commit `7f20220` 2026-04-24.)
- **`_canon.yaml::system.write_surface.allowed`** — `glama.json` entry. (LANDED with this craft's commit.)
- **`docs/primordia/glama_onboarding_runbook_craft_2026-04-24.md`** — this file.
- **`notes/integrated/n_20260424T070557Z_glama-mcp-registry-onboarding-runbook-20.md`** — substrate note capturing the raw learnings (eaten + assimilated 2026-04-24).

## Acceptance

- **Glama listing** at `https://glama.ai/mcp/servers/Battam1111/Myco` returns HTTP 200 with `security=A`, `license=A-permissive`, `quality=A`. ✓ (observed 2026-04-24 06:56 UTC)
- **README badge** at `https://glama.ai/mcp/servers/Battam1111/Myco/badges/score.svg` returns HTTP 200 + rendered SVG showing letter grade. ✓ (observed 2026-04-24 06:56 UTC; SHA256 etag captured in integrated note)
- **awesome-mcp-servers PR #5219** carries labels `has-emoji`, `valid-name`, `has-glama`; `mergeable=MERGEABLE`. ✓ (observed 2026-04-24)
- **Myco immune** passes on self-substrate after canon mutation (glama.json added to write_surface). ✓ (run as part of this craft's gating)
- **Non-regression:** Dockerfile in repo still carries `io.modelcontextprotocol.server.name` label; OCI-aware clients resolving via `io.github.Battam1111/myco` still find the correct image shape.
