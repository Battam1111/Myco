# L1 — Skin (envelope, handshake, single-operator, breach detection, spatial-locus, backup, restart)

> L1 for boundary surface (I8). All numeric thresholds L1-tunable unless specified.
> **Scope**: envelope; intake/output; operator handshake; single-operator; non-deterministic operator-token; network-egress; spatial-locus (P13 folded into P9+I8); backup encryption (L0 §11.1); skin-restart (P9.b); breach detection. Excludes: classifier crypto (L1_GOVERNANCE), SSoT (L1_SCHEMA), cycle cadence/cold-resume (L1_CONTINUITY).

---

## §1. Skin surface declaration

Substrate MUST declare exactly one skin surface in SSoT (tier-1 field): **intake endpoints** (Unix socket, named pipe, TCP port); **output endpoints** (federation peers, anchor endpoint, optional summary export); **forbidden surfaces** (everything else IS breach). CI; no silent addition.

## §2. Envelope schema

Schema: `schemas/skin_envelope.json` (8 fields + payload; envelope wraps every delta at intake).

**§2.1 Integrity check** (I8 + P2): all required fields present; `sender_token` matches active token (§4); `payload_shape` in recognized set; `size_bytes` ≤ default 100 MB; `envelope_digest` recomputes via HMAC; `submitted_at_cycle` within freshness window (default 60 cycles, per L0 §13.1). Failure → `envelope_malformed` (no oracle disclosure).

> Boundary (P2 vs P12): skin admits-or-rejects = P2. Downstream selective attention = P12 (L1_TROPISM).

**§2.2 Causal-parent reference**: `causal_parent_ref` non-null MUST refer to recent sporocarp in most-recent digest. Ancient/non-existent → `causal_chain_violation`.

## §3. Output gating

Outputs leave via declared endpoints; signed by substrate identity key. Anchor outputs carry canonical bytes (L0 §9.3.1); emit cryptographic-proof tuples not verdicts (L0 §9.3.4).

**§3.1 Federation egress freshness**: Every outbound federation envelope MUST verify target freshness + non-revocation BEFORE emission. Stale/revoked → `federation_egress_blocked`. Content uses sorted-key, normalized-whitespace, fixed-precision-numeric serialization (covert-channel limit).

**§3.2 Forbidden output**: Anything outside declared endpoints IS breach.

## §4. Operator handshake protocol (bidirectional)

**§4.1 Initiation + operator key bootstrap**: Operator per-handshake signing keypair: runtime generates fresh; private in runtime-memory only (never disk/transmitted); public in `handshake_initiate` envelope carrying `(envelope_version, operator_kind="handshake_initiate", substrate_id_proof, operator_signing_key_public, operator_attestation_request, continuity_claim, submitted_at)`. Substrate cross-checks `submitted_at`; skew > default ±300s vs anchor trusted-timestamp → `time_source_drift`. Operator pubkey-pinning at bootstrap: owner provides `(substrate-ID, anchor-endpoint-pubkey, owner-pubkey)` out-of-band at first install; operator pins; NEVER trusts owner-pubkey from substrate handshake. Mismatch → `substrate_id_mismatch` + rejection.

**§4.2 Substrate response — bidirectional validation**: Substrate MUST: (1) validate `substrate_id_proof`; (2) derive **non-deterministic operator_token** via `operator_token = sealed_derive(handshake_nonce, current_cycle, kernel_random)` kernel-mediated into {TPM, OS keyring, HSM, hardware-secure-element} — substrate_secret never in process address space plaintext; plaintext-on-disk IS CRITICAL (`substrate_secret_unsealed`); sealing attestation owner-attested at genesis; protects against adversarial agent, NOT adversarial Cultivator; (3) emit `handshake_complete` carrying `(operator_token, substrate_id, owner_birth_attestation_signature, owner_public_key_active_at_handshake, anchor_surface_endpoint_public_key, handshake_timestamp)` — operator fetches owner pubkey from anchor (pinned anchor key), verifies signature, mismatch → rejects; (4) record handshake as sporocarp.

**§4.3 Continuity-challenge**: `continuity_claim: "owner_attested_continuity"` → envelope MUST include owner-signed `continuity_attestation`; verified → quarantine shortened to default 10 cycles. Otherwise: post-handshake quarantine window default 100 cycles; all CI requires fresh attestation.

**§4.4 Single-operator + race handling**: Per I8: skin admits at most one operator-token. Second handshake during active → `skin_busy` + `concurrent_connect_attempt`. Same-cycle A/B tiebreak by OS-accept-queue order (strict FIFO at socket; single-threaded skin enforcer). Nonce-content tiebreak FORBIDDEN.

