//! Validation tier dispatch (L1_SCHEMA §4).
//!
//! ## Doctrine
//!
//! Per L1_SCHEMA §4.1: two-tier validation policy:
//!
//! - **Tier 1 (identity-critical)** — validated every metabolic cycle.
//! - **Tier 2 (everything else)** — owner-triggered or per-deep-cycle.
//!
//! L4 may escalate to a 3-tier policy if tier-1 per-cycle validation
//! overruns cycle budget (per L1_SCHEMA §4.3); the shape is documented
//! there.
//!
//! ## Validator pattern
//!
//! The [`FieldValidator`] trait abstracts per-field validation logic. Each
//! consumer of `kernel/schema` (e.g., `kernel/governance` for classifier-
//! fixed-point fields, `kernel/skin` for surface declaration, etc.)
//! implements `FieldValidator` for its own field semantics.
//!
//! [`validate_ssot`] dispatches the validator over the appropriate tier
//! filter (Tier1 every cycle; Tier2 at deep cycles or owner trigger).
//!
//! ## M1 implementation
//!
//! Tier dispatch logic + trait. The L4 consumer-side validators land per
//! crate in M2+ (kernel/governance validates F-rows; kernel/skin validates
//! F11 skin surface; etc.).

use crate::ssot::{Ssot, SsotField, Tier};
use thiserror::Error;

/// Validation errors.
#[derive(Debug, Error, PartialEq, Eq)]
#[non_exhaustive]
pub enum ValidationError {
    /// A field failed validation. Carries the field name + a descriptive
    /// message for immune-sporocarp emission.
    #[error("validation failed for field {field}: {reason}")]
    FieldInvalid {
        /// Field name that failed.
        field: String,
        /// Reason / specific failure mode.
        reason: String,
    },

    /// SSoT designation requires a field that is missing
    /// (per L1_SCHEMA §1.2 designation enumerates which fields participate
    /// in consistency check).
    #[error("required field missing from SSoT: {0}")]
    RequiredFieldMissing(String),
}

/// Validation scope — which tier(s) to validate.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ValidationScope {
    /// Tier 1 only (per-cycle validation per L1_SCHEMA §4.1).
    Tier1,

    /// Tier 2 only (deep-cycle or owner-triggered per L1_SCHEMA §4.1).
    Tier2,

    /// Both tiers (full validation; typically owner-triggered).
    All,
}

/// Per-field validator trait.
///
/// Consumers of `kernel/schema` (e.g., `kernel/governance`, `kernel/skin`)
/// implement this for their field semantics. The trait is intentionally
/// minimal — a function from field to Result — so multiple validators can
/// be composed via [`CompositeValidator`].
pub trait FieldValidator {
    /// Validate a single SSoT field.
    ///
    /// Returns `Ok(())` on success; [`ValidationError`] on failure.
    fn validate(&self, field: &SsotField) -> Result<(), ValidationError>;
}

/// Compose multiple validators — runs each in order; first failure short-circuits.
///
/// Useful when multiple kernel layers each contribute their own validation
/// logic (e.g., kernel/governance + kernel/skin + kernel/tropism each provide
/// validators that the substrate composes into a single chain).
pub struct CompositeValidator<'a> {
    validators: Vec<&'a dyn FieldValidator>,
}

impl<'a> CompositeValidator<'a> {
    /// Empty composite.
    pub fn new() -> Self {
        CompositeValidator {
            validators: Vec::new(),
        }
    }

    /// Add a validator to the chain.
    pub fn add(mut self, v: &'a dyn FieldValidator) -> Self {
        self.validators.push(v);
        self
    }
}

impl<'a> Default for CompositeValidator<'a> {
    fn default() -> Self {
        CompositeValidator::new()
    }
}

impl<'a> FieldValidator for CompositeValidator<'a> {
    fn validate(&self, field: &SsotField) -> Result<(), ValidationError> {
        for v in &self.validators {
            v.validate(field)?;
        }
        Ok(())
    }
}

/// A no-op validator that always passes. Useful as a default + in tests.
pub struct PassValidator;

impl FieldValidator for PassValidator {
    fn validate(&self, _field: &SsotField) -> Result<(), ValidationError> {
        Ok(())
    }
}

/// Dispatch validator over the configured scope.
///
/// Per L1_SCHEMA §4.1:
/// - [`ValidationScope::Tier1`] — every cycle.
/// - [`ValidationScope::Tier2`] — deep-cycle or owner-triggered.
/// - [`ValidationScope::All`] — full pass; owner-triggered.
///
/// Returns the first validation failure encountered. To collect ALL failures
/// in a single pass (useful for batch reporting), use [`validate_ssot_collect`].
///
/// **Field-iteration order is unspecified.** [`Ssot`] is backed by a `HashMap`,
/// so the first-fired field on multi-failure runs is non-deterministic across
/// substrate restarts. For reproducible failure reporting use
/// [`validate_ssot_collect`], which surfaces ALL failures (the *set* of which
/// is deterministic even though emission order is not).
pub fn validate_ssot<V: FieldValidator>(
    ssot: &Ssot,
    scope: ValidationScope,
    validator: &V,
) -> Result<(), ValidationError> {
    for field in ssot.iter() {
        let include = match scope {
            ValidationScope::Tier1 => field.tier == Tier::Tier1,
            ValidationScope::Tier2 => field.tier == Tier::Tier2,
            ValidationScope::All => true,
        };
        if include {
            validator.validate(field)?;
        }
    }
    Ok(())
}

