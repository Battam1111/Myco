//! SSoT — Single Source of Truth (L1_SCHEMA §1 + L1_HARD_RULES F8).
//!
//! ## Doctrine
//!
//! Per L0 I3: the substrate maintains a self-validating SSoT against which
//! every cycle's state must be self-consistent. Per L1_SCHEMA §1.1: the
//! exact format is L4-picked within {YAML, TOML, JSON+JSONL, SQLite,
//! custom}. This module provides the abstraction layer.
//!
//! ## SSoT designation (F8 fixed-point)
//!
//! Per L1_SCHEMA §1.2: the **designation** lists which substrate state fields
//! participate in SSoT consistency check. Designation is contract-identity-
//! level (L1_HARD_RULES F8); migration is two-phase (L1_SCHEMA §1.3) requiring
//! ≥M cycles of dual-validation before owner co-signs. The set is open-ended
//! at L1; specific fields come from L1_GOVERNANCE classifier dimension table,
//! L1_TROPISM appetite axis schema, L1_SKIN surface declaration, etc.
//!
//! ## Validation tier classification (per L1_SCHEMA §4)
//!
//! - **Tier 1 (identity-critical)** — validated every metabolic cycle.
//!   Includes: substrate-ID, owner_key_history active prefix,
//!   anchor_surface_endpoint, DAG-tip-hash, classifier dimension table,
//!   classifier-fixed-point fields, mortality-signal threshold + update-rule,
//!   skin surface declaration, canonical-bytes serializer specification.
//! - **Tier 2 (everything else)** — owner-triggered or per-deep-cycle.
//!
//! ## Tiering discipline (per L1_SCHEMA §4.2 + pass-2 mycoparasite-26)
//!
//! - **New fields default to tier 1** (adversarial default forbidden).
//! - **Tier promotion** (tier 2 → tier 1) is daily-autonomous (more aggressive
//!   validation is always safe).
//! - **Tier demotion** (tier 1 → tier 2) is CI-gated (enforced at
//!   `kernel/governance`).
//!
//! M1: the SSoT struct stores fields with their tier; `set_tier`-style
//! mutations are accepted but the CI-gating + adversarial-default-rejection
//! enforcement is delegated to `kernel/governance` consumers in M2.

use myco_kernel_shared::canonical_bytes::{encode, CanonicalBytes, CanonicalBytesError, Value};
use std::collections::HashMap;
use thiserror::Error;

/// SSoT errors.
#[derive(Debug, Error, PartialEq, Eq)]
#[non_exhaustive]
pub enum SsotError {
    /// Field name is empty.
    #[error("field name cannot be empty")]
    EmptyFieldName,

    /// Caller attempted to look up a field that doesn't exist.
    /// Returned by `remove` / `get_tier` etc. The plain `get` returns
    /// `Option` instead of error.
    #[error("ssot field not found: {0}")]
    FieldNotFound(String),

    /// Canonical-bytes serialization error.
    #[error("canonical bytes: {0}")]
    CanonicalBytes(#[from] CanonicalBytesError),
}

/// Validation-tier classification (per L1_SCHEMA §4).
///
/// Per pass-2 mycoparasite-26: new fields default to [`Tier::Tier1`]; promotion
/// (Tier2 → Tier1) is daily-autonomous; demotion (Tier1 → Tier2) is CI-gated.
/// M1 stores the tier classification; CI-gating enforcement is M2 at
/// `kernel/governance`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum Tier {
    /// Identity-critical; validated every metabolic cycle.
    Tier1,
    /// Everything else; validated at deep-cycle or owner-triggered.
    Tier2,
}

/// A single SSoT field.
#[derive(Debug, Clone, PartialEq)]
pub struct SsotField {
    /// Field name (e.g., `"substrate_id"`, `"dag_tip_hash"`).
    pub name: String,

    /// Validation-tier classification.
    pub tier: Tier,

    /// Field value, encoded as a [`Value`] from kernel/shared::canonical_bytes.
    /// Storing as `Value` (not raw bytes) enables typed access AND
    /// deterministic canonical-bytes round-trip via [`encode`].
    pub value: Value,
}

/// In-memory SSoT representation.
///
/// ## M1 scope
///
/// - Per-field storage with tier classification.
/// - `set` + `get` + `remove` + tier-filtered iteration.
/// - Canonical-bytes serialization of full SSoT (for hashing).
///
/// ## M2 extensions
///
/// - Two-phase migration (per L1_SCHEMA §1.3).
/// - Designation evolution (CI-gated; `kernel/governance` classifier).
/// - On-disk persistence (L1_SCHEMA §1.1 format L4-pick).
/// - Cold-tier eligibility marking for tier-2 fields (L1_SCHEMA §2.3).
#[derive(Debug, Clone, Default)]
pub struct Ssot {
    fields: HashMap<String, SsotField>,
}

