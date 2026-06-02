// M25.5 P5 万物互联: operator-facing federation message builders/parsers.
//
// Split out of the former monolithic `protocol/messages.ts`. All
// payloads/responses mirror `substrate::server::handle_federation_*`. Field
// name/type drift = bridge protocol drift, surface as decode errors here.

import { type Value } from "@myco/anchor-client/src/canonical_bytes.ts";
import { BridgeProtocolError, type Message, MSG_TYPE } from "./wire.ts";

/** Build the payload for a `federation_open_listener` request (M22.1).
 *
 *  `bindAddr` may be `"127.0.0.1:0"` to let the OS pick a port. Resolved
 *  address is returned by the substrate in the response.
 */
export function federationOpenListenerPayload(args: {
  bindAddr: string;
}): Map<string, Value> {
  if (!args.bindAddr || args.bindAddr.length === 0) {
    throw new BridgeProtocolError(
      "federation_open_listener: bind_addr must be non-empty",
    );
  }
  const m = new Map<string, Value>();
  m.set("bind_addr", { type: "string", value: args.bindAddr });
  return m;
}

/** Parsed `federation_open_listener_response` (M22.1). */
export interface FederationOpenListenerResult {
  /** Resolved bind address (port-zero replaced by OS-picked port). */
  boundAddr: string;
  /** DAG node hash of the `federation_listener_opened` event. */
  listenerOpenedEventHash: Uint8Array;
}

export function parseFederationOpenListenerResponse(
  response: Message,
): FederationOpenListenerResult {
  if (response.messageType !== MSG_TYPE.FEDERATION_OPEN_LISTENER_RESPONSE) {
    throw new BridgeProtocolError(
      `expected federation_open_listener_response; got ${response.messageType}`,
    );
  }
  const addrV = response.payload.get("bind_addr");
  const hashV = response.payload.get("listener_opened_event_hash");
  if (
    !addrV || addrV.type !== "string" ||
    !hashV || hashV.type !== "bytes"
  ) {
    throw new BridgeProtocolError(
      "federation_open_listener_response missing required typed fields",
    );
  }
  return {
    boundAddr: addrV.value,
    listenerOpenedEventHash: hashV.value,
  };
}

/** Build the payload for a `federation_close_listener` request (M22.1).
 *  Empty payload — idempotent, no-op if no listener active. */
export function federationCloseListenerPayload(): Map<string, Value> {
  return new Map<string, Value>();
}

/** Parsed `federation_close_listener_response` (M22.1). */
export interface FederationCloseListenerResult {
  /** True iff a listener was active and got closed. */
  wasListening: boolean;
  /** The address that was bound (empty string when wasListening=false). */
  priorBindAddr: string;
  /** DAG hash of the `federation_listener_closed` event; null if no listener. */
  listenerClosedEventHash: Uint8Array | null;
}

export function parseFederationCloseListenerResponse(
  response: Message,
): FederationCloseListenerResult {
  if (response.messageType !== MSG_TYPE.FEDERATION_CLOSE_LISTENER_RESPONSE) {
    throw new BridgeProtocolError(
      `expected federation_close_listener_response; got ${response.messageType}`,
    );
  }
  const wasV = response.payload.get("was_listening");
  const addrV = response.payload.get("prior_bind_addr");
  if (
    !wasV || wasV.type !== "bool" ||
    !addrV || addrV.type !== "string"
  ) {
    throw new BridgeProtocolError(
      "federation_close_listener_response missing required typed fields",
    );
  }
  const hashV = response.payload.get("listener_closed_event_hash");
  return {
    wasListening: wasV.value,
    priorBindAddr: addrV.value,
    listenerClosedEventHash: hashV && hashV.type === "bytes" ? hashV.value : null,
  };
}

/** Build the payload for a `federation_status` request (M22.1).
 *  Empty payload — read-only state query. */
export function federationStatusPayload(): Map<string, Value> {
  return new Map<string, Value>();
}

/** Parsed `federation_status_response` (M22.1). */
export interface FederationStatusResult {
  /** True iff a listener is currently bound. */
  isListening: boolean;
  /** Currently bound address; empty string when not listening. */
  boundAddr: string;
  /** Count of currently-tracked peers (any state — pending, established, etc.). */
  peerCount: bigint;
  /** Total federation events ingested from peers since process start. */
  eventsReceivedTotal: bigint;
  /** Total federation events sent to peers since process start. */
  eventsSentTotal: bigint;
}

