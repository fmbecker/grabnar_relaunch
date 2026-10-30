#!/usr/bin/env node
/**
 * Applies deploy/umami/reports.json (goals, funnels, segments) to an Umami >= 3.4 website.
 *
 *   UMAMI_URL=http://127.0.0.1:3000 \
 *   UMAMI_API_KEY=umami_… \            # Umami → Einstellungen → API-Schlüssel
 *   UMAMI_WEBSITE_ID=<uuid> \
 *   node deploy/umami/setup-reports.mjs [--dry-run]
 *
 * Matching is by name: missing entries are created, existing ones updated. Nothing is deleted,
 * so entries added in the Umami UI stay untouched. Safe to run again after editing reports.json.
 */
import { readFile } from "node:fs/promises";

const DRY = process.argv.includes("--dry-run");
const { UMAMI_URL, UMAMI_API_KEY, UMAMI_WEBSITE_ID } = process.env;
if (!UMAMI_URL || !UMAMI_API_KEY || !UMAMI_WEBSITE_ID) {
  console.error("UMAMI_URL, UMAMI_API_KEY und UMAMI_WEBSITE_ID setzen (siehe Kopf dieser Datei).");
  process.exit(2);
}
const base = `${UMAMI_URL.replace(/\/$/, "")}/api/websites/${UMAMI_WEBSITE_ID}`;
const config = JSON.parse(await readFile(new URL("./reports.json", import.meta.url), "utf8"));

async function api(method, path, body) {
  const res = await fetch(base + path, {
    method,
    headers: { Authorization: `Bearer ${UMAMI_API_KEY}`, "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  if (!res.ok) throw new Error(`${method} ${path} → HTTP ${res.status}: ${text.slice(0, 300)}`);
  return text ? JSON.parse(text) : {};
}

/** kind: goals | funnels | segments; payload builds the request body for one entry. */
async function sync(kind, entries, payload, listQuery = "") {
  if (!entries?.length) return;
  const existing = (await api("GET", `/${kind}?pageSize=200${listQuery}`)).data ?? [];
  const byName = new Map(existing.map((e) => [e.name, e]));
  for (const entry of entries) {
    const found = byName.get(entry.name);
    const action = found ? "aktualisieren" : "anlegen";
    console.log(`${DRY ? "[dry-run] " : ""}${kind}: ${action} „${entry.name}“`);
    if (DRY) continue;
    await api("POST", found ? `/${kind}/${found.id}` : `/${kind}`, payload(entry));
  }
}

try {
  await sync("goals", config.goals, (g) => ({ name: g.name, description: g.description ?? "", parameters: g.parameters }));
  await sync("funnels", config.funnels, (f) => ({ name: f.name, description: f.description ?? "", parameters: f.parameters }));
  await sync("segments", config.segments, (s) => ({ type: "segment", name: s.name, parameters: s.parameters }), "&type=segment");
  console.log(DRY ? "Probelauf beendet, nichts geändert." : "Fertig.");
} catch (err) {
  console.error(String(err.message ?? err));
  process.exit(1);
}
