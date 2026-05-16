# L1 — Skin (envelope, handshake, single-operator, breach detection, spatial-locus, backup, restart)

> **Status**: DRAFT 3. L1 for boundary surface (I8). Governed by L0. Cultivation vocabulary at L0 §1.2.
> **Scope**: envelope; intake/output; operator handshake; single-operator; non-deterministic operator-token; network-egress; spatial-locus (P13 folded into P9+I8); backup encryption (L0 §11.1); skin-restart (P9.b); breach detection. Excludes: classifier crypto (L1_GOVERNANCE), SSoT (L1_SCHEMA), cycle cadence/cold-resume (L1_CONTINUITY).

---

## §1. Skin surface declaration

Substrate has exactly one declared skin surface in SSoT (tier-1 field): **intake endpoints** (Unix socket, named pipe, TCP port); **output endpoints** (federation peers, anchor endpoint, optional summary export); **forbidden surfaces** (everything else is breach). CI; no silent addition.



## §2. Envelope schema

Every delta at intake is wrapped:

```
{
  "envelope_version": <integer>,
  "sender_token": <operator-token from handshake>,
  "payload_shape": <"text" | "file_ref" | "structured_yaml" | "binary_ref" | ...>,
  "causal_parent_ref": <prior sporocarp ID or null at first delta after handshake>,
  "size_bytes": <delta size>,
  "content_type_hint": <MIME-style or null>,
  "submitted_at_cycle": <substrate metabolic-cycle counter>,
  "envelope_digest": <HMAC(operator_token, canonical_envelope_fields || payload)>,
  "payload": <delta content>
}
```

### §2.1 Envelope integrity check

Substrate validates only the envelope (I8 + P2):

- All required fields present; `sender_token` matches active token (§4); `payload_shape` in recognized set; `size_bytes` ≤ L1-tunable (default 100 MB); `envelope_digest` recomputes via HMAC; `submitted_at_cycle` within freshness window (default 60 cycles, per L0 §13.1).

> Boundary (P2 vs P12): skin admits-or-rejects = P2. Downstream selective attention = P12 (L1_TROPISM). Confusing → salience collapse.

Failure → `envelope_malformed` (no oracle disclosure of which field).

### §2.2 Causal-parent reference

`causal_parent_ref` non-null must refer to recent sporocarp in most-recent digest. Ancient/non-existent → `causal_chain_violation`.

## §3. Output gating

Outputs leave via declared output endpoints; signed by substrate identity key. **Canonical-bytes** (L0 §9.3.1): anchor outputs carry canonical bytes; client renders deterministically. **Witnesses-not-verdicts** (L0 §9.3.4): anchor outputs emit cryptographic-proof tuples (sampled hashes, Merkle paths, parent hashes), never verdicts.

### §3.1 Federation egress freshness check

Every outbound federation envelope verifies target peer freshness + non-revocation per L1_GOVERNANCE §5.2 BEFORE emission. Stale/revoked → `federation_egress_blocked`. Anchor-surface negative-revocation proof required. Content uses sorted-key, normalized-whitespace, fixed-precision-numeric serialization (covert-channel limit; L1_GOVERNANCE §5.3).

### §3.2 Forbidden output

Anything outside declared endpoints is breach.



## §4. Operator handshake protocol (bidirectional)

### §4.1 Initiation + operator key bootstrap

Operator per-handshake signing keypair: runtime generates fresh; private in runtime-memory only (never disk/transmitted); public in handshake_initiate.

```
{
  "envelope_version": <integer>,
  "operator_kind": "handshake_initiate",
  "substrate_id_proof": <claim about target substrate-ID>,
  "operator_signing_key_public": <freshly-generated public key>,
  "operator_attestation_request": <requesting operator-token>,
  "continuity_claim": <"fresh" | "owner_attested_continuity">,
  "submitted_at": <wall-clock; per L0 §13.1>
}
```

Substrate cross-checks `submitted_at`; skew > L1-tunable (default ±300s vs anchor trusted-timestamp) → `time_source_drift`; may reject. **Operator pubkey-pinning at bootstrap**: owner provides `(substrate-ID, anchor-endpoint-pubkey, owner-pubkey)` out-of-band at first install; operator pins; NEVER trusts owner-pubkey from substrate handshake. **Substrate-ID discovery**: operator obtains target ID at bootstrap. Mismatch → `substrate_id_mismatch` + rejection.

### §4.2 Substrate response — bidirectional validation

