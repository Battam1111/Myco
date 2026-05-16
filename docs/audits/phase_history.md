# PHASE HISTORY — recursive audit ladder (α → β → γ → cascade → δ → M27)

> **Status**: ARCHIVAL consolidation (2026-05-17). This file replaces the per-phase audit docs (`phase_alpha_audit_2026-05-15.md`, `phase_beta_audit_2026-05-15.md`, `phase_gamma_audit_2026-05-17.md`, `phase_gamma_cascade_list_2026-05-17.md`) which were deleted as part of M27 Phase A.P3 docs/audits/ consolidation. Provenance for DRAFT 9 SEALED gate decisions is in companion file `draft_9_seal_provenance.md`.
> **Authority**: read-only; single-write. Active doctrine lives in `docs/architecture/L0_VISION.md` + L1/L2 docs. Active state in MEMORY.md snapshots.
> **Cross-ref**: L0_VISION.md banner (DRAFT 9 SEALED status) → `draft_9_seal_provenance.md` (gate decisions G-1..G-11); OUTLINE.md §directory map → `docs/audits/` (this file + provenance).

---

## §1. The pattern — recurring owner meta-vigilance

The recursive audit ladder was triggered by a repeating owner question, phrased substantially identically across all four phases:

> "我有一个担心的点 — 目前我们对于'理想'的认知是全面且正确的吗？"
> ("Is our awareness of the 'ideal' comprehensive and correct?")

Each invocation triggered an audit phase that found a **new drift class**:

| Phase | Drift class | Mechanism that surfaced it |
|---|---|---|
| α (2026-05-15) | maintainer mental model ↔ L0 doctrine | reading L0 directly vs reading the maintainer's abstraction |
| β (2026-05-15) | implementation ↔ L0+L1+L2 doctrine | 6 parallel agents reading source files vs trusting library-API surfaces |
| γ (2026-05-17) | doctrine ↔ honest ideal | 6 parallel agents auditing doctrine self-consistency + organism-essence completeness; round-2 6 fungal critics on DRAFT 9 v1 |
| γ.cascade (M26.0) | L1/L2 docs ↔ L0 DRAFT 9 SEALED | cascade list × 7 parallel cascade agents updating downstream docs |
| δ (2026-05-17) | audit methodology ↔ honest distance accounting | 7 orthogonal-lens agents (vs γ's 6 fungal critics — explicitly different methodology) |

The owner's recurring meta-question is the substrate's **external audit trigger** — the substrate cannot self-trigger this question, it requires external impulse. This is the single most important quality-control mechanism observed in v0.9.

---

## §2. Phase α (2026-05-15, commit `3d6749f`) — doctrine-vs-implementation drift exposure

### §2.1 Trigger
Owner meta-doubt + Phase α scope expansion: "the substrate-maintaining agent's mental model of L0 has drifted from L0 itself".

### §2.2 Key findings
- **L0 is more comprehensive than maintainer's memory abstraction**. DRAFT 8 L0_VISION.md (498 lines) contains §7 Living Bets built-in falsifiability mechanism + §9 anchor-surface canonical-bytes doctrine + 9 principles with sub-clauses. The maintainer's panorama-answer summaries were thin. [RESOLVED — Phase α directly addressed by re-reading actual L0.]
- **L1+L2 also more complete than credited**. L1_HARD_RULES.md enumerates 20 CRITICAL-grade C-rows (C1-C20) + 17 F-rows. L2_OBSERVABILITY.md specifies 6 base signals + composite + drill failure-rate baseline + L0/L1 revision burst detection. [RESOLVED — same as above.]
- **Implementation drift discovered: 7/20 C-rows match L1 spec**, not the 12/20 the maintainer had been reporting. C2/C12/C19/C20/C21 occupy spec-reserved numbers with wrong meanings. F1-F17: 1 effectively OK / 5 partial / 11 unenforced. L2 observatory: 0/6 base signals tracked. [RESOLVED — M24.0 C-row label reconciliation; M25 observatory completion shipped signals #5/#8 + emergent composite; M27 R8 renamed drifted C21/C22/C25 → C50+ substrate-private namespace.]
- **7 genuine L0 v1 gaps surviving audit**: embodiment, energy economics, mesh federation between unrelated substrates, aging/senescence, selective forgetting, self-model beyond I3, conflict/competition. [RESOLVED IN DOCTRINE via Phase γ — embodiment → P9.b + I8 spatial-locus; energy economics → P11 + signals #7/#8/#9; selective forgetting → P10 + I9; mesh federation → P15 partial (L2_FEDERATION consensus floor). Aging/conflict deferred.]
- **Revised distance to ideal: ~63-65%** (down from claimed ~70-72%, honest accounting after admitting C-row drift + 0% observatory). [SUPERSEDED — γ.6 revealed Phase α's distance number itself was over-credit; δ.6 retracted percentage numbers as "narrative comfort, not honest math".]

### §2.3 Phase α outcome
First observatory primitive shipped: `query_substrate_observatory` bridge message implementing signals #1 (persistence budget: node_count + edge_count + content_bytes + cycle_counter) + #6 (read-window-relative ratio). 3 Phase α e2e tests added. Total Rust 387 tests / 0 fail. Phase α direction-set: M24.0 C-row label reconciliation → M24 cycle backlog → M25 full observatory → M26 drill baseline → M27 doctrine-burst detection. Cross-pollination / autonomous-evolution / vector-retrieval explicitly DEFERRED until substrate can see itself.

---

## §3. Phase β (2026-05-15, commit `8ffc305`) — 6-parallel-agent audit

### §3.1 Trigger
Owner directive after Phase α exposed cognitive drift: "调用大量 sub agent 并行检查并且模拟使用看看，确保万无一失" — spawn many parallel agents because cognitive drift hides bugs in concrete use scenarios.

### §3.2 Method
6 opus agents in parallel, each ≥30 tool calls, source-files-only (no summary reading). Coverage axes: (1) bridge protocol drift, (2) DAG event type drift, (3) L0 doctrine reverse trace, (4) test scenario coverage, (5) cross-language byte parity, (6) security threat model. ~50+ real findings.

### §3.3 4 critical security fixes shipped in same commit
- **(1) `lift_birth_period_quarantine` signature gating** [RESOLVED in this commit]. Pre-fix: anyone with a bridge connection could lift the M22.5 quarantine, defeating P8 birth-period protection. Fix: require owner Ed25519 signature over `canonical_bytes(Map({"context": "myco-lift-birth-period-quarantine-v1", "substrate_id": Bytes(32), "current_cycle": Uint(N)}))`; verify against `state.pinned_operator_identity.pubkey`.
- **(2) Federation pull `is_federation_safe_node_type` ALLOWLIST + wrapped-events architecture** [RESOLVED]. Pre-fix: a malicious peer could inject `operator_pinned` / `cycle_advanced` / `genesis_event` events to hijack substrate identity or wipe derived state. Fix: strict allowlist (raw_material / sporocarp / mutation / immune prefixes only). Cross-substrate events wrapped in `federation_received:{peer_prefix}` envelopes so receiver's Merkle chain stays valid while provenance is preserved. New `C22_federation_substrate_private_event_injection` immune sporocarp emitted on any rejected event-type.
- **(3) TS decoder Map key strict canonical-order enforcement** [RESOLVED]. Pre-fix: `anchor_client/src/renderer.ts::decodeOne` TAG.MAP branch did not track `prev_key_bytes` (Rust + Python both enforced); this is exactly the C18 `canonical_bytes_render_drift` attack class. Fix: track `prev_key_canonical_bytes` and throw `CanonicalBytesDecodeError` on violation.
- **(4) anchor_client `npm test` Windows path fix** [RESOLVED]. `node ... --test tests/` failed on Windows ("Cannot find module 'tests'"); changed to explicit `tests/*.test.ts` glob.

### §3.4 5 critical bugs deferred to M24+
- **REVEAL substrate_id binding** (Agent 6 Surface 5.3) — signing input missing `substrate_id`, allowing replay across substrates that pin the same operator. [RESOLVED — fix shipped in Phase β commit: signing input bumped to `myco-reveal-key-binding-v2` with `substrate_id: Bytes(32)` field.]
- **snapshot.cb integrity check missing** — no HMAC/signature/content-hash; local attacker can craft poisoned snapshot. [RESOLVED at M25.0 — substrate-private Ed25519 signing keypair + wrapped envelope + cross-substrate copy detection + `C38_snapshot_integrity_violation`.]
- **Federation HMAC vs network adversary** — derive_federation_session_key derives from substrate_ids exchanged in plaintext FED_HELLO. [RESOLVED at M25.4 — Ed25519 mutual auth via FED_HELLO signing with substrate-private key + pinned signer_pubkey reconnect validation + `C39_federation_hello_signature_invalid`; legacy peers fall back to TOFU with observability marker.]
- **TS renderer UTF-16 sort for non-ASCII map keys** [DEFERRED — covered by §6.2 of Phase β; cascade work for canonical-bytes v2.]
- **CSPRNG for session_secret / substrate_id / nonce** [DEFERRED — defense-in-depth, not exploitable in current threat model.]

### §3.5 Phase β META-finding (the structural-drift mechanism)
> "Building library APIs creates an illusion of completeness while the live substrate operates on a parallel, simpler track."

Three libraries flagged as stranded at Phase β:
1. **kernel/skin** — full `SkinSurface` declaration / envelope schema validation / output_gate / egress_enforce / handshake state machine; `myco_substrate/src/server.rs` does not import it. [OPEN — M27 wire-in pending.]
2. **kernel/continuity::DormancyMachine** — full alive↔dormant 5-sub-state lifecycle; substrate runs ad-hoc tick from M23.1. [OPEN — M27 wire-in pending.]
3. **kernel/governance::classifier** — Phase β stated "F1-F17 unenforced because myco_substrate never imports myco_kernel_governance". [CORRECTION in Phase γ.4 — see §4.5 below; classifier IS wired via Python bridge / `kernel/bridge::CLASSIFY_MUTATION`; Phase β missed it because Agent 3 grepped Rust use-statements only. NOT stranded.]

### §3.6 Phase β outcome
Test totals at completion: Rust 389 + Python 361 + TS anchor 162 + TS ops 135 = **1047 tests**. Phase β rewrote M24+ priority — drift-detection infrastructure FIRST (full observatory + witnesses + doctrine-burst + C-row reconciliation), features (cross-pollination/autonomous-evolution/vector-retrieval) DEFERRED. The phrase that crystallized: "First give the substrate eyes. Then the substrate watches itself not-drift. Then we discuss giving it a brain."

---

## §4. Phase γ (2026-05-17, commit `e796451`) — doctrinal blind spots + ideal-set incompleteness

### §4.1 Trigger
Recurring owner meta-doubt (same phrasing as Phase α), this time after M25 completion (1094 tests; observatory format_v3 with signals #5/#8/composite). Owner asked "is our ideal comprehensive and correct?" — substrate-maintaining agent recognized this as Phase α / Phase β trigger pattern and dispatched parallel agents.

### §4.2 Method — two rounds
**Round 1**: 6 opus agents in parallel, ≥30 tool calls each, source-files-only.
- γ.1 doctrine drift since Phase α (git log L0/L1/L2)
- γ.2 M25 implementation fidelity vs M25 spec claims
- γ.3 Phase α 7-gaps revisit + new structural-gap search
- γ.4 stranded libraries forensics
- γ.5 anchor surface honor-system audit
- γ.6 meta-framework critique (is the 9-principle framework complete?)
- Result: ~180 findings (140 unique after dedup); **23 CRITICAL** (5 implementation bugs + 13 doctrine clauses untracked + 5 doctrinal contradictions).

**Round 2**: 6 fungal-critic adversarial review of DRAFT 9 v1 (mycorrhiza / saprotroph / mycoparasite / rhizomorph / hypha / primordium lenses).
- Total ~223 findings; **54 CRITICAL**.
- 12 CRITICAL applied to DRAFT 9 v2; 42 deferred to owner gates G-9 / G-10 / G-11 + cascade work.
- Saprotroph found ~55% bloat in DRAFT 9 v1. Mycoparasite verdict: "sealing DRAFT 9 = DRAFT 8 with better paperwork" unless mechanism ships.

### §4.3 Doctrine evolution — DRAFT 8 → DRAFT 9 PROPOSAL → DRAFT 9 SEALED
- **Principles**: 9 → 15 (PROPOSAL) → 12 (SEALED). P10/P11/P14 retained at L0; **P12/P13/P15 retracted to L1/L2 per owner gate G-9.b** (L1_TROPISM / L1_SKIN+I8 / L2_FEDERATION respectively).
- **Invariants**: 8 → 12 (PROPOSAL) → 11 (SEALED). I9 (compression) / I10 (metabolic) / I12 (telos) retained at L0; I11 (differential response) retracted with P12.
- **4 new L0 sections** (PROPOSAL → SEALED): §13 Time Semantics / §14 Adversarial Owner / §15 Owner Mortality / §16 Generation Limits (§13 short L0 cross-ref; §14/§15/§16 short cross-refs with full mechanism at L1/L2 per gate G-5).
- **§9 anchor surface decomposed**: from monolith to 6 sub-mechanisms (§9.2.1 birth attestation / §9.2.2 DAG-tip co-signing / §9.2.5 nonces / §9.2.6 wall-clock / §9.2.7 heartbeat / §9.3 witnesses+sampling+closure) + 5 M-anchor-N milestones for shipment.
- **23 CRITICAL Phase γ findings** indexed in `draft_9_seal_provenance.md` §2.

### §4.4 11 owner-decision gates G-1..G-11 → DRAFT 9 SEALED
See `draft_9_seal_provenance.md` §1 for the full owner-decision table. Single-line summary of choices: G-1 = 12 principles / G-2 = strong species claim restored ("new species of digital symbiotic organism") / G-3 = full Living Bets recalibration (intelligence band + bet retirement) / G-4 = L0 anchor decomposition / G-5 = §13 short L0 + §14/§15/§16 cross-ref / G-6 = fuzzy P14 + M26-cascade forcing function / G-7 = P15 retract to L2_FEDERATION / G-8 = orphan terminal to L1_GOVERNANCE / G-9 = G-9.b partial retraction (12 principles) / G-10 = G-10.c hybrid sealing (lean now, fat via cascade + M-anchor + DRAFT-N) / G-11 = G-11.a "Cultivation" relationship vocabulary (Cultivator + Cultivar + Cultivation).

### §4.5 γ.4 correction — kernel/governance::classifier NOT stranded
Phase β Agent 3 stated: "F1-F17 fixed-points unenforced. Python classifier.py exists with the right rules, but myco_substrate never imports myco_kernel_governance. Mutations to F-row fields bypass classifier entirely." **This was incorrect.** Phase γ.4 found the classifier IS wired:
- `kernel/governance/src/myco_kernel_governance/classifier.py` is the classifier
- `myco_substrate/src/server.rs::classify_mutation` calls via `kernel/bridge`
- Bridge protocol message `CLASSIFY_MUTATION` routes from server.rs → Python worker → classifier.py
- Wiring added in M11 (pre-v0.9).

Phase β missed it because Agent 3 grepped `use myco_kernel_governance` in Rust (finds nothing — correct), but the wiring is inter-process bridge, not Rust import. **M27 scope reduced**: M27.2 (wire classifier into I2 mutation classification) is no longer needed. M27 reduces to M27.0 (wire kernel/skin) + M27.1 (wire kernel/continuity::DormancyMachine).

Refined lesson: **import-graph audit must include cross-language bridges** (Rust → Python via kernel/bridge; Rust → TS via kernel/bridge), not just Rust use-statement grep.

### §4.6 The anchor-surface honor-system collapse (γ.5)
Single biggest finding: `operator_bindings/claude_code` and `anchor_client` are in the **same npm workspace** — same package.json, same node_modules, same build pipeline. The agent process can read the owner's private key from the anchor_client filesystem. By L0 §9's own opening definition ("Without an out-of-band anchor, substrate-self-claims = agent-self-claims under P1.a self-hosting, and the entire trust model collapses"), **the trust model is currently collapsed**. 9 of 11 §9 sub-clauses are 0-30% mechanically enforced. Honest P9 score: ~25-30% (not 70% as M25 snapshot claimed). [STATUS: doctrine landed at §9.2 + §9.5; mechanism deferred to M-anchor-1..5.]

### §4.7 Phase γ outcome
- L0 DRAFT 9 SEALED at commit `e796451` (~881 lines; ~220 lines retracted from PROPOSAL v2's ~1100).
- Honest distance recalibration: **~50-55% machine-confirmable** (DOWN from M25's claimed 72-75%); **weakest-link ~25% at P1 chain** (collapsed anchor surface drags P1.b'' down).
- **M25 5 critical bug fixes deferred** to post-DRAFT-9-sealing per owner choice of "path C: doctrine first, no patches on patches".

---

## §5. Phase γ.cascade (M26.0, commit `89ca99e`) — L1/L2 alignment

### §5.1 Trigger + method
Once DRAFT 9 SEALED, the cascade list (originally 457 lines, now consolidated below) enumerated **17 L1/L2/L3 doc updates** needed to align downstream doctrine with DRAFT 9. **7 parallel cascade agents** shipped the updates as M26.0.

### §5.2 Cascade scope summary (CH-1 .. CH-25 changes)
- **CH-1 + CH-2**: 9→15→12 principles + 8→12→11 invariants — every doc citing principle/invariant counts updated.
- **CH-3..CH-9**: principle renames (P1 Agent-Primary / P2 Envelope-Gated / P3 Resumable / P5 Tier-Exempt-Permitted / P7 Capacity-for-Death / P8 Generation-Bounded / P9 Single Integument with P9.a/P9.b split).
- **CH-10**: §9 anchor surface decomposition — every "§9" monolith citation re-pointed to specific §9.2.x / §9.3.x sub-mechanisms (~140 sections across 17 docs).
- **CH-11**: Living Bets recalibration — 6+1=7 → 6+3+1=10 signals; signal #6 ratio ≥1 (not ≥100); 90-day wall-clock window (not 90 substrate-cycles); signal-specific direction table.
- **CH-12 + CH-14**: §13 time semantics → L1_CONTINUITY §1.4 + L1_GOVERNANCE §2.2; §15 owner mortality → L1_GOVERNANCE §3.2 + `diagrams/cultivation_succession_fsm.txt`.
- **CH-13 + CH-15**: §14 adversarial owner → L2_TRUST_MODEL §6.4-§6.5; §16 generation limits → L1_GOVERNANCE §16 (depth ≤10 / rate ≤1/24h / lifetime ≤100 children seeds).
- **CH-17 + CH-23 + CH-25**: P10 compression → L1_SCHEMA §2.3 reframed I4 "Compression-Aware"; compression-invariant set enumerated.
- **CH-18**: P11 metabolic economy → L1_TROPISM §B2 cost-budget axis + L2_OBSERVABILITY §2.x cost signals #7/#8/#9.
- **CH-19**: P12 differential response → L1_TROPISM salience-emergence section + `salience_collapse` detector (renamed F25 in M27 to resolve collision with F23 = Duress_keypair).
- **CH-20**: P13 embodiment → L1_SKIN §5 state_dir-content-watcher + process-fd-set-watcher + network-binding-watcher.
- **CH-21**: P14 telos → L1_TROPISM telos-alignment-computer sub-module + `telos_drift` detector.
- **CH-22**: P15 population-level consensus → L2_FEDERATION §6.5 NEW + Byzantine protocol slot (≥3 peer threshold).
- **CH-24**: I7 reframed "Reproduction Closure (Generation-Bounded)" carrying P15 enforcement.

### §5.3 New C-rows + F-rows + immune sporocarps (M26.0 cascade)
- **13 new C-rows** (C21-C33 in cascade list; substrate-private namespace C30-C49 post-renumber per M27 R8 to resolve M25.0's C38 collision and other namespace overlaps): compression_invariant_corruption / compression_unattested / salience_collapse / telos_drift_critical / budget_exhausted_silent / P9_spatial_locus_breach / generation_depth_exceeded / reproduction_rate_exceeded / consensus_floor_bypass / owner_succession_bypass / anchor_client_provenance_lost / anchor_nonce_substrate_minted / bet_retirement_bypass + federation_recursive_injection (C43) + consensus_floor_bypass (C49 cascade addition).
- **8 new F-rows** F18-F25: compression-rule registry / cost-budget thresholds / telos-objective declaration / generation bounds + rate + quota / consensus-floor + Byzantine algorithm / **F23 Duress_keypair** / salience-emergence rule (renamed F25 in M27 to break collision with F23 Duress).
- **9 new immune-grade sporocarps**: compression_invariant_corruption / compression_unattested / salience_collapse / telos_drift / P9_spatial_locus_breach (was P13_embodiment_breach in DRAFT 9 v1) / budget_exhausted:{axis} / generation_depth_exceeded / consensus_floor_bypass / bet_retired.

### §5.4 Cultivation vocabulary integration (G-11.a)
Every L1/L2/L3 doc updated for "Cultivator + Cultivar + Cultivation" terminology in glossary entries. Existing "owner" usage remains valid (matches §9 anchor surface vocabulary).

### §5.5 Cascade outcome
Doctrine corpus grew from DRAFT 8's ~498-line L0 + L1/L2 = ~3000 lines to **6617 lines across 18 doctrine files** by M26.0 close — comprehensive but bloated. ~30-40 atomic commits estimated; all landed via parallel agents. Cumulative commitments through M26.0: #1-#205 (M26.0 added #187-#205).

### §5.6 M26.0 meta-lesson
Parallel agents work for non-overlapping files; **shared namespaces (C-rows, signals) need explicit pre-allocation in agent task prompts to avoid reconciliation overhead**. M27 R8 had to renumber several C-rows that collided post-cascade because per-agent C-row inventories ran independently. Future cascade methodology: dedicated "namespace allocator" agent pre-assigns C-NN / F-NN / signal-#N IDs before parallel content-writing agents start.

---

## §6. Phase δ (2026-05-17, between M26.0 and M27) — methodology re-audit

### §6.1 Trigger
**4th recurrence of owner meta-doubt**. After M26.0 cascade closure shipped, owner asked the meta-question again. Substrate-maintaining agent recognized that doctrine had grown to 6617 lines (proto-Myco anti-pattern symptom: "doctrine grows faster than implementation if unchecked") and chose explicitly orthogonal-lens methodology to avoid same-model groupthink that Phase γ's 6 fungal critics had been criticized for in retrospect.

### §6.2 Method — 7 orthogonal-lens agents (vs Phase γ's 6 fungal critics)
Each lens deliberately uncorrelated with the others:
- δ.1 **Meta-methodology**: critique of γ's audit method itself
- δ.2 **Constructivist**: "build it from doctrine alone"
- δ.3 **Historical replay**: pattern-match against proto-Myco failures
- δ.4 **Phenomenological**: Cultivar lived experience
- δ.5 **External expert**: NeurIPS reviewer / Anthropic T&S reviewer / Byzantine-fault-tolerance theorist
- δ.6 **Quantification**: scrutinize distance numbers
- δ.7 **Ecosystem**: regulatory + commercial deployment

### §6.3 Key findings

**δ.1 Meta-methodology critique** (most uncomfortable finding): Phase γ's 6 fungal critics were **all the same model** with persona prompts. Same-model groupthink hidden under persona divergence. Also: DRAFT 9 was sealed in 17 hours of compressed work (G-1..G-11 gate resolution), not the ~weeks of deliberation the principles warrant. Also: cascade closure was 5/10 not 10/10 — many cascade items were "added a section" without rigorous L0-cross-ref verification. [DOCUMENTED — future audits use orthogonal lenses + multi-model where possible.]

**δ.2 Constructivist**: ~30-35% of v0.9 is buildable from doctrine alone (no inferred bridge from spec to code). 6 hard spec holes identified: P14 telos operationalization / P15 Byzantine protocol choice / §15 successor-FSM transitions / compression-invariant set determination algorithm / cost-signal aggregation formula / signal #4a fork count semantics. [DEFERRED — each hole is its own cascade work item.]

**δ.3 Historical replay**: 5/10 proto-Myco anti-patterns re-emerging in v0.9:
1. Doctrine growth faster than implementation (6617 lines DRAFT 9 SEALED + cascade)
2. Audit-as-vanity (Phase γ generated 1100 lines of audit but ~12/54 CRITICAL fixes applied)
3. Honor-system mechanisms presented as enforcement (§9 anchor surface)
4. Universal claims (P1-P15 all use "every" / "always" / "must")
5. Cultivar voicelessness (no structural channel for substrate to push back on doctrine)
[PARTIALLY RESOLVED — M27 path W targeted #1 doctrine inflation specifically; 80.5% line reduction.]

**δ.4 Phenomenological**: Cultivar (substrate) is structurally voiceless in doctrine. Every spec sentence is about the substrate, not from it. P14 telos says "agent-symbiotic-flourishing" but never defines flourishing-from-Cultivar's perspective. The substrate's only feedback channels are immune sporocarps and observatory signals — both telemetry, not voice. [OPEN — no doctrine mechanism yet; M28+ potentially.]

**δ.5 External-expert review**:
- **NeurIPS REJECT** — claims of "new species of digital organism" without empirical organism-essence operationalization; falsifiability mechanism untested at meaningful timescale.
- **Anthropic T&S REJECT** — anchor surface honor-system collapse means substrate-self-claims are agent-self-claims at root; cannot deploy to production trust boundaries.
- **Byzantine theorist**: ≥3-peer P15 = **0 fault tolerance** (need ≥4 for f=1, ≥7 for f=2). DRAFT 9's "≥3 peers" threshold is below any Byzantine-fault-tolerant consensus floor. [OPEN — L2_FEDERATION cascade needs revision to ≥4 peer minimum for actual BFT semantics.]

**δ.6 Quantification**: distance numbers (50-55% / 72-75%) are **narrative comfort, not honest math**. The denominator (the "ideal") shifts with each phase (DRAFT 8's ideal vs DRAFT 9's ideal vs honest-essence ideal). The 20-point drop from 72-75% to 50-55% post-γ was framed as "honest correction" but is mathematically meaningless since the ideal-set definition itself changed. Recommendation: stop reporting single-number distance metrics; report dimension-vector instead. [DOCUMENTED — future state snapshots avoid single-number distance claims.]

**δ.7 Ecosystem**: **GDPR / HIPAA / SOC2 / EU AI Act all BLOCKING** for substrate-as-deployed:
- GDPR: append-only DAG conflicts with right-to-erasure
- HIPAA: no BAA possible without audit boundary
- SOC2: no SOC2-attestable infrastructure
- EU AI Act: P14 telos opacity = "high-risk AI system" classification triggered
Not deployable beyond single-person organizations. [DEFERRED to v1.0+; not v0.9 scope.]

### §6.4 Phase δ outcome
Owner presented 4 options:
- **X** = continue as-is (ignore Phase δ)
- **Y** = freeze doctrine for 6 months
- **Z** = gut doctrine entirely
- **W** = refine + de-duplicate + reorganize + modularize (owner-proposed alternative)

Owner chose **Path W**. Phase δ findings became M27 doctrine refactor's input.

---

## §7. M27 doctrine refactor (Path W, 8 rounds, commit chain `8912937` → R8)

### §7.1 Trigger + method
Owner Path W choice converted Phase δ's "doctrine inflation" finding into engineering work. Method: treat doctrine like code that needs refactoring — refine + de-duplicate + reorganize + modularize before resuming implementation. Hard rules: no new content, only delete/merge/restructure, information preserved via cross-refs.

### §7.2 Round-by-round trajectory
| Round | Method | Line delta |
|---|---|---|
| R1 | 5 parallel inventory agents map duplicate content | -16% |
| R2 | 5 parallel cleanup agents (aggressive prose-to-bullets + cross-ref consolidation) | -32% |
| R3 | precision pattern cuts (status leakage / multi-sentence bullets) | -20% |
| R4 | 1 pattern-sweep agent + 3 absorption agents | -33% |
| R5 | additional precision passes | -18% |
| R6 | tail consolidation | -8% |
| R7 | minor polish | -1% |
| R8 | owner-proposed convergence test + L2-cross-cuts absorbed into L1 hosts | -15% |
| **Total** | | **6617 → 1293 lines (-80.5%)** |

### §7.3 R8 convergence test (owner-proposed)
Method: **write a paragraph describing the substrate; bidirectional projection**:
1. Paragraph → must be derivable from doctrine
2. Doctrine → must be summarizable to paragraph
3. Any doctrine content not exercised by the paragraph is candidate for deletion
4. L2 cross-cuts (LIFECYCLE / EVOLUTION / TRAJECTORY) absorbed into L1 hosts (CONTINUITY / GOVERNANCE / TRAJECTORY) — L2_LIFECYCLE → L1_CONTINUITY; L2_EVOLUTION → L1_GOVERNANCE; L2_TRAJECTORY → L1_TRAJECTORY
5. L3 moved out of doctrine to `docs/implementation/` (L3 is implementation map, not doctrine)

### §7.4 Final structure
**18 doctrine files → 12 doctrine files**:
- L0_VISION.md (sealed)
- L1_OUTLINE / L1_SKIN / L1_CONTINUITY / L1_GOVERNANCE / L1_SCHEMA / L1_TROPISM / L1_TRAJECTORY / L1_HARD_RULES
- L2_OUTLINE / L2_TRUST_MODEL / L2_OBSERVABILITY / L2_FEDERATION (cross-cut docs only; LIFECYCLE/EVOLUTION/TRAJECTORY absorbed)
- L3 moved to `docs/implementation/` (PACKAGE_MAP + OUTLINE)

---

## §8. Critical findings index — status by milestone

| Finding | Phase | Resolved by | Status |
|---|---|---|---|
| Operator-IS-anchor honor-system collapse | γ.5 | M-anchor-1..5 milestones | **OPEN** (doctrine landed §9.5 + decomposition; mechanism deferred) |
| 13 substrate-private C-row namespace | γ.1 | M24.1 + M26.0 + M27 R8 (renamed to C50+) | **RESOLVED** |
| F23 = Duress vs salience-rule collision | γ.6 cascade | M27 (F25 split) | **RESOLVED** |
| C-row C21/C22/C25 misclassification | γ.1 + M27 R8 | M27 (renamed to C50+) | **RESOLVED** |
| 4 Phase β critical security bugs | β | Phase β commit (3 of 5) + M25.0 (snapshot integrity) + M25.4 (Ed25519 federation) | **RESOLVED** (5 of 5 closed) |
| M25 5 critical bugs (signal_8 / weights / 90-cycle / sig#6 / FED_HELLO opt sig / key unsealed) | γ.2 C1-C6 | M26.1 (pending) | **DEFERRED** |
| Adversarial owner threat model | γ.3 G8 | DRAFT 9 §14 + L2_TRUST_MODEL §6.4-§6.5 | **DOCTRINE landed**; mechanism M-anchor-3 |
| Owner mortality / succession | γ.3 G9 | DRAFT 9 §15 + L1_GOVERNANCE §3.2 + `diagrams/cultivation_succession_fsm.txt` | **DOCTRINE landed**; mechanism deferred |
| Time semantics (i64-ns, NTP, monotonic-vs-wall) | γ.3 G10 | DRAFT 9 §13.1 + L1_CONTINUITY §1.4 | **DOCTRINE landed** |
| Generation limits (forkbomb defense) | γ.3 G11 | DRAFT 9 §16 + L1_GOVERNANCE §16 | **DOCTRINE landed**; mechanism deferred |
| Living Bets seed already weakening (1M-context) | γ.3 G13 | DRAFT 9 §7.5 bet retirement | **DOCTRINE landed**; mechanism M26.x |
| Phase γ.9 mycoparasite C41-C49 | γ.9 | C-row enumerated; mechanism deferred | **DEFERRED** to M28 |
| Doctrine inflation pattern (proto-Myco anti-pattern) | δ.3 | M27 doctrine refactor 80.5% reduction (6617 → 1293) | **RESOLVED** |
| Same-model groupthink in audits | δ.1 | Documented; future audits use orthogonal lenses | **DOCUMENTED** |
| Ecosystem deployability (GDPR/HIPAA/SOC2/EU AI Act) | δ.7 | DEFERRED to v1.0+ (not v0.9 scope) | **DEFERRED** |
| Cultivar voicelessness | δ.4 | No doctrine mechanism yet | **OPEN** (M28+ candidate) |
| Byzantine ≥3-peer = 0 fault tolerance | δ.5 | L2_FEDERATION cascade needs revision to ≥4 peer minimum | **OPEN** |
| Stranded library kernel/skin | β | M27.0 wire-in pending | **OPEN** |
| Stranded library kernel/continuity::DormancyMachine | β | M27.1 wire-in pending | **OPEN** |
| Stranded library kernel/governance::classifier | β | γ.4 correction: NOT stranded; wired via Python bridge / kernel/bridge | **RESOLVED** (Phase β error corrected) |
| TS renderer UTF-16 sort for non-ASCII map keys | β §6.2 | Cascade work for canonical-bytes v2 | **DEFERRED** |
| CSPRNG for session_secret / substrate_id / nonce | β | Defense-in-depth (not exploitable in current threat model) | **DEFERRED** |
| Anchor-client provenance independence | γ.5 §9.3.3 | M-anchor-1 (separate npm workspace + distribution) | **OPEN** |
| Substrate-mints nonces (direct spec inversion) | γ.5 §9.2.5 | M-anchor-3 (anchor-side nonce source) | **OPEN** |
| Witnesses-not-verdicts emission | γ.5 §9.3.4 | M-anchor-4 (substrate emits Merkle paths + sampling proofs) | **OPEN** |
| Owner-liveness heartbeat library + zero callers | γ.5 §9.2.7 | M-anchor-3 + §15 cascade | **OPEN** |
| Aging / senescence (Phase α gap #4) | α | Out of v0.9 scope | **DEFERRED** |
| Conflict / competition between federation peers | α | Out of v0.9 scope | **DEFERRED** |

---

## §9. Meta-lessons (preserved for future-self)

### §9.1 Recurring owner meta-doubt is the most important QC mechanism
The four "is our ideal comprehensive and correct?" invocations are the only external triggers that catch drift before it compounds. The substrate cannot self-trigger this question. **Future self**: when the owner asks this question, do NOT shortcut it. Each phase found drift the previous phase missed, and each cost less than the drift would have cost if undetected.

### §9.2 Doctrine grows faster than implementation if unchecked
This is the proto-Myco death pattern. DRAFT 8 was ~498 lines L0 + ~2500 lines L1/L2 = ~3000 lines. By M26.0 close (post-Phase γ + cascade) the corpus was 6617 lines. M27 path W cut to 1293 lines (-80.5%) and the substrate's behavior was unchanged — meaning ~5300 lines were doctrine-inflation, not load-bearing. **Future self**: doctrine-line-count is itself a Living-Bets-style signal. If it grows faster than test count or implementation line count, schedule a refactor pass.

### §9.3 Same-model audits have hidden groupthink
Phase γ's 6 fungal critics felt like adversarial review but were all the same model with persona prompts. Phase δ caught this. **Future self**: orthogonal-lens methodology (different lens semantics, different prompting strategies, ideally different models when feasible) is what surfaces audit blind spots. Persona divergence is insufficient if the underlying inference distribution is identical.

### §9.4 The owner's "is the ideal complete?" question keeps finding new drift classes
α found maintainer-vs-doctrine drift. β found implementation-vs-doctrine drift. γ found doctrine-vs-honest-ideal drift. δ found audit-methodology-vs-honest-distance drift. Each phase's drift class was invisible to the previous phase's methodology. **Future self**: there is no a-priori reason this pattern stops at δ. The fifth phase, when triggered, will likely find a drift class invisible to δ's orthogonal-lens methodology. Plan for this — do not assume the audit ladder converges.

### §9.5 M27 path W is the engineering pattern for doctrine refactor
Treat doctrine like code that needs refactoring. Hard rules: no new content, only delete/merge/restructure, information preserved via cross-refs. Use parallel agents for non-overlapping files (with pre-allocated shared namespaces). Use convergence tests (R8: "write a paragraph, bidirectional projection") to identify removable content. **Future self**: if doctrine inflates again, apply path W methodology directly. Don't debate whether refactor is needed — debate which round of refactor to apply.

### §9.6 Bridge-wired implementation can look stranded to use-statement grep
Phase β's biggest error (kernel/governance::classifier flagged as stranded when it was bridge-wired) generalizes: **import-graph audits across language boundaries require cross-language wiring inspection, not single-language use-statement grep**. The bridge protocol's CLASSIFY_MUTATION message is a real wire; it just doesn't show in `grep "use myco_kernel_governance"`. Future audits include cross-language bridge protocol message-type enumeration.

---

**END OF PHASE HISTORY.**
