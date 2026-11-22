import { defineConfig } from "astro/config";
import node from "@astrojs/node";
import react from "@astrojs/react";
import sitemap from "@astrojs/sitemap";
import tailwindcss from "@tailwindcss/vite";

// Domain comes from the build environment (deploy/web.env); see web/src/lib/site.ts.
const site = process.env.PUBLIC_SITE_URL ?? "http://localhost:4321";

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
  // Content-Security-Policy as <meta> in every page; Astro adds hashes for its own scripts and
  // styles. img-src, connect-src and frame-src depend on settings and are added per page
  // (src/lib/csp.ts). frame-ancestors can't be set in a <meta>: Nginx sends X-Frame-Options.
  security: {
    csp: {
      directives: [
        "default-src 'self'",
        "base-uri 'self'",
        "object-src 'none'",
        "form-action 'self'",
        "font-src 'self'",
        "manifest-src 'self'",
      ],
    },
  },
});
