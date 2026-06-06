// SubstrateClient — spawn the myco-substrate binary and drive the M6 protocol.
//
// This is the operator runtime's view of the substrate: from here we issue
// register_axis / perturb / advance / snapshot calls, and underneath the
// substrate transparently fans them out to its Python kernel/tropism worker.
//
// Usage:
//
// ```ts
//   const client = await SubstrateClient.spawn({});
//   await client.registerAxis({...});
//   await client.perturb('curiosity', 1.5);
//   const report = await client.advance(1n);
//   await client.shutdown();
// ```

import { spawn, type ChildProcess } from "node:child_process";
import { randomBytes } from "node:crypto";

import { encodeFrame, FrameReader } from "./protocol/framing.ts";
import { bytesToHex as _toHex } from "./hex.ts";
import {
  acceptSelfEuthanasiaProposalPayload,
  type AcceptSelfEuthanasiaProposalResult,
  advancePayload,
  type AdvanceReport,
  BOOTSTRAP_KEY,
  computeIntentPayload,
  type DagEnumerationReport,
  decodeFrameBody,
  depositForgedUnderstandingPayload,
  type DepositForgedUnderstandingResult,
  emptyPayload,
  encodeFrameBody,
  enumerateDagSincePayload,
  federationCloseListenerPayload,
  type FederationCloseListenerResult,
  federationConnectPeerPayload,
  type FederationConnectPeerResult,
  federationLinkToParentFromHintPayload,
  type FederationLinkToParentFromHintResult,
  federationOpenListenerPayload,
  type FederationOpenListenerResult,
  federationPollPayload,
  type FederationPollResult,
  federationProposePopulationClaimPayload,
  federationPullEventsFromPeerPayload,
  type FederationPullEventsFromPeerResult,
  federationQueryConsensusPayload,
  type FederationQueryConsensusResult,
  federationStatusPayload,
  type FederationStatusResult,
  federationSubmitPeerVotePayload,
  type FederationSubmitPeerVoteResult,
  type PopulationConsensusTally,
  type HelloAck,
  helloPayload,
  type ImmuneCheckReport,
  type ImmuneEventsReport,
  type IngestResult,
  ingestRawMaterialPayload,
  type IntentReport,
  liftBirthPeriodQuarantinePayload,
  type LiftBirthPeriodQuarantineResult,
  type Message,
  type MigrationPendingReport,
  MSG_TYPE,
  type MutationResult,
  type ObservatorySnapshot,
  parseQueryMigrationPendingResponse,
  parseAcceptSelfEuthanasiaProposalResponse,
  parseAdvanceResponse,
  parseComputeIntentResponse,
  parseDepositForgedUnderstandingResponse,
  parseEnumerateDagSinceResponse,
  parseFederationCloseListenerResponse,
  parseFederationConnectPeerResponse,
  parseFederationLinkToParentFromHintResponse,
  parseFederationOpenListenerResponse,
  parseFederationPollResponse,
  parseFederationProposePopulationClaimResponse,
  parseFederationPullEventsFromPeerResponse,
  parseFederationQueryConsensusResponse,
  parseFederationStatusResponse,
  parseFederationSubmitPeerVoteResponse,
  parseHelloAck,
  parseIngestRawMaterialResponse,
  parseLiftBirthPeriodQuarantineResponse,
  parsePerturbAxisFromRawMaterialResponse,
  parseQueryImmuneEventsResponse,
  parseQuerySubstrateObservatoryResponse,
  parseQueryRecentNodesResponse,
  parseReadNodeByHashResponse,
  parseListPlatesResponse,
  parseRunImmuneCheckResponse,
  parseSnapshotResponse,
  parseSubmitMutationResponse,
  parseSproutChildResponse,
  perturbAxisFromRawMaterialPayload,
  perturbPayload,
  type PerturbFromRawResult,
  queryImmuneEventsPayload,
  queryRecentNodesPayload,
  querySubstrateObservatoryPayload,
  type RawMaterialKind,
  type RecentNodesReport,
  type RecentDagNode,
  type PlateIndexReport,
  registerAxisPayload,
  sproutChildPayload,
  type SproutChildResult,
  submitMutationPayload,
  buildSpawnCosignCanonicalBytes,
} from "./protocol/messages.ts";

/** Configuration for spawning a SubstrateClient. */
export interface SubstrateClientConfig {
  /** Absolute path or PATH-resolvable name for the myco-substrate binary.
   * Defaults to "myco-substrate" (PATH resolution). For local development,
   * use `target/debug/myco-substrate` (cargo) or set `MYCO_SUBSTRATE_BIN`. */
  substrateBinary?: string;
  /** Optional environment-variable overrides for the spawned process. */
  env?: Record<string, string>;
  /** Pre-seeded 32-byte session secret. Random by default. */
  sessionSecret?: Uint8Array;
  /** Per-request response timeout in milliseconds. If the substrate writes no
   *  response frame for a request within this window, the awaiting promise
   *  rejects with a {@link SubstrateTimeoutError} and the waiter is evicted.
   *  Defaults to {@link DEFAULT_REQUEST_TIMEOUT_MS} (60_000). This is a
   *  liveness guard against a hung peer — real ops finish well under it. */
  requestTimeoutMs?: number;
}

/** Default per-request response timeout for substrate ops (60s). Generous —
 *  real register/perturb/advance/snapshot round-trips finish in well under a
 *  second; this only fires when the substrate truly hangs. */
export const DEFAULT_REQUEST_TIMEOUT_MS = 60_000;

/** Error thrown by SubstrateClient operations. */
export class SubstrateClientError extends Error {
  constructor(message: string) {
    super(`substrate client: ${message}`);
    this.name = "SubstrateClientError";
  }
}

/** Thrown when a request's response does not arrive within the configured
 *  timeout. Extends {@link SubstrateClientError} so existing `instanceof
 *  SubstrateClientError` handling (and the fatal-error fan-out) treats it as a
 *  substrate failure; the distinct subtype lets callers detect the timeout
 *  specifically. */
