# L2 — Extensibility

> **Status**: APPROVED (v0.5.6, 2026-04-17, per
> `docs/primordia/v0_5_6_doctrine_realignment_craft_2026-04-17.md`).
> **Layer**: L2. Subordinate to `L0_VISION.md` and `L1_CONTRACT/*`.
> **Upward mapping**: realizes L0 principle 3 (永恒进化 — the
> substrate's own shape is mutable), L0 principle 5 (万物互联 —
> the graph integrates all extensions), and L1 R6 (write-surface
> discipline — extensions honor it).
> **Mandate**: Myco has exactly **two** extension seams, they are
> **orthogonal**, and this page is the canonical doctrine that
> governs how they relate. All cross-cutting extensibility concerns
> cite this page.

---

## The two axes

A Myco substrate can be extended along exactly two axes. They are
independent — a substrate can use either, both, or neither. There
is no third axis; any new extensibility proposal must either fit
one of these seams or bump this doctrine.

| Axis | Seam | Scope | Lifecycle | Authoring verb | Audit verb | Enforcement dimension |
|---|---|---|---|---|---|---|
| **Per-substrate** | `.myco/plugins/` | One substrate only | Tied to the substrate (delete the folder → gone) | `myco ramify --substrate-local` | `myco graft --list` | `MF2` (substrate-local plugin health) |
| **Per-host** | `src/myco/boundary/install/` (MCP-config writers, 14 hosts) | All substrates on one host | Tied to the Myco install (ships in the kernel) | `myco-install host <client>` (10 of 14 hosts automated) | host probe via `myco-install host <client> --dry-run` | (no dim — see § "v0.8.5 retirement" below) |

### Why two axes, not one

A substrate's **own** custom lint rule (e.g. "this project requires
all notes tagged `#decision` to have an `authors:` frontmatter
field") belongs to that substrate and should disappear when the
substrate disappears. That's per-substrate extension — implemented
as a substrate-local plugin under `.myco/plugins/`.

A Myco user's **host**-specific Agent-sugar (e.g. "every Myco
substrate I work with in Claude Code should register a
`/myco:hunger` slash-command automatically") belongs to the user's
Myco install and should persist across every substrate they ever
create on that host. That's per-host extension — implemented as a
symbiont module under `src/myco/boundary/host_integration/<host>.py`.

The two axes compose freely. A user writing code in Claude Code on
three projects can have:

- Three separate `.myco/plugins/` trees (one per project, each with
  the project-specific rules)
- **One** `boundary/host_integration/claude_code.py` module shipping with Myco that
  registers `/myco:hunger` across all three

Neither axis interferes with the other. Neither axis can do the
other's job.

## Per-substrate (`.myco/plugins/`)

### Shape

Fixed layout under `<substrate_root>/.myco/plugins/`:

```
.myco/plugins/
├── __init__.py             # auto-imported on Substrate.load()
│                           # runs registration side effects
├── dimensions/             # optional; local Dimension subclasses
│   └── <slug>.py           # one class per file (matches kernel discipline)
├── adapters/               # optional; local ingestion Adapter subclasses
│   └── <slug>.py
├── schema_upgraders/       # optional; local canon upgraders
│   └── <slug>.py
└── verbs/                  # optional; local verb handlers
    └── <name>.py           # paired with an entry in manifest_overlay.yaml
```

And at `<substrate_root>/.myco/manifest_overlay.yaml`:

```yaml
commands:
  - name: "myproj-whatever"
    subsystem: "cycle"
    handler: "plugins.verbs.myproj_whatever:run"
    summary: "..."
    mcp_tool: "myco_myproj_whatever"
    args: []
```

### Registration

At `Substrate.load()` time the kernel imports
`<substrate_root>/.myco/plugins/__init__.py` under an isolated
module name (derived from `substrate_id`) and calls any
`register_external_dimension(cls)` / `register_external_adapter(cls)`
/ `register_external_upgrader(...)` calls the module makes.

`load_manifest_with_overlay(substrate_root)` merges
`manifest_overlay.yaml` into the runtime manifest at `dispatch()`
time; overlay verbs coexist with packaged verbs and are reachable
through both CLI and MCP.

### Import errors are captured, not raised

A broken plugin module fails to import **without** raising to the
kernel. The error is captured on `Substrate.local_plugin_errors`
(a tuple of error strings) and surfaced as `MF2` findings on the
next `myco immune` pass. This keeps the kernel loud-but-resilient
when substrates ship broken plugins.

### Authoring

`myco ramify --substrate-local --<kind> <spec>` writes a stub for
the selected kind. `--substrate-local` auto-toggles **on** when
the substrate root is not `myco-self`; opt out with
`--substrate-local=false` to author a kernel-level stub
instead (rarely what you want).

### Auditing

`myco graft --list` enumerates every registered local plugin.
`myco graft --validate` re-runs the import / registration gate
without a full immune pass. `myco graft --explain <name>` prints
the source file + class docstring for one specific plugin.

### Scope boundary

