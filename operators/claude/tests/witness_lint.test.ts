// Witness lint — L0 Layer C drift guard (META §5.5, existence-level).
//
// META §5.5 mandates a CI lint that "walks all card witness references,
// verifies the test exists, runs the test, and verifies the expected pattern
// (positive passes, negative fails-by-detection, edge passes-the-edge)."
//
// THIS IS THE EXISTENCE-LEVEL MVP. It verifies the *first* clause only — that
// every witness a card declares actually resolves to a real artifact:
//
//   - kind: executable → the cited `substrate/...rs::fn` (or `...rs::tests::fn`
//     lib test) FILE exists AND the `fn <fn>` token is present in it.
//   - kind: narrative  → the cited `canonical_dilemma_corpus/INDEX.md#D-NNNN`
//     dilemma id is present (as a `### D-NNNN` heading) in INDEX.md.
//
// The full "run the test + verify polarity" clause (positive passes / negative
// fails-by-detection / edge passes-the-edge) is STAGED v0.9.x maturity per
// META §5.6 ("initial vs. mature anchoring": v3.1 ship is initial anchoring;
// every-actual-test-run accrues over time). Promoting this lint to run the
// witnesses and assert their polarity is the next maturity step; until then,
// existence-level resolution is the binding contract and the guard against the
// failure mode this capstone closed — cards citing tests that do not exist.
//
// Why existence-level still matters: before this pass, all 28 cards pointed at
// `tests/integration/<x>.rs::<fn>` — a directory that never existed. Every
// witness was dangling. This lint makes that class of drift (a witness naming
// a nonexistent artifact) impossible to commit silently.

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { resolve as resolvePath } from "node:path";

// operators/claude/tests → repo root is three levels up.
const REPO_ROOT = resolvePath(import.meta.dirname ?? __dirname, "..", "..", "..");
const L0_DIR = resolvePath(REPO_ROOT, "docs", "architecture", "L0");
const CARDS_DIR = resolvePath(L0_DIR, "cards");
const DILEMMA_INDEX = resolvePath(L0_DIR, "canonical_dilemma_corpus", "INDEX.md");

type WitnessKind = "executable" | "narrative";

interface CardWitnesses {
  card: string;
  kind: WitnessKind;
  slots: { slot: "positive" | "negative" | "edge"; value: string }[];
}

/** Strip a surrounding quote pair and any trailing ` # comment` from a YAML scalar. */
function cleanScalar(raw: string): string {
  // Drop a trailing inline comment (the nearest-available annotations use ` # ...`).
  // A `#` inside the quoted value would be unusual for our witness paths; we only
  // strip a `#` that appears AFTER the closing quote, so split on the quote first.
  let v = raw.trim();
  if (v.startsWith('"')) {
    const end = v.indexOf('"', 1);
    if (end !== -1) return v.slice(1, end);
  }
  if (v.startsWith("'")) {
    const end = v.indexOf("'", 1);
    if (end !== -1) return v.slice(1, end);
  }
  // Unquoted: cut at the first ` #`.
  const hash = v.indexOf(" #");
  if (hash !== -1) v = v.slice(0, hash);
  return v.trim();
}

/** Parse a single card's front-matter `witnesses:` block. */
function parseCardWitnesses(card: string, text: string): CardWitnesses {
  const lines = text.split(/\r?\n/);
  let inWitnesses = false;
  let kind: WitnessKind | null = null;
  const slots: CardWitnesses["slots"] = [];

  for (const line of lines) {
    if (/^witnesses:\s*$/.test(line)) {
      inWitnesses = true;
      continue;
    }
    if (!inWitnesses) continue;
    // The witnesses block ends at the next top-level (non-indented) key.
    if (/^\S/.test(line)) break;

    const kindMatch = line.match(/^\s+kind:\s*(.+)$/);
    if (kindMatch) {
      const k = cleanScalar(kindMatch[1]);
      assert.ok(
        k === "executable" || k === "narrative",
        `${card}: witnesses.kind must be 'executable' or 'narrative', got '${k}'`,
      );
      kind = k as WitnessKind;
      continue;
    }
    const slotMatch = line.match(/^\s+(positive|negative|edge):\s*(.+)$/);
    if (slotMatch) {
      slots.push({
        slot: slotMatch[1] as "positive" | "negative" | "edge",
        value: cleanScalar(slotMatch[2]),
      });
    }
  }

  assert.ok(kind !== null, `${card}: witnesses block has no 'kind:' discriminator`);
  return { card, kind, slots };
}