export function parseFederationStatusResponse(
  response: Message,
): FederationStatusResult {
  if (response.messageType !== MSG_TYPE.FEDERATION_STATUS_RESPONSE) {
    throw new BridgeProtocolError(
      `expected federation_status_response; got ${response.messageType}`,
    );
  }
  const isV = response.payload.get("is_listening");
  const addrV = response.payload.get("bind_addr");
  const peerV = response.payload.get("peer_count");
  const recvV = response.payload.get("events_received_total");
  const sentV = response.payload.get("events_sent_total");
  if (
    !isV || isV.type !== "bool" ||
    !addrV || addrV.type !== "string" ||
    !peerV || peerV.type !== "uint" ||
    !recvV || recvV.type !== "uint" ||
    !sentV || sentV.type !== "uint"
  ) {
    throw new BridgeProtocolError(
      "federation_status_response missing required typed fields",
    );
  }
  return {
    isListening: isV.value,
    boundAddr: addrV.value,
    peerCount: peerV.value,
    eventsReceivedTotal: recvV.value,
    eventsSentTotal: sentV.value,
  };
}

/** Build the payload for a `federation_connect_peer` request (M22.2). */
export function federationConnectPeerPayload(args: {
  remoteAddr: string;
}): Map<string, Value> {
  if (!args.remoteAddr || args.remoteAddr.length === 0) {
    throw new BridgeProtocolError(
      "federation_connect_peer: remote_addr must be non-empty",
    );
  }
  const m = new Map<string, Value>();
  m.set("remote_addr", { type: "string", value: args.remoteAddr });
  return m;
}

/** Parsed `federation_connect_peer_response` (M22.2). */
export interface FederationConnectPeerResult {
  /** One of: "pinned" | "self_connection" | "identity_drift" | "already_pinned". */
  outcome: string;
  /** Set when outcome ∈ {"pinned","identity_drift","already_pinned"}. */
  peerSubstrateId: Uint8Array | null;
  /** Echo of remote_addr (or substrate-determined string for some outcomes). */
  remoteAddr: string;
  /** Peer's reported DAG tip (only present on initial "pinned" outcome). */
  peerDagTip: Uint8Array | null;
  /** DAG hash of `federation_peer_pinned` event; present only when newly pinned. */
  peerPinnedEventHash: Uint8Array | null;
}

export function parseFederationConnectPeerResponse(
  response: Message,
): FederationConnectPeerResult {
  if (response.messageType !== MSG_TYPE.FEDERATION_CONNECT_PEER_RESPONSE) {
    throw new BridgeProtocolError(
      `expected federation_connect_peer_response; got ${response.messageType}`,
    );
  }
  const outV = response.payload.get("outcome");
  const addrV = response.payload.get("remote_addr");
  if (
    !outV || outV.type !== "string" ||
    !addrV || addrV.type !== "string"
  ) {
    throw new BridgeProtocolError(
      "federation_connect_peer_response missing required typed fields",
    );
  }
  const idV = response.payload.get("peer_substrate_id");
  const tipV = response.payload.get("peer_dag_tip");
  const hashV = response.payload.get("peer_pinned_event_hash");
  return {
    outcome: outV.value,
    peerSubstrateId: idV && idV.type === "bytes" ? idV.value : null,
    remoteAddr: addrV.value,
    peerDagTip: tipV && tipV.type === "bytes" ? tipV.value : null,
    peerPinnedEventHash: hashV && hashV.type === "bytes" ? hashV.value : null,
  };
}

/** Build the payload for a `federation_poll` request (M22.2). Empty payload. */
export function federationPollPayload(): Map<string, Value> {
  return new Map<string, Value>();
}

/** Parsed `federation_poll_response` (M22.2). */
export interface FederationPollResult {
  /** Count of inbound connections accepted this poll. */
  acceptedConnections: bigint;
  /** Count of peers newly pinned this poll (via inbound HELLO completion). */
  pinnedPeers: bigint;
  /** Count of peers rejected this poll (TOFU mismatches, frame errors). */
  rejectedPeers: bigint;
  /** Count of outbound event batches sent to peers this poll. */
  eventBatchesSent: bigint;
}

