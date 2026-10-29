/**
 * Block contract with cms/blocks/blocks.py.
 * Every block type here has exactly one component in src/components/blocks/.
 */

export interface Rendition {
  url: string;
  width: number;
  height: number;
}

export interface ApiImage {
  id: number;
  title: string;
  alt: string;
  width: number;
  height: number;
  renditions: Record<"thumb" | "card" | "wide" | "hero" | "full", Rendition>;
}

export interface ApiLink {
  label: string;
  href: string;
  external: boolean;
  style: "primary" | "secondary" | "link";
}

export interface ServiceSummary {
  title: string;
  href: string;
  teaser: string;
  icon: string;
  image: ApiImage | null;
  /** Only for categories (ServiceIndexPage): the services below it. */
  children?: { title: string; href: string }[];
}

export type EmploymentType = "FULL_TIME" | "PART_TIME" | "MINI_JOB" | "TEMPORARY" | "APPRENTICE";

export interface JobSummary {
  id: number;
  title: string;
  href: string;
  location: string;
  employment_type: EmploymentType;
  employment_type_label: string;
  start_date: string;
  teaser: string;
  valid_through: string | null;
}

// ---- Blocks ---------------------------------------------------------------

export interface HeroValue {
  headline: string;
  subline: string;
  image: ApiImage | null;
  links: ApiLink[];
}

export interface TextImageValue {
  heading: string;
  text: string; // rich text HTML
  image: ApiImage;
  image_position: "left" | "right";
  link: ApiLink | null;
}

export interface ServiceGridValue {
  heading: string;
  intro: string;
  /** "categories" = tiles for ServiceIndexPages (with children), "services" = ServicePages */
  kind: "categories" | "services";
  services: ServiceSummary[];
}

export interface FeatureListValue {
  heading: string;
  features: { icon: string; title: string; text: string }[];
}

export interface StatsValue {
  stats: { value: string; label: string }[];
}

export interface TestimonialValue {
  quote: string;
  name: string;
  company: string;
}

export interface FaqValue {
  heading: string;
  items: { question: string; answer: string }[];
}

export interface CtaValue {
  heading: string;
  text: string;
  link: ApiLink;
}

export interface ContactFormValue {
  heading: string;
  intro: string;
  variant: "contact" | "application";
  success_message: string;
}

export interface JobListValue {
  heading: string;
  show_filter: boolean;
  empty_text: string;
  jobs: JobSummary[];
}

export interface MapValue {
  heading: string;
  zoom: number;
}

export interface GalleryValue {
  heading: string;
  images: ApiImage[];
}

export type Block =
  | { type: "rich_text"; id: string; value: string }
  | { type: "text_image"; id: string; value: TextImageValue }
  | { type: "service_grid"; id: string; value: ServiceGridValue }
  | { type: "feature_list"; id: string; value: FeatureListValue }
  | { type: "stats"; id: string; value: StatsValue }
  | { type: "testimonial"; id: string; value: TestimonialValue }
  | { type: "faq"; id: string; value: FaqValue }
  | { type: "cta"; id: string; value: CtaValue }
  | { type: "contact_form"; id: string; value: ContactFormValue }
  | { type: "job_list"; id: string; value: JobListValue }
  | { type: "map"; id: string; value: MapValue }
  | { type: "gallery"; id: string; value: GalleryValue };

export type BlockType = Block["type"];

// ---- Pages ----------------------------------------------------------------

export type PageType =
  | "home.HomePage"
  | "home.StandardPage"
  | "services.ServiceIndexPage"
  | "services.ServicePage"
  | "jobs.JobIndexPage"
  | "jobs.JobPage";

export interface PageMeta {
  type: PageType;
  detail_url: string;
  html_url: string;
  slug: string;
  show_in_menus: boolean;
  seo_title: string;
  search_description: string;
  first_published_at: string | null;
  parent?: { id: number; meta: { type: string; html_url: string }; title: string } | null;
}

export interface BasePageData {
  id: number;
  meta: PageMeta;
  title: string;
  og_image: ApiImage | null;
  hide_from_sitemap: boolean;
  last_published_at: string | null;
}

export interface HomePageData extends BasePageData {
  meta: PageMeta & { type: "home.HomePage" };
  hero: { type: "hero"; id: string; value: HeroValue }[];
  body: Block[];
}

export interface StandardPageData extends BasePageData {
  meta: PageMeta & { type: "home.StandardPage" | "services.ServiceIndexPage" | "jobs.JobIndexPage" };
  intro: string;
  body: Block[];
}

export interface ServicePageData extends BasePageData {
  meta: PageMeta & { type: "services.ServicePage" };
  icon: string;
  teaser: string;
  hero_image: ApiImage | null;
  body: Block[];
  related: ServiceSummary[];
}

export interface JobPageData extends BasePageData {
  meta: PageMeta & { type: "jobs.JobPage" };
  location: string;
  employment_type: EmploymentType;
  employment_type_label: string;
  start_date: string;
  teaser: string;
  tasks: string;
  requirements: string;
  benefits: string;
  salary_note: string;
  valid_through: string | null;
  show_apply_form: boolean;
  first_published_at: string | null;
}

export type PageData = HomePageData | StandardPageData | ServicePageData | JobPageData;

// ---- Settings / navigation -----------------------------------------------

export interface ContactSettings {
  company_name: string;
  street: string;
  postal_code: string;
  city: string;
  phone: string;
  fax: string;
  email: string;
  opening_hours: string[];
  latitude: number | null;
  longitude: number | null;
  service_area: string;
}

export interface LogoImage {
  url: string;
  url2x: string;
  width: number;
  height: number;
  alt: string;
}

export interface SiteSettings {
  logo: LogoImage | null;
  tagline: string;
  footer_text: string;
  default_og_image: ApiImage | null;
  footer_links: { label: string; href: string; external: boolean }[];
  social_links: { platform: string; url: string }[];
  analytics: { script_url: string; site_id: string } | null;
}

export interface Settings {
  contact: ContactSettings;
  site: SiteSettings;
}

export interface NavItem {
  id: number;
  title: string;
  href: string;
  children?: NavItem[];
}

export interface Navigation {
  home: NavItem;
  items: NavItem[];
}

export interface RedirectItem {
  from: string;
  to: string;
  status: 301 | 302;
}

// ---- Type guards (TS cannot narrow on the nested meta.type discriminant) ---

export const isHomePage = (p: PageData): p is HomePageData => p.meta.type === "home.HomePage";
export const isStandardPage = (p: PageData): p is StandardPageData =>
  p.meta.type === "home.StandardPage" ||
  p.meta.type === "services.ServiceIndexPage" ||
  p.meta.type === "jobs.JobIndexPage";
export const isServicePage = (p: PageData): p is ServicePageData => p.meta.type === "services.ServicePage";
export const isJobPage = (p: PageData): p is JobPageData => p.meta.type === "jobs.JobPage";
