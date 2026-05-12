# Migration history

Version-to-version upgrade instructions for operators of downstream
Myco substrates. v0.8.8 max-aggressive consolidation merged the
per-boundary files (v0.5.24→v0.6.0, v0.7.4→v0.7.5, v0.7.x→v0.8.0)
into this single history doc. Section anchors below preserve the
original headings so external link tables continue to resolve.

## Boundaries covered

| Boundary | Anchor | Headline |
|---|---|---|
| v0.5.24 → v0.6.0 | [#migration-v0524-to-v060](#migration-v0524-to-v060) | Round 4 owner-amended single-shot release; thorough refactor + unified evolution |
| v0.7.4 → v0.7.5 | [#migration-v074-to-v075](#migration-v074-to-v075) | P0-P6 omnibus; canon schema v2→v3 (`metrics.lint_dim_count` field); upgrader chain walks to latest |
| v0.7.x → v0.8.0 | [#migration-v07x-to-v080](#migration-v07x-to-v080) | First L0 amendment since v0.4.x (Living Bets persistence-budget refinement); canon schema v3→v4 (`system.governance.last_living_bets_audit_at` + `persistence_metrics` cache fields for LB1/LB2) |

For v0.8.0+ (all additive, no breaking changes): see
[`../contract_changelog.md`](../contract_changelog.md). The v0.8.5
retirement of `boundary.host_integration`, `surface.capability`, and
MF3 dim was reachable from zero call sites; downstream consumers
had no migration to perform.

### Pre-v0.6 (excreted at v0.8.5)

The v0.5.7→v0.5.8 (write_surface mechanical enforcement) and
v0.5.8→v0.5.9 (immune-zero baseline) migration guides were deleted
at v0.8.5 — the substrate has been on v0.6+ for 8 minor releases
and no live consumer paths upgrade across that boundary. The
contract-level deltas are recorded in `../contract_changelog.md`
§§ v0.5.7-v0.5.9; full guide bodies recoverable via git history.

Always check [`../contract_changelog.md`](../contract_changelog.md)
for the full authoritative changelog. Migration guides translate
contract-level deltas into operator-visible upgrade steps.

---

<a id="migration-v0524-to-v060"></a>

# Migration: v0.5.24 → v0.6.0

> **Source craft**: `docs/primordia/_landed/v0_6_x/v0_6_0_unified_evolution_and_thorough_refactor_craft_2026-04-28.md`
> **Style**: operator-visible deltas, Round 4 owner-amended single-shot release.

v0.6.0 is a **MAJOR-class** release per `L0_VISION.md:223-228`
(MAJOR review-cadence trigger). The SemVer label "0.6.0" reads MINOR
externally; Myco's contract semantics override per craft §F1.

---

## TL;DR — operator action items

| Action | Required? | Notes |
|---|---|---|
| Upgrade kernel to v0.6.0 | yes | `pip install -U myco[mcp,adapters]`. |
| Migrate user scripts off v0.5.2 aliases | **yes — break** | All 9 v0.5.2 CLI aliases (`reflect`, `distill`, `perfuse`, `genesis`, `craft`, `bump`, `evolve`, `scaffold`, `session-end`) are REMOVED at v0.6.0. Run `myco-migrate <script>` to auto-rewrite. |
| Canon schema v1 → v2 auto-upgrade | no — automatic | First `myco hunger` after install applies the in-memory upgrade. To persist v2 shape on disk, manually edit `_canon.yaml` (see "Canon edits"). |
| Symbionts host-side artifacts | optional | `myco-install host <client> --with-symbionts` writes deep adapters (rules / commands / recipes). |
| Glama dashboard category | manual once | Owner action; see `docs/primordia/_landed/glama/glama_categories_drive_craft_2026-04-28.md`. |

---

## What's NEW

### Verb #20: `intake`

Bulk-ingest verb composing forage + eat. Replaces the unimplemented
`forage --digest-on-read` flag.

```
myco intake --path docs/research --filter '\.pdf$' --max 50
myco intake --path /tmp/inbox --strict     # exit 2 on any per-file failure
```

Stub IngestResults are written for failures (status: failed,
failure_reason set) — no more silent skips (AD1 dim).

### Subsystem #7: `boundary` (PHYSICAL merger LANDED)

`canon.subsystems` grew from 6 → 7. The 7th subsystem is `boundary`,
**fully physically merged at v0.6.0** per Round 5 owner directive:

- `boundary.surface`           (`src/myco/boundary/surface/`)
- `boundary.install`           (`src/myco/boundary/install/`)
- `boundary.mcp`               (`src/myco/boundary/mcp/`)
- `boundary.host_integration`  (`src/myco/boundary/host_integration/`)

**BREAKING**: the legacy top-level packages `myco.surface` /
`myco.install` / `myco.mcp` / `myco.symbionts` are **removed**. User
scripts that imported these paths must run `scripts/myco_migrate.py`
to rewrite. 201 import-path migrations across 60 files completed
internally; pyproject entry-points updated to canonical form.

### Lint dimensions: 25 → 46

21 new lint dims land at v0.6.0, all at **declared severity** (no
severity-promotion ladder per craft §A5):

- **Mechanical** (12 new): PA2 (megafile LoC), PA3 (surface pure
  adapter), PA4 (core no-subsys), PA5 (meta-subsys layering), SC1
  (canon JSON-Schema parity, HIGH), DC5 (abstract-parent allowlist),
  MF3 (symbiont sig), DI2 (hooks content), AD1 (adapter silent skip,
  HIGH), MP3 (plugin bytecode audit, HIGH), CL1 (sampling gate, HIGH),
  CL2 (OAuth token-residency, HIGH), CL3 (sampling token clear), MF4
  (overlay subsystem validity).
- **Shipped** (1): SH2 (kernel-ahead-of-canon, HIGH).
- **Metabolic** (3): MB4 (sporulated-reabsorbed), MB6 (stale DRAFT
  / distilled, **fixable**), MB7 (resource_watch quota).
- **Semantic** (3): SE4 (reciprocal back-link), RL2 (R3 sense
  discipline), RL3 (R4 eat discipline).

### Fixable extension: 4 → 12

8 dims gain `fixable=True` with `fix()` implementations:

- M1 (canon identity stamping)
- M3 (write_surface advisory)
- DI1 (minimal hooks.json template)
- DC1 (stub docstring with `_AGENT_TODO_DOCSTRING_` marker)
- DC4 (doctrine-ref hint)
- SE1 (advisory; manual edit)
- PA1 (opt-in via MYCO_FIX_PA1=1)
- MB6 (informational at v0.6.0; auto-excrete in v0.6.x)

### MCP capability surface

Beyond `tools`, v0.6.0 adds:

- **resources**: `myco://canon`, `myco://contract`, `myco://notes/...`,
  `myco://docs/primordia/...`. Default redaction hides
  `identity.federation_peers`, `identity.tags`, `system.governance`.
- **prompts**: 20 verb-guides + 2 workflow prompts (`myco-bootstrap`,
  `myco-contract-r1-r7`).
- **sampling** (gated on `canon.system.llm_policy != "forbidden"`):
  enables sporulate / fruit content authoring via host LLM.
- **logging + progress**: long-running ingest sees `notifications/progress`.
- **elicitation**: auto-germ uses `ctx.session.elicit` instead of
  advice strings.

### Streamable HTTP transport + OAuth 2.1

`python -m myco.boundary.mcp --transport streamable-http --host 0.0.0.0 --port
8000 --mount-path /mcp`. Full PKCE + RFC 8707 + JWKS rotation via
`pip install myco[mcp-auth]`.

### Canon schema v2 (auto-upgrade)

Three simultaneous changes:

1. `system.no_llm_in_substrate: bool` → `system.llm_policy: enum`
   with values `forbidden | opt-in | providers-declared`.
2. `identity.federation_peers: []` (forward-compat field).
3. `lint.dimensions` extracted to sibling `_canon_lint.yaml`; main
   canon retains `lint.dimensions_ref` pointer.

The `_v1_to_v2` upgrader auto-applies on first parse — no operator
action required for in-memory upgrade. To persist on disk, edit
`_canon.yaml` per the canon_schema.md v2 layout.

### Governance tiers

`canon.governance` block adds:

- `public_window_min_senesce_count: 7`
- `public_window_min_wall_clock_days: 7`
- `refresh_token_rotation_grace_seconds: 30`
- `last_winnowed_proposals: []`
- `token_redaction_required: true`

Low-risk crafts can land via agent-self-winnow + 7-session-7-day
public window. Owner-veto via `last_winnowed_proposals[].vetoed_at`
always-on.

### 14 host symbiont adapters

`src/myco/symbionts/` (and re-exported at
`src/myco/boundary/host_integration/`) ships 14 host adapters with
`discover/install_basic/install_deep/uninstall` four-function
protocol:

claude-code · claude-desktop · cline · codex-cli · continue-dev ·
cowork · cursor · gemini-cli · goose · jetbrains · openclaw · vscode ·
windsurf · zed.

Run `myco-install host <client> --with-symbionts` to install deep
adapters (rules / commands / recipes / tasks).

### 8 framework demos

`examples/{claude-sdk,langgraph,crewai,dspy,smolagents,agno,praisonai,microsoft-agent-framework}-myco-demo/`
each ship `main.py --dry` smoke + README + (Claude SDK only) `.mcp.json`.

---

## What's REMOVED (BREAKING)

### v0.5.2 CLI aliases — all 9 deleted

| Removed | Replacement |
|---|---|
| `myco reflect` | `myco assimilate` |
| `myco distill` | `myco sporulate` |
| `myco perfuse` | `myco traverse` |
| `myco genesis` | `myco germinate` |
| `myco craft` | `myco fruit` |
| `myco bump` | `myco molt` |
| `myco evolve` | `myco winnow` |
| `myco scaffold` | `myco ramify` |
| `myco session-end` | `myco senesce` |

`src/myco/{genesis,meta}/` deprecation packages deleted. Imports
`from myco.genesis import ...` and `from myco.meta import ...` now
raise `ModuleNotFoundError`.

**Migration tool**: `scripts/myco-migrate <path>` rewrites user
scripts (Python AST + word-boundary regex on `.sh`/`.mk`/`.json`/
`.toml`/`.yml`); markdown prose excluded.

### Severity-promotion ledger

Per craft §A5 owner amendment, the `_canon.yaml::lint.severity_promotion`
table is removed. New dims fire at declared severity from first run
(no 30-session ramp).

---

## Default behavior changes

- `myco immune` now runs 46 dimensions (was 25).
- `myco_intake` MCP tool now appears in `tools/list`.
- `resources/list` and `prompts/list` MCP methods are advertised
  (when `myco[mcp-resources]` extra installed).
- Streamable-HTTP transport advertises `.well-known/mcp.json` Server
  Card.

---

## Validation

```bash
myco hunger              # contract_version: v0.6.0 confirmed
myco immune              # 46 dim run, 0 finding required
myco brief               # 7 subsystems listed (boundary as 7th)
python scripts/verify_mcp_boot.py
python scripts/verify_mcp_capabilities.py
python scripts/verify_install_examples.py
python scripts/verify_server_json.py
```

---

## Rollback

If v0.6.0 introduces an unforeseen regression in your substrate:

```bash
pip install 'myco==0.5.24' --force-reinstall
```

Note that `_canon.yaml` may have been written with v0.6.0 fields
(`identity.federation_peers`, `system.llm_policy`,
`system.resource_redaction`); these are forward-additive and v0.5.24
parsers will warn but continue. The `lint.dimensions_ref` pointer to
`_canon_lint.yaml` is the only field that v0.5.24 cannot resolve;
manually inline the dimensions table from `_canon_lint.yaml` back into
`_canon.yaml` if rolling back.

---

## See also

- `docs/contract_changelog.md` v0.6.0 section.
- `docs/primordia/_landed/v0_6_x/v0_6_0_unified_evolution_and_thorough_refactor_craft_2026-04-28.md`
- `docs/primordia/_landed/v0_6_x/v0_6_0_living_bets_audit_craft_2026-04-28.md`
- `docs/primordia/_landed/glama/glama_categories_drive_craft_2026-04-28.md`
<a id="migration-v074-to-v075"></a>

# Migration: v0.7.4 → v0.7.5

> **Source craft**: `docs/primordia/_landed/v0_7_x/v0_7_5_p0_to_p6_omnibus_craft_2026-05-10.md`
> **Headline**: P0–P6 omnibus closing every gap surfaced in the v0.7.4 retrospective; first real schema migration since v0.6.0.

v0.7.5 is a **PATCH-class** release per `L0_VISION.md:223-228` —
no surface contract is renamed or removed; this guide exists because
two changes are operator-visible at upgrade time:

1. **Canon schema bump v2 → v3** (auto-upgrade; one new optional field).
2. **`scripts/bump_version.py` auto-refreshes `metrics.test_count`
   and `metrics.lint_dim_count`** every molt. The README/canon drift
   loop that bit v0.7.3 ("46 lint dimensions" stale across three
   READMEs while immune ran 50) closes structurally going forward.

---

## TL;DR — operator action items

| Action | Required? | Notes |
|---|---|---|
| Upgrade kernel to v0.7.5 | yes | `pip install -U myco[mcp,adapters]`. |
| Canon schema v2 → v3 auto-upgrade | no — automatic | First `myco hunger` after install applies the in-memory upgrade. The new field is `metrics.lint_dim_count: int \| null`; on a v2 substrate observed cold the value defaults to `null`. To persist the v3 shape on disk, run `myco molt` (which seeds the live count) or hand-edit `_canon.yaml`. |
| Rebuild downstream Cowork plugin | optional | Drag `myco-0.7.5.zip` into Cowork (replaces v0.7.4 entry by `name` key). |
| Rerun `myco immune --json` to confirm zero | recommended | v0.7.5 ships immune-zero on the self-substrate; downstream substrates should re-anchor. |

---

## What's NEW

### Canon schema v3 — `metrics.lint_dim_count`

A single optional field is added to `_canon.yaml::metrics`:

```yaml
metrics:
  test_count: 1568          # already present in v2; auto-refreshed at v0.7.5
  lint_dim_count: 50        # NEW at v0.7.5; auto-refreshed at v0.7.5
```

**Semantics**: the substrate-cited count of registered immune lint
dimensions. It's the SSoT that READMEs and migration docs cite
("Myco runs N lint dimensions"). The v0.7.3 incident — three
READMEs stuck at "46 lint dimensions" while the kernel actually ran
50 — happened because no SSoT existed; agents were citing a
historical doctrine prose paragraph that nobody refreshed when
new dims landed. v3 fixes the loop structurally:

- The `_v2_to_v3_lint_dim_count_field` partial in
  `myco.core.canon` ensures every substrate parses with the field
  present (defaulted to `null`).
- `scripts/bump_version.py` reads the live immune registry and
  rewrites `metrics.lint_dim_count` (and `metrics.test_count`)
  every molt, so the canon never drifts behind reality again.

### `_apply_upgraders` walks to latest

Cosmetic for operators but technically a behavior change: v0.7.4's
`myco.core.canon._apply_upgraders` early-exited at the first version
in `KNOWN_SCHEMA_VERSIONS`, which meant a v1 substrate would lift
to v2 only. With v3 added, that early-exit would have caused v1
substrates to silently skip v3's metrics field. v0.7.5 walks the
chain to the latest registered version (terminates when no further
upgrader exists). All older substrates now lift to v3 in one
`load_canon` call — the "you never migrate again" promise holds
across N≥3 chained versions for the first time.

User scripts that imported `myco.core.canon._apply_upgraders` and
asserted the intermediate v2 shape need an update; otherwise no
operator-facing change.

### `bump_version.py` auto-refresh of metrics SSoT

`scripts/bump_version.py` (wired separately by the v0.7.5 release
engineer, not by anamorph) now reads:

- The pytest collection count → writes `metrics.test_count`.
- The immune dim registry count → writes `metrics.lint_dim_count`.

Before every molt. This means the "next molt" command alone keeps
the canon in sync with reality. No operator action required.

---

## What's BREAKING

**Nothing on the surface contract.** All v0.7.4 verbs, kwargs, exit
codes, and MCP tool names are preserved.

The one internal contract drift is `_apply_upgraders`'s recursion
shape (described above). If you have downstream test code that
asserts `canon.schema_version == "2"` after a v1-canon `load_canon`,
update the assertion to `"3"` (the new latest).

---

## Auto-upgrades (no operator action)

| What | Where | When |
|---|---|---|
| `metrics.lint_dim_count: null` | added to in-memory canon | every `load_canon` call after v0.7.5 install |
| `metrics.lint_dim_count: <int>` | persisted to disk | next `myco molt` (or manual hand-edit) |
| `metrics.test_count: <int>` | refreshed to live count | every `myco molt` (was static before v0.7.5) |
| Schema chain v1 → v2 → v3 | applied transparently | every `load_canon` call when raw canon < v3 |

---

## Manual edits (optional, persists v3 shape on disk)

If you want your `_canon.yaml` to declare `schema_version: "3"`
on disk **before** running `myco molt`:

```yaml
# _canon.yaml — top of file
schema_version: "3"          # was "2"
contract_version: "v0.7.5"   # was "v0.7.4"

metrics:
  test_count: <live count>
  lint_dim_count: <live count>   # NEW; query `myco immune --json | jq '.dimensions | length'`
```

The kernel reads both shapes silently; the in-memory representation
is identical. The only reason to flip the disk shape early is if
your team's editor tooling validates against
`docs/schema/canon.schema.json` and you want IDE autocomplete to
suggest the v3 field.

---

## Default behavior changes

- `myco hunger` continues to print the same pulse JSON; no new
  fields surface to the agent unless the substrate explicitly
  declares `metrics.lint_dim_count`.
- `myco immune` continues to run 50 dimensions (the inventory hasn't
  changed at v0.7.5 — what changed is that the substrate's
  *self-cited* count is now mechanically refreshable).
- `myco molt` now writes `metrics.lint_dim_count` and refreshes
  `metrics.test_count` before bumping `contract_version`.

---

## Validation

```bash
myco hunger                        # contract_version: v0.7.5 confirmed
myco immune                        # 50 dim run, 0 finding required
python -m pytest tests/unit/core/test_canon_schema_upgrader_v2_to_v3.py -v
# all 12 tests pass
python -c "from myco.core.canon import load_canon; from pathlib import Path; \
  c = load_canon(Path('_canon.yaml')); \
  print(c.schema_version, c.metrics.get('lint_dim_count'))"
# expect: 3 <int or None>
```

---

## Rollback

If v0.7.5 introduces an unforeseen regression in your substrate:

```bash
pip install 'myco==0.7.4' --force-reinstall
```

A v0.7.4 kernel reading a v0.7.5-shaped canon on disk
(`schema_version: "3"`, `metrics.lint_dim_count: <int>`) will:

- Emit a `UserWarning` for the unknown schema_version (the v0.5
  forward-compat contract is honoured — no hard error).
- Read `metrics` as an opaque mapping (the unknown
  `lint_dim_count` field is silently preserved in `Canon.metrics`).

Both shapes round-trip cleanly. No data loss on rollback.

---

## See also

- `docs/contract_changelog.md` v0.7.5 section.
- `docs/primordia/_landed/v0_7_x/v0_7_5_p0_to_p6_omnibus_craft_2026-05-10.md` —
  full P0–P6 omnibus.
- `docs/architecture/L1_CONTRACT/canon_schema.md` — schema doctrine
  (extended at v0.7.5 with the v3 additions).
- `tests/unit/core/test_canon_schema_upgrader_v2_to_v3.py` — pinned
  upgrader behavior.
<a id="migration-v07x-to-v080"></a>

# Migration: v0.7.x → v0.8.0

> **Source crafts**:
> - `docs/primordia/v0_8_0_living_bets_amendment_2026-05-10.md` (L0
>   amendment opening v0.8.0 MAJOR; Option B persistence-budget refinement,
>   landed via commit `783da78`).
> - `docs/primordia/v0_8_0_to_v1_0_omnibus_craft_2026-05-11.md` (v0.8.0
>   omnibus authorising the schema bump as item E + remaining v0.8.x
>   work).
> **Headline**: First L0 amendment since v0.4.x. Refines the Living Bets
> wager from analogy-based ("verbs survive like grep") to predictive
> ("verbs survive in proportion to the substrate's persistence budget"),
> and ships canon schema v3 → v4 carrying two additive cache fields
> that mechanise the new wager.

v0.8.0 is a **MAJOR-class** release per `L0_VISION.md:223-228` —
the first MAJOR ratchet that includes an L0 amendment since v0.4.x
(2026-04-15). The MAJOR window opens with this craft and runs through
v1.0; this guide spans the **entire v0.7.x cycle** (v0.7.0 through
v0.7.10) since v0.7.5 was the last MAJOR-class operator-visible
boundary documented.

---

## TL;DR — operator action items

| Action | Required? | Notes |
|---|---|---|
| Upgrade kernel to v0.8.0 | yes | `pip install -U myco[mcp,adapters]`. |
| Read the L0 amendment | recommended | The Living Bets wager wording changed; the conclusion (verbs survive) is preserved but the rationale shifts from analogy to predictive regime classification. See `docs/architecture/L0_VISION.md` § "Appendix — Living bets" + the source craft (`docs/primordia/v0_8_0_living_bets_amendment_2026-05-10.md`). |
| Canon schema v3 → v4 auto-upgrade | no — automatic | First `myco hunger` after install applies the in-memory upgrade. The two new fields are `system.governance.last_living_bets_audit_at: str \| null` and `system.governance.persistence_metrics: { session_count, host_count, peer_count }` (all defaulting to `null`). To persist the v4 shape on disk, run `myco molt` or hand-edit `_canon.yaml`. |
| Rebuild downstream Cowork plugin | optional | Drag `myco-0.8.0.zip` into Cowork (replaces v0.7.10 entry by `name` key). |
| Rerun `myco immune --json` | recommended | LB1 + LB2 dims gain a fast path; immune output should not change in finding-count, but observe wall-clock improvement on substrates with large `docs/primordia/` trees. |

---

## What's NEW

### L0 amendment — Living Bets persistence-budget refinement

The L0 wager appendix was rewritten from analogy-based to predictive.
Old wording (v0.4.x → v0.7.10):

> Verbs survive the way `cp` / `mv` / `grep` survive IDEs.

New wording (v0.8.0+):

> Verbs survive **in proportion to the substrate's persistence
> budget**. The bet wins in multi-session / multi-host / federated
> work where the substrate's persistence budget exceeds any single
> Agent's read window. The bet loses in ephemeral single-session
> work where one Agent can hold the entire problem in context.
> `cp` / `mv` / `grep` analogy is preserved as one supporting
> example, not as the entire bet.

This is the **first L0 amendment since the v0.4.x identity revision**
(2026-04-15). Per L0 § "Changes to this page" governance, it required:

1. A craft doc — `v0_8_0_living_bets_amendment_2026-05-10.md`.
2. Explicit owner approval — recorded inline in the craft (Round 2:
   "选择 B，那么拜托了！").
3. A contract bump — absorbed into the v0.8.0 MAJOR.
4. Cascade review of every lower-layer doc — performed at the
   v0.8.0 atomic bump.

For downstream-substrate operators: the wager wording changed, but
the substrate's commitment to verb-shaped persistence has not. Any
existing substrate's `_canon.yaml` keeps working without edit. The
amendment is most visible to agents reading L0 for decision criteria
(persistence-budget-aware vs context-window-aware work).

### Canon schema v4 — two governance cache fields

Two optional fields are added under `_canon.yaml::system.governance`:

```yaml
system:
  governance:
    # ... existing v0.6.x / v0.7.x governance keys preserved ...

    # NEW at v0.8.0: ISO 8601 marker for the most-recent Living Bets
    # re-audit doc. LB1 dim reads this before falling back to a
    # filesystem walk under `docs/primordia/**/*living_bets_audit*.md`.
    last_living_bets_audit_at: "2026-05-10T14:52:12Z"  # or null

    # NEW at v0.8.0: Cached persistence-budget signals consumed by
    # the LB2 regime classifier. All three sub-fields are nullable.
    persistence_metrics:
      session_count: null    # distinct session_id count from .myco_state/*.jsonl
      host_count: null       # host adapters with write/install evidence
      peer_count: null       # identity.federation_peers cardinality
```

**Semantics**:

- `last_living_bets_audit_at` feeds **LB1** (Living Bets re-audit
  overdue dim, shipped v0.7.5). LB1 currently filesystem-walks
  `docs/primordia/**/*living_bets_audit*.md` at every immune run,
  which is filesystem-O(N). With this field populated, LB1 reads
  the timestamp directly. **Backward compat**: LB1 falls back to
  the filesystem scan when the field is `null` or missing — no
  behavioural break for v3 substrates.

- `persistence_metrics` feeds **LB2** (Living Bets observed-regime
  classifier dim, shipping in the same v0.8.0 wave). Instead of LB2
  re-walking `.myco_state/*.jsonl` for distinct `session_id` values
  + recounting host adapters + peer list every immune call, the
  cached counts are read here. LB2 may either trust the cache (fast
  path) or recompute when the cache age exceeds a TTL (slow path);
  cache-policy lives in LB2, not in the schema.

The `_v3_to_v4_living_bets_audit_marker_field` and
`_v3_to_v4_persistence_metrics_field` partials in `myco.core.canon`
ensure every substrate parses with both fields present (defaulted to
`null`). Per the v0.6.0 narrowness principle (one partial = one
semantic), the two changes ship as independent partials and the
chain order is irrelevant to correctness.

### Upgrader chain extends to v4

The `myco.core.canon._apply_upgraders` chain now walks `v1 → v2 → v3
→ v4` in a single `load_canon` call. The "you never migrate again"
promise from L0 P3 holds across **N=4 chained versions** for the
first time. User scripts that imported `myco.core.canon._apply_upgraders`
and asserted the intermediate v3 shape (e.g. tests pinning
`schema_version == "3"` after a chain run) need an update; otherwise
no operator-facing change.

---

## What's BREAKING

**Nothing on the surface contract.** All v0.7.x verbs, kwargs, exit
codes, and MCP tool names are preserved.

**Nothing on the canon shape.** All v0.7.x canon fields are preserved;
the v4 changes are purely additive under `system.governance`.

The one internal contract drift is the upgrader chain end-state: it
now lands at `"4"` rather than `"3"`. If you have downstream test code
that asserts `canon.schema_version == "3"` after a v1/v2/v3-canon
`load_canon`, update the assertion to `"4"` (the new latest). The
`tests/unit/core/test_canon_schema_upgrader_v3_to_v4.py` regression
suite pins this end-state explicitly.

---

## Auto-upgrades (no operator action)

| What | Where | When |
|---|---|---|
| `system.governance.last_living_bets_audit_at: null` | added to in-memory canon | every `load_canon` call after v0.8.0 install |
| `system.governance.persistence_metrics: { ..., null, null, null }` | added to in-memory canon | every `load_canon` call after v0.8.0 install |
| `system.governance.last_living_bets_audit_at: <iso-8601>` | persisted to disk | next `myco molt` (v0.8.x or later anamorph extension; out of scope for v0.8.0) or manual hand-edit |
| `system.governance.persistence_metrics: { <int>, <int>, <int> }` | persisted to disk | next `myco molt` (or manual hand-edit) |
| Schema chain v1 → v2 → v3 → v4 | applied transparently | every `load_canon` call when raw canon < v4 |
| L0 § "Living bets" wording | already on disk at v0.8.0 self-substrate | downstream substrates inherit on next `myco assimilate` against v0.8.0 doctrine |

---

## Manual edits (optional, persists v4 shape on disk)

If you want your `_canon.yaml` to declare `schema_version: "4"`
on disk **before** running `myco molt`:

```yaml
# _canon.yaml — top of file
schema_version: "4"          # was "3"
contract_version: "v0.8.0"   # was "v0.7.10"

system:
  governance:
    # ... your existing governance keys ...

    # Add the two new v4 fields. Both default to null on cold canons;
    # populate them yourself if you have observed values.
    last_living_bets_audit_at: null
    persistence_metrics:
      session_count: null
      host_count: null
      peer_count: null
```

The kernel reads both shapes silently; the in-memory representation
is identical. The only reason to flip the disk shape early is if
your team's editor tooling validates against
`docs/schema/canon.schema.json` and you want IDE autocomplete to
suggest the v4 fields.

---

## Default behavior changes

- `myco hunger` continues to print the same pulse JSON; no new
  fields surface to the agent unless the substrate explicitly
  declares `system.governance.last_living_bets_audit_at` or
  `system.governance.persistence_metrics`.
- `myco immune` continues to run the same dimension roster (the
  v0.7.10 inventory at 51 dims). LB1 + LB2 gain canon-cache fast
  paths but produce identical findings to their pre-v0.8.0 behavior.
- `myco molt` will (in a v0.8.x extension) refresh
  `system.governance.last_living_bets_audit_at` from the
  filesystem-observed audit-doc state. v0.8.0 itself ships the
  field as canon shape only; the population wiring is out of scope
  for the schema migration.
- `scripts/bump_version.py` continues to refresh `metrics.test_count`
  and `metrics.lint_dim_count` (the v0.7.5 P2 wiring); it does NOT
  touch the new `system.governance.*` fields. That's intentional —
  the v0.8.0 schema bump only adds the field shape; the population
  policy lands in a follow-up work.

---

## Validation

```bash
myco hunger                        # contract_version: v0.8.0 confirmed
myco immune                        # 51 dim run, finding count unchanged from v0.7.10
python -m pytest tests/unit/core/test_canon_schema_upgrader_v3_to_v4.py -v
# all 14 tests pass
python -c "from myco.core.canon import load_canon; from pathlib import Path; \
  c = load_canon(Path('_canon.yaml')); \
  g = c.system.get('governance') or {}; \
  print(c.schema_version, g.get('last_living_bets_audit_at'), g.get('persistence_metrics'))"
# expect: 4 <iso-8601 or None> {'session_count': ..., 'host_count': ..., 'peer_count': ...}
```

---

## Rollback

If v0.8.0 introduces an unforeseen regression in your substrate:

```bash
pip install 'myco==0.7.10' --force-reinstall
```

A v0.7.10 kernel reading a v0.8.0-shaped canon on disk
(`schema_version: "4"`, `system.governance.{ last_living_bets_audit_at,
persistence_metrics }` populated) will:

- Emit a `UserWarning` for the unknown schema_version (the v0.5
  forward-compat contract is honoured — no hard error).
- Read the new `system.governance.*` fields as opaque mapping entries
  (preserved silently in `Canon.system["governance"]`).

Both shapes round-trip cleanly. No data loss on rollback. Note that
the L0 amendment is a doctrine-side change — rolling back the
**kernel** to v0.7.10 does NOT roll back the L0 wording on your
substrate's `docs/architecture/L0_VISION.md`. To revert L0, restore
the file from a pre-`783da78` commit on your downstream substrate.

---

## See also

- `docs/contract_changelog.md` v0.8.0 section.
- `docs/primordia/v0_8_0_living_bets_amendment_2026-05-10.md` —
  L0 amendment + Option B rationale + 5-critic fanout self-rebuttals.
- `docs/primordia/v0_8_0_to_v1_0_omnibus_craft_2026-05-11.md` —
  v0.8.0 omnibus craft (item E authorises the schema bump).
- `docs/architecture/L0_VISION.md` § "Appendix — Living bets" —
  amended wording.
- `docs/architecture/L1_CONTRACT/canon_schema.md` — schema doctrine
  (extended at v0.8.0 with the v4 additions).
- `docs/migration/HISTORY.md#migration-v074-to-v075` — the previous schema-bump
  migration guide (v2 → v3); style template for this one.
- `tests/unit/core/test_canon_schema_upgrader_v3_to_v4.py` — pinned
  v3 → v4 upgrader behavior.
- `src/myco/homeostasis/dimensions/semantic/lb1_living_bets_overdue.py`
  — consumer of `last_living_bets_audit_at`.
- `src/myco/homeostasis/dimensions/semantic/lb2_living_bets_regime.py`
  — consumer of `persistence_metrics`.
