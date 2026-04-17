---
type: craft
topic: v0.5.2 editable-by-default install model
slug: v0_5_2_editable_default
kind: design
date: 2026-04-17
rounds: 3
craft_protocol_version: 1
status: COMPILED
---

# v0.5.2 — Editable-by-Default Install Model Craft

> **Date**: 2026-04-17.
> **Layer**: L3 (install mechanism) + L0/L2 language revision.
> **Upward**: L0 principle 3 (永恒进化), L0 principle 4 (永恒迭代),
> L0 principle 1 (只为 Agent — the agent is the author, not a
> passive consumer).
> **Governs**: `src/myco/install/`, trilingual READMEs, `docs/INSTALL.md`,
> anywhere the "stable kernel / mutable substrate" phrase appears.

---

## Round 1 — 主张 (claim)

Myco v0.4.1 introduced the framing "stable kernel, mutable substrate:
`pip install` locks the kernel at a released version; the substrate
evolves daily." This framing was inherited into v0.5 without challenge.
It is **wrong**, and Yanjun caught it in the v0.5.1 post-release
review.

Here is why it is wrong. L0 principle 3 (永恒进化) and principle 4
(永恒迭代) make no kernel-vs-substrate distinction. The doctrine says
*the substrate* evolves — but Myco's own source tree is itself a
substrate (it has `_canon.yaml`, `MYCO.md`, `docs/primordia/`). The
kernel code under `src/myco/` is just the innermost ring of that
substrate. If that innermost ring is frozen by `pip install` into a
read-only `site-packages`, then:

1. The agent cannot fix a kernel bug it discovered while working —
   it must wait for a kernel release.
2. The agent cannot add a verb with a real implementation path — v0.5
   `scaffold` writes to `src/myco/<subsystem>/<verb>.py`, which does
   not exist in a read-only install.
3. The agent cannot register a substrate-local lint dimension without
   publishing a separate PyPI package.
4. The L0 "only for agent" principle implies the agent IS the author
   of the code, not its consumer — but read-only `site-packages`
   makes the agent a consumer of code someone else wrote.

The fix is to make **editable install the default**. `pip install`
still works for non-evolving library consumers, but the documented
path for anyone running Myco as intended is:

```
pip install myco[mcp]                  # bootstrap only
myco-install fresh ~/myco              # clone source + pip install -e .
```

or, with no persistent bootstrap install,

```
pipx run --spec 'myco[mcp]' myco-install fresh ~/myco
```

After `fresh`, `~/myco/src/myco/` is a writable clone. The agent
edits it the same way it edits `~/myco/_canon.yaml` or
`~/myco/docs/primordia/`. Kernel evolution is now a `git commit`
away, not a `pip install --upgrade` away.

## Round 1.5 — 自我反驳 (self-rebuttal)

- **T1**: editable-by-default breaks Python packaging norms. Most
  users expect `pip install X` → read-only install → upgrade via
  next `pip install --upgrade X`. Reversing this is surprising.
- **T2**: if the agent edits the kernel freely, how does `pip install
  --upgrade myco` ever work? The user's local kernel will have
  changes that upstream doesn't know about — upgrade becomes a merge
  not a replace. Git can do this, but pip can't.
- **T3**: two installs (pipx bootstrap + editable clone) is more
  complex than one `pip install`. New users hit a more complicated
  path.
- **T4**: an editable clone needs git on the user's machine. pip does
  not require git. Editable-default adds an implicit dependency.
- **T5**: security — the agent modifying kernel code changes Myco's
  attack surface. In a read-only install the kernel is tamper-
  evident (`pip install` hashes); in editable mode any tree under
  `~/myco/src/` is live code.
- **T6**: what about the PyPI package itself? If no one is supposed
  to `pip install myco` as a primary path, what does the PyPI
  release even signal?
- **T7**: disk space + clone time. `pipx run myco[mcp]` is instant;
  `git clone` pulls history + docs + tests, potentially ~20 MB.
- **T8**: what happens to `myco-install claude-code` et al. if the
  agent has edited `src/myco/mcp/` and the host now spawns broken
  code? The blast radius is bigger than before.
- **T9**: CI pipelines and ephemeral environments (Docker containers,
  CI runners) legitimately want read-only installs. Editable-default
  would force them onto a path they do not need.

## Round 2 — 修正 (revision)