**§4.5 Disconnect detection**: Explicit `handshake_terminate` (MAY include `request_dormancy: paused | throttled`); idle timeout (default 100 cycles); transport failure. Disconnect → alive → dormant per L1_CONTINUITY §2.

## §5. Network-egress enforcement (I6; P13-folded second hook)

Substrate MUST operate within egress boundary permitting exactly §1 declared endpoints. Unauthorized egress IS breach — simultaneously I6 + P9+I8 spatial-locus breach. Fires `appetite_locality_breach` (§5); MAY co-fire `P9_spatial_locus_breach` (§6) if destination undeclared host/port.

L4-platform ∈ {kernel-level (netns), container (iptables/nftables), syscall (eBPF/ptrace), userspace proxy}. **Prevents**: secret callouts, embedding service calls outside declared endpoint, covert exfiltration. **Does NOT prevent**: agent-maintainer source modification (CI); host-level adversarial action; covert channels in legitimate federation envelopes.

## §6. Spatial-locus enforcement (P13 folded into P9 + I8)

Substrate MUST periodically list own spatial locus, compare against declared allowed-set. Deviation → `P9_spatial_locus_breach` immune; CRITICAL → §9 quarantine.

- **state_dir allowed**: `{"dag.cb", "snapshot.cb", "substrate_signing_key.cb", "*.tmp", "*.tmp.<pid>", ".gitignore"}`.
- **OS-noise allowed**: `{".DS_Store", "Thumbs.db", "desktop.ini", "*.lock", ".tmp/*", ".lockfile"}` → `spatial_locus_noise_observed` (Daily).
- **FD allowed**: state_dir files; skin sockets; sealed-key handles; stdin/stdout/stderr. Other → `P9_spatial_locus_breach:fd_unexpected:{fd_kind}`.
- **Network binding allowed**: §1 listening; outbound matches §1 output OR anchor OR federation peer in signed list. Outside → `P9_spatial_locus_breach:network_unexpected:{peer}`.
- **Cadence**: default once per cycle. Allowed-set extensions CI; silent extension IS breach.
- **Birth-period + cold-resume**: transient unknown files → `spatial_locus_birth_period_pending` (Daily); owner quarantine-clearance enumerates canonical. Cold-resume: spatial-locus IS pre-handshake witness — file/fd/binding lists as cryptographic-proof tuples.

Excluded: inside-file content drift; CPU/memory/disk budgets (L2_OBSERVABILITY); agent-side source tampering (L0 §14).

## §7. Skin-restart discipline (P9.b)

- **Process supervision (L4)**: external supervisor restarts on crash/OOM-kill/operator-requested cycle (Linux systemd/runit/s6; macOS launchd; Windows sc.exe/NSSM; orchestrator restart-policy). L1 commits external-supervisor shape; substrate does NOT self-restart.
- **Ordered shutdown** on SIGTERM: (1) stop accepting envelopes; (2) drain in-flight up to default 30s; in-transit → `skin_draining` + dead-letter; (3) flush WAL + persist DAG + snapshot.cb + fsync; (4) close output endpoints — peers receive `skin_restart_pending`; (5) emit `skin_restart_started` (Daily); (6) exit 0. Hard-kill → L1_CONTINUITY §4 WAL replay.
- **Recovery on restart**: cold-resume pre-handshake checks (L1_CONTINUITY §3.1); spatial-locus enumeration (§6); WAL recovery (L1_CONTINUITY §4); re-open intake; `dormant → alive`; await handshake; emit `skin_restart_completed` (pre/post cycle MUST equal).
- **Anti-flap rate limit**: ≥ default 5 `skin_restart_completed` within default 1 hr window → `skin_restart_flap` (CRITICAL); refuses re-open until owner `flap_clearance`.

**§7.5 Skin-restart observability events**:

| Event | Grade | When | Witnesses |
|---|---|---|---|
| `skin_restart_started` | Daily | After shutdown signal, before exit | drain stats, snapshot hash, reason |
| `skin_restart_completed` | Daily | After restart, before re-open | pre/post cycle, WAL outcome, spatial-locus outcome |
| `skin_restart_flap` | CRITICAL | §7.4 exceeded | restart timestamps, window, threshold |
| `skin_restart_dead_letter` | Elevated | Per dead-lettered envelope | envelope digest, reason |

Excluded: owner-initiated graceful destruction (L1_GOVERNANCE §4 mortality — terminal); P7 self-euthanasia (supervisor MUST not restart).

