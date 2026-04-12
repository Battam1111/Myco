---
type: craft
status: ACTIVE
created: 2026-04-11
target_confidence: 0.90
current_confidence: 0.91
rounds: 3
craft_protocol_version: 1
decision_class: kernel_contract
---

# Upstream Scan Timestamp Write Path (Wave 16)

## 0. Problem definition

`_canon.yaml::system.upstream_scan_last_run` was added in contract v0.6.0
(Upstream Protocol v1.0, see `upstream_protocol_craft_2026-04-11.md` §473)
as a cached scan timestamp, and referenced in Wave 13's Boot Reflex Arc
proposal A7 as a potential `upstream_scan_stale` trigger. But there is
**no code path that ever writes it**. Every `_canon.yaml` and
`src/myco/templates/_canon.yaml` declares the field as `null`, and no
invocation of `myco upstream scan` updates it. This is a declared reflex
with no nervous system — exactly the hole Batch 4 was scoped to close.

A7 in `boot_reflex_arc_craft_2026-04-11.md` explicitly split this write
path out of Wave 13:

> "The `upstream_scan_last_run` write-path work is a separate fix
>  from Boot Reflex Arc itself — Batch 4."

This craft lands the fix.

## 1. Round 1 — Concept

### A1. Claim
After every successful `myco upstream scan` invocation, the kernel MUST
update `system.upstream_scan_last_run` in the local `_canon.yaml` to the
current UTC ISO-8601 timestamp. "Successful" = scan completed without
raising; it is allowed to return zero pending bundles.

### A2. Attack — Why write on zero-pending scans?
If a zero-pending scan still writes the timestamp, aren't we recording
"we scanned and found nothing" identically to "we scanned and found
10 bundles"? Doesn't that conflate two different states?

### A3. Defense
The timestamp records **freshness of the scan attempt**, not the scan
result. Downstream reflexes (Wave 13 A7 / future `upstream_scan_stale`
signal) want to answer "has the agent checked the inbox recently?", not
"has the agent found something recently?". Writing on zero-pending is
exactly right: the user scanned, found nothing, that's now known-fresh
information. Not writing would force agents to re-scan even when they
just scanned, which is worse.

