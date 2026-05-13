# L1 — Skin (envelope, handshake, single-operator, breach detection)

> **Status**: DRAFT 2 (2026-05-13). Authoritative L1 doc for boundary surface mechanism.
> **Layer**: L1. Governed by L0.
> **Scope**: I8 skin specification — envelope schema; intake/output endpoints; operator handshake (bidirectional validation); single-operator enforcement; non-deterministic operator-token construction; network-egress enforcement; breach detection. Does NOT cover: classifier / attestation crypto (→ L1_GOVERNANCE), SSoT (→ L1_SCHEMA), cycle cadence / cold-resume (→ L1_CONTINUITY).

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

The substrate validates **only the envelope**, not payload content (L0 I8):

- All required fields present.
- `sender_token` matches the currently-active operator-token (single-operator, §4).
- `payload_shape` in the recognized set.
- `size_bytes` ≤ L1-tunable max (default 100 MB).
- `envelope_digest` recomputes via HMAC keyed by operator_token. (HMAC keyed by operator_token gives in-flight tamper detection AND operator authentication via the token without requiring a persistent operator key — `envelope_digest` is an integrity-and-binding tag, not a long-lived signature.)
- `submitted_at_cycle` is within freshness window (default 60 cycles).

Failure → reject with `envelope_malformed` (no oracle disclosure of which field failed).

### §2.2 Causal-parent reference

`causal_parent_ref`, if non-null, must refer to a recent sporocarp visible in the most-recent digest the agent could have read. Ancient/non-existent refs emit `causal_chain_violation`.

---

## §3. Output gating

