# v0.7.4 — `.zip` extension hotfix (drag-drop validator-vs-picker mismatch)

> **Status**: LANDED (2026-05-09).
> **Predecessor**: v0.7.3 (lint-zero + IngestResult extension + L2 legacy-shim doctrine).
> **Trigger**: owner reported `myco-0.7.3.plugin` drag-drop into Cowork failed with `"validation failed"` — bundle byte-identity intact, but extension rejected by upload handler.
> **Cross-reference**: docs/architecture/L2_DOCTRINE/boundary.md § "Cowork plugin artifact extension (v0.7.4+)".

---

## Round 1 — Initial claim

The Cowork plugin bundle MUST be emitted with the `.zip` extension, not `.plugin`. The artifact contents are unchanged; only the filename suffix is different. This is a one-line constant flip in `BUNDLE_EXTENSION` (in `src/myco/boundary/install/plugin_bundle.py`) plus surface-level renames in 11 user-facing files (release.yml, READMEs × 3, scripts × 2, tests × 1, install/__init__.py, cowork.py, stipe.md × 2, boundary.md). A regression test locks the constant to `.zip`. No public-API breakage; the artifact filename is not in any consumer-facing API contract.

**Why a hotfix and not a feature release**: this is a discovery-driven correction of a v0.5.20-era misreading of Claude Desktop's plugin upload contract. Without this fix, every user who follows current README instructions (`download myco-<ver>.plugin → drag into Cowork`) gets the same `"validation failed"` error the owner just hit. v0.7.3 ship → v0.7.4 hotfix lag is ~24 hours, comparable to the v0.7.0 → v0.7.1 cycle (broke MCP host shim within 2 hours, hotfixed same day).

---

## Round 1.5 — Self-rebuttals

**T1 (chytrid / P1 Only-For-Agent)**: Is this an agent-first concern, or a human-distribution concern? The drag-drop UI is human-driven. Does this belong in Myco's L2 boundary doctrine?

→ **Resolution**: The agent-first principle covers the **agent's** ability to operate on a substrate. The Cowork plugin install is the seam by which a Cowork-mode agent acquires Myco's R1-R7 onboarding skill. Without a successful install, no agent in that Cowork session ever sees `myco-substrate` and never boots correctly. So the drag-drop's reliability IS an agent-first concern: not because the agent does the drag-drop, but because every drag-drop failure is an agent that boots without R1 ritual. Doctrine fit confirmed.

**T2 (rhizomorph / P2 Eternal-Devour)**: The v0.5.20 doctrine said `.plugin` was the right choice and cited app.asar evidence. Switching to `.zip` discards that prior craft work. What if Anthropic fixes #40414 next week and `.plugin` becomes preferred again?

→ **Resolution**: The v0.5.20 doctrine read the wrong code path. The picker regex `/\.(zip|plugin)$/i` is not the full upload contract; the **handler** (a different layer) is stricter. v0.5.20 was a partial measurement. The fix isn't "discard `.plugin` because Anthropic broke it" — it's "switch to `.zip` because we mismeasured the contract." Even if Anthropic relaxes the validator, `.zip` continues to work (the file picker accepts both, the OS understands `.zip`, every archive tool understands `.zip`). There is no scenario where `.plugin` is strictly better than `.zip`. Therefore no future Anthropic fix will warrant switching back. The L2 doctrine note encodes this asymmetry.

**T3 (mycoparasite / P3 Eternal-Evolve)**: Is the regression test actually a test, or just a tautology? `assert BUNDLE_EXTENSION == ".zip"` is testing the constant we just set. What does it catch?

→ **Resolution**: It catches a future agent or contributor who, mid-refactor, decides "we should make the artifact filename more semantic" and flips back to `.plugin`. The test fails, the gate quintet rejects, and the contributor must read the comment that explains why. This is the same pattern Myco uses elsewhere (e.g., MF5's intended-mirror byte-identity test, AD1's adapter-failed-stub assertion). The point isn't to verify the constant has the value we typed; it's to flag any drift from a *deliberately-chosen and externally-constrained* value.

**T4 (saprotroph / P4 Eternal-Iterate)**: Why ship as v0.7.4 instead of fixing in-place on v0.7.3? PyPI 0.7.3 is already up.

