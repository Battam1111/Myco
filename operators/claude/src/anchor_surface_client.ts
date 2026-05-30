// AnchorSurfaceClient — TS-side TCP client to anchor_surface_host (M-anchor-1).
//
// ## Doctrine origin
//
// Phase γ.5 audit found "operator-IS-anchor honor-system collapse" as DRAFT
// 9 SEALED's most critical surviving finding. Pre-M-anchor-1, the operator
// process held the owner's Ed25519 private key in its own memory. Any agent
// that could read the operator's memory (or its
// `~/.myco/operator_keys/identity.key` file) could forge owner signatures.
//
// M-anchor-1 moves the owner Ed25519 key into a SEPARATE process
// (`anchor-surface-host` binary) and exposes only signature operations over
// local TCP. After M-anchor-1, the operator process no longer holds
// `Ed25519PrivateKey` — only `AnchorSurfaceClient` references.
//
// ## Wire protocol
//
// The host binary listens on `127.0.0.1:<RANDOM_PORT>` (OS-assigned), writes
// the port to `~/.myco/anchor_surface/port.txt` (0600 on Unix).
//
// Each frame is `[u32 BE length][canonical-bytes Map envelope, length bytes]`.
//
// ```text
// GetPubkeyRequest:  Map({"type": "get_pubkey"})
// GetPubkeyResponse: Map({"pubkey": Bytes(32)})
//
// SignRequest:       Map({"type": "sign", "message": Bytes(N)})
// SignResponse:      Map({"signature": Bytes(64)})
//
// PingRequest:       Map({"type": "ping"})
// PingResponse:      Map({"ok": Bool(true)})
//
// ErrorResponse:     Map({"error": String(message)})
// ```
//
// ## API style
//
// All operations are async — each call performs a request/response over the
// shared TCP socket. The client serializes outstanding requests (one in
// flight at a time) using a chain of awaits internally; ed25519 signing on
// the host side is fast, and the operator process rarely signs in parallel.

import { spawn, type ChildProcess } from "node:child_process";
import { connect as tcpConnect, Socket } from "node:net";
import {
  existsSync,
  mkdirSync,
  readFileSync,
  rmSync,
} from "node:fs";
import { homedir } from "node:os";
import { dirname, resolve as resolvePath } from "node:path";

import {
  CanonicalBytes,
  encode as cbEncode,
  type Value,
} from "@myco/anchor-client/src/canonical_bytes.ts";
import { decode as cbDecode } from "@myco/anchor-client/src/renderer.ts";

/** Default host directory containing `port.txt` + `owner_key.cb`. */
export function defaultAnchorSurfaceDir(): string {
  const override = process.env.MYCO_ANCHOR_SURFACE_DIR;
  if (override) return override;
  return resolvePath(homedir(), ".myco", "anchor_surface");
}

/** Filename for the port-discovery file used to find a running host. */
export const PORT_DISCOVERY_FILENAME = "port.txt";

/** Maximum frame body size on the wire (1 MiB; matches Rust). */
export const MAX_FRAME_BODY_SIZE = 1024 * 1024;

/** Default per-request response timeout for anchor ops (30s). Owner-key
 *  operations (sign / pubkey / nonce / heartbeat) are fast on the host side;
 *  this only fires when the host process truly hangs after a frame is sent. */
export const ANCHOR_DEFAULT_REQUEST_TIMEOUT_MS = 30_000;

/** Error thrown by AnchorSurfaceClient operations. */
export class AnchorSurfaceClientError extends Error {
  constructor(message: string) {
    super(`anchor surface client: ${message}`);
    this.name = "AnchorSurfaceClientError";
  }
}

/** Thrown when a roundtrip's response does not arrive within the configured
 *  timeout. Extends {@link AnchorSurfaceClientError} so existing
 *  `instanceof AnchorSurfaceClientError` handling treats it as a host failure;
 *  the distinct subtype lets callers detect the timeout specifically. */
