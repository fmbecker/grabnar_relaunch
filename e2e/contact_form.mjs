/**
 * E2E: the contact form reports a rejected field to assistive technology.
 *
 * Covers docs/07-web-standards.md finding 2 and the three faults the code review found in
 * it: the failure banner must not appear while the visitor corrects a field, a key with no
 * control here must still produce a message, and the focus move must not depend on timing.
 *
 * Prerequisites: CMS seeded (manage.py seed_dev) and a built site served on the base URL,
 * e.g. `cd web && node scripts/serve-prod.mjs`. The answer from the CMS is stubbed, so the
 * assertions are about the React island only.
 * Run: node e2e/contact_form.mjs [base-url]
 */
import { BASE, chromium, check, report } from "./playwright.mjs";

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

let reply = {
  status: 400,
  body: { ok: false, errors: { email: ["Bitte eine erreichbare E-Mail-Adresse angeben."] } },
};
await page.route("**/api/forms/contact/", (route) =>
  route.fulfill({
    status: reply.status,
    contentType: "application/json",
    body: JSON.stringify(reply.body),
  }),
);

await page.goto(`${BASE}/kontakt/`, { waitUntil: "networkidle" });
// client:visible – the island only hydrates once the form is in view.
await page.locator("form").scrollIntoViewIfNeeded();
const name = page.locator('input[name="name"]');
const email = page.locator('input[name="email"]');
const message = page.locator('textarea[name="message"]');
const consent = page.locator('input[name="consent"]');
const alert = page.locator('form [role="alert"]');
await name.waitFor({ state: "visible" });

// 1. Nothing is announced as invalid before the visitor has done anything.
check(
  "Vor der Eingabe: aria-invalid=false",
  (await email.getAttribute("aria-invalid")) === "false",
  `ist "${await email.getAttribute("aria-invalid")}"`,
);
check("Vor der Eingabe: kein aria-describedby", (await email.getAttribute("aria-describedby")) === null);

// 2. The browser's own :user-invalid state reaches aria-invalid.
await email.click();
await email.pressSequentially("x");
await email.press("Backspace");
await name.click();
check(
  "Leer gelassenes Pflichtfeld: aria-invalid=true",
  (await email.getAttribute("aria-invalid")) === "true",
  `ist "${await email.getAttribute("aria-invalid")}"`,
);
await email.fill("info@example.org");
check("Nach dem Ausfüllen wieder aria-invalid=false", (await email.getAttribute("aria-invalid")) === "false");

// 3. A field the server rejects: message linked, field focused.
await name.fill("Testeingabe");
await message.fill("Bitte um ein Angebot.");
await consent.check();
await page.locator('button[type="submit"]').click();
await page.waitForFunction(
  () => document.querySelector('input[name="email"]')?.getAttribute("aria-invalid") === "true",
);

const describedBy = await email.getAttribute("aria-describedby");
check("Abgelehntes Feld: aria-invalid=true", (await email.getAttribute("aria-invalid")) === "true");
check("Abgelehntes Feld: aria-describedby gesetzt", Boolean(describedBy), `= "${describedBy}"`);
// Attribute selector, not "#id": React's useId produces characters that need escaping,
// and CSS.escape does not exist in Node.
const text = describedBy ? await page.locator(`[id="${describedBy}"]`).textContent() : "";
check("aria-describedby zeigt auf die Meldung", text?.includes("erreichbare E-Mail") === true, `"${text}"`);
const focused = await page.evaluate(() => document.activeElement?.getAttribute("name"));
check("Fokus steht im ersten abgelehnten Feld", focused === "email", `Fokus auf "${focused}"`);
check(
  "Keine Sammel-Meldung neben der Feldmeldung",
  (await alert.count()) === 0,
  `${await alert.count()} Sammel-Meldung(en)`,
);

// 4. Typing clears the server's message again – and must not reveal the failure banner.
// The banner used to be derived from "no field error left", and typing produces exactly that.
await email.fill("info@example.com");
check("Tippen löscht die Server-Meldung", (await email.getAttribute("aria-describedby")) === null);
check(
  "Tippen lässt keine Sammel-Meldung erscheinen",
  (await alert.count()) === 0,
  `${await alert.count()} Sammel-Meldung(en)`,
);

// 5. A key with no control on this form must not be swallowed. The contact variant renders
// no job_title input, so this is the case a hard-coded list of field names missed.
reply = { status: 400, body: { ok: false, errors: { job_title: ["Zu lang."] } } };
await page.locator('button[type="submit"]').click();
await alert.waitFor({ state: "visible" });
check("Schlüssel ohne Feld: Sammel-Meldung erscheint", (await alert.count()) === 1);
const alertFocus = await page.evaluate(() => document.activeElement?.getAttribute("role"));
check("… und bekommt den Fokus", alertFocus === "alert", `Fokus-Rolle "${alertFocus}"`);

// 6. Success: focus must not fall back to the document. Not scoped to the form, because on
// success the island replaces the whole form with the message.
reply = { status: 201, body: { ok: true, id: 1 } };
await page.locator('button[type="submit"]').click();
await page.locator('[role="status"]').waitFor({ state: "visible" });
const okFocus = await page.evaluate(() => document.activeElement?.getAttribute("role"));
check("Nach dem Senden: Fokus auf der Erfolgsmeldung", okFocus === "status", `Fokus-Rolle "${okFocus}"`);

await browser.close();
report();
