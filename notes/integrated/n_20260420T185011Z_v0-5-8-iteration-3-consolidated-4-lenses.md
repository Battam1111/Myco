---
captured_at: '2026-04-20T18:50:11Z'
tags:
- v0.5.8
- audit
- iteration-3
- consolidation
source: agent
stage: integrated
integrated_at: '2026-04-21T05:19:20Z'
---
v0.5.8 Iteration 3 consolidated. 4 lenses returned: Lens 9 Cross-verify (2 P0 / 8 P1 / 88 tools; classification corrections: promoted L1 P1-01 + L6 P1-SEC-11 to P0; demoted L2 P0-8 + L1 P1-03 + L1 P1-08; new P0 NEW-M5 propagate zero write-surface check, NEW-C6 plugin second-layer importlib.import_module in template-generated __init__.py; 8 new P1 including molt changelog-without-canon-rollback, .env still in text_file._CODE_EXTS after SEC-4 fix, frontmatter YAML bomb cousin, substrate_id ASCII-only vs bilingual L0). Lens 10 Windows/encoding (4 P0 / 5 P1 / 116 tools / all reproduced on user Chinese Windows 10 cp936): P0-A stdin not reconfigured in ensure_utf8_stdio, P0-B myco-install fresh crashes on em-dash cp936 decode, P0-C Path('CON.md').write_text silent black-hole, P0-D all text=True subprocess.run in kernel break; CRLF pervasive with fingerprint cross-platform mismatch; .gitignore backslash silent miss. Lens 11 Migration (5 P0 / 12 P1 / 174 tools / 23min; crisis chain: germinate hardcodes v0.4.0-alpha.1 + no synced_contract_version in template + no kernel-vs-canon drift dim + hunger advice says deprecated 'reflect' + assimilate never writes synced_contract_version = every user after git pull completely blind to upgrade); Mac mini SSH confirmed stock Python 3.9.6 cannot install myco; molt regex eats blank line; changelog template uses deprecated 'myco bump'; pip uninstall leaves zombie MCP entries in 5 host configs. Lens 12 Prompt-injection (3 P0 / 5 P1 / 92 tools; all with verified payloads): P0-1 eat._render_note f-string YAML zero escaping enables frontmatter injection via --url source, P0-2 substrate_id never re-validated after genesis injects into every MCP pulse + brief markdown, P0-3 graph _is_external only matches http/https/mailto/#// misses javascript:/file:/data:/vbscript: laundering attacker URLs through immune+traverse. Iter 3 total 14 P0 / 30 P1 — far beyond <2/<5 convergence. Cumulative rough dedup ~29 P0 / ~88 P1. Iter 4 launching in verification mode: Lens 13 race/concurrency/determinism, Lens 14 fresh-agent workflow end-to-end, Lens 15 fix-conflict regression preview, Lens 16 scale/stress testing.
