# L1 — Skin (envelope, handshake, single-operator, breach detection, spatial-locus, backup, restart)

> **Status**: DRAFT 3 (2026-05-17). L1 doc for boundary surface mechanism (I8).
> **Layer**: L1. Governed by L0 DRAFT 9 SEALED (commit `e796451`). Cultivation vocabulary at L0 §1.2.
> **Scope**: envelope; intake/output; operator handshake; single-operator; non-deterministic operator-token; network-egress; spatial-locus (P13 folded into P9+I8 per G-9.b); backup encryption (L0 §11.1); skin-restart discipline (P9.b); breach detection. Excludes: classifier/attestation crypto (L1_GOVERNANCE), SSoT (L1_SCHEMA), cycle cadence/cold-resume (L1_CONTINUITY).

---

## §1. Skin surface declaration

Substrate has exactly one declared skin surface in SSoT (tier-1 field): **intake endpoints** (Unix socket, named pipe, TCP port); **output endpoints** (federation peers, anchor-surface endpoint, optional summary export); **forbidden surfaces** ("everything else is breach"). CI-level; substrate cannot silently add an endpoint.



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

Substrate validates **only the envelope** (L0 I8 + P2):

- All required fields present.
- `sender_token` matches currently-active operator-token (§4).
- `payload_shape` in recognized set.
- `size_bytes` ≤ L1-tunable max (default 100 MB).
- `envelope_digest` recomputes via HMAC (integrity-and-binding tag, not long-lived signature).
- `submitted_at_cycle` within freshness window (default 60 cycles), per L0 §13.1.

> Boundary (P2 vs P12 per G-9.b): skin admits-or-rejects = **P2**. Downstream selective attention = **P12** (L1_TROPISM). Confusing yields "salience collapse".

Failure → reject with `envelope_malformed` (no oracle disclosure of which field failed).

### §2.2 Causal-parent reference

`causal_parent_ref` non-null must refer to recent sporocarp visible in most-recent digest. Ancient/non-existent refs → `causal_chain_violation`.

## §3. Output gating

Outputs leave through declared output endpoints; signed by substrate's identity key.

**Canonical-bytes** (per L0 §9.3.1): outputs to anchor-surface carry **canonical bytes**, not substrate-rendered summaries. Client renders deterministically (L0 §9.3.2).

**Witnesses-not-verdicts** (per L0 §9.3.4): anchor-surface outputs emit cryptographic-proof tuples (sampled hashes, Merkle paths, parent hashes), never bare verdicts. Cultivator re-derives; substrate outputting verdict without witness asserts authority it does not have.

### §3.1 Federation egress freshness check

Every outbound federation envelope verifies target peer's freshness + non-revocation per L1_GOVERNANCE §5.2 **BEFORE emission**. Stale/revoked → suppressed; `federation_egress_blocked` fruits. Substrate caches peer-list; **anchor-surface negative-revocation proof** required for emission.

Federation event content uses sorted-key, normalized-whitespace, fixed-precision-numeric serialization to limit covert-channel bandwidth (per L1_GOVERNANCE §5.3).

### §3.2 Forbidden output

Anything outside declared endpoints is breach.



## §4. Operator handshake protocol (bidirectional)

### §4.1 Handshake initiation + operator key bootstrap

**Operator carries per-handshake signing keypair**: operator runtime generates fresh keypair at initiation. Private key in operator-runtime memory only (never disk; never transmitted); public key in handshake_initiate. Forge-resistant signing surface for operator_witness fields.

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

Substrate cross-checks `submitted_at`; skew > L1-tunable (default ±300s against anchor-surface trusted-timestamp) → `time_source_drift`; may reject. Agent wall-clock never authoritative.

**Operator pubkey-pinning at bootstrap**: at first installation, owner provides `(substrate-ID, anchor-surface-endpoint-public-key, owner-public-key)` via out-of-band channel. Operator pins. NEVER trusts owner-pubkey emitted by substrate handshake response.

**Substrate-ID discovery**: operator obtains target ID at bootstrap from owner. Mismatch with pinned → `substrate_id_mismatch` + rejection.

### §4.2 Substrate response — bidirectional validation

1. Validate `substrate_id_proof` against own identity record.
2. Generate **non-deterministic operator_token** via OS-mediated sealed-key derivation: `operator_token = sealed_derive(handshake_nonce, current_cycle, kernel_random)`. `sealed_derive` is kernel-mediated into {TPM-sealed key, OS keyring, HSM, hardware-secure-element}. Substrate_secret never in process address space in plaintext. Mechanism L4-platform-pick; plaintext-on-disk is CRITICAL breach (`substrate_secret_unsealed`). Sealing attestation owner-attested at genesis (L1_GOVERNANCE §4.1 step 2). OS-sealing protects against adversarial agent; NOT against adversarial Cultivator (L0 §14 + L2_TRUST_MODEL).
3. **Substrate emits attestation** in `handshake_complete`:
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
   Operator **independently fetches canonical owner public key from anchor surface** (using bootstrap-pinned anchor key) — freshness check preventing substrate lying about active owner key. Verifies `owner_birth_attestation_signature` against anchor-fetched pubkey; mismatch → rejects substrate as compromised; does NOT transmit deltas.