export class SubstrateTimeoutError extends SubstrateClientError {
  constructor(messageType: string, elapsedMs: number) {
    super(
      `request '${messageType}' timed out after ${elapsedMs}ms (no response frame)`,
    );
    this.name = "SubstrateTimeoutError";
  }
}

/**
 * SubstrateClient drives the 3-tier process tree:
 *
 * ```
 *   THIS CLIENT  →  myco-substrate (Rust)  →  python -m myco_kernel_bridge
 * ```
 */
export class SubstrateClient {
  private child: ChildProcess;
  private sessionSecret: Uint8Array;
  private nextRequestId: bigint;
  private reader: FrameReader;
  /** Per-request response waiters. Keyed by request_id. Each carries its
   *  own timeout timer so a hung substrate can never deadlock the caller;
   *  the timer is always cleared when the waiter settles (resolve / reject /
   *  fail-all), so no timer leaks to hold the event loop open. */
  private pendingResponses: Map<
    bigint,
    {
      resolve: (msg: Message) => void;
      reject: (err: Error) => void;
      timer: ReturnType<typeof setTimeout>;
    }
  >;
  /** Per-request response timeout (ms). See SubstrateClientConfig. */
  private requestTimeoutMs: number;
  /** Pending fatal error to surface to all waiters on next op. */
  private fatalError: Error | null;
  /** Resolved hello_ack info. */
  helloAck: HelloAck;

  private constructor(
    child: ChildProcess,
    sessionSecret: Uint8Array,
    requestTimeoutMs: number,
  ) {
    this.child = child;
    this.sessionSecret = sessionSecret;
    this.requestTimeoutMs = requestTimeoutMs;
    this.nextRequestId = 1n;
    this.reader = new FrameReader();
    this.pendingResponses = new Map();
    this.fatalError = null;
    this.helloAck = {
      kernelTropismVersion: "",
      pythonVersion: "",
      substrateVersion: "",
    };
  }

  /** Spawn the substrate binary and complete the hello handshake. */
  static async spawn(
    config: SubstrateClientConfig,
  ): Promise<SubstrateClient> {
    const binary =
      config.substrateBinary ??
      process.env.MYCO_SUBSTRATE_BIN ??
      "myco-substrate";
    const sessionSecret =
      config.sessionSecret ?? new Uint8Array(randomBytes(32));
    if (sessionSecret.length !== 32) {
      throw new SubstrateClientError(
        `session_secret must be 32 bytes; got ${sessionSecret.length}`,
      );
    }

    // **v0.9 keyless handshake** (owner-key removal). The M9/M-anchor owner
    // Ed25519 identity, the signed-hello TOFU pinning, and the M-anchor-2
    // birth-attestation injection were all removed with the anchor surface.
    // `substrate/src/handshake.rs::handle_hello` now completes the handshake on
    // a well-formed 32-byte `session_secret` alone (no operator pubkey, no
    // hello signature, no TOFU pin) and ignores any identity fields. Fresh
    // substrates self-mint their substrate_id at genesis; no env injection.
    const child = spawn(binary, [], {
      stdio: ["pipe", "pipe", "inherit"],
      env: { ...process.env, ...config.env },
    });

    const client = new SubstrateClient(
      child,
      sessionSecret,
      config.requestTimeoutMs ?? DEFAULT_REQUEST_TIMEOUT_MS,
    );
    client._wireStreams();

    // Send the keyless hello using BOOTSTRAP_KEY; await hello_ack (subsequent
    // frames are HMAC'd with the exchanged session_secret).
    const requestId = client._allocateRequestId();
    const helloMsg: Message = {
      version: 1n,
      messageType: MSG_TYPE.HELLO,
      requestId,
      payload: helloPayload(sessionSecret),
    };
    const helloFrame = encodeFrameBody(helloMsg, BOOTSTRAP_KEY);
    const waitForAck = client._registerWaiter(requestId, MSG_TYPE.HELLO);
    client._writeFrame(helloFrame);
    const response = await waitForAck;
    client.helloAck = parseHelloAck(response);
    return client;
  }

  private _wireStreams(): void {
    const stdout = this.child.stdout;
    if (!stdout) {
      throw new SubstrateClientError("child stdout not piped");
    }
    stdout.on("data", (chunk: Buffer) => {
      this.reader.push(new Uint8Array(chunk));
      try {
        while (true) {
          const frame = this.reader.tryReadFrame();
          if (!frame) break;
          try {
            const msg = decodeFrameBody(frame, this.sessionSecret);
            this._routeIncoming(msg);
          } catch (e) {
            this._failAll(
              e instanceof Error ? e : new Error(String(e)),
            );
            return;
          }
        }
      } catch (e) {
        this._failAll(e instanceof Error ? e : new Error(String(e)));
      }
    });
    stdout.on("close", () => {
      this._failAll(
        new SubstrateClientError("child stdout closed unexpectedly"),
      );
    });
    this.child.on("exit", (code) => {
      if (this.pendingResponses.size > 0) {
        this._failAll(
          new SubstrateClientError(
            `child exited with code ${code} while requests pending`,
          ),
        );
      }
    });
    this.child.on("error", (err) => {
      this._failAll(
        new SubstrateClientError(`child error: ${err.message}`),
      );
    });
  }

  private _allocateRequestId(): bigint {
    const id = this.nextRequestId;
    this.nextRequestId = this.nextRequestId + 1n;
    return id;
  }

  private _registerWaiter(
    requestId: bigint,
    messageType: string,
  ): Promise<Message> {
    return new Promise<Message>((resolve, reject) => {
      const startedAt = Date.now();
      // Liveness guard: if no response frame arrives within requestTimeoutMs,
      // evict this waiter and reject. The substrate serializes in practice,
      // but a hung peer (frame written, never answered) would otherwise leave
      // the caller awaiting forever. `.unref()` ensures a still-armed timer
      // never keeps the Node event loop (or a `node --test` run) alive — and
      // we always clear it via _settleWaiter the moment the waiter settles.
      const timer = setTimeout(() => {
        const waiter = this.pendingResponses.get(requestId);
        if (!waiter) return; // already settled; nothing to do.
        this.pendingResponses.delete(requestId);
        waiter.reject(
          new SubstrateTimeoutError(messageType, Date.now() - startedAt),
        );
      }, this.requestTimeoutMs);
      // Do not hold the process open solely for a pending response timer.
      timer.unref?.();
      this.pendingResponses.set(requestId, { resolve, reject, timer });
    });
  }

