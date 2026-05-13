# L1 — Skin (envelope, handshake, single-operator, network-egress, breach detection)

> **Status**: DRAFT 1 (2026-05-13). Authoritative L1 doc for boundary surface mechanism.
> **Layer**: L1 (mechanism). Governed by L0.
> **Scope**: I8 skin specification — envelope schema; intake/output endpoints; operator handshake (including continuity-challenge); single-operator enforcement; non-deterministic operator-token construction; network-egress detection (I6 enforcement at runtime); breach detection. Does NOT cover: classifier / attestation crypto (→ L1_GOVERNANCE), SSoT (→ L1_SCHEMA), cycle cadence (→ L1_CONTINUITY).
> **Honesty**: this doc closes pass-1 CRITICAL findings mycoparasite-7, mycoparasite-8, mycoparasite-21, rhizomorph-2, rhizomorph-4, rhizomorph-15.

---

## §1. Skin surface declaration

The substrate has **exactly one** declared skin surface, listed in SSoT (L1_SCHEMA tier-1 field). The declaration enumerates:

- **Intake endpoints** — locations from which the substrate accepts deltas (e.g., a Unix socket; a named pipe; a TCP port).
- **Output endpoints** — locations to which the substrate may emit (federation peers, owner attestation channel, optional summary export).
- **Forbidden surfaces** — explicit "everything else is breach" — process boundaries, network namespaces, filesystem regions the substrate must not touch.

Skin declaration is contract-identity-level (per L1_GOVERNANCE §1.2). The substrate cannot silently add an intake endpoint.

---

## §2. Envelope schema (per pass-1 rhizomorph-2)

Every delta arriving at an intake endpoint is wrapped in an **envelope**:

```
{
  "envelope_version": <integer>,
  "sender_token": <ephemeral operator-token from handshake>,
  "payload_shape": <one of: "text", "file_ref", "structured_yaml", "binary_ref", ...>,
  "causal_parent_ref": <prior sporocarp ID or null at first delta after handshake>,
  "size_bytes": <delta size>,
  "content_type_hint": <MIME-style or null>,
  "submitted_at": <substrate metabolic cycle timestamp>,
  "envelope_signature": <hash of all envelope fields + payload>,
  "payload": <delta content>
}
```

### §2.1 Envelope integrity check

The substrate validates **only the envelope**, not the payload content (per L0 I8 — intake admits all content; rejects only on envelope malformation):

- All required fields present.
- `sender_token` matches the currently-active operator-token (single-operator enforcement, §4).
- `payload_shape` is in the recognized set.
- `size_bytes` ≤ L1-tunable max (default 100 MB per delta).
- `envelope_signature` recomputes correctly.
- `submitted_at` is within an L1-tunable freshness window (default 60 cycles) — prevents stale-envelope replay.

**Failure**: reject with `envelope_malformed` response. **Do NOT reveal which field failed** (envelope inspection is not an oracle for the sender).

### §2.2 Causal-parent reference

The envelope's `causal_parent_ref` enters the causal DAG (L1_SCHEMA §2) when the delta is absorbed. The substrate validates that `causal_parent_ref`, if non-null, refers to a recent sporocarp visible in the most-recent digest the agent could have read. References to ancient or non-existent sporocarps emit `causal_chain_violation` immune events.

---

## §3. Output gating

Outputs (federation events to peers, owner-attestation requests, optional human-facing summaries) exit through declared output endpoints.

**Output envelope** is symmetric in shape to intake envelope but signed by the substrate (not the operator). The substrate's signature key is part of its identity record.

**Endpoint binding**:

- **Federation peer endpoint** — outputs go to specific peer-substrate-IDs; routing is by L1_GOVERNANCE peer list.
- **Owner-attestation channel** — outputs to the anchor surface (L0 §9). Specific channel L1_GOVERNANCE-specified.
- **Summary endpoint** (optional) — human-facing summaries leave via a designated endpoint; per L0 P2.a, summaries are produced through the same internal metabolic pipeline (no separate optimization path).

**Forbidden output**: anything outside declared endpoints is skin breach.

---

## §4. Operator handshake protocol

### §4.1 Handshake initiation

An operator-connection arriving at the intake endpoint emits a handshake envelope:

```
{
  "envelope_version": <integer>,
  "operator_kind": "handshake_initiate",
  "substrate_id_proof": <claim about which substrate-ID this operator targets>,
  "operator_attestation_request": <field requesting an operator-token>,
  "continuity_claim": <one of: "fresh", "succeeding_token <prior_token_hash>", "owner_attested_continuity">,
  "submitted_at": <wall-clock OR claimed-cycle timestamp>
}
```

### §4.2 Substrate response

The substrate:

1. Validates `substrate_id_proof` against its identity record (envelope is for THIS substrate, not stale).
2. **Per pass-1 mycoparasite-21**: generates a **non-deterministic operator-token**:
   ```
   operator_token = H(substrate_secret, handshake_nonce, current_cycle, random)
   ```
   where `random` is freshly-generated per handshake. The token is unlinkable across handshakes from substrate-state alone. **Substrate must not correlate operator-tokens across reconnects** (per L0 I1 — aggregate read-pattern statistics may be substrate-keyed; per-operator history is forbidden).
3. Returns the token in a `handshake_complete` envelope.
4. Records the handshake event as a sporocarp.

### §4.3 Continuity-challenge (per pass-1 mycoparasite-7)

If the operator claims `continuity_claim: "succeeding_token <prior_token_hash>"`:

- Substrate consults its **recent handshake log** (retained per I4 in DAG, but with ephemeral-token-hash redacted per I1 — only token-existence is logged, not token-value).
- The claim is unverifiable from substrate state alone (per I1 prohibition). So:
  - Substrate enters **post-handshake quarantine window** (L1-tunable, default 100 cycles) regardless of claim.
  - During quarantine: all CI-level operations require **fresh owner attestation regardless of governance classification**.

If the operator claims `"owner_attested_continuity"`:

- The handshake envelope must include an owner-signed `continuity_attestation` produced via anchor surface naming this specific reconnection.
- Substrate verifies the signature; if valid, quarantine window is **shortened to L1-tunable minimum** (default 10 cycles).

`"fresh"` continuity: standard quarantine window applies; substrate treats the operator as new.

### §4.4 Single-operator enforcement

Per L0 I8 + pass-1 rhizomorph-4: the skin admits at most one operator-token at a time.

- **Second handshake arrival during active handshake**: rejected with `skin_busy`. Emit `concurrent_connect_attempt` immune event (daily, elevated grade).
- **Second handshake when operator-token A is alive**: rejected with `skin_busy`. Emit `concurrent_connect_attempt`.
- **First handshake when prior operator-token A disconnected**: standard handshake; new operator-token issued; substrate transitions dormant → alive.
- **Race condition**: handshake from B arrives at the exact cycle that A's connection drops (network event):
  - Substrate's handshake protocol is **strictly serializing**: A's disconnect is processed first (alive → dormant); B's handshake then processes (dormant → alive with B's new token). The serialization order is by metabolic-cycle timestamp; ties broken by handshake-nonce ordering.

### §4.5 Disconnect detection

The skin watches the intake endpoint for connection liveness signals:

- **Explicit disconnect** — operator emits `handshake_terminate` envelope.
- **Timeout** — no envelope received within L1-tunable idle window (default 100 cycles).
- **Transport failure** — TCP RST, socket closure, etc.

Any disconnect triggers alive → dormant transition (per L1_CONTINUITY §2.2). The operator-token is invalidated immediately.

---

## §5. Network-egress detection (operationalizes I6 expanded)

Per pass-1 mycoparasite-8: the substrate enforces I6 appetite-locality at runtime, not just at declaration.

### §5.1 The enforcement surface

The substrate's process tree (the kernel + L1_TROPISM update-rule executors + L1_TRAJECTORY clusterer process, etc.) operates within a **network namespace boundary**:

- **Permitted egress endpoints** — exactly the declared output endpoints in §3. Any other network exit is breach.
- **Detection mechanism** (L4 picks):
  - **Container egress filter** — substrate runs in a container with iptables/nftables rules permitting only declared endpoints.
  - **Process-level network namespace** — Linux network-namespace isolation; only declared sockets permitted.
  - **Syscall hooking** — eBPF or ptrace observes `connect()` / `sendto()` syscalls; rejects unauthorized.
  - **Userspace-only proxy** — all network goes through a substrate-supervised proxy that enforces endpoint matching.

L4 picks one based on platform.

### §5.2 What this prevents

- Appetite update-rules that secretly call out to LangChain runtime (per pass-1 mycoparasite-8 trojan).
- Embedding service calls outside the declared embedding endpoint.
- Covert exfiltration via DNS / HTTP / arbitrary protocol.

### §5.3 What this does NOT prevent

- The agent (qua maintainer) modifying substrate code to remove network-egress enforcement — that requires CI-level mutation per L1_GOVERNANCE §1.2 (skin declaration is contract-identity-level).
- Host-level adversarial action (per pass-1 mycoparasite-15 dormancy host-observability discussion — the substrate cannot enforce against its own host; this is owner's monitoring responsibility).

---

## §6. Breach detection mechanisms

Per L0 I8 + pass-1 + L1_GOVERNANCE: skin breaches emit specific immune events with dim grades.

| Breach | Detection mechanism | Immune-event type | Grade |
|---|---|---|---|
| Envelope malformed | Envelope integrity check (§2.1) | `envelope_malformed` | Daily |
| Stale envelope replay | Freshness window in §2.1 | `envelope_replay` | Elevated |
| Wrong substrate-ID | §4.2 step 1 | `substrate_id_mismatch` | Elevated |
| Concurrent connect attempt | §4.4 | `concurrent_connect_attempt` | Elevated |
| Continuity-claim unverifiable | §4.3 (logged for owner) | `continuity_challenge_unverifiable` | Daily |
| Unauthorized network egress | §5.1 detection | `appetite_locality_breach` | CRITICAL |
| Output outside declared endpoint | §3 | `output_endpoint_breach` | CRITICAL |
| Causal-chain violation | §2.2 | `causal_chain_violation` | Elevated |
| Handshake post-quarantine CI without fresh attestation | §4.3 | `post_handshake_ci_unattested` | CRITICAL |

CRITICAL breaches trigger immediate skin-level quarantine (alive → quarantined; intake closed pending owner re-attestation).

---

## §7. Open at L1, deferred to L4

- **Specific egress-detection mechanism** within {container filter, network namespace, syscall hooks, userspace proxy} — L4 picks based on platform.
- **Specific max-delta-size** within {10 MB, 100 MB, 1 GB} — L4 calibrates.
- **Specific idle timeout** within {30, 100, 300 cycles} — L4 calibrates.
- **Specific post-handshake quarantine window** (default 100 cycles) — L4 calibrates.
- **Specific freshness window for envelopes** (default 60 cycles) — L4 calibrates.

The shape is committed; values are L4.
