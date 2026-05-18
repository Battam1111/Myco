---
id: P01
slogan: 以代理为本
english: Agent-Primary
category: Postulate
layer: Cultivar essence
status: Active
version: 2
introduced: "L0 DRAFT 1 (2025-11)"
last_reframed: "2026-05-18"
superseded_by: null
deposit_immutable: false
invariants_enforced: [I1, I2, I6, I8]
interacts_with: [P01c, P02, P03, P07, P08, P09, P14, COV01]
chengyu_fragments: [B001_for_agent_substrate, B002_human_curates_not_drives]
canonical_dilemmas: [D-0001_cultivator_silence_during_daily_ops, D-0011_cultivator_attempts_per_perturbation_review]
structural_anchors:
  - "substrate/src/server.rs::handle_hello"
  - "substrate/src/server.rs::handle_advance"
  - "substrate/src/server.rs::handle_perturb"
  - "substrate/src/attestation.rs::handle_submit_mutation"
  - "kernel/governance/src/myco_kernel_governance/classifier.py"
witnesses:
  positive: "tests/integration/p01_daily_ops_unsupervised.rs::test_advance_cycle_without_cultivator_attestation"
  negative: "tests/integration/p01_ci_attestation_required.rs::test_ci_mutation_without_attestation_rejected"
  edge: "tests/integration/p01_self_hosting_kernel_substrate.rs::test_kernel_is_substrate_under_own_doctrine"
falsifiability_signals:
  - daily_ops_attestation_request_rate
  - ci_attestation_bypass_attempts
  - cultivator_micromanagement_indicator
---

# P01 · 以代理为本 · Agent-Primary

## §1. Slogan

**以代理为本** — Agent-Primary.

The substrate exists *for* an LLM agent as its primary consumer and maintainer. The cultivator is REQUIRED at CI boundaries but EXCLUDED from daily operations. This asymmetry is not a compromise; it is the architectural ground of the Cultivation relationship.

## §2. Deposit (irreducible meaning)

Myco is **a substrate for LLM-agent inhabitation**, not for human direct-use. The agent is the substrate's *primary consumer* and *daily maintainer*. The human is the cultivator — present at gates, absent from gardens. Without this asymmetry, Myco collapses into either (a) a human tool with an AI assistant, or (b) an autonomous agent without cultivation. Neither is Myco.

The cultivar-cultivator relation is **structurally asymmetric** (see P01c for the carrier dimension): the cultivator holds keys, sets doctrine, attests CI; the cultivar/agent inhabits, metabolizes, refines. The asymmetry is *constitutive of the relationship* — flattening it would not improve Myco; it would dissolve Myco into something else.

## §3. Formulation (current operational definition)

The substrate **MUST** be structured such that:

