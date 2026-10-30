/**
 * Event tracking for Umami (cookieless, self-hosted; config in the CMS under
 * Einstellungen → Website-Einstellungen → Statistik).
 *
 * Two ways to send an event, both safe when Umami is not loaded (dev, preview,
 * blocked by the visitor):
 *   - Static markup: spread `umami(EVENT, data)` onto a link or button. Umami's
 *     tracker sends the event on click (data-umami-event / data-umami-event-*).
 *   - Islands and scripts: call `track(EVENT, data)`.
 *
 * Rules: event names ≤ 50 chars, data values ≤ 500 chars, never personal data
 * (no names, e-mail addresses, phone numbers or free text from forms).
 * The full event plan with all properties is in docs/05-tracking.md.
 */

export const EVENT = {
  /** Call-to-action buttons (hero, CTA block, text+image). data: block, label, target */
  cta: "cta-click",
  /** tel: links. data: placement */
  phone: "phone-click",
  /** mailto: links. data: placement */
  email: "email-click",
  /** Phone number or e-mail address copied (desktop users rarely click tel:). data: type, placement */
  contactCopy: "contact-copy",
  /** Every contact: one goal for "Kontakte gesamt".
   *  data: channel (form, phone, email, phone-copy, email-copy), service, placement */
  lead: "lead",
  /** Category tiles on home/Unternehmen. data: category, target (overview|service) */
  category: "category-click",
  /** Service cards. data: service, list (category|related|manual) */
  service: "service-click",
  /** Main navigation, desktop and mobile. data: item, level, menu */
  nav: "nav-click",
  /** Mobile menu opened. */
  menuOpen: "mobile-menu-open",
  /** FAQ question opened. data: question */
  faqOpen: "faq-open",
  /** Gallery image opened. data: image */
  galleryOpen: "gallery-open",
  /** Links to other websites. data: url */
  outbound: "outbound-click",
  /** Document downloads (PDF etc.). data: file */
  download: "download-click",
  /** First interaction with a form. data: form, job */
  formStart: "form-start",
  /** Contact form sent successfully. data: service (from ?leistung=, never typed text) */
  inquirySent: "inquiry-sent",
  /** Application sent successfully. data: job */
  applicationSent: "application-sent",
  /** Sending failed. data: form, reason (invalid|error), fields (names of invalid fields) */
  formError: "form-error",
  /** Job list filter changed. data: field, value */
  jobFilter: "job-filter",
  /** Job opened from the list. data: job */
  jobOpen: "job-open",
  /** "Jetzt bewerben" on a job page. data: job */
  jobApply: "job-apply-click",
  /** 404 page shown. data: path, referrer */
  notFound: "page-not-found",
} as const;

export type EventName = (typeof EVENT)[keyof typeof EVENT];
export type EventData = Record<string, string | number | boolean | undefined | null>;

const clip = (v: unknown) => String(v).slice(0, 500);

/** data-umami-event attributes for static markup: `<a {...umami(EVENT.cta, { block: "hero" })}>`. */
export function umami(event: EventName, data: EventData = {}): Record<string, string> {
  const attrs: Record<string, string> = { "data-umami-event": event };
  for (const [key, value] of Object.entries(data)) {
    if (value === undefined || value === null || value === "") continue;
    attrs[`data-umami-event-${key.toLowerCase().replace(/[^a-z0-9-]/g, "-")}`] = clip(value);
  }
  return attrs;
}

interface UmamiTracker {
  track: (event: string, data?: Record<string, string | number | boolean>) => void;
}

/** Send an event from script code. No-op when Umami is not loaded. */
export function track(event: EventName, data: EventData = {}): void {
  const tracker = (globalThis as { umami?: UmamiTracker }).umami;
  if (!tracker || typeof tracker.track !== "function") return;
  const clean: Record<string, string | number | boolean> = {};
  for (const [key, value] of Object.entries(data)) {
    if (value === undefined || value === null || value === "") continue;
    clean[key] = typeof value === "string" ? clip(value) : value;
  }
  try {
    tracker.track(event, clean);
  } catch {
    /* tracking must never break the page */
  }
}

/** Path of an internal href ("/kontakt/"), or the href itself for anything else. */
export function target(href: string): string {
  try {
    const url = new URL(href, "https://www.grabnar.de");
    return url.hostname.endsWith("grabnar.de") ? url.pathname + url.hash : url.href;
  } catch {
    return href;
  }
}

/** Query parameter that carries the service from a service page's CTA into the contact form. */
export const SERVICE_PARAM = "leistung";

/** Append ?leistung=<service> to links that go to the contact page. */
export function withService(href: string, service?: string): string {
  if (!service) return href;
  try {
    const url = new URL(href, "https://www.grabnar.de");
    if (!url.hostname.endsWith("grabnar.de") || url.pathname !== "/kontakt/") return href;
    url.searchParams.set(SERVICE_PARAM, service);
    return url.pathname + url.search + url.hash;
  } catch {
    return href;
  }
}
