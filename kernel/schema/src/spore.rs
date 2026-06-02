//! Spore-schema — substrate reproductive payload (L1/SCHEMA §3 + L0 P8 / I7).
//!
//! ## Doctrine
//!
//! Per L0 P8: substrate reproduces in three modes (federation / cloning /
//! cross-pollination). At reproduction-as-cloning, the parent constructs a
//! **spore-schema** carrying enough state for the child to begin its own
//! symbiosis.
//!
//! Per L1/SCHEMA §3.1: the spore-schema MUST include the following fields
//! (verified at construction; closure-checked at spawn per §3.3):
//!
//! 1. **schema_definitions** — SSoT structure spec.
//! 2. **canonical_bytes_serializer_spec** — pure-declarative serializer spec
//!    (L1/HARD_RULES F16). Spore-inheritable. All parties (operator, owner,
//!    child) need this for independent canonical-bytes derivation.
//! 3. **sporocarp_type_tree** (under L1/TROPISM dispatch) — atomic-record
//!    type hierarchy.
//! 4. **classifier_dimension_table** — L1/GOVERNANCE I2 classifier function
//!    as data.
//! 5. **initial_appetite_axis_schema** — gradient-update-rule signatures +
//!    threshold seeds.
//! 6. **anchor_surface_config** — where the owner's signing key lives;
//!    child's birth-attestation shape; substrate_secret sealing mechanism
//!    per L1/SKIN §4.2.
//! 7. **parent_immune_signal_summary** — counts of unresolved immune
//!    sporocarps by type + most-recent tip-hash.
//!
//! Per §3.2: the spore-schema does NOT include parent's full causal DAG, nor
//! operator-token history, nor accumulated read-pattern norms (per
//! L0 I1 + pass-1 saprotroph-10).
//!
//! ## Closure verification (per §3.3)
//!
//! At spawn:
//! 1. Parent runs static-schema validation (child's spore matches parent's
//!    current spore-schema-hash).
//! 2. Child runs its own I3 self-validation as its first metabolic cycle.
//! 3. Owner co-signs the spawn at the anchor surface
//!    (parent-substrate-ID, child-substrate-ID, spore-schema-hash, timestamp).
//!
//! Failure on any step aborts spawn BEFORE the federation link commits.
//!
//! ## M1 implementation
//!
//! Struct definition + canonical-bytes round-trip + hash computation +
//! shape validation (`validate_shape`). The closure protocol (parent
//! validation + child first-cycle I3 + owner co-sign) lands in M2 with
//! `kernel/governance` reproduction FSM.

use myco_kernel_shared::canonical_bytes::{encode, CanonicalBytes, CanonicalBytesError, Value};
use myco_kernel_shared::crypto::{merkle_hash, NodeHash};
use std::collections::BTreeMap;
use thiserror::Error;

