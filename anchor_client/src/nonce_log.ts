// Anchor-surface nonce log — TypeScript implementation (L1_GOVERNANCE §2.2 + §2.3).
//
// Per L1_GOVERNANCE §2.2 step 1: the anchor surface (NOT the substrate) issues
// single-use nonces, each bound at issuance to a declared
// (proposed_mutation_hash, dag_tip_hash) pair (closes pass-3 mycoparasite-5:
// nonces cannot be hoarded for later mutations).
//
// Per L1_GOVERNANCE §2.3 step 4: the anchor surface maintains the
// consumed-nonce log; substrate-side replay protection is non-authoritative.
//
// ## State machine
//
//                          issue_nonce()
//     [not issued] -------------------------> [issued]
//                                                |
//                                                | consume()  (mutation_hash + dag_tip + TTL match)
//                                                v
//                                            [consumed]
//                                                |
//                                                | issue_nonce() again
//                                                v
//                                          [reject: already used]
//
// ## M2 scope
//
// - In-memory log; M3+ persists via anchor-surface storage (file / DB /
//   hardware-token-paired storage; L4-picked).
// - Random nonces (32 bytes via Web Crypto API).
// - TTL via wall-clock; M3+ adds owner-attested-trusted-timestamp source.

import { NodeHash } from "./crypto.ts";

/** Standard nonce length (32 bytes). */
export const NONCE_LENGTH = 32;

/** Default nonce TTL (5 minutes per L1_GOVERNANCE §2.2 default). */
export const DEFAULT_NONCE_TTL_SECONDS = 5 * 60;

/** Default rate-limit window: max nonces per substrate per minute. */
export const DEFAULT_RATE_LIMIT_PER_MINUTE = 60;

/** Errors. */
export class NonceLogError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "NonceLogError";
  }
}

/** Nonce was never issued by this anchor surface. */
export class UnknownNonce extends NonceLogError {
  constructor(nonce: Uint8Array) {
    super(`unknown nonce: 0x${bytesToHex(nonce).substring(0, 16)}…`);
    this.name = "UnknownNonce";
  }
}

/** Nonce was already consumed (replay attempt). */
export class NonceAlreadyConsumed extends NonceLogError {
  constructor(nonce: Uint8Array) {
    super(`nonce already consumed: 0x${bytesToHex(nonce).substring(0, 16)}…`);
    this.name = "NonceAlreadyConsumed";
  }
}

/** Nonce binding mismatch (mutation_hash or dag_tip_hash doesn't match issuance). */
export class NonceBindingMismatch extends NonceLogError {
  constructor(field: string, nonce: Uint8Array) {
    super(
      `nonce binding mismatch (${field}): 0x${bytesToHex(nonce).substring(0, 16)}…`,
    );
    this.name = "NonceBindingMismatch";
  }
}

/** Nonce TTL expired. */
export class NonceExpired extends NonceLogError {
  constructor(nonce: Uint8Array) {
    super(`nonce TTL expired: 0x${bytesToHex(nonce).substring(0, 16)}…`);
    this.name = "NonceExpired";
  }
}

/** Rate-limit hit (per L1_GOVERNANCE §2.2: triggers
 * attestation_request_saturation owner-side observable). */
export class RateLimitExceeded extends NonceLogError {
  constructor(substrateId: string) {
    super(`nonce issuance rate limit exceeded for substrate: ${substrateId}`);
    this.name = "RateLimitExceeded";
  }
}

/** State of a previously-issued nonce. */
interface IssuedNonce {
  nonce: Uint8Array;
  substrateId: string;
  mutationHash: NodeHash;
  dagTipHash: NodeHash;
  issuedAtUnixSeconds: number;
  ttlSeconds: number;
}

/** Source of randomness (test-injectable). */
export interface RandomSource {
  randomBytes(n: number): Uint8Array;
}

/** Production randomness via Web Crypto (Node.js 22 has globalThis.crypto). */
export class WebCryptoRandomSource implements RandomSource {
  randomBytes(n: number): Uint8Array {
    const buf = new Uint8Array(n);
    globalThis.crypto.getRandomValues(buf);
    return buf;
  }
}

/** Deterministic fake source for tests.
 *
 * Encodes a 32-bit counter into the first 4 bytes of each generated buffer;
 * rest is zero. This guarantees uniqueness across calls (up to 2^32 calls)
 * which is what tests need. NOT cryptographically random — for tests only.
 */
export class FixedRandomSource implements RandomSource {
  private counter = 0;

  randomBytes(n: number): Uint8Array {
    this.counter++;
    const buf = new Uint8Array(n);
    if (n >= 4) {
      const view = new DataView(buf.buffer, buf.byteOffset, n);
      view.setUint32(0, this.counter, false);
    } else {
      // For very short buffers, just XOR counter into bytes.
      for (let i = 0; i < n; i++) {
        buf[i] = (this.counter >> (i * 8)) & 0xff;
      }
    }
    return buf;
  }
}

/** Source of wall-clock time (test-injectable). */
export interface ClockSource {
  unixSeconds(): number;
}

export class SystemClockSource implements ClockSource {
  unixSeconds(): number {
    return Math.floor(Date.now() / 1000);
  }
}

/** Manual clock for tests. */
export class FixedClockSource implements ClockSource {
  time: number;

  constructor(time: number) {
    this.time = time;
  }

  unixSeconds(): number {
    return this.time;
  }