export class AnchorSurfaceTimeoutError extends AnchorSurfaceClientError {
  constructor(requestType: string, elapsedMs: number) {
    super(
      `request '${requestType}' timed out after ${elapsedMs}ms (no response frame)`,
    );
    this.name = "AnchorSurfaceTimeoutError";
  }
}

/** Options for `connectOrSpawn`. */
export interface ConnectOrSpawnOptions {
  /** Override the host directory (defaults to defaultAnchorSurfaceDir()). */
  dir?: string;
  /** Path to the anchor-surface-host binary. Required when spawning;
   *  optional when connecting to an already-running host. */
  hostBinary?: string;
  /** Optional owner-seed hex override (testing only — 64 hex chars). When
   *  set, the spawned host genesis-uses this seed instead of generating
   *  fresh randomness. The seed is passed via environment variable so it
   *  never appears in `argv` (visible to other processes via `ps`). */
  ownerSeedHex?: string;
  /** Spawn a host if no port.txt is found OR if connecting to the recorded
   *  port fails. Defaults to true. Set false to require a pre-existing host. */
  autoSpawn?: boolean;
  /** Max milliseconds to wait for a freshly-spawned host to start listening
   *  (default 5000). Ignored when an existing host is found. */
  spawnTimeoutMs?: number;
  /** Per-request response timeout in milliseconds applied to every roundtrip
   *  (sign / pubkey / ping / attest / nonce / heartbeat). On expiry the
   *  awaiting promise rejects with an {@link AnchorSurfaceTimeoutError} and the
   *  pending waiter is evicted. Defaults to
   *  {@link ANCHOR_DEFAULT_REQUEST_TIMEOUT_MS} (30_000). */
  requestTimeoutMs?: number;
}

/** TS-side client that delegates owner-key operations to anchor-surface-host. */
export class AnchorSurfaceClient {
  private socket: Socket;
  private spawnedChild: ChildProcess | null;
  private rxBuffer: Uint8Array;
  /** Resolves the next pending response (FIFO; we send one at a time). */
  private pending: {
    resolve: (frame: Uint8Array) => void;
    reject: (err: Error) => void;
  } | null;
  private fatalError: Error | null;
  /** Cached pubkey to avoid round-tripping on every read. */
  private cachedPubkey: Uint8Array | null;
  /** Serializes outstanding requests (one at a time). */
  private writeQueue: Promise<void>;
  /** Per-request response timeout (ms). See ConnectOrSpawnOptions. */
  private requestTimeoutMs: number;

  private constructor(
    socket: Socket,
    spawnedChild: ChildProcess | null,
    requestTimeoutMs: number,
  ) {
    this.socket = socket;
    this.spawnedChild = spawnedChild;
    this.rxBuffer = new Uint8Array(0);
    this.pending = null;
    this.fatalError = null;
    this.cachedPubkey = null;
    this.writeQueue = Promise.resolve();
    this.requestTimeoutMs = requestTimeoutMs;
    this._wireSocket();
  }

  /** Connect to a running anchor_surface_host. If none is running and
   *  `autoSpawn` is true (default), spawn a new host using `hostBinary`. */
  static async connectOrSpawn(
    options: ConnectOrSpawnOptions = {},
  ): Promise<AnchorSurfaceClient> {
    const dir = options.dir ?? defaultAnchorSurfaceDir();
    const autoSpawn = options.autoSpawn ?? true;
    const requestTimeoutMs =
      options.requestTimeoutMs ?? ANCHOR_DEFAULT_REQUEST_TIMEOUT_MS;
    const portFile = resolvePath(dir, PORT_DISCOVERY_FILENAME);

    // First try connecting to an existing host.
    if (existsSync(portFile)) {
      const port = parsePortFile(portFile);
      if (port !== null) {
        try {
          const socket = await connectTcp(port);
          return new AnchorSurfaceClient(socket, null, requestTimeoutMs);
        } catch {
          // Existing port.txt but couldn't connect — port stale; fall through
          // to spawn (if allowed) or fail.
        }
      }
    }

    if (!autoSpawn) {
      throw new AnchorSurfaceClientError(
        `no running host at ${portFile} and autoSpawn=false`,
      );
    }
    if (!options.hostBinary) {
      throw new AnchorSurfaceClientError(
        "no running host and no hostBinary provided to spawn",
      );
    }

    // Clean any stale port.txt before spawning so we don't read the old port.
    if (existsSync(portFile)) {
      try {
        rmSync(portFile);
      } catch {
        // Ignore; the spawn will overwrite.
      }
    }
    mkdirSync(dir, { recursive: true });
    const child = spawnHost(options.hostBinary, dir, options.ownerSeedHex);
    const timeout = options.spawnTimeoutMs ?? 5000;
    const port = await waitForHostReady(child, portFile, timeout);
    const socket = await connectTcp(port);
    return new AnchorSurfaceClient(socket, child, requestTimeoutMs);
  }