export function parseFederationPollResponse(
  response: Message,
): FederationPollResult {
  if (response.messageType !== MSG_TYPE.FEDERATION_POLL_RESPONSE) {
    throw new BridgeProtocolError(
      `expected federation_poll_response; got ${response.messageType}`,
    );
  }
  const acceptedV = response.payload.get("accepted_connections");
  const pinnedV = response.payload.get("pinned_peers");
  const rejectedV = response.payload.get("rejected_peers");
  const sentV = response.payload.get("event_batches_sent");
  if (
    !acceptedV || acceptedV.type !== "uint" ||
    !pinnedV || pinnedV.type !== "uint" ||
    !rejectedV || rejectedV.type !== "uint" ||
    !sentV || sentV.type !== "uint"
  ) {
    throw new BridgeProtocolError(
      "federation_poll_response missing required typed fields",
    );
  }
  return {
    acceptedConnections: acceptedV.value,
    pinnedPeers: pinnedV.value,
    rejectedPeers: rejectedV.value,
    eventBatchesSent: sentV.value,
  };
}

/** Build the payload for `federation_pull_events_from_peer` (M22.3). */
export function federationPullEventsFromPeerPayload(args: {
  peerSubstrateId: Uint8Array;
  sinceNodeHash?: Uint8Array;
  maxEvents?: bigint;
}): Map<string, Value> {
  if (args.peerSubstrateId.length !== 32) {
    throw new BridgeProtocolError(
      `peer_substrate_id must be 32 bytes; got ${args.peerSubstrateId.length}`,
    );
  }
  const m = new Map<string, Value>();
  m.set("peer_substrate_id", { type: "bytes", value: args.peerSubstrateId });
  if (args.sinceNodeHash !== undefined) {
    if (args.sinceNodeHash.length !== 32) {
      throw new BridgeProtocolError(
        `since_node_hash must be 32 bytes; got ${args.sinceNodeHash.length}`,
      );
    }
    m.set("since_node_hash", { type: "bytes", value: args.sinceNodeHash });
  }
  if (args.maxEvents !== undefined) {
    m.set("max_events", { type: "uint", value: args.maxEvents });
  }
  return m;
}

/** Parsed `federation_pull_events_from_peer_response` (M22.3). */
export interface FederationPullEventsFromPeerResult {
  /** Count of events the peer returned. */
  eventsReceivedCount: bigint;
  /** Count of events ingested into the receiver's DAG as
   *  `federation_received:{peer_prefix}` wrappers (allowlist-filtered). */
  eventsIngestedCount: bigint;
  /** True iff the peer indicated this batch completes its known events. */
  isLastBatch: boolean;
  /** DAG node hash of the `federation_events_received` marker emitted by the
   *  receiver; null if no events were ingested (allowlist may have filtered all). */
  eventsReceivedEventHash: Uint8Array | null;
}

export function parseFederationPullEventsFromPeerResponse(
  response: Message,
): FederationPullEventsFromPeerResult {
  if (response.messageType !== MSG_TYPE.FEDERATION_PULL_EVENTS_FROM_PEER_RESPONSE) {
    throw new BridgeProtocolError(
      `expected federation_pull_events_from_peer_response; got ${response.messageType}`,
    );
  }
  const recvV = response.payload.get("events_received_count");
  const ingV = response.payload.get("events_ingested_count");
  const lastV = response.payload.get("is_last_batch");
  if (
    !recvV || recvV.type !== "uint" ||
    !ingV || ingV.type !== "uint" ||
    !lastV || lastV.type !== "bool"
  ) {
    throw new BridgeProtocolError(
      "federation_pull_events_from_peer_response missing required typed fields",
    );
  }
  const hashV = response.payload.get("events_received_event_hash");
  return {
    eventsReceivedCount: recvV.value,
    eventsIngestedCount: ingV.value,
    isLastBatch: lastV.value,
    eventsReceivedEventHash:
      hashV && hashV.type === "bytes" ? hashV.value : null,
  };
}

/** Build the payload for `federation_link_to_parent_from_hint` (M22.4).
 *  Empty payload — substrate scans its own DAG for the hint event. */
export function federationLinkToParentFromHintPayload(): Map<string, Value> {
  return new Map<string, Value>();
}

