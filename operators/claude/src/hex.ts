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
