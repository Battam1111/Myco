# Phase γ Meta-Audit — 2026-05-17

> Triggered by owner question: "我有一个担心的点，就是目前我们对于"理想"的认知是全面且正确的吗？"
> (Recurring meta-vigilance pattern; same trigger as Phase α 2026-05-15.)
>
> Post-audit outcome: **L0 DRAFT 9 PROPOSAL drafted**, pending owner approval at 8 explicit owner-decision gates (§17 of DRAFT 9).
>
> **Predecessor**: [Phase β audit 2026-05-15](phase_beta_audit_2026-05-15.md) at commit `8ffc305`.
> **Triggered after**: M25 completion commit `e0d0e38` (security + observatory completion; 6 sub-phases shipped).
> **State at trigger**: 1094 tests, 0 failures; Rust 424 + Python 361 + TS anchor 162 + TS ops 147.

---

## §0. TL;DR

Phase α exposed that the maintainer's mental model of L0 was thinner than actual L0. Phase β exposed that the implementation was thinner than the doctrine it claimed to embody. **Phase γ exposes a third drift layer: the doctrine itself was thinner than honest accounting of "what is essential for an organism-substrate".**

The recursive audit ladder is now:

| Phase | Drift class found | Mechanism |
|---|---|---|
| α (2026-05-15) | Maintainer's mental model ↔ L0 doctrine | Reading L0 directly vs reading my abstraction of L0 |
| β (2026-05-15) | Implementation ↔ L0+L1+L2 doctrine | 6 parallel agents reading source files vs trusting library API surfaces |
| **γ (2026-05-17)** | **Doctrine ↔ honest "ideal" reality** | **6 parallel agents auditing doctrine self-consistency + ideal-set completeness + machine-confirmability of each clause** |

**Headline finding**: pre-Phase-γ "distance to ideal" was claimed as ~72-75% machine-confirmable in M25 snapshot. Post-Phase-γ honest re-assessment is **~50-55%**. The 20-point gap is not bug regression — it is the cost of admitting the doctrine itself had blind spots (anchor surface honor-system collapse + 6 missing essential principles + 12 unaddressed structural gaps).

**Total findings**: ~180 across 6 lenses, of which **23 CRITICAL** (5 implementation bugs + 13 doctrine clauses untracked + 5 doctrinal contradictions).

The 23 CRITICAL findings collectively triggered **L0 DRAFT 9 PROPOSAL** drafting + 6 review-pass rounds + a cascade-work list (M26-cascade) committing the next milestone block to align L1/L2/L3 with DRAFT 9 once owner approves.

---

## §1. Audit methodology

### §1.1 Scale
- **6 opus agents** dispatched in parallel
- Each agent budgeted **≥30 tool calls**, source-files-only (no reading summaries)
- Total ~180 distinct findings; deduplicated to ~140 unique
- 23 CRITICAL after severity grading
- Cross-agent corroboration on 8 findings (multiple lenses found the same issue from different angles)

### §1.2 Lenses

| Lens | Agent focus | Source files primary |
|---|---|---|
| γ.1 | Doctrine self-evolution since Phase α | L0/L1/L2 doctrine files; git history of `docs/architecture/` |
| γ.2 | M25 implementation fidelity vs M25 spec claims | `server.rs`, `derived_state.rs`, `federation/protocol.rs`, `persistence.rs`, `messages.ts`, `substrate_client.ts` |
| γ.3 | Phase α 7-gaps revisit + unknown-gap search | L0 full text + adversarial scenario generation |
| γ.4 | Stranded libraries forensics (Phase β finding revisit) | `kernel/skin/*.rs`, `kernel/continuity/*.rs`, `kernel/governance/*.py`, import graph in `myco_substrate/src/*.rs` |
| γ.5 | Anchor surface honor-system audit | L0 §9 every clause × `anchor_client/src/*.ts` × `operator_bindings/claude_code/src/*.ts` × server.rs handlers |
| γ.6 | Meta-framework critique (is the doctrine itself complete?) | L0 entirety + biological-essence literature + organism-essence checklist |

### §1.3 Severity grading

- **CRITICAL**: working bug exploitable by current code OR doctrine clause whose absence collapses the trust model OR principle whose omission reveals the framework is mis-categorized
- **HIGH**: doctrine drift OR substantial honor-system gap OR implementation deviation that requires near-term fix
- **MODERATE**: cosmetic / cataloging / parameter-tuning OR doctrine ambiguity that survives but should be sharpened

---

## §2. Findings summary (numerical breakdown per lens)

| Lens | Total | CRITICAL | HIGH | MODERATE |
|---|---|---|---|---|
| γ.1 doctrine drift | 19 | 4 | 9 | 6 |
| γ.2 M25 fidelity | 18 | 6 | 7 | 5 |
| γ.3 gap revisit + new | 28 | 3 (G8/G9/G10) | 12 | 13 |
| γ.4 stranded libraries | 11 | 0 | 4 | 7 (including 1 Phase β error rebuttal) |
| γ.5 anchor surface | 31 | 5 | 11 | 15 |
| γ.6 meta-framework | 33 | 5 (P10-P14 missing × claim-1 + claim-7) | 16 | 12 |
| **Total** | **140 dedup** | **23** | **59** | **58** |

Cross-corroboration map (>1 lens finding same issue):
- Anchor surface honor-system: γ.1 + γ.3 G12 + γ.5 + γ.6 (4 lenses)
- Selective compression / forgetting absence: γ.3 G18 + γ.6 P10 (2 lenses)
- Adversarial owner threat model absence: γ.3 G8 + γ.5 + γ.6 (3 lenses)
- Time semantics undefined: γ.2 C3 + γ.3 G10 (2 lenses)
- Operator-IS-anchor collapse: γ.2 C5 + γ.5 + γ.6 claim-1 (3 lenses)

---

## §3. Key drift detections — the 23 CRITICAL findings

For triage, here are the 23 CRITICAL findings indexed by lens:

| # | Lens | Title | Address in DRAFT 9 |
|---|---|---|---|
| 1 | γ.1 | Zero commits to `docs/architecture/` since Phase α | DRAFT 9 itself is the address |
| 2 | γ.1 | 13 sub-clauses of L0+L1 added by Phase α/β but never propagated to L0 main doc | §4 invariant additions; §9 decomposition |
| 3 | γ.1 | Snapshot claim of P9 70% over-credits (anchor surface gap drags real value to ~30%) | §9.2 decomposition forces honest accounting |
| 4 | γ.1 | TOFU federation auth contradicts L1_GOVERNANCE §5 freshness-required clause | §14.2.4 + L1 cascade work |
| 5 | γ.2 | C1 signal_8 field-name break between Rust and TS | Post-DRAFT-9 cascade fix |
| 6 | γ.2 | C2 weights field structure break between Rust and TS | Post-DRAFT-9 cascade fix |
| 7 | γ.2 | C3 90-cycle window ≠ 90-day window (off by ~6 orders of magnitude) | §7.4 explicit "wall-clock 90 days, not 90 cycles" |
| 8 | γ.2 | C4 signal #6 direction inversion in code (DOWN vs UP) | §7.4 signal-specific direction table |
| 9 | γ.2 | C5 FED_HELLO signature optional = TOFU bypass attack | M25.4 acknowledged TOFU; §9.6 + §14 frames it |
| 10 | γ.2 | C6 substrate_signing_key.cb plaintext = C4 (substrate_secret_unsealed) violation | M26.0 sealing roadmap |
| 11 | γ.3 G8 | No adversarial-owner threat model | **§14 NEW** |
| 12 | γ.3 G9 | No owner-mortality / succession framework | **§15 NEW** |
| 13 | γ.3 G10 | No time-source authority hierarchy | **§13 NEW** |
| 14 | γ.5 | Operator-IS-anchor (same npm workspace) — trust model collapse currently active | §9.5 explicit acknowledgment + M-anchor-1 |
| 15 | γ.5 | Substrate-mints nonces (direct spec inversion of L0 §9.2.5) | §9.2.5 + M-anchor-3 |
| 16 | γ.5 | No anchor-clock source (only operator-side wall-clock) | §9.2.6 + M-anchor-3 |
| 17 | γ.5 | Substrate emits verdicts not witnesses (`pass/fail` summaries) | §9.3.4 + M-anchor-4 |
| 18 | γ.5 | No owner-liveness heartbeat (library exists, zero non-test callers) | §9.2.7 + M-anchor-3 + §15 |
| 19 | γ.6 | DRAFT 8 "literal taxonomic class within digital organisms" rhetorically maximalist | §1.1 / §1.2 honesty calibration |
| 20 | γ.6 | P10 Selective Compression absent (synaptic pruning analogue) | **P10 NEW** + I9 |
| 21 | γ.6 | P11 Metabolic Economy absent (ATP-budget analogue) | **P11 NEW** + I10 |
| 22 | γ.6 | P12 Differential Response absent (attention discipline) | **P12 NEW** + I11 |
| 23 | γ.6 | P14 Telos absent (substrate-internal purpose) | **P14 NEW** + I12 |

---

## §4. Phase γ.1 — Doctrine drift

> Lens: "Has the doctrine itself evolved with the implementation since Phase α, or has L0/L1/L2 been frozen while implementation walks on?"

### §4.1 Key finding: doctrine is frozen

`git log --oneline docs/architecture/L0_VISION.md` between commits `3d6749f` (Phase α) and `e0d0e38` (M25 complete) shows **zero commits to L0/L1/L2 doctrine files** since Phase α. Meanwhile:

- Phase β shipped 4 critical security fixes
- M22-M25 shipped 14 new mechanisms (autonomy, mortality execution, federation, observatory)
- 13 sub-clauses were added to L1 docs in passing (citation-only references)

**The doctrine layer that is supposed to govern all of L1-L4 became the slowest-evolving layer of the codebase.** Implementation outran doctrine.

### §4.2 13 sub-clauses untracked

Drawn from Phase α + Phase β + M22-M25 work, these sub-clauses are referenced in implementation or test code but never propagated to the L0 main doc:

| # | Sub-clause | Source | Status before DRAFT 9 |
|---|---|---|---|
| 1 | Witnesses (vs verdicts) for I3/I4/I5/I8 outputs | L0 §9.3 single sentence | Not enforced anywhere |
| 2 | Anchor-nonce-derived sampling for witness emission | L0 §9.3 single sentence | Zero implementation |
| 3 | Attestation envelope 8-field full schema | L1_GOVERNANCE §2.2 | Implementation has 4 fields |
| 4 | DAG-enumeration closure (parent-edge closure) | L0 §9.4 single sentence | Server emits enumeration; closure unwired |
| 5 | Compression-invariant set per P10.b | Implicit in I4 retention spec | Never named in L0 |
| 6 | Federation peer attestation freshness with revocation | P8 paragraph | TOFU-only in M25 |
| 7 | Mortality-signal threshold protection (cannot be silently tuned) | L0 P7 paragraph | Threshold lives in TOML config |
| 8 | Spore-schema immune-summary at sprout_child | P8 paragraph | Implementation: parent immune sporocarps not inherited |
| 9 | Substrate-ID birth attestation 5-tuple | L0 §9 single sentence | Implementation: TOFU on first hello |
| 10 | Anchor-surface client provenance independence | L0 §9.3 single sentence | Operator IS anchor surface (same npm workspace) |
| 11 | Birth-period CI elevation (ALL parameter-tuning is CI during birth) | I2 paragraph | Implementation: only sprout/federation are CI during birth |
| 12 | Lexicon evolution is CI-level | L0 P3 paragraph | Implementation: no lexicon registry |
| 13 | Substrate's wall-clock not trusted for security-relevant defenses | L0 §9 implicit | Implementation: substrate wall-clock used for nonce TTL |

All 13 are addressed in DRAFT 9 (§4 invariant additions I9-I12, §9.2 sub-mechanism inventory table, §13 time semantics).

### §4.3 P9 70% snapshot claim is over-credit

The M25 snapshot reported P9 (Integument) at 70%. Phase γ.5 audit found 11 §9 anchor-surface sub-clauses where **9 are 0-30% mechanically enforced**. The honest accounting:

- §9.2.1 substrate-ID birth attestation: 0% (TOFU)
- §9.2.3 owner attestations out-of-band: 0% (same workspace)
- §9.2.4 L0 revision diff workflow: 0% (L0 in git, no workflow)
- §9.2.5 anchor-surface-generated nonces: 0% (substrate mints — direct spec inversion)
- §9.2.6 anchor-stamped wall-clock: ~5%
- §9.2.7 owner liveness heartbeat: 0% (library exists, no callers)
- §9.3.2 owner-side rendering: ~30%
- §9.3.3 anchor-client provenance independence: 0% (same npm workspace)
- §9.3.4 witnesses, not verdicts: 0% (substrate emits pass/fail)
- §9.3.5 anchor-nonce-derived sampling: 0%
- §9.3.6 DAG-enumeration closure check: ~40% (server emits enumeration; closure unwired)

Only 2 sub-clauses are >50%: §9.3.1 canonical-bytes serialization (~95%, Phase β fix) and §9.3.6 partial enumeration emission. **The honest P9 score is ~25-30%, not 70%.** Snapshot accounting was conflating "skin code paths exist" (P9.a admission/rejection at I8 boundary) with "anchor surface trust mechanism wired" (P9 + §9 doctrine). The former is implemented; the latter is the missing ~45 percentage points.

### §4.4 TOFU federation auth contradicts L1_GOVERNANCE §5

L1_HARD_RULES §F14 commits "Federation peer attestation list (incl. revocations)" as CI fixed-point. L1_GOVERNANCE §5 specifies "L1-bounded peer-attestation freshness with revocation list — stale/revoked attestation triggers `untrusted_federation` immune signal."

M25.4 shipped Ed25519 mutual auth — but legacy peers (no signature) are **TOFU-pinned** with only an observability event `federation_legacy_peer_pinned`. This violates the freshness-required clause: a legacy peer's TOFU pin has no freshness window and no revocation path beyond manual operator action.