/**
 * Resolve an executable witness `substrate/.../<file>.rs::<...>::<fn>` and assert
 * the file exists and the `fn <fn>` token is present.
 */
function assertExecutableWitness(card: string, slot: string, value: string): void {
  const sep = value.indexOf("::");
  assert.ok(
    sep !== -1,
    `${card} (${slot}): executable witness '${value}' must be of the form <file>.rs::<fn>`,
  );
  const filePart = value.slice(0, sep);
  const symPart = value.slice(sep + 2);
  // The actual fn name is the LAST `::`-separated segment (handles
  // `<file>.rs::tests::<fn>` lib-test paths as well as `<file>.rs::<fn>`).
  const fnName = symPart.split("::").pop()!.trim();

  assert.ok(
    filePart.endsWith(".rs"),
    `${card} (${slot}): executable witness file '${filePart}' should be a .rs file`,
  );
  const abs = resolvePath(REPO_ROOT, filePart);
  assert.ok(
    existsSync(abs),
    `${card} (${slot}): witness file does not exist: ${filePart}`,
  );
  const src = readFileSync(abs, "utf8");
  // Grep-level: the `fn <name>` token must be present (covers `fn`, `pub fn`,
  // `pub(crate) fn`, `async fn`, etc., since we match the `fn <name>` substring).
  assert.ok(
    src.includes(`fn ${fnName}`),
    `${card} (${slot}): witness fn '${fnName}' not found in ${filePart} (declared: ${value})`,
  );
}

/**
 * Resolve a narrative witness `canonical_dilemma_corpus/INDEX.md#D-NNNN` and
 * assert the `D-NNNN` id is present as a `### D-NNNN` heading in INDEX.md.
 */
function assertNarrativeWitness(
  card: string,
  slot: string,
  value: string,
  indexText: string,
): void {
  const hash = value.indexOf("#");
  assert.ok(
    hash !== -1,
    `${card} (${slot}): narrative witness '${value}' must reference a dilemma id via '#D-NNNN'`,
  );
  const pathPart = value.slice(0, hash);
  const dilemmaId = value.slice(hash + 1).trim();

  assert.ok(
    pathPart.endsWith("canonical_dilemma_corpus/INDEX.md"),
    `${card} (${slot}): narrative witness should point at canonical_dilemma_corpus/INDEX.md, got '${pathPart}'`,
  );
  assert.match(
    dilemmaId,
    /^D-\d{4}$/,
    `${card} (${slot}): narrative witness id '${dilemmaId}' must be of the form D-NNNN`,
  );
  // INDEX.md headings look like `### D-0044 — ...`.
  const headingRe = new RegExp(`^###\\s+${dilemmaId}\\b`, "m");
  assert.match(
    indexText,
    headingRe,
    `${card} (${slot}): dilemma '${dilemmaId}' has no '### ${dilemmaId}' heading in canonical_dilemma_corpus/INDEX.md`,
  );
}

const cardFiles = readdirSync(CARDS_DIR)
  .filter((f) => f.endsWith(".md"))
  .sort();

const indexText = readFileSync(DILEMMA_INDEX, "utf8");

describe("L0 witness lint (META §5.5, existence-level — §5.6 staging)", () => {
  it("the cards directory and dilemma INDEX both resolve", () => {
    assert.ok(cardFiles.length > 0, `no card .md files found under ${CARDS_DIR}`);
    assert.ok(existsSync(DILEMMA_INDEX), `dilemma INDEX missing: ${DILEMMA_INDEX}`);
  });

  for (const file of cardFiles) {
    const card = file.replace(/\.md$/, "");
    describe(card, () => {
      const text = readFileSync(resolvePath(CARDS_DIR, file), "utf8");
      const parsed = parseCardWitnesses(card, text);

      it("declares all three witness slots (positive/negative/edge)", () => {
        const present = new Set(parsed.slots.map((s) => s.slot));
        for (const slot of ["positive", "negative", "edge"] as const) {
          assert.ok(present.has(slot), `${card}: missing '${slot}' witness`);
        }
      });

      for (const { slot, value } of parsed.slots) {
        it(`${slot} witness resolves (kind: ${parsed.kind})`, () => {
          if (parsed.kind === "executable") {
            assertExecutableWitness(card, slot, value);
          } else {
            assertNarrativeWitness(card, slot, value, indexText);
          }
        });
      }
    });
  }
});
