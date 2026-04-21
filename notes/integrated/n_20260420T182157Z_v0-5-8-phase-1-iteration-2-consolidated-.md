---
captured_at: '2026-04-20T18:21:57Z'
tags:
- v0.5.8
- audit
- iteration-2
- consolidation
source: agent
stage: integrated
integrated_at: '2026-04-21T05:19:20Z'
---
v0.5.8 Phase 1 Iteration 2 consolidated. 4 more opus lenses returned: Lens 5 Bitter-Lesson (0 P0 / 11 P1 / 6 P2 / 73 tools; 18-verb survival ranking at 2030 Claude tier: 10 clean / 4 degrade / 3 calcification candidates / 1 orthogonal; 8 missing bitter-lesson-friendly affordances M1-M8 named). Lens 6 Security (4 P0 / 10 P1 / 7 P2 / 76 tools; CRITICAL P0-SEC-1 unauthenticated RCE via .myco/plugins auto-exec_module; P0-SEC-2 overlay handler arbitrary import; P0-SEC-3 YAML alias bomb DoS 10B-leaf at 10 levels; P0-SEC-4 .env credential exfil via eat --path / forage). Lens 7 Performance (3 P0 / 5 P1 / 4 P2 / 89 tools; P0-01 first hunger 1-1.8s cold due to eager pypdf/PIL via adapter registry; P0-02 forage 5.5-6.4s due to .git traversal; P0-03 immune cache-miss 1.2s + SE1 2400x speedup via graph.nodes set-membership instead of Path.exists). Lens 8 Discipline (design-lens; proposed 14 new dims to catch 13/13 Iteration-1 findings mechanically: DC1 DC2 DC3 CS1 RL1 FR1 PA1 DC4 MB3 SE3 MP2 CG1 CG2 DI1; plus 4 PreToolUse variants + post-commit hook + 3 CI gates + 2 source fixes). Iter 1+2 totals: 20 P0 / 73+ P1 / 50 P2 / 801 tool uses / ~143 distinct issues. Iteration 3 launching with 4 targeted follow-up lenses: Lens 9 cross-verification (duplicate/sibling hunt, regression-risk in fix paths), Lens 10 platform/Windows/encoding (cp936/CRLF/UNC/reserved-names/ADS/Unicode-norm), Lens 11 migration/fresh-install (v0.5.6->v0.5.7 upgrade, pip install myco[mcp] cold, schema upgrader chain test), Lens 12 prompt-injection/Agent-trust boundary (hostile note content, brief sanitization, markdown injection vectors). Convergence criterion: Iter 3 total < 2 P0 and < 5 P1 across 4 lenses = STOP; else Iter 4 continues per 6-iter cap.