  /** Remove a waiter from the pending map AND clear its timeout timer.
   *  Single choke-point so no settle path leaks a timer. Returns the waiter
   *  (or undefined if already settled). */
  private _settleWaiter(
    requestId: bigint,
  ):
    | { resolve: (msg: Message) => void; reject: (err: Error) => void }
    | undefined {
    const waiter = this.pendingResponses.get(requestId);
    if (!waiter) return undefined;
    clearTimeout(waiter.timer);
    this.pendingResponses.delete(requestId);
    return waiter;
  }

  private _routeIncoming(msg: Message): void {
    if (msg.messageType === MSG_TYPE.ERROR) {
      // Error envelope: surface to whichever request is awaiting (or the first one).
      const code = (msg.payload.get("code") as { type: "string"; value: string } | undefined)?.value ?? "unknown";
      const text = (msg.payload.get("message") as { type: "string"; value: string } | undefined)?.value ?? "(no message)";
      const inResponseTo = msg.payload.get("in_response_to");
      const target =
        inResponseTo && inResponseTo.type === "uint"
          ? inResponseTo.value
          : msg.requestId;
      const waiter = this._settleWaiter(target);
      if (waiter) {
        waiter.reject(
          new SubstrateClientError(`worker error: code=${code} message=${text}`),
        );
      } else {
        // No specific waiter — fail all.
        this._failAll(
          new SubstrateClientError(
            `unsolicited worker error: code=${code} message=${text}`,
          ),
        );
      }
      return;
    }
    const waiter = this._settleWaiter(msg.requestId);
    if (!waiter) {
      this._failAll(
        new SubstrateClientError(
          `received response for unknown request_id ${msg.requestId}`,
        ),
      );
      return;
    }
    waiter.resolve(msg);
  }

  private _failAll(err: Error): void {
    this.fatalError = err;
    for (const [, waiter] of this.pendingResponses) {
      clearTimeout(waiter.timer);
      waiter.reject(err);
    }
    this.pendingResponses.clear();
  }

  private _writeFrame(frameBody: Uint8Array): void {
    if (this.fatalError) throw this.fatalError;
    const stdin = this.child.stdin;
    if (!stdin) {
      throw new SubstrateClientError("child stdin not piped");
    }
    const wireFrame = encodeFrame(frameBody);
    if (!stdin.write(wireFrame)) {
      // Backpressure — for M6 minimum, we ignore; node buffers.
    }
  }

  private async _sendRequest(
    messageType: string,
    payload: Map<
      string,
      import("./canonical/canonical_bytes.ts").Value
    >,
  ): Promise<Message> {
    if (this.fatalError) throw this.fatalError;
    const requestId = this._allocateRequestId();
    const msg: Message = {
      version: 1n,
      messageType,
      requestId,
      payload,
    };
    const frame = encodeFrameBody(msg, this.sessionSecret);
    const waiter = this._registerWaiter(requestId, messageType);
    this._writeFrame(frame);
    return waiter;
  }

  // -------------------------------------------------------------------------
  // Public API.
  // -------------------------------------------------------------------------

  /** Register a gradient axis on the Python worker (via the substrate). */
  async registerAxis(args: {
    name: string;
    axisClass: "appetite" | "decay";
    fruitingThreshold: number;
    initialValue: number;
    decayRatePerCycle: number;
    isMortalitySignal: boolean;
    updateRuleKind: "noop" | "decay";
  }): Promise<void> {
    const response = await this._sendRequest(
      MSG_TYPE.REGISTER_AXIS,
      registerAxisPayload(args),
    );
    if (response.messageType !== MSG_TYPE.REGISTER_AXIS_ACK) {
      throw new SubstrateClientError(
        `expected register_axis_ack; got ${response.messageType}`,
      );
    }
  }

  /** Perturb a gradient axis. */
  async perturb(axisName: string, delta: number): Promise<void> {
    const response = await this._sendRequest(
      MSG_TYPE.PERTURB,
      perturbPayload(axisName, delta),
    );
    if (response.messageType !== MSG_TYPE.PERTURB_ACK) {
      throw new SubstrateClientError(
        `expected perturb_ack; got ${response.messageType}`,
      );
    }
  }

  /** Run one metabolic cycle. Returns sporocarp report. */
  async advance(currentCycle: bigint): Promise<AdvanceReport> {
    const response = await this._sendRequest(
      MSG_TYPE.ADVANCE,
      advancePayload(currentCycle),
    );
    return parseAdvanceResponse(response);
  }

  /** Snapshot all axis values. */
  async snapshot(): Promise<Map<string, number>> {
    const response = await this._sendRequest(
      MSG_TYPE.SNAPSHOT,
      emptyPayload(),
    );
    return parseSnapshotResponse(response);
  }

  /** M8: Query the substrate's recent DAG nodes (causal history diagnostic).
   *
   *  M16: optional `nodeTypePrefix` filter — return only nodes whose node_type
   *  starts with the prefix. Useful filters:
   *  - `"raw_material:"` — ingested raw material (M16)
   *  - `"mutation:"` — accepted classified mutations (M10)
   *  - `"immune:"` — immune sporocarps (M11+)
   *  - `"sporocarp:"` — gradient-axis sporocarps (M8)
   *  - `"perturb_from_raw:"` — causal-link nodes (M16)
   */
  async queryRecentNodes(
    count: bigint = 50n,
    nodeTypePrefix?: string,
  ): Promise<RecentNodesReport> {
    const response = await this._sendRequest(
      MSG_TYPE.QUERY_RECENT_NODES,
      queryRecentNodesPayload(count, nodeTypePrefix),
    );
    return parseQueryRecentNodesResponse(response);
  }

