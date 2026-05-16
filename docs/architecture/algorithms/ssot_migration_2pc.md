# `ssot_migration_2pc` — Two-phase commit for SSoT designation evolution

> **Status**: REFERENCE ALGORITHM. Extracted from L1_SCHEMA §1.3 to keep active doctrine lean. Authoritative spec lives at **L1_SCHEMA §1.3** (commitment) + this file (consolidated algorithm).

---

## §1. Parameter

- `M` = required count of consecutive successful dual-validation cycles. Seed `M_default = 100`. L4-tunable in [100, 10000]; outside requires CI mutation. `M` is tier-1 SSoT (L1_SCHEMA §4.1).

## §2. Phase 1 — Dual-validation accumulation

1. Cultivator co-signs `ssot_migration_proposal` with canonical-bytes of `(current_designation, candidate_designation)` per L1_GOVERNANCE §2.2.
2. Substrate runs dual-validation every metabolic cycle: both current + candidate designations MUST produce self-consistent I3.
3. On mismatch in any cycle: emit `ssot_migration_inconsistent` immune sporocarp; reset consecutive-success counter to 0; abort proposal.
4. Phase 1 succeeds iff ≥ `M` consecutive successful cycles observed (counter resets on inconsistency).

## §3. Phase 2 — Commit

5. Cultivator co-signs `ssot_migration_commit` per §2 attestation, payload:
   ```
   {
     "current_canonical_bytes_hash": <hash>,
     "candidate_canonical_bytes_hash": <hash>,
     "M_consecutive_count_observed": <≥ M>,
     "dual_validation_witness_sample": <anchor-nonce-derived sample of cycles>
   }
   ```
6. On commit: candidate becomes active SSoT designation. Old SSoT designation retained per I4 causal coverage (joins P10.b compression-invariant set per L0 P10.b + L1_GOVERNANCE F18).

## §4. Witnesses-not-verdicts

Substrate emits Merkle proof of `M` Phase-1 cycles + sampled comparisons (indices anchor-nonce-derived per L0 §9.2.5). Substrate does NOT emit a self-asserted `phase_1_passed` flag. Cultivator verifies the proof at anchor-side.

## §5. Cascade

- L1 commitment: L1_SCHEMA §1.3.
- L1 attestation envelope: L1_GOVERNANCE §2.2 (`ssot_migration_proposal`, `ssot_migration_commit`).
- L1_HARD_RULES C-row: C8 `ssot_migration_phase_skip` — fires when Phase 2 commit observed without prior Phase 1 evidence.
- Compression-invariant set: P10.b (retained old SSoT designation).
