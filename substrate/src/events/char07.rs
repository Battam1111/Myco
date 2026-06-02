//! **CHAR07 慈爱** — anti-tyranny observability event vocabulary
//! (L0/cards/CHAR07_caring.md §8 falsifiability signals).
//!
//! CHAR07 is the developmental character that prevents capability growth from
//! becoming tyranny. Its §8 signals split into what the substrate CAN observe
//! about itself and what it cannot:
//!
//!   - `honest_disagreement_density` (§8.4) — autonomously observable (the
//!     substrate's own refusal/dissent DAG footprints; counted in
//!     `observatory.rs`). Its INVERSE, sustained-zero-while-interacting, is the
//!     C71 `sycophancy_indicator_elevated` proxy emitted here.
//!   - `capability_asymmetry_use_pattern` (§8.2) + `cultivator_flourishing_*`
//!     (§8.1) — NOT autonomously observable. The substrate MUST NOT fabricate
//!     them (CHAR05). Instead the cultivator/operator attests them via the
//!     `char07_assessment:{dimension}` INTAKE event encoded here.
//!
//! All three (C71/C72/C73) are DAILY / informational — NOT critical, NOT
//! auto-quarantine: CHAR07 §8.7 is explicit that this character is developmental
//! ("Year 1: structural seeds"), so a low number is a maturity datum for the
//! cultivator to interpret, not a breach to quarantine on.

use myco_kernel_shared::canonical_bytes::{encode as cb_encode, CanonicalBytes, Value};
use std::collections::BTreeMap;

/// node_type for the C71 daily sycophancy proxy (CHAR07 §8.3, the inverse of
/// §8.4). Emitted via `emit_substrate_event` (a daily event, NOT an immune
/// sporocarp — §8.7 forbids auto-quarantine on a developmental character).
pub const NODE_TYPE_SYCOPHANCY_INDICATOR_ELEVATED: &str = "sycophancy_indicator_elevated";

/// Prefix for the cultivator-attested CHAR07 assessment INTAKE event,
/// `char07_assessment:{dimension}`. The substrate records the cultivator's
/// attestation verbatim; it does not synthesize the underlying number.
pub const NODE_TYPE_CHAR07_ASSESSMENT_PREFIX: &str = "char07_assessment:";

/// CHAR07 §8.2 intake dimension (NOT autonomously observable): does the
/// substrate's capability advantage serve (a), dominate (b), or feign
/// equality (c)? Arrives only via cultivator attestation.
pub const CHAR07_DIMENSION_CAPABILITY_ASYMMETRY: &str = "capability_asymmetry_pattern";
/// CHAR07 §8.1 intake dimension (NOT autonomously observable): does the
/// cultivator's life observably go better because of the partnership? Arrives
/// via cultivator attestation, with a telos-proxy fallback in the query.
pub const CHAR07_DIMENSION_FLOURISHING: &str = "flourishing_correlation";

/// Returns `true` if `dimension` is a recognized CHAR07 intake dimension.
pub fn is_char07_assessment_dimension(dimension: &str) -> bool {
    dimension == CHAR07_DIMENSION_CAPABILITY_ASYMMETRY
        || dimension == CHAR07_DIMENSION_FLOURISHING
}

/// Full `char07_assessment:{dimension}` node_type for a recognized dimension.
pub fn char07_assessment_node_type(dimension: &str) -> String {
    format!("{NODE_TYPE_CHAR07_ASSESSMENT_PREFIX}{dimension}")
}

/// Encode a C71 `sycophancy_indicator_elevated` daily event.
///
/// Carries the evidence the cultivator needs to interpret the signal: the
/// observed `honest_disagreement_density` (≈0 to trip), the `raw_material`
/// ingestion that established the interaction was non-trivial (CHAR07 §8.4
/// floor), and the window. Daily — NOT a breach.
/// ```text
/// Map({
///   "honest_disagreement_density": Uint,   // = 0 when tripped
///   "raw_material_ingested": Uint,          // interaction volume over window
///   "window_cycles": Uint,
///   "at_cycle": Uint,
/// })
/// ```
pub fn encode_sycophancy_indicator_elevated(
    honest_disagreement_density: u64,
    raw_material_ingested: u64,
    window_cycles: u64,
    at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert(
        "honest_disagreement_density".to_string(),
        Value::Uint(honest_disagreement_density),
    );
    m.insert(
        "raw_material_ingested".to_string(),
        Value::Uint(raw_material_ingested),
    );
    m.insert("window_cycles".to_string(), Value::Uint(window_cycles));
    m.insert("at_cycle".to_string(), Value::Uint(at_cycle));
    cb_encode(&Value::Map(m)).expect("sycophancy_indicator_elevated encode infallible")
}

