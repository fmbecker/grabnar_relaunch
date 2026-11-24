/**
 * E2E: the mobile menu as a native popover.
 *
 * Covers the three cases of docs/07-web-standards.md finding 3 that axe cannot reach,
 * because it only ever inspects a page at rest: Escape, a click outside, and the category
 * disclosures. Escape and the outside click are specified behaviour of popover="auto", so
 * what this really checks is that the markup lets the browser do its job – the list is the
 * popover, the button its declarative trigger – and that focus returns to the button.
 *
 * Prerequisites: CMS seeded (manage.py seed_dev) and a built site served on the base URL,
 * e.g. `cd web && node scripts/serve-prod.mjs`.
 * Run: node e2e/mobile_menu.mjs [base-url]
 */
import { BASE, chromium, check, report } from "./playwright.mjs";

const browser = await chromium.launch();
// Narrow viewport: the menu button is hidden from the lg breakpoint upwards.
const page = await browser.newPage({ viewport: { width: 390, height: 844 } });

await page.goto(`${BASE}/`, { waitUntil: "networkidle" });
const button = page.locator('button[popovertarget="mobile-menu"]');
const menu = page.locator("#mobile-menu");
const open = () => menu.evaluate((el) => el.matches(":popover-open"));

check("Der Menü-Knopf ist auf dem Telefon sichtbar", await button.isVisible());
check("Das Menü ist zu, bevor etwas geklickt wird", (await open()) === false);

await button.click();
await menu.waitFor({ state: "visible" });
check("Klick öffnet das Menü", (await open()) === true);
check("Das Menü liegt unter dem Header", (await menu.boundingBox())?.y >= 80, `y = ${(await menu.boundingBox())?.y}`);

// 1. Escape – the browser's own light dismiss for popover="auto".
await page.keyboard.press("Escape");
await menu.waitFor({ state: "hidden" });
check("Escape schließt das Menü", (await open()) === false);
const afterEscape = await page.evaluate(() => document.activeElement?.getAttribute("popovertarget"));
check("Der Fokus kehrt zum Knopf zurück", afterEscape === "mobile-menu", `Fokus auf "${afterEscape}"`);

// 2. A click outside.
await button.click();
await menu.waitFor({ state: "visible" });
await page.mouse.click(10, 700);
await menu.waitFor({ state: "hidden" });
check("Klick daneben schließt das Menü", (await open()) === false);

// 3. The category disclosures. The markup renders them expanded so the menu works without
// JavaScript; the script collapses them and wires the buttons.
await button.click();
await menu.waitFor({ state: "visible" });
const category = menu.locator("[data-menu-toggle]").first();
const subList = menu.locator("#mobile-menu-0");
check("Es gibt Kategorien mit Unterpunkten", (await menu.locator("[data-menu-toggle]").count()) >= 1);
check("Kategorie startet zugeklappt", (await category.getAttribute("aria-expanded")) === "false");
check("… und ihre Unterpunkte sind verborgen", (await subList.isHidden()) === true);

await category.click();
check("Klick klappt die Kategorie auf", (await category.getAttribute("aria-expanded")) === "true");
check("… und zeigt die Unterpunkte", (await subList.isVisible()) === true);

await category.click();
check("Nochmal klicken klappt sie zu", (await category.getAttribute("aria-expanded")) === "false");
check("… und verbirgt die Unterpunkte wieder", (await subList.isHidden()) === true);

// The menu itself must still be open: a category is a disclosure inside it, not a dismiss.
check("Das Menü bleibt dabei offen", (await open()) === true);

await browser.close();
report();
