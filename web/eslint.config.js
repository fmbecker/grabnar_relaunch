import js from "@eslint/js";
import tseslint from "typescript-eslint";
import astro from "eslint-plugin-astro";
import globals from "globals";

export default tseslint.config(
  { ignores: ["dist/", ".astro/", "node_modules/"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  ...astro.configs.recommended,
  { files: ["scripts/**/*.mjs"], languageOptions: { globals: globals.node } },
  // audit.mjs passes callbacks to page.evaluate(), which run in the browser
  { files: ["scripts/audit.mjs"], languageOptions: { globals: { ...globals.node, ...globals.browser } } },
);
