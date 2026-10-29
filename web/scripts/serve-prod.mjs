#!/usr/bin/env node
/**
 * Local stand-in for deploy/nginx/grabnar.conf – for audits and testing the production
 * delivery without Nginx:
 *   - static files from dist/client with gzip/brotli and the same cache headers
 *   - /media/, /api/, /documents/, /admin/ proxied to the CMS (default 127.0.0.1:8000)
 *   - /preview/ proxied to the SSR preview server (default 127.0.0.1:4322)
 *
 * Usage: node scripts/serve-prod.mjs [--port 8080] [--cms http://127.0.0.1:8000] [--ssr http://127.0.0.1:4322]
 * Build first with same-origin URLs:  WAGTAIL_MEDIA_URL= PUBLIC_FORMS_API_URL=/api/forms pnpm build
 */
import { createReadStream, existsSync, statSync } from "node:fs";
import { request } from "node:http";
import { createServer } from "node:http";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";
import { constants, createBrotliCompress, createGzip } from "node:zlib";

const args = Object.fromEntries(
  process.argv.slice(2).reduce((acc, a, i, arr) => (a.startsWith("--") ? [...acc, [a.slice(2), arr[i + 1]]] : acc), []),
);
const PORT = Number(args.port ?? 8080);
const CMS = new URL(args.cms ?? "http://127.0.0.1:8000");
const SSR = new URL(args.ssr ?? "http://127.0.0.1:4322");
const ROOT = fileURLToPath(new URL("../dist/client/", import.meta.url));

const TYPES = {
  ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript", ".mjs": "text/javascript",
  ".json": "application/json", ".svg": "image/svg+xml", ".png": "image/png", ".webp": "image/webp",
  ".jpg": "image/jpeg", ".ico": "image/x-icon", ".xml": "application/xml", ".txt": "text/plain",
  ".woff2": "font/woff2",
};
const COMPRESSIBLE = new Set([".html", ".css", ".js", ".mjs", ".json", ".svg", ".xml", ".txt"]);
const SECURITY = {
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "SAMEORIGIN",
  "Referrer-Policy": "strict-origin-when-cross-origin",
};

function proxy(req, res, target) {
  const upstream = request(
    { hostname: target.hostname, port: target.port, path: req.url, method: req.method, headers: { ...req.headers, host: target.host, "x-forwarded-proto": "http" } },
    (up) => {
      const headers = { ...up.headers };
      if (req.url.startsWith("/media/")) headers["cache-control"] = "public, max-age=2592000";
      res.writeHead(up.statusCode ?? 502, headers);
      up.pipe(res);
    },
  );
  upstream.on("error", () => { res.writeHead(502); res.end("upstream error"); });
  req.pipe(upstream);
}

function resolveFile(urlPath) {
  const clean = normalize(decodeURIComponent(urlPath.split("?")[0])).replace(/^(\.\.[/\\])+/, "");
  for (const candidate of [clean, join(clean, "index.html"), `${clean}/index.html`]) {
    const file = join(ROOT, candidate);
    if (file.startsWith(ROOT) && existsSync(file) && statSync(file).isFile()) return file;
  }
  return null;
}

createServer((req, res) => {
  const url = req.url ?? "/";
  if (/^\/(media|api|documents|admin|django-admin|django-static)\//.test(url)) return proxy(req, res, CMS);
  if (url.startsWith("/preview/")) return proxy(req, res, SSR);

  let file = resolveFile(url);
  let status = 200;
  if (!file) { file = join(ROOT, "404.html"); status = 404; }
  const ext = extname(file);
  const headers = { "Content-Type": TYPES[ext] ?? "application/octet-stream", ...SECURITY, Vary: "Accept-Encoding" };
  headers["Cache-Control"] = url.startsWith("/_astro/") ? "public, max-age=31536000, immutable" : ext === ".html" ? "no-cache" : "public, max-age=86400";

  const accept = String(req.headers["accept-encoding"] ?? "");
  let stream = createReadStream(file);
  if (COMPRESSIBLE.has(ext) && accept.includes("br")) {
    headers["Content-Encoding"] = "br";
    stream = stream.pipe(createBrotliCompress({ params: { [constants.BROTLI_PARAM_QUALITY]: 5 } }));
  } else if (COMPRESSIBLE.has(ext) && accept.includes("gzip")) {
    headers["Content-Encoding"] = "gzip";
    stream = stream.pipe(createGzip());
  }
  res.writeHead(status, headers);
  stream.pipe(res);
}).listen(PORT, "127.0.0.1", () => console.log(`serve-prod: http://127.0.0.1:${PORT}  (cms ${CMS.origin}, preview ${SSR.origin})`));