  /** Recall by hash (amplifier step 2) — fetch ONE DAG node by its 32-byte hash,
   *  O(1) via the substrate's `dag.get`, reaching ANY node (NOT window-bounded).
   *  Returns the node, or null if it does not exist. This is what lets the pilot
   *  stand on a forged_understanding plate older than the recent window. */
  async readNodeByHash(hash: Uint8Array): Promise<RecentDagNode | null> {
    const payload = new Map<
      string,
      import("./canonical/canonical_bytes.ts").Value
    >();
    payload.set("node_hash", { type: "bytes", value: hash });
    const response = await this._sendRequest(MSG_TYPE.READ_NODE_BY_HASH, payload);
    return parseReadNodeByHashResponse(response);
  }

  /** The pilot's compact "what I know" map (amplifier step 2) — every LIVE
   *  (non-superseded) forged_understanding plate as (label, value, hash), sorted by
   *  value. The pilot reads the whole map, judges relevance with its own cognition,
   *  then fetches the chosen plates' full content with readNodeByHash. */
  async listPlates(): Promise<PlateIndexReport> {
    const payload = new Map<
      string,
      import("./canonical/canonical_bytes.ts").Value
    >();
    const response = await this._sendRequest(MSG_TYPE.LIST_PLATES, payload);
    return parseListPlatesResponse(response);
  }

  /** M16: P2 永恒吞噬 — Ingest a raw material payload. The substrate stores
   *  it as a `raw_material:{kind}` DAG node, hashing the full (kind, bytes,
   *  source_uri, meta) tuple as canonical bytes. Max 1 MiB per call.
   *
   *  This activates the L0 P2 "no filter on intake" principle: any bytes the
   *  operator can present become first-class substrate content. Downstream
   *  use: call `perturbAxisFromRawMaterial` to causally link gradient changes
   *  to the ingested material.
   */
  async ingestRawMaterial(args: {
    contentKind: RawMaterialKind;
    contentBytes: Uint8Array;
    sourceUri?: string;
    meta?: Map<string, import("./canonical/canonical_bytes.ts").Value>;
  }): Promise<IngestResult> {
    const response = await this._sendRequest(
      MSG_TYPE.INGEST_RAW_MATERIAL,
      ingestRawMaterialPayload(args),
    );
    return parseIngestRawMaterialResponse(response);
  }

  /** The "use-forges" forging loop (P2 永恒吞噬 + P6 永恒因果) — deposit the
   *  agent's DIGESTED understanding (prose/knowledge it forged out of
   *  raw_material) as a `forged_understanding:{label}` DAG node. The substrate
   *  hashes the full (label, understanding, source_raw_material_hashes,
   *  forged_at_cycle) tuple as canonical bytes and parents the node by BOTH the
   *  prior tip AND each source raw_material node it was forged from. Max 512 KiB
   *  on `understanding`.
   *
   *  Where `ingestRawMaterial` stores UNDIGESTED intake, this stores the
   *  digested output of the agent's forging. `sourceRawMaterialHashes` MAY be
   *  empty; when present, each must reference a `raw_material:*` node (the
   *  substrate rejects an unknown / wrong-typed source). General — NOT tied to a
   *  gradient axis.
   */
  async depositForgedUnderstanding(args: {
    label: string;
    understanding: Uint8Array;
    sourceRawMaterialHashes?: Uint8Array[];
    /** Step-1 discernment: pilot-assigned importance 0..=100 (recall ranks by it). */
    value?: number;
    /** Step-1 discernment: pilot's confidence in this plate 0..=100. */
    confidence?: number;
    /** Step-1 maturation: prior forged_understanding plate hashes this one supersedes. */
    supersedes?: Uint8Array[];
  }): Promise<DepositForgedUnderstandingResult> {
    const response = await this._sendRequest(
      MSG_TYPE.DEPOSIT_FORGED_UNDERSTANDING,
      depositForgedUnderstandingPayload(args),
    );
    return parseDepositForgedUnderstandingResponse(response);
  }

  /** M24.2: query the substrate's substrate_id by inspecting its genesis_event.
   *
   *  Returns the 32-byte substrate_id stored in the genesis_event DAG node's
   *  content_canonical_bytes Map. Throws if the substrate has no genesis_event
   *  (pre-M21 legacy substrate or fresh-state-dir before first hello).
   *
   *  Used by M24.2 REVEAL substrate_id binding: TS-side reveal_key_binding
   *  signing input includes substrate_id to prevent cross-substrate replay.
   */
  async querySubstrateId(): Promise<Uint8Array> {
    const recent = await this.queryRecentNodes(50n, "genesis_event:");
    if (recent.nodes.length === 0) {
      throw new Error(
        "querySubstrateId: no genesis_event found in substrate's DAG (pre-M21 legacy or empty state)",
      );
    }
    // Genesis is the first DAG node (insertion order); newest-first traversal
    // means it's the LAST in `nodes` array.
    const genesis = recent.nodes[recent.nodes.length - 1]!;
    const { decode } = await import("./canonical/renderer.ts");
    const { CanonicalBytes } = await import(
      "./canonical/canonical_bytes.ts"
    );
    const decoded = decode(new CanonicalBytes(genesis.contentCanonicalBytes));
    if (decoded.type !== "map") {
      throw new Error("genesis_event content is not a Map");
    }
    const idValue = decoded.value.get("substrate_id");
    if (!idValue || idValue.type !== "bytes") {
      throw new Error("genesis_event content missing substrate_id bytes");
    }
    if (idValue.value.length !== 32) {
      throw new Error(
        `substrate_id has wrong length: ${idValue.value.length} (expected 32)`,
      );
    }
    return idValue.value;
  }

