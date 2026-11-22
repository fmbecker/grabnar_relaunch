import type { APIRoute } from "astro";
import { ALLOW_INDEXING, SITE_URL } from "@/lib/site";

// Staging (PUBLIC_ALLOW_INDEXING != "true") blocks everything; every page also carries
// <meta name="robots" content="noindex"> and Nginx adds X-Robots-Tag (deploy/nginx/).
const INDEXED = `User-agent: *
Allow: /
Disallow: /preview/
Disallow: /admin/
Sitemap: ${new URL("/sitemap-index.xml", SITE_URL)}
`;

const BLOCKED = `User-agent: *
Disallow: /
`;

export const GET: APIRoute = () =>
  new Response(ALLOW_INDEXING ? INDEXED : BLOCKED, {
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
