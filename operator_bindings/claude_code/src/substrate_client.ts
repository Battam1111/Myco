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
import {
  advancePayload,
  type AdvanceReport,
  BOOTSTRAP_KEY,
  computeIntentPayload,
  decodeFrameBody,
  emptyPayload,
  encodeFrameBody,
  type HelloAck,
  helloPayload,
  helloSigningBody,
  type IntentReport,
  type Message,
  MSG_TYPE,
  parseAdvanceResponse,
  parseComputeIntentResponse,
  parseHelloAck,
  parseQueryRecentNodesResponse,
  parseSnapshotResponse,
  perturbPayload,
  queryRecentNodesPayload,
  type RecentNodesReport,
  registerAxisPayload,
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
}

/** Error thrown by SubstrateClient operations. */
export class SubstrateClientError extends Error {
  constructor(message: string) {
    super(`substrate client: ${message}`);
    this.name = "SubstrateClientError";
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
  /** Per-request response waiters. Keyed by request_id. */
  private pendingResponses: Map<
    bigint,
    {
      resolve: (msg: Message) => void;
      reject: (err: Error) => void;
    }
  >;
  /** Pending fatal error to surface to all waiters on next op. */
  private fatalError: Error | null;
  /** Resolved hello_ack info. */
  helloAck: HelloAck;

  private constructor(child: ChildProcess, sessionSecret: Uint8Array) {
    this.child = child;
    this.sessionSecret = sessionSecret;
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

    // M9: load (or create) the operator identity for signing the hello message.
    const identity = config.operatorIdentity ?? OperatorIdentity.loadOrCreate();
    const operatorPubkey = identity.publicKeyBytes();

    // Compute the hello signature over the canonical-bytes of {session_secret, operator_pubkey}.
    const signingInput = helloSigningBody(sessionSecret, operatorPubkey);
    const helloSignature = identity.sign(signingInput);

    const child = spawn(binary, [], {
      stdio: ["pipe", "pipe", "inherit"],
      env: { ...process.env, ...config.env },
    });

    const client = new SubstrateClient(child, sessionSecret);
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
    const waitForAck = client._registerWaiter(requestId);
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

  private _registerWaiter(requestId: bigint): Promise<Message> {
    return new Promise<Message>((resolve, reject) => {
      this.pendingResponses.set(requestId, { resolve, reject });
    });
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
      const waiter = this.pendingResponses.get(target);
      if (waiter) {
        this.pendingResponses.delete(target);
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
    const waiter = this.pendingResponses.get(msg.requestId);
    if (!waiter) {
      this._failAll(
        new SubstrateClientError(
          `received response for unknown request_id ${msg.requestId}`,
        ),
      );
      return;
    }
    this.pendingResponses.delete(msg.requestId);
    waiter.resolve(msg);
  }

  private _failAll(err: Error): void {
    this.fatalError = err;
    for (const [, waiter] of this.pendingResponses) {
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
    const waiter = this._registerWaiter(requestId);
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

  /** M8: Query the substrate's recent DAG nodes (causal history diagnostic). */
  async queryRecentNodes(count: bigint = 50n): Promise<RecentNodesReport> {
    const response = await this._sendRequest(
      MSG_TYPE.QUERY_RECENT_NODES,
      queryRecentNodesPayload(count),
    );
    return parseQueryRecentNodesResponse(response);
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

  /** Graceful shutdown — sends shutdown, awaits ack, waits for child exit. */
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