  /** Get the owner's 32-byte Ed25519 public key. Cached on first call. */
  async getPubkey(): Promise<Uint8Array> {
    if (this.cachedPubkey) return this.cachedPubkey;
    const reqMap: Map<string, Value> = new Map();
    reqMap.set("type", { type: "string", value: "get_pubkey" });
    const response = await this._roundtrip(reqMap);
    const pk = mapGetBytes(response, "pubkey");
    if (pk.length !== 32) {
      throw new AnchorSurfaceClientError(
        `pubkey response length ${pk.length} != 32`,
      );
    }
    this.cachedPubkey = pk;
    return pk;
  }

  /** Sign a message with the owner's Ed25519 private key. Returns 64 bytes. */
  async sign(message: Uint8Array): Promise<Uint8Array> {
    const reqMap: Map<string, Value> = new Map();
    reqMap.set("type", { type: "string", value: "sign" });
    reqMap.set("message", { type: "bytes", value: message });
    const response = await this._roundtrip(reqMap);
    const sig = mapGetBytes(response, "signature");
    if (sig.length !== 64) {
      throw new AnchorSurfaceClientError(
        `signature response length ${sig.length} != 64`,
      );
    }
    return sig;
  }

  /** Liveness check. Returns true when the host responds with `ok: true`. */
  async ping(): Promise<boolean> {
    const reqMap: Map<string, Value> = new Map();
    reqMap.set("type", { type: "string", value: "ping" });
    const response = await this._roundtrip(reqMap);
    const ok = response.get("ok");
    return ok?.type === "bool" && ok.value === true;
  }

  /**
   * **M-anchor-2 §9.2.1**: produce a birth attestation for a fresh
   * substrate. Returns the owner's Ed25519 signature over the L0/cards/AS_anchor_surface §3
   * 5-tuple canonical-bytes, the owner pubkey, AND the exact canonical
   * bytes that were signed (so the substrate can persist all three in its
   * DAG and re-verify offline on every boot).
   *
   * Wire protocol: `BirthAttestRequest`/`BirthAttestation` (see
   * `anchor_surface_host::protocol`). The signature is over a
   * domain-separated canonical-bytes Map — substrate-side verification
   * must reconstruct the exact same bytes (use the same canonical-bytes
   * spec via `@myco/anchor-client/src/canonical_bytes.ts`).
   */
  async birthAttest(args: {
    substrateId: Uint8Array;
    genesisTimestampUnixNs: bigint;
    sporeSchemaHash: Uint8Array;
    anchorEndpointPubkey: Uint8Array;
  }): Promise<{
    signature: Uint8Array;
    ownerPubkey: Uint8Array;
    attestedCanonicalBytes: Uint8Array;
  }> {
    if (args.substrateId.length !== 32) {
      throw new AnchorSurfaceClientError(
        `birthAttest: substrateId must be 32 bytes; got ${args.substrateId.length}`,
      );
    }
    if (args.sporeSchemaHash.length !== 32) {
      throw new AnchorSurfaceClientError(
        `birthAttest: sporeSchemaHash must be 32 bytes; got ${args.sporeSchemaHash.length}`,
      );
    }
    if (args.anchorEndpointPubkey.length !== 32) {
      throw new AnchorSurfaceClientError(
        `birthAttest: anchorEndpointPubkey must be 32 bytes; got ${args.anchorEndpointPubkey.length}`,
      );
    }
    const reqMap: Map<string, Value> = new Map();
    reqMap.set("type", { type: "string", value: "birth_attest" });
    reqMap.set("substrate_id", { type: "bytes", value: args.substrateId });
    reqMap.set("genesis_timestamp_unix_ns", {
      type: "timestamp",
      value: args.genesisTimestampUnixNs,
    });
    reqMap.set("spore_schema_hash", { type: "bytes", value: args.sporeSchemaHash });
    reqMap.set("anchor_endpoint_pubkey", {
      type: "bytes",
      value: args.anchorEndpointPubkey,
    });
    const response = await this._roundtrip(reqMap);
    expectKind(response, "birth_attestation");
    const signature = mapGetBytes(response, "signature");
    if (signature.length !== 64) {
      throw new AnchorSurfaceClientError(
        `birthAttest signature length ${signature.length} != 64`,
      );
    }
    const ownerPubkey = mapGetBytes(response, "owner_pubkey");
    if (ownerPubkey.length !== 32) {
      throw new AnchorSurfaceClientError(
        `birthAttest owner_pubkey length ${ownerPubkey.length} != 32`,
      );
    }
    const attestedCanonicalBytes = mapGetBytes(response, "attested_canonical_bytes");
    return { signature, ownerPubkey, attestedCanonicalBytes };
  }

