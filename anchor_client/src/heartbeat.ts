// Owner liveness heartbeat — TypeScript implementation (L1_GOVERNANCE §3.2).
//
// Per L1_GOVERNANCE §3.2 owner succession: succession activation uses
// **positive owner-liveness-heartbeat staleness** at the anchor surface, NOT
// substrate-side absence-of-CI-emission. The owner periodically signs
// `liveness_heartbeat` events at the anchor surface; succession trigger fires
// only when the heartbeat has been stale for ≥ L1-tunable window.
//
// Per L1_HARD_RULES §4: owner_liveness_heartbeat is anchor-surface-resident
// state. The substrate cannot author it (only the owner's sealed key signs).
//
// ## M2 scope
//
// - `HeartbeatEvent`: canonical structure for a single liveness heartbeat.
// - `signHeartbeat`: owner-side signing using a SealedKey.
// - `verifyHeartbeat`: substrate-side verification using a known owner pubkey.
// - `staleness`: returns seconds since the last heartbeat at a given clock.
//
// Cadence (L1_GOVERNANCE §7 default: monthly) is owner-policy; this module
// provides the primitives. The anchor-surface server (M3+) tracks the
// freshest heartbeat per substrate.

import {
  CanonicalBytes,
  encode,
  type Value,
} from "./canonical_bytes.ts";
import { Ed25519PublicKey, Ed25519Signature, verifySignature } from "./crypto.ts";
import type { SealedKey } from "./sealed_key.ts";

/** Errors. */
export class HeartbeatError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "HeartbeatError";
  }
}

export class HeartbeatInvalid extends HeartbeatError {
  constructor(message: string) {
    super(`heartbeat invalid: ${message}`);
    this.name = "HeartbeatInvalid";
  }
}

/** A single owner-liveness heartbeat event. */
export interface HeartbeatEvent {
  /** Substrate-ID this heartbeat is for (one heartbeat per substrate; an
   * owner managing N substrates emits N heartbeats per cadence). */
  substrateId: string;

  /** Anchor-surface trusted Unix-seconds timestamp at emission. */
  anchorTimestampUnixSeconds: number;

  /** Owner's Ed25519 signature over `canonicalBytes(event)`. */
  ownerSignature: Ed25519Signature;
}

/** Canonical-bytes representation of the heartbeat (the bytes the owner signs).
 *
 * Per L1_GOVERNANCE §3.2: the heartbeat is owner-attested. Substrate
 * receiving a heartbeat verifies the signature against the active owner key.
 */
export function heartbeatCanonicalBytes(
  substrateId: string,
  anchorTimestampUnixSeconds: number,
): CanonicalBytes {
  const m_value: Value = {
    type: "map",
    value: new Map<string, Value>([
      ["type", { type: "string", value: "owner_liveness_heartbeat" }],
      ["substrate_id", { type: "string", value: substrateId }],
      [
        "anchor_timestamp_unix_seconds",
        { type: "timestamp", value: BigInt(anchorTimestampUnixSeconds) },
      ],
    ]),
  };
  return encode(m_value);
}

/**
 * Sign a heartbeat event (owner side).
 *
 * The owner runs this with their sealed key + the anchor-surface-trusted
 * timestamp. Resulting event is sent to the anchor-surface server, which
 * appends to the per-substrate heartbeat log.
 */
export function signHeartbeat(
  sealedKey: SealedKey,
  substrateId: string,
  anchorTimestampUnixSeconds: number,
): HeartbeatEvent {
  const canonical = heartbeatCanonicalBytes(
    substrateId,
    anchorTimestampUnixSeconds,
  );
  const sig = sealedKey.sign(canonical.bytes);
  return {
    substrateId,
    anchorTimestampUnixSeconds,
    ownerSignature: sig,
  };
}

/**
 * Verify a heartbeat event (substrate side).
 *
 * Per L1_GOVERNANCE §2.3 step 2: substrate verifies owner signatures
 * against the key valid at the attestation's anchor-surface timestamp.
 * Same applies to heartbeats: verify against the owner-key active at
 * `event.anchorTimestampUnixSeconds`.
 *
 * @throws {HeartbeatInvalid} if the signature does not verify.
 */
export function verifyHeartbeat(
  event: HeartbeatEvent,
  ownerPublicKey: Ed25519PublicKey,
): void {
  const canonical = heartbeatCanonicalBytes(
    event.substrateId,
    event.anchorTimestampUnixSeconds,
  );
  try {
    verifySignature(
      ownerPublicKey.bytes,
      event.ownerSignature.bytes,
      canonical.bytes,
    );
  } catch (e) {
    throw new HeartbeatInvalid(
      `signature does not verify: ${(e as Error).message}`,
    );
  }
}

/**
 * Compute heartbeat staleness in seconds.
 *
 * Returns the elapsed time since `heartbeat.anchorTimestampUnixSeconds`
 * given the current clock. Negative if heartbeat is in the future
 * (clock skew); the caller decides how to handle.
 *
 * Used by the succession-trigger logic per L1_GOVERNANCE §3.2: when
 * staleness exceeds the L1-tunable window, owner-succession activation
 * is enabled.
 */
export function heartbeatStalenessSeconds(
  heartbeat: HeartbeatEvent,
  currentUnixSeconds: number,
): number {
  return currentUnixSeconds - heartbeat.anchorTimestampUnixSeconds;
}
