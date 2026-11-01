# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Primary:** Hausverwaltungen, Facility-Verantwortliche und Geschäftsführer kleiner und mittlerer
  Unternehmen im Raum Stuttgart. They look for a dependable provider for an object they are
  responsible for, compare a few candidates, and want to request an offer or call quickly.
- **Secondary:** Bewerber (Reinigungskräfte, Vorarbeiter, Objektleitung) looking for open positions,
  honest information about workplace and hours, and a short application.
- **Not addressed:** private customers (company decision, 30.10.2026) – no wording like „Privathaushalt“,
  „Privatumzug“, „Privatwohnung“.

## Product Purpose

Company website of M. B. Grabnar Gebäudereinigungs- und Handwerker-Service GmbH (www.grabnar.de).
Success means: commercial enquiries (call 0711 2 36 33 30 or `/kontakt/`) and applications via the
careers section. Editors maintain content in Wagtail; the site must stay fast, accessible and
maintainable by one developer.

## Positioning

Confirmed by Felix (31.10.2026), all four together:

- **Alles aus einer Hand:** cleaning, building services (Hausmeister, Winterdienst, Grünanlagen) and
  craft work through one contact.
- **Meisterbetrieb** des Gebäudereinigerhandwerks.
- **Zertifiziert nach ISO 9001 und ISO 14001.**
- **Inhabergeführt und regional:** Stuttgart and region (Affalterbach / Pleidelsheim area), short ways.

## Operating Context

Visitors are professionals evaluating a service provider, often on a desktop at work, sometimes on a
phone on site. They scan for the service they need, proof of reliability, and a contact. Many call
rather than fill in a form.

## Capabilities and Constraints

- Headless Wagtail (`cms/`) + static Astro/Tailwind 4 (`web/`); React only in existing islands; one SSR
  route for preview. Details: `CLAUDE.md`, `docs/03-technik.md`.
- Forms post to the own CMS endpoint (no third parties). Self-hosted fonts only, no external requests.
- Tracking via Umami (`docs/05-tracking.md`); never personal data.
- Confirmed company facts: `docs/02-konzept.md` („Bestätigte Angaben“). Arbeitnehmerüberlassung (AÜG)
  may be named. The Bewachungserlaubnis (§ 34a GewO) must **never** be mentioned.
- Content tree, page models and texts are approved; the design rework (`docs/06-design.md`,
  `docs/design/brief-rework.md`) changes presentation only, plus the hero motto field.

## Brand Commitments

- Name: M. B. Grabnar GmbH. Motto: „Zusammenkommen ist der Anfang – Zusammenarbeiten ist der Erfolg.“
- Logos: `docs/assets/logo-mbgrabnar.png`, `docs/assets/logo-mbgrabnar-weiss.png` (on blue).
- Colours fixed by the logo (`#2D78BC`, `#8BC1E5`); visual decisions live in `docs/06-design.md`.
- Voice: **Sie-Form, sachlich-direkt**, short, without marketing phrases – as in `docs/content-neu/`.
  German for content and editor UI.

## Evidence on Hand

- ISO 9001 / 14001 certification (combined seal follows via site settings).
- Real service texts for 22 services in 4 categories (`docs/content-neu/`, `docs/content-export/`).
- Founding year and other figures exist but have **not been supplied yet**; until Felix provides them,
  show no years, employee counts or other numbers.
- **No** photos yet (placeholders until the company delivers), **no** reference customers, testimonials
  or logos. Never invent any of these.

## Product Principles

1. Contact is always one step away: phone and enquiry visible on every page.
2. Only confirmed statements – no invented numbers, customers or claims.
3. Speak to business customers and applicants, never to private households.
4. Fast and accessible for everyone (Lighthouse 100, axe 0) beats decoration.
5. Editors must be able to keep it right without a developer.

## Accessibility & Inclusion

WCAG 2.1 AA minimum; project target Lighthouse mobile 100/100/100/100 and axe 0 violations
(`web/scripts/audit.mjs`, CI job `audit`). Visible focus, touch targets ≥ 44 px, `prefers-reduced-motion`.
