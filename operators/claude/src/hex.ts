// Shared bytes→hex helper for the operators/claude package.
//
// Single source of truth for the lowercase, zero-padded (two hex digits per
// byte) encoding used across the operator runtime — both for human-readable
// tool responses (mcp_server.ts) and for the env-var hex triples handed to the
// spawned substrate (substrate_client.ts birth-attestation injection).
//
// Output contract (load-bearing — substrate-side decoders depend on it):
//   - lowercase hex
//   - exactly two hex digits per input byte (zero-padded)
//   - no separators, no `0x` prefix
//   - empty input → empty string

/** Convert a Uint8Array to a lowercase, zero-padded hex string. */
export function bytesToHex(bytes: Uint8Array): string {
  let s = "";
  for (const b of bytes) s += b.toString(16).padStart(2, "0");
  return s;
}

/** Parse a 64-character hex string into a 32-byte Uint8Array.
 *
 *  Inverse of {@link bytesToHex} for the 32-byte case. Shared by every MCP tool
 *  that accepts a `*_hash_hex` / `*_l0_hash_hex` / `tip_hash_hex` argument
 *  (raw_material link, dag_tip cosign, l0 revision, enumerate-since). Throws on a
 *  non-64-length input so a malformed hex surfaces as an error rather than a
 *  silently-truncated hash. `label` names the offending field in the message. */
export function hexTo32(hex: string, label = "value"): Uint8Array {
  if (hex.length !== 64) {
    throw new Error(
      `${label} must be 64 hex chars (32 bytes); got ${hex.length}`,
    );
  }
  const out = new Uint8Array(32);
  for (let i = 0; i < 32; i++) {
    out[i] = parseInt(hex.substring(i * 2, i * 2 + 2), 16);
  }
  return out;
}