  /** M20 + **P08 §3.5 / §5.1** — Sprout a child substrate (KEYLESS v0.9).
   *
   *  A child spawn is still a CI-class doctrine event: the substrate REQUIRES a
   *  well-formed `myco-spawn-cosign-v1` envelope (parent replay-guard +
   *  I7(a) spore-schema binding + §16.B anchor-clock rate throttle) or it
   *  refuses with C68. The owner-key removal dropped ONLY the Ed25519
   *  co-signature gate (reproduction.rs gate 5) — the envelope STRUCTURE is
   *  still decoded + checked, so this builds + sends it, just without a
   *  signature.
   *
   *  Steps:
   *  1. **querySubstrateId** — read the parent's substrate_id (binds the
   *     envelope to THIS parent → substrate-side replay guard).
   *  2. Compute `spore_schema_hash = blake3(sporeSchemaCanonicalBytes)`
   *     (raw BLAKE3 — matches the substrate's I7(a) check exactly).
   *  3. Stamp the envelope's `anchor_timestamp_unix_ns` with the local wall
   *     clock + a fresh random nonce (no anchor process to consult; the
   *     §16.B throttle only needs a STRICTLY-increasing stamp vs prior spawns).
   *  4. Build the `myco-spawn-cosign-v1` envelope and send it (no signature).
   *     The substrate mints the §5.6 deterministic child-id, builds the child
   *     DAG, and emits `genesis_attested:{child_prefix}` (I7-closure).
   *
   *  The parent's causal DAG is NOT transferred (child starts its own causal
   *  history). Rejects if `childStateDir` already contains a dag.cb / manifest.cb.
   *
   *  `childGenesisTimestampUnixNs` defaults to the local wall clock. `depthOverride`
   *  defaults to false (the §16.A lineage-depth cap is enforced); set true to
   *  permit a spawn past the cap for THIS child.
   */
  async sproutChild(args: {
    childStateDir: string;
    /** The child's spore-schema canonical bytes (the 7-field L1/SCHEMA §3.1
     *  shape). Assembled by the caller (mcp_server) from the parent's current
     *  schema. blake3 of these bytes is bound as the spore_schema_hash. */
    sporeSchemaCanonicalBytes: Uint8Array;
    /** Optional explicit child genesis timestamp (unix ns). Defaults to the
     *  local wall clock. */
    childGenesisTimestampUnixNs?: bigint;
    /** Optional cultivator depth-override for this spawn (§16.A / F22).
     *  Default false. */
    depthOverride?: boolean;
    spore_metadata?: Map<string, import("./canonical/canonical_bytes.ts").Value>;
  }): Promise<SproutChildResult> {
    // 1. Parent substrate_id (replay guard).
    const parentSubstrateId = await this.querySubstrateId();

    // 2. Spore-schema hash (raw BLAKE3 — matches substrate I7(a)).
    const { blake3 } = await import("@noble/hashes/blake3.js");
    const sporeSchemaHash = blake3(args.sporeSchemaCanonicalBytes);

    // 3. Keyless: local wall-clock anchor timestamp + a fresh random nonce.
    //    (No anchor process in v0.9; the §16.B rate gate only needs the
    //    anchor_timestamp to be STRICTLY later than the prior spawn's.)
    const anchorTimestampUnixNs = BigInt(Date.now()) * 1_000_000n;
    const anchorNonce = new Uint8Array(randomBytes(32));
    const childGenesisTimestampUnixNs =
      args.childGenesisTimestampUnixNs ?? anchorTimestampUnixNs;

    // 4. Build the spawn-cosign envelope (no signature — keyless v0.9).
    const envelope = buildSpawnCosignCanonicalBytes({
      parentSubstrateId,
      sporeSchemaHash,
      childGenesisTimestampUnixNs,
      anchorTimestampUnixNs,
      anchorNonce,
      depthOverride: args.depthOverride ?? false,
    });

    // 5. Send. The substrate decodes the envelope (C68 on malformed/replayed),
    //    mints the child-id + emits genesis_attested. No signature is checked.
    const response = await this._sendRequest(
      MSG_TYPE.SPROUT_CHILD,
      sproutChildPayload({
        childStateDir: args.childStateDir,
        spawnCosignEnvelope: envelope,
        sporeSchemaCanonicalBytes: args.sporeSchemaCanonicalBytes,
        spore_metadata: args.spore_metadata,
      }),
    );
    return parseSproutChildResponse(response);
  }

  /** M16: P2 永恒吞噬 + P6 永恒因果 — Perturb an axis with causal linkage to
   *  a previously-ingested raw_material node. The substrate inserts a
   *  `perturb_from_raw:{axis}` DAG node parented by BOTH prior tip AND the
   *  referenced raw_material — making the gradient change traceable to its
   *  environmental source.
   *
   *  Rejects if `rawMaterialHash` is unknown OR doesn't reference a
   *  `raw_material:*` node.
   */
  async perturbAxisFromRawMaterial(args: {
    axisName: string;
    delta: number;
    rawMaterialHash: Uint8Array;
  }): Promise<PerturbFromRawResult> {
    const response = await this._sendRequest(
      MSG_TYPE.PERTURB_AXIS_FROM_RAW_MATERIAL,
      perturbAxisFromRawMaterialPayload(args),
    );
    return parsePerturbAxisFromRawMaterialResponse(response);
  }

  /** M8: Compute the substrate's current intent (cluster_C over neighborhood). */
  async currentIntent(args: {
    radiusCycles?: bigint;
    pivotHash?: Uint8Array;
  } = {}): Promise<IntentReport> {
    const response = await this._sendRequest(
      MSG_TYPE.COMPUTE_INTENT,
      computeIntentPayload({
        radiusCycles: args.radiusCycles ?? 10n,
        pivotHash: args.pivotHash,
      }),
    );
    return parseComputeIntentResponse(response);
  }