impl Ssot {
    /// Construct an empty SSoT.
    pub fn new() -> Self {
        Ssot::default()
    }

    /// Set a field (insert-or-update).
    ///
    /// Per pass-2 mycoparasite-26: new fields default to [`Tier::Tier1`];
    /// caller may override by passing the tier explicitly.
    pub fn set(&mut self, name: String, tier: Tier, value: Value) -> Result<(), SsotError> {
        if name.is_empty() {
            return Err(SsotError::EmptyFieldName);
        }
        self.fields.insert(
            name.clone(),
            SsotField {
                name,
                tier,
                value,
            },
        );
        Ok(())
    }

    /// Set a field with [`Tier::Tier1`] default (per
    /// L1_SCHEMA §4.2 pass-2 mycoparasite-26 — adversarial default forbidden).
    pub fn set_default_tier(&mut self, name: String, value: Value) -> Result<(), SsotError> {
        self.set(name, Tier::Tier1, value)
    }

    /// Look up a field by name.
    pub fn get(&self, name: &str) -> Option<&SsotField> {
        self.fields.get(name)
    }

    /// Get a field's tier classification (or error if not found).
    pub fn get_tier(&self, name: &str) -> Result<Tier, SsotError> {
        self.fields
            .get(name)
            .map(|f| f.tier)
            .ok_or_else(|| SsotError::FieldNotFound(name.to_string()))
    }

    /// Remove a field. Returns the removed field; errors if not found.
    ///
    /// **Note**: in M1, any caller can remove any field. M2 wires the CI-gate
    /// via `kernel/governance` classifier (mutating an F-row field, e.g.,
    /// `substrate_id` via F2, requires owner-attested CI envelope).
    pub fn remove(&mut self, name: &str) -> Result<SsotField, SsotError> {
        self.fields
            .remove(name)
            .ok_or_else(|| SsotError::FieldNotFound(name.to_string()))
    }

    /// Iterate over all fields in arbitrary order.
    pub fn iter(&self) -> impl Iterator<Item = &SsotField> {
        self.fields.values()
    }

    /// Iterate over tier-1 fields only (called every metabolic cycle for
    /// tier-1 validation per L1_SCHEMA §4.1).
    pub fn tier1_fields(&self) -> impl Iterator<Item = &SsotField> {
        self.fields.values().filter(|f| f.tier == Tier::Tier1)
    }

    /// Iterate over tier-2 fields only (called at deep-cycle for tier-2
    /// validation).
    pub fn tier2_fields(&self) -> impl Iterator<Item = &SsotField> {
        self.fields.values().filter(|f| f.tier == Tier::Tier2)
    }

    /// Total field count.
    pub fn field_count(&self) -> usize {
        self.fields.len()
    }

    /// Tier-1 field count.
    pub fn tier1_count(&self) -> usize {
        self.tier1_fields().count()
    }

    /// Tier-2 field count.
    pub fn tier2_count(&self) -> usize {
        self.tier2_fields().count()
    }