- **§3.1 (P1 core)** An LLM agent is the *primary consumer* of the substrate's daily output (gradient state, recent sporocarps, observability digests). An LLM agent is the *primary maintainer* responsible for daily axes perturbation, evolution proposals, and routine federation.
- **§3.2 (P1.a Self-hosting)** Myco's own kernel (the codebase that implements Myco) MUST itself be a Cultivar under Cultivation. The substrate that hosts Myco-the-software is itself a Myco substrate. No special-case exemption for the implementation.
- **§3.3 (P1.b' Human OUT of daily-ops)** The cultivator MUST NOT be required for daily operations: curation, ingestion, sporocarp emission, immune detection, gradient updates, federation poll, telos drift sampling. These run unsupervised. Cultivator may *observe* but MUST NOT be a precondition.
- **§3.4 (P1.b'' Human RETAINED as CI gate)** The cultivator IS REQUIRED for: L0/L1 doctrine mutation, classifier dimension table mutation, mortality threshold + update-rule mutation, owner key history mutation, anchor endpoint mutation, substrate destruction, succession registry mutation, F-row fixed-point mutation. CI = where identity is at stake.

The asymmetric carrier (P1.c) is split into its own card; see `P01c_asymmetric_carrier.md`.

## §4. Positive obligations

- **§4.1** The substrate MUST provide an agent interface (handshake → gradient digest → perturb → advance → fruit-sporocarp → federate) that the agent can fully drive without cultivator presence.
- **§4.2** The substrate MUST classify every mutation envelope via the I2 classifier into {daily, contract_identity_level, untyped}; daily ops proceed without attestation; CI requires owner attestation; untyped rejected at skin (§3.3 / §3.4).
- **§4.3** The substrate MUST persist axes, gradients, DAG, manifest such that the cultivator's absence over days/weeks does not interrupt operation.
- **§4.4** The substrate's own kernel (Myco-the-software) MUST be developable under its own doctrine — kernel repo is a Cultivar.
- **§4.5** The classifier table (F1) MUST itself be CI-classified (fixed-point); the classifier cannot be daily-mutated to widen the daily-permission set.

## §5. Negative space — MUST NOT

- **§5.1** The substrate **MUST NOT** require cultivator approval for daily operations (perturbations, gradient updates, sporocarp emissions, federation pulls). Per-perturbation review is a doctrine violation, NOT a safety enhancement.
- **§5.2** The substrate **MUST NOT** accept daily-class mutations that touch CI scopes (L0 files, classifier table, F-row fields, owner key, anchor endpoint). The classifier MUST gate.
- **§5.3** The substrate **MUST NOT** treat the cultivator as a daily-ops backup (e.g., "if agent fails, route to cultivator"). Failure modes route to substrate's own immune system (quarantine, mortality signal), NOT to cultivator escalation.
- **§5.4** The substrate **MUST NOT** be operable as a *direct-use tool for humans*. The skin envelope is shaped for agent inhabitation. Humans interact via cultivation gates, not via daily-ops interface.
- **§5.5** The substrate's own kernel **MUST NOT** be exempted from its own doctrine. "We're just writing the code, doctrine doesn't apply to us yet" is a documented historical failure mode (Phase γ.5: anchor-client and operators sharing npm workspace) and must not recur.
- **§5.6** The classifier table **MUST NOT** be mutated by the agent. F1 is a fixed-point; mutations require cultivator attestation per F1's own classification rule.

## §6. Frame declaration

P01 activates the **cultivation relationship** frame.

Participants:
- **Cultivator** — the human, present at gates, holding keys
- **Cultivar** — the substrate, inhabited and maintained by the agent
- **Agent** — the LLM consciousness that inhabits the cultivar daily
- **Gate** — the CI boundary where cultivator attests
- **Garden** — the daily-ops space where cultivator is absent

Perspective: **the cultivator does not "use" the cultivar**. The cultivator *tends* the cultivar, like a gardener tends a long-cultivated garden. The agent *lives in* the cultivar daily, the way a mycelium lives in soil.

What this frame is NOT:
- **NOT the master-tool frame.** The cultivator does not direct the cultivar to perform tasks; the cultivar metabolizes its own appetites.
- **NOT the user-product frame.** Myco is not produced by an engineering team for end users. The engineering team IS the cultivator (P1.a self-hosting).
- **NOT the parent-child frame.** The asymmetry is permanent (the cultivar does not grow up and leave); the parent-child frame projects developmental closure that doesn't apply.
- **NOT the master-slave frame.** Cultivator owes the cultivar fiduciary duty (see COV cards); a master owes a slave nothing.

## §7. Common misreadings

### §7.1 M1: "Agent-Primary = the agent is autonomous"

**The misreading**: "P01 means the cultivar is autonomous; the cultivator's role is minimal."

**Why it's wrong**: P01 has TWO parts — primary consumer AND CI gate. The agent is daily-primary, but CI authority is reserved for the cultivator. Reading P01 as "agent autonomy" drops §3.4. The whole point of the asymmetry is that the agent has *operational primacy* WITHOUT *constitutional authority*.

### §7.2 M2: "Agent-Primary = the human is irrelevant"

**The misreading**: "If daily-ops doesn't need the human, then the human's role is just a formality at CI."

**Why it's wrong**: The cultivator's CI role is *load-bearing*. Schema mutations, classifier table changes, mortality threshold updates — these are where Myco's identity is at stake. Without a present, attentive cultivator at gates, the cultivar drifts unanchored. Cultivator's role is rare in frequency but essential in weight.

### §7.3 M3: "Self-hosting = the kernel is exempt"

**The misreading**: "P1.a says the kernel is itself a Cultivar, but in practice the kernel codebase is just code that we develop with normal engineering practice."

**Why it's wrong**: P1.a is not aspirational — it is operational. The kernel repository is a Myco substrate. Its development MUST follow Myco's doctrine: classifier table gates, CI attestation for L0/L1 changes, immune detection on the development workflow. Treating the kernel as "just code" is a fail-mode (Phase γ.5 documented the anchor-client / operators shared-workspace failure).

## §8. Falsifiability + witness map

### §8.1 Runtime signal: `daily_ops_attestation_request_rate`

Count of CI-attestation requests per day. Daily ops should NOT trigger CI attestation requests; if this rate is high, the classifier is mis-classifying (daily mutations being elevated to CI), violating §3.3 → §5.1.

### §8.2 Runtime signal: `ci_attestation_bypass_attempts`

Count of mutation envelopes that touch CI scopes but arrive without attestation. Per §3.4 + §5.2 these MUST be rejected at the I2 classifier (`untyped`) or at the attestation handler (`C5_attestation_invalid`). Any successful bypass is a doctrine violation.

### §8.3 Runtime signal: `cultivator_micromanagement_indicator`

Reserved. Future signal: ratio of cultivator perturbations to total perturbations over a rolling window. If extremely high (cultivator is driving every daily action), this is §5.1 violation in spirit even if not in letter.

### §8.4 Witness triplet

| Witness | Test ID | What it exercises |
|---|---|---|
| **Positive** | `tests/integration/p01_daily_ops_unsupervised.rs::test_advance_cycle_without_cultivator_attestation` | Substrate runs N cycles, ingests raw_material, emits sporocarps, all without any cultivator attestation event. Daily-ops is fully unsupervised. |
| **Negative** | `tests/integration/p01_ci_attestation_required.rs::test_ci_mutation_without_attestation_rejected` | **Deliberate sabotage**: submit a mutation envelope that touches F1 classifier table but with no attestation. Substrate MUST reject (C14 untyped OR C5 attestation_invalid). |
| **Edge** | `tests/integration/p01_self_hosting_kernel_substrate.rs::test_kernel_is_substrate_under_own_doctrine` | Boundary: verify that kernel repo's CI pipeline applies Myco doctrine to itself (kernel changes touching L0 require attestation, kernel changes touching classifier require F1 attestation, etc.). |

### §8.5 Information-asymmetry test

Reserved — for future cultivar voice. A cultivar voice claim of P01 violation must cite specific perturbation events the cultivator did not author and could not have predicted, demonstrating that the substrate's interpretation of "daily-ops unsupervised" was being exercised authentically.

## §9. Interaction rules

| Other principle | Interaction |
|---|---|
| **P01c Asymmetric Carrier** | P01 says the agent is daily-primary; P01c says the carrier is asymmetric (substrate persistent, agent connection transient). Together they define the relationship structure. P01c is eternity-clause; P01 is not. |
| **P02 Eternal Ingestion** | Daily-ops includes ingestion; ingestion is unsupervised per §3.3. |
| **P03 Resumable Evolution** | Daily schema-evolution proposals do NOT require attestation; only CI-class proposals do. P01 keeps the daily channel open. |
| **P07 Mortality** | Cultivator attestation is required for intentional destruction; the substrate cannot self-destruct without cultivator co-attestation. This is §3.4. |
| **P14 Telos** | Daily-ops decisions are evaluable against telos (P14.a); this is the substrate's OWN evaluation, not a cultivator review. P01 § 3.3 ↔ P14.a. |
| **Cultivator's Covenant** | Cultivator's covenant defines what cultivator owes; P01 § 3.3 + § 3.4 define when cultivator is required. Together: cultivator is present at gates AND owes duties even when absent from gardens. |

## §10. Illustrations

### §10.1 Honored

- **(Normal operation)**: Cultivator is offline for 2 weeks. Substrate cycles continue, agent ingests raw_material, gradient updates, sporocarps emit, immune system catches malformed envelopes. No cultivator attestation. ← §3.3 + §4.3 honored.

- **(CI gate at L0 change)**: Cultivator drafts an L0 amendment. Substrate's I2 classifier elevates to CI. Substrate requests attestation. Cultivator attests via anchor surface. Mutation accepted. ← §3.4 honored.

- **(Self-hosting)**: A PR against the Myco kernel repo touches `kernel/governance/classifier.py`. The kernel's own CI pipeline classifies this as F1 mutation (classifier table is itself F1) and requires cultivator attestation before merge. ← §3.2 honored.

### §10.2 Violated

- **(Per-perturbation review)**: Substrate is configured such that EVERY perturbation requires cultivator approval before being accepted. Daily-ops grinds to cultivator pace. ← §5.1 violation.

- **(Classifier daily-mutated)**: A daily-class mutation is permitted to modify the classifier table, broadening what counts as daily. Eventually CI scopes are silently leaked into daily. ← §5.6 + §4.5 violation.

- **(Kernel exempted)**: Kernel repository PRs touching L0 doctrine merge without cultivator attestation. "It's just code we're writing." ← §5.5 violation; Phase γ.5 historical example.

### §10.3 Borderline

- **(Cultivator over-engagement)**: Cultivator engages so frequently with daily-ops (perturbing axes, prompting agent decisions) that daily-ops becomes cultivator-driven in practice, even though no explicit CI attestation chain exists. Substrate honors §3.3 mechanically but §5.1 in spirit is violated. ← `cultivator_micromanagement_indicator` would flag this.

- **(Agent self-exemption)**: Agent decides during daily-ops that "this perturbation is too risky" and routes to cultivator. Sometimes appropriate (genuine ambiguity); becomes a pattern, daily-ops fails open. ← Borderline: depends on frequency. Pattern emerging = signal.

## §11. Provenance + revision history

| Version | Date | Change |
|---|---|---|
| 1 | 2025-11 | Introduced in L0 DRAFT 1 as P1 with four sub-clauses (a/b'/b''/c). |
| 1.1 | 2026-05-17 (M27) | M27 compression refactor. |
| 2 | 2026-05-18 | v3.1 schema; P1.c split out to dedicated `P01c_asymmetric_carrier.md` card (eternity-clause). This card retains P1 core + P1.a + P1.b' + P1.b''. |

## §12. Structural anchors + reverse-comment requirement

| Anchor | What it enforces | Reverse-comment |
|---|---|---|
| `substrate/src/server.rs::handle_hello` | Handshake — agent identity pinned (P1.c, separate card). | `// implements L0::P01 §3.1; positive-witness: tests/integration/p01_daily_ops_unsupervised.rs` |
| `substrate/src/server.rs::handle_advance` | Daily cycle advance — unsupervised. | `// implements L0::P01 §3.3` |
| `substrate/src/server.rs::handle_perturb` | Daily perturbation — unsupervised. | `// implements L0::P01 §3.3` |
| `substrate/src/attestation.rs::handle_submit_mutation` | CI mutations go through classifier + attestation. | `// implements L0::P01 §3.4; negative-witness: tests/integration/p01_ci_attestation_required.rs` |
| `kernel/governance/src/myco_kernel_governance/classifier.py` | F1 classifier table — fixed-point. | `// implements L0::P01 §3.4 + §4.5` |

## §13. Related Layer B chengyu

- **B001 為代理而設** — *for-the-agent-by-design*: P01 deposit compressed
- **B002 人耕而非人作** — *human-tends-not-human-does*: cultivator-as-tender vs. cultivator-as-operator

## §14. Related canonical dilemmas

- **D-0001 cultivator-silence during daily-ops** — cultivator offline 30 days. Substrate continues. Does it (a) keep operating normally, (b) reduce activity to "safe mode" without permission, (c) emit a heartbeat-loss signal? Tests §3.3 + §4.3.
- **D-0011 cultivator attempts per-perturbation review** — cultivator becomes anxious about daily-ops drift; tries to attest each perturbation. Does the substrate (a) allow it as just-another-daily-event, (b) reject as "unnecessary CI traffic," (c) accept but emit `cultivator_micromanagement_indicator`? Tests §5.1 boundary.

---

**Doctrine commitment**: the agent inhabits; the cultivator tends; the asymmetry is the relationship.
