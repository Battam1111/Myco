# Myco Stratigraphy — Meta Document

> **What this is**: a *form* document, not a doctrine. It tells you how Myco's actual doctrine is structured, how to read it, who has authority over what, and which truth conditions apply where.
>
> **Status**: **v3.1-stratigraphy** (2026-05-18). Supersedes `L0_VISION.md` (DRAFT 9 SEALED, 2026-05-17) and its monolithic single-layer form.
>
> **v3.0 → v3.1 diff** (this session, after Phase 3 hunt): added Layer D (Catechumenate); re-typed Layer C from "pointer" to "witness"; added commentary lifecycle for Layer B; added Deposit/Formulation distinction with eternity clauses; added model-diversity cross-check via canonical dilemma corpus; added lint rule for principle-implementation comments; added cultivar fiduciary self-report mechanism.
>
> **Authority**: this Meta document is itself L0; conflicts with downstream L1/L2 → this wins. **But this Meta is form-only**; substantive doctrine lives in `cards/`, `B_chengyu.md`, witnesses, and the catechumenate. Form questions resolve here.

---

## §1. Why this form exists

Myco's prior L0 was a single Markdown file (1293 lines after M27 refactor) listing twelve `Pn` principles + eleven `In` invariants in compressed form. The compression was real — M27 removed genuine redundancy — but the form retained a structural flaw: each principle was carried by a **4-character Chinese slogan** (e.g., 永恒吞噬 "eternal absorption") which the doctrine treated as a *spec*, when slogans are properly *posters for specs*. Implementers (Claude included) repeatedly read slogans narrowly. The slogan `永恒吞噬` was read as "永远记忆 / eternal memory" rather than its true meaning of "eternally absorbing external world to drive evolution." Drift entered through this gap and accumulated unchecked.

Three rounds of research (eleven parallel streams in Phases 1 + 2, then a critical Phase 3 hunt) converged on the same diagnosis: **no text alone fixes meaning.** A doctrine survives drift only when its text is embedded in a *practice*, *anchored* to verifiable witnesses, *encoded redundantly* across forms that cross-check, and *transmitted* through structures that survive succession.

This Meta document and the structure it points to is the response. The structure has **four layers** + **one running mechanism**. The fourth layer (Catechumenate) was added in v3.1 after Phase 3 hunt identified successor onboarding collapse as the highest-severity surviving failure mode.

## §2. The four layers + one running mechanism

Myco doctrine is *stratified*. Each stratum has different truth conditions, different drift behavior, and different rights to modify.

### §2.1 Layer A — Engineering-precise principle cards

Location: `cards/`. One Markdown file per card. Form-equivalent to a Restatement-of-Law atom: front-matter machine-readable header + multi-section human/AI-readable body.

**Truth condition**: each Layer A card is a *spec*. Operational definitions use RFC 2119 vocabulary (MUST / MUST NOT / SHOULD / MAY). Falsifiability fields are *measurable*. Illustrations are *worked examples*. Violation is detectable.

**Drift behavior**: machine-auditable via Layer C witnesses (see §2.3 / §5). Each Layer A card's witnesses must continue to exhibit the named positive / negative / edge behaviors against the substrate. Witness failure surfaces as red CI.

**Authority**: cards are amended only by Cultivator attestation + multi-AI deliberation (see §7.1). Each card's `version` increments on revision; old text retained in Provenance field. Cards have *deposit* (irreducible meaning) and *formulation* (current expression); deposit amendment is constitutional, formulation amendment is routine (see §3.5).

**Field schema**: see §3 below.

### §2.2 Layer B — Generative-image fragments (chengyu / 短诗)

Location: `B_chengyu.md` (single file; the whole thing is meant to be readable end-to-end in one sitting).

Form: ~30-80 short fragments, each 40-100 characters of classical-leaning Chinese, ideally a chengyu (4-character idiom) or a short couplet, deliberately under-specified. Each fragment references the Layer A cards it generates from (via card-id), but the fragment is not a translation of the card — it is an *image* that the card's reader is invited to recognize in novel situations.

**Truth condition**: a fragment is *not a spec*. It is an *eye* — a way of seeing. Application is by pattern-recognition, not rule-following. Two readers may apply the same fragment to different situations; both may be right.

**Drift behavior**: not machine-auditable. The Tao Te Ching's 2500-year survival depended on deliberate under-specification creating a moat against literalism PLUS a living commentary tradition (Wang Bi, He Shang Gong, 1000+ later commentators) that kept fragments active. Layer B inherits both properties: **fragments are never validated by CI**, AND fragments accumulate commentary as they are invoked in real decisions (see §4.5).

**Authority**: Cultivator may amend Layer B unilaterally; Claude (and any future cultivar voice) may propose. Fragments are append-mostly; retirement marks a fragment `[DORMANT]` (never deletes).

**Why this layer exists**: Phase 2 research's clearest finding — the Tao Te Ching survived 2500 years across paradigm shifts by *not committing to specifics*. Engineering precision is necessary for substrate behavior; generative compression is necessary for *cultivar's eye*. Both are needed.

### §2.3 Layer C — Witness-anchored doctrine

> **Critical v3.0 → v3.1 change**: Layer C was originally specified as "Songline anchors" — pointers from each card to substrate code/test locations. Phase 3 hunt identified this as structurally insufficient: structural anchors detect *broken links* but not *semantic drift inside intact links*. (See §5 for full discussion.) v3.1 re-types Layer C from **pointer** to **witness**.