  /** M10/M13/M14/M15: Submit a classified mutation.
   *
   *  Layers:
   *  - M10: Daily mutations omit signature; CI mutations include an Ed25519
   *    signature over `contentCanonicalBytes`.
   *  - M13: optional `nonce` + `expiryUnixNs` for anchor-surface envelope.
   *  - M14: optional `revealPubkey` + `identitySignatureOverRevealPubkey` for
   *    per-handshake REVEAL keypair (limits credential exposure per mutation).
   *    When REVEAL is present, `attestationSignature` is REVEAL-signed-content
   *    (not IDENTITY-signed); IDENTITY signs the REVEAL pubkey separately.
   *  - M15: optional `anchorClockSubmittedAtUnixNs` for dual-clock expiry.
   *    Required iff the nonce was issued with `anchorClockUnixNs`.
   */
  async submitMutation(args: {
    mutationType: string;
    touchedFields?: string[];
    touchedFiles?: string[];
    touchedMetaStructures?: string[];
    contentCanonicalBytes: Uint8Array;
    attestationSignature?: Uint8Array;
    nonce?: Uint8Array;
    expiryUnixNs?: bigint;
    revealPubkey?: Uint8Array;
    identitySignatureOverRevealPubkey?: Uint8Array;
    anchorClockSubmittedAtUnixNs?: bigint;
    /** v3.1.1 Sprint 8.G (P03 §10.4): opt into two-phase migration for a
     *  schema_evolution mutation. See `submitMutationPayload`. */
    migrationMode?: boolean;
  }): Promise<MutationResult> {
    const response = await this._sendRequest(
      MSG_TYPE.SUBMIT_MUTATION,
      submitMutationPayload(args),
    );
    return parseSubmitMutationResponse(response);
  }

  /** v3.1.1 Sprint 8.G (P03 §10.4): query whether a two-phase schema migration
   *  is currently in flight, and if so its op + window + current cycle. A pure
   *  read of substrate state (no DAG mutation); survives cold-resume because the
   *  candidate is hydrated from the DAG / snapshot at boot. */
  async queryMigrationPending(): Promise<MigrationPendingReport> {
    const response = await this._sendRequest(
      MSG_TYPE.QUERY_MIGRATION_PENDING,
      emptyPayload(),
    );
    return parseQueryMigrationPendingResponse(response);
  }

  // **v0.9 owner-key removal**: `submitMutationWithReveal` (M14 REVEAL-keypair
  // envelope), `cosignDagTip` (M-anchor-5 §9.2.2), `signL0Revision`
  // (§9.2.4), and `requestAttestationNonce` (M13) were REMOVED with the anchor
  // surface. The substrate no longer issues attestation nonces, no longer
  // verifies owner Ed25519 signatures on CI mutations, and no longer accepts
  // the `dag_tip_cosign` / `l0_revision_attest` mutation types. CI mutations
  // are now classified keyless by the Python classifier; submit them via
  // `submitMutation` (the attestation_signature field is optional + ignored).

  /** M15: Enumerate DAG node hashes added since `prevTip` (or all from genesis
   *  if `prevTip` undefined). Returns each node with full metadata so the
   *  owner can independently reconstruct the Merkle chain.
   *
   *  Closes L1/HARD_RULES C6 dag_enumeration_unclosed: the substrate cannot
   *  hide parallel-branch forgery, because the owner recomputes every node's
   *  hash from declared parents + content. Call `verifyEnumeration(report)`
   *  to validate the chain locally.
   *
   *  On unknown prevTip: substrate emits C6 immune sporocarp + rejects. */
  async enumerateDagSince(prevTip?: Uint8Array): Promise<DagEnumerationReport> {
    const response = await this._sendRequest(
      MSG_TYPE.ENUMERATE_DAG_SINCE,
      enumerateDagSincePayload(prevTip),
    );
    return parseEnumerateDagSinceResponse(response);
  }

  /** M15: Verify a DAG enumeration locally by recomputing each node's BLAKE3
   *  Merkle hash from (parent_hashes, content_canonical_bytes) and comparing
   *  to the substrate-claimed hash. Returns an array of error strings; empty
   *  array = the substrate's enumeration is self-consistent.
   *
   *  This is the owner-side defense against substrate hash forgery. A
   *  malicious substrate that returns a hash inconsistent with its claimed
   *  parents+content cannot survive this check.
   */
  static async verifyEnumeration(
    report: DagEnumerationReport,
  ): Promise<string[]> {
    const errors: string[] = [];
    // Reuse anchor-client's merkleHash (BLAKE3 + parent-count length prefix).
    const { merkleHash, NodeHash } = await import("./canonical/crypto.ts");
    for (let i = 0; i < report.nodes.length; i++) {
      const node = report.nodes[i]!;
      const parents = node.parentHashes.map((b) => new NodeHash(b));
      const recomputed = merkleHash(parents, node.contentCanonicalBytes);
      if (!_bytesEqual(recomputed.bytes, node.hash)) {
        errors.push(
          `node[${i}] hash mismatch: substrate claimed ${_toHex(node.hash)}, ` +
            `recomputed ${_toHex(recomputed.bytes)}`,
        );
      }
    }
    // Also check that each non-genesis node's parents appear earlier in the
    // enumeration OR are the prev_tip (for partial enumerations). This is a
    // soft check — partial enumerations may legitimately reference parents
    // outside the returned window.
    if (report.prevTip === null) {
      // Full enumeration from genesis: every parent must appear earlier.
      const seen = new Set<string>();
      for (let i = 0; i < report.nodes.length; i++) {
        const node = report.nodes[i]!;
        const hashHex = _toHex(node.hash);
        for (const p of node.parentHashes) {
          const pHex = _toHex(p);
          if (!seen.has(pHex)) {
            errors.push(
              `node[${i}] (${hashHex.substring(0, 16)}…) references unseen parent ${pHex.substring(0, 16)}…`,
            );
          }
        }
        seen.add(hashHex);
      }
    }
    return errors;
  }

  /** M11: Query recent immune events (rejected mutations, pubkey mismatches,
   *  DAG tamper detections). Filters the DAG by node_type prefix "immune:". */
  async queryImmuneEvents(count: bigint = 50n): Promise<ImmuneEventsReport> {
    const response = await this._sendRequest(
      MSG_TYPE.QUERY_IMMUNE_EVENTS,
      queryImmuneEventsPayload(count),
    );
    return parseQueryImmuneEventsResponse(response);
  }