- **R1** (addresses T1): the surprise is real but the alternative —
  a read-only install that silently violates the project's first
  principle — is worse. The `fresh` subcommand name makes the
  model explicit ("this is a fresh, writable install"). The README
  calls out the pip-install-only path as "library consumers,
  CI, vendoring" so no one is tricked.
- **R2** (addresses T2): `pip install --upgrade` is not the
  upgrade path for editable installs; `git pull` is. The README
  renames this section "Upgrading your kernel" and documents
  `cd ~/myco && git pull` + running `myco immune` to verify no
  post-upgrade drift. Merge conflicts in agent-authored kernel
  edits are legitimate craft events — the agent authored something
  that diverged from upstream, and now it reconciles via a
  pull-request-like flow. This is correct, not a bug.
- **R3** (addresses T3): `fresh` is ONE command. The user runs
  `pipx run --spec 'myco[mcp]' myco-install fresh ~/myco`, which
  clones + installs editable + configures any hosts passed via
  `--configure`, all in one shot. The bootstrap-then-editable
  split is an implementation detail the user does not see.
- **R4** (addresses T4): `fresh` checks `git --version` up front;
  if absent, it prints a clean error pointing the user to
  git-scm.com. Git is table stakes for "agent maintains the
  substrate including its own code" so requiring it is honest.
- **R5** (addresses T5): Myco's security model is not hash-pinned
  site-packages; it is the craft + immune combo. The agent's
  kernel edits pass through `myco immune`, `myco bump --contract`,
  and contract-changelog entries. Tamper evidence is replaced by
  audit evidence.
- **R6** (addresses T6): the PyPI release still signals "this is
  what the craft-approved latest kernel looks like". It is still
  the bootstrap path (`pipx run --spec 'myco[mcp]' ...`). It is
  also still a valid consumer-mode install for users who want to
  vendor Myco into another Python project. The release is not
  deprecated; only its role as "the normal install" is.
- **R7** (addresses T7): 20 MB of history + docs is a rounding
  error in 2026 disk budgets. `--depth 1` is offered as an option
  for bandwidth-constrained environments.
- **R8** (addresses T8): `myco-install host <client>` (the renamed
  existing command) keeps working after `fresh`. The host config
  still points at the user's editable Python via `sys.executable`,
  and that Python now imports from `~/myco/src/myco/`. If the agent
  breaks the kernel, the breakage surfaces the next time any host
  spawns the server — loud failure, not silent corruption.
- **R9** (addresses T9): the read-only install path stays available
  unchanged; it is the secondary path documented as "library
  consumers, CI, vendoring". CI pipelines unchanged.

## Round 2.5 — 再驳 (counter-rebuttal)

- **T10**: `fresh` requires a git repo URL. If Myco is ever mirrored
  privately, or the user wants to clone a fork, the URL must be
  configurable. Fix: `--repo <URL>` flag, default
  `https://github.com/Battam1111/Myco.git`.
- **T11**: `myco-install fresh` is a side-effect-heavy command
  (clones, pip installs, edits host configs). A --dry-run mode
  is mandatory. Also `--yes` for non-interactive use.
- **T12**: the CLI structure today is `myco-install <client>
  [--dry-run] [--uninstall] [--global]`. Adding `fresh` as a
  subcommand breaks that positional shape. Fix: introduce
  subparsers (`fresh` and `host`), keep legacy `myco-install
  <client>` working by sniffing whether the first arg is a known
  client name and auto-routing to `host`.
- **T13**: `fresh` is not pre-substrate in Myco's terminology
  (there is no ctx yet when it runs — it is being run before any
  substrate exists). It is a `myco-install` subcommand, not a
  `myco` verb. No manifest entry needed. Clean.
- **T14**: what if `--target` already exists and is a prior Myco
  clone? `fresh` should refuse non-empty dirs unless `--force` is
  passed. `--force` inside a prior clone means "reset and re-init"
  which is destructive; document clearly.
- **T15**: after `fresh`, the user's shell may still have an old
  `myco` on PATH (from a prior pipx install, for example). The
  `fresh` output must tell the user what `python -m myco`,
  `myco` (console script), and `pipx run myco` will each resolve
  to, so confusion is pre-empted.

## Round 3 — 反思 (reflection and decision)

All tensions resolved. v0.5.2 ships:

