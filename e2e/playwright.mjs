/**
 * Shared bits for the Node e2e scripts.
 *
 * playwright is a devDependency of web/, and these files sit outside that folder, so a bare
 * import would not resolve. Resolving from web/package.json keeps the scripts runnable from
 * anywhere without an environment variable.
 */
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const requireFromWeb = createRequire(new URL("../web/package.json", import.meta.url));
const mod = await import(pathToFileURL(requireFromWeb.resolve("playwright")).href);

/** @type {import("playwright").BrowserType} */
export const chromium = (mod.default ?? mod).chromium;

/** Base URL of the served build; override with the first argument. */
export const BASE = (process.argv[2] ?? "http://127.0.0.1:8080").replace(/\/$/, "");

const results = [];

/** Records one assertion and prints it. */
export function check(name, pass, detail = "") {
  results.push({ name, pass });
  console.log(`${pass ? "✔" : "✘"} ${name}${detail ? ` – ${detail}` : ""}`);
}

/** Prints the tally and exits non-zero if anything failed. */
export function report() {
  const failed = results.filter((r) => !r.pass);
  console.log(
    failed.length
      ? `\n${failed.length} von ${results.length} fehlgeschlagen: ${failed.map((r) => r.name).join(", ")}`
      : `\nAlle ${results.length} Prüfungen bestanden.`,
  );
  process.exit(failed.length ? 1 : 0);
}