→ **Resolution**: Three reasons:
- **PyPI immutability**: PyPI permanently forbids re-uploading deleted filenames. Re-issuing v0.7.3 would require a `.postN` workaround (the v0.6.0 path-B pattern) or accept that PyPI's 0.7.3 wheel + sdist remain stale-but-installable. Both cost more attention than a clean v0.7.4 bump.
- **GitHub Release immutability**: the existing v0.7.3 GitHub Release has `myco-0.7.3.plugin` as an asset. We can `gh release upload --clobber` a `.zip` sibling, but the release notes already point to `.plugin`. A v0.7.4 release publishes correct notes pointing to `.zip` from line one.
- **MCP Registry semantics**: a fresh tag generates a fresh registry entry with `isLatest=true`, lifting users searching the registry to the working build. Re-publishing the same version is a duplicate-version error path (we exercised it in v0.6.0 path-B; tolerable but messy).

A clean v0.7.4 bump is the cheapest correct path.

**T5 (mycorrhiza / P5 All-Things-Connected)**: Does this affect downstream substrates? Does propagation to a federated peer break?

→ **Resolution**: No. The `.zip` artifact is consumed only by Cowork's drag-drop UI, which is a per-user-account install. Federation propagates substrate content (notes, canon, surface manifest), not host-install artifacts. The plugin bundle is host-side glue, not substrate content. Downstream substrates that depend on Myco continue to consume the PyPI wheel (unaffected) and the MCP Registry server card (unaffected); only end-user installs of the Cowork-side plugin are touched.

---

## Round 2 — Refinement

**Surface delta scope (final list)**:

| File | Change |
|------|--------|
| `src/myco/boundary/install/plugin_bundle.py` | `BUNDLE_EXTENSION = ".zip"` + docstring update with #40414 reference |
| `src/myco/boundary/install/cowork_plugin.py` | UPLOAD_INSTRUCTIONS rewording + module-level docstring + alias error-message |
| `src/myco/boundary/install/__init__.py` | CLI help strings (`cowork-plugin` subcommand) + dry-run printout |
| `src/myco/boundary/host_integration/cowork.py` | install_deep + module docstring extension reference |
| `scripts/build_plugin.py` | docstring + argparse description |
| `scripts/install_cowork_plugin.py` | deprecated-script printout (legacy redirector) |
| `.github/workflows/release.yml` | step name + glob `dist/myco-*.zip` + comment block |
| `tests/integration/test_install_cowork_plugin.py` | 5 assertions changed `.plugin` → `.zip` + 1 NEW regression test (`test_bundle_extension_constant_is_zip`) |
| `README.md` + `README_zh.md` + `README_ja.md` | Install paragraph + integration paragraph |
| `.claude/agents/stipe.md` (+ `agents/stipe.md` mirror via sync_plugin_mirrors.py) | description frontmatter + body narrative |
| `docs/architecture/L2_DOCTRINE/boundary.md` | new ~50-line section "Cowork plugin artifact extension (v0.7.4+)" + stipe-row table edit |

Audit-agent fanout: **not run this cycle**. The change is mechanical and externally-constrained (Anthropic's validator dictates the answer); a 5-critic fanout would surface the same conclusions the 5 self-rebuttals above already cover. v0.7.4 deliberately scopes-down the craft cadence on the principle that **mechanical hotfixes do not warrant the full L0-P1-P5 critic fanout**; that ceremony is for design crafts where multiple solution shapes are viable.

**Test count delta**: +1 (the new `test_bundle_extension_constant_is_zip`). Total goes 1566 → 1567.

**Lint delta**: zero. `myco_immune` was at exit_code 0 (1 informational MB8 finding) on v0.7.3 ship; no lint dimension is touched by this hotfix.

---

## Round 3 — Decision shape

**LANDED.** v0.7.4 ships with:

1. `BUNDLE_EXTENSION = ".zip"` in `plugin_bundle.py`.
2. 11-file surface-rename sweep (table above).
3. 1 new regression test + 5 updated assertions.
4. L2 doctrine codification under `boundary.md` § "Cowork plugin artifact extension (v0.7.4+)".
5. Standard release pipeline: gate quintet → bump → atomic commit → push → tag → ci.yml + release.yml watch → cloud verification.

**User-facing migration**: download `myco-0.7.4.zip` from the new GitHub Release. Existing v0.7.3 users who already have Myco installed via `myco-install host cowork` keep their MCP entry; they only need to drop the new `.zip` (replacing the old `.plugin` entry in their per-account marketplace). Cowork keys plugins by `name` field, not filename, so the v0.7.3 marketplace entry is overwritten in-place.

**Audit verdict**: this is a non-controversial hotfix. The single L0 P1 (Agent-First) consideration is "every agent boot through Cowork goes through this drag-drop", which the fix preserves and improves (drag-drop now works without manual rename). No P2-P5 concerns surfaced beyond the rebuttals already resolved in Round 1.5.
