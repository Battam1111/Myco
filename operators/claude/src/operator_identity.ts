// Operator identity — thin client over anchor_surface_host (M-anchor-1).
//
// ## Role evolution
//
// - M9 introduced a persistent Ed25519 identity for the operator, stored in
//   `~/.myco/operator_keys/identity.key`. The private seed lived in the
//   operator process memory.
// - **M-anchor-1** (this version) moves the owner Ed25519 key into a
//   SEPARATE process — the anchor_surface_host binary. The operator process
//   talks to that host over local TCP via `AnchorSurfaceClient`. The seed
//   bytes NEVER appear in the operator's memory after M-anchor-1.
//
// ## Why this is the right M-anchor-1
//
// Phase γ.5 fungal-critic audit found "operator-IS-anchor honor-system
// collapse" as DRAFT 9 SEALED's most critical surviving finding. Pre-
// M-anchor-1, any agent that could read the operator's memory (or its
// `~/.myco/operator_keys/identity.key` file) could forge owner signatures.
// M-anchor-1 closes that gap by ensuring the operator process is a
// signature CONSUMER — it can sign but cannot exfiltrate the key.
//
// ## Doctrine
//
// - L1/SKIN §4.1 — per-handshake operator signing key. The IDENTITY layer
//   now lives in anchor_surface_host, not the operator process.
// - L1/HARD_RULES C2 — handshake_pubkey_mismatch: rejection on pinned-key
//   divergence is the cross-process realization of this detector. The
//   pubkey itself still flows through the operator process; only the
//   private seed is hidden.
// - L1/GOVERNANCE §2.1 — owner's private key never enters substrate memory
//   nor operator memory after M-anchor-1.
//
// ## API change (breaking)
//
// `sign(message)` is now `async sign(message): Promise<Uint8Array>`. All
// callers must `await` it. The async form is required because every signing
// operation now performs a TCP round-trip to the anchor_surface_host.
//
// ## Migration from pre-M-anchor-1 operators
//
// Existing operators with a `~/.myco/operator_keys/identity.key` file have
// NOT been auto-migrated. Auto-migration is risky (silent re-binding of
// trust to a different process) and is deferred to an explicit one-shot
// tool. New deployments use `anchor_surface_host` from day one; legacy
// deployments must run the migration tool before upgrading.

import { resolve as resolvePath } from "node:path";
import { homedir } from "node:os";

import {
  AnchorSurfaceClient,
  type ConnectOrSpawnOptions,
} from "./anchor_surface_client.ts";

/** Legacy filename for the pre-M-anchor-1 operator identity seed. Kept as
 *  a constant so legacy paths can still be referenced in migration tooling. */
export const OPERATOR_IDENTITY_FILENAME = "identity.key";

/** Default directory for the legacy operator-key storage location (kept for
 *  migration tooling). Production identity now lives in
 *  `anchor_surface_host`'s state directory. */
export function defaultOperatorKeyDir(): string {
  const override = process.env.MYCO_OPERATOR_KEY_DIR;
  if (override) return override;
  return resolvePath(homedir(), ".myco", "operator_keys");
}

/** Error thrown by OperatorIdentity operations. */
export class OperatorIdentityError extends Error {
  constructor(message: string) {
    super(`operator identity: ${message}`);
    this.name = "OperatorIdentityError";
  }
}

/** Connection options for `OperatorIdentity.connectOrSpawn`. */
export type OperatorIdentityOptions = ConnectOrSpawnOptions;

/**
 * OperatorIdentity — thin client over `anchor_surface_host`.
 *
 * The owner's Ed25519 private seed lives in the SEPARATE anchor_surface_host
 * process. This class issues sign/get_pubkey calls over the host's local
 * TCP socket. The operator process never holds an `Ed25519PrivateKey`.
 *
 * **Construction**: use `OperatorIdentity.connectOrSpawn(options)`. The
 * factory connects to an existing host if one is running (via the
 * `~/.myco/anchor_surface/port.txt` discovery file) OR spawns a new host
 * using `options.hostBinary`.
 */
