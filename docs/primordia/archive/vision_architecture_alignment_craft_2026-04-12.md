---
type: craft
status: ACTIVE
created: 2026-04-12
target_confidence: 0.90
current_confidence: 0.90
rounds: 2
craft_protocol_version: 1
decision_class: kernel_contract
---

# Vision + Architecture Alignment (Wave 58)

## §0 Problem

vision.md §四 comparison table predated Wave 55 (still showed "✅ 目标" for
self-model instead of operational status). architecture.md (v1.1) completely
omitted graph.py, cohorts.py, sessions.py — three load-bearing modules from
Waves 47-52.

## §1 Round 1

### D1: vision.md §四 table update
Changed column "元进化" → "内化选择" to reflect Wave 55 internalized
mutation-selection. Updated Myco row: self-model from "目标" to "A+B 运行中,
C/D 种子". Positioning line updated to mention hunger execute + scheduled task.

### D2: architecture.md Appendix F
Added ~80 lines documenting graph.py (F.1), cohorts.py (F.2), sessions.py (F.3),
and their composition (F.4) as a sensing pipeline feeding hunger signals.
Bumped version v1.1 → v1.2.

### D3: What NOT to change
vision.md §二 C2 ("human loses selection = cancer") is CORRECT. It describes
oversight capability (veto power), not day-to-day model. Wave 55 internalized
routine selection; C2 preserves the human emergency brake.

## §2 Round 2

### A1: "Architecture document is getting long"
Appendix F is additive (doesn't restructure existing pillars). The three
modules cut across pillars — they're instruments, not pillars themselves.

## §3 Conclusion
Both documents now reflect the Wave 47-55 reality. No contract bump needed
(docs-only changes, no contract surface semantics altered).
