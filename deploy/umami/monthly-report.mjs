#!/usr/bin/env node
/**
 * Monthly website report from Umami (>= 3.4) as an e-mail-ready HTML document.
 *
 *   UMAMI_URL=http://127.0.0.1:3000 UMAMI_API_KEY=umami_… UMAMI_WEBSITE_ID=<uuid> \
 *   node deploy/umami/monthly-report.mjs [--month=2026-10] [--out=report.html]
 *
 * Default month: the previous calendar month (Europe/Berlin). Compared with the month before.
 * Goals and funnels are looked up by the names in deploy/umami/reports.json, so run
 * setup-reports.mjs first. Only aggregates are reported, no individual visits.
 * Sending: deploy/umami/send-monthly-report.sh (systemd timer grabnar-umami-report).
 *
 *   --demo   render with built-in sample numbers, no Umami needed (to check the layout)
 */
import { readFile, writeFile } from "node:fs/promises";

const TZ = "Europe/Berlin";
const args = Object.fromEntries(
  process.argv.slice(2).map((a) => {
    const [k, v] = a.replace(/^--/, "").split("=");
    return [k, v ?? true];
  }),
);
const reports = JSON.parse(await readFile(new URL("./reports.json", import.meta.url), "utf8"));
const GOAL_LEAD = reports.goals[0].name; // "Kontakte gesamt"
const FUNNEL_INQUIRY = reports.funnels[0].name; // "Anfrage: Button → Formular → gesendet"

// ---------------------------------------------------------------- dates (Europe/Berlin)

/** Epoch ms of local midnight on the 1st of a month in Europe/Berlin. */
function berlinMonthStart(year, month /* 1-12 */) {
  const guess = Date.UTC(year, month - 1, 1);
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: TZ, hourCycle: "h23", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit",
  }).formatToParts(new Date(guess));
  const p = Object.fromEntries(parts.map((x) => [x.type, x.value]));
  const asUtc = Date.UTC(+p.year, +p.month - 1, +p.day, +p.hour, +p.minute);
  return guess - (asUtc - guess); // shift by the zone offset at that moment
}

function monthRange(year, month) {
  const next = month === 12 ? [year + 1, 1] : [year, month + 1];
  return { startAt: berlinMonthStart(year, month), endAt: berlinMonthStart(...next) - 1 };
}

function targetMonth() {
  if (typeof args.month === "string" && /^\d{4}-\d{2}$/.test(args.month)) {
    const [y, m] = args.month.split("-").map(Number);
    return [y, m];
  }
  const now = new Intl.DateTimeFormat("en-CA", { timeZone: TZ, year: "numeric", month: "2-digit" }).format(new Date());
  const [y, m] = now.split("-").map(Number);
  return m === 1 ? [y - 1, 12] : [y, m - 1];
}

const [YEAR, MONTH] = targetMonth();
const [PY, PM] = MONTH === 1 ? [YEAR - 1, 12] : [YEAR, MONTH - 1];
const CUR = monthRange(YEAR, MONTH);
const PREV = monthRange(PY, PM);
const monthName = (y, m) => new Intl.DateTimeFormat("de-DE", { month: "long", year: "numeric", timeZone: TZ }).format(new Date(Date.UTC(y, m - 1, 15)));

// ---------------------------------------------------------------- Umami API

const { UMAMI_URL, UMAMI_API_KEY, UMAMI_WEBSITE_ID } = process.env;
async function api(path, params = {}) {
  const url = new URL(`${UMAMI_URL.replace(/\/$/, "")}/api/websites/${UMAMI_WEBSITE_ID}${path}`);
  for (const [k, v] of Object.entries(params)) if (v !== undefined) url.searchParams.set(k, String(v));
  const res = await fetch(url, { headers: { Authorization: `Bearer ${UMAMI_API_KEY}` } });
  if (!res.ok) throw new Error(`GET ${path} → HTTP ${res.status}: ${(await res.text()).slice(0, 200)}`);
  return res.json();
}
const range = (r) => ({ startAt: r.startAt, endAt: r.endAt, timezone: TZ });
const rows = (data) =>
  (Array.isArray(data) ? data : data?.data ?? []).map((r) => ({
    label: String(r.x ?? r.value ?? r.name ?? "–"),
    value: Number(r.y ?? r.total ?? r.count ?? r.visitors ?? 0),
  }));