1. Validate `substrate_id_proof` against identity record.
2. **Non-deterministic operator_token** via OS-mediated sealed-key derivation: `operator_token = sealed_derive(handshake_nonce, current_cycle, kernel_random)`; kernel-mediated into {TPM, OS keyring, HSM, hardware-secure-element}. Substrate_secret never in process address space plaintext; plaintext-on-disk is CRITICAL (`substrate_secret_unsealed`). Sealing attestation owner-attested at genesis. Protects against adversarial agent; NOT adversarial Cultivator (L2_TRUST_MODEL).
3. Substrate emits `handshake_complete`:
   ```
   {
     "operator_token": <token>,
     "substrate_id": <substrate-ID>,
     "owner_birth_attestation_signature": <from identity record>,
     "owner_public_key_active_at_handshake": <from owner_key_history>,
     "anchor_surface_endpoint_public_key": <from identity record>,
     "handshake_timestamp": <substrate cycle>
   }
   ```
   Operator independently fetches canonical owner pubkey from anchor (using pinned anchor key); verifies `owner_birth_attestation_signature`; mismatch → rejects substrate as compromised.
4. Record handshake as sporocarp.

### §4.3 Continuity-challenge

`continuity_claim: "owner_attested_continuity"` → envelope includes owner-signed `continuity_attestation`; verified → quarantine shortened to L1-tunable min (default 10 cycles). Otherwise (`fresh`/unverifiable): post-handshake quarantine window (default 100 cycles); all CI requires fresh attestation.

### §4.4 Single-operator enforcement + race handling

Per I8: skin admits at most one operator-token. Second handshake during active → `skin_busy` + `concurrent_connect_attempt`. First when prior disconnected → standard. **Race**: same-cycle A/B tiebreak by OS-accept-queue order (strict FIFO at socket; single-threaded skin enforcer). Nonce-content tiebreak forbidden (nonce-grinding exploitable).

### §4.5 Disconnect detection

Explicit `handshake_terminate` (MAY include `request_dormancy: paused | throttled`); idle timeout (default 100 cycles); transport failure (RST, socket closure). Disconnect → alive → dormant per L1_CONTINUITY §2.



## §5. Network-egress enforcement (I6; P13-folded second hook)

Substrate operates within network-egress enforcement boundary permitting exactly §1 declared output endpoints. Unauthorized egress = breach.

> Dual-hook: unauthorized egress is simultaneously I6 universal-inclusion breach AND P9+I8 spatial-locus breach. Same event fires `appetite_locality_breach` (§5); may co-fire `P9_spatial_locus_breach` (§6) if destination is undeclared host/port. Two detectors on different evidence (egress packets vs binding-table snapshots) — cross-validation.

L4-platform: {kernel-level (network namespace), container-level (iptables/nftables), syscall-level (eBPF/ptrace), userspace proxy}.

**Prevents**: appetite rules secretly calling out; embedding service calls outside declared endpoint; covert exfiltration. **Does NOT prevent**: agent-maintainer source modification (CI); host-level adversarial action (owner monitoring); covert channels in legitimate federation envelopes. **Reciprocal**: operator-runtime enforcement is owner-side — owner attests non-leaky runtime; substrate cannot enforce against agent runtime.



## §6. Spatial-locus enforcement (P13 folding into P9 + I8 per L0 G-9.b)

Substrate periodically lists own spatial locus, compares against declared allowed-set. Deviation → `P9_spatial_locus_breach` immune; CRITICAL → §9 quarantine. Three surfaces (L1-default allowed-set; substrate-type override L4 §6.5): (1) state_dir contents; (2) process FD set; (3) network bindings.

### §6.2-§6.4 Default allowed-sets

- **state_dir**: `{"dag.cb", "snapshot.cb", "substrate_signing_key.cb", "*.tmp", "*.tmp.<pid>", ".gitignore"}`. Literal filename or glob (`*` / `*.<suffix>` only; no regex).
- **OS-noise**: `{".DS_Store", "Thumbs.db", "desktop.ini", "*.lock", ".tmp/*", ".lockfile"}` → `spatial_locus_noise_observed` (Daily). Avoids alarm fatigue.
- **FD**: state_dir files; skin intake/output sockets; sealed-key handles; stdin/stdout/stderr. Other → `P9_spatial_locus_breach:fd_unexpected:{fd_kind}`.
- **Network binding**: §1 listening; outbound `(peer_host, peer_port)` matches §1 output OR anchor OR federation peer in signed list. Outside → `P9_spatial_locus_breach:network_unexpected:{peer}`. Complements §5 (packet vs binding layer).

