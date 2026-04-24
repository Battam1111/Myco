---
captured_at: '2026-04-24T07:05:57Z'
source: agent:glama-onboarding
stage: integrated
tags:
- glama
- onboarding
- mcp-registry
- docker
- pep-668
- awesome-mcp-servers
- runbook
integrated_at: '2026-04-24T07:06:04Z'
---
Glama MCP registry onboarding runbook (2026-04-23/24)

## End-state achieved
- Myco listed at https://glama.ai/mcp/servers/Battam1111/Myco with quality=A, license=A-permissive, security=tested
- Badge live at /badges/score.svg (was 404 placeholder pre-scan)
- README in 3 languages carry the badge; Glama auto-refreshes
- punkpeye/awesome-mcp-servers PR #5219: label `has-glama` applied, mergeable=MERGEABLE
- glama.json at repo root captures ownership (maintainers: [Battam1111]) and is the sole spec-compliant file

## What is a glama.json (minimal surface)
Schema at https://glama.ai/mcp/schemas/server.json defines EXACTLY two fields:
  $schema (string), maintainers (array of GitHub usernames, required)
That's it. NO categories / description / displayName / tags / envVars. All auto-scraped from the repo (README, pyproject.toml, LICENSE, Dockerfile labels). Any metadata the scraper gets wrong must be corrected via Glama's web dashboard, NOT by adding fields to glama.json — unknown fields are silently ignored.

## Four false paths burned (save next agent from)
1. `https://glama.ai/mcp/servers/submit` — NOT a real route. Glama SPA redirects to `?query=author:submit` (treats "submit" as author-name search). The real submit entry is an auth-gated "Add MCP Server" button on /mcp/servers/ that only appears after GitHub OAuth login.
2. Admin panel is NOT "paste a Dockerfile textarea". It's a structured config form (Node.js version, Python version, Build steps JSON array, CMD args JSON array, env var schema, placeholder params, pinned commit SHA) that generates Glama's own Dockerfile template. Our repo's own Dockerfile is irrelevant to Glama's scan — they build their own.
3. Default Build step `["uv sync"]` assumes a uv-lock-managed repo. Myco uses hatchling + setuptools-style pyproject; no uv.lock exists. Fix: override Build step to `["uv pip install --system --break-system-packages 'myco[mcp]'"]` — installs our PyPI wheel into Debian's managed Python 3.11, bypassing PEP 668 (acceptable inside ephemeral Glama scanner container).
4. Without `--break-system-packages`, uv pip refuses with "The interpreter at /usr is externally managed". PEP 668 was landed in Debian 12 to protect apt-managed Python. In Docker container this protection is over-cautious; flag is the documented escape.

## Glama Dockerfile template anatomy (for debugging future failures)
Base: debian:bookworm-slim
Layers:
- apt-get install ca-certificates curl git + nodejs (via NodeSource setup_24.x) + npm install -g mcp-proxy@6.4.3 pnpm@10.14.0 + curl astral.sh/uv/install.sh + uv python install <VERSION> --default --preview + symlink /usr/local/bin/python
- WORKDIR /app
- RUN git clone <REPO> . && git checkout <PINNED_SHA or HEAD>
- RUN <BUILD_STEPS>
- CMD [<CMD_ARGS>] — default ["mcp-proxy", "--", "<server-executable>"]

mcp-proxy is punkpeye's own npm package (v6.4.3). It wraps stdio-based MCP servers and proxies to SSE so Glama's scanner can probe via HTTP. Our mcp-server-myco console script (registered in pyproject.toml::project.scripts) is what mcp-proxy spawns.

## Key contract knobs for Glama-scannable MCP servers
- pyproject.toml must have a [project.scripts] entry that becomes an on-PATH executable after pip install. Ours: mcp-server-myco = "myco.mcp:main".
- optional-dependencies group for MCP SDK: `myco[mcp]` pulls in `mcp>=1.2` (FastMCP).
- Dockerfile in repo is orthogonal to Glama's build (they generate their own). Ours exists for namespace verification via LABEL `io.modelcontextprotocol.server.name="io.github.Battam1111/myco"` — different purpose.

## Follow-ups (non-blocking)
- Glama auto-categorized us as "Knowledge & Memory" + "Agent Orchestration". First is WRONG (Myco is explicitly a cognitive substrate, NOT a memory tool per L0 principle + v0.5.19 skill frontmatter). Correct via Glama dashboard: change category to `agent-orchestration` + `developer-tools` (valid slug list at /mcp/categories).
- glama.json at repo root doesn't control categories; correction must be manual web UI action.

## Time budget observed
- Submit via UI: ~30s (once button located)
- First Build & Release (failed, uv sync): ~683ms (fast fail, no image built)
- Second Build & Release (passed, --break-system-packages): <2 min total
- Badge CDN propagation: <30s after successful build
- awesome-mcp-servers PR label refresh: <1 min after Glama listing becomes scored

Source: this session, 2026-04-23/24. Badge currently served from
https://glama.ai/mcp/servers/Battam1111/Myco/badges/score.svg
(SHA256 etag as of first fetch: 9b9bf1f5a7a1855912ecdc2ea3478111c385876a35a9c2ab03e498b09f3a2d91)