  /**
   * **M-anchor-3 §9.2.5**: generate a fresh anchor-side nonce + signature.
   * `ttlSeconds` is clamped to `[1, 3600]` by the host. Returns the nonce,
   * issue + expiry timestamps (anchor wall-clock), and signature over the
   * tuple.
   */
  async generateAnchorNonce(ttlSeconds: bigint): Promise<{
    nonce: Uint8Array;
    anchorTimestampUnixNs: bigint;
    expiryUnixNs: bigint;
    signature: Uint8Array;
  }> {
    const reqMap: Map<string, Value> = new Map();
    reqMap.set("type", { type: "string", value: "generate_anchor_nonce" });
    reqMap.set("ttl_seconds", { type: "uint", value: ttlSeconds });
    const response = await this._roundtrip(reqMap);
    expectKind(response, "anchor_nonce");
    const nonce = mapGetBytes(response, "nonce");
    if (nonce.length !== 32) {
      throw new AnchorSurfaceClientError(
        `generateAnchorNonce nonce length ${nonce.length} != 32`,
      );
    }
    const anchorTimestampUnixNs = mapGetTimestamp(response, "anchor_timestamp_unix_ns");
    const expiryUnixNs = mapGetTimestamp(response, "expiry_unix_ns");
    const signature = mapGetBytes(response, "signature");
    if (signature.length !== 64) {
      throw new AnchorSurfaceClientError(
        `generateAnchorNonce signature length ${signature.length} != 64`,
      );
    }
    return { nonce, anchorTimestampUnixNs, expiryUnixNs, signature };
  }

  /**
   * **M-anchor-3 §9.2.6**: read the anchor's current wall-clock as a
   * signed assertion. Per L0/cards/P06_eternal_causality + L1/CONTINUITY (time semantics), anchor wall-clock is authoritative
   * for time-bound defenses.
   */
  async getAnchorWallClock(): Promise<{
    anchorTimestampUnixNs: bigint;
    signature: Uint8Array;
  }> {
    const reqMap: Map<string, Value> = new Map();
    reqMap.set("type", { type: "string", value: "get_anchor_wall_clock" });
    const response = await this._roundtrip(reqMap);
    expectKind(response, "anchor_wall_clock");
    const anchorTimestampUnixNs = mapGetTimestamp(response, "anchor_timestamp_unix_ns");
    const signature = mapGetBytes(response, "signature");
    if (signature.length !== 64) {
      throw new AnchorSurfaceClientError(
        `getAnchorWallClock signature length ${signature.length} != 64`,
      );
    }
    return { anchorTimestampUnixNs, signature };
  }