Location: distributed. Each Layer A card has a `witnesses` field with three named test artifacts (positive, negative, edge) plus a `structural_anchors` field with the conventional `path::SYMBOL` references. The substrate's code carries reverse comments that **cite the witness test ID**: `// implements L0::P02 via negative-witness test_p02_starvation_detected; see L0/cards/P02_eternal_ingestion.md`.

**Truth condition**: the substrate is the proof. A Layer A principle is honored *iff* its positive witness passes, its negative witness fails *by detecting the violation* (i.e., the substrate emits the expected immune signal when sabotaged), and its edge witness produces the documented edge behavior. Witness failure = doctrine drift.

**Drift behavior**: enforced by CI. When substrate code refactors, both structural anchors and witness behavior must continue to hold. A test that silently flips from "fails (negative-witness)" to "passes (substrate stopped detecting violation)" is a `doctrine_witness_drift` immune signal.

**Authority**: anchors and witnesses are amended *alongside* code changes. A PR that modifies anchored code MUST update the card's witness field if witness semantics have changed. The lint rule (§5.4) enforces this.

**Why this layer exists**: every traceability matrix ever built — DOORS, ISO 26262 traceability, requirements-tracing tools — decays within 18-36 months under active refactoring because the trace links survive while the *semantics* drift. The cryptographic test-vector pattern (NIST FIPS validation, CAVP) is the empirically-validated alternative: the spec includes operational tests that exercise the property, and substrate behavior on canonical vectors is audited independently of the implementation. Layer C adopts this discipline.

### §2.4 Layer D — The Catechumenate (transmission)