/// Spore-schema errors.
#[derive(Debug, Error, PartialEq, Eq)]
#[non_exhaustive]
pub enum SporeError {
    /// A required field is `Value::Null` or otherwise empty.
    /// (Per L1/SCHEMA §3.1 all 7 fields must be present.)
    #[error("required spore field missing or null: {0}")]
    MissingRequiredField(&'static str),

    /// Canonical-bytes serialization error.
    #[error("canonical bytes: {0}")]
    CanonicalBytes(#[from] CanonicalBytesError),

    /// The decoded spore-schema canonical bytes are not the expected
    /// top-level shape (e.g., not a Map). Used by
    /// [`SporeSchema::validate_canonical_bytes_shape`] (P08 §3.5 I7(a)).
    #[error("malformed spore-schema: {0}")]
    MalformedSpore(&'static str),
}

/// The seven required spore-schema fields (per L1/SCHEMA §3.1).
///
/// Each field is a [`Value`] from kernel/shared::canonical_bytes for
/// type-uniformity. L4 layers populate with their domain types serialized
/// to `Value` (e.g., `Value::Map` for table-shaped fields).
///
/// L1/SCHEMA §3.1 commits the **shape** (seven named fields); the exact
/// internal structure of each `Value` is determined by the consuming kernel
/// layer at L4.
#[derive(Debug, Clone, PartialEq)]
pub struct SporeSchema {
    /// SSoT structure spec (per L1/SCHEMA §3.1 field 1).
    pub schema_definitions: Value,

    /// Pure-declarative canonical-bytes serializer specification
    /// (per L1/SCHEMA §3.1 field 2 + F16). Must be runnable by any party
    /// that has the spec — no runtime-dependent primitives.
    pub canonical_bytes_serializer_spec: Value,

    /// Sporocarp type tree (per L1/SCHEMA §3.1 field 3 under L1/TROPISM
    /// dispatch).
    pub sporocarp_type_tree: Value,

    /// Classifier dimension table (per L1/SCHEMA §3.1 field 4 — the I2
    /// classifier function as data).
    pub classifier_dimension_table: Value,

    /// Initial appetite-axis schema (per L1/SCHEMA §3.1 field 5).
    pub initial_appetite_axis_schema: Value,

    /// Anchor-surface configuration (per L1/SCHEMA §3.1 field 6 — where
    /// the owner's signing key lives; child's birth-attestation shape;
    /// substrate_secret sealing mechanism per L1/SKIN §4.2).
    pub anchor_surface_config: Value,

    /// Parent immune-signal summary (per L1/SCHEMA §3.1 field 7 — counts
    /// of unresolved immune sporocarps by type + most-recent tip-hash).
    /// Spawning while parent has unresolved immune sporocarps puts child
    /// in quarantined birth period until owner re-attests intent.
    pub parent_immune_signal_summary: Value,
}

impl SporeSchema {
    /// Validate that all 7 required fields are present (non-Null).
    ///
    /// Per L1/SCHEMA §3.1: all 7 fields must be present. M1 enforcement is
    /// `!matches!(field, Value::Null)`; M2 may strengthen to type-shape checks
    /// (e.g., `classifier_dimension_table` must be `Value::Map`).
    pub fn validate_shape(&self) -> Result<(), SporeError> {
        if matches!(self.schema_definitions, Value::Null) {
            return Err(SporeError::MissingRequiredField("schema_definitions"));
        }
        if matches!(self.canonical_bytes_serializer_spec, Value::Null) {
            return Err(SporeError::MissingRequiredField(
                "canonical_bytes_serializer_spec",
            ));
        }
        if matches!(self.sporocarp_type_tree, Value::Null) {
            return Err(SporeError::MissingRequiredField("sporocarp_type_tree"));
        }
        if matches!(self.classifier_dimension_table, Value::Null) {
            return Err(SporeError::MissingRequiredField(
                "classifier_dimension_table",
            ));
        }
        if matches!(self.initial_appetite_axis_schema, Value::Null) {
            return Err(SporeError::MissingRequiredField(
                "initial_appetite_axis_schema",
            ));
        }
        if matches!(self.anchor_surface_config, Value::Null) {
            return Err(SporeError::MissingRequiredField("anchor_surface_config"));
        }
        if matches!(self.parent_immune_signal_summary, Value::Null) {
            return Err(SporeError::MissingRequiredField(
                "parent_immune_signal_summary",
            ));
        }
        Ok(())
    }

    /// Canonical-bytes representation of the spore-schema.
    ///
    /// Per L1/SCHEMA §3.3 step 1: parent uses this to compute the
    /// spore-schema-hash that the child verifies against.
    pub fn to_canonical_bytes(&self) -> Result<CanonicalBytes, SporeError> {
        let mut m = BTreeMap::new();
        m.insert(
            "schema_definitions".to_string(),
            self.schema_definitions.clone(),
        );
        m.insert(
            "canonical_bytes_serializer_spec".to_string(),
            self.canonical_bytes_serializer_spec.clone(),
        );
        m.insert(
            "sporocarp_type_tree".to_string(),
            self.sporocarp_type_tree.clone(),
        );
        m.insert(
            "classifier_dimension_table".to_string(),
            self.classifier_dimension_table.clone(),
        );
        m.insert(
            "initial_appetite_axis_schema".to_string(),
            self.initial_appetite_axis_schema.clone(),
        );
        m.insert(
            "anchor_surface_config".to_string(),
            self.anchor_surface_config.clone(),
        );
        m.insert(
            "parent_immune_signal_summary".to_string(),
            self.parent_immune_signal_summary.clone(),
        );
        encode(&Value::Map(m)).map_err(SporeError::from)
    }

    /// Spore-schema hash (BLAKE3 of canonical bytes).
    ///
    /// Per L1/SCHEMA §3.3 step 1 + L0/cards/AS_anchor_surface §3 owner-co-sign: this hash binds
    /// (parent-substrate-ID, child-substrate-ID, spore-schema-hash, timestamp)
    /// in the spawn co-sign envelope.
    pub fn hash(&self) -> Result<NodeHash, SporeError> {
        let cbytes = self.to_canonical_bytes()?;
        Ok(merkle_hash(&[], cbytes.as_ref()))
    }

    /// **P08 §3.5 / L1/SCHEMA §3.3 step 1 — I7(a) static-schema validation.**
    ///
    /// Validate a spore-schema directly from its canonical-bytes form, as the
    /// parent does at spawn-closure: the child's `spore_schema_canonical_bytes`
    /// (supplied by the operator + co-signed by the cultivator) must decode to
    /// a Map carrying all seven required fields, each present (non-Null).
    ///
    /// This is the no-struct-reconstruction path used by the substrate's
    /// `verify_spawn_co_attestation`: it does not need the typed `SporeSchema`
    /// back, only the static-shape guarantee that the co-signed schema is
    /// well-formed (so a child cannot be birthed against a malformed /
    /// truncated spore-schema). Returns `Err(MissingRequiredField)` naming the
    /// first absent field; the substrate maps any error → C68 reject.
    ///
    /// Mirrors [`SporeSchema::validate_shape`] field-for-field so the typed
    /// and bytes paths agree.
    pub fn validate_canonical_bytes_shape(bytes: &[u8]) -> Result<(), SporeError> {
        use myco_kernel_shared::canonical_bytes::decode;
        let v = decode(bytes).map_err(SporeError::from)?;
        let m = match v {
            Value::Map(m) => m,
            _ => return Err(SporeError::MalformedSpore("spore-schema is not a Map")),
        };
        // The seven required fields, in the same source order as
        // `validate_shape` (so the first-missing diagnostics match).
        const REQUIRED: [&str; 7] = [
            "schema_definitions",
            "canonical_bytes_serializer_spec",
            "sporocarp_type_tree",
            "classifier_dimension_table",
            "initial_appetite_axis_schema",
            "anchor_surface_config",
            "parent_immune_signal_summary",
        ];
        for field in REQUIRED {
            match m.get(field) {
                None | Some(Value::Null) => {
                    return Err(SporeError::MissingRequiredField(field));
                }
                Some(_) => {}
            }
        }
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Construct a fully-populated test spore.
    fn make_full_spore() -> SporeSchema {
        SporeSchema {
            schema_definitions: Value::String("schema_v1".to_string()),
            canonical_bytes_serializer_spec: Value::String("cb_spec_v1".to_string()),
            sporocarp_type_tree: Value::Array(vec![
                Value::String("genesis".to_string()),
                Value::String("delta".to_string()),
            ]),
            classifier_dimension_table: Value::Map({
                let mut m = BTreeMap::new();
                m.insert(
                    "appetite_axis".to_string(),
                    Value::String("daily".to_string()),
                );
                m
            }),
            initial_appetite_axis_schema: Value::Array(vec![Value::String("axis_a".to_string())]),
            anchor_surface_config: Value::Map({
                let mut m = BTreeMap::new();
                m.insert("endpoint_pubkey".to_string(), Value::Bytes(vec![0xab; 32]));
                m
            }),
            parent_immune_signal_summary: Value::Map({
                let mut m = BTreeMap::new();
                m.insert("unresolved_count".to_string(), Value::Uint(0));
                m.insert("most_recent_tip_hash".to_string(), Value::Hash([0xcd; 32]));
                m
            }),
        }
    }

    #[test]
    fn test_validate_shape_full_ok() {
        let spore = make_full_spore();
        spore.validate_shape().unwrap();
    }

    #[test]
    fn test_validate_shape_missing_schema_definitions() {
        let mut spore = make_full_spore();
        spore.schema_definitions = Value::Null;
        assert_eq!(
            spore.validate_shape().unwrap_err(),
            SporeError::MissingRequiredField("schema_definitions")
        );
    }

    #[test]
    fn test_validate_shape_missing_serializer_spec() {
        let mut spore = make_full_spore();
        spore.canonical_bytes_serializer_spec = Value::Null;
        assert_eq!(
            spore.validate_shape().unwrap_err(),
            SporeError::MissingRequiredField("canonical_bytes_serializer_spec")
        );
    }

    #[test]
    fn test_validate_shape_missing_sporocarp_type_tree() {
        let mut spore = make_full_spore();
        spore.sporocarp_type_tree = Value::Null;
        assert_eq!(
            spore.validate_shape().unwrap_err(),
            SporeError::MissingRequiredField("sporocarp_type_tree")
        );
    }

    #[test]
    fn test_validate_shape_missing_classifier_table() {
        let mut spore = make_full_spore();
        spore.classifier_dimension_table = Value::Null;
        assert_eq!(
            spore.validate_shape().unwrap_err(),
            SporeError::MissingRequiredField("classifier_dimension_table")
        );
    }

    #[test]
    fn test_validate_shape_missing_appetite_schema() {
        let mut spore = make_full_spore();
        spore.initial_appetite_axis_schema = Value::Null;
        assert_eq!(
            spore.validate_shape().unwrap_err(),
            SporeError::MissingRequiredField("initial_appetite_axis_schema")
        );
    }

    #[test]
    fn test_validate_shape_missing_anchor_config() {
        let mut spore = make_full_spore();
        spore.anchor_surface_config = Value::Null;
        assert_eq!(
            spore.validate_shape().unwrap_err(),
            SporeError::MissingRequiredField("anchor_surface_config")
        );
    }

    #[test]
    fn test_validate_shape_missing_immune_summary() {
        let mut spore = make_full_spore();
        spore.parent_immune_signal_summary = Value::Null;
        assert_eq!(
            spore.validate_shape().unwrap_err(),
            SporeError::MissingRequiredField("parent_immune_signal_summary")
        );
    }

    #[test]
    fn test_validate_shape_multiple_nulls_first_fires() {
        // When ALL 7 fields are null, the first-listed in source order
        // (schema_definitions) fires. Documents the validate_shape ordering
        // semantics for downstream callers.
        let spore = SporeSchema {
            schema_definitions: Value::Null,
            canonical_bytes_serializer_spec: Value::Null,
            sporocarp_type_tree: Value::Null,
            classifier_dimension_table: Value::Null,
            initial_appetite_axis_schema: Value::Null,
            anchor_surface_config: Value::Null,
            parent_immune_signal_summary: Value::Null,
        };
        assert_eq!(
            spore.validate_shape().unwrap_err(),
            SporeError::MissingRequiredField("schema_definitions")
        );
    }

    #[test]
    fn test_to_canonical_bytes_deterministic() {
        let spore = make_full_spore();
        let b1 = spore.to_canonical_bytes().unwrap();
        let b2 = spore.to_canonical_bytes().unwrap();
        assert_eq!(b1, b2);
    }

    #[test]
    fn test_hash_deterministic() {
        let spore = make_full_spore();
        let h1 = spore.hash().unwrap();
        let h2 = spore.hash().unwrap();
        assert_eq!(h1, h2);
    }

    #[test]
    fn test_hash_changes_on_content_change() {
        let spore1 = make_full_spore();
        let mut spore2 = spore1.clone();
        spore2.schema_definitions = Value::String("different_schema".to_string());
        assert_ne!(spore1.hash().unwrap(), spore2.hash().unwrap());
    }

    #[test]
    fn test_validate_canonical_bytes_shape_full_ok() {
        // P08 §3.5 I7(a): the bytes-path validator accepts a fully-populated
        // spore-schema's canonical bytes (agrees with validate_shape).
        let spore = make_full_spore();
        let bytes = spore.to_canonical_bytes().unwrap();
        SporeSchema::validate_canonical_bytes_shape(bytes.as_ref()).unwrap();
    }

    #[test]
    fn test_validate_canonical_bytes_shape_missing_field_rejects() {
        // A spore-schema whose canonical bytes omit a required field is
        // rejected naming that field — the substrate maps this → C68.
        let mut spore = make_full_spore();
        spore.classifier_dimension_table = Value::Null;
        let bytes = spore.to_canonical_bytes().unwrap();
        assert_eq!(
            SporeSchema::validate_canonical_bytes_shape(bytes.as_ref()).unwrap_err(),
            SporeError::MissingRequiredField("classifier_dimension_table")
        );
    }

    #[test]
    fn test_validate_canonical_bytes_shape_non_map_rejects() {
        // Bytes that decode to a non-Map → MalformedSpore (not a panic).
        let bytes = encode(&Value::String("not a spore map".to_string())).unwrap();
        assert!(matches!(
            SporeSchema::validate_canonical_bytes_shape(bytes.as_ref()).unwrap_err(),
            SporeError::MalformedSpore(_)
        ));
    }

    #[test]
    fn test_validate_canonical_bytes_shape_garbage_bytes_rejects() {
        // Non-canonical-bytes garbage → CanonicalBytes decode error (no panic).
        assert!(SporeSchema::validate_canonical_bytes_shape(b"\xff\xff not cb").is_err());
    }

    #[test]
    fn test_canonical_bytes_includes_all_7_fields() {
        // Construct a spore with distinct values per field; verify each
        // contributes to the canonical bytes.
        let spore = make_full_spore();
        let cb_full = spore.to_canonical_bytes().unwrap();

        // Now mutate ONE field and verify cb changes.
        let mut spore_mutated = spore.clone();
        spore_mutated.sporocarp_type_tree = Value::Array(vec![]); // changed
        let cb_mutated = spore_mutated.to_canonical_bytes().unwrap();
        assert_ne!(cb_full, cb_mutated);
    }
}