  /**
   * **M-anchor-3 §9.2.7**: owner liveness heartbeat. Returns a fresh
   * nonce + current anchor timestamp + signature. The substrate persists
   * the most recent heartbeat; the Cultivation successor activation gate
   * (L1/GOVERNANCE §3.2) checks staleness.
   */
  async heartbeat(): Promise<{
    anchorTimestampUnixNs: bigint;
    heartbeatNonce: Uint8Array;
    signature: Uint8Array;
  }> {
    const reqMap: Map<string, Value> = new Map();
    reqMap.set("type", { type: "string", value: "heartbeat" });
    const response = await this._roundtrip(reqMap);
    expectKind(response, "heartbeat");
    const anchorTimestampUnixNs = mapGetTimestamp(response, "anchor_timestamp_unix_ns");
    const heartbeatNonce = mapGetBytes(response, "heartbeat_nonce");
    if (heartbeatNonce.length !== 32) {
      throw new AnchorSurfaceClientError(
        `heartbeat nonce length ${heartbeatNonce.length} != 32`,
      );
    }
    const signature = mapGetBytes(response, "signature");
    if (signature.length !== 64) {
      throw new AnchorSurfaceClientError(
        `heartbeat signature length ${signature.length} != 64`,
      );
    }
    return { anchorTimestampUnixNs, heartbeatNonce, signature };
  }

  /** Tear down the TCP connection. If this client spawned its own host, the
   *  child is killed as well — useful for tests. */
  async close(): Promise<void> {
    try {
      this.socket.end();
    } catch {
      // Ignore.
    }
    if (this.spawnedChild) {
      try {
        this.spawnedChild.kill();
      } catch {
        // Ignore.
      }
      await new Promise<void>((resolve) => {
        const child = this.spawnedChild;
        if (!child) {
          resolve();
          return;
        }
        if (child.exitCode !== null) {
          resolve();
          return;
        }
        child.once("exit", () => resolve());
      });
    }
  }

  /** Issue one request map → wait for one response map. Serialized: only
   *  one request is in flight at a time. */
  private async _roundtrip(
    requestMap: Map<string, Value>,
  ): Promise<Map<string, Value>> {
    if (this.fatalError) throw this.fatalError;
    const next = this.writeQueue.then(() => this._sendAndReceive(requestMap));
    // Chain the queue so the next caller waits for THIS to finish.
    this.writeQueue = next.then(
      () => undefined,
      () => undefined,
    );
    return next;
  }

  private async _sendAndReceive(
    requestMap: Map<string, Value>,
  ): Promise<Map<string, Value>> {
    if (this.fatalError) throw this.fatalError;
    const reqValue: Value = { type: "map", value: requestMap };
    const reqBytes = cbEncode(reqValue).bytes;
    if (reqBytes.length > MAX_FRAME_BODY_SIZE) {
      throw new AnchorSurfaceClientError(
        `request body ${reqBytes.length} > ${MAX_FRAME_BODY_SIZE}`,
      );
    }
    const lengthHeader = new Uint8Array(4);
    new DataView(lengthHeader.buffer).setUint32(0, reqBytes.length, false);

    // Request-type discriminator, purely for the timeout error message.
    const typeVal = requestMap.get("type");
    const requestType =
      typeVal && typeVal.type === "string" ? typeVal.value : "(unknown)";

    const responseBytes = await new Promise<Uint8Array>((resolve, reject) => {
      const startedAt = Date.now();
      // Wrap resolve/reject so the liveness timer (armed just below) is always
      // cleared the moment this roundtrip settles — no leaked timer can keep
      // `node --test` alive.
      const waiter: {
        resolve: (frame: Uint8Array) => void;
        reject: (err: Error) => void;
      } = {
        resolve: (frame: Uint8Array) => {
          clearTimeout(timer);
          resolve(frame);
        },
        reject: (err: Error) => {
          clearTimeout(timer);
          reject(err);
        },
      };
      // Liveness guard: a host that accepts the frame but never answers would
      // otherwise leave this caller (and the serialized write-queue behind it)
      // blocked forever. On expiry we evict the pending waiter and fail the
      // client fatally — a late frame on a single-in-flight socket would
      // desync the stream, which is exactly the existing fatal condition.
      // `.unref()` keeps a still-armed timer from holding the event loop open;
      // we clear it on every settle path above regardless.
      const timer = setTimeout(() => {
        // Only act if THIS request is still the pending one (not already
        // resolved/rejected by an in-flight frame or _failAll).
        if (this.pending !== waiter) return;
        this.pending = null;
        this._failAll(
          new AnchorSurfaceTimeoutError(requestType, Date.now() - startedAt),
        );
      }, this.requestTimeoutMs);
      timer.unref?.();
      this.pending = waiter;
      try {
        this.socket.write(lengthHeader);
        this.socket.write(reqBytes);
      } catch (e) {
        waiter.reject(e instanceof Error ? e : new Error(String(e)));
      }
    });

    const decoded = cbDecode(new CanonicalBytes(responseBytes));
    if (decoded.type !== "map") {
      throw new AnchorSurfaceClientError(
        `response root is not a Map (got ${decoded.type})`,
      );
    }
    // Surface error envelopes as exceptions.
    const errMsg = decoded.value.get("error");
    if (errMsg && errMsg.type === "string") {
      throw new AnchorSurfaceClientError(`host error: ${errMsg.value}`);
    }
    return decoded.value;
  }

