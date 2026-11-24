/**
 * E2E: the job filter keeps its selection in the URL, and the FAQ is an exclusive accordion.
 *
 * Covers small items 2 and 3 of docs/07-web-standards.md and the three faults the code
 * review found in them: the live region must speak even when the number of matches stays
 * the same, a filter value that no job has must leave the address bar too, and two faq
 * blocks on one page must not close each other's answers.
 *
 * Prerequisites: CMS seeded WITH the demo jobs (manage.py seed_dev --demo-jobs), so the job
 * list has something to filter, and a built site served on the base URL, e.g.
 * `cd web && node scripts/serve-prod.mjs`. Without --demo-jobs the list shows its empty
 * text and the filter never renders, so the first checks fail.
 * Run: node e2e/job_filter_faq.mjs [base-url]
 */
import { BASE, chromium, check, report } from "./playwright.mjs";

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

// Scoped to the block: the header, the footer and the page itself hold other lists.
const list = page.locator("#stellen");
const jobs = () => list.locator("ul li").count();
const query = () => new URL(page.url()).search;
const sel = (which) => list.locator(`select[id$="-${which}"]`);
const live = () => list.locator('[role="status"]').textContent();

await page.goto(`${BASE}/karriere/`, { waitUntil: "networkidle" });
// client:idle – the island hydrates once the browser is done with the first paint.
await sel("location").waitFor();
check("Ohne Auswahl: alle Stellen, keine Query", (await jobs()) === 3 && query() === "", `${await jobs()} Stellen, "${query()}"`);
check("Live-Region zunächst leer", (await live()) === "");

await sel("location").selectOption("Affalterbach");
await page.waitForFunction(() => location.search.includes("ort="));
check("Auswahl landet in der URL", query() === "?ort=Affalterbach", `"${query()}"`);
check("Liste gefiltert", (await jobs()) === 1, `${await jobs()} Stellen`);
const firstMessage = await live();
check("Live-Region meldet das Ergebnis", firstMessage?.includes("1 von 3") === true, `"${firstMessage}"`);

// The one job in Affalterbach is full time, so this second choice matches the same single
// job. A message of counts alone would be the identical text: no DOM change, and
// role="status" stays silent.
await sel("type").selectOption("FULL_TIME");
check("Zweiter Filter kommt dazu", query() === "?ort=Affalterbach&art=FULL_TIME", `"${query()}"`);
const secondMessage = await live();
check(
  "Live-Region spricht auch bei gleicher Trefferzahl",
  secondMessage !== firstMessage && secondMessage?.includes("1 von 3") === true,
  `vorher "${firstMessage}", jetzt "${secondMessage}"`,
);

await page.goBack();
await page.waitForFunction(() => !location.search.includes("art="));
check("Zurück nimmt den letzten Schritt zurück", query() === "?ort=Affalterbach", `"${query()}"`);
check("… und der Select folgt", (await sel("type").inputValue()) === "", `Select = "${await sel("type").inputValue()}"`);

await page.goto(`${BASE}/karriere/?art=FULL_TIME`, { waitUntil: "networkidle" });
await page.waitForFunction(() => document.querySelectorAll("#stellen ul li").length === 2);
check("Geteilter Link stellt die Auswahl her", (await sel("type").inputValue()) === "FULL_TIME");

// A stale or hand-edited link must not leave the select showing a choice that filters
// everything away – and the dropped value must not stay in the address bar either, or
// copying the link would pass it on.
await page.goto(`${BASE}/karriere/?ort=Nirgendwo`, { waitUntil: "networkidle" });
await sel("location").waitFor();
await page.waitForFunction(() => !location.search.includes("ort="));
check(
  "Unbekannter Wert wird verworfen",
  (await sel("location").inputValue()) === "" && (await jobs()) === 3,
  `Select = "${await sel("location").inputValue()}", ${await jobs()} Stellen`,
);
check("… und verschwindet auch aus der URL", query() === "", `"${query()}"`);
check("Live-Region schweigt bei der Korrektur", (await live()) === "", `"${await live()}"`);

// --- FAQ ------------------------------------------------------------------------------
// The seeded page carries two faq blocks, which is what makes the grouping testable.
await page.goto(`${BASE}/unternehmen/`, { waitUntil: "networkidle" });
const faqBlocks = page.locator("section:has(details)");
check("Zwei FAQ-Blöcke auf der Seite", (await faqBlocks.count()) === 2, `${await faqBlocks.count()} Blöcke`);

const names = await page.locator("details").evaluateAll((all) => [...new Set(all.map((d) => d.name))]);
check("Jeder Block hat seinen eigenen Gruppennamen", names.length === 2, `${names.length} Namen`);

const blockA = faqBlocks.first();
await blockA.locator("summary").first().click();
await blockA.locator("summary").nth(1).click();
check(
  "Pro Block bleibt nur eine Antwort offen",
  (await blockA.locator("details[open]").count()) === 1,
  `${await blockA.locator("details[open]").count()} offen`,
);

// The group name used to be cut from the heading, so two blocks whose headings agree in
// their first characters shared one group and closed each other's answers.
await faqBlocks.nth(1).locator("summary").first().click();
const openTotal = await page.locator("details[open]").count();
check("Der zweite Block schließt den ersten nicht", openTotal === 2, `${openTotal} offen, erwartet 2`);

await browser.close();
report();
