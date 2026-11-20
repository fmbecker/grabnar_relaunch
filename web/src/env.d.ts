/// <reference types="astro/client" />

interface ImportMetaEnv {
  readonly WAGTAIL_API_URL: string;
  readonly WAGTAIL_MEDIA_URL: string;
  readonly PUBLIC_SITE_URL: string;
  /** "true" only for the live domain – everything else is noindex (web/src/lib/site.ts). */
  readonly PUBLIC_ALLOW_INDEXING?: string;
  readonly PUBLIC_FORMS_API_URL: string;
}
interface ImportMeta {
  readonly env: ImportMetaEnv;
}