/** Optional section: a failing endpoint must not cost the whole report. */
async function soft(fn, fallback) {
  try { return await fn(); } catch (e) { console.error(`Hinweis: ${e.message}`); return fallback; }
}

async function collect() {
  const stats = await api("/stats", range(CUR)); // includes .comparison for the previous period
  const goalList = (await api("/goals", { pageSize: 200 })).data ?? [];
  const funnelList = (await api("/funnels", { pageSize: 200 })).data ?? [];
  const goals = [];
  for (const def of reports.goals) {
    const saved = goalList.find((g) => g.name === def.name);
    if (!saved) { console.error(`Hinweis: Ziel „${def.name}“ fehlt in Umami (setup-reports.mjs ausführen).`); continue; }
    const [cur, prev] = await Promise.all([api(`/goals/${saved.id}/stats`, range(CUR)), api(`/goals/${saved.id}/stats`, range(PREV))]);
    goals.push({ name: def.name, num: Number(cur?.num ?? 0), total: Number(cur?.total ?? 0), prev: Number(prev?.num ?? 0) });
  }
  const funnelDef = funnelList.find((f) => f.name === FUNNEL_INQUIRY);
  const funnel = funnelDef ? await soft(() => api(`/funnels/${funnelDef.id}/stats`, range(CUR)), []) : [];
  const values = (eventName, propertyName, r = CUR) =>
    soft(async () => rows(await api("/event-data/values", { ...range(r), eventName, propertyName })), []);
  const metric = (type, limit = 10) => soft(async () => rows(await api("/metrics", { ...range(CUR), type, limit })).slice(0, limit), []);
  const [leadChannel, leadService, notFound, notFoundPrev, pages, referrers, channels, devices, utm] = await Promise.all([
    values("lead", "channel"),
    values("lead", "service"),
    values("page-not-found", "path"),
    values("page-not-found", "path", PREV),
    metric("path"),
    metric("referrer"),
    metric("channel"),
    metric("device", 5),
    metric("utmSource"),
  ]);
  return { stats, goals, funnel, leadChannel, leadService, notFound, notFoundPrev, pages, referrers, channels, devices, utm };
}

function demo() {
  return {
    stats: { pageviews: 2140, visitors: 812, visits: 951, bounces: 470, totaltime: 95100,
      comparison: { pageviews: 1890, visitors: 700, visits: 820, bounces: 430, totaltime: 80200 } },
    goals: [
      { name: "Kontakte gesamt", num: 23, total: 812, prev: 31 },
      { name: "Anfragen (Formular)", num: 9, total: 812, prev: 12 },
      { name: "Bewerbungen", num: 4, total: 812, prev: 2 },
      { name: "Anrufe (Klick auf Nummer)", num: 8, total: 812, prev: 13 },
      { name: "Kontaktseite besucht", num: 61, total: 812, prev: 58 },
    ],
    funnel: [
      { type: "event", value: "cta-click", visitors: 74 },
      { type: "path", value: "/kontakt/", visitors: 52 },
      { type: "event", value: "form-start", visitors: 21 },
      { type: "event", value: "inquiry-sent", visitors: 9 },
    ],
    leadChannel: [{ label: "phone", value: 8 }, { label: "form", value: 9 }, { label: "phone-copy", value: 3 }, { label: "email", value: 2 }, { label: "email-copy", value: 1 }],
    leadService: [{ label: "Unterhaltsreinigung", value: 4 }, { label: "Glas- und Fassadenreinigung", value: 2 }, { label: "Winterdienst", value: 2 }],
    notFound: [{ label: "/Gebäudereinigung/Glasreinigung", value: 6 }, { label: "/wp-login.php", value: 3 }],
    notFoundPrev: [{ label: "/wp-login.php", value: 5 }],
    pages: [{ label: "/", value: 690 }, { label: "/gebaeudereinigung/unterhaltsreinigung/", value: 210 }, { label: "/kontakt/", value: 160 }, { label: "/karriere/", value: 120 }],
    referrers: [{ label: "google.com", value: 420 }, { label: "bing.com", value: 31 }, { label: "gelbeseiten.de", value: 12 }],
    channels: [{ label: "organicSearch", value: 455 }, { label: "direct", value: 301 }, { label: "referral", value: 40 }],
    devices: [{ label: "mobile", value: 470 }, { label: "desktop", value: 320 }, { label: "tablet", value: 22 }],
    utm: [{ label: "fahrzeug", value: 14 }, { label: "google", value: 9 }],
  };
}

