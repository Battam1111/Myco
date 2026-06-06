"""Myco v0.9 — kernel/governance.

Python implementation of the governance kernel per L3/PACKAGE_MAP §5.

Public surface (re-exported from the submodules for ergonomic imports):

- ``canonical_bytes`` — the cross-language canonical-bytes serializer
  (L1/SCHEMA §3.1): the typed :class:`Value` tree, :func:`encode` /
  :func:`decode`, and the ``expect_*`` accessors.
- ``crypto`` — BLAKE3 Merkle hashing, HMAC-SHA256, and Ed25519
  (L1/SCHEMA §2.1 + L1/SKIN §2). The cross-language signing primitives are
  retained (they back DAG hashing + the bridge HMAC + operator-side parity);
  v0.9 removed only the owner-key *usage*, not the primitive library.
- ``classifier`` — the I2 mutation classifier (L1/GOVERNANCE §1).
- ``schema_evolution`` — P3 schema-diff apply/rollback (L4 M17).

**v0.9 owner-key removal**: the ``owner_keys`` / ``owner_keys_persistence``
(owner-key history + on-disk persistence) and ``attestation`` (CI attestation
envelope protocol) submodules were removed with the rest of the
owner-key/anchor subsystem. CI mutations are accepted keyless.
"""

from __future__ import annotations

from myco_kernel_governance.canonical_bytes import (
    Array,
    Bool,
    Bytes,
    CanonicalBytes,
    CanonicalBytesError,
    Hash,
    Int,
    Map,
    Null,
    String,
    Timestamp,
    Uint,
    Value,
    decode,
    encode,
    expect_array,
    expect_bool,
    expect_bytes,
    expect_map,
    expect_string,
    expect_uint,
    map_get,
    read_varint,
    write_varint,
)
from myco_kernel_governance.classifier import (
    BACKUP_ENCRYPTION_STATUS_VALID_VALUES,
    FORBIDDEN_PRESERVE_ALL_MUTATION_TYPES,
    SEED_DIMENSION_TABLE,
    Classification,
    ClassifierContext,
    ClassifierRule,
    MutationEnvelope,
    classify,
    is_cultivator_preserve_all_attempt,
    is_valid_backup_encryption_status,
    matched_rules,
)
from myco_kernel_governance.crypto import (
    PUBLIC_KEY_LENGTH,
    SECRET_KEY_LENGTH,
    SIGNATURE_LENGTH,
    CryptoError,
    Ed25519PrivateKey,
    Ed25519PublicKey,
    Ed25519Signature,
    HmacEmptyKey,
    HmacInvalid,
    HmacTag,
    NodeHash,
    PrivateKeyMalformed,
    PublicKeyMalformed,
    SignatureInvalid,
    SignatureMalformed,
    hmac_sign,
    hmac_verify,
    merkle_hash,
    verify_signature,
)
from myco_kernel_governance.schema_evolution import (
    ApplyResult,
    SchemaDiff,
    SchemaDiffOp,
    SchemaEvolutionError,
    apply_schema_diff,
    parse_schema_diff,
    schema_diff_add_axis_bytes,
    schema_diff_modify_axis_threshold_bytes,
)

__version__ = "0.9.0a1"

__all__ = [
    "BACKUP_ENCRYPTION_STATUS_VALID_VALUES",
    "FORBIDDEN_PRESERVE_ALL_MUTATION_TYPES",
    "PUBLIC_KEY_LENGTH",
    "SECRET_KEY_LENGTH",
    "SEED_DIMENSION_TABLE",
    "SIGNATURE_LENGTH",
    "ApplyResult",
    "Array",
    "Bool",
    "Bytes",
    "CanonicalBytes",
    "CanonicalBytesError",
    "Classification",
    "ClassifierContext",
    "ClassifierRule",
    "CryptoError",
    "Ed25519PrivateKey",
    "Ed25519PublicKey",
    "Ed25519Signature",
    "Hash",
    "HmacEmptyKey",
    "HmacInvalid",
    "HmacTag",
    "Int",
    "Map",
    "MutationEnvelope",
    "NodeHash",
    "Null",
    "PrivateKeyMalformed",
    "PublicKeyMalformed",
    "SchemaDiff",
    "SchemaDiffOp",
    "SchemaEvolutionError",
    "SignatureInvalid",
    "SignatureMalformed",
    "String",
    "Timestamp",
    "Uint",
    "Value",
    "__version__",
    "apply_schema_diff",
    "classify",
    "decode",
    "encode",
    "expect_array",
    "expect_bool",
    "expect_bytes",
    "expect_map",
    "expect_string",
    "expect_uint",
    "hmac_sign",
    "hmac_verify",
    "is_cultivator_preserve_all_attempt",
    "is_valid_backup_encryption_status",
    "map_get",
    "matched_rules",
    "merkle_hash",
    "parse_schema_diff",
    "read_varint",
    "schema_diff_add_axis_bytes",
    "schema_diff_modify_axis_threshold_bytes",
    "verify_signature",
    "write_varint",
]
