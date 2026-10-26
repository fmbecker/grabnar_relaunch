/**
 * Minimal inline icon set (Lucide-style paths, MIT). Editors reference icons by name
 * in ServicePage.icon / FeatureBlock.icon. Unknown names fall back to "sparkles".
 */
export const ICONS: Record<string, string> = {
  sparkles: "M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3zM5 19l.7 2 .7-2 2-.7-2-.7-.7-2-.7 2-2 .7 2 .7z",
  window: "M4 4h16v16H4zM4 12h16M12 4v16",
  building: "M6 21V5a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v16M9 8h2m2 0h2M9 12h2m2 0h2M9 16h2m2 0h2M3 21h18",
  layers: "M12 3l9 5-9 5-9-5 9-5zM3 13l9 5 9-5M3 17l9 5 9-5",
  wrench: "M14.7 6.3a4 4 0 0 0-5.4 5.4L3 18l3 3 6.3-6.3a4 4 0 0 0 5.4-5.4l-2.7 2.7-2.4-2.4 2.7-2.7z",
  hammer: "M15 12l-8.5 8.5a2 2 0 0 1-3-3L12 9M17.6 6.4l-2-2a2 2 0 0 0-2.8 0L9 8.2 15.8 15l3.8-3.8a2 2 0 0 0 0-2.8l-2-2z",
  snowflake: "M12 2v20M2 12h20M5 5l14 14M19 5L5 19",
  truck: "M3 7h11v9H3zM14 10h4l3 3v3h-7zM7 19a2 2 0 1 0 0-4 2 2 0 0 0 0 4zM17 19a2 2 0 1 0 0-4 2 2 0 0 0 0 4z",
  shield: "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z",
  clock: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 7v5l3 2",
  "map-pin": "M12 21s7-6.3 7-11a7 7 0 1 0-14 0c0 4.7 7 11 7 11zM12 12a2 2 0 1 0 0-4 2 2 0 0 0 0 4z",
  users: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM22 21v-2a4 4 0 0 0-3-3.9M16 3.1a4 4 0 0 1 0 7.8",
  check: "M20 6L9 17l-5-5",
  phone: "M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8.1 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.8 2z",
  mail: "M4 4h16v16H4zM4 6l8 7 8-7",
  arrow: "M5 12h14M13 6l6 6-6 6",
  briefcase: "M3 7h18v13H3zM8 7V4h8v3M3 13h18",
};

export function iconPath(name: string | undefined): string {
  return ICONS[name ?? ""] ?? ICONS.sparkles;
}