// ---------------------------------------------------------------- analysis

const num = (v) => Number(v ?? 0);
const pct = (a, b) => (b ? Math.round(((a - b) / b) * 100) : null);
const fmt = (n) => new Intl.NumberFormat("de-DE").format(Math.round(n));
const duration = (sec) => `${Math.floor(sec / 60)}:${String(Math.round(sec % 60)).padStart(2, "0")} min`;
const LABELS = {
  phone: "Telefon (Klick)", email: "E-Mail (Klick)", form: "Kontaktformular", application: "Bewerbung",
  "phone-copy": "Telefonnummer kopiert", "email-copy": "E-Mail-Adresse kopiert",
  organicSearch: "Suchmaschinen", direct: "Direkt / Lesezeichen", referral: "Verweise", organicSocial: "Soziale Medien",
  paidSearch: "Bezahlte Suche", email_channel: "E-Mail", mobile: "Smartphone", desktop: "Computer", tablet: "Tablet", laptop: "Laptop",
  "cta-click": "Klick auf Aktions-Button", "/kontakt/": "Kontaktseite geöffnet", "form-start": "Formular begonnen", "inquiry-sent": "Anfrage gesendet",
};
const label = (s) => LABELS[s] ?? s;

function analyse(d) {
  const s = d.stats, c = s.comparison ?? {};
  const kpi = (cur, prev) => ({ cur, prev, delta: pct(cur, prev) });
  const visits = num(s.visits);
  const k = {
    visitors: kpi(num(s.visitors), num(c.visitors)),
    visits: kpi(visits, num(c.visits)),
    pageviews: kpi(num(s.pageviews), num(c.pageviews)),
    bounce: kpi(visits ? (num(s.bounces) / visits) * 100 : 0, num(c.visits) ? (num(c.bounces) / num(c.visits)) * 100 : 0),
    duration: kpi(visits ? num(s.totaltime) / visits : 0, num(c.visits) ? num(c.totaltime) / num(c.visits) : 0),
  };
  const notes = [];
  const lead = d.goals.find((g) => g.name === GOAL_LEAD);
  if (lead) {
    const dl = pct(lead.num, lead.prev);
    if (lead.num === 0 && lead.prev > 0) notes.push(["warn", `Keine Kontakte über die Website (Vormonat ${lead.prev}). Formular und Telefonlinks prüfen.`]);
    else if (dl !== null && Math.abs(dl) >= 25 && Math.abs(lead.num - lead.prev) >= 3)
      notes.push([dl < 0 ? "warn" : "good", `Kontakte ${dl > 0 ? "+" : ""}${dl} % gegenüber dem Vormonat (${lead.num} statt ${lead.prev}).`]);
  }
  if (k.visitors.delta !== null && Math.abs(k.visitors.delta) >= 20)
    notes.push([k.visitors.delta < 0 ? "warn" : "good", `Besucher ${k.visitors.delta > 0 ? "+" : ""}${k.visitors.delta} % gegenüber dem Vormonat.`]);
  if (d.funnel.length > 1) {
    let worst = null;
    for (let i = 1; i < d.funnel.length; i++) {
      const before = num(d.funnel[i - 1].visitors), after = num(d.funnel[i].visitors);
      const loss = before ? Math.round(((before - after) / before) * 100) : 0;
      if (before >= 5 && (!worst || loss > worst.loss)) worst = { loss, from: d.funnel[i - 1].value, to: d.funnel[i].value };
    }
    if (worst && worst.loss >= 50) notes.push(["info", `Größter Absprung im Anfrage-Weg: ${worst.loss} % zwischen „${label(worst.from)}“ und „${label(worst.to)}“.`]);
  }
  const prev404 = new Set(d.notFoundPrev.map((r) => r.label));
  const new404 = d.notFound.filter((r) => !prev404.has(r.label) && r.value >= 2 && !/\.(php|env|xml)$|wp-/i.test(r.label));
  if (new404.length) notes.push(["warn", `Neue nicht gefundene Adressen: ${new404.slice(0, 3).map((r) => r.label).join(", ")} – Weiterleitung prüfen.`]);
  const topService = d.leadService[0];
  if (topService) notes.push(["info", `Die meisten Kontakte mit Leistungsbezug: ${topService.label} (${topService.value}).`]);
  return { k, notes };
}

