/**
 * Client for the Wagtail API v2 (cms/grabnar/api.py).
 * Runs only on the server: at build time (static pages) and in the SSR preview
 * route (/preview/). Never in the browser.
 *
 * Responses are memoised for the duration of a static build. The preview route
 * passes { fresh: true } so drafts, settings and navigation are always current
 * in the long-running preview server.
 */

import type { ApiImage, Navigation, PageData, PageType, RedirectItem, Settings } from "./types";

// Runtime env (preview server) wins over build-time values.
const runtimeEnv = (key: string): string | undefined =>
  typeof process !== "undefined" ? process.env[key] : undefined;
const API_URL = (runtimeEnv("WAGTAIL_API_URL") ?? import.meta.env.WAGTAIL_API_URL ?? "http://127.0.0.1:8000/api/v2").replace(/\/$/, "");
const MEDIA_URL = (runtimeEnv("WAGTAIL_MEDIA_URL") ?? import.meta.env.WAGTAIL_MEDIA_URL ?? "").replace(/\/$/, "");

const PAGE_TYPES: PageType[] = [
  "home.HomePage",
  "home.StandardPage",
  "services.ServiceIndexPage",
  "services.ServicePage",
  "jobs.JobIndexPage",
  "jobs.JobPage",
];

const cache = new Map<string, unknown>();

export interface FetchOptions {
  /** Bypass the build-time memo cache (used by the SSR preview). */
  fresh?: boolean;
}

export class WagtailApiError extends Error {
  constructor(
    public status: number,
    url: string,
  ) {
    super(`Wagtail API ${status} for ${url}`);
  }
}

async function get<T>(path: string, params: Record<string, string> = {}, opts: FetchOptions = {}): Promise<T> {
  const url = new URL(`${API_URL}${path}`);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const key = url.toString();
  if (!opts.fresh && cache.has(key)) return cache.get(key) as T;
  const res = await fetch(url, opts.fresh ? { cache: "no-store" } : undefined);
  if (!res.ok) throw new WagtailApiError(res.status, key);
  const data = (await res.json()) as T;
  if (!opts.fresh) cache.set(key, data);
  return data;
}

/** Turn a relative /media/... URL into an absolute one for the build host. */
export function mediaUrl(url: string): string {
  return url.startsWith("http") ? url : `${MEDIA_URL}${url}`;
}

/** Rewrite all rendition URLs in an image so <img src> works in dev and prod. */
export function withMedia<T extends ApiImage | null>(image: T): T {
  if (!image) return image;
  const renditions = Object.fromEntries(
    Object.entries(image.renditions).map(([k, r]) => [k, { ...r, url: mediaUrl(r.url) }]),
  ) as ApiImage["renditions"];
  return { ...image, renditions };
}

/** Path part of Wagtail's html_url, always with trailing slash. */
export function pathFromHtmlUrl(htmlUrl: string): string {
  const p = new URL(htmlUrl).pathname;
  return p.endsWith("/") ? p : `${p}/`;
}

interface ListResponse<T> {
  meta: { total_count: number };
  items: T[];
}

export async function getAllPages(): Promise<PageData[]> {
  const pages: PageData[] = [];
  for (const type of PAGE_TYPES) {
    let offset = 0;
    for (;;) {
      const res = await get<ListResponse<PageData>>("/pages/", {
        type,
        fields: "*",
        limit: "100",
        offset: String(offset),
      });
      pages.push(...res.items);
      offset += res.items.length;
      if (offset >= res.meta.total_count || res.items.length === 0) break;
    }
  }
  return pages;
}

export async function getPage(id: number): Promise<PageData> {
  return get<PageData>(`/pages/${id}/`);
}

/** Draft behind a wagtail-headless-preview token. Throws WagtailApiError(404) if invalid/expired. */
export async function getPreviewPage(contentType: string, token: string): Promise<PageData> {
  return get<PageData>("/page_preview/", { content_type: contentType, token }, { fresh: true });
}

export async function getSettings(opts: FetchOptions = {}): Promise<Settings> {
  const s = await get<Settings>("/settings/", {}, opts);
  return {
    ...s,
    site: {
      ...s.site,
      logo: s.site.logo
        ? { ...s.site.logo, url: mediaUrl(s.site.logo.url), url2x: mediaUrl(s.site.logo.url2x) }
        : null,
      default_og_image: withMedia(s.site.default_og_image),
      certificate: s.site.certificate
        ? {
            ...s.site.certificate,
            seal: { ...s.site.certificate.seal, url: mediaUrl(s.site.certificate.seal.url), url2x: mediaUrl(s.site.certificate.seal.url2x) },
            document_url: s.site.certificate.document_url ? mediaUrl(s.site.certificate.document_url) : "",
          }
        : null,
    },
  };
}

export async function getNavigation(opts: FetchOptions = {}): Promise<Navigation> {
  return get<Navigation>("/navigation/", {}, opts);
}

export async function getRedirects(): Promise<RedirectItem[]> {
  return (await get<{ items: RedirectItem[] }>("/redirects/")).items;
}

/** Deep-rewrite media URLs inside a page payload (hero/body/images). */
export function normalizePage<T extends PageData>(page: T): T {
  if (!MEDIA_URL) return page;
  const walk = (v: unknown): unknown => {
    if (Array.isArray(v)) return v.map(walk);
    if (v && typeof v === "object") {
      const o = v as Record<string, unknown>;
      if ("renditions" in o && "alt" in o) return withMedia(o as unknown as ApiImage);
      // Fixed-height images (logo, seal) and document links inside blocks.
      if ("url2x" in o && typeof o.url === "string" && typeof o.url2x === "string")
        return { ...o, url: mediaUrl(o.url), url2x: mediaUrl(o.url2x) };
      if (typeof o.document_url === "string" && o.document_url)
        return Object.fromEntries(
          Object.entries(o).map(([k, val]) => [k, k === "document_url" ? mediaUrl(val as string) : walk(val)]),
        );
      return Object.fromEntries(Object.entries(o).map(([k, val]) => [k, walk(val)]));
    }
    return v;
  };
  return walk(page) as T;
}