    /// Serialize the full SSoT to canonical bytes.
    ///
    /// Produces a canonical [`Value::Map`] keyed by field name → field value.
    /// Tier classification is NOT included in the canonical bytes — the
    /// canonical-bytes view of the SSoT is the field-value snapshot for
    /// consistency hashing; tier metadata is substrate-internal.
    ///
    /// Per L1_HARD_RULES F16: this serialization is governed by the
    /// canonical-bytes serializer spec (tier-1 SSoT field itself).
    pub fn to_canonical_bytes(&self) -> Result<CanonicalBytes, SsotError> {
        let mut m = std::collections::BTreeMap::new();
        for (name, field) in &self.fields {
            m.insert(name.clone(), field.value.clone());
        }
        encode(&Value::Map(m)).map_err(SsotError::from)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_new_ssot_is_empty() {
        let ssot = Ssot::new();
        assert_eq!(ssot.field_count(), 0);
        assert_eq!(ssot.tier1_count(), 0);
        assert_eq!(ssot.tier2_count(), 0);
    }

    #[test]
    fn test_set_and_get() {
        let mut ssot = Ssot::new();
        ssot.set(
            "substrate_id".to_string(),
            Tier::Tier1,
            Value::String("sub_001".to_string()),
        )
        .unwrap();
        let field = ssot.get("substrate_id").unwrap();
        assert_eq!(field.name, "substrate_id");
        assert_eq!(field.tier, Tier::Tier1);
        assert_eq!(field.value, Value::String("sub_001".to_string()));
    }

    #[test]
    fn test_get_unknown_returns_none() {
        let ssot = Ssot::new();
        assert!(ssot.get("missing").is_none());
    }

    #[test]
    fn test_empty_field_name_rejected() {
        let mut ssot = Ssot::new();
        let result = ssot.set("".to_string(), Tier::Tier1, Value::Null);
        assert_eq!(result, Err(SsotError::EmptyFieldName));
    }

    #[test]
    fn test_set_default_tier_is_tier1() {
        let mut ssot = Ssot::new();
        ssot.set_default_tier("x".to_string(), Value::Null).unwrap();
        assert_eq!(ssot.get_tier("x").unwrap(), Tier::Tier1);
    }

    #[test]
    fn test_set_overwrites() {
        let mut ssot = Ssot::new();
        ssot.set(
            "x".to_string(),
            Tier::Tier1,
            Value::String("v1".to_string()),
        )
        .unwrap();
        ssot.set(
            "x".to_string(),
            Tier::Tier2,
            Value::String("v2".to_string()),
        )
        .unwrap();
        let field = ssot.get("x").unwrap();
        assert_eq!(field.tier, Tier::Tier2);
        assert_eq!(field.value, Value::String("v2".to_string()));
        // Still only 1 field total.
        assert_eq!(ssot.field_count(), 1);
    }

    #[test]
    fn test_remove() {
        let mut ssot = Ssot::new();
        ssot.set("x".to_string(), Tier::Tier1, Value::Null).unwrap();
        let removed = ssot.remove("x").unwrap();
        assert_eq!(removed.name, "x");
        assert!(ssot.get("x").is_none());
        assert_eq!(ssot.field_count(), 0);
    }

    #[test]
    fn test_remove_unknown_errors() {
        let mut ssot = Ssot::new();
        let result = ssot.remove("missing");
        assert_eq!(
            result.unwrap_err(),
            SsotError::FieldNotFound("missing".into())
        );
    }

    #[test]
    fn test_tier_filtering() {
        let mut ssot = Ssot::new();
        ssot.set("a".into(), Tier::Tier1, Value::Null).unwrap();
        ssot.set("b".into(), Tier::Tier2, Value::Null).unwrap();
        ssot.set("c".into(), Tier::Tier1, Value::Null).unwrap();
        ssot.set("d".into(), Tier::Tier2, Value::Null).unwrap();
        ssot.set("e".into(), Tier::Tier1, Value::Null).unwrap();

        assert_eq!(ssot.field_count(), 5);
        assert_eq!(ssot.tier1_count(), 3);
        assert_eq!(ssot.tier2_count(), 2);

        let tier1_names: std::collections::HashSet<&str> = ssot
            .tier1_fields()
            .map(|f| f.name.as_str())
            .collect();
        assert!(tier1_names.contains("a"));
        assert!(tier1_names.contains("c"));
        assert!(tier1_names.contains("e"));
        assert!(!tier1_names.contains("b"));
        assert!(!tier1_names.contains("d"));
    }

    #[test]
    fn test_get_tier_unknown_errors() {
        let ssot = Ssot::new();
        let result = ssot.get_tier("missing");
        assert_eq!(
            result.unwrap_err(),
            SsotError::FieldNotFound("missing".into())
        );
    }

    #[test]
    fn test_to_canonical_bytes_deterministic() {
        let mut ssot = Ssot::new();
        ssot.set("a".into(), Tier::Tier1, Value::Uint(1)).unwrap();
        ssot.set("b".into(), Tier::Tier2, Value::Uint(2)).unwrap();
        let b1 = ssot.to_canonical_bytes().unwrap();
        let b2 = ssot.to_canonical_bytes().unwrap();
        assert_eq!(b1, b2);
    }

    #[test]
    fn test_to_canonical_bytes_excludes_tier_metadata() {
        // Two SSoTs with identical (name → value) but different tier
        // assignments produce identical canonical bytes (tier is substrate-
        // internal metadata, not part of the value-canonical view).
        let mut s1 = Ssot::new();
        s1.set("x".into(), Tier::Tier1, Value::Uint(42)).unwrap();
        let mut s2 = Ssot::new();
        s2.set("x".into(), Tier::Tier2, Value::Uint(42)).unwrap();
        assert_eq!(
            s1.to_canonical_bytes().unwrap(),
            s2.to_canonical_bytes().unwrap()
        );
    }

    #[test]
    fn test_canonical_bytes_changes_on_value_change() {
        let mut ssot = Ssot::new();
        ssot.set("x".into(), Tier::Tier1, Value::Uint(1)).unwrap();
        let b1 = ssot.to_canonical_bytes().unwrap();
        ssot.set("x".into(), Tier::Tier1, Value::Uint(2)).unwrap();
        let b2 = ssot.to_canonical_bytes().unwrap();
        assert_ne!(b1, b2);
    }
}
