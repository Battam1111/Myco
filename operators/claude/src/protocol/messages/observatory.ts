// Phase α / M24.5 — Living Bets observatory primitive.
//
// Split out of the former monolithic `protocol/messages.ts`. Mirrors
// `substrate::server::handle_query_substrate_observatory`. Supports
// format_versions 1 through 5; field name/type drift surfaces as decode errors.
// **v5 (OBSERVATORY gap)** adds `saturation_status` (P11.c), the CHAR07 keys
// (`char07_honest_disagreement` / `char07_capability_asymmetry` /
// `char07_flourishing`), and surfaces signal #4a's real cumulative fork count
// (was a 0n placeholder through v4). All v5 additions are additive — v4 clients
// keep parsing — and the new keys are surfaced as `raw` maps here for
// forward-compatible consumption.

import { type Value } from "@myco/anchor-client/src/canonical_bytes.ts";
import { BridgeProtocolError, type Message, MSG_TYPE } from "./wire.ts";

/** Build the payload for `query_substrate_observatory` (Phase α / M24.5).
 *
 *  `operatorAttestedContextWindowBytes` is optional. When supplied, the
 *  substrate computes signal #6 (read-window-relative position); otherwise
 *  signal #6 is omitted from the response.
 */
export function querySubstrateObservatoryPayload(args: {
  operatorAttestedContextWindowBytes?: bigint;
} = {}): Map<string, Value> {
  const m = new Map<string, Value>();
  if (args.operatorAttestedContextWindowBytes !== undefined) {
    m.set("operator_attested_context_window_bytes", {
      type: "uint",
      value: args.operatorAttestedContextWindowBytes,
    });
  }
  return m;
}

/** CHAR07 intake dimension — the two NOT-autonomously-observable dimensions
 *  the cultivator attests (§8.1 flourishing, §8.2 capability asymmetry). */
export type Char07Dimension =
  | "capability_asymmetry_pattern"
  | "flourishing_correlation";

/** Build the payload for `submit_char07_assessment` (CHAR07 §8.1/§8.2 intake).
 *  `valueRepr` is a repr-float string (cross-language determinism). The
 *  substrate records the attestation verbatim; it does not synthesize the
 *  underlying number (CHAR05). */
export function submitChar07AssessmentPayload(args: {
  dimension: Char07Dimension;
  valueRepr: string;
}): Map<string, Value> {
  const m = new Map<string, Value>();
  m.set("dimension", { type: "string", value: args.dimension });
  m.set("value_repr", { type: "string", value: args.valueRepr });
  return m;
}

/** Parsed `submit_char07_assessment_response`. */
export interface SubmitChar07AssessmentResult {
  recordedEventHash: Uint8Array;
  dimension: string;
  atCycle: bigint;
}

/** Parse a `submit_char07_assessment_response`. */
export function parseSubmitChar07AssessmentResponse(
  response: Message,
): SubmitChar07AssessmentResult {
  if (response.messageType !== MSG_TYPE.SUBMIT_CHAR07_ASSESSMENT_RESPONSE) {
    throw new BridgeProtocolError(
      `expected submit_char07_assessment_response; got ${response.messageType}`,
    );
  }
  const h = response.payload.get("recorded_event_hash");
  const d = response.payload.get("dimension");
  const c = response.payload.get("at_cycle");
  if (
    !h || h.type !== "bytes" ||
    !d || d.type !== "string" ||
    !c || c.type !== "uint"
  ) {
    throw new BridgeProtocolError(
      "submit_char07_assessment_response missing recorded_event_hash / dimension / at_cycle",
    );
  }
  return {
    recordedEventHash: h.value,
    dimension: d.value,
    atCycle: c.value,
  };
}

/** Signal #1 — persistence budget. Always present in v1+. */
export interface ObservatorySignal1 {
  dagNodeCount: bigint;
  dagEdgeCount: bigint;
  dagTotalContentBytes: bigint;
  manifestCycleCounter: bigint;
}

/** Signal #2 — evolution rate. Present from format_version >= 2. */
export interface ObservatorySignal2 {
  evolutionEventCount: bigint;
  axisRegisterCount: bigint;
  /** evolution_event_count / max(1, manifest_cycle_counter). */
  rate: number;
}