// ===========================================================================
// L2/FEDERATION §6.5 — Stage-1 population-consensus floor (quorum cert).
//
// Thin operator drivers: the substrate signs its own vote + verifies peer
// signatures + mints the cert. The TS side carries no Ed25519 logic — it just
// frames the operator's intent (propose a claim / submit a peer's vote bytes /
// query a claim's status) and parses the substrate's tally.
//
// The three valid claim_type strings (§6.5.b): "peer_revocation",
// "universal_junk_classification", "cross_substrate_aggregate_metric".
// ===========================================================================

/** Build the payload for a `federation_propose_population_claim` request — mint
 *  THIS substrate's own vote over a population claim, opening a consensus round. */
export function federationProposePopulationClaimPayload(args: {
  claimType: string;
  claimPayload: Uint8Array;
}): Map<string, Value> {
  if (!args.claimType || args.claimType.length === 0) {
    throw new BridgeProtocolError(
      "federation_propose_population_claim: claim_type must be non-empty",
    );
  }
  const m = new Map<string, Value>();
  m.set("claim_type", { type: "string", value: args.claimType });
  m.set("claim_payload", { type: "bytes", value: args.claimPayload });
  return m;
}

/** Tally of a population claim (shared shape of propose/submit/query responses). */
export interface PopulationConsensusTally {
  claimType: string;
  claimHash: Uint8Array;
  roundId: bigint;
  votesReceived: bigint;
  quorumNeeded: bigint;
  peerSetSizeN: bigint;
  /** DAG hash of the `population_consensus_reached` cert; null until quorum. */
  consensusReachedEventHash: Uint8Array | null;
}

function tallyCommon(
  payload: Map<string, Value>,
): Omit<PopulationConsensusTally, "claimType"> & { claimType: string | null } {
  const ctV = payload.get("claim_type");
  const chV = payload.get("claim_hash");
  const ridV = payload.get("round_id");
  const vrV = payload.get("votes_received");
  const qnV = payload.get("quorum_needed");
  const nV = payload.get("peer_set_size_n");
  if (
    !chV || chV.type !== "bytes" ||
    !ridV || ridV.type !== "uint" ||
    !vrV || vrV.type !== "uint" ||
    !qnV || qnV.type !== "uint" ||
    !nV || nV.type !== "uint"
  ) {
    throw new BridgeProtocolError(
      "population-consensus response missing required typed tally fields",
    );
  }
  const certV = payload.get("consensus_reached_event_hash");
  return {
    claimType: ctV && ctV.type === "string" ? ctV.value : null,
    claimHash: chV.value,
    roundId: ridV.value,
    votesReceived: vrV.value,
    quorumNeeded: qnV.value,
    peerSetSizeN: nV.value,
    consensusReachedEventHash: certV && certV.type === "bytes" ? certV.value : null,
  };
}

export function parseFederationProposePopulationClaimResponse(
  response: Message,
): PopulationConsensusTally {
  if (response.messageType !== MSG_TYPE.FEDERATION_PROPOSE_POPULATION_CLAIM_RESPONSE) {
    throw new BridgeProtocolError(
      `expected federation_propose_population_claim_response; got ${response.messageType}`,
    );
  }
  const t = tallyCommon(response.payload);
  return { ...t, claimType: t.claimType ?? "" };
}

/** Build the payload for a `federation_submit_peer_vote` request — ingest a
 *  peer's vote (the canonical `population_vote` body bytes, as pulled over
 *  FED_EVENT_BATCH). The substrate verifies the embedded signature. */
export function federationSubmitPeerVotePayload(args: {
  voteEventBytes: Uint8Array;
}): Map<string, Value> {
  if (args.voteEventBytes.length === 0) {
    throw new BridgeProtocolError(
      "federation_submit_peer_vote: vote_event_bytes must be non-empty",
    );
  }
  const m = new Map<string, Value>();
  m.set("vote_event_bytes", { type: "bytes", value: args.voteEventBytes });
  return m;
}

/** Parsed `federation_submit_peer_vote_response`. */
export interface FederationSubmitPeerVoteResult {
  /** True iff the vote verified + was recorded; false carries `reason`. */
  accepted: boolean;
  /** Rejection reason when accepted=false. */
  reason: string | null;
  /** Tally after this vote (present only when accepted=true). */
  tally: PopulationConsensusTally | null;
}

