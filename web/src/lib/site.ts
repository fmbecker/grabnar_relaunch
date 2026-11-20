/**
 * Public address of the site and whether search engines may index it – both set at build time
 * (deploy/web.env on the server, web/.env locally).
 *
 * The site first runs under a staging domain (mbg.aivii.de, behind basic auth) and moves to
 * www.grabnar.de once DNS is switched (docs/09-domainumzug.md). Canonical, Open Graph, sitemap,
 * JSON-LD and robots.txt all derive from these two values, so moving the domain is a rebuild.
 */
export const SITE_URL: string = import.meta.env.PUBLIC_SITE_URL ?? "http://localhost:4321";

export const SITE_HOST: string = new URL(SITE_URL).hostname;

/** Indexing has to be switched on explicitly: a forgotten variable must never get staging indexed. */
export const ALLOW_INDEXING: boolean = import.meta.env.PUBLIC_ALLOW_INDEXING === "true";

/** True for links to this site – the build's domain or whatever host the page is served from. */
export function isOwnHost(hostname: string): boolean {
  if (hostname === SITE_HOST) return true;
  return typeof location !== "undefined" && hostname === location.hostname;
}
