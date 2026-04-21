---
captured_at: '2026-04-20T19:21:23Z'
tags:
- v0.5.8
- audit
- iteration-4
- consolidation
source: agent
stage: integrated
integrated_at: '2026-04-21T05:19:20Z'
---
v0.5.8 Iter 4 consolidated. 4 lenses: Lens 13 Race (4 P0 / 8 P1 / 113 tools / 19min - all reproduced: eat TOCTOU loses 70% of notes in concurrent writes; eat --path adapter loses 21% of files; molt write window crashes concurrent readers 240 times in 2s; reflect concurrent crash leaves disk orphan + permanent ContractError loop). Lens 14 Workflow E2E (5 P0 / 11 P1 / 10 P2 / 103 tools - all workflow-level: propagate-assimilate chain COMPLETELY broken n_ prefix mismatch = Myco core value prop nonfunctional; eat --path Windows-backslash YAML Unicode escape breaks all downstream assimilate; hunger never reports contract_drift; 3 eat silent-success modes; germinate / = raw traceback). Lens 15 Fix-conflict META (0 P0 / 0 P1 / 89 tools - consolidation output: 9 pair conflicts with mitigations; scope estimate ~620h=16 weeks total, Must-ship P0 only ~220h 3-week sprint, Should-ship 380h 5-week sprint, Stretch all 145+ NOT recommended; ~100 new test files needed; 14 new dims should split v0.5.8=≤5 + v0.5.9=rest; single atomic_write helper solves 4 race P0/P1). Lens 16 Scale (1 real P0 + 7 P1 / 103 tools / 27min - P0-16-01 cache-hit fingerprint linear in src size so 10k files = 9.2s per verb call = Lens 7 hoped-for O(1) cache is FALSE; Windows _getfinalpathname is 240us/path; Lens 7 extrapolations were 2-3x off; good news: no memory leak, test suite unaffected). Iter 4 total 10 P0 / ~21 P1; still far from <2/<5 convergence. Cumulative dedup ~39 P0 / ~110 P1 / 150+ distinct findings. Iter 5 launching with 4 follow-up lenses: 17 L0-principle-as-shipped, 18 observability/debuggability, 19 ecosystem-integration, 20 meta root-cause clustering.
