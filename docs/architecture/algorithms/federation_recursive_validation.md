# Federation — Recursive Injection Defense

Canonical algorithm reference for **L2_FEDERATION §11** (SECURITY-CRITICAL).

## Why required

Without this defense, L2_FEDERATION §9.4 allowlist is bypassable via recursive nesting: the allowlist applies only to the OUTERMOST inner `node_type`. An attacker can smuggle a banned inner via nested `federation_received:` wrappers (matches own prefix → layered laundry).

## Attack

Malicious peer X builds inner `federation_received:peer_X/operator_pinned`; wraps in OUTER `federation_received:peer_Y`. Receiver §9.4 sees outer inner prefix-matches → accept. DAG now contains a wrapper attesting banned `operator_pinned` as observed-via-federation. Downstream P12 may mistake the smuggled claim as legitimate cross-substrate evidence.

## Defense (recursive inner validation)

```
function validate_federation_inner(content_canonical_bytes, depth, max_depth):
    if depth > max_depth:
        reject ("federation_recursive_depth_exceeded")
        emit C43_federation_recursive_injection (cascade_flag=true)
        return Rejected
    decoded = cb_decode(content_canonical_bytes)
    inner_node_type = decoded["peer_event_node_type"]
    if not is_federation_safe_node_type(inner_node_type):
        reject (inner_node_type)
        emit C35_federation_substrate_private_event_injection (cascade_flag=true, depth=depth)
        return Rejected
    if inner_node_type.starts_with("federation_received:"):
        return validate_federation_inner(decoded["peer_event_content_canonical_bytes"], depth + 1, max_depth)
    return Accepted

validate_federation_inner(outer_wrapper.content, depth=0, max_depth=L1_max_recursion_depth)
```

## Max depth

Seed `max_recursion_depth = 5`. Depth=0 = outermost. Depth-exceeded → reject OUTERMOST (partial acceptance forbidden). L1 may tighten (3) or relax (7); CI-attested.

## Rejection cascade

Reject ENTIRE outermost envelope (layers 0..N-1's testimony was *about* layer N).

Emit:

- C35 (banned inner at depth N: `cascade_flag=true, depth=N, inner_node_type=T, peer_substrate_id`).
- OR C43 (depth-exceeded: `attempted_depth=N+1, peer_substrate_id`).

Per-peer rate-limit (seed 3 rejections / 24 wall-clock hours) → `federation_peer_recursive_attack_burst` + propose peer revocation (below floor: owner-attested; above: P15 §6.5.b.1).

## C43 row

| ID | Name | P-cov | I-cov | Detector | Semantics |
|---|---|---|---|---|---|
| C43 | `federation_recursive_injection` | P9 + P15.guard | I8 | `myco_substrate/src/server.rs` (M27) | Depth exceeded; outermost rejected; `attempted_depth + peer_substrate_id` |

C43 vs C35: C35 = banned-type-at-some-depth; C43 = depth-exhaustion.

## Composition

- §11 extends §9.4 to every depth.
- §10 transport-auth irrelevant (content validation; a valid-FED_HELLO peer is still subject to §11).
- §6.5 quorum cert at depth-1 has allowlist-validated content + embedded `peer_votes` §10 Ed25519-verified — depth-bypass still fails signature verification.