  private _wireSocket(): void {
    this.socket.on("data", (chunk: Buffer) => {
      // Append to the rx buffer.
      const combined = new Uint8Array(this.rxBuffer.length + chunk.length);
      combined.set(this.rxBuffer, 0);
      combined.set(new Uint8Array(chunk), this.rxBuffer.length);
      this.rxBuffer = combined;
      // Try to extract complete frames.
      try {
        while (this.rxBuffer.length >= 4) {
          const view = new DataView(
            this.rxBuffer.buffer,
            this.rxBuffer.byteOffset,
            this.rxBuffer.byteLength,
          );
          const length = view.getUint32(0, false);
          if (length > MAX_FRAME_BODY_SIZE) {
            throw new AnchorSurfaceClientError(
              `incoming frame too large: ${length}`,
            );
          }
          if (this.rxBuffer.length < 4 + length) break;
          const frame = this.rxBuffer.slice(4, 4 + length);
          this.rxBuffer = this.rxBuffer.slice(4 + length);
          const waiter = this.pending;
          this.pending = null;
          if (waiter) {
            waiter.resolve(frame);
          } else {
            // No pending waiter — this is a protocol error (host shouldn't
            // emit unsolicited frames).
            this._failAll(
              new AnchorSurfaceClientError(
                "received unsolicited frame from host",
              ),
            );
            return;
          }
        }
      } catch (e) {
        this._failAll(e instanceof Error ? e : new Error(String(e)));
      }
    });
    this.socket.on("error", (e: Error) => {
      this._failAll(
        new AnchorSurfaceClientError(`socket error: ${e.message}`),
      );
    });
    this.socket.on("close", () => {
      if (this.pending) {
        this._failAll(
          new AnchorSurfaceClientError("socket closed mid-request"),
        );
      }
    });
  }

  private _failAll(err: Error): void {
    this.fatalError = err;
    if (this.pending) {
      this.pending.reject(err);
      this.pending = null;
    }
  }
}

// ---------------------------------------------------------------------------
// Helpers (file-local).
// ---------------------------------------------------------------------------

function parsePortFile(portFile: string): number | null {
  try {
    const raw = readFileSync(portFile, "utf8").trim();
    const n = Number.parseInt(raw, 10);
    if (Number.isFinite(n) && n > 0 && n < 65_536) return n;
  } catch {
    // Ignore.
  }
  return null;
}

function connectTcp(port: number): Promise<Socket> {
  return new Promise<Socket>((resolve, reject) => {
    const socket = tcpConnect({ host: "127.0.0.1", port }, () => {
      resolve(socket);
    });
    socket.once("error", (e) => {
      reject(e);
    });
  });
}

