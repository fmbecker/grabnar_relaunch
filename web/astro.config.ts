import { defineConfig } from "astro/config";
import node from "@astrojs/node";
import react from "@astrojs/react";
import sitemap from "@astrojs/sitemap";
import tailwindcss from "@tailwindcss/vite";

const site = process.env.PUBLIC_SITE_URL ?? "https://www.grabnar.de";

export default defineConfig({
  site,
  // Static site; only /preview/ (prerender = false) is rendered on demand by the
  // Node server in dist/server/ – see deploy/systemd/grabnar-preview.service.
  output: "static",
  adapter: node({ mode: "standalone" }),
  trailingSlash: "always",
  integrations: [react(), sitemap({ filter: (page) => !page.includes("/preview/") })],
  vite: { plugins: [tailwindcss()] },
  // Images come pre-rendered from Wagtail; Astro's optimizer is not needed.
  image: { service: { entrypoint: "astro/assets/services/noop" } },
});