// ---------------------------------------------------------------- HTML (e-mail safe: tables + inline styles)

const C = { brand: "#2d78bc", ink: "#1b2430", muted: "#5b6878", line: "#dfe5ec", soft: "#f3f6fa", good: "#1f7a46", warn: "#a35600" };
const esc = (s) => String(s).replace(/[&<>"]/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[ch]);
const delta = (d, invert = false) => {
  if (d === null || !isFinite(d)) return `<span style="color:${C.muted}">–</span>`;
  const good = invert ? d < 0 : d > 0;
  const color = d === 0 ? C.muted : good ? C.good : C.warn;
  return `<span style="color:${color}">${d > 0 ? "▲ +" : d < 0 ? "▼ " : ""}${d} %</span>`;
};
const h2 = (t) => `<h2 style="font-size:17px;margin:28px 0 8px;color:${C.ink}">${esc(t)}</h2>`;
const table = (head, body) => `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;font-size:14px">
<tr>${head.map((h, i) => `<th align="${i ? "right" : "left"}" style="padding:6px 8px;border-bottom:2px solid ${C.line};color:${C.muted};font-weight:600">${esc(h)}</th>`).join("")}</tr>
${body.map((r) => `<tr>${r.map((cell, i) => `<td align="${i ? "right" : "left"}" style="padding:6px 8px;border-bottom:1px solid ${C.line}">${cell}</td>`).join("")}</tr>`).join("\n")}
</table>`;
const list = (title, data, empty = "Keine Daten in diesem Monat.", name = label) =>
  h2(title) + (data.length ? table(["", "Anzahl"], data.map((r) => [esc(name(r.label)), fmt(r.value)])) : `<p style="color:${C.muted};font-size:14px">${empty}</p>`);
const raw = (s) => s;

function render(d, { k, notes }) {
  const title = `Website-Statistik ${monthName(YEAR, MONTH)}`;
  const tiles = [
    ["Besucher", fmt(k.visitors.cur), delta(k.visitors.delta)],
    ["Besuche", fmt(k.visits.cur), delta(k.visits.delta)],
    ["Seitenaufrufe", fmt(k.pageviews.cur), delta(k.pageviews.delta)],
    ["Absprungrate", `${Math.round(k.bounce.cur)} %`, delta(pct(k.bounce.cur, k.bounce.prev), true)],
    ["Ø Besuchsdauer", duration(k.duration.cur), delta(pct(k.duration.cur, k.duration.prev))],
  ];
  const noteColor = { warn: C.warn, good: C.good, info: C.brand };
  const goalRows = d.goals.map((g) => [
    esc(g.name), fmt(g.num), g.total ? `${(Math.round((g.num / g.total) * 1000) / 10).toLocaleString("de-DE")} %` : "–", `${fmt(g.prev)} ${delta(pct(g.num, g.prev))}`,
  ]);
  const first = num(d.funnel[0]?.visitors);
  const funnelRows = d.funnel.map((s, i) => [
    `${i + 1}. ${esc(label(s.value))}`, fmt(num(s.visitors)), first ? `${Math.round((num(s.visitors) / first) * 100)} %` : "–",
  ]);
  return `<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>${esc(title)}</title></head>
<body style="margin:0;background:${C.soft};font-family:Arial,Helvetica,sans-serif;color:${C.ink}">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="max-width:640px;width:100%;background:#ffffff;border:1px solid ${C.line}">
<tr><td style="background:${C.brand};color:#ffffff;padding:20px 24px">
  <div style="font-size:12px;letter-spacing:.06em;text-transform:uppercase;opacity:.85">www.grabnar.de</div>
  <div style="font-size:22px;font-weight:bold;margin-top:4px">${esc(title)}</div>
  <div style="font-size:13px;opacity:.85;margin-top:4px">Vergleich mit ${esc(monthName(PY, PM))}</div>
</td></tr>
<tr><td style="padding:8px 24px 24px">
${notes.length ? h2("Auf einen Blick") + `<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-size:14px">${notes.map(([kind, text]) => `<tr><td style="padding:6px 10px;border-left:3px solid ${noteColor[kind]};background:${C.soft}">${esc(text)}</td></tr><tr><td style="height:6px"></td></tr>`).join("")}</table>` : ""}
${h2("Besucher")}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="font-size:14px"><tr>
${tiles.map(([t, v, dl]) => `<td width="20%" valign="top" style="padding:10px 6px;border:1px solid ${C.line};text-align:center"><div style="color:${C.muted};font-size:12px">${t}</div><div style="font-size:19px;font-weight:bold;margin:4px 0">${v}</div><div style="font-size:12px">${dl}</div></td>`).join("\n")}
</tr></table>
${h2("Kontakte und Ziele")}
${d.goals.length ? table(["Ziel", "Besucher", "Anteil", "Vormonat"], goalRows) : `<p style="color:${C.muted};font-size:14px">Keine Ziele gefunden – deploy/umami/setup-reports.mjs ausführen.</p>`}
${list("Kontakte nach Weg", d.leadChannel)}
${list("Kontakte nach Leistung", d.leadService, "Kein Kontakt mit Leistungsbezug (kommt über die Buttons auf den Leistungsseiten).")}
${d.funnel.length ? h2("Anfrage-Weg") + table(["Schritt", "Besucher", "vom Start"], funnelRows) : ""}
${list("Meistbesuchte Seiten", d.pages, undefined, raw)}
${list("Herkunft", d.referrers, undefined, raw)}
${list("Kanäle", d.channels)}
${list("Geräte", d.devices)}
${d.utm.length ? list("Kampagnen (UTM-Quelle)", d.utm) : ""}
${list("Nicht gefundene Adressen (404)", d.notFound, "Keine – alle aufgerufenen Adressen existieren.", raw)}
<p style="font-size:12px;color:${C.muted};margin-top:28px;line-height:1.5">Automatisch erstellt aus Umami (ohne Cookies, keine Einzelpersonen).
„Besucher“ bei Zielen = Besucher mit mindestens einem Abschluss, Anteil bezogen auf alle Besucher. Zeitraum: ${esc(monthName(YEAR, MONTH))}, Zeitzone Europe/Berlin.</p>
</td></tr></table>
</td></tr></table>
</body></html>`;
}

// ---------------------------------------------------------------- main

try {
  let data;
  if (args.demo) data = demo();
  else {
    if (!UMAMI_URL || !UMAMI_API_KEY || !UMAMI_WEBSITE_ID) {
      console.error("UMAMI_URL, UMAMI_API_KEY und UMAMI_WEBSITE_ID setzen (oder --demo).");
      process.exit(2);
    }
    data = await collect();
  }
  const html = render(data, analyse(data));
  if (typeof args.out === "string") await writeFile(args.out, html);
  else process.stdout.write(html);
  console.error(`Bericht ${monthName(YEAR, MONTH)} erstellt.`);
} catch (err) {
  console.error(String(err.message ?? err));
  process.exit(1);
}