/** Signal #3 — read-pattern diversity. Present from format_version >= 2. */
export interface ObservatorySignal3 {
  distinctPerturbedAxesCount: bigint;
}

/** Signal #4 — federation health. Present from format_version >= 2. */
export interface ObservatorySignal4 {
  /** Cumulative count of `spore_emission:*` (fork) events. Real from v5
   *  (was a 0n placeholder through v4). Monotone-healthy — NOT counted in the
   *  bet-weakening quorum. */
  signal4aCumulativeForkCount: bigint;
  /** Currently-established peer count. */
  signal4bReachablePeerCount: bigint;
  /** Cumulative count of `federation_received:*` envelopes ingested. */
  eventsReceivedFromPeers: bigint;
}

/** Signal #5 — time trends (format_version >= 3). */
export interface ObservatorySignal5 {
  /** Raw substrate-private structure; surface untouched for forward-compat. */
  raw: Map<string, Value>;
}

/** Signal #6 — read-window-relative position. Present iff caller supplied
 *  operator_attested_context_window_bytes. */
export interface ObservatorySignal6 {
  substrateTotalBytes: bigint;
  operatorAttestedContextWindowBytes: bigint;
  /** substrate_total / context_window. Parsed from repr string; +Infinity when
   *  window=0 (substrate emits "inf"). */
  ratio: number;
}

/** **Signal #7 — compute per cycle (M26.2 P11.b)**. format_version >= 4.
 *  Wall-clock nanoseconds elapsed in the most recent metabolic cycle. */
export interface ObservatorySignal7 {
  /** Most recent cycle's compute_ns. 0n if no cycle has advanced yet. */
  currentCycleNs: bigint;
  /** Rolling arithmetic mean of compute_ns across the observatory history. */
  rollingMeanNs: number;
}

/** **Signal #8 — network per cycle (M26.2 P11.b)**. format_version >= 4.
 *  Federation egress wire bytes (4-byte length prefix + body) in the most
 *  recent metabolic cycle. */
export interface ObservatorySignal8 {
  /** Most recent cycle's egress bytes. */
  currentCycleBytes: bigint;
  /** Rolling arithmetic mean of network bytes across the history window. */
  rollingMeanBytes: number;
}

/** **Signal #9 — storage per cycle (M26.2 P11.b)**. format_version >= 4.
 *  Byte delta of `dag.cb` + `snapshot.cb` on disk in the most recent cycle. */
export interface ObservatorySignal9 {
  /** Most recent cycle's storage byte delta. */
  currentCycleBytes: bigint;
  /** Rolling arithmetic mean of storage delta across the history window. */
  rollingMeanBytes: number;
}

/** **Signal #10 — composite health score (M26.2)**. Renamed from
 *  `ObservatorySignal7` in earlier schemas. Composite blends signals
 *  1, 2, 4b, 7, 8, 9; production signals contribute positively, cost
 *  signals contribute negatively. Higher = healthier. */
export interface ObservatorySignal10 {
  compositeHealthScore: number;
  compositeFormatVersion: bigint;
  /** Per-signal weights (format_version >= 4 includes signals 7/8/9). */
  weights?: Map<string, number>;
  /** Method tag for the weight derivation (e.g. "emergent_variance"). */
  weightsMethod?: string;
}

/** Doctrine-instability burst status. NOT one of the 10 Living Bet signals
 *  — this is a C37 detector output. Pre-M26.2 schemas emitted this under the
 *  `signal_8_doctrine_revision_burst` key (a naming collision with the actual
 *  signal #8 introduced in M26.2). format_version >= 4 emits under
 *  `doctrine_revision_burst_status`. */
export interface ObservatoryDoctrineRevisionBurstStatus {
  /** Raw substrate-private structure; surface untouched for forward-compat. */
  raw: Map<string, Value>;
}

/** bet_weakening_quorum — composite L0/cards/LB_living_bets falsifiability counter
 *  (format_version >= 3). */
export interface ObservatoryBetWeakeningQuorum {
  raw: Map<string, Value>;
}

