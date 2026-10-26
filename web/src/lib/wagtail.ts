/**
 * Build-time client for the Wagtail API v2 (cms/grabnar/api.py).
 * Runs only on the server (getStaticPaths / frontmatter); never in the browser.
 */

import type { ApiImage, Navigation, PageData, PageType, RedirectItem, Settings } from "./types";

const API_URL = (import.meta.env.WAGTAIL_API_URL ?? "http://127.0.0.1:8000/api/v2").replace(/\/$/, "");
const MEDIA_URL = (import.meta.env.WAGTAIL_MEDIA_URL ?? "").replace(/\/$/, "");

const PAGE_TYPES: PageType[] = [
  "home.HomePage",
  "home.StandardPage",
  "services.ServiceIndexPage",
  "services.ServicePage",
  "jobs.JobIndexPage",
  "jobs.JobPage",
];

const cache = new Map<string, unknown>();

async function get<T>(path: string, params: Record<string, string> = {}): Promise<T> {
  const url = new URL(`${API_URL}${path}`);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const key = url.toString();
  if (cache.has(key)) return cache.get(key) as T;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Wagtail API ${res.status} for ${url}`);
  const data = (await res.json()) as T;
  cache.set(key, data);
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

export async function getSettings(): Promise<Settings> {
  const s = await get<Settings>("/settings/");
  return {
    ...s,
    site: {
      ...s.site,
      logo: withMedia(s.site.logo),
      default_og_image: withMedia(s.site.default_og_image),
    },
  };
}

export async function getNavigation(): Promise<Navigation> {
  return get<Navigation>("/navigation/");
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
      return Object.fromEntries(Object.entries(o).map(([k, val]) => [k, walk(val)]));
    }
    return v;
  };
  return walk(page) as T;
}
