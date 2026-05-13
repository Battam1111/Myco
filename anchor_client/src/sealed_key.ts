// Sealed-key access — TypeScript implementation (L1_GOVERNANCE §2.1).
//
// Per L1_GOVERNANCE §2.1: the owner's signing key MUST live outside the
// substrate's process boundary AND outside any process the agent can spawn
// or read memory of. **Specific mechanism is L4-picked** within:
//
// - Hardware security token (e.g., YubiKey, hardware-wallet-style devices).
// - Separate machine (sign on owner's primary device; submit signature).
// - Cloud HSM (AWS KMS, Azure Key Vault, GCP Cloud KMS with hardware backing).
// - Signed-prompt review on an isolated channel (owner reviews canonical
//   bytes on a separate device + signs there).
//
// The L1 invariant: the owner's private key never enters the substrate
// process's address space; substrate sees only signatures.
//
// ## M2 scope: in-memory stub
//
// `InMemorySealedKey` is the M2 development stub. It stores the owner
// private key in-process memory. **NOT PRODUCTION-SAFE.** Production
// anchor_client deployments MUST replace this with one of the L1_GOVERNANCE
// §2.1 candidate mechanisms.
//
// The SealedKey interface lets downstream code (heartbeat, attestation flow)
// remain agnostic to the backing storage: any conforming impl signs without
// exposing the private key.

import {
  Ed25519PrivateKey,
  Ed25519PublicKey,
  Ed25519Signature,
} from "./crypto.ts";

/** Errors. */
export class SealedKeyError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SealedKeyError";
  }
}

/**
 * Sealed-key interface — exposes only the public key and signing operation;
 * never returns the private key.
 *
 * Conforming implementations:
 *
 * - `InMemorySealedKey` (M2 stub).
 * - `TpmSealedKey` (M3+ — wraps TPM 2.0).
 * - `HardwareTokenSealedKey` (M3+ — wraps YubiKey or similar).
 * - `RemoteSignerSealedKey` (M3+ — owner signs on a separate machine).
 */
export interface SealedKey {
  /** The corresponding Ed25519 public key (publication-safe). */
  publicKey(): Ed25519PublicKey;

  /** Sign a message; the implementation MUST NOT expose the private key. */
  sign(message: Uint8Array): Ed25519Signature;
}

/**
 * In-memory sealed-key stub (M2 development).
 *
 * **NOT PRODUCTION-SAFE.** Holds the Ed25519 private key in JavaScript heap
 * memory; any process with access to the anchor_client memory can read it.
 *
 * Production anchor_client deployments MUST replace with one of:
 *
 * - `TpmSealedKey` (hardware TPM 2.0 with key sealed to PCRs).
 * - `HardwareTokenSealedKey` (FIDO U2F / WebAuthn / hardware-wallet).
 * - `RemoteSignerSealedKey` (separate machine; signed-prompt protocol).
 *
 * M2 tests + local dev use this stub.
 */
export class InMemorySealedKey implements SealedKey {
  private readonly privateKey: Ed25519PrivateKey;

  constructor(privateKey: Ed25519PrivateKey) {
    this.privateKey = privateKey;
  }

  /** Construct from a 32-byte seed. */
  static fromSeed(seed: Uint8Array): InMemorySealedKey {
    return new InMemorySealedKey(Ed25519PrivateKey.fromSeed(seed));
  }

  publicKey(): Ed25519PublicKey {
    return this.privateKey.publicKey();
  }

  sign(message: Uint8Array): Ed25519Signature {
    return this.privateKey.sign(message);
  }

  /** Redacted toString — never leaks private key. */
  toString(): string {
    return "InMemorySealedKey(<NOT PRODUCTION-SAFE>)";
  }

  /** Redacted JSON serialization. */
  toJSON(): string {
    return this.toString();
  }
}
