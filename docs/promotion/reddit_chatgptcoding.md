# r/ChatGPTCoding post draft

## Title

```
Myco: long-term memory for your Cursor/Claude-Code agent that survives across sessions, projects, and model versions
```

## Body

```
If you've used Cursor or Claude Code across multiple projects over months, you've probably hit the memory wall — the agent has amnesia between projects, re-derives the same conventions every morning, and can't remember why you chose one approach over another three weeks ago.

I built Myco (https://github.com/Battam1111/Myco) to fix this. It's a filesystem shape + a CLI + an MCP server that gives your agent a persistent substrate across every project you touch. One MCP server install, every MCP-speaking host sees the same 18 verbs.

Why this matters for Cursor/Claude-Code specifically

1. **Cross-project propagation.** When you make a decision in project A (e.g. "use Bun instead of Node for scripts"), Myco captures it in A's substrate. Later, starting project B, `myco propagate --dst ~/project-b` can push that decision as raw material into B's substrate. The agent doesn't re-derive conventions from scratch.

2. **Per-substrate plugins.** Each project can declare its own lint rules via `.myco/plugins/dimensions/`. Example: "every note tagged `decision` must have an `authors:` frontmatter field". The kernel's 25 dims stay universal; project-specific discipline lives in the project.

3. **MCP-first.** One `myco-install fresh ~/myco` clones and installs the whole thing. Cursor, Claude Desktop, Claude Code, Windsurf, Zed, VS Code (GitHub Copilot), Goose, Codex CLI, Gemini CLI, OpenClaw — all auto-configured with one command (or pick one with `myco-install host claude-code`).

4. **Session discipline.** R1 = every session boots with `hunger` (what's missing?). R2 = every session ends with `senesce` (assimilate + immune --fix). These are wired to SessionStart + PreCompact + SessionEnd hooks in Claude Code; the agent doesn't skip them because the host kills them if it tries.

5. **Editable by default.** Myco is installed via `pip install -e`, not as a frozen library. When the agent needs a new verb or dim for your workflow, it scaffolds one with `myco ramify` — in your tree, not in a fork of Myco.

Minimum viable flow

```
pipx run --spec 'myco[mcp]' myco-install fresh ~/myco-sandbox
cd ~/myco-sandbox
python -m myco hunger
# (now add MCP config to your host — `myco-install host claude-code` does it)
# ... agent drives from here ...
```

Comparison with what's already in this sub

- **vs "just use a CLAUDE.md"**: CLAUDE.md is the entry page (Myco uses MYCO.md for the same role). The substrate *underneath* the entry page is what makes long-term memory work — 18 verbs + 25 dims + the governance loop.
- **vs Aider's git-aware history**: Aider remembers what it changed in the code; Myco remembers why. Orthogonal; many people use both.
- **vs Cursor's built-in memory**: Cursor's memory is great for single-project continuity. Myco is the cross-project + cross-host layer.

Repo + docs + examples:
- https://github.com/Battam1111/Myco
- https://github.com/Battam1111/Myco/tree/main/examples/research-assistant (realistic substrate template)
- https://github.com/Battam1111/Myco/tree/main/docs/architecture (L0 five principles + L1 R1-R7)

Curious what's working for people here — if you've hit the cross-session memory wall and solved it with something else, would love to hear the shape.
```

---

## Why this shape

- **Directly names Cursor + Claude Code + r/ChatGPTCoding-relevant
  tools** in the first line. The sub is practitioner-focused;
  titles that name the agent they use feel targeted.
- **Five numbered "why this matters" bullets** instead of prose.
  Subs like this skim.
- **Concrete shell commands** — `pipx run` + `myco-install` — the
  sub's favourite format.
- **Explicit "vs CLAUDE.md" + "vs Aider" + "vs Cursor memory"**
  section pre-empts the comparison comments.
- **"Curious what's working for people here"** closing converts
  the post from announcement to conversation.

## After posting

r/ChatGPTCoding comments skew toward "show me it running" — if
someone asks for a demo GIF / video / screenshot, you don't have
one ready. Offer: "happy to drop a Claude Code session
transcript showing the flow — DM me and I'll paste one over."
That defers without dodging.
