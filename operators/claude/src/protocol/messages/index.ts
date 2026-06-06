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
//                     (M22.5 / M23.2; v0.9 keyless, no owner-signed inputs).
//   cultivation.ts  — COV06 cultivator-mortality + succession FSM
//                     (update_successor_chain / accept_succession /
//                     accept_bet_retired_proposal). v0.9 keyless: the
//                     record_cultivator_heartbeat builder was removed.
//   observatory.ts  — query_substrate_observatory + Observatory* signal types.
//   ingest.ts       — ingest_raw_material + perturb_axis_from_raw_material (M16).
//   mutation.ts     — schema_diff builders, the spawn-cosign envelope builder,
//                     submit_mutation payload (v0.9 keyless: the attestation-
//                     nonce / REVEAL-key / DAG-tip-cosign / L0-revision builders
//                     were removed with the anchor surface).
//   responses.ts    — enumerate_dag_since + advance/snapshot/hello_ack/
//                     compute_intent/immune/submit_mutation/recent_nodes parsers.

export * from "./wire.ts";
export * from "./floats.ts";
export * from "./core.ts";
export * from "./reproduction.ts";
export * from "./federation.ts";
export * from "./mortality.ts";
export * from "./cultivation.ts";
export * from "./observatory.ts";
export * from "./ingest.ts";
export * from "./mutation.ts";
export * from "./responses.ts";
