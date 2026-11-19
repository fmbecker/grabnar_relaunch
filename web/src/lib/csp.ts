/**
 * Content-Security-Policy helpers. Astro writes the policy as a <meta> tag into every page
 * (astro.config.ts → security.csp) and adds hashes for its own scripts and styles itself.
 * Sources that depend on settings or env – media host, forms API, Umami, the job portal –
 * are added per page with Astro.csp in Base.astro – there, because Astro writes the <meta> tag
 * when it reaches <head>: entries added later by components in <body> would be missing.
 *
 * Each directive may be set only once per page: browsers ignore a repeated directive.
 */
import { createHash } from "node:crypto";

/** Origin of an absolute http(s) URL, "" for relative URLs or garbage. */
export function originOf(url: string | null | undefined): string {
  if (!url || !/^https?:\/\//i.test(url)) return "";
  try {
    return new URL(url).origin;
  } catch {
    return "";
  }
}

/** "'self' a b" from a list of origins, without empties or duplicates. */
export function sources(...origins: string[]): string {
  return ["'self'", ...new Set(origins.filter(Boolean))].join(" ");
}

/** CSP hash of an inline script or style body, as Astro.csp.insertScriptHash expects it. */
export function sha256(code: string): `sha256-${string}` {
  return `sha256-${createHash("sha256").update(code).digest("base64")}`;
}

/** Origins of all job portal embeds in a page (blocks of type job_embed, at any depth) for frame-src. */
export function frameOrigins(page: unknown): string[] {
  const found = new Set<string>();
  const walk = (v: unknown): void => {
    if (Array.isArray(v)) return v.forEach(walk);
    if (!v || typeof v !== "object") return;
    const o = v as { type?: unknown; value?: { url?: unknown } };
    if (o.type === "job_embed" && typeof o.value?.url === "string") found.add(originOf(o.value.url));
    Object.values(o).forEach(walk);
  };
  walk(page);
  found.delete("");
  return [...found];
}