`.myco/plugins/` is out of scope for kernel-level dimensions.
Specifically:

- `MP1` (no-LLM-in-substrate) **does not** scan `.myco/plugins/`.
  A substrate that imports `openai` inside a local plugin is out
  of scope for kernel enforcement — per-substrate plugins are the
  substrate author's responsibility. (A future per-substrate
  dimension may cover this axis.)
- `MF1` (declared subsystems exist) scans canon subsystems, not
  local plugins. `MF2` is the plugin-axis analogue.

## Per-host (`src/myco/boundary/install/`)

### v0.8.5 retirement of the host_integration adapter package

Through v0.8.4, per-host extension lived as one
`src/myco/boundary/host_integration/<host>.py` module per supported
host, paired with the `MF3` (host-side artifact integrity) lint
dimension. At v0.8.5 the entire `host_integration/` subpackage and
its enforcing dim were excreted: the install-time surface that
actually shipped per host was a single `write_mcp_config()` writer,
which was already implemented inside `boundary/install/` with
per-host schema knowledge. The split into two packages duplicated
intent without adding behavior. `MF3` had no findings to emit once
the inert symbiont probes were retired.

### Shape (v0.8.5+)

Per-host integration is now a thin surface inside `boundary/install/`:

- `src/myco/boundary/install/__init__.py` — the `myco-install host
  <client>` CLI dispatcher.
- Per-host config writers (one function per host) — schema-aware,
  idempotent, dry-run capable, uninstall-capable.

At v0.8.6 the writers cover 14 host targets (claude-code, claude-
desktop, cowork, cursor, windsurf, zed, vscode, openclaw, gemini-cli,
codex-cli, goose — automated; Continue.dev, Cline, JetBrains — manual
config snippets shipped in `.docs/INSTALL.md`).

### Authoring

`myco-install host <client>` resolves the absolute Python
interpreter path and writes the host's expected MCP-config schema.
The list of supported hosts lives in `boundary/install/` and is
extended by adding a new writer function alongside the existing
ones; no separate symbiont module is required.

### Scope boundary

Install-time writers can write to host-specific paths outside the
substrate root (e.g. `~/.claude.json`, `~/.cursor/mcp.json`). Those
paths are **not** governed by `_canon.yaml::system.write_surface.allowed`
— which covers writes inside the substrate. Host-side writes are
governed by the host's own config discipline. This is a deliberate
boundary: the substrate cannot enforce writes to paths it doesn't
own. The Cowork plugin upload step (§ INSTALL.md 1.1) is the only
flow where the user, not Myco, performs the actual write.

## What neither axis is

To prevent creep, this section is deliberately explicit about what
falls outside both seams:

- **Forks of Myco itself** — if a change needs to modify
  `src/myco/` beyond the `boundary/install/` per-host writers, it
  is a kernel change, not an extension. Kernel changes go through
  craft + molt.
- **Runtime-discovered plugins outside `.myco/plugins/`** — the
  kernel only auto-imports from `.myco/plugins/`. A module dropped
  into `notes/` or `docs/` will not be loaded as a plugin; it will
  be treated as a note or doc.
- **LLM provider coupling** — `system.llm_policy` (v0.6.14: 2-value
  enum `forbidden`|`opt-in`) governs whether the substrate process
  may speak directly to a provider. The pre-v0.6.14 `src/myco/providers/`
  package was reserved as the opt-in landing pad, but excreted at
  v0.6.14 after seven minor releases without population. Future
  provider coupling, if ever needed, requires its own L0 P1 amendment
  craft + fresh contract-bumping molt rather than a pre-baked escape
  hatch sitting empty for years. `MP1`/`MP2`/`MP3` + `CL1`/`CL2`/`CL3`
  are the mechanical guards.
- **Site-packages overrides** — monkey-patching Myco by installing
  a sibling package that shadows internal modules is unsupported
  and immune-flag-eligible when detected.

## Cross-reference matrix

| Concern | Home |
|---|---|
| Per-substrate plugin protocol (loader, registration hooks) | This doc, `L2_DOCTRINE/homeostasis.md` (MF2), `src/myco/core/substrate.py` |
| Per-host adapter protocol (discover, install, SymbiontProbe) | `L2_DOCTRINE/boundary.md` |
| LLM-provider opt-in seam | `L0_VISION.md` principle 1 addendum, `L1_CONTRACT/canon_schema.md` (`system.llm_policy`), `L2_DOCTRINE/homeostasis.md` (MP1/MP2/MP3) |
| Authoring verbs | `L3_IMPLEMENTATION/command_manifest.md` §governance verbs (`ramify`, `graft`) |
| Write-surface discipline | `L1_CONTRACT/protocol.md` R6, `L1_CONTRACT/canon_schema.md` (system.write_surface.allowed) |

## Review cadence

This doctrine is re-audited at every MAJOR release. If a future
release proposes a third extension axis (e.g. cross-host federation
plugins), it must either (a) justify why neither existing axis
fits, or (b) bump this doctrine's two-axis mandate — not silently
add a third.
