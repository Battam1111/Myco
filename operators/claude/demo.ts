// Myco keyless LIVE demo: one breath of the metabolic loop on a real substrate.
// Spawns a fresh substrate and drives it through the pilot's use-forges loop,
// narrating each step. Ephemeral (fresh temp state dir, torn down at the end).
// These are the SAME operations the MCP tools (myco_ingest_raw_material,
// myco_forge_understanding, ...) expose to a Claude pilot.

import { SubstrateClient } from "./src/substrate_client.ts";
import { resolve as resolvePath } from "node:path";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";

const enc = (s: string) => new TextEncoder().encode(s);
const hx = (u8: Uint8Array | null) =>
  u8 ? Buffer.from(u8).toString("hex").slice(0, 16) + "..." : "(none)";
const line = (s = "") => console.log(s);
const step = (n: number, s: string) => console.log(`\n[${n}] ${s}`);

function stringifyVal(v: unknown): string {
  if (typeof v === "bigint") return v.toString();
  if (v instanceof Uint8Array) return Buffer.from(v).toString("hex").slice(0, 12) + "...";
  if (v && typeof v === "object") return "{...}";
  return String(v);
}

function locateBinary(): string {
  const exe = process.platform === "win32" ? ".exe" : "";
  const root = resolvePath(import.meta.dirname, "..", "..");
  const cand = resolvePath(root, "target", "debug", `myco-substrate${exe}`);
  if (!existsSync(cand)) throw new Error(`substrate binary not found: ${cand}`);
  return cand;
}

async function main() {
  const bin = locateBinary();
  const dir = mkdtempSync(resolvePath(tmpdir(), "myco-demo-"));
  line("=".repeat(68));
  line("  MYCO KEYLESS LIVE DEMO: one breath of the metabolic loop");
  line("=".repeat(68));
  line(`  fresh state dir: ${dir}`);

  let client: SubstrateClient | null = null;
  try {
    step(1, "BOOT: spawn a fresh keyless substrate (no key to generate or hold)");
    client = await SubstrateClient.spawn({
      substrateBinary: bin,
      env: { ...process.env, MYCO_STATE_DIR: dir },
    });
    const ack = client.helloAck;
    line(`  alive: substrate ${ack.substrateVersion} | python ${ack.pythonVersion} | kernel ${ack.kernelTropismVersion}`);
    line(`  (one runtime, three languages: TS operator <-> Rust substrate <-> Python kernel)`);

    step(2, "PERCEIVE (empty): what does a brand-new armor know?");
    let plates = await client.listPlates();
    line(`  forged-understanding plates: ${plates.livePlates} live  ->  it knows nothing yet`);

    step(3, "DEVOUR: ingest raw experience as immutable history (ore in)");
    const ore = await client.ingestRawMaterial({
      contentKind: "text",
      contentBytes: enc(
        "Myco went keyless at v3.1.5: the owner key + anchor surface were retired. " +
          "Trust is now the live human at the CI gate, the causal DAG, and the BLAKE3-sealed bundle.",
      ),
    });
    line(`  ingested raw_material -> ${hx(ore.dagNodeHash)}   DAG size now ${ore.totalDagSize}`);

    step(4, "FORGE: deposit DIGESTED understanding, linked to its ore (plate out)");
    const plate = await client.depositForgedUnderstanding({
      label: "myco-keyless-trust-root",
      understanding: enc(
        "Keyless trust has three legs: the human reviewing at the CI/PR gate, the " +
          "substrate's tamper-evident causal DAG, and the BLAKE3-sealed doctrine. No owner " +
          "key exists; at runtime the bonded pilot is the authority (same body, shared fate).",
      ),
      sourceRawMaterialHashes: [ore.dagNodeHash],
      value: 90,
      confidence: 85,
    });
    line(`  forged plate -> ${hx(plate.dagNodeHash)}   DAG size now ${plate.totalDagSize}`);

    step(5, "METABOLIZE: run one autonomic cycle (the armor's own life)");
    await client.registerAxis({
      name: "curiosity",
      axisClass: "appetite",
      fruitingThreshold: 2.0,
      initialValue: 0.0,
      decayRatePerCycle: 1.0,
      isMortalitySignal: false,
      updateRuleKind: "noop",
    });
    await client.perturb("curiosity", 3.0);
    const report = await client.advance(1n);
    line(`  cycle advanced -> fruited: [${report.fruitedAxes.join(", ")}]  sporocarps: ${report.sporocarps.length}`);
    if (report.sporocarps[0]) {
      line(`  emitted "${report.sporocarps[0].sporocarpType}" (the armor acted on its own)`);
    }

    step(6, "SELF-PERCEIVE: the armor reads its own vital signs");
    try {
      const obs = (await client.querySubstrateObservatory()) as Record<string, unknown>;
      const summary = Object.keys(obs)
        .slice(0, 5)
        .map((k) => `${k}=${stringifyVal(obs[k])}`)
        .join("  ");
      line(`  observatory: ${summary}`);
    } catch {
      line("  observatory: (snapshot received)");
    }

    step(7, "INHERIT: a future pilot finds the plate AND its lineage");
    plates = await client.listPlates();
    line(`  plates now: ${plates.livePlates} live`);
    for (const p of plates.plates) {
      line(`    - "${p.label}"  importance=${p.value}  ${hx(p.hash)}`);
    }
    const back = await client.readNodeByHash(plate.dagNodeHash);
    if (back) {
      const linksToOre = back.parentHashes.some(
        (p) => Buffer.compare(Buffer.from(p), Buffer.from(ore.dagNodeHash)) === 0,
      );
      line(`  read plate node: type="${back.nodeType}"  parents=${back.parentHashes.length}`);
      line(`  plate -> ore causal link present: ${linksToOre}  (understanding remembers the experience it came from)`);
    }

    line("\n" + "=".repeat(68));
    line("  ONE BREATH: devour -> forge -> metabolize -> perceive -> inherit.");
    line("  That is the mechanism. Real cultivation (A) is a human living this daily,");
    line("  with Claude as the pilot, the armor carrying context across model generations.");
    line("=".repeat(68));
  } finally {
    if (client) await client.shutdown();
    rmSync(dir, { recursive: true, force: true });
  }
}

main().catch((e) => {
  console.error("DEMO FAILED:", e);
  process.exitCode = 1;
});
