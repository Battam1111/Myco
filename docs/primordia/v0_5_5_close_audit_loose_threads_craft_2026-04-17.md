---
type: craft
topic: v0.5.5 close audit loose threads
slug: v0_5_5_close_audit_loose_threads
kind: audit
date: 2026-04-17
rounds: 3
craft_protocol_version: 1
status: COMPILED
---

# v0.5.5 — Close Every Loose Thread from v0.4.1 Audit + v0.5.1 Craft

> **Date**: 2026-04-17.
> **Layer**: L3 (mechanism) + L2 (digestion + circulation doctrine
> updates) + one doctrine decision at L2-boundary (symbiont /
> `.myco/plugins/` relationship).
> **Upward**: L0 principle 3 (永恒进化), 4 (永恒迭代), 5 (万物互联) —
> three principles that v0.4.1 + v0.5.1 sketched but left partially
> un-mechanized.
> **Governs**: `src/myco/homeostasis/dimension.py` (fix method),
> M2 + MB1 fix implementations, `src/myco/circulation/graph.py` +
> new `graph_src.py` + persistence, new `myco brief` verb, 3 new
> MCP host writers, `src/myco/symbionts/` decision, sporulate
> doctrine boundary.

---

## Round 1 — 主张 (claim)

Every post-release audit since v0.4.1 has surfaced the same pattern:
**infrastructure in place, no concrete use**. The machinery is built,
the tests pass, the doctrine text references it — but the actual
intended behaviour is never exercised. v0.5.5 closes eight such
loose threads in a single release.

The eight:

1. **MAJOR-A: fixable dimensions** — `immune --fix` flag has existed
   since v0.4.0 and has been plumbed through every kernel call as a
   no-op. M2 (missing entry-point) + MB1 (raw backlog) get the first
   real fix implementations; the `Dimension` base class gets a
   `fix(ctx, finding)` method and a `fixable: ClassVar[bool]` flag.
2. **MAJOR-B: schema upgrader demo** — v0.5.1 shipped the
   `schema_upgraders: dict[str, Callable]` registry with chain-apply
   + cycle detection. Zero entries registered, zero tests proving
   the end-to-end path. v0.5.5 registers one synthetic v0-to-1
   upgrader under a non-conflicting key to prove the wire works.
3. **MAJOR-C: sporulate doctrine boundary** — v0.4.1 audit flagged
   `sporulate` (then `distill`) as a "stub generator". The real
   synthesis is an LLM call, but Myco's L0 principle 1 says
   `Agent calls LLM`, not `substrate calls LLM`. v0.5.5 writes that
   boundary into L2 `digestion.md`: sporulate prepares materials +
   proposes structure; the Agent authors synthesis.
4. **MAJOR-D: symbiont resolution** — `src/myco/symbionts/` has been
   an empty package since the greenfield rewrite. v0.5.3 added
   `.myco/plugins/` as the new substrate-local extension seam.
   What is `symbionts/` for? v0.5.5 writes a symbiont craft that
   either (a) defines the remaining niche or (b) deprecates the
   package. Decision: **(a)** — symbionts are **host-side
   Agent-sugar adapters** (Claude Code, Cursor, VS Code specific
   hooks / skills / slash-commands generated from manifest).
   `.myco/plugins/` is per-substrate; symbionts are per-host.
5. **MAJOR-F: circulation graph over `src/**`** — v0.4.1 audit
   noted the graph covers `notes/**`, `docs/**`, canon, and entry
   point, but NOT code. Code-to-doctrine traversal is blind. v0.5.5
   extends the graph via AST walk (import edges + docstring doc-
   reference edges).
6. **MAJOR-J: graph persistence** — v0.4.1 noted the graph is
   rebuilt in memory on every call; no persistence, no incremental
   update. v0.5.5 adds `.myco_state/graph.json` with a canon +
   src-fingerprint cache key. Cold build full; warm build reuses.
