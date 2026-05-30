// Bridge wire protocol — TypeScript implementation (L4 M6).
//
// This file is a THIN BARREL. The implementation was decomposed into the
// `messages/` module tree (grouped by message family); see `messages/index.ts`
// for the module map. Every public symbol is re-exported here UNCHANGED so
// existing `import { X } from ".../protocol/messages.ts"` call sites keep
// resolving — the byte-exact wire contract lives in `messages/wire.ts`
// (framing + canonical-bytes body Map), `messages/floats.ts` (float repr),
// and the per-family modules.
//
// Mirror of Rust `kernel/bridge/rust/src/protocol.rs` and Python
// `kernel/bridge/python/src/myco_kernel_bridge/protocol.py`. The body Map
// shape, HMAC key derivation, and message types MUST match those modules
// byte-for-byte; any drift = L1/HARD_RULES C18 canonical_bytes_render_drift.
//
// ## Wire frame (length-prefixed)
//
// ```
//   [u32 BE length, 4 bytes][hmac, 32 bytes][body, length-32 bytes]
// ```
//
// Body = canonical-bytes Map with four keys (canonically sorted):
//
// - `v`: Uint(PROTOCOL_VERSION = 1)
// - `type`: String(message_type)
// - `request_id`: Uint(correlation_id)
// - `payload`: Map(type-specific)
//
// HMAC = HMAC-SHA256(body, key=session_secret). The `hello` message uses
// `BOOTSTRAP_KEY` instead of the (not-yet-exchanged) session_secret.

export * from "./messages/index.ts";
