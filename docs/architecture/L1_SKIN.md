# L1 — Skin (envelope, handshake, single-operator, breach detection, spatial-locus, backup, restart)

> **Status**: DRAFT 3 (2026-05-17). Authoritative L1 doc for boundary surface mechanism (I8).
> **Layer**: L1. Governed by L0 DRAFT 9 SEALED (commit `e796451`).
> **Scope**: envelope schema; intake/output endpoints; operator handshake (bidirectional); single-operator enforcement; non-deterministic operator-token; network-egress enforcement; **spatial-locus enforcement (P13 folded into P9+I8 per G-9.b)**; **backup encryption (per L0 §11.1)**; **skin-restart discipline (per L0 P9.b)**; breach detection. Does NOT cover: classifier / attestation crypto (→ L1_GOVERNANCE), SSoT (→ L1_SCHEMA), cycle cadence / cold-resume (→ L1_CONTINUITY). Principle names follow L0 DRAFT 9 SEALED (P1/P2/P3/P5/P9/P9.b/P12/P14 — projection mapping at L0 §4); Cultivation vocabulary defined in §10.

---

## §1. Skin surface declaration

The substrate has exactly one declared skin surface in SSoT (tier-1 field). Lists:

- **Intake endpoints** — where deltas enter (e.g., Unix socket, named pipe, TCP port).
- **Output endpoints** — where outputs exit (federation peers, anchor-surface endpoint, optional summary export).
- **Forbidden surfaces** — explicit "everything else is breach" boundary.

Skin declaration is contract-identity-level. Substrate cannot silently add an endpoint.

---

## §2. Envelope schema

Every delta arriving at an intake endpoint is wrapped:

```
{
  "envelope_version": <integer>,
  "sender_token": <operator-token from handshake>,
  "payload_shape": <one of: "text" | "file_ref" | "structured_yaml" | "binary_ref" | ...>,
  "causal_parent_ref": <prior sporocarp ID or null at first delta after handshake>,
  "size_bytes": <delta size>,
  "content_type_hint": <MIME-style or null>,
  "submitted_at_cycle": <substrate metabolic-cycle counter>,
  "envelope_digest": <HMAC(operator_token, canonical_envelope_fields || payload)>,
  "payload": <delta content>
}
```

### §2.1 Envelope integrity check

The substrate validates **only the envelope**, not payload content (L0 I8 + P2 envelope-gated):

- All required fields present.
- `sender_token` matches the currently-active operator-token (single-operator, §4).
- `payload_shape` in the recognized set.
- `size_bytes` ≤ L1-tunable max (default 100 MB).
- `envelope_digest` recomputes via HMAC keyed by operator_token. (HMAC keyed by operator_token gives in-flight tamper detection AND operator authentication via the token without requiring a persistent operator key — `envelope_digest` is an integrity-and-binding tag, not a long-lived signature.)
- `submitted_at_cycle` is within freshness window (default 60 cycles). The freshness check uses the **substrate's metabolic-cycle counter** as the authoritative source per L0 §13.1 time-source authority hierarchy (anchor-surface trusted-timestamp > local wall-clock > cycle counter — for skin envelopes the cycle counter is the relevant authority because envelopes target the substrate's process clock).

> Boundary note (P2 vs P12, per L0 G-9.b retraction): the skin admits-or-rejects envelopes — this is **P2 (Eternal Ingestion, Envelope-Gated)**. Downstream selective attention to which admitted material gets metabolized into sporocarps is **P12 (Differential Response)** and lives in `L1_TROPISM`, not here. Confusing the two yields the "salience collapse" failure mode.

Failure → reject with `envelope_malformed` (no oracle disclosure of which field failed).

### §2.2 Causal-parent reference

`causal_parent_ref`, if non-null, must refer to a recent sporocarp visible in the most-recent digest the agent could have read. Ancient/non-existent refs emit `causal_chain_violation`.

---

## §3. Output gating