7. **MAJOR-G: `myco brief` — the one human-facing verb** — L0
   principle 1 says "humans do not browse Myco". In practice,
   humans occasionally need a batch summary (for approval gates,
   periodic review, handoff). `brief` is the explicit, single,
   carved-out exception — it does not replace any agent-side verb;
   it rolls up their outputs for a human reading moment.
8. **MAJOR-I: 3 new automated MCP hosts** — Gemini CLI, Codex CLI,
   Goose. All three had manual snippets in `docs/INSTALL.md`
   already; v0.5.5 moves them under `myco-install host`. Takes
   automated coverage from 7 to 10.

Single release: 8 threads, one contract version bump, one craft.

## Round 1.5 — 自我反驳 (self-rebuttal)

- **T1**: brief verb violates L0 principle 1 ("只为 Agent"). Carving
  an exception weakens the principle. Once there's one human-
  facing verb, where does it stop? What's next, a `myco prettify`
  for a human-readable log viewer?
- **T2**: fixable dimensions need a "safe fix" discipline not yet
  written. A fix that creates a file with wrong content is worse
  than a fix that does nothing. No contract pins what "safe fix"
  means.
- **T3**: schema upgrader demo is theatre. Registering a synthetic
  upgrader that nobody ever invokes in practice is adding test
  chrome, not real use. A real v1→v2 migration is the proof; v0.5.5
  doesn't deliver that.
- **T4**: symbiont decision (host-side Agent-sugar) is too narrow.
  It commits `symbionts/` to one specific thing forever. Maybe
  symbionts should have been the substrate-local path and we just
  picked the wrong vocabulary at v0.4.
- **T5**: graph-over-src is scope creep beyond circulation. Code is
  code, docs are docs. Why would sense/traverse have to know about
  Python imports?
- **T6**: graph persistence opens a cache-invalidation problem.
  Canon change → rebuild. But src file edit? tests edit? The
  fingerprint has to cover enough or stale cache lingers.
- **T7**: 8 threads in one release is high regression risk. Pick 3,
  ship, then do the rest in v0.5.6.
- **T8**: moving sporulate from "stub generator" to "material
  preparer + Agent writes" without renaming the verb means the
  manifest description is still "Sporulate a distillation proposal
  from integrated notes" which reads like the verb does the
  synthesis.

## Round 2 — 修正 (revision)

- **R1** (addresses T1): L0 principle 1 is "Agent reads Myco". It
  does not say "no human ever reads anything". It says the Agent
  is the primary consumer, humans only speak natural language.
  `brief` is for the natural-language moment: you say "what has
  happened since last week", Agent runs `myco brief`, hands you a
  formatted markdown summary. This is *humans approving and
  reviewing*, the third leg of the agent-human-Myco triangle. One
  verb carved with a single concrete purpose does not erode the
  principle; an undocumented human-UI growth would. Ship `brief`
  with the explicit doctrine note that `brief` is the one exception
  and every other verb stays agent-first.
- **R2** (addresses T2): v0.5.5 writes the safe-fix discipline as
  part of this craft's Deliverables section. The discipline:
  (a) idempotent (re-running is a no-op), (b) narrow (creates or
  corrects exactly one field/file), (c) never destructive (never
  deletes, never overwrites non-empty content), (d) bounded (the
  fix's write target must be under canon `write_surface.allowed`;
  the kernel guards this automatically). M2 and MB1 both honour
  these rules; future fixable dimensions inherit.
- **R3** (addresses T3): the demo upgrader isn't theatre because
  it proves the chain-apply + cycle-detection + warning-silencing
  code paths that nobody has exercised end-to-end. v0.5.5 registers
  it under schema_version "0" (never a real shipped version) so
  the demo doesn't affect any substrate. The test exercises:
  register → substrate with schema_version "0" → load → upgrader
  fires → warning suppressed → canon parses. That's real behaviour
  pinning real code.
- **R4** (addresses T4): symbionts = host-side Agent-sugar is
  narrow by design, not by accident. Per-host adapters (Claude
  Code skill-generators, Cursor rule-file writers, VS Code task
  configurators) are a real thing Myco hasn't covered; calling
  that `symbionts/` honours the biology metaphor (cross-species
  cooperation with the host environment). v0.5.5 writes the
  craft + a `symbiont_protocol.md` stub under L3 but does NOT
  populate with concrete adapters — that's separate releases.
  The package stays empty with the doctrine note pointing at the
  protocol.
