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
  acceptSelfEuthanasiaProposalSigningInput,
  advancePayload,
  type AdvanceReport,
  type AttestationNonceResult,
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
  helloSigningBody,
  type ImmuneCheckReport,
  type ImmuneEventsReport,
  type IngestResult,
  ingestRawMaterialPayload,
  type IntentReport,
  liftBirthPeriodQuarantinePayload,
  type LiftBirthPeriodQuarantineResult,
  liftBirthPeriodQuarantineSigningInput,
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
  parseRequestAttestationNonceResponse,
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
  registerAxisPayload,
  requestAttestationNoncePayload,
  revealKeyBindingSigningInput,
  sproutChildPayload,
  type SproutChildResult,
  submitMutationPayload,
  buildDagTipCosignCanonicalBytes,
  buildL0RevisionCanonicalBytes,
  buildSpawnCosignCanonicalBytes,
} from "./protocol/messages.ts";
import { OperatorIdentity } from "./operator_identity.ts";

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
  /** Operator identity for M9 hello signing. If omitted, loads-or-creates
   *  from ~/.myco/operator_keys/ (or $MYCO_OPERATOR_KEY_DIR). Pass an explicit
   *  OperatorIdentity for tests (isolated keypairs). */
  operatorIdentity?: OperatorIdentity;
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
  /** Identity auto-loaded by spawn() (NOT a caller-provided one). When set,
   *  shutdown() will close it; without this the anchor-surface-host child
   *  it owns would leak (its stdio pipes keep the parent alive). */
  private autoLoadedIdentity: OperatorIdentity | null;

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
    this.autoLoadedIdentity = null;
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

    // M9/M-anchor-1: load (or create) the operator identity for signing
    // the hello message. After M-anchor-1, this delegates to
    // anchor_surface_host over local TCP — the owner Ed25519 private key
    // never enters the operator process memory.
    //
    // If the caller passed an explicit identity, they OWN its lifecycle.
    // If we auto-load one, WE own its lifecycle — shutdown() must close it
    // so the anchor-surface-host child it spawned doesn't leak (its stdio
    // pipes hold the parent process alive until the child exits).
    const callerProvidedIdentity = config.operatorIdentity ?? null;
    const identity =
      callerProvidedIdentity ?? (await OperatorIdentity.loadOrCreate());
    const operatorPubkey = identity.publicKeyBytes();

    // Compute the hello signature over the canonical-bytes of {session_secret, operator_pubkey}.
    const signingInput = helloSigningBody(sessionSecret, operatorPubkey);
    const helloSignature = await identity.sign(signingInput);

    // **M-anchor-2 §9.2.1 birth attestation injection**.
    //
    // If this looks like a FRESH substrate (no MYCO_STATE_DIR override OR
    // an explicitly-empty state dir), pre-generate substrate_id +
    // genesis_time, request a birth attestation from anchor_surface_host
    // via OperatorIdentity, and pass all values to the substrate as env
    // vars. The substrate's Manifest::genesis path honors
    // MYCO_SUBSTRATE_ID_OVERRIDE_HEX + MYCO_GENESIS_TIME_OVERRIDE_UNIX_NS;
    // server.rs honors MYCO_BIRTH_ATTESTATION_* and emits the DAG event
    // right after genesis_event.
    //
    // For PRE-EXISTING substrates (state dir already has manifest.cb),
    // skipping injection is correct: the birth_attestation event is
    // already in their DAG, and substrate-side C20 verifier re-checks it
    // on every boot regardless.
    const birthAttestationEnv = await maybeBuildBirthAttestationEnv(
      identity,
      config.env?.MYCO_STATE_DIR,
    );

    const child = spawn(binary, [], {
      stdio: ["pipe", "pipe", "inherit"],
      env: { ...process.env, ...config.env, ...birthAttestationEnv },
    });

    const client = new SubstrateClient(
      child,
      sessionSecret,
      config.requestTimeoutMs ?? DEFAULT_REQUEST_TIMEOUT_MS,
    );
    // Record ownership: if we auto-loaded the identity, we must close it.
    if (!callerProvidedIdentity) {
      client.autoLoadedIdentity = identity;
    }
    client._wireStreams();

    // Send hello using BOOTSTRAP_KEY; await hello_ack signed with session_secret.
    const requestId = client._allocateRequestId();
    const helloMsg: Message = {
      version: 1n,
      messageType: MSG_TYPE.HELLO,
      requestId,
      payload: helloPayload(sessionSecret, operatorPubkey, helloSignature),
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
      import("@myco/anchor-client/src/canonical_bytes.ts").Value
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
    meta?: Map<string, import("@myco/anchor-client/src/canonical_bytes.ts").Value>;
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
    const { decode } = await import("@myco/anchor-client/src/renderer.ts");
    const { CanonicalBytes } = await import(
      "@myco/anchor-client/src/canonical_bytes.ts"
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

  /** M20 + **P08 §3.5 / §5.1** — Sprout a child substrate WITH a cultivator
   *  co-attestation. This is an attestation orchestrator (modelled on
   *  `cosignDagTip`): a child spawn is a CI-class doctrine event, not a
   *  daily-mode mutation, so the cultivator MUST co-sign it at the anchor
   *  surface or the substrate refuses with C68.
   *
   *  Steps:
   *  1. **querySubstrateId** — read the parent's substrate_id (binds the
   *     envelope to THIS parent → substrate-side replay guard).
   *  2. Compute `spore_schema_hash = blake3(sporeSchemaCanonicalBytes)`
   *     (raw BLAKE3 — matches the substrate's I7(a) check exactly).
   *  3. **getAnchorWallClock** + **generateAnchorNonce** — owner's
   *     authoritative timestamp + unbiasable nonce.
   *  4. Build the `myco-spawn-cosign-v1` envelope binding
   *     `(parent_substrate_id, spore_schema_hash,
   *      child_genesis_timestamp_unix_ns, anchor_timestamp_unix_ns,
   *      anchor_nonce, depth_override)`.
   *  5. **sign** — owner's Ed25519 key signs the envelope bytes.
   *  6. **sprout_child** — send envelope + signature + spore-schema bytes; the
   *     substrate verifies, owner-mints the §5.6 deterministic child-id, builds
   *     the child DAG, and emits `genesis_attested:{child_prefix}` (I7-closure).
   *
   *  The parent's causal DAG is NOT transferred (child starts its own causal
   *  history). Rejects if `childStateDir` already contains a dag.cb / manifest.cb.
   *
   *  `childGenesisTimestampUnixNs` defaults to the anchor wall-clock (the most
   *  natural birth timestamp). `depthOverride` defaults to false (the §16.A
   *  lineage-depth cap is enforced); set true to have the cultivator's signed
   *  override permit a spawn past the cap for THIS child.
   */
  async sproutChild(args: {
    childStateDir: string;
    /** The child's spore-schema canonical bytes (the 7-field L1/SCHEMA §3.1
     *  shape). Assembled by the caller (mcp_server) from the parent's current
     *  schema. blake3 of these bytes is co-signed as the spore_schema_hash. */
    sporeSchemaCanonicalBytes: Uint8Array;
    /** Operator/owner identity to co-sign with. Required (operator==owner in
     *  v0.9; the substrate verifies against the pinned owner pubkey). */
    operatorIdentity: OperatorIdentity;
    /** Optional explicit child genesis timestamp (unix ns). Defaults to the
     *  anchor wall-clock fetched during orchestration. */
    childGenesisTimestampUnixNs?: bigint;
    /** Optional cultivator depth-override for this spawn (§16.A / F22).
     *  Default false. */
    depthOverride?: boolean;
    spore_metadata?: Map<string, import("@myco/anchor-client/src/canonical_bytes.ts").Value>;
  }): Promise<SproutChildResult> {
    // 1. Parent substrate_id (replay guard).
    const parentSubstrateId = await this.querySubstrateId();

    // 2. Spore-schema hash (raw BLAKE3 — matches substrate I7(a)).
    const { blake3 } = await import("@noble/hashes/blake3.js");
    const sporeSchemaHash = blake3(args.sporeSchemaCanonicalBytes);

    // 3. Anchor wall clock + nonce.
    const wallClock = await args.operatorIdentity.getAnchorWallClock();
    const nonceResult = await args.operatorIdentity.generateAnchorNonce(300n);

    const childGenesisTimestampUnixNs = args.childGenesisTimestampUnixNs ??
      wallClock.anchorTimestampUnixNs;

    // 4. Build the spawn-cosign envelope.
    const envelope = buildSpawnCosignCanonicalBytes({
      parentSubstrateId,
      sporeSchemaHash,
      childGenesisTimestampUnixNs,
      anchorTimestampUnixNs: wallClock.anchorTimestampUnixNs,
      anchorNonce: nonceResult.nonce,
      depthOverride: args.depthOverride ?? false,
    });

    // 5. Owner signs the envelope bytes.
    const signature = await args.operatorIdentity.sign(envelope);

    // 6. Send. The substrate verifies the co-attestation BEFORE any side
    //    effect (C68 on failure), then mints the child-id + emits
    //    genesis_attested.
    const response = await this._sendRequest(
      MSG_TYPE.SPROUT_CHILD,
      sproutChildPayload({
        childStateDir: args.childStateDir,
        spawnCosignEnvelope: envelope,
        attestationSignature: signature,
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

  /** M14: Submit a CI mutation with full per-handshake REVEAL envelope.
   *
   *  This helper:
   *  1. Generates a fresh ephemeral Ed25519 keypair (the REVEAL key).
   *  2. Has the operator IDENTITY key (M9) sign the REVEAL pubkey via
   *     `revealKeyBindingSigningInput` (closes C17 operator_witness_forgery).
   *  3. Has the REVEAL private key sign `contentCanonicalBytes` (the attestation).
   *  4. Requests an attestation nonce for the content (M13).
   *  5. Submits the full envelope: content + REVEAL pubkey + IDENTITY-signed-REVEAL
   *     + REVEAL-signed-content + nonce + expiry.
   *
   *  If the operator's IDENTITY private key leaks but the REVEAL key did not,
   *  only THIS mutation's attestation can be forged — not future ones.
   *  Per-mutation credential isolation. */
  async submitMutationWithReveal(args: {
    mutationType: string;
    touchedFields?: string[];
    touchedFiles?: string[];
    touchedMetaStructures?: string[];
    contentCanonicalBytes: Uint8Array;
    operatorIdentity: import("./operator_identity.ts").OperatorIdentity;
    /** M24.2 SECURITY (Phase β fix): substrate_id of the target substrate,
     *  bound into the IDENTITY-over-REVEAL signature so the signature cannot
     *  be replayed against a different substrate with the same pinned operator.
     *  Obtainable from the genesis_event in the substrate's DAG. */
    substrateId: Uint8Array;
  }): Promise<MutationResult> {
    const { ed25519 } = await import("@noble/curves/ed25519.js");
    const { randomBytes: rb } = await import("node:crypto");

    // 1. Fresh REVEAL keypair.
    const revealSeed = new Uint8Array(rb(32));
    const revealPubkey = ed25519.getPublicKey(revealSeed);

    // 2. IDENTITY signs the REVEAL pubkey + substrate_id (M24.2 v2 binding).
    const identitySigningInput = revealKeyBindingSigningInput(
      revealPubkey,
      args.substrateId,
    );
    const identitySigOverReveal = await args.operatorIdentity.sign(identitySigningInput);

    // 3. REVEAL signs the content (the "attestation" signature).
    const revealSig = ed25519.sign(args.contentCanonicalBytes, revealSeed);

    // 4. Request a nonce bound to content + current DAG tip.
    const nonceResult = await this.requestAttestationNonce(args.contentCanonicalBytes);

    // 5. Submit the full envelope.
    return this.submitMutation({
      mutationType: args.mutationType,
      touchedFields: args.touchedFields,
      touchedFiles: args.touchedFiles,
      touchedMetaStructures: args.touchedMetaStructures,
      contentCanonicalBytes: args.contentCanonicalBytes,
      attestationSignature: revealSig,
      nonce: nonceResult.nonce,
      expiryUnixNs: nonceResult.expiryUnixNs,
      revealPubkey,
      identitySignatureOverRevealPubkey: identitySigOverReveal,
    });
  }

  /** **M-anchor-5 §9.2.2** — co-sign a DAG-tip from the anchor surface.
   *
   *  This is the high-level orchestrator for owner-side DAG-tip attestation.
   *  It performs the four anchor-surface round-trips needed to produce a
   *  valid `dag_tip_cosign` mutation:
   *
   *  1. **getAnchorWallClock** — fetch the owner's authoritative timestamp.
   *  2. **generateAnchorNonce** — fetch a 32-byte unbiasable nonce.
   *  3. Build the `myco-dag-tip-cosign-v1` canonical-bytes envelope binding
   *     `(tip_hash, enumerated_node_hashes, proposed_mutation_hash,
   *     anchor_timestamp_unix_ns, anchor_nonce)`.
   *  4. **sign** — owner's Ed25519 key signs the canonical bytes.
   *  5. **submitMutation** — wrap the envelope + signature into a CI mutation;
   *     substrate decodes + emits `tip_cosigned:{tip_prefix}` DAG event.
   *
   *  After this returns successfully, the DAG contains an immutable
   *  owner-attested record that "at this substrate-cycle, the owner
   *  observed THIS exact tip + history walk." Any post-hoc DAG rewrite
   *  becomes detectable by re-deriving from the cosign envelope.
   *
   *  `proposedMutationHash` is optional — pass undefined for a standalone
   *  tip cosign (the substrate accepts 32 zero bytes as "no proposed mutation").
   */
  async cosignDagTip(args: {
    /** The DAG tip the owner is attesting to (32 bytes). Typically obtained
     *  via a recent `queryRecentNodes` call's `dagTip` field. */
    tipHash: Uint8Array;
    /** In-order list of DAG node hashes the owner has independently walked
     *  and verified up to `tipHash`. Each must be 32 bytes. May be empty
     *  for a "tip-only" cosign that does not pin history walk. */
    enumeratedNodeHashes: Uint8Array[];
    /** Optional 32-byte hash of a proposed CI mutation that the owner is
     *  cosigning AS A PRECONDITION. Pass undefined for a standalone tip
     *  cosign. */
    proposedMutationHash?: Uint8Array;
    /** Operator identity to sign with. Required (the owner's anchor-surface
     *  key is what proves ownership of the signature). */
    operatorIdentity: OperatorIdentity;
  }): Promise<MutationResult> {
    // 1. Anchor wall clock + 2. anchor nonce (both via OperatorIdentity).
    const wallClock = await args.operatorIdentity.getAnchorWallClock();
    const nonceResult = await args.operatorIdentity.generateAnchorNonce(300n);

    // 3. Build the envelope.
    const proposedMutationHash = args.proposedMutationHash ?? new Uint8Array(32);
    const envelope = buildDagTipCosignCanonicalBytes({
      tipHash: args.tipHash,
      enumeratedNodeHashes: args.enumeratedNodeHashes,
      proposedMutationHash,
      anchorTimestampUnixNs: wallClock.anchorTimestampUnixNs,
      anchorNonce: nonceResult.nonce,
    });

    // 4. Owner signs the canonical bytes.
    const signature = await args.operatorIdentity.sign(envelope);

    // 5. Submit as CI mutation. The substrate-side handler will decode the
    //    envelope, capture the signature, and emit `tip_cosigned:{prefix}`
    //    DAG event after the mutation:dag_tip_cosign node lands.
    //    Substrate-issued nonce is also bound to the content hash for replay
    //    protection (independent of the anchor nonce inside the envelope).
    const subNonce = await this.requestAttestationNonce(envelope);
    return this.submitMutation({
      mutationType: "dag_tip_cosign",
      contentCanonicalBytes: envelope,
      attestationSignature: signature,
      nonce: subNonce.nonce,
      expiryUnixNs: subNonce.expiryUnixNs,
    });
  }

  /** **M-anchor-5 §9.2.4** — attest an L0 doctrine revision from the
   *  anchor surface.
   *
   *  When L0_DOCTRINE evolves from version X to version Y (e.g., a sealed
   *  draft progresses, or a §-section is added), this helper anchors the
   *  transition into the DAG as an owner-signed event. Without this anchor,
   *  the substrate could silently shift its doctrine ground truth between
   *  sessions; with it, every revision is permanently recorded and any
   *  rewrite is detectable.
   *
   *  Orchestrates the same four anchor-surface calls as `cosignDagTip`:
   *  wallClock → anchorNonce → buildEnvelope → sign → submitMutation. The
   *  envelope binds `(prior_l0_hash, new_l0_hash, diff_summary,
   *  anchor_timestamp_unix_ns, anchor_nonce)`.
   *
   *  After a successful return, the DAG contains
   *  `l0_revision_attested:{prior_l0_hash_prefix}` referencing the new
   *  doctrine hash plus the owner's signature — re-verifiable offline by
   *  anyone with the owner's public key.
   */
  async signL0Revision(args: {
    /** 32-byte hash of the L0 doctrine BEFORE the revision (e.g., SHA-256
     *  of the L0_DOCTRINE.md file at the prior commit). */
    priorL0Hash: Uint8Array;
    /** 32-byte hash of the L0 doctrine AFTER the revision. */
    newL0Hash: Uint8Array;
    /** Short human-readable description of what changed
     *  (e.g., "Add §9.4 federation observatory"). Stored verbatim in the
     *  signed envelope; canonicalization preserves the exact bytes. */
    diffSummary: string;
    operatorIdentity: OperatorIdentity;
  }): Promise<MutationResult> {
    const wallClock = await args.operatorIdentity.getAnchorWallClock();
    const nonceResult = await args.operatorIdentity.generateAnchorNonce(300n);
    const envelope = buildL0RevisionCanonicalBytes({
      priorL0Hash: args.priorL0Hash,
      newL0Hash: args.newL0Hash,
      diffSummary: args.diffSummary,
      anchorTimestampUnixNs: wallClock.anchorTimestampUnixNs,
      anchorNonce: nonceResult.nonce,
    });
    const signature = await args.operatorIdentity.sign(envelope);
    const subNonce = await this.requestAttestationNonce(envelope);
    return this.submitMutation({
      mutationType: "l0_revision_attest",
      contentCanonicalBytes: envelope,
      attestationSignature: signature,
      nonce: subNonce.nonce,
      expiryUnixNs: subNonce.expiryUnixNs,
    });
  }

  /** M13: Request an attestation nonce bound to a proposed mutation's content
   *  hash. The substrate returns nonce + expiry + dag_tip; operator includes
   *  the nonce in submit_mutation to prove a fresh (non-replay) intent.
   *
   *  M15: optionally supply `anchorClockUnixNs` (operator's wall-clock at
   *  request time). When present, the response includes
   *  `anchorClockExpiryUnixNs`, and the operator MUST supply
   *  `anchorClockSubmittedAtUnixNs` at submit time for the dual-clock check.
   *  Both clock checks must pass for nonce verification to succeed.
   */
  async requestAttestationNonce(
    contentCanonicalBytes: Uint8Array,
    anchorClockUnixNs?: bigint,
  ): Promise<AttestationNonceResult> {
    const contentHash = await this._sha256(contentCanonicalBytes);
    const response = await this._sendRequest(
      MSG_TYPE.REQUEST_ATTESTATION_NONCE,
      requestAttestationNoncePayload(contentHash, anchorClockUnixNs),
    );
    return parseRequestAttestationNonceResponse(response);
  }

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
    const { merkleHash, NodeHash } = await import("@myco/anchor-client/src/crypto.ts");
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

  /** M13: Internal SHA-256 helper (substrate-side compute_content_hash counterpart). */
  private async _sha256(data: Uint8Array): Promise<Uint8Array> {
    const { sha256 } = await import("@noble/hashes/sha2.js");
    return sha256(data);
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

  /** M22.5 (Phase β security fix): Owner-signed lift of birth-period
   *  quarantine. The substrate requires the caller's Ed25519 IDENTITY-key
   *  signature over the canonical signing input built by
   *  `liftBirthPeriodQuarantineSigningInput` (context + substrate_id +
   *  current_cycle). The current_cycle binding ensures the signature is not
   *  replayable across substrate boots — operator must re-sign per-cycle.
   *
   *  When not in active quarantine, `wasInQuarantine=false` and no DAG event
   *  is emitted.
   *
   *  Use `signLiftBirthPeriodQuarantine` to build the signature deterministically. */
  async liftBirthPeriodQuarantine(args: {
    ownerSignature: Uint8Array;
  }): Promise<LiftBirthPeriodQuarantineResult> {
    const response = await this._sendRequest(
      MSG_TYPE.LIFT_BIRTH_PERIOD_QUARANTINE,
      liftBirthPeriodQuarantinePayload(args),
    );
    return parseLiftBirthPeriodQuarantineResponse(response);
  }

  /** Helper: build the 64-byte Ed25519 owner signature for
   *  `liftBirthPeriodQuarantine`. The signing input is bound to the
   *  substrate_id (no cross-substrate replay) and current_cycle (no cross-boot
   *  replay). The substrate's cycle counter is queried automatically. */
  async signLiftBirthPeriodQuarantine(
    operatorIdentity: OperatorIdentity,
  ): Promise<Uint8Array> {
    const substrateId = await this.querySubstrateId();
    // Read current cycle via observatory (signal #1.manifest_cycle_counter is
    // always present in v1+). This costs one round-trip per signature but
    // ensures the cycle binding is exact.
    const observatory = await this.querySubstrateObservatory();
    const currentCycle = observatory.signal1?.manifestCycleCounter ?? 0n;
    const signingInput = liftBirthPeriodQuarantineSigningInput(
      substrateId,
      currentCycle,
    );
    return await operatorIdentity.sign(signingInput);
  }

  /** M23.2 P7 必朽: Owner co-attestation acceptance of a previously-emitted
   *  `self_euthanasia_proposal:{axis_name}` DAG node. The substrate verifies
   *  the IDENTITY-key signature over the canonical input built by
   *  `acceptSelfEuthanasiaProposalSigningInput` (context + proposal_hash +
   *  substrate_id), emits a `self_euthanasia_executed:{axis_name}` event, and
   *  replies with success.
   *
   *  **The substrate gracefully shuts down AFTER this response is written.**
   *  The DAG persists on disk as the substrate's signed post-mortem record.
   *  The caller's `this.child` will exit cleanly (code 0) shortly after the
   *  response resolves. Subsequent client operations will fail; callers
   *  typically follow this call with `shutdown()` or `_waitChildExit()` to
   *  observe the exit.
   *
   *  Use `signAcceptSelfEuthanasiaProposal` to build the signature
   *  deterministically. */
  async acceptSelfEuthanasiaProposal(args: {
    proposalHash: Uint8Array;
    ownerSignature: Uint8Array;
  }): Promise<AcceptSelfEuthanasiaProposalResult> {
    const response = await this._sendRequest(
      MSG_TYPE.ACCEPT_SELF_EUTHANASIA_PROPOSAL,
      acceptSelfEuthanasiaProposalPayload(args),
    );
    return parseAcceptSelfEuthanasiaProposalResponse(response);
  }

  /** Helper: build the 64-byte Ed25519 owner signature for
   *  `acceptSelfEuthanasiaProposal`. The signing input is bound to the
   *  proposal_hash + substrate_id; the signature is not replayable across
   *  different proposals nor across different substrates. */
  async signAcceptSelfEuthanasiaProposal(
    operatorIdentity: OperatorIdentity,
    proposalHash: Uint8Array,
  ): Promise<Uint8Array> {
    const substrateId = await this.querySubstrateId();
    const signingInput = acceptSelfEuthanasiaProposalSigningInput(
      proposalHash,
      substrateId,
    );
    return await operatorIdentity.sign(signingInput);
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

  /** Graceful shutdown — sends shutdown, awaits ack, waits for child exit,
   *  and closes any auto-loaded operator identity (which kills its spawned
   *  anchor-surface-host child). */
  async shutdown(): Promise<void> {
    if (this.fatalError) {
      // Still try to clean up the child.
      this._killChild();
      await this._closeAutoLoadedIdentity();
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
    await this._closeAutoLoadedIdentity();
  }

  private async _closeAutoLoadedIdentity(): Promise<void> {
    const id = this.autoLoadedIdentity;
    if (!id) return;
    this.autoLoadedIdentity = null;
    try {
      await id.close();
    } catch {
      // Best-effort; anchor host may already be dead.
    }
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

/**
 * **M-anchor-2 §9.2.1**: if the target state_dir looks fresh, pre-generate
 * `substrate_id` + `genesis_time_unix_ns`, request a birth attestation from
 * anchor_surface_host via the OperatorIdentity's underlying
 * AnchorSurfaceClient, and produce the env-var triple the substrate's
 * `read_birth_attestation_env_vars` helper expects.
 *
 * For PRE-EXISTING substrates (state dir has manifest.cb), returns `{}` so
 * the substrate's existing birth_attestation event (already in its DAG)
 * stays authoritative. Substrate-side C20 verifier re-checks on every boot.
 */
async function maybeBuildBirthAttestationEnv(
  identity: OperatorIdentity,
  stateDirOverride: string | undefined,
): Promise<Record<string, string>> {
  // Detect fresh substrate: state_dir doesn't yet contain manifest.cb.
  // If no override, the substrate uses its default dir (~/.myco/substrate/default);
  // we conservatively skip injection because we can't easily detect freshness
  // without inspecting the default path (and the default path may not exist
  // for first-time installs — but those are rare; auto-injection there can
  // happen via a future explicit `--bootstrap` flag).
  if (!stateDirOverride) return {};
  const { existsSync } = await import("node:fs");
  const { resolve: rp } = await import("node:path");
  const manifestPath = rp(stateDirOverride, "manifest.cb");
  const dagPath = rp(stateDirOverride, "dag.cb");
  if (existsSync(manifestPath) || existsSync(dagPath)) {
    // Substrate already exists — its DAG already carries (or doesn't carry)
    // a birth_attestation event; C20 will verify or fire accordingly. Don't
    // re-inject (would double-emit or clobber).
    return {};
  }

  // Fresh substrate. Pre-generate substrate_id + genesis_time, request
  // attestation, return env triple.
  const { randomBytes: rb } = await import("node:crypto");
  const substrateId = new Uint8Array(rb(32));
  const genesisTsNs = BigInt(Date.now()) * 1_000_000n;
  // Spore schema hash: M-anchor-2 minimum uses a placeholder hash. Future
  // M-anchor-2.5 will compute over the canonical-bytes of the initial
  // axis schema + sporocarp type tree per L1/SCHEMA §3.1. Placeholder is
  // a deterministic hash of the substrate_id so two substrates with
  // different IDs get different placeholders (defeats trivial duplication).
  const { createHash } = await import("node:crypto");
  const sporeSchemaHash = new Uint8Array(
    createHash("sha256").update(substrateId).update("placeholder_spore_v1").digest(),
  );
  // Anchor endpoint pubkey: per L0/cards/AS_anchor_surface §5 (v0.9 anchor collapsed to operator
  // process), this equals the owner pubkey.
  const anchorEndpointPubkey = identity.publicKeyBytes();

  // identity wraps an AnchorSurfaceClient; expose birthAttest via a
  // thin pass-through. The TS OperatorIdentity hides the inner client to
  // keep its private-by-default contract clean, so we round-trip via a
  // public helper that we'll add next.
  const result = await identity.birthAttest({
    substrateId,
    genesisTimestampUnixNs: genesisTsNs,
    sporeSchemaHash,
    anchorEndpointPubkey,
  });

  return {
    MYCO_SUBSTRATE_ID_OVERRIDE_HEX: _toHex(substrateId),
    MYCO_GENESIS_TIME_OVERRIDE_UNIX_NS: genesisTsNs.toString(),
    MYCO_BIRTH_ATTESTATION_BYTES_HEX: _toHex(result.attestedCanonicalBytes),
    MYCO_BIRTH_ATTESTATION_SIGNATURE_HEX: _toHex(result.signature),
    MYCO_BIRTH_ATTESTATION_OWNER_PUBKEY_HEX: _toHex(result.ownerPubkey),
  };
}