4. Record handshake as sporocarp.

### §4.3 Continuity-challenge

`continuity_claim: "owner_attested_continuity"`: envelope includes owner-signed `continuity_attestation` (anchor-surface-produced) naming this reconnection. Verified → quarantine window shortened to L1-tunable minimum (default 10 cycles).

Otherwise (`fresh` or unverifiable): **post-handshake quarantine window** (L1-tunable, default 100 cycles); all CI-level operations require fresh owner attestation.

### §4.4 Single-operator enforcement + race handling

Per L0 I8: skin admits at most one operator-token at a time.

- Second handshake during active connection → `skin_busy` + `concurrent_connect_attempt`.
- First handshake when prior disconnected → standard; dormant → alive.
- **Race**: same-cycle from A and B tiebreak by **OS-accept-queue order** (strict FIFO at socket layer; single-threaded skin enforcer). Nonce-content tiebreak forbidden (exploitable via nonce-grinding).

### §4.5 Disconnect detection

- Explicit: `handshake_terminate`. MAY include `request_dormancy: paused | throttled`.
- Timeout: no envelope within idle window (default 100 cycles).
- Transport failure: TCP RST, socket closure.

Disconnect → alive → dormant per L1_CONTINUITY §2.



## §5. Network-egress enforcement (I6 expanded; second hook to P13-folded-into-P9+I8)

Substrate operates within **network-egress enforcement boundary** permitting exactly §1 declared output endpoints. Unauthorized egress = breach.

> Dual-hook: unauthorized egress is **simultaneously** I6 universal-inclusion breach AND P9+I8 spatial-locus breach. Same event fires `appetite_locality_breach` (§5); may co-fire `P9_spatial_locus_breach` (§6) if destination is undeclared host/port. Two detectors on different evidence (egress packets vs binding-table snapshots) — cross-validation.

L4-platform-specific within {kernel-level (network namespace), container-level (iptables/nftables), syscall-level (eBPF/ptrace), userspace proxy}.

**Prevents**: appetite update-rules secretly calling out; embedding service calls outside declared endpoint; covert exfiltration.

**Does NOT prevent**: agent-maintainer source modification (CI per L1_GOVERNANCE §1.2); host-level adversarial action (owner monitoring per L0 §6); covert channels within legitimate federation envelopes (L1_GOVERNANCE §5.3).

**Reciprocal**: operator-runtime enforcement on agent side is **owner-side, not substrate-side** — owner attests non-leaky operator runtime; substrate cannot enforce against agent runtime.



## §6. Spatial-locus enforcement (P13 folding into P9 + I8 per L0 G-9.b)

Substrate **periodically lists** own spatial locus, compares against declared **allowed-set**. Deviation emits `P9_spatial_locus_breach` (immune); CRITICAL → §9 quarantine path.

**Three surfaces** (each with L1-default allowed-set; substrate-type overrides L4 per §6.5):

1. **state_dir contents allowlist** — files/subdirectories under declared state_dir.
2. **Process FD set** — every open FD held by substrate process.
3. **Network bindings allowlist** — listening sockets + active outbound connections.

### §6.2 Default state_dir allowed-set (per M25.0)

`{"dag.cb", "snapshot.cb" (M25.0 integrity-wrapped), "substrate_signing_key.cb" (sealed per §4.2), "*.tmp", "*.tmp.<pid>", ".gitignore" (optional)}`. Declarative — literal filename or glob (`*` and `*.<suffix>` only; no regex).

### §6.3 OS-noise allowlist

`{".DS_Store", "Thumbs.db", "desktop.ini", "*.lock", ".tmp/*", ".lockfile"}` → `spatial_locus_noise_observed` (Daily) — avoids alarm fatigue without licensing substrate to ignore unknown files.

### §6.4 FD + network-binding allowed-sets

**FD**: state_dir files when open; skin intake/output sockets (§1, anchor-surface client, federation peers); sealed-key handles (§4.2); stdin/stdout/stderr for operator-supervisor IPC. Other → `P9_spatial_locus_breach:fd_unexpected:{fd_kind}`.

**Network binding**: listening sockets in §1 intake; outbound sockets whose `(peer_host, peer_port)` matches §1 output endpoint OR anchor-surface endpoint OR federation peer in signed peer-list. Outside → `P9_spatial_locus_breach:network_unexpected:{peer}`.