// Module-level registry of spawned host children. Ensures we kill any host
// that this Node process spawned when the process exits, even if a caller
// forgets to call `identity.close()`. Without this, tests (which spawn many
// short-lived isolated hosts) would leak anchor-surface-host processes on
// Windows where children are not auto-killed when the parent exits.
const SPAWNED_HOST_CHILDREN: Set<ChildProcess> = new Set();
let EXIT_HANDLERS_INSTALLED = false;

/**
 * Kill every anchor-surface-host child this process has spawned and that has
 * not already exited. Returns a Promise that resolves after all kill signals
 * have been issued AND every tracked child has emitted its `exit` event (or
 * 5s have elapsed, whichever first).
 *
 * Intended for test teardown (`after(() => killAllSpawnedHosts())`): without
 * this, tests that obtained an OperatorIdentity but never called `close()`
 * leave their host children alive, holding the parent Node event loop open
 * (their stdio pipes are reffed) and the test process hangs after all tests
 * pass instead of exiting cleanly.
 */
export async function killAllSpawnedHosts(): Promise<void> {
  const children = Array.from(SPAWNED_HOST_CHILDREN);
  SPAWNED_HOST_CHILDREN.clear();
  const waiters: Array<Promise<void>> = [];
  for (const child of children) {
    if (child.exitCode !== null) continue;
    waiters.push(
      new Promise<void>((resolve) => {
        const timer = setTimeout(() => resolve(), 5000);
        child.once("exit", () => {
          clearTimeout(timer);
          resolve();
        });
        try {
          child.kill();
        } catch {
          clearTimeout(timer);
          resolve();
        }
      }),
    );
  }
  await Promise.all(waiters);
}

function installExitHandlersOnce(): void {
  if (EXIT_HANDLERS_INSTALLED) return;
  EXIT_HANDLERS_INSTALLED = true;
  // Synchronous best-effort kill on exit. Async cleanup (graceful shutdown)
  // is not possible from `exit`; we just signal termination.
  const killAll = () => {
    for (const child of SPAWNED_HOST_CHILDREN) {
      try {
        if (child.exitCode === null) child.kill();
      } catch {
        // Ignore — child already dead or kill failed.
      }
    }
    SPAWNED_HOST_CHILDREN.clear();
  };
  process.once("exit", killAll);
  // SIGINT/SIGTERM additionally so Ctrl-C in interactive test runs also cleans up.
  const signalKill = () => {
    killAll();
    process.exit(130);
  };
  process.once("SIGINT", signalKill);
  process.once("SIGTERM", signalKill);
}

function spawnHost(
  hostBinary: string,
  dir: string,
  ownerSeedHex: string | undefined,
): ChildProcess {
  installExitHandlersOnce();
  const env: NodeJS.ProcessEnv = {
    ...process.env,
    MYCO_ANCHOR_SURFACE_DIR: dir,
    MYCO_ANCHOR_SURFACE_BIND_ADDR: "127.0.0.1:0",
  };
  if (ownerSeedHex) {
    env.MYCO_ANCHOR_SURFACE_OWNER_SEED_HEX = ownerSeedHex;
  }
  // Make sure the parent directory exists before the host writes port.txt.
  mkdirSync(dirname(resolvePath(dir, PORT_DISCOVERY_FILENAME)), {
    recursive: true,
  });
  const child = spawn(hostBinary, [], {
    env,
    stdio: ["ignore", "pipe", "pipe"],
  });
  // Drain stderr so it doesn't block the pipe; surface to console for diagnostics.
  child.stderr?.on("data", (chunk: Buffer) => {
    // Keep silent in normal operation; uncomment for debugging:
    // process.stderr.write(`[anchor-surface-host] ${chunk.toString()}`);
    const _ = chunk;
  });
  // Track + auto-deregister on child exit. The module-level `process.on("exit")`
  // handler installed in `installExitHandlersOnce()` kills any host still in
  // SPAWNED_HOST_CHILDREN at process exit — that's the safety net for callers
  // that forgot to invoke `client.close()`. The primary cleanup path remains
  // `client.close()` (synchronously sends SIGTERM + awaits exit).
  SPAWNED_HOST_CHILDREN.add(child);
  child.once("exit", () => {
    SPAWNED_HOST_CHILDREN.delete(child);
  });
  return child;
}