export function parseFederationSubmitPeerVoteResponse(
  response: Message,
): FederationSubmitPeerVoteResult {
  if (response.messageType !== MSG_TYPE.FEDERATION_SUBMIT_PEER_VOTE_RESPONSE) {
    throw new BridgeProtocolError(
      `expected federation_submit_peer_vote_response; got ${response.messageType}`,
    );
  }
  const accV = response.payload.get("accepted");
  if (!accV || accV.type !== "bool") {
    throw new BridgeProtocolError(
      "federation_submit_peer_vote_response missing accepted:bool",
    );
  }
  if (!accV.value) {
    const reasonV = response.payload.get("reason");
    return {
      accepted: false,
      reason: reasonV && reasonV.type === "string" ? reasonV.value : null,
      tally: null,
    };
  }
  const t = tallyCommon(response.payload);
  return {
    accepted: true,
    reason: null,
    tally: { ...t, claimType: t.claimType ?? "" },
  };
}

/** Build the payload for a `federation_query_consensus` request. */
export function federationQueryConsensusPayload(args: {
  claimType: string;
  claimPayload: Uint8Array;
}): Map<string, Value> {
  if (!args.claimType || args.claimType.length === 0) {
    throw new BridgeProtocolError(
      "federation_query_consensus: claim_type must be non-empty",
    );
  }
  const m = new Map<string, Value>();
  m.set("claim_type", { type: "string", value: args.claimType });
  m.set("claim_payload", { type: "bytes", value: args.claimPayload });
  return m;
}

/** Parsed `federation_query_consensus_response`. */
export interface FederationQueryConsensusResult {
  /** "reached" | "pending" | "stuck". */
  status: string;
  tally: PopulationConsensusTally;
}

export function parseFederationQueryConsensusResponse(
  response: Message,
): FederationQueryConsensusResult {
  if (response.messageType !== MSG_TYPE.FEDERATION_QUERY_CONSENSUS_RESPONSE) {
    throw new BridgeProtocolError(
      `expected federation_query_consensus_response; got ${response.messageType}`,
    );
  }
  const statusV = response.payload.get("status");
  if (!statusV || statusV.type !== "string") {
    throw new BridgeProtocolError(
      "federation_query_consensus_response missing status:string",
    );
  }
  const t = tallyCommon(response.payload);
  return {
    status: statusV.value,
    tally: { ...t, claimType: t.claimType ?? "" },
  };
}

/** Parsed `federation_link_to_parent_from_hint_response` (M22.4). */
export interface FederationLinkToParentFromHintResult {
  /** True iff a parent_federation_hint event was found in the DAG. */
  hintFound: boolean;
  /** True iff a federation_parent_linked event already existed (idempotent). */
  alreadyLinked: boolean;
  /** Present when hintFound=true. */
  parentSubstrateId: Uint8Array | null;
  /** Present when hintFound=true. */
  parentFederationAddr: string | null;
  /** Present when a new federation_parent_linked event was emitted. */
  parentLinkedEventHash: Uint8Array | null;
  /** Present when hintFound=true but connect failed
   *  (values: "self_connection" | "identity_drift" | "already_pinned" | "unknown"). */
  connectOutcome: string | null;
}

export function parseFederationLinkToParentFromHintResponse(
  response: Message,
): FederationLinkToParentFromHintResult {
  if (response.messageType !== MSG_TYPE.FEDERATION_LINK_TO_PARENT_FROM_HINT_RESPONSE) {
    throw new BridgeProtocolError(
      `expected federation_link_to_parent_from_hint_response; got ${response.messageType}`,
    );
  }
  const foundV = response.payload.get("hint_found");
  const linkedV = response.payload.get("already_linked");
  if (
    !foundV || foundV.type !== "bool" ||
    !linkedV || linkedV.type !== "bool"
  ) {
    throw new BridgeProtocolError(
      "federation_link_to_parent_from_hint_response missing required typed fields",
    );
  }
  const idV = response.payload.get("parent_substrate_id");
  const addrV = response.payload.get("parent_federation_addr");
  const hashV = response.payload.get("parent_linked_event_hash");
  const outV = response.payload.get("connect_outcome");
  return {
    hintFound: foundV.value,
    alreadyLinked: linkedV.value,
    parentSubstrateId: idV && idV.type === "bytes" ? idV.value : null,
    parentFederationAddr: addrV && addrV.type === "string" ? addrV.value : null,
    parentLinkedEventHash: hashV && hashV.type === "bytes" ? hashV.value : null,
    connectOutcome: outV && outV.type === "string" ? outV.value : null,
  };
}