Complements §5 (packet layer vs binding-table layer).

### §6.5 Detection cadence + substrate-type allowed-set

Default once per metabolic cycle; L1-tunable every N (min 10, default 1). Cheap (body ≤ tens of files/FDs/sockets).

Substrate-type-specific (baseline-Cultivar §6.2/§6.4; research-Cultivar may add `embeddings.cb`, `index.bin`; federation-mesh-Cultivar may add peer sockets, gossip port). Extensions **CI-level** (paired with §1 declaration). Silent extension = breach.

### §6.6 Birth-period exemption + cold-resume reconciliation

Birth-period quarantine (L1_CONTINUITY §3.2): files matching neither set may transiently appear; emit `spatial_locus_birth_period_pending` (Daily) instead of breach. Owner's quarantine-clearance enumerates which pending entries become canonical.

Cold-resume (L1_CONTINUITY §3.1): spatial-locus check is pre-handshake witness: file-list + fd-list + binding-list as cryptographic-proof tuples (canonical-bytes of sorted lists, hashed), not bare verdicts.

### §6.7 Excluded

Inside-file content drift (M25.0 snapshot.cb integrity + L1_CONTINUITY §3.1); CPU/memory/disk-byte budgets (P11 #7/#8/#9 at L2_OBSERVABILITY); agent-side source tampering (L0 §14; anchor-attested at genesis + key rotation).



## §7. Skin-restart discipline (P9.b)

### §7.1 Process supervision (L4-platform-pick)

Substrate runs under **external supervisor** restarting on crash/OOM-kill/operator-requested cycle. L4 options: Linux (`systemd`/`runit`/`s6`/`supervisord`); macOS (`launchd`); Windows (Service via `sc.exe` or NSSM); Containerized (orchestrator restart-policy). L1 commits shape (external supervisor; substrate does NOT self-restart).

### §7.2 Ordered shutdown protocol

On SIGTERM / service-stop:

1. **Stop accepting new envelopes** (close `listen()`; sockets drain).
2. **Drain in-flight** up to L1-tunable drain-deadline (default 30s). In-transit receive `skin_draining` + dead-letter for re-emission.
3. **Flush WAL + persist DAG** to `dag.cb`; ensure snapshot.cb current; fsync.
4. **Close output endpoints** — anchor + federation peers receive `skin_restart_pending`.
5. **Emit `skin_restart_started`** (Daily): cycle, reason, drain duration, dead-letter count, snapshot hash.
6. **Exit** status 0.

Hard-kill bypasses → L1_CONTINUITY §4 WAL replay.

### §7.3 Recovery on restart

In order: (1) cold-resume pre-handshake checks per L1_CONTINUITY §3.1 (I1, I3, I4, I5, I8); (2) spatial-locus enumeration per §6; (3) WAL crash-recovery per L1_CONTINUITY §4; (4) re-open intake endpoints (§1); (5) `dormant → alive`; await handshake; (6) emit `skin_restart_completed` (pre/post cycle must equal — restart not metabolic event), WAL outcome, dead-letter count, spatial-locus outcome.

### §7.4 Anti-flap rate limit

≥ L1-tunable (default 5) `skin_restart_completed` within L1-tunable window (default 1 hr, anchor trusted-timestamp) → `skin_restart_flap` (CRITICAL); refuses re-opening intake until owner-attested `flap_clearance`. Prevents adversarial agent (or buggy supervisor) inducing restart loops masking other failures.

### §7.5 Skin-restart observability events

| Event | Grade | When | Witnesses |
|---|---|---|---|
| `skin_restart_started` | Daily | After shutdown signal, before exit | drain stats, snapshot hash, reason |
| `skin_restart_completed` | Daily | After restart, before re-open | pre/post cycle, WAL outcome, spatial-locus outcome |
| `skin_restart_flap` | CRITICAL | §7.4 threshold exceeded | restart timestamps, window, threshold |
| `skin_restart_dead_letter` | Elevated | Per envelope dead-lettered on shutdown | envelope digest, dead-letter reason |

Surface in L2_OBSERVABILITY drill baseline.

### §7.6 Excluded

Owner-initiated graceful destruction (L1_GOVERNANCE §4 mortality — terminal); P7 self-euthanasia (`self_euthanasia_executed`; supervisor MUST not restart — host-level adversarial action per §5).



## §8. Backup encryption (per L0 §11.1)

### §8.1 Threat model

state_dir backups (periodic snapshot.cb copies, off-host DR archives) NOT internally access-controlled. Anyone with read access reads full state — DAG, owner key archive, sealed-key-derivation parameters, all sporocarps. **G16 backup-attack surface** (Phase γ.3). Two attackers: **reader** (colocation operator, cloud-storage provider, ex-employee with old tape); **tamperer** (inject altered state on restore-path). §8 addresses **reader**; **tamperer** handled by M25.0 snapshot.cb integrity.

### §8.2 Cultivator-controlled symmetric encryption key

- **Generation**: Cultivator generates locally at genesis or first-backup-attestation (AES-256-GCM or XChaCha20-Poly1305). Substrate NEVER mints.
- **Holding**: Cultivator's responsibility. Substrate stores only **public-derivation pointer** (key-ID) in SSoT; key never persists in state_dir.
- **Access path**: operator-runtime-mediated. Operator runtime fetches key from Cultivator-controlled storage (hardware token, password manager, OS keyring, HSM) and encrypts. Substrate provides plaintext canonical-bytes; operator runtime applies encryption transit-side.

Separates custody (Cultivator + operator) from substrate process. Adversarial agent cannot exfiltrate from substrate.

### §8.3 Key escrow

Cultivator MAY declare at anchor surface:

```
key_escrow = (
  escrow_method,        # M-of-N Shamir / time-locked hardware token /
                        # attorney-held envelope / successor-Cultivator-co-signed
  escrow_parameters,
  escrow_attestation    # anchor-surface-signed by Cultivator
)
```

No escrow → recovery on key-loss impossible; sealed black box. Acceptable (some Cultivators value confidentiality above recoverability). DRAFT 9 mandates only the choice is **explicit and documented at anchor surface**. Successor coordination (L0 §1.4 + L1_GOVERNANCE §3.2): if successor declared, escrow SHOULD include successor as one M-of-N party.

### §8.4 Key rotation aligned with owner key rotation

Backup-key rotation logically distinct from owner-key but SHOULD coordinate:

- When Cultivator rotates owner anchor-key per L1_GOVERNANCE §3.1 (default 30-day cooldown), SHOULD ALSO rotate backup-key.
- New backup-key applies to all backups after rotation; older remain decryptable with prior key (Cultivator archives).
- SSoT `backup_key_id_history` tracks `(key_id, valid_from_anchor_timestamp, valid_until_anchor_timestamp, rotation_attestation_signed_by_owner)`, active-prefix + archived-tail per L1_GOVERNANCE §3.1.
- Recommended: same 30-day cooldown for unified cadence.

### §8.5 Backup access controls

- **Restrictive permissions** (`umask 077`; Unix `0600`). Loose → `backup_permissions_loose` (Elevated).
- **Destination declared in SSoT** as backup-output endpoint. Undeclared writes → `output_endpoint_breach`.
- **Backup integrity** (separate from confidentiality): every backup carries snapshot.cb canonical-bytes hash signed by substrate signing key; Cultivator verifies on restore. Tampered/truncated → `backup_integrity_failure`.

### §8.6 Absent-encryption acknowledgment

Per L0 §11.1: DRAFT 9 does NOT mandate backup encryption at L0 but DOES mandate L1 access controls + absent encryption acknowledged as privacy attack surface.

Without encryption (air-gapped host, filesystem-level encryption deemed sufficient), SSoT carries `backup_encryption_status = "cultivator_declined_explicit"` with Cultivator-signed declination. Silent omission → `"unspecified"` → emits `backup_encryption_undeclared` (Daily) on each backup-emit until resolved.

### §8.7 Excluded

In-process memory encryption (kernel-level adversary defeats §8 — L0 §14); backup-transit encryption (off-host transit is at-rest-encrypted form; transit-layer TLS/SSH L4-operational); quantum-cryptography readiness (post-quantum L4 future per L0 §10).



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

Cross-layer immune signals not detected here (`salience_collapse`, `telos_drift` → L1_TROPISM; `compression_invariant_corruption`, `compression_unattested` → L1_SCHEMA; `budget_exhausted:{axis}` → L1_CONTINUITY + L2_OBSERVABILITY #7/#8/#9; `generation_depth_exceeded` → L1_GOVERNANCE §4.3; `consensus_floor_bypass` → L2_FEDERATION; `bet_retired` → L2_OBSERVABILITY §7.5) surface in respective detector docs.

CRITICAL breaches → immediate skin-level quarantine per L1_CONTINUITY §5.

---

## §10. Glossary (Cultivation per L0 §1.2 G-11.a)

L0 §1.2 owns Cultivator / Cultivar / Cultivation / Owner / Anchor surface. Document-private:

- **Spatial locus** — substrate's physical body: `state_dir + process + skin endpoints`. Operational target of P13 (folded into P9+I8 per G-9.b). §6.
- **Skin endpoints** — declared `(intake, output, anchor-surface, federation, backup-output)` from §1 + §8.5.
- **Single integument** — P9. Single declared skin surface; no redundancy at integument level; restartability at process level (P9.b).