async function waitForHostReady(
  child: ChildProcess,
  portFile: string,
  timeoutMs: number,
): Promise<number> {
  // Strategy: parse the first stdout line "anchor-surface-host listening on
  // 127.0.0.1:<PORT>" — fastest + most reliable. Fall back to polling
  // port.txt if stdout is somehow unavailable.
  const startedAt = Date.now();
  if (child.stdout) {
    const port = await readPortFromStdout(child, timeoutMs);
    if (port !== null) return port;
  }
  // Fallback: poll port.txt.
  while (Date.now() - startedAt < timeoutMs) {
    if (existsSync(portFile)) {
      const p = parsePortFile(portFile);
      if (p !== null) return p;
    }
    await sleep(25);
  }
  throw new AnchorSurfaceClientError(
    `host did not become ready within ${timeoutMs}ms`,
  );
}

function readPortFromStdout(
  child: ChildProcess,
  timeoutMs: number,
): Promise<number | null> {
  return new Promise<number | null>((resolve) => {
    if (!child.stdout) {
      resolve(null);
      return;
    }
    let buf = "";
    const onData = (chunk: Buffer) => {
      buf += chunk.toString("utf8");
      // Looking for: "anchor-surface-host listening on 127.0.0.1:<PORT>\n"
      const newlineIdx = buf.indexOf("\n");
      if (newlineIdx >= 0) {
        const line = buf.substring(0, newlineIdx);
        const m = line.match(/127\.0\.0\.1:(\d+)/);
        if (m) {
          const port = Number.parseInt(m[1]!, 10);
          if (Number.isFinite(port)) {
            cleanup();
            resolve(port);
            return;
          }
        }
        // Move past the parsed line; keep scanning subsequent lines if any.
        buf = buf.substring(newlineIdx + 1);
      }
    };
    const timer = setTimeout(() => {
      cleanup();
      resolve(null);
    }, timeoutMs);
    const cleanup = () => {
      clearTimeout(timer);
      child.stdout?.off("data", onData);
    };
    child.stdout.on("data", onData);
    child.once("exit", () => {
      cleanup();
      resolve(null);
    });
  });
}

function sleep(ms: number): Promise<void> {
  return new Promise<void>((resolve) => setTimeout(resolve, ms));
}

function mapGetBytes(
  m: Map<string, Value>,
  key: string,
): Uint8Array {
  const v = m.get(key);
  if (!v) {
    throw new AnchorSurfaceClientError(`response missing key ${key}`);
  }
  if (v.type !== "bytes") {
    throw new AnchorSurfaceClientError(
      `response key ${key} is not bytes (got ${v.type})`,
    );
  }
  return v.value;
}

/** M-anchor-2+3: extract a Timestamp (bigint) value from a response Map. */
function mapGetTimestamp(m: Map<string, Value>, key: string): bigint {
  const v = m.get(key);
  if (!v) {
    throw new AnchorSurfaceClientError(`response missing key ${key}`);
  }
  if (v.type !== "timestamp") {
    throw new AnchorSurfaceClientError(
      `response key ${key} is not timestamp (got ${v.type})`,
    );
  }
  return v.value;
}

/** M-anchor-2+3: verify the response's `kind` discriminator matches the
 *  expected value. The new response types (birth_attestation, anchor_nonce,
 *  anchor_wall_clock, heartbeat) all share the `signature` field, so the
 *  `kind` discriminator is how we know which shape to parse. */
function expectKind(m: Map<string, Value>, expected: string): void {
  const v = m.get("kind");
  if (!v) {
    throw new AnchorSurfaceClientError(
      `response missing 'kind' discriminator (expected ${expected})`,
    );
  }
  if (v.type !== "string") {
    throw new AnchorSurfaceClientError(
      `response 'kind' is not a string (got ${v.type})`,
    );
  }
  if (v.value !== expected) {
    throw new AnchorSurfaceClientError(
      `response kind=${v.value} != expected ${expected}`,
    );
  }
}
