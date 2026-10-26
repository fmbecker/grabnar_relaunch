// Prints an nginx `map` body from /api/v2/redirects/ – used by deploy/build-web.sh.
// Output lines:  "/alter-pfad/" "https://www.grabnar.de/neuer-pfad/";
const api = (process.env.WAGTAIL_API_URL ?? "http://127.0.0.1:8000/api/v2").replace(/\/$/, "");
const site = (process.env.PUBLIC_SITE_URL ?? "https://www.grabnar.de").replace(/\/$/, "");
const res = await fetch(`${api}/redirects/`);
if (!res.ok) throw new Error(`redirects API ${res.status}`);
const { items } = await res.json();
const esc = (s) => s.replace(/"/g, '\\"');
for (const r of items) {
  const target = r.to.startsWith("http") ? r.to : `${site}${r.to}`;
  const from = r.from.endsWith("/") ? r.from : `${r.from}/`;
  process.stdout.write(`"${esc(r.from)}" "${esc(target)}";\n`);
  if (from !== r.from) process.stdout.write(`"${esc(from)}" "${esc(target)}";\n`);
}
