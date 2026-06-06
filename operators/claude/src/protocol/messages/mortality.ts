// M22.5 / M23.2 — operator mortality overrides (KEYLESS v0.9).
//
// Split out of the former monolithic `protocol/messages.ts`. Mirrors
// `substrate::lifecycle::handle_lift_birth_period_quarantine` +
// `handle_accept_self_euthanasia_proposal`. **v0.9 owner-key removal**: both
// handlers are now keyless — the owner Ed25519 signature gates were dropped with
// the anchor surface. lift_birth_period_quarantine reads nothing from the
// payload; accept_self_euthanasia_proposal needs only a real `proposal_hash`.

import { type Value } from "../../canonical/canonical_bytes.ts";
import { BridgeProtocolError, type Message, MSG_TYPE } from "./wire.ts";

/** Build the payload for `lift_birth_period_quarantine` (M22.5; KEYLESS v0.9).
 *
 *  The owner Ed25519 signature gate was removed with the anchor surface;
 *  `handle_lift_birth_period_quarantine` reads NOTHING from the payload, so
 *  this sends an empty Map. */
export function liftBirthPeriodQuarantinePayload(): Map<string, Value> {
  return new Map<string, Value>();
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

/** Build the payload for `accept_self_euthanasia_proposal` (M23.2; keyless
 *  v3.1.5 — the owner Ed25519 co-signature was removed with the anchor layer.
 *  Whole-death is a deliberate call referencing a real proposal node). */
export function acceptSelfEuthanasiaProposalPayload(args: {
  proposalHash: Uint8Array;
}): Map<string, Value> {
  if (args.proposalHash.length !== 32) {
    throw new BridgeProtocolError(
      `proposal_hash must be 32 bytes; got ${args.proposalHash.length}`,
    );
  }
  const m = new Map<string, Value>();
  m.set("proposal_hash", { type: "bytes", value: args.proposalHash });
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
