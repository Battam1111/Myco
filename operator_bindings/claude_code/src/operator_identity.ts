// Operator identity — long-lived Ed25519 keypair persisted across sessions (L4 M9).
//
// ## Role
//
// The substrate's M5-M8 trust model was amnesiac: every MCP session generated
// a fresh `session_secret` and the substrate trusted whoever held the
// BOOTSTRAP_KEY. M9 introduces a persistent operator IDENTITY:
//
// - Each operator (each LLM-host installation) owns ONE long-lived Ed25519
//   keypair stored under `~/.myco/operator_keys/identity.key`.
// - On every `hello` to a substrate, the operator includes its public key
//   and a signature over the hello body.
// - The substrate pins the public key on first sight (TOFU — trust on
//   first use). Subsequent `hello` messages must present the same key OR
//   the substrate rejects them.
//
// ## Why this is the right M9
//
// M7 made substrate identity persistent. M8 made substrate memory
// persistent. M9 makes the **operator-substrate trust relationship**
// persistent. This is the foundation for M10+ classified-mutation flow
// (where the operator's signature on a classified mutation must trace back
// to a known identity, not a random session_secret).
//
// ## Doctrine
//
// - L1_SKIN §4.1 — per-handshake operator signing key (this is the IDENTITY
//   layer; the per-handshake REVEAL key for classified mutations is M10+).
// - L1_HARD_RULES C2 — handshake_pubkey_mismatch: rejection on pinned-key
//   divergence is the cross-process realization of this detector.
// - L1_GOVERNANCE §2.1 — owner's private key never enters substrate memory;
//   operator's private key never enters substrate memory either (this
//   module only ships the key over a sealed-derive interface to the
//   anchor surface; substrate sees only signatures + pubkey).

import {
  existsSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
} from "node:fs";
import { dirname, resolve as resolvePath } from "node:path";
import { homedir } from "node:os";
import { randomBytes } from "node:crypto";

import {
  Ed25519PrivateKey,
  Ed25519PublicKey,
  Ed25519Signature,
} from "@myco/anchor-client/src/crypto.ts";

/** Filename for the operator identity seed (32-byte raw Ed25519 seed). */
export const OPERATOR_IDENTITY_FILENAME = "identity.key";

/** Default directory for operator keys. */
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

/**
 * OperatorIdentity — the operator's long-lived Ed25519 identity.
 *
 * Held in memory only inside this class (the seed is never exposed via
 * accessors). On disk: `<keyDir>/identity.key` is the raw 32-byte seed.
 */
export class OperatorIdentity {
  private readonly privateKey: Ed25519PrivateKey;
  readonly publicKey: Ed25519PublicKey;

  private constructor(privateKey: Ed25519PrivateKey) {
    this.privateKey = privateKey;
    this.publicKey = privateKey.publicKey();
  }

  /**
   * Load the operator identity from `<keyDir>/identity.key`, or generate
   * and persist a fresh one if no file exists.
   *
   * The file mode is set to 0600 on Unix-like systems (read+write owner only).
   */
  static loadOrCreate(keyDir?: string): OperatorIdentity {
    const dir = keyDir ?? defaultOperatorKeyDir();
    const path = resolvePath(dir, OPERATOR_IDENTITY_FILENAME);
    if (existsSync(path)) {
      const seed = readFileSync(path);
      if (seed.length !== 32) {
        throw new OperatorIdentityError(
          `seed file ${path} has ${seed.length} bytes; expected 32`,
        );
      }
      return new OperatorIdentity(Ed25519PrivateKey.fromSeed(new Uint8Array(seed)));
    }
    // Generate fresh.
    const seed = randomBytes(32);
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, seed, { mode: 0o600 });
    return new OperatorIdentity(Ed25519PrivateKey.fromSeed(new Uint8Array(seed)));
  }

  /** Construct from an explicit seed (testing convenience). */
  static fromSeed(seed: Uint8Array): OperatorIdentity {
    return new OperatorIdentity(Ed25519PrivateKey.fromSeed(seed));
  }

  /** Public key bytes (32 bytes). */
  publicKeyBytes(): Uint8Array {
    return this.publicKey.bytes;
  }

  /** Sign a message. Returns 64-byte Ed25519 signature. */
  sign(message: Uint8Array): Uint8Array {
    const sig: Ed25519Signature = this.privateKey.sign(message);
    return sig.bytes;
  }
}