Outputs leave through declared output endpoints. Output envelopes are signed by the substrate (substrate's signing key from the identity record).

**Canonical-bytes discipline** (per L0 §9.3.1 canonical-bytes sub-mechanism): outputs to the anchor-surface endpoint carry **canonical bytes**, not substrate-rendered summaries. Anchor-surface client renders deterministically for owner review per L0 §9.3.2.

**Witnesses-not-verdicts discipline** (per L0 §9.3.4): substrate outputs to the anchor surface emit cryptographic-proof tuples (sampled hashes, Merkle paths, parent hashes) — never bare boolean verdicts about its own integrity. The Cultivator (owner) re-derives the verdict from the witness; a substrate that outputs a verdict without the witness is asserting authority it does not have.

### §3.1 Federation egress freshness check

Every outbound federation envelope verifies its target peer's freshness + non-revocation per L1_GOVERNANCE §5.2 **BEFORE emission**. Stale or revoked target → emission suppressed; `federation_egress_blocked` immune event fruits. Substrate canon caches a peer-list mirror but the **anchor-surface negative-revocation proof** is required for emission, not the cache.

**Egress rate-limiting + canonical low-entropy serialization** (per L1_GOVERNANCE §5.3): federation event content uses sorted-key, normalized-whitespace, fixed-precision-numeric serialization to limit covert-channel bandwidth.

### §3.2 Forbidden output

Anything outside declared endpoints is skin breach.

---

## §4. Operator handshake protocol (bidirectional)

### §4.1 Handshake initiation + operator key bootstrap

**Operator carries a per-handshake signing keypair**: the operator's runtime generates a fresh keypair (`operator_signing_key_public`, `operator_signing_key_private`) at handshake initiation. Private key lives in operator-runtime memory only (never on disk; never transmitted to substrate); public key is published in the handshake_initiate envelope. This gives the operator a real signing surface distinct from the substrate-generated operator_token: operator_witness fields signed with operator_signing_key_private are forge-resistant by the substrate.

```
{
  "envelope_version": <integer>,
  "operator_kind": "handshake_initiate",
  "substrate_id_proof": <claim about target substrate-ID>,
  "operator_signing_key_public": <freshly-generated operator-side public key>,
  "operator_attestation_request": <field requesting operator-token>,
  "continuity_claim": <"fresh" | "owner_attested_continuity">,
  "submitted_at": <wall-clock; see L0 §13.1 time-source authority hierarchy>
}
```

> Time-source note (per L0 §13 time semantics): handshake `submitted_at` is operator-runtime wall-clock; substrate cross-checks against its own metabolic-cycle counter to detect clock skew. If skew exceeds L1-tunable threshold (default ±300 seconds against anchor-surface trusted-timestamp), substrate emits `time_source_drift` immune signal and may reject the handshake. The substrate **never** treats agent-provided wall-clock as authoritative — it is admissible advisory data only.

**Operator pubkey-pinning at agent-bootstrap**: at first operator-agent installation, the owner provides `(substrate-ID, anchor-surface-endpoint-public-key, owner-public-key)` to the operator runtime via an owner-controlled out-of-band channel. The operator pins these. The operator NEVER trusts an owner-pubkey emitted by the substrate's own handshake response — it only verifies the substrate's emitted signature against the anchor-surface-fetched (or bootstrap-pinned) owner pubkey.

**Substrate-ID discovery**: operator obtains the target substrate-ID at agent-bootstrap from the owner (per the bootstrap-pinning above). Substrate-ID in agent-readable canon is advisory; mismatch with the bootstrap-pinned substrate-ID → `substrate_id_mismatch` + handshake rejection.

### §4.2 Substrate response — bidirectional validation

The substrate:

1. Validates `substrate_id_proof` against its own identity record (the agent is targeting THIS substrate, not stale).
2. Generates a **non-deterministic operator_token** via an **OS-mediated sealed-key derivation** (substrate_secret cannot live in agent-readable substrate-process memory if P1.a self-hosting is honest about the agent maintaining substrate code):
   ```
   operator_token = sealed_derive(handshake_nonce, current_cycle, kernel_random)
   ```
   where `sealed_derive` is a kernel-mediated call into one of {TPM-sealed key, OS keyring, HSM, hardware-secure-element} — the substrate_secret never enters substrate process address space in plaintext; the substrate invokes the OS-level sealed-API and receives `operator_token` without ever holding the underlying secret. **Specific sealing mechanism is L4-platform-pick**; plaintext-on-disk substrate_secret is a CRITICAL skin breach (`substrate_secret_unsealed`). Sealing-mechanism attestation is owner-attested at genesis (per L1_GOVERNANCE §4.1 step 2 — added to the genesis parameter set).
   
   **Adversarial-owner caveat**: OS-sealing protects against an adversarial agent (the maintainer cannot exfiltrate substrate_secret from sealed storage); it does NOT protect against an adversarial Cultivator — see L0 §14 + L2_TRUST_MODEL.
3. **Substrate emits its own attestation to the agent** in `handshake_complete`:
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
   The operator **independently fetches the canonical owner public key from the anchor surface** (using the bootstrap-pinned `anchor-surface-endpoint-public-key` from §4.1) — this is the freshness check that prevents the substrate from lying about which owner key is active. The operator then verifies `owner_birth_attestation_signature` against the anchor-surface-fetched owner pubkey; if the substrate's `owner_public_key_active_at_handshake` differs from anchor-surface authoritative record, operator rejects substrate as compromised and does NOT transmit deltas.
4. Records handshake event as a sporocarp.

### §4.3 Continuity-challenge

If `continuity_claim: "owner_attested_continuity"`: handshake envelope must include an owner-signed `continuity_attestation` (anchor-surface-produced) naming this specific reconnection. Verified → quarantine window shortened to L1-tunable minimum (default 10 cycles).

Otherwise (`fresh` or unverifiable): substrate enters **post-handshake quarantine window** (L1-tunable, default 100 cycles) during which all CI-level operations require fresh owner attestation regardless of governance classification.

### §4.4 Single-operator enforcement + race handling

Per L0 I8: skin admits at most one operator-token at a time.

- Second handshake during active connection → `skin_busy` + `concurrent_connect_attempt` immune event.
- First handshake when prior operator disconnected → standard handshake; substrate transitions dormant → alive.
- **Race**: handshakes from A and B arrive in the same cycle. Tiebreak by **OS-accept-queue order** (strict FIFO at socket layer; single-threaded skin enforcer). Nonce-content tiebreak is forbidden (would be exploitable via nonce-grinding).

### §4.5 Disconnect detection

- Explicit: operator emits `handshake_terminate`. MAY include `request_dormancy: paused | throttled`, which substrate honors as a preference (subject to resource pressure override).
- Timeout: no envelope received within idle window (default 100 cycles).
- Transport failure: TCP RST, socket closure, etc.

Any disconnect → alive → dormant per L1_CONTINUITY §2.

---

## §5. Network-egress enforcement (operationalizes I6 expanded; second hook to P13-folded-into-P9+I8)

The substrate process operates within a **network-egress enforcement boundary** that permits exactly the §1 declared output endpoints. Unauthorized egress = breach.

> Dual-hook note: unauthorized egress is **simultaneously** an I6 universal-inclusion breach (the substrate accepted intake but is now extruding it outside declared output) AND a P9+I8 spatial-locus breach (the substrate's "body" of operations crossed an undeclared boundary). The same network event fires both `appetite_locality_breach` (this section) and may co-fire `P9_spatial_locus_breach` (§6) if the destination is to an undeclared host/port pair. The two detectors operate on different evidence (egress packets vs binding-table snapshots) and serve as cross-validation.

**Specific enforcement mechanism is L4-platform-specific** within {kernel-level (network namespace), container-level (iptables/nftables), syscall-level (eBPF/ptrace), userspace proxy}. L1 does not pre-pick a platform.

**What this prevents**: appetite update-rules that secretly call out (mycoparasite-8 trojan); embedding service calls outside the declared endpoint; covert exfiltration via arbitrary protocol.

**What this does NOT prevent**: agent-maintainer source modification (a CI-level mutation per L1_GOVERNANCE §1.2); host-level adversarial action (owner's monitoring responsibility, L0 §6); covert channels within legitimate federation envelopes (handled by L1_GOVERNANCE §5.3 rate-limiting + canonical low-entropy serialization).

**Reciprocal enforcement**: operator-runtime enforcement on the agent side (preventing agent from exfiltrating substrate-exposed state to third parties) is **owner-side, not substrate-side** — the owner attests non-leaky operator runtime; substrate cannot enforce against agent runtime.

---

## §6. Spatial-locus enforcement (P13 folding into P9 + I8 per L0 G-9.b)

The substrate **periodically lists** its own spatial locus and compares against a declared **allowed-set**. Deviation emits `P9_spatial_locus_breach` (immune-grade) and triggers the §9 quarantine path on CRITICAL grades.

### §6.1 Three spatial-locus surfaces

The substrate's body has three concrete surfaces, each with its own allowed-set:

1. **state_dir contents allowlist** — every file and subdirectory under the substrate's declared state_dir.
2. **Process file-descriptor set** — every open FD held by the substrate process (regular file, socket, pipe, eventfd, etc.).
3. **Network bindings allowlist** — every listening socket bound by the substrate (TCP/UDP listen) and every outbound connection currently open from the substrate process.

Each surface has an L1-declared default allowed-set; substrate-type-specific overrides are L4-tunable (per §6.5).

### §6.2 Default state_dir allowed-set (per current M25.0 state)

```
{
  "dag.cb",                          # canonical-bytes DAG persistence
  "snapshot.cb",                     # canonical-bytes snapshot (M25.0 integrity wraps this)
  "substrate_signing_key.cb",        # substrate identity signing key (sealed per §4.2)
  "*.tmp",                           # in-flight atomic-rename temporaries (any file matching glob)
  "*.tmp.<pid>",                     # in-flight atomic-rename with PID suffix
  ".gitignore"                       # optional, when state_dir is under a git workspace
}
```

The allowed-set is **declarative** — every entry is a literal filename or a glob pattern. Globs are restricted to `*` and `*.<suffix>` patterns (no full regex, to keep the allowlist auditable).

### §6.3 OS-noise allowlist (separate sub-set, lower severity)

OS / filesystem / build-system noise is enumerated separately so its presence does not trigger CRITICAL breaches:

```
{
  ".DS_Store",       # macOS Finder metadata
  "Thumbs.db",       # Windows thumbnail cache
  "desktop.ini",     # Windows folder config
  "*.lock",          # filesystem-level lock files
  ".tmp/*",          # subdirectory-scoped temporaries (some FS lifecycle libs)
  ".lockfile"
}
```

Files matching OS-noise allowlist fire `spatial_locus_noise_observed` (Daily grade, not Elevated). This avoids alarm fatigue on macOS/Windows hosts without giving the substrate license to ignore unknown files.

### §6.4 Default process-FD and network-binding allowed-sets

**FD allowed-set** (described positively; deviations fire breach):
- The state_dir files declared in §6.2 (when open for I/O).
- Skin intake sockets declared in §1.
- Skin output sockets declared in §1 (including anchor-surface client, federation peers).
- Sealed-key handles (the `sealed_derive` FD per §4.2; never a plaintext-secret file).
- Standard fd 0/1/2 (stdin/stdout/stderr) for operator-supervisor IPC where applicable.

Any FD not in the above set emits `P9_spatial_locus_breach:fd_unexpected:{fd_kind}`.

**Network binding allowed-set**:
- Every listening socket declared in §1 intake endpoints (host:port tuples or AF_UNIX paths).
- Every actively-connected outbound socket whose `(peer_host, peer_port)` matches a §1 output endpoint OR an anchor-surface endpoint OR a federation peer in the substrate's signed peer-list.

Any binding/connection outside this set emits `P9_spatial_locus_breach:network_unexpected:{peer}`. This complements §5's network-egress enforcement: §5 enforces at the **packet** layer (covert egress prevention); §6 enforces at the **binding-table** layer (steady-state body integrity).

### §6.5 Detection cadence + L1-tunable allowed-set per substrate type

Detection runs **once per metabolic cycle by default**; L1-tunable to every N cycles for resource-constrained substrates (minimum every 10 cycles, default 1 cycle). The check is **cheap** — the body is small (≤ tens of files, ≤ tens of FDs, ≤ small number of sockets) so a per-cycle full enumeration is affordable.

The allowed-set is **substrate-type-specific**:

- A baseline-Cultivar substrate uses the §6.2/§6.4 defaults.
- A research-Cultivar with vector-embedding cache may declare additional state_dir entries: `embeddings.cb`, `index.bin`.
- A federation-mesh-Cultivar may declare additional bindings: outbound federation peer sockets, gossip protocol port.

Allowed-set extensions are **CI-level**: each substrate's allowed-set is part of the SSoT contract-identity declaration (§1 declares the skin surface; the allowed-set is the spatial-locus declaration paired with it). Silent extension is breach.

### §6.6 Birth-period exemption + cold-resume reconciliation

During birth-period quarantine (per L1_CONTINUITY §3.2), the substrate may transiently observe files matching neither allowed-set nor noise-set; these emit `spatial_locus_birth_period_pending` (Daily) instead of `P9_spatial_locus_breach`. The owner's quarantine-clearance event explicitly enumerates which previously-pending entries are now part of the canonical allowed-set; subsequent enumerations apply the updated set.

On cold-resume (L1_CONTINUITY §3.1), the spatial-locus check is one of the pre-handshake check witnesses: substrate emits the file-list + fd-list + binding-list as cryptographic-proof tuples (canonical-bytes serialization of the sorted lists, hashed), not as bare boolean verdicts.

### §6.7 What §6 explicitly does NOT cover

Inside-file content drift (handled by M25.0 snapshot.cb integrity + DAG-tip self-consistency at L1_CONTINUITY §3.1); CPU/memory/disk-byte budgets (P11 metabolic-economy signals at L2_OBSERVABILITY #7/#8/#9); agent-side source-code tampering (self-hosting paradox per L0 §14; anchor-surface-attested at genesis + key rotation).

---

## §7. Skin-restart discipline (P9.b single-failure-point per L0)

### §7.1 Process supervision (L4-platform-pick)

The substrate runs under a **process supervisor**: an external init system that restarts the substrate process on crash, OOM-kill, or operator-requested cycle. L4 platform options:

- **Linux**: `systemd` unit (recommended for production hosts), `runit`, `s6`, `supervisord`.
- **macOS**: `launchd` LaunchAgent / LaunchDaemon.
- **Windows**: Windows Service via `sc.exe` or NSSM wrapper.
- **Containerized**: container orchestrator's restart-policy (Kubernetes Pod restart, Docker `--restart unless-stopped`).

L1 commits to the **shape** (external supervisor manages process lifecycle, substrate does NOT self-restart from within); L4 picks the platform.

### §7.2 Ordered shutdown protocol

On receiving shutdown signal (SIGTERM on Unix, service-stop on Windows), the substrate executes a strict ordered sequence:

1. **Stop accepting new envelopes** at intake endpoints (close `listen()` socket; existing connected sockets enter drain phase).
2. **Drain in-flight envelopes** — process all envelopes already past the envelope-integrity check up to the L1-tunable drain-deadline (default 30 seconds). Envelopes still in transit on connected sockets receive `skin_draining` response and are dead-lettered for re-emission on restart.
3. **Flush WAL + persist DAG** — write any pending DAG nodes to `dag.cb`; ensure snapshot.cb is up to date; fsync.
4. **Close skin output endpoints** — anchor-surface client, federation peers receive `skin_restart_pending` close-envelope.
5. **Emit `skin_restart_started` sporocarp** (Daily grade, observability) recording: cycle counter, reason, drain duration, dead-lettered count, snapshot hash.
6. **Exit cleanly** with status 0.

Hard-kill (SIGKILL, OOM-kill) bypasses this sequence — recovery falls to L1_CONTINUITY §4 crash-recovery via WAL replay. The ordered-shutdown protocol is the **soft path**.

### §7.3 Recovery semantics on restart

On supervisor-initiated restart, the substrate executes (in order):

1. Cold-resume pre-handshake checks per L1_CONTINUITY §3.1 (I1, I3, I4, I5, I8).
2. Spatial-locus enumeration per §6 (state_dir / FDs at process start / network bindings about to be opened).
3. WAL crash-recovery per L1_CONTINUITY §4 (replay incomplete cycles, dead-letter partial-deltas).
4. Re-open declared intake endpoints from §1.
5. Substrate transitions `dormant → alive` (no operator yet) and awaits handshake.
6. Emit `skin_restart_completed` sporocarp recording: pre-restart cycle, post-restart cycle (must equal pre-restart cycle since restart is not a metabolic event), WAL recovery outcome, dead-letter count, spatial-locus check outcome.

Cold-resume **invariants** are L1_CONTINUITY §3.1's responsibility; §7.3 here only references them.

### §7.4 Anti-flap rate limit

The supervisor SHOULD enforce a restart-rate limit; the substrate ALSO enforces an in-substrate limit. If the substrate observes ≥ L1-tunable threshold (default 5) `skin_restart_completed` events within an L1-tunable wall-clock window (default 1 hour, queried from anchor-surface trusted-timestamp on each restart), the substrate emits `skin_restart_flap` immune signal (CRITICAL grade) and refuses to re-open intake endpoints until owner-attested `flap_clearance` event arrives.

This prevents an adversarial agent (or buggy supervisor configuration) from inducing endless restart loops that mask other failure modes.

### §7.5 Skin-restart observability events

| Event | Grade | When emitted | Witnesses |
|---|---|---|---|
| `skin_restart_started` | Daily | After shutdown signal, before exit | drain stats, snapshot hash, reason |
| `skin_restart_completed` | Daily | After restart, before re-open | pre/post cycle, WAL outcome, spatial-locus outcome |
| `skin_restart_flap` | CRITICAL | When §7.4 threshold exceeded | restart timestamps, window, threshold |
| `skin_restart_dead_letter` | Elevated | Per envelope dead-lettered on shutdown | envelope digest, dead-letter reason |

These events surface in the L2_OBSERVABILITY drill baseline (every supervisor-initiated restart is observed and provable).

### §7.6 What §7 explicitly does NOT cover

Owner-initiated graceful destruction (L1_GOVERNANCE §4 mortality protocol — terminal, not resumption); P7 self-euthanasia (`self_euthanasia_executed` per L1_GOVERNANCE §4; supervisor MUST not restart after — failure is host-level adversarial action per §5).

---

## §8. Backup encryption requirements (per L0 §11.1)

### §8.1 Threat model addressed

Substrate state_dir backups (per L1_SCHEMA recoverability budget — periodic snapshot.cb copies, off-host disaster-recovery archives) are NOT internally access-controlled by Myco doctrine. Anyone with read access to the backup medium reads full substrate state — including DAG history, owner key archive, sealed-key-derivation parameters, all sporocarps. This is the **G16 backup-attack surface** identified in Phase γ.3.

Two distinct attackers:

- **Backup-medium reader** (e.g., colocation operator with disk access, cloud-storage provider, ex-employee with old backup tape): wants substrate state for surveillance / extortion / model training.
- **Backup-medium tamperer** (more sophisticated): wants to inject altered state on restore-path.

§8 addresses **reader**; **tamperer** is handled by snapshot.cb integrity (M25.0) which is independent of encryption.

### §8.2 Operator-controlled symmetric encryption key

The backup encryption key is **Cultivator-controlled**:

- **Key generation**: at substrate genesis or first-backup-attestation event, Cultivator generates a fresh symmetric key (recommended: AES-256-GCM key or XChaCha20-Poly1305 key). Cultivator generates locally — substrate NEVER mints this key.
- **Key holding**: Cultivator's responsibility. Substrate stores only a **public-derivation pointer** in the SSoT identity record (e.g., a key-ID identifier; the key itself never persists in state_dir).
- **Key access path**: backup process is operator-runtime-mediated. The operator runtime (running on the same host with Cultivator-trust) fetches the key from Cultivator-controlled key storage (hardware token, password manager, OS keyring, HSM — Cultivator's pick) and encrypts the backup. Substrate provides the **plaintext canonical-bytes** at backup time; operator runtime applies encryption transit-side.

This separates the encryption-key custody (Cultivator + operator runtime) from the substrate process (which never holds the key). An adversarial agent cannot exfiltrate the backup key from the substrate because the substrate never had it.

### §8.3 Key escrow protocol

The Cultivator MAY (not must) declare a key-escrow tuple at the anchor surface during their lifetime, supporting recovery if the primary key is lost:

```
key_escrow = (
  escrow_method,        # one of: M-of-N Shamir secret-sharing,
                        #         time-locked hardware token,
                        #         attorney-held sealed envelope,
                        #         successor-Cultivator-co-signed
  escrow_parameters,    # method-specific parameters
  escrow_attestation    # anchor-surface-signed by Cultivator
)
```

If the Cultivator declares **no** escrow, backup recovery on key-loss is **impossible** — the backup becomes a sealed black box. This is a real and acceptable failure mode (some Cultivators value confidentiality above recoverability). DRAFT 9 mandates only that the choice is **explicit and documented at the anchor surface**, not silently assumed.

Successor-Cultivator coordination (per L0 §1.4 Cultivation transferability + L1_GOVERNANCE §3.2 succession): if the Cultivator declares a successor, the key-escrow protocol SHOULD include the successor as one of the M-of-N parties, ensuring the successor inherits backup-decryption capability alongside Cultivation rights.

### §8.4 Key rotation aligned with owner key rotation

Backup encryption-key rotation is **logically distinct** from owner-key (Ed25519 anchor-key) rotation, but the two SHOULD be coordinated to bound exposure of any single compromised key:

- When the Cultivator rotates the owner anchor-key per L1_GOVERNANCE §3.1 (default 30-day cooldown window), the Cultivator SHOULD ALSO rotate the backup encryption-key.
- The new backup-encryption-key is applied to **all backups produced after the rotation**. Older backups remain decryptable with the prior key (which the Cultivator retains in archived state).
- The substrate's SSoT identity record's `backup_key_id_history` tracks `(key_id, valid_from_anchor_timestamp, valid_until_anchor_timestamp, rotation_attestation_signed_by_owner)`, with the same active-prefix + archived-tail discipline as `owner_key_history` per L1_GOVERNANCE §3.1.
- Rotation cooldown windows for backup-keys are L1-tunable; recommended alignment is the same 30-day cooldown as owner-key rotation, so the Cultivator's rotation cadence is unified.

### §8.5 Backup access controls

The backup *file*, once encrypted, has filesystem-level access controls per the host platform's discipline. L1 mandates:

- **Backup files MUST be written with restrictive filesystem permissions** (`umask 077` discipline; Unix `0600` or equivalent ACL). Loose permissions on the backup file (world-readable) emit `backup_permissions_loose` (Elevated) on next backup-emit.
- **Backup destination MUST be declared in the SSoT identity record** as a backup-output endpoint (alongside §1's intake/output endpoints). Writes to undeclared destinations emit `output_endpoint_breach`.
- **Backup integrity** (separate from confidentiality): every backup carries its snapshot.cb canonical-bytes hash signed by the substrate's signing key; the Cultivator verifies the signature on restore. Tampered-or-truncated backup emits `backup_integrity_failure` on attempted restore.

### §8.6 Absent-encryption acknowledgment

Per L0 §11.1: "DRAFT 9 does NOT mandate backup encryption at L0 (operational choice), but DOES mandate that backup access controls are documented at L1 and that absent encryption is acknowledged as a known privacy attack surface."

L1_SKIN ratifies the acknowledgment: if the Cultivator chooses to operate without backup encryption (e.g., air-gapped host, filesystem-level encryption deemed sufficient), the substrate's SSoT identity record carries `backup_encryption_status = "cultivator_declined_explicit"` with the Cultivator-signed declination attestation. Silent omission (no explicit attestation) is treated as `backup_encryption_status = "unspecified"`, which emits `backup_encryption_undeclared` (Daily) on each backup-emit until the Cultivator resolves the question. This is the **Cultivator-aware** acknowledgment — the choice is named, not hidden.

### §8.7 What §8 explicitly does NOT cover

In-process memory encryption (plaintext for canonical-bytes serialization + DAG manipulation; kernel-level adversary defeats §8 — adversarial-Cultivator surface per L0 §14); backup-transit encryption (off-host transit is at-rest-encrypted form; transit-layer TLS/SSH is L4-operational); quantum-cryptography readiness (post-quantum migration is L4 future per L0 §10).

---

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
| **Spatial-locus breach (state_dir file)** | **§6.1 + §6.2** | **`P9_spatial_locus_breach:file_unexpected:{path}`** | **CRITICAL** |
| **Spatial-locus breach (process FD)** | **§6.1 + §6.4** | **`P9_spatial_locus_breach:fd_unexpected:{fd_kind}`** | **CRITICAL** |
| **Spatial-locus breach (network binding)** | **§6.1 + §6.4** | **`P9_spatial_locus_breach:network_unexpected:{peer}`** | **CRITICAL** |
| **Spatial-locus OS-noise observed** | **§6.3** | **`spatial_locus_noise_observed`** | **Daily** |
| **Spatial-locus birth-period pending** | **§6.6** | **`spatial_locus_birth_period_pending`** | **Daily** |
| **Skin-restart flap (rate-limit exceeded)** | **§7.4** | **`skin_restart_flap`** | **CRITICAL** |
| **Skin-restart dead-letter on shutdown** | **§7.5** | **`skin_restart_dead_letter`** | **Elevated** |
| **Backup permissions loose** | **§8.5** | **`backup_permissions_loose`** | **Elevated** |
| **Backup encryption undeclared** | **§8.6** | **`backup_encryption_undeclared`** | **Daily** |
| **Backup integrity failure on restore** | **§8.5** | **`backup_integrity_failure`** | **CRITICAL** |

> Cross-layer immune signals not detected here (`salience_collapse`, `telos_drift` → L1_TROPISM; `compression_invariant_corruption`, `compression_unattested` → L1_SCHEMA; `budget_exhausted:{axis}` → L1_CONTINUITY + L2_OBSERVABILITY signals #7/#8/#9; `generation_depth_exceeded` → L1_GOVERNANCE §4.3; `consensus_floor_bypass` → L2_FEDERATION; `bet_retired` → L2_OBSERVABILITY §7.5) surface in their respective detector docs; this table lists only the skin-detected signals.

CRITICAL breaches → immediate skin-level quarantine per L1_CONTINUITY §5.

---

## §10. Glossary (Cultivation vocabulary per L0 §1.2 G-11.a)

Cultivator / Cultivar / Cultivation / Owner / Anchor surface are defined at L0 §1.2 (canonical glossary). Document-private terms:

- **Spatial locus** — the substrate's physical body: `state_dir + process + skin endpoints`. The operational target of P13 (folded into P9+I8 per G-9.b). See §6.
- **Skin endpoints** — the declared `(intake, output, anchor-surface, federation, backup-output)` from §1 + §8.5; the network/IPC side of the substrate's body.
- **Single integument** — P9 (DRAFT 9). The substrate's single declared skin surface; no redundancy at the integument level, restartability at the process level (P9.b).

**Skin-doc terminology guidance**: default to "Cultivator" for the relational role; use "owner" for crypto/identity-record field names; "agent"/"operator" for the runtime that connects via skin envelopes; avoid "user" (ambiguous) and "system" (de-living).

---

## §11. Open at L1, deferred to L4

- Specific egress-enforcement mechanism within the four candidate families (L4 platform-pick).
- Max-delta-size within {10 MB, 100 MB, 1 GB}.
- Idle timeout within {30, 100, 300 cycles}.
- Post-handshake quarantine window (default 100 cycles).
- Envelope freshness window (default 60 cycles).
- Anchor-surface endpoint protocol per genesis-specified L1_GOVERNANCE §2.1.
- **Process supervisor choice (§7.1)** within {systemd, launchd, Windows Service, container orchestrator}.
- **Drain-deadline (§7.2)** within {10, 30, 120 seconds}.
- **Anti-flap restart window + threshold (§7.4)** within {1 hr / 5 restarts, 24 hr / 20 restarts, custom}.
- **Spatial-locus detection cadence (§6.5)** within {every cycle, every 10 cycles, every 100 cycles}.
- **Spatial-locus substrate-type allowed-set extensions (§6.5)** — substrate-type-specific.
- **Backup encryption suite (§8.2)** within {AES-256-GCM, XChaCha20-Poly1305, post-quantum candidate}.
- **Backup key escrow method (§8.3)** within {Shamir M-of-N, time-locked HSM, attorney-held envelope, successor-co-signed}.
- **Backup-key rotation cadence (§8.4)** aligned with L1_GOVERNANCE §3.1 owner-key rotation.

The shape is committed; values are L4.