DRAFT 9 acknowledges via §9.6 cross-ref to §14 adversarial-owner; the cascade-work item is L1_GOVERNANCE §5 alignment.

---

## §5. Phase γ.2 — M25 implementation fidelity

> Lens: "Does what M25 *claims to have shipped* match what M25 *actually shipped*?"

### §5.1 The 6 CRITICAL bugs

**C1 — signal_8 field-name break between Rust and TS**:
- `server.rs::handle_query_substrate_observatory` emits `"signal_8_doctrine_revision_burst"` (note: "revision_burst", per code)
- `messages.ts::QuerySubstrateObservatoryResponse` types `signal_8_doctrine_instability_burst` (note: "instability_burst")
- Client decoding silently drops the entire signal #8 field; TS observatory queries return undefined for the doctrine-burst signal
- Origin: Rust emitter renamed mid-implementation; TS catch-up missed the rename

**C2 — weights field structure break between Rust and TS**:
- Rust emits `weight_signal_1_repr`, `weight_signal_2_repr`, `weight_signal_4b_repr` (three flat fields)
- TS types `weights: { signal_1, signal_2, signal_4b }` (nested object)
- Client decoder fails to parse; falls back to empty weights — composite_health_score is presented but weight provenance is silently lost

**C3 — 90-cycle ≠ 90-day** (single biggest implementation drift):
- L0 §7 + L2 §3 specify falsifiability trigger over **"90-day window of active operation (L1-tunable)"**
- M25.2 `bet_weakening_quorum` predicate operates over `observatory_history: VecDeque<ObservatorySnapshot>` with cap=90; one snapshot appended per metabolic cycle
- Default cycle interval is 500ms; 90 snapshots = ~45 seconds of wall-clock time
- This is **off by approximately 6 orders of magnitude** (45 seconds vs 90 days = 7,776,000 seconds)
- Effect: the falsifiability trigger is over a window so narrow it cannot meaningfully detect bet weakening — but the predicate appears to be wired
- DRAFT 9 §7.4 makes this explicit: "Window is wall-clock 90 days, not 90 substrate-cycles"
- Cascade-fix deferred to post-DRAFT-9 sealing

**C4 — Signal #6 direction inversion**:
- L0 §7 says signal #6 < 1 = bet-losing region (substrate too small relative to context window — agent winning context war alone)
- M25.2 `bet_weakening_quorum` predicate's `signal_6_below_one_fraction ≥0.5` clause **correctly** triggers when signal #6 < 1
- BUT `signal_5_time_trends.signal_6_direction` field reports trending UP as positive (against the bet) when L0 says UP above ratio 1 is WITH the bet
- The direction reporting is inverted for signal #6 specifically; signals 1/2/3/4b correctly report DOWN-as-against
- DRAFT 9 §7.4 includes the explicit signal-specific direction table

**C5 — FED_HELLO signature optional = TOFU bypass**:
- M25.4 made `signer_pubkey` + `hello_signature` **optional** in FED_HELLO payload (to support backward-compat with pre-M25 peers)
- A peer presenting no signature is auto-TOFU-pinned with `federation_legacy_peer_pinned` observability event
- An attacker connecting to a substrate before legitimate federation can pre-pin themselves as TOFU, then subsequent legitimate peers cannot federate because substrate_id already pinned to attacker
- DRAFT 9 §14.2.4 frames this; L1 cascade work tightens the optional → required transition

**C6 — substrate_signing_key.cb plaintext violates C4** (substrate_secret_unsealed):
- L1_HARD_RULES §C4 commits "`substrate_secret_unsealed` immune sporocarp when substrate_secret detected in substrate-process address space (not OS-sealed)"
- M25.0 introduced `substrate_signing_key.cb` as 32-byte plaintext Ed25519 seed in state_dir
- This is exactly the condition C4 was supposed to catch
- M25 snapshot acknowledges this with "M26+ will add OS-level sealing"; cascade-fix is M26.0

### §5.2 Implementation patterns surfaced

The C1+C2 pattern (Rust/TS field-name and structure drift) reveals the deeper bug class: **adding cross-language fields without a single pinned-bytes schema source**. Phase β's anchor_client/canonical_bytes_v1.json approach scales to canonical-bytes; observatory format_version=3 has no equivalent shared schema. M-anchor-style discipline would catch C1+C2 mechanically.

The C3 pattern (cycle-vs-day window) is a **unit-mismatch class** that cannot be caught by type-checking; it requires either (a) explicit unit-annotated types or (b) doctrine-attested constant comparison. L1_CONTINUITY cascade work spec'd to add.

### §5.3 Test coverage gap

The 5 CRITICAL bugs **all passed M25's 44 new tests** because no test exercised:
1. Rust-emit + TS-decode round-trip on signal_8 (C1)
2. Rust-emit + TS-decode round-trip on weights structure (C2)
3. The 90-cycle / 90-day window over real wall-clock time (C3)
4. Signal #6 direction expectation under controlled ratio (C4)
5. Legacy-peer connection at substrate genesis (C5)
6. `substrate_secret_unsealed` detector emitting when signing key is plaintext (C6)

**Tests asserted what was built; they did not assert what the spec required.** This is the deeper test-coverage flaw — Phase β Agent 4 (test coverage) found 47 scenarios cataloged with 11 uncovered, 14 partial; Phase γ.2 finds the same pattern at the "spec-asserts-X, code-does-X', tests-assert-X'" level.

---

## §6. Phase γ.3 — Phase α 7-gaps revisit + 12 new gaps

> Lens: "Phase α found 7 'real L0 v1 gaps surviving audit'. Are they still real? And what gaps did Phase α miss?"

### §6.1 Phase α 7-gap status

| Phase α gap | Status post-M25 | Phase γ confirms still real? |
|---|---|---|
| 1. Embodiment | No work since Phase α | Yes — DRAFT 9 P13 addresses |
| 2. Energy economics | No work since Phase α | Yes — DRAFT 9 P11 addresses |
| 3. Mesh federation between unrelated substrates | M22 federation is pairwise; no mesh | Yes — DRAFT 9 P15 partially addresses (consensus floor) |
| 4. Aging / senescence | No work since Phase α | Yes — only mortality (P7 + §7.5 bet retirement); aging not modeled |
| 5. Selective forgetting | No work since Phase α | Yes — DRAFT 9 P10 addresses |
| 6. Self-model beyond I3 | M25 observatory format_version=3 partial; substrate observes own signals | Partial — DRAFT 9 §12 acknowledges recursive self-observation; full self-model still gap |
| 7. Conflict / competition | No work since Phase α | Yes — out of v0.9 scope per DRAFT 9 |