- **R5** (addresses T5): circulation is 万物互联. Code importing
  code IS mycelial connection. The v0.4.1 audit was explicit:
  "mycelium graph covers `notes/**`, `docs/**`, `_canon.yaml`, and
  the entry point; it does NOT cover `src/**` code files". The
  audit is the authority; v0.5.5 honours it.
- **R6** (addresses T6): fingerprint = sha256(canon text +
  sorted(path, mtime) for every `.py` file under `src/`). Canon
  edit → rebuild. Src edit → rebuild. Tests edit → no rebuild
  (tests are not under src in this fingerprint). That's the right
  granularity: test edits should not invalidate the graph.
- **R7** (addresses T7): every item has a bounded scope (~50-300
  LOC each + tests). Total ~1500 new LOC + ~60 new tests. The
  reason to ship as one release is **narrative coherence**: all
  eight are "v0.4.1 audit / v0.5.1 craft loose threads"; they form
  a single act of honouring debt rather than dribbling it out.
- **R8** (addresses T8): `sporulate` manifest summary rewrites to
  "Sporulate: bundle integrated notes into a proposal skeleton.
  The Agent writes the synthesis prose separately." That's
  explicit. The verb stays; the expectation is corrected.

## Round 2.5 — 再驳 (counter-rebuttal)

- **T9**: fixing the immune `run_immune` signature to return fix
  outcomes changes the payload shape. Every test that asserts
  exact payload keys will break. Fixable at edit time but a churn.
- **T10**: graph-over-src walking the entire `src/myco/` tree is
  slow on cold build. 79 files × AST parse × import resolution is
  ~1 second. The persistence layer helps but cold install is slow.
- **T11**: `brief`'s output format is not pinned. Different
  invocations could produce different markdown layouts, confusing
  humans. Fix: brief output has a fixed section order with stable
  headers.
- **T12**: Codex CLI's TOML writing via block-surgery (no real
  TOML writer) is fragile. A pre-existing `[mcp_servers.myco]`
  block with extra fields gets trampled on re-install.

## Round 3 — 反思 (reflection and decision)

All tensions resolved. v0.5.5 ships:

### Final scope

| Major | Verb/mechanism | Scope |
|---|---|---|
| A | `Dimension.fix()` + M2 + MB1 fixable | New base method + 2 implementations |
| B | `schema_upgraders` v0→1 demo | 1 upgrader + 1 test under non-conflicting key |
| C | Sporulate doctrine boundary | L2 `digestion.md` edit + `sporulate.py` docstring + manifest summary |
| D | Symbiont resolution | `docs/primordia/` craft + L3 `symbiont_protocol.md` stub; package stays empty |
| F | Graph over `src/**` | New `graph_src.py` + import/docstring edges |
| G | `myco brief` verb | New handler in `cycle/`; markdown human rollup |
| I | 3 new MCP hosts | gemini-cli / codex-cli / goose in `install/clients.py` |
| J | Graph persistence | `.myco_state/graph.json` + fingerprint cache |

### Safe-fix discipline (new doctrine)

A fixable lint dimension MUST:
1. Be **idempotent** — re-running is a no-op.
2. Be **narrow** — creates or corrects exactly one named file or
   one field; never cascades.
3. Be **non-destructive** — never deletes; never overwrites non-
   empty content; if the target is pre-populated, report `applied:
   false` with a clear `detail`.
4. Respect `write_surface` — the kernel checks every fix target
   against `canon.system.write_surface.allowed` before dispatch.

### What this craft revealed

1. The audit + craft loop works. Every post-release round (v0.4.1
   audit, v0.5.0 craft, v0.5.1 audit, v0.5.3 dogfood) has
   surfaced real gaps; v0.5.5 is the first release specifically
   about "close the ones we've been staring at". The discipline of
   "every release ends with a craft; every craft surfaces gaps;
   gaps queue for the next release" is self-perpetuating — as
   designed.