  advance(seconds: number): void {
    this.time += seconds;
  }
}

/**
 * The anchor-surface nonce log.
 *
 * Per L1_HARD_RULES §4 (anchor-surface-resident state): the substrate cannot
 * author entries here. This module runs on the anchor-surface side only.
 */
export class NonceLog {
  /** Active issuances (issued but not yet consumed/expired). */
  private issued = new Map<string, IssuedNonce>();

  /** Consumed nonces — hex-encoded for Map keying. M3+ may bound this set
   * via expiry-purge; M2 retains all consumed nonces forever (memory-bounded
   * but unbounded over substrate lifetime). */
  private consumed = new Set<string>();

  /** Rate-limit tracking: per-substrate timestamps of recent issuances. */
  private issuancePerSubstrate = new Map<string, number[]>();

  private readonly random: RandomSource;
  private readonly clock: ClockSource;
  private readonly defaultTtlSeconds: number;
  private readonly rateLimitPerMinute: number;

  constructor(
    random: RandomSource = new WebCryptoRandomSource(),
    clock: ClockSource = new SystemClockSource(),
    defaultTtlSeconds: number = DEFAULT_NONCE_TTL_SECONDS,
    rateLimitPerMinute: number = DEFAULT_RATE_LIMIT_PER_MINUTE,
  ) {
    this.random = random;
    this.clock = clock;
    this.defaultTtlSeconds = defaultTtlSeconds;
    this.rateLimitPerMinute = rateLimitPerMinute;
  }

  /**
   * Issue a new nonce bound to (mutation_hash, dag_tip_hash).
   *
   * Per L1_GOVERNANCE §2.2 step 1: the anchor surface binds the nonce to
   * the declared mutation_hash + dag_tip_hash. Substrate cannot reuse the
   * nonce with a different mutation later.
   *
   * @throws {RateLimitExceeded} if the substrate exceeds rate-limit window.
   */
  issueNonce(
    substrateId: string,
    mutationHash: NodeHash,
    dagTipHash: NodeHash,
  ): Uint8Array {
    const now = this.clock.unixSeconds();

    // Rate-limit check.
    const recent = this.issuancePerSubstrate.get(substrateId) ?? [];
    const sinceOneMinute = recent.filter((t) => t > now - 60);
    if (sinceOneMinute.length >= this.rateLimitPerMinute) {
      throw new RateLimitExceeded(substrateId);
    }
    sinceOneMinute.push(now);
    this.issuancePerSubstrate.set(substrateId, sinceOneMinute);

    // Mint a fresh nonce.
    const nonce = this.random.randomBytes(NONCE_LENGTH);
    const key = bytesToHex(nonce);
    this.issued.set(key, {
      nonce,
      substrateId,
      mutationHash,
      dagTipHash,
      issuedAtUnixSeconds: now,
      ttlSeconds: this.defaultTtlSeconds,
    });
    return nonce;
  }

  /**
   * Consume a nonce. The substrate presents
   * `(nonce, mutation_hash, dag_tip_hash)`; this method validates the binding
   * matches the issuance + TTL is fresh + nonce hasn't been consumed.
   *
   * On success: marks the nonce as consumed and returns.
   *
   * @throws {UnknownNonce} if the nonce was never issued.
   * @throws {NonceAlreadyConsumed} if the nonce has been consumed before.
   * @throws {NonceBindingMismatch} if mutation_hash or dag_tip_hash differs
   *   from issuance.
   * @throws {NonceExpired} if TTL has elapsed.
   */
  consume(
    nonce: Uint8Array,
    expectedMutationHash: NodeHash,
    expectedDagTipHash: NodeHash,
  ): void {
    const key = bytesToHex(nonce);

    if (this.consumed.has(key)) {
      throw new NonceAlreadyConsumed(nonce);
    }
    const issued = this.issued.get(key);
    if (!issued) {
      throw new UnknownNonce(nonce);
    }
    if (!issued.mutationHash.equals(expectedMutationHash)) {
      throw new NonceBindingMismatch("mutation_hash", nonce);
    }
    if (!issued.dagTipHash.equals(expectedDagTipHash)) {
      throw new NonceBindingMismatch("dag_tip_hash", nonce);
    }
    const now = this.clock.unixSeconds();
    if (now > issued.issuedAtUnixSeconds + issued.ttlSeconds) {
      throw new NonceExpired(nonce);
    }

    // Mark consumed.
    this.issued.delete(key);
    this.consumed.add(key);
  }

  /** Check whether a nonce has been consumed (read-only). */
  isConsumed(nonce: Uint8Array): boolean {
    return this.consumed.has(bytesToHex(nonce));
  }

  /** Number of currently-issued (not yet consumed/expired) nonces. */
  issuedCount(): number {
    return this.issued.size;
  }

  /** Number of consumed nonces. */
  consumedCount(): number {
    return this.consumed.size;
  }

  /** Purge expired issuances (housekeeping; called periodically). */
  purgeExpired(): number {
    const now = this.clock.unixSeconds();
    let purged = 0;
    for (const [key, entry] of this.issued) {
      if (now > entry.issuedAtUnixSeconds + entry.ttlSeconds) {
        this.issued.delete(key);
        purged++;
      }
    }
    return purged;
  }
}

function bytesToHex(bytes: Uint8Array): string {
  let s = "";
  for (const b of bytes) {
    s += b.toString(16).padStart(2, "0");
  }
  return s;
}