  /** M12: Trigger an ad-hoc integrity scan. The substrate runs its
   *  C9-family checks (substrate_id well-formedness, DAG hash chain integrity,
   *  cycle counter monotonicity, pinned-pubkey well-formedness, owner_keys
   *  consistency) and emits a C9 immune sporocarp for each failure. */
  async runImmuneCheck(): Promise<ImmuneCheckReport> {
    const response = await this._sendRequest(
      MSG_TYPE.RUN_IMMUNE_CHECK,
      emptyPayload(),
    );
    return parseRunImmuneCheckResponse(response);
  }

  // -------------------------------------------------------------------------
  // M25.5 P5 万物互联 — operator-facing federation + observatory + mortality.
  // -------------------------------------------------------------------------

  /** M22.1: Open a TCP federation listener. Pass `127.0.0.1:0` to let the OS
   *  pick a port; the response carries the resolved address.
   *
   *  The substrate emits a `federation_listener_opened` DAG event on success,
   *  recording the bind address into its causal graph (P5 + P6). */
  async federationOpenListener(args: {
    bindAddr: string;
  }): Promise<FederationOpenListenerResult> {
    const response = await this._sendRequest(
      MSG_TYPE.FEDERATION_OPEN_LISTENER,
      federationOpenListenerPayload(args),
    );
    return parseFederationOpenListenerResponse(response);
  }

  /** M22.1: Close the active federation listener. Idempotent — no-op if no
   *  listener was active. When a listener was active, the substrate emits a
   *  `federation_listener_closed` DAG event. */
  async federationCloseListener(): Promise<FederationCloseListenerResult> {
    const response = await this._sendRequest(
      MSG_TYPE.FEDERATION_CLOSE_LISTENER,
      federationCloseListenerPayload(),
    );
    return parseFederationCloseListenerResponse(response);
  }

  /** M22.1: Read-only federation status query — currently bound address,
   *  peer count, cumulative event totals. */
  async federationStatus(): Promise<FederationStatusResult> {
    const response = await this._sendRequest(
      MSG_TYPE.FEDERATION_STATUS,
      federationStatusPayload(),
    );
    return parseFederationStatusResponse(response);
  }

  /** M22.2: Dial a peer substrate at `remoteAddr`, perform FED_HELLO handshake,
   *  TOFU-pin the peer's substrate_id. Outcome is one of:
   *  - `"pinned"` — first time we saw this peer; pinned successfully.
   *  - `"self_connection"` — peer's substrate_id matches our own (rejected).
   *  - `"identity_drift"` — peer's substrate_id differs from a previous pinning
   *    at the same address (C20 immune sporocarp emitted).
   *  - `"already_pinned"` — we already pinned this peer at this address. */
  async federationConnectPeer(args: {
    remoteAddr: string;
  }): Promise<FederationConnectPeerResult> {
    const response = await this._sendRequest(
      MSG_TYPE.FEDERATION_CONNECT_PEER,
      federationConnectPeerPayload(args),
    );
    return parseFederationConnectPeerResponse(response);
  }

  /** M22.2+: Drive one round of nonblocking federation I/O:
   *  1. Accept queued inbound TCP connections.
   *  2. Advance each pending peer through FED_HELLO handshake.
   *  3. Drain inbound frames (event batches) from established peers.
   *
   *  This is a poll — call it periodically (e.g. each cycle) when federation
   *  is active. M23 wires it into the substrate's autonomous tick. */
  async federationPoll(): Promise<FederationPollResult> {
    const response = await this._sendRequest(
      MSG_TYPE.FEDERATION_POLL,
      federationPollPayload(),
    );
    return parseFederationPollResponse(response);
  }

  /** M22.3: Request DAG events from a previously-pinned peer.
   *
   *  Inbound peer events pass through an ALLOWLIST (only substrate-environmental
   *  node types — raw_material/sporocarp/mutation/immune — are accepted). Each
   *  allowed event is wrapped in a `federation_received:{peer_prefix}` envelope
   *  parented by the RECEIVER's local tip; the receiver's Merkle chain stays
   *  valid. Cross-substrate provenance is preserved inside the wrapper content
   *  (peer_event_original_hash + peer_event_parent_hashes). */
  async federationPullEventsFromPeer(args: {
    peerSubstrateId: Uint8Array;
    sinceNodeHash?: Uint8Array;
    maxEvents?: bigint;
  }): Promise<FederationPullEventsFromPeerResult> {
    const response = await this._sendRequest(
      MSG_TYPE.FEDERATION_PULL_EVENTS_FROM_PEER,
      federationPullEventsFromPeerPayload(args),
    );
    return parseFederationPullEventsFromPeerResponse(response);
  }

  /** M22.4: After child substrate boot, scan local DAG for a
   *  `parent_federation_hint` event (written by the parent at `sproutChild`
   *  time when federation was active). If found, dial the parent's federation
   *  address + TOFU-pin + emit `federation_parent_linked`. Idempotent if
   *  already linked. */
  async federationLinkToParentFromHint(): Promise<FederationLinkToParentFromHintResult> {
    const response = await this._sendRequest(
      MSG_TYPE.FEDERATION_LINK_TO_PARENT_FROM_HINT,
      federationLinkToParentFromHintPayload(),
    );
    return parseFederationLinkToParentFromHintResponse(response);
  }

  /** L2/FEDERATION §6.5: Propose a population-level claim — the substrate mints
   *  its OWN vote (signed with its signing seed) and opens a consensus round.
   *  Returns the round_id + tally. Only fires consequence at ≥3 peers (the
   *  consensus floor); below that, pairwise-trust + owner-attestation governs.
   *
   *  `claimType` must be one of: "peer_revocation",
   *  "universal_junk_classification", "cross_substrate_aggregate_metric". */
  async federationProposePopulationClaim(args: {
    claimType: string;
    claimPayload: Uint8Array;
  }): Promise<PopulationConsensusTally> {
    const response = await this._sendRequest(
      MSG_TYPE.FEDERATION_PROPOSE_POPULATION_CLAIM,
      federationProposePopulationClaimPayload(args),
    );
    return parseFederationProposePopulationClaimResponse(response);
  }