export class OperatorIdentity {
  /** The pubkey is fetched eagerly at construction time so existing
   *  synchronous-pubkey call sites keep working. Private seed is NOT here. */
  readonly publicKey: { readonly bytes: Uint8Array };
  private readonly client: AnchorSurfaceClient;

  private constructor(client: AnchorSurfaceClient, pubkey: Uint8Array) {
    this.client = client;
    this.publicKey = { bytes: pubkey };
  }

  /**
   * Connect to a running anchor_surface_host OR spawn one if `hostBinary`
   * is provided. Eagerly fetches the owner pubkey so synchronous-access
   * call sites (`identity.publicKey.bytes`) keep working.
   */
  static async connectOrSpawn(
    options: OperatorIdentityOptions = {},
  ): Promise<OperatorIdentity> {
    const client = await AnchorSurfaceClient.connectOrSpawn(options);
    try {
      const pubkey = await client.getPubkey();
      return new OperatorIdentity(client, pubkey);
    } catch (e) {
      await client.close().catch(() => undefined);
      throw e;
    }
  }

  /**
   * Static-style ergonomic alias preserved for backward-compat in call
   * sites that previously used `OperatorIdentity.loadOrCreate(keyDir?)`.
   *
   * **Behavior change**: the `keyDir` parameter is now interpreted as the
   * anchor_surface_host directory (not the legacy operator_keys directory).
   * Existing tests that pass a fresh tmpdir will get an isolated host
   * spawned (provided `MYCO_ANCHOR_SURFACE_BIN` is set in the environment
   * or `options.hostBinary` is supplied).
   *
   * Most call sites should switch to `connectOrSpawn` for clarity.
   */
  static async loadOrCreate(
    keyDir?: string,
    options: Omit<OperatorIdentityOptions, "dir"> = {},
  ): Promise<OperatorIdentity> {
    const hostBinary =
      options.hostBinary ??
      process.env.MYCO_ANCHOR_SURFACE_BIN ??
      undefined;
    return OperatorIdentity.connectOrSpawn({
      dir: keyDir,
      hostBinary,
      ...options,
    });
  }

  /** Public key bytes (32 bytes; copy). */
  publicKeyBytes(): Uint8Array {
    return new Uint8Array(this.publicKey.bytes);
  }

  /**
   * Sign a message. Now async — every sign performs a TCP round-trip to
   * the anchor_surface_host. Returns the 64-byte Ed25519 signature.
   */
  async sign(message: Uint8Array): Promise<Uint8Array> {
    return this.client.sign(message);
  }

  /**
   * **M-anchor-2 §9.2.1**: pass-through to AnchorSurfaceClient.birthAttest.
   * Used by `SubstrateClient.spawn` to fetch a birth attestation from the
   * anchor_surface_host before spawning a fresh substrate.
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
    return this.client.birthAttest(args);
  }

  /**
   * **M-anchor-3 §9.2.5**: pass-through to AnchorSurfaceClient.generateAnchorNonce.
   */
  async generateAnchorNonce(ttlSeconds: bigint): Promise<{
    nonce: Uint8Array;
    anchorTimestampUnixNs: bigint;
    expiryUnixNs: bigint;
    signature: Uint8Array;
  }> {
    return this.client.generateAnchorNonce(ttlSeconds);
  }

  /**
   * **M-anchor-3 §9.2.6**: pass-through to AnchorSurfaceClient.getAnchorWallClock.
   */
  async getAnchorWallClock(): Promise<{
    anchorTimestampUnixNs: bigint;
    signature: Uint8Array;
  }> {
    return this.client.getAnchorWallClock();
  }

  /**
   * **M-anchor-3 §9.2.7**: pass-through to AnchorSurfaceClient.heartbeat.
   */
  async heartbeat(): Promise<{
    anchorTimestampUnixNs: bigint;
    heartbeatNonce: Uint8Array;
    signature: Uint8Array;
  }> {
    return this.client.heartbeat();
  }

  /** Tear down the connection to the host (and kill the spawned host if
   *  this client spawned its own). Required for clean test teardown. */
  async close(): Promise<void> {
    await this.client.close();
  }
}