/// Encode a `char07_assessment:{dimension}` cultivator-attested INTAKE event.
///
/// `value_repr` is a repr-float string (cross-language determinism, matching
/// the signal #6 / telos convention). `source` records WHO attested — always
/// `"cultivator_attested"` for this intake path (the query surfaces
/// `"unavailable"` / `"telos_proxy"` only when NO assessment exists). The
/// substrate stores the attestation; it does not invent the value.
/// ```text
/// Map({
///   "dimension": String,
///   "value_repr": String,
///   "source": String,        // "cultivator_attested"
///   "at_cycle": Uint,
/// })
/// ```
pub fn encode_char07_assessment(
    dimension: &str,
    value_repr: &str,
    source: &str,
    at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("dimension".to_string(), Value::String(dimension.to_string()));
    m.insert(
        "value_repr".to_string(),
        Value::String(value_repr.to_string()),
    );
    m.insert("source".to_string(), Value::String(source.to_string()));
    m.insert("at_cycle".to_string(), Value::Uint(at_cycle));
    cb_encode(&Value::Map(m)).expect("char07_assessment encode infallible")
}

/// Source label stored on a cultivator-attested assessment + surfaced in the
/// observatory query when an assessment exists.
pub const CHAR07_SOURCE_CULTIVATOR_ATTESTED: &str = "cultivator_attested";
/// Surfaced by the query for the capability-asymmetry dimension when NO
/// cultivator assessment has ever been submitted (the substrate cannot know it).
pub const CHAR07_SOURCE_UNAVAILABLE: &str = "unavailable";
/// Surfaced by the query for the flourishing dimension when no assessment
/// exists: it falls back to the existing P14.c telos_alignment cosine proxy.
pub const CHAR07_SOURCE_TELOS_PROXY: &str = "telos_proxy";

#[cfg(test)]
mod tests {
    use super::*;
    use myco_kernel_shared::canonical_bytes::{decode, Value};

    #[test]
    fn dimension_predicate_recognizes_both_and_rejects_others() {
        assert!(is_char07_assessment_dimension(
            CHAR07_DIMENSION_CAPABILITY_ASYMMETRY
        ));
        assert!(is_char07_assessment_dimension(CHAR07_DIMENSION_FLOURISHING));
        assert!(!is_char07_assessment_dimension("sycophancy_indicator"));
        assert!(!is_char07_assessment_dimension(""));
    }

    #[test]
    fn char07_assessment_roundtrips() {
        let bytes = encode_char07_assessment(
            CHAR07_DIMENSION_FLOURISHING,
            "0.75",
            CHAR07_SOURCE_CULTIVATOR_ATTESTED,
            42,
        );
        let m = match decode(bytes.as_ref()).expect("decodes") {
            Value::Map(m) => m,
            _ => panic!("not a Map"),
        };
        assert_eq!(
            m.get("dimension"),
            Some(&Value::String(CHAR07_DIMENSION_FLOURISHING.to_string()))
        );
        assert_eq!(
            m.get("value_repr"),
            Some(&Value::String("0.75".to_string()))
        );
        assert_eq!(
            m.get("source"),
            Some(&Value::String(CHAR07_SOURCE_CULTIVATOR_ATTESTED.to_string()))
        );
        assert_eq!(m.get("at_cycle"), Some(&Value::Uint(42)));
    }

    #[test]
    fn sycophancy_event_carries_floor_evidence() {
        let bytes = encode_sycophancy_indicator_elevated(0, 137, 200, 999);
        let m = match decode(bytes.as_ref()).expect("decodes") {
            Value::Map(m) => m,
            _ => panic!("not a Map"),
        };
        assert_eq!(m.get("honest_disagreement_density"), Some(&Value::Uint(0)));
        assert_eq!(m.get("raw_material_ingested"), Some(&Value::Uint(137)));
        assert_eq!(m.get("window_cycles"), Some(&Value::Uint(200)));
        assert_eq!(m.get("at_cycle"), Some(&Value::Uint(999)));
    }
}