  /** L2/FEDERATION §6.5: Ingest a peer's vote over a population claim (the
   *  canonical `population_vote` body bytes, as pulled over FED_EVENT_BATCH).
   *  The substrate verifies the embedded Ed25519 signature against the peer's
   *  §10 FED_HELLO-pinned `signer_pubkey`; an unpinned/tampered vote is
   *  rejected. When the tally reaches ≥2/3 quorum the substrate auto-mints the
   *  self-verifying `population_consensus_reached` certificate. */
  async federationSubmitPeerVote(args: {
    voteEventBytes: Uint8Array;
  }): Promise<FederationSubmitPeerVoteResult> {
    const response = await this._sendRequest(
      MSG_TYPE.FEDERATION_SUBMIT_PEER_VOTE,
      federationSubmitPeerVotePayload(args),
    );
    return parseFederationSubmitPeerVoteResponse(response);
  }

  /** L2/FEDERATION §6.5: Query a population claim's status —
   *  "reached" | "pending" | "stuck" — plus the current tally + (if reached)
   *  the cert event hash. */
  async federationQueryConsensus(args: {
    claimType: string;
    claimPayload: Uint8Array;
  }): Promise<FederationQueryConsensusResult> {
    const response = await this._sendRequest(
      MSG_TYPE.FEDERATION_QUERY_CONSENSUS,
      federationQueryConsensusPayload(args),
    );
    return parseFederationQueryConsensusResponse(response);
  }

  /** M22.5 (KEYLESS v0.9): lift this substrate's birth-period quarantine.
   *  The owner Ed25519 signature gate was removed with the anchor surface;
   *  `handle_lift_birth_period_quarantine` now reads NOTHING from the payload
   *  and simply emits `birth_period_quarantine_lifted` (the structural
   *  birth-period gating in `dispatch` still applies until lifted/expired).
   *
   *  Idempotent — when not in active quarantine, `wasInQuarantine=false` and
   *  no DAG event is emitted. */
  async liftBirthPeriodQuarantine(): Promise<LiftBirthPeriodQuarantineResult> {
    const response = await this._sendRequest(
      MSG_TYPE.LIFT_BIRTH_PERIOD_QUARANTINE,
      liftBirthPeriodQuarantinePayload(),
    );
    return parseLiftBirthPeriodQuarantineResponse(response);
  }

  /** M23.2 P7 必朽 (keyless v3.1.5): acceptance of a previously-emitted
   *  `self_euthanasia_proposal:{axis_name}` DAG node. The owner Ed25519
   *  co-signature was removed with the anchor layer; whole-death is now a
   *  DELIBERATE call whose only gate is that `proposalHash` point to a real
   *  proposal node. The substrate emits `self_euthanasia_executed:{axis_name}`
   *  and replies with success.
   *
   *  **The substrate gracefully shuts down AFTER this response is written.**
   *  The DAG persists on disk as the post-mortem record. The caller's
   *  `this.child` will exit cleanly (code 0) shortly after; callers typically
   *  follow this call with `shutdown()` or `_waitChildExit()`. */
  async acceptSelfEuthanasiaProposal(args: {
    proposalHash: Uint8Array;
  }): Promise<AcceptSelfEuthanasiaProposalResult> {
    const response = await this._sendRequest(
      MSG_TYPE.ACCEPT_SELF_EUTHANASIA_PROPOSAL,
      acceptSelfEuthanasiaProposalPayload(args),
    );
    return parseAcceptSelfEuthanasiaProposalResponse(response);
  }

  /** Phase α / M24.5: Read the Living Bets observatory snapshot.
   *
   *  Currently exposes (format_version=2):
   *  - signal #1: persistence budget (DAG size + cycle counter)
   *  - signal #2: evolution rate (axis_registered + evolution_* counts)
   *  - signal #3: read-pattern diversity (distinct perturbed-axis count)
   *  - signal #4: federation health (reachable peers + events received)
   *  - signal #6: read-window-relative ratio (iff caller supplies window)
   *  - signal #7: composite health score (weighted aggregate of 1+2+4b)
   *
   *  M25.x lands signal #5 (time trends) + #8 (doctrine-instability burst)
   *  + bet_weakening_quorum at format_version=3. The parser surfaces those
   *  fields when present and leaves them undefined otherwise. */
  async querySubstrateObservatory(args: {
    operatorAttestedContextWindowBytes?: bigint;
  } = {}): Promise<ObservatorySnapshot> {
    const response = await this._sendRequest(
      MSG_TYPE.QUERY_SUBSTRATE_OBSERVATORY,
      querySubstrateObservatoryPayload(args),
    );
    return parseQuerySubstrateObservatoryResponse(response);
  }

  /** Graceful shutdown — sends shutdown, awaits ack, waits for child exit.
   *  (v0.9 keyless: there is no auto-loaded operator identity / anchor-surface
   *  child to close anymore.) */
  async shutdown(): Promise<void> {
    if (this.fatalError) {
      // Still try to clean up the child.
      this._killChild();
      return;
    }
    try {
      const response = await this._sendRequest(
        MSG_TYPE.SHUTDOWN,
        emptyPayload(),
      );
      if (response.messageType !== MSG_TYPE.SHUTDOWN_ACK) {
        throw new SubstrateClientError(
          `expected shutdown_ack; got ${response.messageType}`,
        );
      }
    } catch {
      // Ignore — we'll kill the child anyway.
    }
    await this._waitChildExit();
  }

  private _waitChildExit(): Promise<void> {
    return new Promise((resolve) => {
      if (this.child.exitCode !== null) {
        resolve();
        return;
      }
      this.child.once("exit", () => resolve());
      // Safety: close stdin to signal EOF.
      try {
        this.child.stdin?.end();
      } catch {
        // Ignore.
      }
    });
  }

  private _killChild(): void {
    try {
      this.child.kill();
    } catch {
      // Ignore.
    }
  }
}

// ---------------------------------------------------------------------------
// M15: small helpers used by verifyEnumeration.
// ---------------------------------------------------------------------------

function _bytesEqual(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) return false;
  }
  return true;
}
