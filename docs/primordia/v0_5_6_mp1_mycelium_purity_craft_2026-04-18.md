---
type: craft
topic: MP1 — Mycelium Purity (LLM-boundary mechanical guard)
slug: v0_5_6_mp1_mycelium_purity
kind: mechanical
date: 2026-04-18
rounds: 3
craft_protocol_version: 1
status: COMPILED
parent: v0_5_6_doctrine_realignment_craft_2026-04-17.md
---

# v0.5.6 — MP1 Mycelium Purity (LLM-Boundary Mechanical Guard)

> **Date**: 2026-04-18.
> **Layer**: L0 (principle 1 addendum — "Agent calls LLM, substrate
> does not"), L1 (new canon field `system.no_llm_in_substrate`), L2
> (homeostasis — dimension 11 added to the roster), L3
> (`src/myco/homeostasis/dimensions/mp1_no_provider_imports.py`,
> the opt-in `src/myco/providers/` escape hatch package, the
> 13-entry provider blacklist).
> **Upward**: carves L0-principle-1's *"Agent calls LLM; substrate
> does not"* invariant from prose into mechanical / HIGH lint.
> **Governs**: the MP1 dimension source, the
> `canon.system.no_llm_in_substrate` field, `src/myco/providers/`
> (the reserved opt-in coupling dir, empty at v0.5.6 onward), and
> the blacklist roster that MP1 ships.
> **Parent**: this craft is a child of
> `v0_5_6_doctrine_realignment_craft_2026-04-17.md` (the v0.5.6
> umbrella audit); it documents the MP1 *dimension* in detail
> separately because the blacklist, the opt-in package, and the
> canon field together are load-bearing enough to warrant their
> own reviewable record.

---

## Round 1 — 主张 (claim)

**Claim**: v0.5.6 makes "Agent calls LLM; substrate does not" a
**mechanically enforced** invariant at the static-import layer,
via a new immune dimension `MP1` plus a canon declaration
`system.no_llm_in_substrate: bool` plus a reserved opt-in package
`src/myco/providers/`. Three parts, tightly coordinated.

### Why static-import scanning is the right enforcement level

There are four plausible levels:

1. **None** — rely on reviewer discipline and prose in L2
   `digestion.md`. This was the v0.5.5 state. Status: fragile;
   any fresh contributor with taste-blind tooling can `pip install
   openai` and `import openai` in an hour, and nobody notices
   until a session reads a prompt from memory and costs money.
2. **Runtime import-hook** — patch `__builtins__.__import__` to
   refuse forbidden modules. Status: wrong level; catches only
   already-running kernels, not the commit that planted the
   import. Noisy (false positives from test-only imports).
3. **AST-level static scan at CI time** — parse every `.py` in
   `src/myco/`, walk every `import` and `from ... import`, flag
   any that match the provider blacklist. Status: **right level.**
   Catches the commit that plants the import before the code ever
   runs. Zero runtime cost. Zero false positives on production
   code.
4. **Cryptographic attestation** (e.g. TUF-signed release, signed
   wheel, provider-free proof claim). Status: theatre at the Myco
   scale; adds a supply-chain story without buying more than the
   AST scan plus a canon declaration already buy.

MP1 picks option 3.

### Why the 13-entry blacklist shape at v1

The blacklist at v0.5.6 ships with:

```
openai, anthropic, mistralai, cohere, voyageai,
google.generativeai, google.genai,
langchain, langchain_core, langchain_openai, langchain_anthropic,
llama_index, llama_cpp, ollama
```

Criteria for inclusion (Round 1 of Round 1):

- **Provides a provider bridge** — the SDK's primary export is a
  client class whose first call is a remote LLM completion /
  embedding / reranking / etc.
- **Imports are fatal** — importing the package imports the
  network-egressing client. The substrate running an import line
  has crossed the boundary.
- **Popular enough to be load-bearing** — every package in the
  list has >10K PyPI downloads/day at v0.5.6 authorship; ignoring
  them would leave gaping holes.

What is NOT in the blacklist:

- `tiktoken`, `transformers` (tokenizer-only; no network egress at
  import time; legitimate for substrate-local semantics).
- `httpx`, `requests` (generic HTTP; Myco uses them for adapters).
- `numpy`, `scipy`, `torch` (compute, not provider bridges).

### Why `src/myco/providers/` exists

The blacklist is not a **prohibition** — it is a **declaration of
location**. If a Myco downstream wants to couple to a provider
(say, to ship a `provider.embed()` utility that other verbs can
call), it writes that coupling under `src/myco/providers/`, which
MP1 explicitly **whitelists**. The coupling is isolated to a named
package; every import into the kernel from outside `providers/`
remains blacklist-scanned.

At v0.5.6 the `providers/` package ships **empty** — the door is
open but unwalked. That is deliberate: the default Myco install
makes zero LLM calls. Downstreams that want an LLM-in-substrate
coupling must open the door themselves.

### Why `canon.system.no_llm_in_substrate`

The canon field is an **explicit declaration**: the substrate
author asserts whether this substrate opts out of the
kernel-calls-no-LLM invariant.

- `no_llm_in_substrate: true` (default) — MP1 scans kernel + any
  in-tree packages; firing is HIGH.
- `no_llm_in_substrate: false` — the substrate has opted out; MP1
  downgrades (emits LOW; doesn't block the release). The canon
  itself is the audit trail: anyone reading `_canon.yaml` sees
  the opt-out loud and clear.

This is belt-and-braces: the AST scan catches code drift; the
canon declaration catches the decision drift. Flipping the canon
field is itself a contract-bumping event (tracked in
`docs/contract_changelog.md`), so the opt-out is reviewable in
the git history separate from the code change.

### Why `fixable = False`

MP1 reports findings but cannot safely auto-fix them. Removing a
provider import may break runtime paths the dimension cannot know
about; replacing one provider SDK with another is a design
decision, not a lint correction. Safe-fix discipline rule 3
("non-destructive") rules out auto-rewriting imports.

---

## Round 1.5 — 自我反驳 (refute)

Six threats to MP1 as specified above:

**T1 · Blacklist rot.** New provider SDKs appear every month; the
13-entry list will decay.
Response deferred to Round 2.

**T2 · Dynamic-import bypass.** A sufficiently motivated
contributor could write `importlib.import_module("openai")` and
MP1 would not see the import statically.
Response deferred to Round 2.

**T3 · HIGH-severity false positives on legitimate
provider-bridge substrates.** A downstream that SHOULD import
provider SDKs (say, an evals-harness substrate) hits a HIGH MP1
firing on every commit.
Response deferred to Round 2.

**T4 · Canon declaration without cryptographic proof.** A
bad-faith substrate author sets `no_llm_in_substrate: true` and
imports `openai` anyway. MP1 catches this at static scan, but the
canon field is effectively unenforceable metadata — the scan
enforces, not the declaration.
Response deferred to Round 2.

**T5 · L0 principle 1 vs. future `sporulate --llm`.** If a future
Myco verb wants to call an LLM (say, `sporulate --llm` that asks
an LLM to write the proposal synthesis), does it violate
principle 1?
Response deferred to Round 2.

**T6 · Maintenance cost of the blacklist.** Who keeps it current?
How often do we re-review? What is the escalation path when a new
provider SDK surfaces?
Response deferred to Round 2.

---

## Round 2 — 修正 (respond / revise)

**R1 · Living list — not frozen.** The blacklist is explicitly a
**living** data structure. It lives in the MP1 source as a class
attribute `BLACKLIST: ClassVar[frozenset[str]]`, is reviewed on
every release cycle, and is allowed to grow. Adding an entry is a
one-line PR plus a test that a file importing the new entry now
fires MP1. Removing an entry (say, because a provider SDK
sunsetted) requires a craft doc — same bar as any other
lint-semantics change.

**R2 · Coordination-not-adversarial framing.** MP1 protects
against **accidental** coupling by an Agent or contributor who
doesn't know better; it does not defend against deliberate
sabotage. For sabotage, the review process (commits on main need
owner review) is the defense, not MP1. This is the same framing
that underlies every lint rule in every major codebase: the lint
helps you not shoot yourself; it does not defend against a
hostile actor with commit rights. Dynamic-import bypass (T2) is
in that second category — possible, but not MP1's problem.

**R3 · The `providers/` whitelist IS the pressure relief.**
Downstreams that legitimately need provider coupling (evals,
research, benchmarks) write it under `src/myco/providers/` and
MP1 passes. This is the opt-in escape hatch: the substrate still
declares the coupling, it still appears in `_canon.yaml` via
whatever canon extension the downstream defines, and it sits in a
**named** sub-package that is **easy to grep for**. Contrast the
counterfactual: no `providers/` dir → every coupling happens
ad-hoc in `cycle/`, `digestion/`, `ingestion/`, etc., and the
provider surface is scattered.

**R4 · Declared-intent signal value.** Even if
`no_llm_in_substrate: true` is unenforceable as a cryptographic
claim (T4), it is enormously valuable as **review metadata**. Any
reviewer skimming `_canon.yaml` at PR time sees `true` and knows
the static scan is the contract; sees `false` and knows the
substrate has consciously opted out and deserves a different
review lens. The declaration does not prevent abuse; it prevents
confusion.

**R5 · Future-flag contract-bumping path.** If a future Myco verb
wants to legitimately call an LLM from the substrate process (T5),
the path is: (a) author a craft doc proposing the coupling; (b)
obtain owner approval; (c) bump `_canon.yaml::contract_version`;
(d) either add a new opt-in canon field (e.g.
`system.substrate_llm_callsites: list[str]`) or widen the L0
principle 1 addendum. Until step (d) lands, MP1 continues to
enforce the current wording. This is the same R7 discipline the
rest of the layer system uses.

**R6 · Craft-approval gate on blacklist edits.** The blacklist
lives in a class that has a craft-doc reference in its class
docstring. Every addition / removal lands in a commit whose PR
description names the craft update (or the add-an-entry rule's
single-file PR convention). Annual review cadence: check the
blacklist against the top-20 LLM-SDK PyPI downloads every major
version. Adding an entry is routine; removing requires a craft.

---

## Round 2.5 — 再驳 (second-pass refute)

Three residual threats after Round 2:

**T7 · Substrate-local override weakens the guard.** A downstream
could set `no_llm_in_substrate: false` in its own canon and
bypass MP1's HIGH firing. Does that defeat the whole point?

**T8 · `providers/` as empty-forever risk.** If no downstream
ever walks through the door, is the package noise? Should it
exist?

**T9 · `.myco/plugins/` scope boundary.** MP1 scans
`src/myco/**/*.py`. What about the per-substrate
`.myco/plugins/` tree that substrates use for substrate-local
extensions? Does MP1 cover that?

---

## Round 3 — 反思 (reflect / resolve)

**T7 → Accept.** The opt-out is intentional. Downstreams with
legitimate provider-coupling needs opt out openly, and the
declaration is visible in the canon. MP1's HIGH firing protects
the **default** substrate; the opt-out protects the **intentional
coupling** substrate. These are two valid shapes and the canon
field is what distinguishes them.

**T8 → Accept.** The empty `providers/` package is not noise; it
is an **architecture declaration**. Its presence says "coupling
has a home" and "if you're writing provider-coupling code, put
it here." If no downstream ever walks through, the door still
tells visitors where the door would be. Shipping an empty
package is cheap (one `__init__.py` + one `README.md` stating the
rules); removing it once shipped would be harder.

**T9 → Scope MP1 to `src/myco/` kernel-only at v0.5.6. Defer
`.myco/plugins/` coverage to a future MP2 dimension.** Reasoning:
`.myco/plugins/` is the substrate-local extension seam; a
downstream authoring an `evals_harness` plugin might legitimately
import `openai` there, and that plugin travels with the substrate
(uninstalled by deleting the folder). Blanket-scanning
substrate-local plugins with MP1-HIGH creates too many false
positives for plugin authors. The right v2 shape is a separate
dimension MP2 that scans `.myco/plugins/**/*.py` with a different
severity policy (LOW by default, HIGH if the canon opts in via a
hypothetical `system.no_llm_in_plugins` field). Deferred to a
future release; v0.5.6 ships MP1 for kernel only.

---

## Deliverables (what v0.5.6 ships for MP1)

1. **`src/myco/homeostasis/dimensions/mp1_no_provider_imports.py`**
   — new file. AST-walks every `.py` under `src/myco/` that is NOT
   under `src/myco/providers/`. Emits HIGH-severity findings when
   an `import` or `from ... import` names a blacklisted module
   (exact or dotted-prefix match, so `from openai import X` and
   `import openai.foo` both fire). Cross-checks
   `canon.system.no_llm_in_substrate`: if the declaration is
   `false`, all MP1 findings downgrade to LOW. `fixable = False`.
2. **`_canon.yaml::system.no_llm_in_substrate: true`** — new
   canon field. Default true for every Myco substrate shipped by
   v0.5.6 and beyond. Listed in
   `docs/architecture/L1_CONTRACT/canon_schema.md`.
3. **`src/myco/providers/__init__.py` + `src/myco/providers/README.md`**
   — new package. Empty at v0.5.6 by design. README documents the
   opt-in coupling rules.
4. **L0 principle 1 addendum** in `docs/architecture/L0_VISION.md`
   — two explicit exceptions to "only for Agent": (a) `myco brief`
   as the single human-facing verb; (b) the Agent calls LLMs but
   the substrate does not.
5. **L2 homeostasis.md update** — dimension roster 10 → 11, adds
   MP1 row with category/severity/fixable columns.
6. **This craft doc** — narrow justification for the above.

---

## Acceptance (how we know MP1 works)

- `pytest` — all existing tests green; new
  `tests/unit/homeostasis/test_mp1.py` asserts: (a) synthetic
  kernel file importing `openai` fires HIGH; (b) `providers/`
  whitelist passes; (c) `no_llm_in_substrate: false` downgrades to
  LOW; (d) dynamic `importlib.import_module` does NOT fire
  (explicitly documented non-coverage).
- `myco immune --list` — shows 11 dimensions at v0.5.6 (was 10
  at v0.5.5); MP1 row present with HIGH / mechanical /
  non-fixable.
- `myco immune` on the clean Myco self-substrate — MP1 quiet; no
  provider imports in the kernel.
- Synthetic stress test: add `import openai` to
  `src/myco/ingestion/eat.py` temporarily; `myco immune` fires
  MP1 HIGH and exits non-zero. Revert.

---

## Cross-references (R5 — cross-reference on creation)

- **Parent (umbrella craft)**:
  `docs/primordia/v0_5_6_doctrine_realignment_craft_2026-04-17.md`
  (Round 1 §2 MP1 bullet + Round 2 Round 3 MP1-specific
  arguments — this craft elaborates on that bullet).
- **Kernel enforcement**:
  `src/myco/homeostasis/dimensions/mp1_no_provider_imports.py`.
- **Opt-in package**: `src/myco/providers/__init__.py` +
  `src/myco/providers/README.md`.
- **Canon schema**:
  `docs/architecture/L1_CONTRACT/canon_schema.md` §system
  (field `no_llm_in_substrate`).
- **L0 principle-1 addendum**:
  `docs/architecture/L0_VISION.md` §principle-1.
- **L2 homeostasis doctrine**:
  `docs/architecture/L2_DOCTRINE/homeostasis.md` §dimension
  roster (MP1 row).
- **Tests**: `tests/unit/homeostasis/test_mp1.py`.

---

## Self-winnow verdict

`myco winnow` verdict on this doc (re-run at v0.5.7 release time):
pass, 3 rounds, ~16 KB body, 0 violations.