1. **`myco-install fresh <target>`** — the new primary install
   path. Subcommand of `myco-install`. Clones source, editable-
   installs it, optionally configures one or more MCP hosts
   (`--configure claude-code cursor windsurf`), verifies by
   invoking `python -m myco --version`. `--dry-run` previews;
   `--yes` skips any interactive confirmations; `--repo <URL>`
   overrides default clone source; `--branch <REF>` overrides
   default branch; `--depth <N>` caps clone history.

2. **`myco-install host <client>`** — the renamed existing
   behavior. Legacy `myco-install <client>` (with client as first
   positional) still works via a sniff in the CLI shim.

3. **Trilingual README rewrite** — the "Stable kernel, mutable
   substrate" paragraph is replaced with **"Editable by default,
   kernel IS substrate"**. Quick-start flips to the `fresh` flow.
   The library-consumer path (`pip install myco`) moves to a
   later "Non-evolving install" section.

4. **`docs/INSTALL.md` rewrite** — primary flow is `fresh`;
   secondary flows (manual per-host snippets) remain documented
   unchanged.

5. **Version metadata** — `__version__ = "0.5.2"`,
   `_canon.yaml::contract_version: v0.5.2` + synced,
   `.claude-plugin/plugin.json::version: 0.5.2`.

6. **CHANGELOG.md** entry `[0.5.2] — 2026-04-17` with the install-
   model reframing + the four textual surfaces it touches.

7. **`docs/contract_changelog.md`** entry `## v0.5.2 — 2026-04-17
   — Editable-by-default install model` — this IS a contract
   change because it changes the documented-and-supported primary
   user-facing install path.

8. **Tests** — `test_install_fresh.py` covers: happy path with
   `--dry-run`; missing-git detection; non-empty target refusal;
   `--configure` routing; legacy `myco-install <client>` sniff.

### What this craft revealed

1. The "stable kernel, mutable substrate" phrase was a compromise
   with traditional Python packaging conventions that Myco's own
   doctrine rejects. It slipped in at v0.4.1 without three-round
   review. This is why the craft discipline exists — to catch
   such compromises before they calcify.
2. The L0 principles are more uncompromising than the install
   mechanism had acknowledged. "只为 Agent" means the agent
   authors code, not just consumes it. Read-only `site-packages`
   contradicts principle 1 as much as it contradicts principles
   3 and 4.
3. The `scaffold` verb shipped in v0.5 was architecturally half-
   broken for exactly this reason — it writes to `src/myco/...`
   which is read-only in a normal install. `fresh` makes
   `scaffold` work for the first time outside Myco's own dev
   checkout.
4. PyPI is not deprecated as a distribution channel; its role
   simply shifts from "the normal install" to "the bootstrap
   channel + library-consumer channel". Both are legitimate;
   neither is primary for the agent-first use case.

## Deliverables

- `src/myco/install/__init__.py` — subparser-based CLI with
  `fresh` and `host` subcommands, plus legacy-sniff fallback.
- `src/myco/install/fresh.py` — new module implementing the
  clone + editable-install + host-config flow.
- `README.md` / `README_zh.md` / `README_ja.md` — rewritten
  positioning paragraph + Quick Start section.
- `docs/INSTALL.md` — editable-default flow primary; library-
  consumer flow documented as secondary.
- `src/myco/__init__.py` — `__version__ = "0.5.2"`.
- `.claude-plugin/plugin.json` — version 0.5.2.
- `_canon.yaml` — contract_version + synced_contract_version
  v0.5.2.
- `CHANGELOG.md` — new `[0.5.2]` section.
- `docs/contract_changelog.md` — new `## v0.5.2` section.
- `tests/unit/install/test_fresh.py` — new test file.
- `tests/unit/install/test_clients.py` — adjust for subparser
  split (legacy-sniff test added).

## Acceptance

- **pytest**: full suite green (target: ≥ 465 tests including the
  new fresh tests).
- **behavioral**:
  - `myco-install fresh --dry-run /tmp/fake` prints the plan
    without side effects.
  - `myco-install fresh /tmp/test-install --yes --configure
    claude-code` clones, installs editable, writes the
    claude-code MCP config.
  - Legacy `myco-install claude-code` still routes to the host
    subcommand.
  - `myco-install --help` shows both `fresh` and `host`
    subcommands.
- **non-regression**:
  - `myco-install claude-code --dry-run` behaves identically to
    v0.5.1 output.
  - All 7 existing host writers unchanged.
  - `myco --version` prints 0.5.2.