/** **P11.c saturation_status** (format_version >= 5). The live ordered-fallback
 *  state: stage + consecutive-cycle counters + per-axis exceeded flags. Surfaced
 *  raw for forward-compatible consumption. */
export interface ObservatorySaturationStatus {
  raw: Map<string, Value>;
}

/** **CHAR07 慈爱 anti-tyranny surface** (format_version >= 5). Three keys:
 *  the real `honest_disagreement` proxy (§8.4), and the cultivator-attested
 *  `capability_asymmetry` (§8.2) + `flourishing` (§8.1) INTAKE dimensions (each
 *  carrying a `source` field — "cultivator_attested" / "unavailable" /
 *  "telos_proxy"). Surfaced raw; the substrate never fabricates the un-observable
 *  dimensions (CHAR05). */
export interface ObservatoryChar07 {
  honestDisagreement: Map<string, Value>;
  capabilityAsymmetry: Map<string, Value>;
  flourishing: Map<string, Value>;
}

/** Parsed `query_substrate_observatory_response`. Supports format_versions
 *  1 through 4. **M26.2 (v4)** added signals 7/8/9 (cost), renamed the
 *  composite to signal_10, and decoupled doctrine_revision_burst_status
 *  from numbered Living Bet signals. Pre-v4 producers that still emit the
 *  old `signal_7_composite_health` key are parsed into `signal10` for
 *  forward compatibility. */
export interface ObservatorySnapshot {
  formatVersion: bigint;
  capturedAtUnixNs: bigint;
  signal1?: ObservatorySignal1;
  signal2?: ObservatorySignal2;
  signal3?: ObservatorySignal3;
  signal4?: ObservatorySignal4;
  signal5?: ObservatorySignal5;
  signal6?: ObservatorySignal6;
  /** Signal #7 cost (M26.2+); pre-M26.2 producers emit no signal_7
   *  `compute_per_cycle` key — this stays undefined. */
  signal7?: ObservatorySignal7;
  /** Signal #8 cost (M26.2+). */
  signal8?: ObservatorySignal8;
  /** Signal #9 cost (M26.2+). */
  signal9?: ObservatorySignal9;
  /** Composite #10 (M26.2+). Backward-compat: pre-v4 producers' old
   *  `signal_7_composite_health` key is also surfaced here. */
  signal10?: ObservatorySignal10;
  /** C37 detector status. Pre-v4 key `signal_8_doctrine_revision_burst`
   *  is also accepted (backward compat). */
  doctrineRevisionBurstStatus?: ObservatoryDoctrineRevisionBurstStatus;
  betWeakeningQuorum?: ObservatoryBetWeakeningQuorum;
  /** P11.c saturation state (format_version >= 5). */
  saturationStatus?: ObservatorySaturationStatus;
  /** CHAR07 anti-tyranny surface (format_version >= 5). Present iff all three
   *  char07_* keys decoded. */
  char07?: ObservatoryChar07;
}

