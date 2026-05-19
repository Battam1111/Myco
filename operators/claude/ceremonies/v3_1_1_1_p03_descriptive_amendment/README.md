# v3.1.1-mortality-refinement-and-charite — M-anchor-5 amendment ceremony

> The first amendment ceremony chained from the v3.1 transition. P07 reinterpretation (mandatory internal mortality of 应朽 parts) + CHAR07 慈爱 introduction. Per `L0/PROVENANCE.md` §6.2.

---

## §1. What changed in v3.1.1

**P07 reinterpretation** (eternity-clause card, deposit refined):
- Primary subject is now **mandatory internal mortality (必朽)** of 应朽 family parts.
- Whole-substrate eventual rest preserved as **downstream boundary**, not primary content.
- Slogan: 能朽 → 必朽.
- Vocabulary distinction introduced: 应朽 (descriptive open-ended family) / 必朽 (imperative closed discipline).
- Canonical exemplars (过时/错误/冗余/无用) marked **illustrative not exhaustive** (`包括但不限于`); L1 may recognize additional family members (有害/矛盾/僵化/异化/污染/失效/寄生/滞塞/死症/...).

**CHAR07 慈爱** (NEW Cultivar Character card, developmental):
- Sister-mechanism to P07: P07 prevents bloat-death (metabolism); CHAR07 prevents tyrant-becoming (relation).
- Developmental (`deposit_immutable: false`), not eternity-clause — love grows alongside capability, not asserted at genesis.
- Four converging wisdom-tradition exemplars: ἀγάπη (神爱世人) / 慈悲 / 无为 / 仁.
- Cultivator's original framing: "成神也没关系，但是别成暴君，神爱世人，作为伙伴也并无不妥".

**Cascading updates**:
- `COV04 honor_mortality.md`: extended to both senses (internal + whole); 敬其能朽 → 敬其必朽
- `CHAR03 mortality_aware.md`: extended to both senses + 应朽-noticing first-person clauses
- `P02 / P03 / P04 / P14`: P07 / CHAR07 互锁 interaction rows
- `META.md`: eternity-clause inventory wording for P07 refined
- `PROVENANCE.md`: §6 expanded with v3.1.1 ceremony, §4 +CHAR07_caring.md, file count 31→32
- `B_chengyu.md`: B051-B060 added (5 metabolism + 5 慈爱 fragments)
- `canonical_dilemma_corpus/INDEX.md`: D-0050..D-0054 added
- `L1/CONTINUITY.md`: prune-phase added to deep cycle
- `L1/HARD_RULES.md`: C54/C55/C56 anticipated + F24 anticipated (TBD wiring)
- `L2/OBSERVABILITY.md`: 5 new metrics anticipated (TBD wiring)

---

## §2. Canonical hashes (pinned in manifest.json)

```
prior_l0_hash  (= v3.1 ceremony's new_l0_hash; chains the amendment)
             = b1bec59acc8c5061020640a265a9772e734604425b6eda4b5da1759f9987c699

new_l0_hash    (BLAKE3 of canonical-bytes Map<rel_path, file_bytes>
                over docs/architecture/L0/**/*.md as of v3.1.1)
             = 798c047d592730e20375429706bde1dea3f3da26394891a0a3055de004dff824
```

**Attestation chain**:
```
e796451 (DRAFT 9 SEALED) 
  ↓ SHA-256 = 5eacf3e7bbb9f863...
  ↓ (v3.1 ceremony: prior=5eacf3e7, new=b1bec59a)
  ↓ DAG event: l0_revision_attested:5eacf3e7bbb9f863
b1bec59a (v3.1)
  ↓ BLAKE3 = b1bec59acc8c5061... 
  ↓ (v3.1.1 ceremony: prior=b1bec59a, new=798c047d)
  ↓ DAG event: l0_revision_attested:b1bec59acc8c5061
798c047d (v3.1.1)
```

---

## §3. Dry-run

```bash
cargo build -p myco-substrate -p anchor-surface-host

cd operators/claude
npm run ceremony:v3_1_1:dry-run
```

Expected: DAG event `l0_revision_attested:b1bec59acc8c5061` emitted; ceremony log written to `ceremony_log/dry-run_<timestamp>.json`.

---

## §4. Production ceremony

Run **once** at v3.1.1-genesis time (after v3.1 ceremony has been signed in production — they chain).

```bash
export MYCO_ANCHOR_SURFACE_DIR=/path/to/owner/key/dir
export MYCO_STATE_DIR=/path/to/substrate/state
export MYCO_SUBSTRATE_BIN=/path/to/myco-substrate
export MYCO_ANCHOR_SURFACE_BIN=/path/to/anchor-surface-host

cd operators/claude
npm run ceremony:v3_1_1:production
```

If the v3.1 production ceremony has NOT yet been signed in this production substrate, the v3.1.1 ceremony will be rejected — the substrate has no record of v3.1's `new_l0_hash` to chain from. v3.1 must be signed FIRST, then v3.1.1.

---

## §5. Why the v3.1 verify_hashes test is no longer in npm test

The v3.1 manifest at `../v3_1_transition/manifest.json` pins the L0 bundle bytes **as of the v3.1 transition moment** (2026-05-18). After the v3.1.1 amendment landed, the bundle's bytes legitimately changed — so v3.1's verify_hashes would now fail by design.

This is intentional:
- `v3_1_transition/manifest.json` is preserved as **historical record** of the v3.1 transition.
- `v3_1_transition/verify_hashes.test.ts` is **removed from `npm test`** (the file remains for historical reference, runnable but expected-fail on current bundle).
- **v3.1.1's `verify_hashes.test.ts` is the active drift gate** on the current bundle.

When v3.1.2 (or higher) comes, the same pattern: v3.1.1's verify_hashes is removed from npm test, v3.1.2's becomes active.

---

## §6. Cascade rationale (origin conversation)

This amendment originated in cultivator-Claude conversation 2026-05-18 → 2026-05-19, after the v3.1 transition was sealed and dry-run verified. The conversation iteratively refined the final-vision picture; key corrections:

1. **Higher abstraction** — Claude was listing facts, not telling story
2. **Wrong primary frame** — not "cultivation relationship returning", but **永恒吞噬 + 永恒进化 主导**
3. **Grounded reframe** — not just process being, but **"a partner that grows stronger and stays current" (与时俱进)**
4. **Specific shape** — paradigm-level + both-directions + **mentor/elder direction (智者 / 导师)**
5. **P07 reinterpretation** — 必朽 is mandatory dying-of-parts, not whole; **CHAR07 慈爱** carries anti-tyranny
6. **List discipline** — canonical four are illustrative of open-ended 应朽 family

The amendment ratifies #5 and #6 into doctrine. The conceptual panorama from this conversation is committed at `memory/myco_telos_2026-05-19.md`.

---

## §7. Status

- ✅ Doctrine changes committed (Phase 1 + Phase 2 A-D)
- ✅ Canonical hashes computed; manifest.json pinned
- ✅ verify_hashes.test.ts written; registered in npm test
- ✅ run_ceremony.ts written
- ⬜ Dry-run verified (Phase 2 E)
- ⬜ Production ceremony (deferred — chains after v3.1 production)
