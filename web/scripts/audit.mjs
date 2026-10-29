#!/usr/bin/env node
/**
 * Quality audit: Lighthouse (mobile) + axe-core (WCAG 2.1 AA) for representative pages.
 *
 * Usage:
 *   node scripts/audit.mjs [--base http://127.0.0.1:4322] [--min-perf 90] [--min 95] [--json out.json]
 *
 * Needs a running site (built static pages, e.g. `node dist/server/entry.mjs` with PORT=4322)
 * and the CMS for media. Exit code 1 if a threshold is missed or axe finds violations.
 */
import { execSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import lighthouse from "lighthouse";

const require = createRequire(import.meta.url);
function loadPlaywright() {
  try {
    return require("playwright");
  } catch {
    // Fall back to a globally installed playwright (CI / preinstalled environments).
    return require(`${execSync("npm root -g").toString().trim()}/playwright`);
  }
}
const { chromium } = loadPlaywright();

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, a, i, arr) => (a.startsWith("--") ? [...acc, [a.slice(2), arr[i + 1]]] : acc), []),
);
const BASE = (args.base ?? "http://127.0.0.1:4322").replace(/\/$/, "");
const MIN = Number(args.min ?? 95); // accessibility, best practices, SEO
const MIN_PERF = Number(args["min-perf"] ?? 90); // performance is noisy on shared CI runners

export const PAGES = [
  "/",
  "/gebaeudereinigung/",
  "/gebaeudereinigung/unterhaltsreinigung/",
  "/unternehmen/",
  "/karriere/",
  "/karriere/beispiel-objektleitung/",
  "/kontakt/",
  "/impressum/",
];

const AXE_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa", "best-practice"];
const axeSource = readFileSync(require.resolve("axe-core/axe.min.js"), "utf8");

const PORT = 9333;
const browser = await chromium.launch({ args: [`--remote-debugging-port=${PORT}`] });

async function runAxe(path, viewport) {
  const page = await browser.newPage({ viewport });
  await page.goto(BASE + path, { waitUntil: "networkidle" });
  // Lazy images and client:visible islands: scroll through the page first.
  await page.evaluate(async () => {
    for (let y = 0; y < document.body.scrollHeight; y += 500) {
      window.scrollTo(0, y);
      await new Promise((r) => setTimeout(r, 40));
    }
    window.scrollTo(0, 0);
  });
  await page.waitForLoadState("networkidle");
  await page.addScriptTag({ content: axeSource });
  const result = await page.evaluate(
    (tags) => window.axe.run(document, { runOnly: { type: "tag", values: tags } }),
    AXE_TAGS,
  );
  await page.close();
  return result.violations.map((v) => ({
    id: v.id,
    impact: v.impact,
    help: v.help,
    nodes: v.nodes.length,
    targets: v.nodes.slice(0, 3).map((n) => n.target.join(" ")),
  }));
}

async function runLighthouse(path) {
  const { lhr } = await lighthouse(BASE + path, {
    port: PORT,
    output: "json",
    logLevel: "error",
    onlyCategories: ["performance", "accessibility", "best-practices", "seo"],
    formFactor: "mobile",
    screenEmulation: { mobile: true, width: 412, height: 823, deviceScaleFactor: 1.75, disabled: false },
  });
  const score = (k) => Math.round((lhr.categories[k]?.score ?? 0) * 100);
  const failed = Object.values(lhr.audits)
    .filter((a) => a.score !== null && a.score < 0.9 && a.scoreDisplayMode !== "informative" && a.scoreDisplayMode !== "manual" && a.scoreDisplayMode !== "notApplicable")
    .map((a) => ({ id: a.id, title: a.title, score: a.score, value: a.displayValue ?? "" }));
  return {
    performance: score("performance"),
    accessibility: score("accessibility"),
    bestPractices: score("best-practices"),
    seo: score("seo"),
    lcp: lhr.audits["largest-contentful-paint"]?.displayValue,
    cls: lhr.audits["cumulative-layout-shift"]?.displayValue,
    tbt: lhr.audits["total-blocking-time"]?.displayValue,
    failed,
  };
}

const report = [];
let ok = true;
for (const path of PAGES) {
  const lh = await runLighthouse(path);
  const axeMobile = await runAxe(path, { width: 390, height: 844 });
  const axeDesktop = await runAxe(path, { width: 1280, height: 900 });
  const axeAll = [...axeMobile, ...axeDesktop.filter((d) => !axeMobile.some((m) => m.id === d.id))];
  const pass =
    lh.performance >= MIN_PERF && lh.accessibility >= MIN && lh.bestPractices >= MIN && lh.seo >= MIN && axeAll.length === 0;
  ok &&= pass;
  report.push({ path, ...lh, axe: axeAll, pass });
  console.log(
    `${pass ? "✔" : "✘"} ${path.padEnd(42)} perf ${lh.performance} · a11y ${lh.accessibility} · bp ${lh.bestPractices} · seo ${lh.seo} · axe ${axeAll.length} · LCP ${lh.lcp} · CLS ${lh.cls}`,
  );
  for (const v of axeAll) console.log(`    axe ${v.impact}: ${v.id} (${v.nodes}×) – ${v.help} – ${v.targets.join(" | ")}`);
  for (const f of lh.failed) console.log(`    lh: ${f.id} (${f.score}) ${f.value}`);
}
await browser.close();
if (args.json) writeFileSync(args.json, JSON.stringify(report, null, 2));
console.log(ok ? "\nAlle Seiten bestehen." : `\nNicht bestanden (Ziel: Performance ≥ ${MIN_PERF}, sonst ≥ ${MIN}, 0 axe-Verstöße).`);
process.exit(ok ? 0 : 1);
