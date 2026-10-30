// Every event used in deploy/umami/reports.json must exist in src/lib/analytics.ts (EVENT),
// so a renamed event cannot silently break a goal or funnel in Umami. Run: pnpm check:tracking
import { readFileSync } from "node:fs";

const root = new URL("../../", import.meta.url);
const source = readFileSync(new URL("web/src/lib/analytics.ts", root), "utf8");
const block = source.slice(source.indexOf("export const EVENT"), source.indexOf("} as const"));
const events = new Set([...block.matchAll(/:\s*"([a-z0-9-]+)"/g)].map((m) => m[1]));
const reports = JSON.parse(readFileSync(new URL("deploy/umami/reports.json", root), "utf8"));

const used = [
  ...reports.goals.filter((g) => g.parameters.type === "event").map((g) => [g.name, g.parameters.value]),
  ...reports.funnels.flatMap((f) => f.parameters.steps.filter((s) => s.type === "event").map((s) => [f.name, s.value])),
];
const missing = used.filter(([, event]) => !events.has(event));
if (missing.length) {
  for (const [name, event] of missing) console.error(`reports.json: „${name}“ nutzt unbekanntes Ereignis "${event}"`);
  process.exit(1);
}
console.log(`Tracking: ${used.length} Ereignis-Bezüge in reports.json, alle in EVENT definiert (${events.size} Ereignisse).`);