2. The `brief` exception to "only for Agent" is honest doctrine
   work. Writing L0 principle 1 without the carved exception would
   have made the verb feel smuggled in; writing it WITH the
   exception acknowledges that humans need a window, just one
   carefully-bounded one.
3. Symbiont resolution (host-side Agent-sugar) is a real niche but
   not a v0.5 release. Writing the craft + the protocol stub now
   means v0.6 can populate concrete adapters without a design
   backlog.

## Deliverables

- `src/myco/homeostasis/dimension.py` — `fixable: ClassVar[bool]`,
  default-no-op `fix(ctx, finding) -> dict[str, Any]`.
- `src/myco/homeostasis/kernel.py` — `run_immune(fix=True)` invokes
  fixable dimensions, guards with write-surface check, captures
  exceptions into `payload["fixes"]`.
- `src/myco/homeostasis/dimensions/m2_entry_point_exists.py` —
  `fixable=True` + `fix()` creates canon-declared entry point file
  from minimal skeleton.
- `src/myco/homeostasis/dimensions/mb1_raw_notes_backlog.py` —
  `fixable=True` + `fix()` calls `reflect(ctx)` and reports
  promotion count.
- `src/myco/core/canon.py` — register demo `v0_to_1` upgrader under
  schema_version "0" at module import time; gated behind a
  MYCO_DEMO_UPGRADER env var so production substrates don't see
  it unless opted in. Actually: register at `core.canon` level
  unconditionally; it's harmless because no real canon has
  schema_version "0".
- `src/myco/cycle/brief.py` — new handler. Markdown output with
  fixed section order: Identity / Hunger / Immune summary / Notes
  inventory / Primordia recent / Local plugins / Suggested next.
- `src/myco/surface/manifest.yaml` — add `brief` verb entry with
  `subsystem: cycle`, `handler: myco.cycle.brief:run`, args:
  `--since` (optional date), `--format` (markdown|json, default
  markdown), `--project-dir` (global).
- `src/myco/circulation/graph_src.py` — AST walker for `src/**`.
- `src/myco/circulation/graph.py` — persistence + fingerprint +
  cache-aware `build_graph`.
- `src/myco/core/paths.py` — `graph_cache` property.
- `src/myco/install/clients.py` — `install_gemini_cli`,
  `install_codex_cli`, `install_goose`.
- `docs/architecture/L2_DOCTRINE/digestion.md` — sporulate
  boundary edit.
- `docs/architecture/L2_DOCTRINE/circulation.md` — graph coverage
  + persistence doctrine.
- `docs/architecture/L3_IMPLEMENTATION/symbiont_protocol.md` —
  new stub: symbionts = per-host Agent-sugar adapters.
- `docs/primordia/v0_5_5_close_audit_loose_threads_craft_2026-04-
  17.md` (this doc).
- `docs/contract_changelog.md` + `CHANGELOG.md` — v0.5.5 entries.
- `_canon.yaml` + `pyproject.toml` — version 0.5.5 / v0.5.5.
- 60+ new tests across the 8 scopes.

## Acceptance

- **pytest**: green at ≥600 (was 543 at v0.5.4).
- **behavioural**:
  - `myco immune --fix` on a substrate missing MYCO.md creates
    MYCO.md; re-run is no-op.
  - `myco immune --fix` on substrate with raw backlog triggers
    assimilate and reports promotion count.
  - `myco traverse` reports `src_node_count > 0` on myco-self.
  - Second `myco traverse` in same substrate loads cached graph
    (cached=True, faster).
  - `myco brief` produces a markdown document with stable sections.
  - `myco-install host gemini-cli --dry-run` previews; real install
    writes `~/.gemini/settings.json`.
- **non-regression**:
  - Every v0.5.4 test still green (+60 new tests additive).
  - Every v0.5.x legacy alias still resolves (tested via full suite).
  - `from myco.meta import session_end_run` still imports via shim.