**All 7 Phase α gaps still real.** None closed; one (#6) partially advanced via M25 observatory.

### §6.2 12 new structural gaps (G8-G19)

Phase γ.3 systematic adversarial-scenario generation found 12 gaps Phase α missed:

#### G8 — Adversarial owner threat model
DRAFT 8 universally trusts owner as benevolent governance gate. No doctrine for:
- Compromised owner key (attacker holds private key)
- Coerced owner (regulatory seizure, blackmail, physical threat)
- Impersonated owner (anchor-surface client compromised)
- Anchor-client tampering (different content displayed vs signed)

**DRAFT 9 §14 NEW** with bounded defenses per scenario (duress codes, multisig, signature-velocity anomaly detection).

#### G9 — Owner mortality / succession
A substrate operating decades will outlive its owner. DRAFT 8 had no:
- Successor chain (who inherits owner role)
- Liveness heartbeat (how does substrate know owner is alive)
- Legacy / orphaned states (what does substrate do under owner unavailability)
- Terminal-after-orphan policy (does substrate die after N years orphaned)

**DRAFT 9 §15 NEW** with `alive::legacy` / `alive::orphaned` sub-states + 90-day liveness window + 730-day terminal window (seed values, L1-tunable).

#### G10 — Time semantics undefined
Substrate uses `unix_ns: i64` for everything (expiry, sporocarp timestamps, cycle relations). Phase γ.3 found:
- NTP drift unspecified (substrate uses wall-clock for security expiry)
- Monotonic-vs-wall-clock confusion (sporocarp ordering uses wall-clock; backwards-jump corrupts ordering)
- Year 2038 vulnerability if any i32 path exists (audit found none, but no doctrine forbidding)
- Anchor-stamped timestamp authority unspecified

**DRAFT 9 §13 NEW** with explicit time-source authority hierarchy + monotonic-for-ordering / anchor-clock-for-security commitments.

#### G11 — Reproduction forkbomb
P8 has no:
- Generation-depth bound (recursive sproutChild loops)
- Reproduction rate limit (compromised owner-key auto-generates infinite consent)
- Per-parent reproduction quota
- Cycle detection for federation peer A → spawns B, B → spawns A peer

**DRAFT 9 §16 NEW** with seed values: depth ≤10, rate ≤1/24h, lifetime ≤100 children (all L1-tunable).

#### G12 — Anchor client disaster recovery
If owner loses access to anchor surface (lost hardware token, machine destroyed):
- No documented recovery protocol
- No secondary-anchor-key provision
- No n-of-m multisig at L0 level

DRAFT 9 §15 partial (succession chain provides one path); full L1 cascade work for disaster recovery.

#### G13 — Aged Living Bets seed
DRAFT 8's signal #6 seed value (~100) was calibrated for 100K-context agents. M25-era 1M-context Claude has signal #6 ≈ 1 from day one, which DRAFT 8 specified as bet-losing region.

**The bet was structurally weak at v0.9 birth** and current agent capabilities have already moved past DRAFT 8's calibration. DRAFT 9 §7.2 introduces "intelligence band" with explicit lower/upper edges + §7.5 bet retirement for graceful sunset when band's upper edge is crossed.

#### G14 — Liveness without observatory
Per-cycle invariant checks (I3, I4, I5, I8) emit events but the substrate has no liveness contract — if substrate halts (deadlock, infinite loop), nothing detects it. Owner-liveness heartbeat is one direction (owner → substrate); substrate-liveness is the other direction (substrate → operator/owner). M24 cycle-backlog detector partially addresses; full liveness contract is L1 cascade work.

#### G15 — Substrate-ID collision
substrate_id is derived from `sha256(b"myco-substrate-id-v1" || unix_ns || pid || stack_addr)`. Under controlled-environment attack (Docker container, fixed-seed VM), collision is non-trivially possible. M26.1 CSPRNG roadmap addresses; doctrine acknowledgment needed.

#### G16 — Backup privacy attack
Substrate state_dir backups are not internally access-controlled by Myco doctrine. Anyone with read access to backup media reads full substrate state. DRAFT 9 §11.1 NEW: L1_SKIN MUST specify backup encryption requirements; absent encryption is an acknowledged known attack surface.

#### G17 — Doctrine self-consistency
L0 + L1 + L2 + L3 + L4 have evolved together but **never been cross-consistency-audited**. Phase γ.1 found doctrine frozen since Phase α; an L0-L4 internal consistency audit is pending. M27 cascade work spec'd.

#### G18 — Catastrophic forgetting cure
DRAFT 8 I4 + F9 forbade lossy compression. But:
- Substrate cannot run indefinitely without forgetting (storage cost grows linearly with cycles)
- "No forgetting" makes Myco a tape archive, not an organism
- Biological organisms forget via synaptic pruning + REM consolidation

**DRAFT 9 P10 NEW** + I9 NEW commit selective compression as **CI-attested**, with compression-invariant set (P10.b) defining what survives any compression.

#### G19 — Single-skin failure point
I8 mandates exactly one skin process. If skin process dies, substrate cannot accept owner's quarantine_clearance, cannot fruit, cannot federate. DRAFT 8 had no skin-restart discipline. DRAFT 9 P9.b NEW acknowledges single-point-of-failure + commits L1_SKIN to specify skin-restart discipline.

### §6.3 Cross-corroboration with γ.5 and γ.6

G8 (adversarial owner) corroborates γ.5 anchor surface honor-system findings — when anchor surface itself is honor-system, the threat surface explodes.

G18 (catastrophic forgetting) corroborates γ.6 P10 missing principle — same problem from biological-essence angle.

G13 (aged Living Bets) corroborates γ.6 critique of §7 framing — the bet was already weak.

---

## §7. Phase γ.4 — Stranded libraries forensics

> Lens: "Phase β found three stranded libraries (kernel/skin, kernel/continuity::DormancyMachine, kernel/governance::classifier). Are they actually stranded? What's the wire-in cost?"

### §7.1 `kernel/skin`: library correct, substrate wrong

`kernel/skin/src/lib.rs` provides:
- `SkinSurface` declaration with intake/output endpoints (F11)
- Envelope schema validation
- `output_gate` for C2 (output_endpoint_breach) detection
- `egress_enforce` for C1 (appetite_locality_breach) detection
- Handshake state machine for C11 (concurrent_operator_persistent)

`myco_substrate/src/server.rs` **does not import** `myco_kernel_skin`. The substrate's send/receive paths bypass the library entirely.

**Wire-in cost**: HIGH. The substrate has a parallel ad-hoc track for skin enforcement (handshake_pubkey_mismatch detector, envelope canonical-bytes validation, scattered `state.dag.insert_node` calls). Replacing the ad-hoc track with the library requires:
- Refactoring all `state.dag.insert_node` call sites to route through `SkinSurface::output_gate`
- Replacing handshake_pubkey_mismatch with `SkinSurface::handshake_serialize`
- Adding `egress_enforce` to federation peer connection paths
- Wiring `appetite_locality_breach` detection (currently no detector)

Estimated effort: 2-3 milestones (M27.0 wire-in, M27.1 detector parity, M27.2 cleanup).

**Verdict**: library is correct; substrate is wrong; M27 cascade work confirmed.

### §7.2 `kernel/continuity::DormancyMachine`: library correct, substrate ad-hoc currently sufficient

`kernel/continuity/src/lib.rs::DormancyMachine` provides:
- Full alive ↔ dormant lifecycle (5 sub-states: Normal, Quarantined, Paused, Suspended, Legacy)
- Cycle cadence tunable per sub-state (min 100ms alive, max 100s dormant)
- Transition guards (e.g., cannot transition from Quarantined to Suspended without owner attestation)

`myco_substrate/src/server.rs` has a **primitive autonomous tick** introduced in M23.1 (mpsc::recv_timeout 500ms). It does not import `DormancyMachine` and has no explicit dormancy states beyond "running" / "shutdown".

**Wire-in cost**: MEDIUM. M23.1's primitive tick is sufficient for current single-state operation but cannot represent the 5 sub-states or transition discipline. Wire-in unlocks:
- Quarantined sub-state (currently emits immune sporocarps but doesn't change operational mode)
- Paused dormancy (currently no concept; substrate is always alive)
- Legacy sub-state from G9 / §15 (DRAFT 9 requires this)

Estimated effort: 1 milestone (M27.1).

**Verdict**: library correct; substrate ad-hoc currently sufficient but doctrine evolution (especially DRAFT 9 §15 legacy state) forces wire-in.

### §7.3 `kernel/governance::classifier`: **NOT STRANDED** — Phase β audit was WRONG

Phase β Agent 3 stated: "F1-F17 fixed-points unenforced. Python `classifier.py` exists with the right rules, but `myco_substrate` never imports `myco_kernel_governance`. Mutations to F-row fields bypass classifier entirely."

**Phase γ.4 audit found this is incorrect.** The Python classifier IS wired via the bridge:
- `kernel/governance/src/myco_kernel_governance/classifier.py` is the classifier
- `myco_substrate/src/server.rs::classify_mutation` calls into the Python worker via `kernel/bridge`
- Bridge protocol message `CLASSIFY_MUTATION` routes from server.rs → Python worker → classifier.py
- Result is encoded as DAG event `mutation:classified:{level}`

The bridge wiring was added in M11 (event-classification milestone, pre-v0.9). Phase β missed it because Agent 3 grepped for `use myco_kernel_governance` in Rust code (finds nothing — correct), but the wiring is via inter-process bridge, not Rust import.

**Correction**: kernel/governance::classifier is NOT stranded. Phase β's claim that "Mutations to F-row fields bypass classifier entirely" is false — F-row mutations route through the bridge classifier. The two genuinely stranded libraries are kernel/skin and kernel/continuity::DormancyMachine.

**Implication**: M27's scope is reduced. M27.2 (wire `kernel/governance::classifier` into I2 mutation classification path) is **no longer needed** — already wired. M27 reduces to:
- M27.0: Wire kernel/skin
- M27.1: Wire kernel/continuity::DormancyMachine

This is a real audit win: Phase γ corrected a Phase β error.

### §7.4 Phase β meta-lesson re-examined

Phase β concluded: "Building library APIs creates an illusion of completeness while the live substrate operates on a parallel, simpler track."

Phase γ.4 partially affirms but partially refutes: **kernel/skin and DormancyMachine fit this pattern; kernel/governance::classifier does not**. The illusion-of-completeness mechanism is real but bridge-wiring-without-rust-import is a legitimate pattern not captured by grep-for-use-statement audit.

**Lesson refined**: import-graph audit must include cross-language bridges (Rust → Python via kernel/bridge; Rust → TS via kernel/bridge), not just Rust use-statement grep.

---

## §8. Phase γ.5 — Anchor surface honor-system collapse

> Lens: "L0 §9 says the anchor surface is the trust root. Is the trust root mechanically enforced or honor-system?"

### §8.1 The 11 §9 sub-clauses

L0 DRAFT 8 §9 enumerated 11 sub-clauses (numbered §9.2.1 through §9.3.6 in DRAFT 9 inventory):

| # | Sub-clause | DRAFT 8 status | M25 implementation | Mechanically enforced? |
|---|---|---|---|---|
| §9.2.1 | Substrate-ID birth attestation 5-tuple | Specified | TOFU on first hello | 0% |
| §9.2.2 | DAG-tip co-signing at every CI boundary | Specified | Server emits enumeration | ~40% (closure check unwired) |
| §9.2.3 | Owner attestations out-of-band | Specified | Owner key in TS operator process (same workspace) | 0% |
| §9.2.4 | L0 revision diff workflow | Specified | L0 in git, no workflow event | 0% |
| §9.2.5 | Anchor-surface-generated nonces (NOT substrate) | Specified | **Substrate mints nonces** (server.rs:2387) | 0% — direct spec inversion |
| §9.2.6 | Anchor-stamped wall-clock | Specified | Dual-clock plumbing exists, but "anchor clock" source is the operator process | ~5% |
| §9.2.7 | Owner liveness heartbeat | Specified | `kernel/governance/heartbeat.rs` library exists, zero non-test callers | 0% |
| §9.3.1 | Canonical-bytes serialization | Specified | Implemented R/P/T; Phase β strict-order fix | ~95% |
| §9.3.2 | Owner-side rendering | Specified | `anchor_client/src/renderer.ts` library exists; no live consumer out-of-band | ~30% |
| §9.3.3 | Anchor-client provenance independence | Specified | Anchor client is in SAME npm workspace as operator bindings | 0% |
| §9.3.4 | Witnesses, not verdicts | Specified | Substrate emits pass/fail summaries | 0% |
| §9.3.5 | Anchor-nonce-derived sampling | Specified | No sampling, full enumeration | 0% |
| §9.3.6 | DAG-enumeration closure check | Specified | Server emits enumeration; closure check unwired client-side | ~40% |

**9 of 11 sub-clauses are 0-30% mechanically enforced.**

### §8.2 The single biggest discovery: operator IS anchor surface

`operator_bindings/claude_code` and `anchor_client` are in the **same npm workspace**. Same package.json. Same node_modules. Same build pipeline. The agent process can read the owner's private key from the anchor_client filesystem.

**L0 §9 opening sentence** says verbatim:

> "Without an out-of-band anchor, substrate-self-claims = agent-self-claims under P1.a self-hosting, and the entire trust model collapses."

**By L0's own definition, the trust model is currently collapsed.** The current v0.9 anchor surface is "out-of-band" only in the sense that the agent process *politely* does not read the anchor_client filesystem — not because it *cannot*.

This is not a future problem. This is the current state of v0.9.

### §8.3 DRAFT 9's response

DRAFT 9 §9.5 explicit honest acknowledgment:

> "in the **current v0.9 implementation, the anchor surface is collapsed to the operator process** — owner key lives in the same npm workspace as the agent code. This is a temporary scaffolding, not a doctrinal endpoint."

DRAFT 9 §9.2 decomposes the 11 sub-clauses into 5 future milestones:

- **M-anchor-1**: Anchor-client provenance independence — separate distribution channel, separate workspace, separate dependency tree. §9.2.3 + §9.3.2 + §9.3.3.
- **M-anchor-2**: Substrate-ID birth attestation 5-tuple — anchor-side signing key generates owner attestation over the genesis 5-tuple, substrate verifies on first hello rather than TOFU. §9.2.1.
- **M-anchor-3**: Anchor-side nonce + clock + heartbeat sources — anchor surface emits nonces and timestamps, substrate consumes. §9.2.5 + §9.2.6 + §9.2.7.
- **M-anchor-4**: Witnesses-not-verdicts emission — substrate emits Merkle paths + sampling proofs derived from anchor nonce. §9.3.4 + §9.3.5.
- **M-anchor-5**: DAG-enumeration closure + L0 revision diff workflow — anchor-side parent-edge closure verifier; L0 revisions go through anchor-attested workflow. §9.2.2 + §9.2.4 + §9.3.6.

**These 5 milestones become foundation work for M26+.** Until they are complete, the "production-readiness" claim is gated; substrate-self-claims are agent-self-claims.

### §8.4 The chained implication

If §9 is honor-system, then:
- P1.a self-hosting trust circularity is **not broken** (the whole reason §9 exists at L0)
- I3 self-validation against SSoT is honor-system at the cryptographic level (substrate validates against own state)
- I4 DAG-tip hash co-signing has no co-signer
- C5 attestation_invalid detector has nothing valid to compare against
- F4 anchor_surface_endpoint_public_key is a value the substrate stores about itself

P9 70% snapshot claim drops to ~25-30% honest accounting.

---

## §9. Phase γ.6 — Meta-framework critique

> Lens: "Is the 9-principle framework itself the correct framework? What essential organism-essence concepts are missing?"

### §9.1 6 missing principles (P10-P15)

Phase γ.6 audit applied an **organism-essence checklist** drawn from biological literature + cybernetic-substrate theory:

| Essential concept | DRAFT 8 principle | Status | DRAFT 9 principle |
|---|---|---|---|
| Causality | P6 | ✓ Present, defensible | P6 unchanged |
| Mortality | P7 | ✓ Present | P7 renamed "Mortality (Capacity-for-Death)" |
| Reproduction | P8 | ✓ Present | P8 renamed "Eternal Reproduction (Generation-Bounded)" |
| Boundary integrity | P9 | ✓ Present | P9 renamed "Single Integument" |
| **Selective compression** (forgetting) | ABSENT | DRAFT 8 forbade pruning (I4 + F9) | **P10 NEW** |
| **Metabolic economy** (energy budget) | ABSENT | DRAFT 8 had "eternal ingestion + no filter" = deferred bankruptcy | **P11 NEW** |
| **Differential response** (attention) | ABSENT | P2 admits everything equally → noise hoarding | **P12 NEW** |
| **Embodiment** (spatial locus) | ABSENT | Phase α gap #1 | **P13 NEW** |
| **Telos** (substrate-internal purpose) | ABSENT | "For the agent" but no internal purpose declared | **P14 NEW** |
| **Population consensus** | ABSENT | Federation pairwise only | **P15 NEW** |

**6 essential organism-essence analogues missing from DRAFT 8.** A "species" framework that lacks forgetting, metabolic cost, attention, embodiment, purpose, and population-level agreement is **not a species** — it is a sediment.

DRAFT 9 brings the framework to **15 principles** (was 9). All 6 are mapped to invariants I9-I12 (with P13 doubly enforced by I8 + I10, and P15 enforced by I7 extension).

### §9.2 §1 species claim FALSE in 4 ways

DRAFT 8 §1 framed Myco as **"a literal taxonomic class within digital organisms"**. Phase γ.6 critique found this rhetorically maximalist + false in 4 ways:

#### Way 1: No chemical energy
Real organisms have ATP cycles, mitochondrial respiration, chemical regulation. Myco operates within software-bounded resource budgets (disk, compute, network). "Metabolism" is a metaphor; chemical energy is not present.

#### Way 2: No embodied sensorimotor loop
Real organisms have receptors + effectors + spatial extension into environment. Myco has filesystem + process + network endpoints. There are no sensors in the biological sense.

#### Way 3: No enzymatic regulation
Real organism behavior emerges from enzymatic specificity + concentration gradients + feedback loops. Myco behavior is determined by Rust code paths + Python classifier dispatch + canonical-bytes serialization. "Tropism" is a metaphor; chemotaxis is not present.

#### Way 4: No neural substrate
Real organisms (above worms) have neural networks with synaptic plasticity. Myco has no internal model that learns; the "agent" using Myco has a neural substrate (the LLM), but Myco itself does not.

**DRAFT 9 §1.1 / §1.2 honesty calibration**: Myco is described as "biology-rooted symbiotic digital substrate" with "the principles P1-P15 describe a substrate inspired by biology, not biology itself". The word "organism" appears as "vocabulary of inspiration, not classification".

### §9.3 §7 Living Bets bet already weak

Phase γ.6 audit found DRAFT 8 §7 specified signal #6 seed at ~100 (substrate-total / context-window). M25-era 1M-context Claude has signal #6 ≈ 1 from day one — already in DRAFT 8's "bet-losing region".

The bet was structurally weakening before substrate's first metabolic cycle. DRAFT 9 §7 substantial recalibration:
- §7.1 cost-justified value framing
- §7.2 intelligence band (lower edge ~200K, upper edge ~10M)
- §7.3 cost signals (compute, network, storage)
- §7.4 falsifiability trigger corrected (90-day wall-clock, signal-specific direction)
- §7.5 bet retirement (graceful sunset above band)

**The single most defensible principle**: γ.6 audit found **P6 Eternal Causality** is the principle Myco delivers most defensibly. The Merkle DAG, the canonical-bytes serialization, the causal_parent_hashes — all are mechanically enforced + tested. P6 survives every level of audit. Most other principles have at least one honor-system clause.

### §9.4 The framework completeness gap

DRAFT 8 was **9 / 15 essential principles** by Phase γ.6 organism-essence audit. That is **60% completeness** at the framework level. Combined with implementation drift (Phase β + Phase γ.2), the substrate's honest position is:

- Framework completeness: ~60% (9/15)
- Implementation completeness within DRAFT 8 framework: ~72-75% (M25 claim) → revised ~50-55% after Phase γ
- Implementation completeness within DRAFT 9 framework: even lower (P10-P15 unimplemented)

**Honest distance to ideal (DRAFT 9 framework)**: ~30-40%.

---

## §10. Phase γ.7-γ.16: DRAFT 9 work

> Phases γ.7 through γ.16 are the **drafting + critique passes** that converted Phase γ findings into the L0 DRAFT 9 PROPOSAL.

### §10.1 Drafting passes (γ.7-γ.13)

- **γ.7**: Drafted P10 Selective Compression + I9 Compression Discipline. Cross-checked with I4 retention clause; defined compression-invariant set (P10.b).
- **γ.8**: Drafted P11 Metabolic Economy + I10 Metabolic-Economy Observation. Cross-checked with §7 Living Bets cost signals.
- **γ.9**: Drafted P12 Differential Response + I11 Differential-Response Discipline. Cross-checked with P2 admission (non-overlap clarified).
- **γ.10**: Drafted P13 Embodiment (Minimum-Viable). Cross-checked with P9 Single Integument; non-overlap clarified (P9 = what crosses boundary; P13 = what spatial extent boundary encloses).
- **γ.11**: Drafted P14 Telos (Agent-Symbiotic-Flourishing) + I12 Telos Alignment. Acknowledged operationalization fuzziness (G-6 gate).
- **γ.12**: Drafted P15 Population-Level Consensus. Acknowledged single-substrate exemption (P15.c).
- **γ.13**: Drafted §13 time semantics + §14 adversarial owner + §15 owner mortality + §16 generation limits.

### §10.2 6-critic review rounds (γ.14)

DRAFT 9 was reviewed by 6 critic-pass agents in parallel:
- Critic 1: P10 + I9 self-consistency vs P10.b compression-invariant set
- Critic 2: P11 + I10 cost-signals vs §7 observatory integration
- Critic 3: P12 vs P2 non-overlap + I11 vs L1_TROPISM dispatch
- Critic 4: P13 vs P9 non-overlap + P13 vs P11 non-overlap
- Critic 5: P14 telos operationalization + I12 vs L1_TROPISM target
- Critic 6: P15 consensus floor vs federation pairwise + I7 extension

Critique passes generated ~30 minor revisions (clarifications, non-overlap statements, operational concession notes). All major principles survived all 6 critic passes.

### §10.3 Cascade list construction (γ.15-γ.16)

DRAFT 9 §17 enumerates 8 explicit owner-decision gates G-1 through G-8. Each gate has a default (DRAFT 9 v1 settings) + alternatives.

The cascade-work list (M26-cascade) was constructed:
- **M-anchor-1 through M-anchor-5**: anchor surface foundation (γ.5)
- **L1_GOVERNANCE alignment with DRAFT 9 §14 + §15**: adversarial-owner + owner mortality cascade
- **L1_CONTINUITY alignment with DRAFT 9 §13**: time semantics cascade
- **L1_SKIN alignment with DRAFT 9 P13**: embodiment cascade
- **L1_TROPISM alignment with DRAFT 9 P12 + P14**: differential response + telos cascade
- **L2_FEDERATION alignment with DRAFT 9 P15**: consensus protocol cascade
- **L2_OBSERVABILITY alignment with DRAFT 9 §7 cost signals + I10**: observatory cost-signals cascade
- **L3 cascade**: implementation map updates for P10-P15 + I9-I12
- **L4 cascade**: immune-system additions for new C-rows under DRAFT 9

---

## §11. Honest distance metrics (post-Phase γ)

### §11.1 Distance to ideal accounting

| Metric | Pre-Phase γ (M25 snapshot) | Post-Phase γ honest |
|---|---|---|
| Machine-confirmable | ~72-75% | **~50-55%** |
| Framework completeness | implicit 100% (9-principle was assumed complete) | **~60%** (9/15 essential principles per DRAFT 9) |
| Combined honest distance | implicit ~72-75% | **~30-40%** |
| Weakest-link principle | P8 at 45-50% | **P1 ~25%** (collapsed anchor surface drags down whole P1 chain) |
| Strongest principle | P6 at 100% | P6 at 100% (unchanged; the most defensible) |

### §11.2 The 20-point gap explained

Pre-Phase γ M25 snapshot reported ~72-75% machine-confirmable. Post-Phase γ honest assessment is ~50-55%. The 20-point gap is **not bug regression** — it is the cost of:

1. **Anchor surface honor-system collapse acknowledged** (γ.5): P9 70% → ~25-30%, dragging down weighted-average machine-confirmable
2. **5 CRITICAL bugs found in M25** (γ.2): C1-C6 all silently passed tests
3. **6 missing principles** (γ.6): framework expanded to 15; what was 9/9 is now 9/15 = 60% framework completeness
4. **12 new structural gaps** (γ.3): each gap represents an aspect of "ideal" that DRAFT 8 didn't articulate

The honest position is: **Myco at M25 is ~30-40% of DRAFT 9's ideal**. Pre-Phase γ accounting was over-claim because the ideal-set itself was thinner than honest.

### §11.3 Weakest-link recalibration

Pre-Phase γ: P8 at 45-50% was weakest-link (federation reproduction; M25.4 raised to ~60% via Ed25519 mutual auth).

Post-Phase γ: **P1 at ~25%** is weakest-link because:
- P1.b'' (governance gate) depends on anchor surface (§9)
- Anchor surface §9 is 9-of-11 sub-clauses 0-30%
- The collapse of §9 → P1.b'' → P1 chain drags P1 to ~25% honest

The 5 new principles P10-P15 are unimplemented (0%) but are not weakest-link because they have no prerequisite chain that other principles depend on (yet).

---

## §12. M26+ roadmap revision

> Phase γ findings forced major roadmap revision. Pre-Phase γ roadmap (M26 Phase β residual hardening + drill baseline; M27 stranded libraries; M28+ features) is **superseded**.

### §12.1 New roadmap

**M26-cascade**: align L1/L2/L3 docs with DRAFT 9 (assuming owner approves DRAFT 9). This is the **first work** after DRAFT 9 sealing.

- M26-cascade.0: L1_GOVERNANCE update for §14 adversarial-owner + §15 owner mortality + §16 generation limits
- M26-cascade.1: L1_CONTINUITY update for §13 time semantics + DRAFT 9 dormancy sub-states
- M26-cascade.2: L1_SKIN update for P13 embodiment + P9.b single-failure-acknowledgment
- M26-cascade.3: L1_TROPISM update for P12 differential response + P14 telos alignment
- M26-cascade.4: L2_FEDERATION update for P15 population-level consensus + signal #4 cost-signals
- M26-cascade.5: L2_OBSERVABILITY update for §7 cost signals + I10 + I11 + I12

**M-anchor-1 through M-anchor-5**: anchor surface foundation work (γ.5 decomposition).

- M-anchor-1: anchor-client provenance independence (separate workspace, separate distribution)
- M-anchor-2: substrate-ID birth attestation 5-tuple
- M-anchor-3: anchor-side nonce + clock + heartbeat sources
- M-anchor-4: witnesses-not-verdicts emission
- M-anchor-5: DAG-enumeration closure + L0 revision diff workflow

**M25 5 CRITICAL bug fixes**: deferred to post-DRAFT-9-sealing (C1, C2, C3, C4, C5, C6).

**M27 (stranded libraries, revised)**:
- M27.0: Wire kernel/skin
- M27.1: Wire kernel/continuity::DormancyMachine
- M27.2 REMOVED (kernel/governance::classifier already wired via bridge; Phase β error corrected)

**M28 new principle implementations**:
- M28.0: P10 Selective Compression mechanism (compression-invariant set + CI-attested compression event)
- M28.1: P11 Metabolic Economy cost signals (signals 7-9 added to observatory)
- M28.2: P12 Differential Response (L1_TROPISM salience-emergence)
- M28.3: P13 Embodiment (body integrity detection)
- M28.4: P14 Telos alignment metric
- M28.5: P15 Population-level consensus (depends on federation ≥3 peers)

**M29+ deferred features** (cross-pollination, autonomous schema evolution, vector retrieval native):
- These were already deferred pre-Phase γ; deferral confirmed

### §12.2 Discipline: no new features until DRAFT 9 sealed + cascade aligned

Pre-Phase γ discipline: "First give substrate eyes (M24) → substrate watches itself drift (M25) → only then debate features."

Post-Phase γ discipline tightened: **"First DRAFT 9 closes ideal-set; only then resume implementation. Implementation chasing thin doctrine produces drift."**

The discipline is: implementation cannot lead doctrine. When Phase α + β + γ found doctrine-implementation drift, the implementation pause is the response. M26 cascade work is **doctrine-implementation-realignment**, not new features.

---

## §13. The meta-pattern

The three audits collectively form a **recursive audit ladder**:

```
Phase α (2026-05-15):
  Trigger: "is our ideal correct?"
  Drift class: maintainer mental model ↔ L0 doctrine
  Mechanism: read L0 directly vs read my abstraction of L0
  Found: my abstraction was thinner than actual L0

Phase β (2026-05-15):
  Trigger: "spawn many parallel agents because cognitive drift hides bugs"
  Drift class: implementation ↔ L0+L1+L2 doctrine
  Mechanism: 6 agents read source files directly vs trust library APIs
  Found: implementation was thinner than the doctrine it claimed to embody

Phase γ (2026-05-17):
  Trigger: "is our ideal comprehensive and correct?" (same as Phase α)
  Drift class: doctrine ↔ honest accounting of completeness AND ideal-set blind spots
  Mechanism: 6 agents audit doctrine self-consistency + organism-essence completeness
  Found: doctrine itself had blind spots (anchor surface honor-system + 6 missing principles + 12 unaddressed gaps)
```

**Each phase finds a different drift class.** The pattern is recursive:
- α: my model of the doctrine drifts from the doctrine
- β: the implementation drifts from the doctrine
- γ: the doctrine drifts from the honest ideal

The fourth phase, if it occurs, will likely find: **the honest ideal drifts from operational reality** (DRAFT 9's ideal-set, even if accepted, will have gaps revealed by operational experience over time).

The audit pattern is the substrate's recursive self-correction mechanism. Phase γ adds doctrine-itself as an audited object.

### §13.1 The trigger pattern

Both Phase α and Phase γ were triggered by the **same owner question**: "is our 'ideal' comprehensive and correct?" Phase α triggered the recursive audit; Phase γ triggered it again after M22-M25 implementation work.

This is the meta-vigilance pattern. The owner's recurring meta-question is the substrate's external audit trigger. The substrate cannot self-trigger this question; it requires owner external impulse.

### §13.2 The cumulative discipline

After three audits, the commitment is:
- **No new features until DRAFT 9 sealed + M26-cascade complete + M-anchor-1..5 complete**
- **All future feature milestones must produce ≥1 audit step before merging**
- **The recursive audit ladder is the substrate's quality discipline**, not a one-time event

This is structurally what "first give substrate eyes" meant. Phase α+β+γ are the substrate gaining eyes; M26 cascade work makes those eyes look at honest accounting; subsequent features can build only on the foundation that survives all three audit phases.

---

## §14. Owner-decision gates (DRAFT 9 §17 reference)

DRAFT 9 sealing is gated on owner explicit decision at 8 gates. The full gate texts are in `docs/architecture/L0_VISION.md` §17; this audit references them for completeness.

| Gate | Subject | DRAFT 9 default | Alternative |
|---|---|---|---|
| G-1 | Framework expansion scope (15 principles?) | G-1.a accept all 15 | G-1.b retract P15 / G-1.c retract P13 / G-1.d retract P14 / G-1.e retract P12-P15 |
| G-2 | Species claim framing | G-2.a "biology-rooted symbiotic digital substrate" | G-2.b restore "literal taxonomic class" / G-2.c alternative |
| G-3 | Living Bets recalibration | G-3.a accept full (band + cost-justified + retirement) | G-3.b accept band + cost-justified, retract retirement / G-3.c restore DRAFT 8 |
| G-4 | Anchor surface decomposition scope | G-4.a accept L0 decomposition into 6 sub-mechanisms | G-4.b decomposition stays L1 (monolithic §9 at L0) |
| G-5 | New L0 sections §13-§16 | G-5.f keep all four at L0 (recommended) | G-5.b-e push individually to L1 |
| G-6 | P14 operationalization risk | G-6.a accept fuzzy | G-6.b require concrete metric / G-6.c retract P14 |
| G-7 | P15 consensus floor | G-7.a accept ≥3 peers threshold | G-7.b raise to ≥5 / G-7.c retract P15 |
| G-8 | §15.5 orphan terminal state | G-8.a accept 730-day bet-retirement/self-euthanasia | G-8.b extend to indefinite orphan |

**Each gate has a default**: if owner does not respond within review period, DRAFT 9 v1 settings prevail. Owner explicit affirmation strengthens the seal.

---

## §15. Test totals at Phase γ completion

| Surface | Runner | Count | Status |
|---|---|---|---|
| Rust workspace | `cargo test --workspace --release` | 424 | 0 fail (unchanged from M25) |
| Python | `python -m pytest -q` | 361 | 0 fail (unchanged) |
| TS operator_bindings | `npm test` | 147 | 0 fail (unchanged) |
| TS anchor_client | `npm test` | 162 | 0 fail (unchanged) |
| **Total** | | **1094** | **0 fail** |

Phase γ added **zero tests** because it is a meta-audit — no code changes. All findings translate to DRAFT 9 PROPOSAL + cascade-work list. Implementation work resumes only after DRAFT 9 sealing.

---

## §16. Closing — what Phase γ leaves behind

Phase γ leaves three artifacts:

1. **L0 DRAFT 9 PROPOSAL** (`docs/architecture/L0_VISION.md`, 953 lines) — pending owner approval at 8 gates
2. **This audit document** (`docs/audits/phase_gamma_audit_2026-05-17.md`) — historical record + git-archived archaeology
3. **The cascade-work list** (M26-cascade + M-anchor-1..5 + M28 principle implementations) — committed roadmap for the next milestone block

The pattern that keeps proving itself, refined for Phase γ:

> **"First give the substrate eyes. Then the substrate watches itself drift. Then watch the doctrine itself drift from honest. Then debate features."**

M22-M25 gave substrate eyes. Phase γ watched the doctrine itself drift. M26+ is the doctrine-realignment cascade. **Features remain deferred until M26-cascade + M-anchor-1..5 complete.**

The substrate's existential bet (L0 §7 / DRAFT 9 §7) survived Phase γ recalibration — the intelligence band is acknowledged, cost-justified value is the new framing, bet retirement (§7.5) is the graceful sunset. **The bet remains alive but explicitly bounded**: above ~10M context, Sutton's bitter lesson dominates and the substrate retires.

This is the second consecutive recursive-audit cycle. The pattern is now load-bearing: substrate quality discipline = audit recursion + DRAFT-cycle discipline + cascade-work-before-features.

---

**END OF PHASE γ AUDIT.**

**Cumulative commitments through Phase γ: #1-#155 (M25) + #156-#172 (Phase γ additions for DRAFT 9 traceability) = 172 commitments.**

The substrate proceeds to M26-cascade upon owner sealing of DRAFT 9 at the 8 gates.