export function parseQuerySubstrateObservatoryResponse(
  response: Message,
): ObservatorySnapshot {
  if (response.messageType !== MSG_TYPE.QUERY_SUBSTRATE_OBSERVATORY_RESPONSE) {
    throw new BridgeProtocolError(
      `expected query_substrate_observatory_response; got ${response.messageType}`,
    );
  }
  const verV = response.payload.get("observatory_format_version");
  const capturedV = response.payload.get("captured_at_unix_ns");
  if (
    !verV || verV.type !== "uint" ||
    !capturedV || capturedV.type !== "timestamp"
  ) {
    throw new BridgeProtocolError(
      "query_substrate_observatory_response missing observatory_format_version or captured_at_unix_ns",
    );
  }
  const snap: ObservatorySnapshot = {
    formatVersion: verV.value,
    capturedAtUnixNs: capturedV.value,
  };

  // Signal #1 (persistence budget) — always emitted from v1.
  const s1 = response.payload.get("signal_1_persistence_budget");
  if (s1 && s1.type === "map") {
    const m = s1.value;
    const nc = m.get("dag_node_count");
    const ec = m.get("dag_edge_count");
    const cb = m.get("dag_total_content_bytes");
    const cc = m.get("manifest_cycle_counter");
    if (
      nc && nc.type === "uint" &&
      ec && ec.type === "uint" &&
      cb && cb.type === "uint" &&
      cc && cc.type === "uint"
    ) {
      snap.signal1 = {
        dagNodeCount: nc.value,
        dagEdgeCount: ec.value,
        dagTotalContentBytes: cb.value,
        manifestCycleCounter: cc.value,
      };
    }
  }

  // Signal #2 (evolution rate) — format_version >= 2.
  const s2 = response.payload.get("signal_2_evolution_rate");
  if (s2 && s2.type === "map") {
    const m = s2.value;
    const ec = m.get("evolution_event_count");
    const ar = m.get("axis_register_count");
    const rr = m.get("rate_repr");
    if (
      ec && ec.type === "uint" &&
      ar && ar.type === "uint" &&
      rr && rr.type === "string"
    ) {
      snap.signal2 = {
        evolutionEventCount: ec.value,
        axisRegisterCount: ar.value,
        rate: parseFloat(rr.value),
      };
    }
  }

  // Signal #3 (read-pattern diversity).
  const s3 = response.payload.get("signal_3_read_pattern_diversity");
  if (s3 && s3.type === "map") {
    const m = s3.value;
    const dc = m.get("distinct_perturbed_axes_count");
    if (dc && dc.type === "uint") {
      snap.signal3 = { distinctPerturbedAxesCount: dc.value };
    }
  }

  // Signal #4 (federation health).
  const s4 = response.payload.get("signal_4_federation_health");
  if (s4 && s4.type === "map") {
    const m = s4.value;
    const fa = m.get("signal_4a_cumulative_fork_count");
    const fb = m.get("signal_4b_reachable_peer_count");
    const er = m.get("events_received_from_peers");
    if (
      fa && fa.type === "uint" &&
      fb && fb.type === "uint" &&
      er && er.type === "uint"
    ) {
      snap.signal4 = {
        signal4aCumulativeForkCount: fa.value,
        signal4bReachablePeerCount: fb.value,
        eventsReceivedFromPeers: er.value,
      };
    }
  }

  // Signal #5 (time trends) — substrate-private structure; preserved raw.
  const s5 = response.payload.get("signal_5_time_trends");
  if (s5 && s5.type === "map") {
    snap.signal5 = { raw: s5.value };
  }

  // Signal #6 (read-window-relative position) — present iff operator
  // supplied operator_attested_context_window_bytes in the request.
  const s6 = response.payload.get("signal_6_read_window_position");
  if (s6 && s6.type === "map") {
    const m = s6.value;
    const tb = m.get("substrate_total_bytes");
    const cw = m.get("operator_attested_context_window_bytes");
    const rr = m.get("ratio_repr");
    if (
      tb && tb.type === "uint" &&
      cw && cw.type === "uint" &&
      rr && rr.type === "string"
    ) {
      // Substrate emits "inf" when window=0; parseFloat returns NaN.
      const ratio = rr.value === "inf" ? Infinity :
        rr.value === "-inf" ? -Infinity :
          rr.value === "nan" ? NaN : parseFloat(rr.value);
      snap.signal6 = {
        substrateTotalBytes: tb.value,
        operatorAttestedContextWindowBytes: cw.value,
        ratio,
      };
    }
  }

  // -----------------------------------------------------------------------
  // **M26.2 P11.b** signals #7/#8/#9 (cost per cycle). format_version >= 4.
  // Each cost signal carries {current_cycle_*, rolling_mean_*_repr}.
  // -----------------------------------------------------------------------
  const s7Cost = response.payload.get("signal_7_compute_per_cycle");
  if (s7Cost && s7Cost.type === "map") {
    const m = s7Cost.value;
    const cur = m.get("current_cycle_ns");
    const meanRepr = m.get("rolling_mean_ns_repr");
    if (
      cur && cur.type === "uint" &&
      meanRepr && meanRepr.type === "string"
    ) {
      snap.signal7 = {
        currentCycleNs: cur.value,
        rollingMeanNs: parseFloat(meanRepr.value),
      };
    }
  }

  const s8Cost = response.payload.get("signal_8_network_per_cycle");
  if (s8Cost && s8Cost.type === "map") {
    const m = s8Cost.value;
    const cur = m.get("current_cycle_bytes");
    const meanRepr = m.get("rolling_mean_bytes_repr");
    if (
      cur && cur.type === "uint" &&
      meanRepr && meanRepr.type === "string"
    ) {
      snap.signal8 = {
        currentCycleBytes: cur.value,
        rollingMeanBytes: parseFloat(meanRepr.value),
      };
    }
  }

  const s9Cost = response.payload.get("signal_9_storage_per_cycle");
  if (s9Cost && s9Cost.type === "map") {
    const m = s9Cost.value;
    const cur = m.get("current_cycle_bytes");
    const meanRepr = m.get("rolling_mean_bytes_repr");
    if (
      cur && cur.type === "uint" &&
      meanRepr && meanRepr.type === "string"
    ) {
      snap.signal9 = {
        currentCycleBytes: cur.value,
        rollingMeanBytes: parseFloat(meanRepr.value),
      };
    }
  }

  // -----------------------------------------------------------------------
  // Signal #10 — composite health. M26.2 RENAMED from `signal_7_composite_health`.
  // Backward compat: pre-v4 producers still emit under the old key, so we
  // accept either and surface as `snap.signal10`.
  // -----------------------------------------------------------------------
  const s10 =
    response.payload.get("signal_10_composite_health") ??
    response.payload.get("signal_7_composite_health");
  if (s10 && s10.type === "map") {
    const m = s10.value;
    const sr = m.get("composite_health_score_repr");
    const fv = m.get("composite_format_version");
    if (
      sr && sr.type === "string" &&
      fv && fv.type === "uint"
    ) {
      const sig10: ObservatorySignal10 = {
        compositeHealthScore: parseFloat(sr.value),
        compositeFormatVersion: fv.value,
      };
      const wMap = m.get("weights");
      if (wMap && wMap.type === "map") {
        const weights = new Map<string, number>();
        for (const [k, v] of wMap.value) {
          if (v.type === "string") weights.set(k, parseFloat(v.value));
        }
        if (weights.size > 0) sig10.weights = weights;
      }
      const wm = m.get("weights_method");
      if (wm && wm.type === "string") sig10.weightsMethod = wm.value;
      snap.signal10 = sig10;
    }
  }

  // -----------------------------------------------------------------------
  // Doctrine-revision burst status. M26.2 RENAMED key from
  // `signal_8_doctrine_revision_burst` to `doctrine_revision_burst_status`
  // (the old key collided with M26.2 actual signal #8). Backward-compat:
  // also accept the old key for pre-v4 producers.
  // -----------------------------------------------------------------------
  const burst =
    response.payload.get("doctrine_revision_burst_status") ??
    response.payload.get("signal_8_doctrine_revision_burst");
  if (burst && burst.type === "map") {
    snap.doctrineRevisionBurstStatus = { raw: burst.value };
  }

  // bet_weakening_quorum (M25.2) — composite L0/cards/LB_living_bets falsifiability counter.
  const bq = response.payload.get("bet_weakening_quorum");
  if (bq && bq.type === "map") {
    snap.betWeakeningQuorum = { raw: bq.value };
  }

  // **v5 (OBSERVATORY gap)** — P11.c saturation_status.
  const sat = response.payload.get("saturation_status");
  if (sat && sat.type === "map") {
    snap.saturationStatus = { raw: sat.value };
  }

  // **v5 (OBSERVATORY gap)** — CHAR07 anti-tyranny surface. All three keys are
  // emitted together from v5; surface only when all three decode as maps.
  const hdd = response.payload.get("char07_honest_disagreement");
  const cap = response.payload.get("char07_capability_asymmetry");
  const flo = response.payload.get("char07_flourishing");
  if (
    hdd && hdd.type === "map" &&
    cap && cap.type === "map" &&
    flo && flo.type === "map"
  ) {
    snap.char07 = {
      honestDisagreement: hdd.value,
      capabilityAsymmetry: cap.value,
      flourishing: flo.value,
    };
  }

  return snap;
}