### §6.5 Detection cadence + substrate-type allowed-set

Default once per cycle; L1-tunable every N (min 10, default 1). Substrate-type-specific (baseline-Cultivar §6.2/§6.4; research-Cultivar may add `embeddings.cb` / `index.bin`; federation-mesh may add peer sockets / gossip port). Extensions CI (paired with §1). Silent extension = breach.

### §6.6 Birth-period exemption + cold-resume reconciliation

Birth-period (L1_CONTINUITY §3.2): transient unknown files → `spatial_locus_birth_period_pending` (Daily) instead of breach; owner's quarantine-clearance enumerates which become canonical. Cold-resume (L1_CONTINUITY §3.1): spatial-locus is pre-handshake witness — file-list + fd-list + binding-list as cryptographic-proof tuples (canonical-bytes of sorted lists, hashed), not verdicts.

### §6.7 Excluded

Inside-file content drift (§6 integrity wrapper); CPU/memory/disk budgets (L2_OBSERVABILITY #7/#8/#9); agent-side source tampering (L0 §14).



## §7. Skin-restart discipline (P9.b)

### §7.1 Process supervision (L4)

External supervisor restarts on crash/OOM-kill/operator-requested cycle. L4: Linux (systemd/runit/s6/supervisord); macOS (launchd); Windows (sc.exe/NSSM); Containerized (orchestrator restart-policy). L1 commits shape — external supervisor; substrate does NOT self-restart.

### §7.2 Ordered shutdown

SIGTERM / service-stop: (1) stop accepting envelopes (close `listen()`); (2) drain in-flight up to L1-tunable (default 30s); in-transit receive `skin_draining` + dead-letter; (3) flush WAL + persist DAG; ensure snapshot.cb current; fsync; (4) close output endpoints — peers receive `skin_restart_pending`; (5) emit `skin_restart_started` (Daily) with cycle, reason, drain duration, dead-letter count, snapshot hash; (6) exit 0. Hard-kill bypasses → L1_CONTINUITY §4 WAL replay.

### §7.3 Recovery on restart

In order: cold-resume pre-handshake checks (L1_CONTINUITY §3.1 — I1/I3/I4/I5/I8); spatial-locus enumeration (§6); WAL crash-recovery (L1_CONTINUITY §4); re-open intake endpoints; `dormant → alive`; await handshake; emit `skin_restart_completed` (pre/post cycle must equal — restart not metabolic event), with WAL outcome, dead-letter count, spatial-locus outcome.

### §7.4 Anti-flap rate limit

≥ L1-tunable (default 5) `skin_restart_completed` within L1-tunable window (default 1 hr) → `skin_restart_flap` (CRITICAL); refuses re-open until owner `flap_clearance`. Prevents adversarial agent / buggy supervisor from inducing restart loops masking other failures.

### §7.5 Skin-restart observability events

| Event | Grade | When | Witnesses |
|---|---|---|---|
| `skin_restart_started` | Daily | After shutdown signal, before exit | drain stats, snapshot hash, reason |
| `skin_restart_completed` | Daily | After restart, before re-open | pre/post cycle, WAL outcome, spatial-locus outcome |
| `skin_restart_flap` | CRITICAL | §7.4 exceeded | restart timestamps, window, threshold |
| `skin_restart_dead_letter` | Elevated | Per dead-lettered envelope | envelope digest, reason |

Surface in L2_OBSERVABILITY drill baseline.

### §7.6 Excluded

Owner-initiated graceful destruction (L1_GOVERNANCE §4 mortality — terminal); P7 self-euthanasia (supervisor MUST not restart — host-level adversarial action).



## §8. Backup encryption (per L0 §11.1)

### §8.1 Threat model

state_dir backups (periodic snapshot.cb copies, off-host DR archives) NOT internally access-controlled — anyone with read sees full state. Two attackers: **reader** (colocation operator, cloud provider, ex-employee with old tape); **tamperer** (inject altered state on restore-path). §8 addresses reader; tamperer handled by L1_SCHEMA §6.

### §8.2 Cultivator-controlled symmetric encryption key

- **Generation**: Cultivator generates locally at genesis or first-backup-attestation (AES-256-GCM or XChaCha20-Poly1305); substrate NEVER mints.
- **Holding**: Cultivator-held; substrate stores only public-derivation pointer (key-ID) in SSoT; key never in state_dir.
- **Access**: operator-runtime fetches key from Cultivator-controlled storage (hardware token, password manager, OS keyring, HSM) and encrypts; substrate provides plaintext canonical-bytes; operator runtime applies encryption transit-side.

Separates custody from substrate process; adversarial agent cannot exfiltrate.

### §8.3 Key escrow

Cultivator MAY declare at anchor:

```
key_escrow = (
  escrow_method,        # M-of-N Shamir / time-locked hardware token /
                        # attorney-held envelope / successor-Cultivator-co-signed
  escrow_parameters,
  escrow_attestation    # anchor-signed by Cultivator
)
```

No escrow → key-loss recovery impossible; sealed black box. Acceptable. DRAFT 9 mandates only that the choice be explicit and anchor-documented. If successor declared, escrow SHOULD include successor as one M-of-N party.

### §8.4 Key rotation aligned with owner key rotation

Backup-key rotation distinct from owner-key but SHOULD coordinate: when Cultivator rotates owner anchor-key (default 30-day cooldown), SHOULD ALSO rotate backup-key. New backup-key applies post-rotation; older remain decryptable with prior. SSoT `backup_key_id_history` tracks `(key_id, valid_from_anchor_timestamp, valid_until_anchor_timestamp, rotation_attestation_signed_by_owner)` (active-prefix + archived-tail).

### §8.5 Backup access controls

- Restrictive permissions (`umask 077`; Unix `0600`). Loose → `backup_permissions_loose` (Elevated).
- Destination declared in SSoT. Undeclared writes → `output_endpoint_breach`.
- **Backup integrity**: every backup carries snapshot.cb canonical-bytes hash signed by substrate key; Cultivator verifies on restore. Tampered/truncated → `backup_integrity_failure`.

### §8.6 Absent-encryption acknowledgment

L0 §11.1 does NOT mandate encryption but DOES mandate L1 access controls + absent encryption acknowledged as privacy attack surface. Without encryption: SSoT carries `backup_encryption_status = "cultivator_declined_explicit"` with Cultivator-signed declination. Silent omission → `"unspecified"` → `backup_encryption_undeclared` (Daily) on each backup-emit.

### §8.7 Excluded

In-process memory encryption (kernel-level adversary defeats §8); backup-transit encryption (transit-layer TLS/SSH L4); post-quantum readiness (L4 future).



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
| Spatial-locus breach (state_dir file) | §6.1 + §6.2 | `P9_spatial_locus_breach:file_unexpected:{path}` | CRITICAL |
| Spatial-locus breach (process FD) | §6.1 + §6.4 | `P9_spatial_locus_breach:fd_unexpected:{fd_kind}` | CRITICAL |
| Spatial-locus breach (network binding) | §6.1 + §6.4 | `P9_spatial_locus_breach:network_unexpected:{peer}` | CRITICAL |
| Spatial-locus OS-noise observed | §6.3 | `spatial_locus_noise_observed` | Daily |
| Spatial-locus birth-period pending | §6.6 | `spatial_locus_birth_period_pending` | Daily |
| Skin-restart flap (rate-limit exceeded) | §7.4 | `skin_restart_flap` | CRITICAL |
| Skin-restart dead-letter on shutdown | §7.5 | `skin_restart_dead_letter` | Elevated |
| Backup permissions loose | §8.5 | `backup_permissions_loose` | Elevated |
| Backup encryption undeclared | §8.6 | `backup_encryption_undeclared` | Daily |
| Backup integrity failure on restore | §8.5 | `backup_integrity_failure` | CRITICAL |

Cross-layer immune signals (`salience_collapse`, `telos_drift`, `compression_invariant_corruption`, `compression_unattested`, `budget_exhausted:{axis}`, `generation_depth_exceeded`, `consensus_floor_bypass`, `bet_retired`) surface in respective detector docs.

CRITICAL breaches → immediate skin-level quarantine per L1_CONTINUITY §5.

---

## §10. Glossary

L0 §1.2 owns Cultivator / Cultivar / Cultivation / Owner / Anchor surface. Document-private:

- **Spatial locus** — substrate's physical body: `state_dir + process + skin endpoints` (§6).
- **Skin endpoints** — declared `(intake, output, anchor-surface, federation, backup-output)` from §1 + §8.5.
- **Single integument** — P9. One declared skin surface; no integument-level redundancy; process-level restartability (P9.b).