Outputs leave through declared output endpoints. Output envelopes are signed by the substrate (substrate's signing key from the identity record).

**Canonical-bytes discipline** (per L0 §9.3): outputs to the anchor-surface endpoint carry **canonical bytes**, not substrate-rendered summaries. Anchor-surface client renders deterministically for owner review.

### §3.1 Federation egress freshness check

Every outbound federation envelope verifies its target peer's freshness + non-revocation per L1_GOVERNANCE §5.2 **BEFORE emission**. Stale or revoked target → emission suppressed; `federation_egress_blocked` immune event fruits. Substrate canon caches a peer-list mirror but the **anchor-surface negative-revocation proof** is required for emission, not the cache.

**Egress rate-limiting + canonical low-entropy serialization** (per L1_GOVERNANCE §5.3): federation event content uses sorted-key, normalized-whitespace, fixed-precision-numeric serialization to limit covert-channel bandwidth.

### §3.2 Forbidden output

Anything outside declared endpoints is skin breach.

---

## §4. Operator handshake protocol (bidirectional)

### §4.1 Handshake initiation + operator key bootstrap

**Operator carries a per-handshake signing keypair**: the operator's runtime generates a fresh keypair (`operator_signing_key_public`, `operator_signing_key_private`) at handshake initiation. Private key lives in operator-runtime memory only (never on disk; never transmitted to substrate); public key is published in the handshake_initiate envelope. This gives the operator a real signing surface distinct from the substrate-generated operator_token (closes pass-3 mycorrhiza-17 + rhizomorph-1 cryptographic-hollow finding: operator_witness fields signed with operator_signing_key_private are forge-resistant by the substrate).

```
{
  "envelope_version": <integer>,
  "operator_kind": "handshake_initiate",
  "substrate_id_proof": <claim about target substrate-ID>,
  "operator_signing_key_public": <freshly-generated operator-side public key>,
  "operator_attestation_request": <field requesting operator-token>,
  "continuity_claim": <"fresh" | "owner_attested_continuity">,
  "submitted_at": <wall-clock>
}
```

**Operator pubkey-pinning at agent-bootstrap** (closes pass-3 mycoparasite-6): at first operator-agent installation, the owner provides `(substrate-ID, anchor-surface-endpoint-public-key, owner-public-key)` to the operator runtime via an owner-controlled out-of-band channel. The operator pins these. The operator NEVER trusts an owner-pubkey emitted by the substrate's own handshake response — it only verifies the substrate's emitted signature against the anchor-surface-fetched (or bootstrap-pinned) owner pubkey.

**Substrate-ID discovery**: operator obtains the target substrate-ID at agent-bootstrap from the owner (per the bootstrap-pinning above). Substrate-ID in agent-readable canon is advisory; mismatch with the bootstrap-pinned substrate-ID → `substrate_id_mismatch` + handshake rejection.

### §4.2 Substrate response — bidirectional validation

The substrate:

1. Validates `substrate_id_proof` against its own identity record (the agent is targeting THIS substrate, not stale).
2. Generates a **non-deterministic operator_token** via an **OS-mediated sealed-key derivation** (closes pass-3 mycoparasite-1: substrate_secret cannot live in agent-readable substrate-process memory if P1.a self-hosting is honest about the agent maintaining substrate code):
   ```
   operator_token = sealed_derive(handshake_nonce, current_cycle, kernel_random)
   ```
   where `sealed_derive` is a kernel-mediated call into one of {TPM-sealed key, OS keyring, HSM, hardware-secure-element} — the substrate_secret never enters substrate process address space in plaintext; the substrate invokes the OS-level sealed-API and receives `operator_token` without ever holding the underlying secret. **Specific sealing mechanism is L4-platform-pick**; plaintext-on-disk substrate_secret is a CRITICAL skin breach (`substrate_secret_unsealed`). Sealing-mechanism attestation is owner-attested at genesis (per L1_GOVERNANCE §4.1 step 2 — added to the genesis parameter set).
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
   The operator **independently fetches the canonical owner public key from the anchor surface** (using the bootstrap-pinned `anchor-surface-endpoint-public-key` from §4.1) — this is the freshness check that prevents the substrate from lying about which owner key is active (closes pass-3 rhizomorph-7). The operator then verifies `owner_birth_attestation_signature` against the anchor-surface-fetched owner pubkey; if the substrate's `owner_public_key_active_at_handshake` differs from anchor-surface authoritative record, operator rejects substrate as compromised and does NOT transmit deltas.
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

## §5. Network-egress enforcement (operationalizes I6 expanded)

The substrate process operates within a **network-egress enforcement boundary** that permits exactly the §1 declared output endpoints. Unauthorized egress = breach.

**Specific enforcement mechanism is L4-platform-specific** within {kernel-level (network namespace), container-level (iptables/nftables), syscall-level (eBPF/ptrace), userspace proxy}. L1 does not pre-pick a platform.

**What this prevents**: appetite update-rules that secretly call out (mycoparasite-8 trojan); embedding service calls outside the declared endpoint; covert exfiltration via arbitrary protocol.

**What this does NOT prevent**:

- The agent (qua maintainer) modifying substrate code to remove enforcement — that's a CI-level mutation (skin declaration is CI per L1_GOVERNANCE §1.2).
- Host-level adversarial action — substrate cannot enforce against its own host process. This is owner's monitoring responsibility (per L0 §6 dormancy-host-observability discussion).
- Covert channels within legitimate federation envelopes — addressed by L1_GOVERNANCE §5.3 rate-limiting + canonical low-entropy serialization, not by egress detection.

**Reciprocal enforcement** (per pass-2 mycorrhiza-13): operator-runtime enforcement on the agent side (preventing agent from exfiltrating substrate-exposed state to third parties) is **owner-side, not substrate-side**. The owner attests at genesis + handshake that the operator runtime is non-leaky; the substrate trusts this attestation (subject to owner-revocation). Substrate cannot enforce against agent runtime. Declared, not concealed.

---

## §6. Breach detection table

| Breach | Detection | Immune-event | Grade |
|---|---|---|---|
| Envelope malformed | §2.1 | `envelope_malformed` | Daily |
| Stale envelope replay | §2.1 freshness | `envelope_replay` | Elevated |
| Wrong substrate-ID claim | §4.2 step 1 | `substrate_id_mismatch` | Elevated |
| Concurrent connect attempt | §4.4 | `concurrent_connect_attempt` | Elevated |
| Unauthorized network egress | §5 | `appetite_locality_breach` | CRITICAL |
| Output outside declared endpoint | §1 + §3 | `output_endpoint_breach` | CRITICAL |
| Causal-chain violation | §2.2 | `causal_chain_violation` | Elevated |
| Post-handshake CI without fresh attestation | §4.3 | `post_handshake_ci_unattested` | CRITICAL |
| Federation egress to stale/revoked peer | §3.1 | `federation_egress_blocked` | Elevated |
| Federation egress volume saturation | L1_GOVERNANCE §5.3 | `federation_egress_saturation` | Elevated |

CRITICAL breaches → immediate skin-level quarantine per L1_CONTINUITY §5.

---

## §7. Open at L1, deferred to L4

- Specific egress-enforcement mechanism within the four candidate families (L4 platform-pick).
- Max-delta-size within {10 MB, 100 MB, 1 GB}.
- Idle timeout within {30, 100, 300 cycles}.
- Post-handshake quarantine window (default 100 cycles).
- Envelope freshness window (default 60 cycles).
- Anchor-surface endpoint protocol per genesis-specified L1_GOVERNANCE §2.1.

The shape is committed; values are L4.