### A4. Revise
Keep A1 as written. Add explicit comment in code: "timestamp records
scan freshness, not result." Add failure-mode rule: scan that raises
or aborts mid-way MUST NOT write the timestamp (partial scans are not
fresh, they're uncertain).

## 2. Round 2 — Design

### B1. Claim
Implementation uses a surgical regex-based line replacement on
`_canon.yaml`, NOT `yaml.dump()`. Preserves all comments, field order,
and user formatting. Write is best-effort: failure to update the
timestamp logs a warning but does NOT fail the scan.

### B2. Attack — Why not yaml.dump round-trip?
yaml.safe_load + yaml.dump is the "proper" Python way to mutate YAML
files. Regex line replacement is fragile; what if the user has
`upstream_scan_last_run` on a multi-line format, or has indented it
differently, or has a comment on the same line?

### B3. Defense
yaml.dump with PyYAML's default dumper **destroys all comments** and
reorders keys alphabetically unless using ruamel.yaml. The kernel's
`_canon.yaml` is heavily commented (Wave 8 rebaseline banner, W1/W5/W8
doctrine notes, severity justifications). Destroying those comments on
every scan would be a regression catastrophe. ruamel.yaml is a new
dependency we don't currently take. Therefore: surgical line edit with
a strict regex that matches exactly `^(\s*)upstream_scan_last_run\s*:\s*.*`
and replaces the value portion. If the regex fails to match (user has
reformatted the field), fail silently with a `[WARN]` message — scan
still succeeds.

### B4. Revise
Accept B3. Add invariant: the regex MUST match exactly one line in
`_canon.yaml`; if zero or multiple matches, bail out with warning. This
makes the update deterministic and catches canon corruption early.

## 3. Round 3 — Edges

### C1. Claim
Timestamp format is `YYYY-MM-DDTHH:MM:SSZ` (UTC, seconds precision,
no microseconds). Stored as a YAML string (quoted), not a YAML
timestamp scalar.

### C2. Attack — Why not YAML native timestamp?
YAML 1.1 has a native timestamp scalar type. Using a string means
readers must `datetime.fromisoformat()` it themselves. Why not let
PyYAML handle the conversion?

### C3. Defense
Three reasons: (1) PyYAML's `safe_load` returns native `datetime`
objects for YAML timestamps, which do not JSON-serialize — the
hunger report and MCP surface emit JSON and would need a converter.
(2) Strings survive round-trips through any YAML parser without
surprises; timestamps do not (YAML 1.1 vs 1.2 treat `2026-04-11` as
different types). (3) ISO-8601 strings are human-readable in the raw
file without parser assistance. D: string format with explicit `Z`
suffix, parsed with `datetime.fromisoformat(s.rstrip("Z"))` at
read-time.

### C4. Revise
Accept. Also specify: write path uses
`datetime.utcnow().replace(microsecond=0).isoformat() + "Z"`.
Read path (future consumers) should tolerate missing field (null
→ treat as "never scanned"), tolerate malformed string (log warn,
treat as null).

## 4. Conclusion extraction

Decisions:

- **D1**: Successful `myco upstream scan` updates
  `system.upstream_scan_last_run` to current UTC ISO-8601 string.
- **D2**: Zero-pending scans also write (freshness ≠ result).
- **D3**: Scans that raise mid-way do NOT write.
- **D4**: Implementation is surgical regex edit of `_canon.yaml`, not
  `yaml.dump` round-trip. Comments and formatting preserved.
- **D5**: Regex MUST match exactly one line. Zero or multiple → WARN,
  bail out, scan still succeeds.
- **D6**: Timestamp format: `YYYY-MM-DDTHH:MM:SSZ` (UTC, seconds, quoted
  string). Written as `"YYYY-MM-DDTHH:MM:SSZ"` in the YAML file.
- **D7**: No new contract lint dimension — the field already existed,
  this is only wiring the writer. Downstream `upstream_scan_stale`
  reflex is future work (not this craft).
- **D8**: Contract version bump: v0.14.0 → v0.15.0 (minor — new
  behavior, backward compatible). Downstream instances see drift on
  next boot per Wave 13 protocol.
- **D9**: Self-test — run `myco upstream scan` against kernel; verify
  timestamp appears in `_canon.yaml`; re-run lint expecting 16/16 green.

## 5. Landing checklist

- [x] Write this craft
- [ ] Add `_update_scan_timestamp(root)` helper in `src/myco/upstream_cmd.py`
- [ ] Call helper at end of successful `_cmd_scan`
- [ ] Bump contract version v0.14.0 → v0.15.0 in both `_canon.yaml` files
- [ ] Bump `synced_contract_version` in templates
- [ ] Add changelog entry for v0.15.0
- [ ] Self-test: `myco upstream scan` → inspect `_canon.yaml` diff
- [ ] `myco lint --project-dir .` → 16/16 green
- [ ] `myco eat` Wave 16 conclusion note → digest integrated
- [ ] Append Wave 16 milestone to `log.md`
- [ ] Commit + push via desktop-commander host-side

## 6. Known limitations

- L-1: The `upstream_scan_stale` reflex signal itself (consumer of this
  timestamp) is not implemented in this craft. This only writes the
  data; a future Wave will read it into a reflex arc.
- L-2: The regex depends on `upstream_scan_last_run:` living at a
  consistent indentation in `_canon.yaml`. If a user hand-edits the
  file to nest it differently, the writer fails gracefully (WARN, no
  crash). Next scan re-attempts.
- L-3: Sub-second precision is lost. For a scan frequency measured in
  hours to days, this is not a meaningful loss.
