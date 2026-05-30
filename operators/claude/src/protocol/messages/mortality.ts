// M22.5 / M23.2 — operator owner-signed mortality overrides.
//
// Split out of the former monolithic `protocol/messages.ts`. Mirrors
// `substrate::server::handle_lift_birth_period_quarantine` +
// `handle_accept_self_euthanasia_proposal`. The signing-input Map shapes are
// the security boundary; one byte off breaks the substrate signature check.

import { encode, type Value } from "@myco/anchor-client/src/canonical_bytes.ts";
import { BridgeProtocolError, type Message, MSG_TYPE } from "./wire.ts";

/** Compute the canonical-bytes signing input for `lift_birth_period_quarantine`
 *  owner attestation (M22.5; Phase β security fix).
 *
 *  Mirrors Rust reconstruction in `handle_lift_birth_period_quarantine`:
 *  ```
 *  canonical_bytes(Map({
 *    "context": "myco-lift-birth-period-quarantine-v1",
 *    "substrate_id": Bytes(32),
 *    "current_cycle": Uint(cycle_counter),
 *  }))
 *  ```
 *
 *  The operator IDENTITY key signs THIS. The `current_cycle` field binds the
 *  signature to a specific point in time — replay across cycles is blocked.
 */
export function liftBirthPeriodQuarantineSigningInput(
  substrateId: Uint8Array,
  currentCycle: bigint,
): Uint8Array {
  if (substrateId.length !== 32) {
    throw new BridgeProtocolError(
      `substrate_id must be 32 bytes; got ${substrateId.length}`,
    );
  }
  const m = new Map<string, Value>();
  m.set("context", {
    type: "string",
    value: "myco-lift-birth-period-quarantine-v1",
  });
  m.set("substrate_id", { type: "bytes", value: substrateId });
  m.set("current_cycle", { type: "uint", value: currentCycle });
  return encode({ type: "map", value: m }).bytes;
}

/** Build the payload for `lift_birth_period_quarantine` (M22.5). */
export function liftBirthPeriodQuarantinePayload(args: {
  ownerSignature: Uint8Array;
}): Map<string, Value> {
  if (args.ownerSignature.length !== 64) {
    throw new BridgeProtocolError(
      `owner_signature must be 64 bytes; got ${args.ownerSignature.length}`,
    );
  }
  const m = new Map<string, Value>();
  m.set("owner_signature", { type: "bytes", value: args.ownerSignature });
  return m;
}

/** Parsed `lift_birth_period_quarantine_response` (M22.5). */
export interface LiftBirthPeriodQuarantineResult {
  /** True iff the substrate was in active quarantine when the call landed. */
  wasInQuarantine: boolean;
  /** DAG node hash of the emitted `birth_period_quarantine_lifted` event;
   *  null when wasInQuarantine=false (nothing to lift). */
  quarantineLiftedEventHash: Uint8Array | null;
}

export function parseLiftBirthPeriodQuarantineResponse(
  response: Message,
): LiftBirthPeriodQuarantineResult {
  if (response.messageType !== MSG_TYPE.LIFT_BIRTH_PERIOD_QUARANTINE_RESPONSE) {
    throw new BridgeProtocolError(
      `expected lift_birth_period_quarantine_response; got ${response.messageType}`,
    );
  }
  const wasV = response.payload.get("was_in_quarantine");
  if (!wasV || wasV.type !== "bool") {
    throw new BridgeProtocolError(
      "lift_birth_period_quarantine_response missing was_in_quarantine bool",
    );
  }
  const hashV = response.payload.get("quarantine_lifted_event_hash");
  return {
    wasInQuarantine: wasV.value,
    quarantineLiftedEventHash:
      hashV && hashV.type === "bytes" ? hashV.value : null,
  };
}

/** Compute the canonical-bytes signing input for `accept_self_euthanasia_proposal`
 *  owner co-attestation (M23.2 P7 必朽).
 *
 *  Mirrors Rust reconstruction in `handle_accept_self_euthanasia_proposal`:
 *  ```
 *  canonical_bytes(Map({
 *    "context": "myco-self-euthanasia-v1",
 *    "proposal_hash": Bytes(32),
 *    "substrate_id": Bytes(32),
 *  }))
 *  ```
 *
 *  The operator IDENTITY key signs THIS. The triple binding
 *  (context + proposal_hash + substrate_id) prevents replay:
 *  - context: distinct from other operator co-attestations
 *  - proposal_hash: this specific proposal in this DAG
 *  - substrate_id: not replayable against another substrate
 */
export function acceptSelfEuthanasiaProposalSigningInput(
  proposalHash: Uint8Array,
  substrateId: Uint8Array,
): Uint8Array {
  if (proposalHash.length !== 32) {
    throw new BridgeProtocolError(
      `proposal_hash must be 32 bytes; got ${proposalHash.length}`,
    );
  }
  if (substrateId.length !== 32) {
    throw new BridgeProtocolError(
      `substrate_id must be 32 bytes; got ${substrateId.length}`,
    );
  }
  const m = new Map<string, Value>();
  m.set("context", { type: "string", value: "myco-self-euthanasia-v1" });
  m.set("proposal_hash", { type: "bytes", value: proposalHash });
  m.set("substrate_id", { type: "bytes", value: substrateId });
  return encode({ type: "map", value: m }).bytes;
}

/** Build the payload for `accept_self_euthanasia_proposal` (M23.2). */
export function acceptSelfEuthanasiaProposalPayload(args: {
  proposalHash: Uint8Array;
  ownerSignature: Uint8Array;
}): Map<string, Value> {
  if (args.proposalHash.length !== 32) {
    throw new BridgeProtocolError(
      `proposal_hash must be 32 bytes; got ${args.proposalHash.length}`,
    );
  }
  if (args.ownerSignature.length !== 64) {
    throw new BridgeProtocolError(
      `owner_signature must be 64 bytes; got ${args.ownerSignature.length}`,
    );
  }
  const m = new Map<string, Value>();
  m.set("proposal_hash", { type: "bytes", value: args.proposalHash });
  m.set("owner_signature", { type: "bytes", value: args.ownerSignature });
  return m;
}

/** Parsed `accept_self_euthanasia_proposal_response` (M23.2). */
export interface AcceptSelfEuthanasiaProposalResult {
  /** The mortality_signal axis name that originally fruited (echoed from proposal). */
  axisName: string;
  /** DAG node hash of the emitted `self_euthanasia_executed:{axis}` event —
   *  the substrate's signed post-mortem record. The substrate gracefully
   *  shuts down AFTER this response is written. */
  executedEventHash: Uint8Array;
}

export function parseAcceptSelfEuthanasiaProposalResponse(
  response: Message,
): AcceptSelfEuthanasiaProposalResult {
  if (response.messageType !== MSG_TYPE.ACCEPT_SELF_EUTHANASIA_PROPOSAL_RESPONSE) {
    throw new BridgeProtocolError(
      `expected accept_self_euthanasia_proposal_response; got ${response.messageType}`,
    );
  }
  const axisV = response.payload.get("axis_name");
  const hashV = response.payload.get("executed_event_hash");
  if (
    !axisV || axisV.type !== "string" ||
    !hashV || hashV.type !== "bytes"
  ) {
    throw new BridgeProtocolError(
      "accept_self_euthanasia_proposal_response missing required typed fields",
    );
  }
  return {
    axisName: axisV.value,
    executedEventHash: hashV.value,
  };
}
