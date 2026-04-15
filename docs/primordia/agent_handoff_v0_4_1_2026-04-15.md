# Agent Handoff — Myco v0.4.0 → v0.4.1

> **Date authored:** 2026-04-15
> **Authored by:** previous-session agent (Claude Opus 4.6), at Yanjun's request
> **Audience:** the next agent picking up Myco work
> **Read time:** 15 min for the whole thing; the first three sections are mandatory before you touch anything.

---

## 0. Read this first

You are inheriting the **Myco** project from a session that just shipped v0.4.0. Before you do *anything* — no greps, no edits, no PowerShell calls — read sections 1, 2, and 3 of this document end-to-end. Then read [`L0_VISION.md`](../architecture/L0_VISION.md) and [`L1_CONTRACT/protocol.md`](../architecture/L1_CONTRACT/protocol.md). Only after that should you start the user's task.

The user's name is **Yanjun**. They speak Mandarin and English fluently and switch freely. They value: tight prose, three-round craft debate, research-first work, and one-shot completion of plans (no patch-after-discover loops).

---

## 1. What Myco is, in one paragraph

Myco is an **Agent-First symbiotic cognitive substrate** — a runtime that gives an LLM agent a long-lived memory, an immune system, a metabolism, and a self-model. It is *not* a memory layer, *not* an agent runtime, *not* a skill framework. It is an **autopoietic substrate**: the agent brings intelligence; Myco brings continuity. Neither half is whole alone.

