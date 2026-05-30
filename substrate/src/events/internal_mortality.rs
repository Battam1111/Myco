//! **v3.1.1 P07 必朽 internal mortality** — tombstones for the 应朽 family.
//!
//! L0/cards/P07_mortality.md §3.3 mandates that every internal-mortality act
//! (pruning of a part that has entered 应朽 state) emits a tombstone DAG
//! event so the substrate REMEMBERS what was killed and why. Silent deletion
//! is forbidden (§5.2). The tombstone preserves causality (P06): the killed
//! part once existed; the substrate retains the record of its existence and
//! its cause-of-death even though its operative role has ended.
//!
//! The four canonical 应朽 family categories (illustrative not exhaustive per
//! P07 §2 / §3.1.c — `包括但不限于`):
//!   - 过时 (outdated)   — context-expiry / epoch-crossed
//!   - 错误 (wrong)      — falsified / contradicted
//!   - 冗余 (redundant)  — structural duplicate without disambiguation
//!   - 无用 (useless)    — zero-reachability / orphan past grace
//! L1-recognized family members (per F24 anticipated registry) may include:
//!   有害 / 矛盾 / 僵化 / 异化 / 污染 / 失效 / 寄生 / 滞塞 / 死症 / ...

use myco_kernel_shared::canonical_bytes::{encode as cb_encode, CanonicalBytes, Value};
use std::collections::BTreeMap;

/// **v3.1.1 P07 §3.3** prefix for `internal_mortality_event:{category}` DAG
/// nodes. Emitted every time the prune-scan kills a part that has entered
/// the 应朽 family. The category suffix is one of the canonical four
/// (`过时` / `错误` / `冗余` / `无用`) or an L1-recognized family member
/// name (registered via F24 应朽 detection rule registry).
///
/// Closes P07 §3.3 silent-deletion prohibition: every part-death MUST have
/// a tombstone in the DAG. C55 `silent_internal_mortality` fires if a part
/// becomes inactive without a corresponding tombstone.
pub const NODE_TYPE_INTERNAL_MORTALITY_EVENT_PREFIX: &str = "internal_mortality_event:";

/// **v3.1.1 P07 §3.3** encode an `internal_mortality_event:{category}` DAG
/// node content. Records the cause of part-death so the substrate
/// REMEMBERS even what it killed (P06 causality preserved through prune).
///
/// Content map (canonical-bytes Map):
/// ```ignore
/// {
///   "category": "无用",                            // family member name
///   "rule_id": "L0.seed.orphan_past_grace",        // which rule fired
///   "killed_part_hash": <32 bytes>,                // the dead part's hash
///   "killed_part_node_type": "raw_material:...",   // what kind of part
///   "reason": "string explanation",                // human-readable cause
///   "replaced_by_hash": <32 bytes or null>,        // if replacement exists
///   "emitted_at_cycle": uint,                      // when death happened
/// }
/// ```
///
/// Per L0/cards/P07_mortality.md §4.2.
pub fn encode_internal_mortality_event(
    category: &str,
    rule_id: &str,
    killed_part_hash: &[u8; 32],
    killed_part_node_type: &str,
    reason: &str,
    replaced_by_hash: Option<&[u8; 32]>,
    emitted_at_cycle: u64,
) -> CanonicalBytes {
    let mut m = BTreeMap::new();
    m.insert("category".to_string(), Value::String(category.to_string()));
    m.insert("rule_id".to_string(), Value::String(rule_id.to_string()));
    m.insert(
        "killed_part_hash".to_string(),
        Value::Bytes(killed_part_hash.to_vec()),
    );
    m.insert(
        "killed_part_node_type".to_string(),
        Value::String(killed_part_node_type.to_string()),
    );
    m.insert("reason".to_string(), Value::String(reason.to_string()));
    match replaced_by_hash {
        Some(h) => {
            m.insert(
                "replaced_by_hash".to_string(),
                Value::Bytes(h.to_vec()),
            );
        }
        None => {
            m.insert("replaced_by_hash".to_string(), Value::Null);
        }
    }
    m.insert(
        "emitted_at_cycle".to_string(),
        Value::Uint(emitted_at_cycle),
    );
    cb_encode(&Value::Map(m)).expect("internal_mortality_event encode infallible")
}

/// **v3.1.1 P07 §3.3** convenience: full `internal_mortality_event:{category}`
/// node_type string. Category is the 应朽 family member name (canonical
/// four or L1 extension).
pub fn internal_mortality_event_node_type(category: &str) -> String {
    format!("{NODE_TYPE_INTERNAL_MORTALITY_EVENT_PREFIX}{category}")
}
