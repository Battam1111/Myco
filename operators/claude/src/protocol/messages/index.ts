// Bridge wire protocol — module barrel (L4 M6).
//
// The former monolithic `protocol/messages.ts` was decomposed into a
// `messages/` module tree grouped by message family. This barrel re-exports
// every public symbol so existing imports of the form
// `import { X } from ".../protocol/messages.ts"` resolve UNCHANGED — the thin
// `protocol/messages.ts` shim re-exports from here.
//
// Module map:
//   wire.ts         — framing constants, MSG_TYPE, Message, error classes,
//                     body/HMAC/frame-body codec (the canonical-bytes core).
//   floats.ts       — floatRepr (shared float-repr wire helper).
//   core.ts         — hello / register_axis / perturb / advance / empty /
//                     query_recent_nodes / compute_intent request builders.
//   reproduction.ts — sprout_child (M20 永恒繁衍).
//   federation.ts   — federation_* builders + parsers (M22/M25.5 万物互联).
//   mortality.ts    — lift_birth_period_quarantine + accept_self_euthanasia
//                     (M22.5 / M23.2; owner-signed signing inputs).
//   observatory.ts  — query_substrate_observatory + Observatory* signal types.
//   ingest.ts       — ingest_raw_material + perturb_axis_from_raw_material (M16).
//   mutation.ts     — schema_diff builders, attestation-nonce, REVEAL-key
//                     binding, DAG-tip co-sign + L0-revision envelopes,
//                     submit_mutation payload.
//   responses.ts    — enumerate_dag_since + advance/snapshot/hello_ack/
//                     compute_intent/immune/submit_mutation/recent_nodes parsers.

export * from "./wire.ts";
export * from "./floats.ts";
export * from "./core.ts";
export * from "./reproduction.ts";
export * from "./federation.ts";
export * from "./mortality.ts";
export * from "./observatory.ts";
export * from "./ingest.ts";
export * from "./mutation.ts";
export * from "./responses.ts";
