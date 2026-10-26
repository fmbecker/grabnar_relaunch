import { defineConfig } from "astro/config";
import react from "@astrojs/react";
import sitemap from "@astrojs/sitemap";
import tailwindcss from "@tailwindcss/vite";

const site = process.env.PUBLIC_SITE_URL ?? "https://www.grabnar.de";

export default defineConfig({
  site,
  output: "static",
  trailingSlash: "always",
  integrations: [react(), sitemap()],
  vite: { plugins: [tailwindcss()] },
  // Images come pre-rendered from Wagtail; Astro's optimizer is not needed.
  image: { service: { entrypoint: "astro/assets/services/noop" } },
});