## §8. Backup encryption (per L0 §11.1)

Cultivator-controlled symmetric encryption key; substrate NEVER mints. L1 commits:

- **Key custody**: Cultivator generates locally at genesis (AES-256-GCM or XChaCha20-Poly1305); substrate stores only public-derivation pointer (key-ID) in SSoT; key never in state_dir. Operator-runtime encrypts; substrate provides plaintext canonical-bytes.
- **Key escrow + rotation**: Cultivator MAY declare anchor-signed `key_escrow = (escrow_method ∈ {M-of-N Shamir, time-locked hardware token, attorney-held envelope, successor-Cultivator-co-signed}, escrow_parameters, escrow_attestation)`. No escrow → key-loss recovery impossible; acceptable iff explicit. Rotation coordinates with owner anchor-key rotation (default 30-day cooldown). SSoT `backup_key_id_history` (active-prefix + archived-tail).
- **Access + integrity**: restrictive permissions (`umask 077`; Unix `0600`); loose → `backup_permissions_loose` (Elevated). Undeclared destinations → `output_endpoint_breach`. Backup carries snapshot.cb hash signed by substrate key; tampered/truncated → `backup_integrity_failure`.
- **Absent-encryption acknowledgment**: SSoT `backup_encryption_status = "cultivator_declined_explicit"` with Cultivator-signed declination; silent omission → `"unspecified"` → `backup_encryption_undeclared` (Daily).

Excluded: in-process memory encryption; backup-transit encryption (L4); post-quantum readiness (L4).

## §9. Breach detection table

| Breach | Detection | Immune-event | Grade |
|---|---|---|---|
| Envelope malformed | §2.1 | `envelope_malformed` | Daily |
| Stale envelope replay | §2.1 freshness | `envelope_replay` | Elevated |
| Time-source drift exceeds threshold | §4.1 | `time_source_drift` | Elevated |
| Wrong substrate-ID claim | §4.2 step 1 | `substrate_id_mismatch` | Elevated |
| Concurrent connect attempt | §4.4 | `concurrent_connect_attempt` | Elevated |
| Substrate-secret in plaintext on disk | §4.2 | `substrate_secret_unsealed` | CRITICAL |
| Unauthorized network egress (packet layer) | §5 | `appetite_locality_breach` | CRITICAL |
| Output outside declared endpoint | §1 + §3 | `output_endpoint_breach` | CRITICAL |
| Causal-chain violation | §2.2 | `causal_chain_violation` | Elevated |
| Post-handshake CI without fresh attestation | §4.3 | `post_handshake_ci_unattested` | CRITICAL |
| Federation egress to stale/revoked peer | §3.1 | `federation_egress_blocked` | Elevated |
| Federation egress volume saturation | L1_GOVERNANCE §5.3 | `federation_egress_saturation` | Elevated |
| Spatial-locus breach (state_dir file) | §6 | `P9_spatial_locus_breach:file_unexpected:{path}` | CRITICAL |
| Spatial-locus breach (process FD) | §6 | `P9_spatial_locus_breach:fd_unexpected:{fd_kind}` | CRITICAL |
| Spatial-locus breach (network binding) | §6 | `P9_spatial_locus_breach:network_unexpected:{peer}` | CRITICAL |
| Spatial-locus OS-noise observed | §6 | `spatial_locus_noise_observed` | Daily |
| Spatial-locus birth-period pending | §6 | `spatial_locus_birth_period_pending` | Daily |
| Skin-restart flap (rate-limit exceeded) | §7 | `skin_restart_flap` | CRITICAL |
| Skin-restart dead-letter on shutdown | §7 | `skin_restart_dead_letter` | Elevated |
| Backup permissions loose | §8 | `backup_permissions_loose` | Elevated |
| Backup encryption undeclared | §8 | `backup_encryption_undeclared` | Daily |
| Backup integrity failure on restore | §8 | `backup_integrity_failure` | CRITICAL |

Cross-layer immune signals (`salience_collapse`, `telos_drift`, `compression_invariant_corruption`, `compression_unattested`, `budget_exhausted:{axis}`, `generation_depth_exceeded`, `consensus_floor_bypass`, `bet_retired`) surface in respective detector docs. CRITICAL breaches → immediate skin-level quarantine per L1_CONTINUITY §5.

---

## §10. Doc-private terms

**Spatial locus** = `state_dir + process + skin endpoints` (§6); **Skin endpoints** = `(intake, output, anchor-surface, federation, backup-output)` per §1 + §8; **Single integument** = P9 one declared skin surface, no redundancy, process-level restartability (P9.b).