/// Like [`validate_ssot`] but collects all failures (does not short-circuit).
///
/// Returns a vec of failures (empty = full pass).
pub fn validate_ssot_collect<V: FieldValidator>(
    ssot: &Ssot,
    scope: ValidationScope,
    validator: &V,
) -> Vec<ValidationError> {
    let mut errors = Vec::new();
    for field in ssot.iter() {
        let include = match scope {
            ValidationScope::Tier1 => field.tier == Tier::Tier1,
            ValidationScope::Tier2 => field.tier == Tier::Tier2,
            ValidationScope::All => true,
        };
        if include {
            if let Err(e) = validator.validate(field) {
                errors.push(e);
            }
        }
    }
    errors
}

#[cfg(test)]
mod tests {
    use super::*;
    use myco_kernel_shared::canonical_bytes::Value;

    /// Test validator that fails on a specific field name.
    struct FailOnNameValidator {
        bad_name: String,
    }

    impl FieldValidator for FailOnNameValidator {
        fn validate(&self, field: &SsotField) -> Result<(), ValidationError> {
            if field.name == self.bad_name {
                Err(ValidationError::FieldInvalid {
                    field: field.name.clone(),
                    reason: "matches bad_name".to_string(),
                })
            } else {
                Ok(())
            }
        }
    }

    fn make_test_ssot() -> Ssot {
        let mut ssot = Ssot::new();
        ssot.set("a".into(), Tier::Tier1, Value::Uint(1)).unwrap();
        ssot.set("b".into(), Tier::Tier2, Value::Uint(2)).unwrap();
        ssot.set("c".into(), Tier::Tier1, Value::Uint(3)).unwrap();
        ssot
    }

    #[test]
    fn test_pass_validator_always_succeeds() {
        let ssot = make_test_ssot();
        validate_ssot(&ssot, ValidationScope::All, &PassValidator).unwrap();
    }

    #[test]
    fn test_fail_validator_short_circuits() {
        let ssot = make_test_ssot();
        let v = FailOnNameValidator {
            bad_name: "a".to_string(),
        };
        let result = validate_ssot(&ssot, ValidationScope::Tier1, &v);
        assert!(matches!(
            result,
            Err(ValidationError::FieldInvalid { field, .. }) if field == "a"
        ));
    }

    #[test]
    fn test_scope_tier1_skips_tier2_fields() {
        let ssot = make_test_ssot();
        // bad_name = "b" which is Tier2; validate only Tier1 → pass.
        let v = FailOnNameValidator {
            bad_name: "b".to_string(),
        };
        validate_ssot(&ssot, ValidationScope::Tier1, &v).unwrap();
    }

    #[test]
    fn test_scope_tier2_skips_tier1_fields() {
        let ssot = make_test_ssot();
        // bad_name = "a" which is Tier1; validate only Tier2 → pass.
        let v = FailOnNameValidator {
            bad_name: "a".to_string(),
        };
        validate_ssot(&ssot, ValidationScope::Tier2, &v).unwrap();
    }

    #[test]
    fn test_scope_all_visits_every_field() {
        let ssot = make_test_ssot();
        // bad_name = "b" (Tier2); All scope must catch.
        let v = FailOnNameValidator {
            bad_name: "b".to_string(),
        };
        let result = validate_ssot(&ssot, ValidationScope::All, &v);
        assert!(result.is_err());
    }

    #[test]
    fn test_validate_collect_returns_all_failures() {
        let mut ssot = Ssot::new();
        ssot.set("bad1".into(), Tier::Tier1, Value::Null).unwrap();
        ssot.set("good".into(), Tier::Tier1, Value::Null).unwrap();
        ssot.set("bad2".into(), Tier::Tier1, Value::Null).unwrap();

        struct AlwaysFailValidator;
        impl FieldValidator for AlwaysFailValidator {
            fn validate(&self, field: &SsotField) -> Result<(), ValidationError> {
                if field.name.starts_with("bad") {
                    Err(ValidationError::FieldInvalid {
                        field: field.name.clone(),
                        reason: "bad prefix".to_string(),
                    })
                } else {
                    Ok(())
                }
            }
        }

        let errors = validate_ssot_collect(&ssot, ValidationScope::Tier1, &AlwaysFailValidator);
        assert_eq!(errors.len(), 2);
    }

    #[test]
    fn test_composite_validator_chains() {
        let pass = PassValidator;
        let fail_a = FailOnNameValidator {
            bad_name: "a".to_string(),
        };

        let mut ssot = Ssot::new();
        ssot.set("a".into(), Tier::Tier1, Value::Null).unwrap();

        let composite = CompositeValidator::new().add(&pass).add(&fail_a);
        let result = validate_ssot(&ssot, ValidationScope::Tier1, &composite);
        assert!(matches!(result, Err(ValidationError::FieldInvalid { .. })));
    }

    #[test]
    fn test_composite_empty_passes_everything() {
        let composite = CompositeValidator::new();
        let mut ssot = Ssot::new();
        ssot.set("x".into(), Tier::Tier1, Value::Null).unwrap();
        validate_ssot(&ssot, ValidationScope::All, &composite).unwrap();
    }

    #[test]
    fn test_empty_ssot_passes_validation() {
        let ssot = Ssot::new();
        validate_ssot(&ssot, ValidationScope::All, &PassValidator).unwrap();
    }
}
