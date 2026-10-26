// Prints an nginx `map` body from /api/v2/redirects/ – used by deploy/build-web.sh.
// Nginx matches the *decoded* $uri; we still emit percent-encoded variants and
// with/without trailing slash so every form an old link might use is covered.
//   "/Gebäudereinigung/Baureinigung/" "https://www.grabnar.de/gebaeudereinigung/baureinigung/";
const api = (process.env.WAGTAIL_API_URL ?? "http://127.0.0.1:8000/api/v2").replace(/\/$/, "");
const site = (process.env.PUBLIC_SITE_URL ?? "https://www.grabnar.de").replace(/\/$/, "");
const res = await fetch(`${api}/redirects/`);
if (!res.ok) throw new Error(`redirects API ${res.status}`);
const { items } = await res.json();
const esc = (s) => s.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
const seen = new Set();
for (const r of items) {
  const target = r.to.startsWith("http") ? r.to : `${site}${r.to}`;
  const base = r.from.replace(/\/$/, "") || "/";
  const variants = new Set([base, `${base}/`]);
  for (const v of [...variants]) variants.add(encodeURI(v));
  for (const from of variants) {
    if (from === "/" || from === "//" || seen.has(from)) continue;
    seen.add(from);
    process.stdout.write(`"${esc(from)}" "${esc(target)}";\n`);
  }
}