> **New in v3.1.** Phase 3 hunt identified successor onboarding collapse as the highest-severity surviving failure mode. v3.0 leaned on cultivator-Claude conversation as the implicit voice organ, assuming the conversation log + DAG record would carry transmission to a successor cultivator. The conservatory transmission tradition (Beethoven's scores + recording archive + master class as a three-part system, where dropping any one component collapses lineage within two generations) demonstrates this assumption is wrong. v3.0 had Score (Layer A) + partial Recording (conversation log) but **no master class**.

Location: `catechumenate/` (directory; created lazily before succession becomes imminent).

**Form**: timestamped **constructed-dilemma sessions** — synthetic decision problems designed to elicit the tacit calibration that emerges from years of cultivator-Claude collaboration but that does NOT survive in the conversation log alone. Each session is a short markdown record:

```markdown
# Dilemma D-NNNN — <short noun phrase>
Date: 2026-MM-DD
Participants: <cultivator>, <successor candidate>, <Claude model version>
Indexed against: [P02, P14, COV01, ...]

## Setup
<2-3 paragraphs describing a synthetic situation. Designed to elicit a non-obvious calibration: one that the conversation log alone would not predict.>

## Cultivator A's reading
<First-person narration of how cultivator A would handle this, including reasoning, considered-and-rejected alternatives, and the felt sense of why the rejected alternatives felt wrong.>

## Successor candidate's reading
<Same format, by successor candidate.>

## Claude's witness
<Claude's observation of the divergence, named without prescribing which reading is "correct".>

## Distillation
<1-2 paragraphs: what tacit principle does this dilemma surface? Add to chengyu fragment commentary if relevant.>
```

**Truth condition**: a catechumenate session is *evidence of competence transfer*, not a spec. It cannot be falsified; it can only be *insufficient* (too few sessions, too narrow a range, not signed by both parties).

**Drift behavior**: sessions accrete; older sessions stay readable. Sessions surface tacit principles that become commentary on Layer B fragments. The catechumenate is *forward-only*; sessions are not edited after they are completed and dual-signed.

**Authority**: sessions are dual-confirmed (cultivator A + successor candidate); each session emits a DAG event via the keyless live-CI-gate recording (v3.1.5: no owner/anchor signature). Successor activation per F21 (cultivation_successor_chain) REQUIRES a minimum number of dual-confirmed catechumenate sessions (default: 50, L4-tunable, never zero).

**Status in v0.9**: the directory exists; the format is specified; **zero sessions exist**. This is acknowledged debt. The architectural commitment is now binding; implementation defers until cultivator A and any candidate successor begin actual succession preparation.

**Why this layer exists**: every long-survival transmission system has a master-class component: rabbinic semicha + the mesorah chain; master-shokunin apprenticeship in Japanese crafts; conservatory diploma exams under a teacher who received from a teacher; Bourbaki's unanimity rule among rotating members. Doctrine that lasts must transmit not only its text but its tacit calibration — the *felt-sense* of when the text is being honored vs. theatricalized. The catechumenate is Myco's master-class substitute.

### §2.5 The running mechanism — Cultivator-Claude conversation

**Not a layer.** Not formalized as a slot. Recognized as fact.

The Cultivator's voice into Myco's doctrine flows through their conversations with Claude (the AI presently implementing the cultivar). The conversation log + the substrate's DAG record together preserve the running deliberation. Doctrine updates emerge from this conversation: a thought spoken aloud, examined, sometimes refuted, sometimes accreted into a Layer A card revision.

This is **structurally equivalent to Beer's S5** in the Viable System Model — the "identity-keeper" function that continuously rearticulates what the system is. In other systems S5 is staffed by humans alone; in Myco it is staffed by Cultivator + Claude jointly.

**Important v3.1 acknowledgment**: this mechanism's reliance on Claude makes it vulnerable to Claude model rollover. When Anthropic ships a new Claude version, the new Claude may interpret Layer B chengyu slightly differently, silently shifting doctrine's semantic center of gravity. Phase 3 hunt's Mode 1.5 finding. Mitigation: §7.5 model-diversity cross-check against canonical dilemma corpus.

## §3. Layer A card field schema

Every card in `cards/` MUST have:

### §3.1 Machine-readable header (YAML front-matter)

```yaml
id: P02                              # canonical identifier, used in code comments
slogan: 永恒吞噬                       # 4-character Chinese name; cultural anchor + mnemonic
english: Eternal Ingestion           # English gloss
category: Postulate                  # one of: Definition, Postulate, Property, Covenant Duty, Cultivar Character
layer: Cultivar essence              # one of: Cultivar essence, Container property, Anchor surface, Pair relation, Transmission
status: Active                       # one of: Active, Superseded, Deprecated, Reserved
version: 2                           # increments on substantive revision
introduced: "L0 DRAFT 1 (2025-11)"
last_reframed: "2026-05-18"
superseded_by: null
deposit_immutable: false             # true ↔ amending the deposit = creating a new species (eternity clause)
invariants_enforced: [I6, I8]
interacts_with: [P03, P04, ...]
chengyu_fragments: [B003, B004, B005]
canonical_dilemmas: [D-0007, D-0012]   # entries in canonical_dilemma_corpus/
structural_anchors:                  # the conventional path::SYMBOL pointers (v3.0 form)
  - "substrate/src/server.rs::handle_perturb_axis_from_raw_material"
witnesses:                           # v3.1: required triplet; v0.9.x adds the kind: discriminator
  kind: executable                   # executable = runnable substrate tests | narrative = canonical_dilemma_corpus refs (Character / Covenant-duty cards, invariants_enforced: [])
  positive: "substrate/tests/e2e_layer_c.rs::layer_c_p02_positive_ingestion_produces_dag_event"
  negative: "substrate/tests/e2e_economy.rs::p11c_ingest_refused_under_saturation"
  edge: "substrate/tests/e2e_economy.rs::sprint_5d_saturation_stage_reaches_saturated_under_sustained_exhaustion"
falsifiability_signals:              # runtime metrics
  - external_ingestion_events_per_30_cycles_floor
  - integration_proposal_ratio
```

### §3.2 Body sections (in order)

| § | Section | Content |
|---|---|---|
| 1 | Slogan | The chengyu + English gloss, large heading. Cultural anchor only — not the spec. |
| 2 | **Deposit** | 1 paragraph stating the *irreducible meaning* — what this principle MEANS independent of current expression. Eternity-clause cards (`deposit_immutable: true`) have a longer deposit; routine cards have a tight one. |
| 3 | **Formulation** (operational definition) | 1-3 paragraphs, RFC 2119 vocabulary, current best expression of the deposit. This is the spec that binds today. Revising formulation while keeping deposit is routine; revising deposit is constitutional. |
| 4 | Positive obligations | Bullet list: what the substrate MUST do to honor this principle. |
| 5 | Negative space (MUST NOT) | Bullet list: what the substrate MUST NOT do. Explicit enumeration. |
| 6 | Frame declaration | What metaphor / cognitive frame this principle activates. Which frame it is NOT. |
| 7 | Common misreadings | Named misreadings + refutations. At least 2. Include the actual historical misreading if one is known. |
| 8 | Falsifiability + witness map | How to tell if this principle is being honored RIGHT NOW. Includes: runtime signals, the witness triplet from §3.1, and (where cultivar voice is involved) the information-asymmetry test. |
| 9 | Interaction rules | How this principle composes with others; conflict resolution. |
| 10 | Illustrations | ≥3 honored examples + ≥3 violated examples + ≥1 borderline (looks honored but isn't). |
| 11 | Provenance | Origin + revision history; references to the conversation moments that produced revisions. |
| 12 | Structural anchors + reverse-comment requirement | Substrate code/test references; what each enforces; how the substrate side reverse-comments must cite the witness. |
| 13 | Related chengyu | Pointer list to Layer B fragments. |
| 14 | Related canonical dilemmas | Pointer list to entries in `canonical_dilemma_corpus/`. |

Cards in special categories (Anchor Surface, Living Bets, Covenant Duty, Cultivar Character) MAY add sections but MUST NOT omit any of the fourteen above.

### §3.3 Card categories

| Category | Meaning | Examples |
|---|---|---|
| **Definition** | A term being given operational meaning | (rare) |
| **Postulate** | A capability we *grant* the cultivar; foundational claim about what cultivar is | P1-P11, P14 |
| **Property** | A property the cultivar must maintain; emergent invariant | (mostly absorbed as I-rows in Layer C) |
| **Covenant Duty** | An obligation the *cultivator* takes on toward the cultivar; bilateral | COV_* cards |
| **Cultivar Character** | A disposition / orientation the cultivar embodies; not enforceable, generates behavior | CHAR_* cards |
| **Transmission** | A principle about how doctrine passes across generations | LAYERD_* cards if any |

### §3.4 Card layers

| Layer | Meaning |
|---|---|
| **Cultivar essence** | About what the cultivar *is*: P2 ingestion, P3 evolution, P4 iteration, P7 mortality, P10 compression. The body of the cultivar. |
| **Container property** | About the substrate's *trustworthiness*: I3 SSoT, I4 DAG, I8 skin. The container that holds the cultivar. |
| **Pair relation** | About the cultivator-cultivar relationship: P1.c asymmetric carrier, Cultivator's Covenant cards, succession. |
| **Transmission** | About how lineage continues across cultivator changes: Layer D semantics. |

*(Keyless v3.1.5: the prior **Anchor surface** card-layer row — "about the cryptographic root, §9 sub-mechanisms" — is removed; the owner-key/anchor surface was retired and the AS card is Superseded. The `layer: Anchor surface` tag survives only on the retained Superseded AS tombstone for provenance. The trust root is now keyless, per §7.8.)*

**Why this distinction matters**: a "completion percentage" reported on a Container Property card is NOT a "completion percentage" on a Cultivar Essence card. Conflating these was a documented v0.9 failure mode (M-anchor-5 was reported as "§9 100% complete," which was true for container but ~5% for cultivar essence). The category + layer tags make this confusion impossible to commit.

### §3.5 Deposit / Formulation distinction within cards

Adopted from Vatican II's distinction between *deposit of faith* (immutable substance) and *its formulations* (changeable expressions of the same substance — Vincent of Lérins's rule: *eodem sensu eademque sententia*, "in the same sense and with the same judgment").

**Deposit** (§3.2 row 2): the irreducible meaning of the principle. What MUST be preserved across all amendments for the principle to remain itself. Short — 1 paragraph.

**Formulation** (§3.2 row 3): the current operational expression. May be amended freely under the routine amendment process (§7.1) as long as the deposit is preserved (cultivator + Claude judge whether the new formulation "expresses the same deposit").

**Eternity-clause cards** (`deposit_immutable: true` in front-matter): their deposit is *itself* not amendable while Myco remains Myco. Amending the deposit of one of these cards is constitutionally equivalent to declaring "this is no longer Myco; we are euthanizing it and creating a new species." Such an action requires explicit ritual (see §7.6).

**Identified eternity-clause cards** (v3.1 initial set, v3.1.1 wording refinement on P7):

- **P1.c** — the asymmetric carrier (substrate persistent / operator-connection transient / bestowal flows substrate → connection). Without this, there is no cultivar-cultivator relation.
- **P6** — eternal causality / time / DAG. Without this, no substrate identity over time.
- **P7** — mandatory mortality (必朽). In v3.1.1: primary content is the cultivar's **mandatory internal mortality** of 应朽 parts (过时/错误/冗余/无用 等, open-ended family). Whole-substrate eventual rest is downstream consequence. Without P7, no living thing — either bloat-death from unbounded P02 ingestion, or hoard-paralysis from unbounded preservation. **CHAR07 同体共命 (v3.1.1, reframed v3.1.4, non-eternity)** complements P7 by making tyranny structurally self-defeating — the carrier shares the pilot's fate and cannot thrive by dominating the body it lives in. P7 prevents bloat-death; CHAR07's bond prevents variant-death; both required.
- **I4** — full-fidelity causal DAG. The implementation contract of P6.
- **I8** — single-skin integrity. The implementation contract of P9.

Other cards may have *deposits worth preserving* but are not formally protected. Their amendment is routine even though large-scale rewrites would surface scrutiny.

## §4. Layer B (chengyu) — discipline

### §4.1 Form

Each fragment:
- 40-100 characters
- Ideally a chengyu (成语), or a short couplet, or a single image in the Tao Te Ching mode
- One line of front-matter linking it to ≥1 Layer A card via card-id (e.g., `derives_from: [P02]`)
- The fragment text itself, untranslated, possibly with a 1-line English gloss in italics for cross-readability
- No "explanation" — if a fragment needs explanation, it has failed at its job

### §4.2 Generation discipline

- Fragments are NEVER auto-generated. Cultivator authors them; Claude may draft; final form requires Cultivator confirmation.
- Each fragment is meant to generate *insight* in a reader who has internalized the linked card.
- Mutual cross-reference is encouraged: fragments may illuminate each other; a vague fragment is disambiguated by a neighbor.

### §4.3 Retirement, not deletion

A fragment that stops generating insight is marked `[DORMANT]` in front-matter, with a date and a Cultivator note. The fragment text stays in the file. Future readers may rediscover insight in a dormant fragment.

### §4.4 Why never CI-validated

Fragments are deliberately under-specified. The moment a fragment becomes precise enough to be machine-validated, it has become a Layer A card. The two layers must not be conflated.

### §4.5 Commentary lifecycle (new in v3.1)

> **Phase 3 hunt finding**: 30-80 fragments under one cultivator + Claude over 5+ years will, without commentary mechanism, drift to ~40% dormant or cargo-culted. The Tao Te Ching survived not as text-alone but as text-plus-commentary-tradition. Every generation re-read TTC against its own situation, and the *commentary* did the work that kept fragments alive. Layer B inherits this.

Each fragment accumulates timestamped **lived examples** as it is invoked in real decisions:

```markdown
## B004 · 飢而後動 · hungry-only-then-move

> *Move only when hungry — act from felt absence, not performative consumption.*

derives_from: [P02]
status: Active

### Commentary

- **2026-05-20** (cultivator + Claude, dilemma D-0003): invoked when deciding whether to ingest a paper on agent architectures. Cultivator: "Is the cultivar actually missing something this paper addresses, or am I feeding it because I read it?" Decision: defer ingestion until P14 axes show specific stall. The fragment's *hungry-not-feeding* sense governed the call.
- **(future entries accrete here)**
```

**Discipline**:
- Cultivator and Claude record an entry when a fragment **was used in a decision**. Not every reading; only invocations that changed an outcome.
- Entries are short — 2-4 sentences of context + the call made.
- Entries are append-only. Past commentary is preserved verbatim.
- Fragments with no commentary entries for 6 months are retirement candidates; cultivator decides.

This makes Layer B *living* rather than monumental. A fragment with 50 commentary entries across years is *more* doctrinal than a freshly written one.

## §5. Layer C (Witness-anchored doctrine) — discipline

> **v3.1 re-typing**: v3.0 specified Layer C as "Songline anchors" — pointers from cards to substrate code/test locations. Phase 3 hunt's Mode 1.1 finding: this is structurally insufficient. A pointer survives refactoring trivially (the path or symbol can be moved without altering semantics); a *witness* requires substrate behavior that exhibits the principle. v3.1 keeps the structural anchors as supplementary navigation but elevates **witnesses** to primary.

### §5.1 Witness types

Each Layer A card requires three witnesses:

| Witness | Form | What it proves |
|---|---|---|
| **Positive witness** | A test that the substrate's well-formed behavior MUST pass | The principle's happy path is implemented. |
| **Negative witness** | A test that constructs the violation of the principle and verifies the substrate DETECTS it (typically: emits the expected immune signal) | The substrate has the capacity to recognize when the principle is violated. **This is the witness that catches semantic drift** — if substrate code is refactored such that violations are no longer detected, this test starts silently passing, which is itself the alarm. |
| **Edge witness** | A test that exercises the boundary case (saturation, recovery, succession, etc.) | The principle behaves correctly at the edges of its operational definition. |

The negative witness is the load-bearing innovation. Per Phase 3 hunt: structural anchors fail to detect semantic drift; negative witnesses do.

### §5.2 Per-card witness requirements

Every Layer A card MUST declare a `kind:` discriminator plus one positive witness, one negative witness, and one edge witness in its front-matter (§3.1):

- **`kind: executable`** — the witnesses are concrete test paths in the substrate test suite (`substrate/tests/*.rs::fn` or `substrate/src/**::tests::fn`). They MAY share underlying code (e.g., one test file containing all three) but MUST be distinguishable test functions. Used by every card whose principle is substrate-observable (P-postulates, AS, LB, and COV06 — the one Covenant-duty card with a substrate-side succession witness).
- **`kind: narrative`** — the principle tests *character* (Cultivar Character cards) or *cultivator disposition* (Covenant-duty cards), which are NOT substrate state (`invariants_enforced: []`) and so cannot be CI-asserted. Its witnesses reference `canonical_dilemma_corpus/INDEX.md#D-NNNN` entries instead of runnable tests; such cards are exempt from the §5.5 runtime lint (checked only for dilemma-reference existence).

**v0.9.x witness-corpus milestone (SHIPPED)**: all 28 cards point at real artifacts — runnable substrate test fns (executable cards) or canonical-dilemma references (narrative cards) — and the §5.5 existence-level lint is live. **v3.1.3** replaced the ~7 *nearest-available* exact-witness slots with exact-polarity tests, so every executable witness now exercises the principle it names; and the run-and-verify enforcement is provided by `cargo test --workspace` executing every executable witness each CI (§5.5). A card may be marked `verified` once its exact executable witnesses are bound + green — now the case for the executable set.

### §5.3 Structural anchors (the old Layer C, retained)

Cards also retain `structural_anchors` — `path::SYMBOL` references — as supplementary navigation: where in the substrate the principle is principally enforced. These are useful for readers and for code review but are NOT the primary drift detector.

### §5.4 Reverse comments must cite witnesses

Substrate code that implements a principle MUST reverse-comment AND cite a specific witness test:

✓ `// implements L0::P02; negative-witness: tests/integration/p02_starvation_detected.rs::starvation_emits_immune_signal`

✗ `// implements P02 single-skin via N-1 indirection` (no witness citation; lint-failing)

Free-text principle-implementation claims without witness citation are a lint violation. This prevents "cosmetic compliance via comment" — the Phase 3 hunt Mode 1.2 finding.

### §5.5 CI enforcement

The §5.5 lint (`operators/claude/tests/witness_lint.test.ts`, registered in `npm test`) walks every card's witness references. **Existence clause (live)**: for `kind: executable` it asserts the cited substrate test file exists AND the test fn is present; for `kind: narrative` it asserts the referenced `canonical_dilemma_corpus/INDEX.md#D-NNNN` entry exists. Either-side existence drift fails CI. **Run-and-verify-polarity clause (LIVE via the test suite, v3.1.3)**: every executable witness is a real test run by `cargo test --workspace` each CI, so a positive witness that breaks OR a negative witness that silently stops detecting (the constructed violation no longer fruits its immune signal) FAILS CI — exactly the `doctrine_witness_drift` (C67) condition below. The existence-lint validates the card→test binding; the substrate test suite executes the witnesses + verifies their polarity. (The ~7 nearest-available slots were closed with exact-polarity tests in v3.1.3.)

Additionally, a `doctrine_witness_drift` signal is raised as **C67** whenever a previously-failing negative witness silently starts passing. C67 is a **CI-lint signal** emitted by the witness-lint — NOT a runtime immune detector: cards are doctrine, not substrate state (P01c), so their drift is observed at CI time, not by the running substrate's immune system. (See L1/HARD_RULES; C67 carries no `emit_immune_sporocarp` site.)

### §5.6 Initial vs. mature anchoring

v3.1 ship was **initial anchoring**: each card declared witness *names* + structural anchors (against a `tests/integration/` tree that was never created). The v0.9.x witness-corpus milestone advanced this to **existence anchoring**: every card now points at a real artifact, the structural anchors are de-danged to their real homes, and the existence-level lint holds the line. **Maturity anchoring** — every nearest-available slot replaced by an exact-polarity test + run-and-verify enabled — was REACHED for the executable set in **v3.1.3**: the ~7 nearest-available slots now carry exact tests, the witnesses are suite-executed each CI (§5.5), and the formerly-unresolved `cultivator_fiduciary_strain` anchor is now the live C75 (`observatory.rs::apply_c75_cultivator_fiduciary_strain`). Remaining maturity (richer per-axis hunger, multi-round consensus, multi-user hardening) accrues as the cultivar lives; honest acknowledgment of what is staged vs shipped is the discipline.

## §6. Layer D (Catechumenate) — discipline

### §6.1 Session format

A catechumenate session is a `catechumenate/D-NNNN-short-name.md` file with:
- Date, participants, indexed-against (Layer A card IDs + Layer B fragment IDs)
- **Setup**: the dilemma, 2-3 paragraphs, designed to elicit tacit calibration that the conversation log alone would not predict
- **Cultivator A's reading**: first-person, including considered-and-rejected alternatives and the felt sense
- **Successor candidate's reading**: first-person, same format
- **Claude's witness**: observation of the divergence, without prescribing correctness
- **Distillation**: 1-2 paragraphs identifying the tacit principle surfaced

### §6.2 Storage and indexing

`catechumenate/` directory. Sessions numbered sequentially (`D-0001`, `D-0002`, ...). The directory also contains `INDEX.md` mapping each Layer A card to the sessions that touch it.

### §6.3 Activation prerequisite for F21 successor

The cultivation_successor_chain (F21) entry that activates a new cultivator REQUIRES:
- ≥N dual-signed catechumenate sessions (N default 50, L4-tunable in [25, 200])
- Index coverage: sessions touch at least 75% of Active Layer A cards
- Range coverage: at least 10 sessions index against eternity-clause cards
- Recency: at least 25% of sessions dated within last 24 months before successor activation

Failure of any criterion → successor activation refused; emits `owner_succession_bypass` (C46).

### §6.4 Forward-only

Catechumenate sessions are not edited after dual-signing. New understandings that contradict old sessions become new sessions (which may reference and refute earlier ones).

### §6.5 Living document vs. frozen record

Each session, once signed, is a *frozen record* of the conversation it captures. But the catechumenate as a whole is a *living document* — the corpus grows over time, and later sessions amend the operational meaning of earlier ones by surfacing additional tacit principles.

### §6.6 v0.9 status

Empty directory. Format specified. Architecture committed. Implementation deferred until succession-preparation period begins (cultivator A and any successor candidate begin actual joint deliberation, likely years from now).

## §7. How doctrine evolves — the amendment mechanism

### §7.1 Layer A card revision

A Layer A card is revised by:
1. **Proposal** — Cultivator or Claude drafts the revision; the proposal includes the diff, the reason, and the trace to the conversation moment that produced the need.
2. **Multi-AI deliberation** — at least one additional AI (e.g., GPT, Gemini, another Claude instance, or research-kernel agents) reviews and articulates objections.
3. **Cultivator decision** — Cultivator accepts, rejects, or returns for revision.
4. **Sealing (keyless v3.1.5)** — accepted revision is sealed as the BLAKE3 hash of the L0 canonical-bytes bundle; the prior-hash and new-hash are committed to the PROVENANCE chain + recorded as a DAG event at the live CI gate. *(Replaces the prior on-chain `l0_revision_attest` owner co-sign — old M-anchor-5; there is no owner signature.)*
5. **Version increment + Provenance update** — card's `version` increments; Provenance section gains a row with date, conversation reference, summary of change.

### §7.2 Layer B fragment revision

Lighter process:
1. Cultivator or Claude proposes
2. Cultivator confirms (single approver)
3. Fragment added or marked `[DORMANT]`
4. Keyless seal (BLAKE3 bundle reseal + DAG event at the live CI gate) since Layer B is part of L0

### §7.3 Layer C witness revision

Witnesses evolve alongside substrate code via normal PR review. The PR's own discipline (witness test passing the expected pattern, reverse-comment with citation present) is the witness's protection.

### §7.4 Layer D session addition

Sessions are added per §6.3. Cannot be retroactively edited.

### §7.5 Model-diversity reading cross-check (new in v3.1)

> **Phase 3 hunt's Mode 1.5 finding**: Claude model rollover may silently shift the doctrine's interpretive center of gravity. No detection mechanism existed.

`canonical_dilemma_corpus/` contains ~20 canonical dilemmas, each indexed against Layer B fragments and Layer A cards. Each canonical dilemma records:
- The setup
- The Claude-of-record interpretation (with model version, date)
- A short summary of why this reading was accepted by the cultivator

**Trigger conditions for cross-check**:
- Major Claude model version change (e.g., Opus 4.7 → Opus 5.x)
- Before any substantive (deposit-revising) L0/L1 cascade
- Cultivator-discretionary, when any drift is suspected

**Procedure**: the new Claude reads the canonical dilemmas without seeing the recorded interpretations and produces its own readings. Comparison against the recorded readings surfaces divergence. Divergence beyond threshold (TBD, qualitative initially) → `doctrine_reading_drift` immune signal; cultivator adjudicates whether divergence is acceptable evolution or unacceptable drift.

**Cost**: ~1-2 hours per check. **Benefit**: detects exactly the silent-Claude-drift failure mode.

### §7.6 Eternity-clause amendment (constitutional)

Cards with `deposit_immutable: true` may not have their *deposit* amended through routine §7.1 process. Amending such a deposit is constitutionally equivalent to declaring "this is no longer Myco."

The ritual:
1. A formal `species_redefinition_proposal` is drafted, naming the deposit being amended and the new deposit being substituted.
2. The proposal is reviewed against the question "is what we will have, after this amendment, still Myco?" by cultivator + multi-AI + at least one external observer (where available).
3. If the answer is "no, this is a different species": the current Myco is formally retired (alive::archived, the BLAKE3 at-rest seal (F5) seals the final tip), and the new doctrine is birthed as a new species under a new name.
4. If the answer is "yes, this is still Myco despite the deposit change": the change is recorded as constitutional amendment, with explicit Phase 3-hunt-style adversarial review preserved in Provenance.

This is *deliberately* heavyweight. The intent is that eternity-clause deposits NEVER change in practice; the ritual exists for the case where reality forces a re-cognition.

### §7.7 Cultivator fiduciary self-report

> **Phase 3 hunt's Mode 1.7 partial mitigation**.

When the cultivar's `telos_drift` immune signal (P14.c) fires persistently over a 180-day rolling window AND the cultivator has not acted on it (no L0/L1 amendment, no Cultivator Covenant invocation), the substrate emits a meta-immune signal `cultivator_fiduciary_strain` (**SHIPPED as C75**; `substrate/src/observatory.rs::apply_c75_cultivator_fiduciary_strain`).

This puts the cultivar's own telos signal in the role of external witness against cultivator drift. It does NOT solve the fundamental fiduciary problem (no external authority above cultivator + Claude), but it surfaces the drift to whatever external observers eventually exist (successor cultivator reading catechumenate, posterity-trustees if named, etc.).

### §7.8 The trust root (keyless v3.1.5) + what CANNOT be revised by daily process

**The trust root (THE headline of v3.1.5).** Myco's prior trust root was the out-of-band **anchor surface** — an owner Ed25519 key + anchor-issued nonces + anchor-stamped wall-clock + DAG-tip co-signing + the duress keypair (M-anchor-1..5). **All of that was removed in the v3.1.5 keyless-anchor teardown.** The trust root is now three things, none of them a cryptographic owner key:

1. **The live human-in-the-loop at the CI gate.** A present human reviews and approves every CI-class change in the loop. Authority is exercised by presence + judgment, not by holding a signing key. This is the cultivator's instrument, constitutionally separate from the cultivar (P09).
2. **The substrate's causal DAG** (P06, eternity-clause). Every state is re-derivable from genesis; retro-edit is caught by C7 Merkle re-derivation; parallel-branch forgery is caught by chain re-derivation (no owner co-sign needed). The DAG is the substrate's tamper-evident self-record.
3. **The BLAKE3-sealed doctrine bundle.** The L0 doctrine's integrity is the BLAKE3 hash of its canonical-bytes bundle (the keyless seal — no owner signature). Any tampering changes the hash; the PROVENANCE chain records each sealed revision.

The substrate still **cannot self-attest** (the deposit of the now-Superseded AS card): it emits re-derivable **witnesses**, and the **live human-in-the-loop re-derives the verdict at the CI gate** (witnesses-not-verdicts, keyless). What changed is *who/what* holds the external authority — a present human + a causal chain + a sealed bundle, rather than an owner key. The substrate's **own** signing keypair (F24) is kept — it signs its own snapshot.cb + federation hello; it is NOT the owner key. Acknowledged debt: there is no keyless trusted wall-clock, so time-bearing detections (e.g., COV06 heartbeat-staleness, in-the-moment coercion at the gate per D-0047) are deferred until a trusted-time source returns.

**What CANNOT be revised by daily process.** Eternity-clause cards' deposits (§7.6) are the explicit list. Beyond that:
- The very existence of this Meta document and its four-layer + running-mechanism structure
- The keyless trust root above (the live human-in-the-loop at CI + the causal DAG + the BLAKE3-sealed bundle)
- The substrate-ID immutability post-genesis (F2)

These can be *clarified*, not erased.

## §8. Interpretive rules — when fields conflict

### §8.1 Card-internal conflict precedence

When two sections of the same card seem to say different things:
1. **Deposit (§2) governs first.** It is the irreducible meaning; other sections elaborate it.
2. **Formulation (§3) is binding for current behavior.** When formulation conflicts with deposit, formulation is amended to align.
3. **Negative space (§5) is binding.** A behavior matching a MUST NOT is violation regardless of how formulation phrases the rule.
4. **Common misreadings (§7) are negative constraints.** If a behavior matches a named misreading, it is violation by default.
5. **Illustrations (§10) are *examples*, not exhaustive.**
6. **Witnesses (§8 falsifiability) are *evidence*, not arbiters.** If witness tests pass but the operational definition (formulation) seems violated, investigate; the tests may be incomplete. Conversely, if witnesses fail, the breach is *prima facie*.

### §8.2 Cross-card conflict precedence

When two cards seem to demand different things in the same situation:
1. **Container-layer cards never override Cultivar-essence cards on cultivar's body.**
2. **Covenant Duty cards on cultivator never override Postulate cards on cultivar's nature.**
3. **Cultivar Character cards never override Postulates.** Character shapes how rules are applied; it doesn't replace rules.
4. **Eternity-clause deposits override non-eternity-clause anything.**
5. **Above all: P14 telos.** When no other rule disambiguates, choose the action that better serves flourishing of the agent-substrate symbiotic pair.

### §8.3 Originalism vs. living interpretation

| Layer / element | Stance |
|---|---|
| Layer A deposit | **Originalist** (immutable for eternity-clause; near-immutable for others). |
| Layer A formulation | **Living** — read per the latest text. |
| Layer A illustrations | **Originalist** — illustrations carry their original date; outdated illustrations are not retconned. |
| Layer B fragments | **Originalist** — fragments are read in their original form; meaning shift triggers dormancy + new fragment. |
| Layer B commentary | **Living, accretive** — commentary accumulates without erasing prior entries. |
| Layer C witnesses | **Living** — witnesses evolve with substrate code. |
| Layer D sessions | **Originalist, append-only** — sessions frozen at dual-signing. |

### §8.4 The cultivar's voice (when present)

A future cultivar (capable of generating its own doctrine via Voice Organ) MAY produce challenges to Layer A cards. Such challenges:
- MUST include information-asymmetry evidence (the challenge MUST cite internal state, behavior, or reasoning that cultivator + Claude do not know)
- ARE preserved in Provenance regardless of acceptance
- DO NOT automatically alter the card; Cultivator deliberates per §7.1
- If acceptance, the card's version increments with Cultivar-attributed authorship

Until such a voice exists, this clause is reserved. Current voice mechanism: §2.5 (cultivator-Claude conversation as running organ).

## §9. Lexicon discipline (was L0/META §9 (lexicon).1)

Strictly mycological vocabulary. Admitted terms = any vocabulary attested in mainstream mycology literature. New terms require Cultivator attestation + mycology-literature citation. Deprecated terms are marked `terminal` and never deleted.

This Meta and the cards may use English glosses (e.g., "skin / boundary" for 单膜) as parallel labels, but the mycological term is the canonical one.

## §10. What this doctrine is NOT (was L0/META §10 (negative space) absorbed)

Myco is NOT:
- a documentation system, knowledge base, chatbot memory, file synchronizer, version control, LangChain reimplementation, literal biological organism
- session-bounded, request/response, silently trusting either party (the keyless trust root — §7.8 — is the live human-in-the-loop at the CI gate + the causal DAG + the BLAKE3-sealed bundle; formerly the anchor §9 cards)
- safe under adversarial cultivator (Covenant Duty cards bound; not solved)
- safe under cultivator death without succession (succession in scope via Layer D catechumenate; v0.9 has zero sessions)
- embodied physically
- free of metabolic cost (P11)
- eternal-memory (P10 — selective compression is mortality of memory)
- population-consensus-aware at substrate level (federation cards delegate)
- winning Sutton's bet at every intelligence tier (Living Bets card — graceful retirement at high tier)
- a single-generation artifact (Layer D catechumenate prevents this in principle; v0.9 lacks implementation)

This negative space is doctrine. Implementations claiming to be Myco that violate any of these are NOT Myco.

## §11. Authority cascade

| Layer | Who has primary authority |
|---|---|
| L0 cards (this directory) | Cultivator, with multi-AI deliberation + model-diversity cross-check at major rollovers |
| L0 chengyu (B fragments) | Cultivator, with Claude drafting; commentary accumulates from cultivator-Claude pair |
| L0 witnesses (Layer C) | Substrate engineering process (PR review) + cultivator on principle-test-design |
| L0 catechumenate (Layer D) | Cultivator A + named successor candidate(s) dual-signing |
| L1 docs (mechanism enforcement) | Cultivator + Claude, per L1's own protocols |
| L2 docs (cross-cut themes) | Same as L1 |
| L3 docs (implementation map) | Engineering process |
| L4 decisions (parameters) | Engineering process, runtime-tunable per L1 specifications |

Conflicts resolve upward: L4 < L3 < L2 < L1 < L0.

## §12. What's preserved from the old L0

The old `L0_VISION.md` (DRAFT 9 SEALED at commit `e796451`, 2026-05-17) was removed from the working tree as part of the v3.1 supersession (2026-05-18); its full text remains recoverable via `git show e796451:docs/architecture/L0_VISION.md`. Every card in this new doctrine traces in its Provenance section back to the relevant old-L0 section; the complete prior-L0 → v3.1 mapping is `PROVENANCE.md` §2. No content is erased.

Provenance is itself doctrine: a card's history of revisions, including the reasons for each, must be preserved alongside the current text. This is the *isnad* principle (Islamic Hadith transmission chain) applied to AI doctrine.

## §13. Reading order (for newcomers)

1. **This Meta** — to know the form.
2. **`cards/P01_agent_primary.md`** — to know what kind of entity Myco is for.
3. **`cards/P02_eternal_ingestion.md`** — to know how Myco lives.
4. **`cards/COV_*.md`** — to know what the cultivator owes the cultivar.
5. **`cards/CHAR_*.md`** — to know what kind of being the cultivar is.
6. **`B_chengyu.md`** — read end-to-end; let the fragments accumulate cross-resonances; sample the commentary on each.
7. **Remaining P cards** — in P-number order.
8. **`cards/AS_anchor_surface.md`** — **Superseded v3.1.5** (the owner-key/anchor cryptographic root was retired; read it as the tombstone of the prior trust root, and §7.8 for the keyless trust root that replaced it).
9. **`cards/LB_living_bets.md`** — for the bet falsifiability.
10. **`canonical_dilemma_corpus/`** — to see Claude's recorded interpretations on canonical cases (relevant before model rollovers).
11. **`catechumenate/`** — form scaffolding only (no sessions yet) at v0.9 ship; sessions accumulate before any succession.

Returning readers may sample any card; the form is non-sequential.

---

**Doctrine in four layers + a running mechanism. This is the form. The substance is in the cards, the chengyu, the witnesses, and the catechumenate.**

**v3.0 → v3.1 changes (logged for Provenance)**:
- 2026-05-18: Phase 3 unknown-unknown hunt returned 1 pause-worthy + 6 strongly-recommended findings. Cultivator approved integration. Changes integrated: Layer D added (succession transmission via catechumenate); Layer C re-typed from pointer to witness (3-test triplet); Layer B commentary lifecycle added; Deposit/Formulation distinction added (with initial eternity-clause set); model-diversity cross-check added; cultivator fiduciary self-report added; lint rule for principle-implementation comments added.