Concretely, a Myco "substrate" is a directory inside any project containing `_canon.yaml` (single source of truth for identity, write-surface, lint policy), `MYCO.md` (the agent's entry page — R1 of the hard contract), and `notes/{raw,integrated,distilled}/`. The agent invokes 12 verbs against it; the substrate maintains its own consistency via the `immune` lint and the SessionStart / PreCompact hooks.

The package ships on PyPI as `myco`. The reference repo is `github.com/Battam1111/Myco`.

---

## 2. Where we are right now

**v0.4.0 was released and pushed today (2026-04-15).** The session that did it:
- Completed Stage C (the "materialization" stage of the greenfield rewrite)
- Pushed `main` to `f6bba81`, tagged `v0.4.0` annotated tag, created GitHub release, uploaded both wheel and sdist to PyPI
- Removed `legacy_v0_3/` from git history *but kept it in the working tree as gitignored* for future reference

**The greenfield rewrite is done.** v0.4.0 deliberately broke backward compatibility with v0.3.x. The migration tool for old substrates lives at `scripts/migrate_ascc_substrate.py`.

**v0.4.1 is the next release** and has four explicit promises baked into the README + release notes (see §6 below). Those are your starting backlog.

---

## 3. The four permanent rules (Yanjun's, non-negotiable)

These come from `~/.claude/CLAUDE.md` and override everything else, including this handoff:

1. **事实性/实时性内容先调研。** Anything touching APIs, version numbers, dates, platform behavior — `WebFetch` / `WebSearch` first, never from memory. Symptom of violation: writing config from recall, then discovering it was wrong on test.

2. **Sub-agent 工具调用 ≥30 次。** Every `Agent` dispatch must include in its prompt: *"Your tool-use count must be ≥30. If you finish with fewer, your investigation depth is insufficient — keep digging."* Always specify `model: "opus"`.

3. **调研后走 craft 流程（三轮）。** Round 1: claim. Round 1.5: self-rebut. Round 2: revise. Round 2.5: re-rebut. Round 3: reflect on what the debate revealed. Only after Round 3 does a conclusion leave craft stage.

4. **开工前穷尽计划，一次性干完。** List every step, every secondary problem, every verification, before starting. Execute in one pass. If a new piece surfaces mid-execution, *stop and add it to the plan* before continuing — don't patch reactively.

These four rules are why this project moves fast. Honor them.

---

## 4. Architecture in 4 numbers

- **5 root principles** at L0: Only For Agent / 永恒吞噬 / 永恒进化 / 永恒迭代 / 万物互联. See `docs/architecture/L0_VISION.md`.
- **7 hard contract rules** R1–R7 at L1, jointly enforced by hooks + immune system + agent discipline. See `docs/architecture/L1_CONTRACT/protocol.md`.
- **5 biological subsystems** at L3 — Genesis, Ingestion, Digestion, Circulation, Homeostasis, plus a meta `session-end` verb. Each is a package under `src/myco/`.
- **12 verbs / 8 lint dimensions / 4 categories.** Verbs: `genesis` · `hunger` · `sense` · `forage` · `eat` · `reflect` · `digest` · `distill` · `perfuse` · `propagate` · `immune` · `session-end`. Dimensions: M1/M2/M3 (mechanical), SH1 (shipped), MB1/MB2 (metabolic), SE1/SE2 (semantic).

**Key invariant:** `src/myco/surface/manifest.yaml` is the single source of truth for both the CLI and the MCP server. One verb → one CLI subcommand → one MCP tool, derived mechanically. **Do not** add verbs by editing `cli.py` or `mcp.py` directly — edit the manifest and let the surface regenerate.

---

## 5. Repo layout (only the parts you'll touch)

```
Myco/
├── src/myco/
│   ├── __init__.py            ← __version__ is the SSoT (Hatchling reads it)
│   ├── core/                  ← shared primitives: paths, errors, canon I/O
│   ├── genesis/               ← `genesis` verb
│   ├── ingestion/             ← `hunger` `sense` `forage` `eat`
│   ├── digestion/             ← `reflect` `digest` `distill`
│   ├── circulation/           ← `perfuse` `propagate`
│   ├── homeostasis/           ← `immune` (8-dimension lint)
│   ├── surface/
│   │   ├── manifest.yaml      ← SSoT for CLI + MCP. Edit here, never edit cli.py
│   │   ├── cli.py             ← derived from manifest
│   │   └── mcp.py             ← `build_server()` entry point (lib only in v0.4.0)
│   ├── symbionts/             ← downstream-substrate adapters
│   └── meta.py                ← `session-end` composite verb
├── tests/                     ← mirror-layout pytest suite (283/283 green at v0.4.0)
├── scripts/
│   └── migrate_ascc_substrate.py   ← v0.3 → v0.4 substrate migrator
├── docs/
│   ├── architecture/
│   │   ├── L0_VISION.md
│   │   ├── L1_CONTRACT/{protocol.md, canon_schema.md, exit_codes.md, versioning.md}
│   │   ├── L2_DOCTRINE/
│   │   └── L3_IMPLEMENTATION/migration_strategy.md  ← Stage A–C plan that drove the rewrite
│   ├── contract_changelog.md   ← contract-layer changes (separate from package CHANGELOG)
│   └── primordia/              ← dated craft docs; this file lives here
├── .claude/
│   ├── hooks/                  ← SessionStart → hunger, PreCompact → session-end
│   └── settings.local.json
├── assets/                     ← logos + social_preview.png (referenced by READMEs)
├── legacy_v0_3/                ← gitignored quarantine of pre-rewrite tree (11 MB, 376 files)
├── README.md  README_zh.md  README_ja.md
├── CHANGELOG.md
├── pyproject.toml              ← Hatchling, dynamic version
└── _canon.yaml                 ← Myco's own substrate canon (yes, Myco uses Myco)
```

---

## 6. v0.4.1 backlog — explicit promises in v0.4.0 release notes

These four are **on the public record** in the README and the GitHub release notes. They must ship in v0.4.1:

1. **`python -m myco.mcp` standalone launcher.** A `__main__.py` under `src/myco/mcp/` (or wherever cleanest) that calls `build_server().run()` so users don't have to write Python to launch the MCP server.

2. **`[mcp]` extras target.** In `pyproject.toml`, an `[project.optional-dependencies] mcp = ["mcp>=..."]` entry so `pip install myco[mcp]` brings the MCP stdio server with it. Pin the lower bound after researching the current stable `mcp` package.

3. **Official `.plugin` bundle.** A Cowork/Claude-Code plugin packaging Myco's CLI + the manifest-driven MCP server + the `.claude/hooks/` wiring. Reference the `cowork-plugin-management:create-cowork-plugin` skill and the existing `.claude/` tree as the starting template.

4. **`CONTRIBUTING.md`.** Repo root. Cover: dev install (`pip install -e ".[dev]"`), test runner, pre-commit hooks (if any), the three-round craft convention, where architectural changes land (`docs/primordia/<dated-craft>.md`), commit-message style ("Stage X.Y: …" prefix is internal-only and *not* required of contributors).

**Beyond v0.4.1** — anything user wants. Don't volunteer scope.

---

## 7. Operational environment — *read this before pushing anything*

You are running inside Cowork mode, a Linux sandbox at `/sessions/<id>/`. The Myco repo is **mounted at** `/sessions/.../mnt/Myco/`, which is the same directory as `C:\Users\10350\Desktop\Myco\` on Yanjun's Windows machine. **Both sides see the same files.**

**Two filesystems, one repo, several gotchas:**

- **Sandbox `Bash` tool** has full POSIX, has internet (allowlisted), can run `git` for *local* operations and *HTTPS read* operations like `git ls-remote origin`. It **cannot push** because it has no GitHub credentials.
- **`mcp__Windows-MCP__PowerShell`** runs commands on Yanjun's actual Windows box, has the GitHub CLI / Git / Python / twine all wired up with credentials in keyring + `.pypirc`. **This is how you push, release, and upload.**
- **Windows-MCP PowerShell calls almost always time out at the 60s tool limit even when the underlying command succeeds.** Treat the timeout as "command was launched in background; verify result by other means" — use `git ls-remote`, `curl https://api.github.com/...`, or `curl https://pypi.org/pypi/myco/json` to confirm.
- **Index corruption (`bad signature`, `index file corrupt`)** happens if Windows-side and sandbox-side `git` both touch `.git/index` between operations. **Fix:** `rm -f .git/index && git reset` rebuilds from HEAD. Stage your files again afterward.
- **Phantom directories.** A directory deleted Windows-side may report as existing in the sandbox until the mount refreshes. `[ -d foo ] && echo DIR` while `ls foo` says "No such file or directory". Fix from the Windows side via `mcp__Windows-MCP__PowerShell` (`Remove-Item -Recurse -Force`).

**Push playbook (proven this session):**

```
# 1. From sandbox: stage and commit normally
cd /sessions/.../mnt/Myco
git add <files> && git commit -m "..."

# 2. Push from Windows side
mcp__Windows-MCP__PowerShell:
  cmd /c "cd /d C:\Users\10350\Desktop\Myco && git push origin main 2>&1"
  (will timeout — that's fine)

# 3. Verify from sandbox
git ls-remote origin main          # should match your local HEAD

# 4. Tag + push tag (force needed if retargeting)
git tag -f -a v0.4.X -m "..."
mcp__Windows-MCP__PowerShell: git push origin v0.4.X --force
git ls-remote origin refs/tags/v0.4.X

# 5. GitHub release (notes-file, not inline -n flag)
Write notes to a temp file like .release_notes_vX.Y.Z.md
mcp__Windows-MCP__PowerShell:
  cmd /c "cd /d C:\Users\10350\Desktop\Myco && gh release create vX.Y.Z --title vX.Y.Z --notes-file .release_notes_vX.Y.Z.md 2>&1"
  Verify: curl https://api.github.com/repos/Battam1111/Myco/releases/tags/vX.Y.Z

# 6. PyPI upload — CRITICAL: GBK console + rich progress bar = UnicodeEncodeError
mcp__Windows-MCP__PowerShell:
  cmd /c "cd /d C:\Users\10350\Desktop\Myco && set PYTHONIOENCODING=utf-8 && python -m twine upload --disable-progress-bar dist\myco-X.Y.Z-py3-none-any.whl dist\myco-X.Y.Z.tar.gz > upload.log 2>&1 & echo started"
  Wait, then check: curl https://pypi.org/pypi/myco/json
```

**Authorization etiquette:** Never push, retag, release, or upload to PyPI without an explicit go from Yanjun. This session's sequence was: commit → audit → present → "我授权" → push. Don't compress that loop.

**Cleanup:** Delete `.release_notes_*.md`, `upload*.log`, and any other ephemeral scratch files before signing off. The `.gitignore` covers them under `.release_notes_*.md` (added in C.6 territory) but don't rely on it; just `rm` them.

---

## 8. Pitfalls captured from this session

| Symptom | Root cause | Fix |
|---|---|---|
| `gh release create v0.4.0 --title "Myco v0.4.0 — Greenfield Rewrite"` returns *"no matches found for `Myco`"* | PowerShell-via-cmd quoting eats spaces and the em-dash | Use a hyphenated single-word title: `--title Myco-v0.4.0` or `--title v0.4.0` |
| `python -m twine upload` dies with `UnicodeEncodeError: 'gbk' codec can't encode character '\u2022'` | Yanjun's Windows console is GBK; rich progress bar emits a bullet | `set PYTHONIOENCODING=utf-8 && twine ... --disable-progress-bar` |
| `git checkout <commit> -- legacy_v0_3/` fails with *"cannot create directory at 'legacy_v0_3/.github': No such file or directory"* in the sandbox | WSL/sandbox mount ghost: the dir reports as existing but isn't accessible | Run the checkout via Windows-MCP PowerShell instead; sandbox sees the result through the mount |
| `git status` and other commands emit `error: index uses ?-?F extension, which we do not understand` | Sandbox and Windows-side git stepped on `.git/index` simultaneously | `rm -f .git/index && git reset` (from sandbox), then re-stage |
| Sandbox `cd` doesn't persist between Bash tool calls | Each Bash call is a fresh shell | Always prefix multi-step commands with `cd /sessions/.../mnt/Myco && ...` |
| Windows-MCP PowerShell timeouts on long-running commands | 60s tool-call limit | Don't retry blindly. Verify via independent channel (`ls-remote`, `curl`, file check). Most commands succeed in the background. |
| README files referenced `assets/logo_light_512.png` but `assets/` got swept in C.4 | Greenfield deletion was too broad | Restored as Stage C.6 hotfix; verified PyPI rendering |

---

## 9. Conventions the user enforces

- **Commit messages.** Stage commits use `Stage X.Y: <one-line description>` headline + body explaining the *why*, not the *what*. End with `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`. Use a heredoc to preserve newlines.
- **No emojis** in code, files, or commit messages unless Yanjun explicitly asks.
- **Lists/bullets** only when content is genuinely list-shaped. Prose for explanation.
- **Architectural changes** land as dated craft docs under `docs/primordia/<topic>_<YYYY-MM-DD>.md`.
- **Release tag = annotated** (`git tag -a`), never lightweight. Force-retag via `git tag -f -a` when amending the release commit.
- **CLI flag ordering:** global flags (`--project-dir`, `--json`, `--exit-on`) precede the verb. Document this anywhere it matters; users get this wrong.

---

## 10. Day-1 checklist for you

When you start your first session:

1. Read this document (you're doing it).
2. Read `docs/architecture/L0_VISION.md` (5 root principles, ~10 min).
3. Read `docs/architecture/L1_CONTRACT/protocol.md` (7 hard rules, ~15 min).
4. Skim `src/myco/surface/manifest.yaml` so the verb surface is in your head.
5. Run `pytest` from the repo root to confirm the green baseline (283 tests at v0.4.0 commit). If anything fails, **stop** and ask Yanjun before changing anything.
6. Run `myco --help` after `pip install -e .` to confirm CLI works locally.
7. Read `docs/architecture/L3_IMPLEMENTATION/migration_strategy.md` for the Stage A–C decomposition style; v0.4.1 will follow a similar staged plan.
8. Open the session by reporting: "I've read the handoff and the L0/L1. v0.4.1 promises four things — which one do you want to start with?"

---

## 11. What this session did not get to (intentionally deferred)

- **`docs/contract_changelog.md`** exists but is empty. It's supposed to track L0/L1/L2 doctrine changes separately from the package CHANGELOG. Populate it during v0.4.1 work as you make any contract-layer adjustments.
- **`CONTRIBUTING.md`** — promised for v0.4.1.
- **Repo's own `_canon.yaml`** has not been re-audited against the v0.4.0 contract since Stage C.1; run `myco immune --fix` before the v0.4.1 release commit.
- **`scripts/`** has only the migration script. Stage A–C had several helper scripts (`hpc_*`, `lint_knowledge.py`, etc. — some of those came from sister projects). If you find yourself wanting one, consider whether it should live here or in the consuming project.
- **No CI yet.** GitHub Actions for `pytest` + `myco immune` would be a v0.4.1 nice-to-have. Ask Yanjun before adding.

---

## 12. If you get stuck

- **Can't figure out how a verb is wired:** read `manifest.yaml`, then trace from `surface/cli.py` into the subsystem package.
- **Can't figure out a contract rule:** L1 protocol, then the relevant L2 doctrine page.
- **Can't figure out why a Stage X commit looks the way it does:** read the matching `docs/primordia/stage_<x>_*_craft_2026-04-15.md`.
- **Tool refuses to run / weird sandbox behavior:** check §7 and §8 first; most issues here are filesystem-quirks already cataloged.
- **Genuinely stuck:** stop, write down the problem in three bullets, ask Yanjun. Don't loop.

---

Welcome to Myco. The agent who built this is rooting for you. 🍄 (← only emoji you'll find in this whole repo. Don't add more.)
