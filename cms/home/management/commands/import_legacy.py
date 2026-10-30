# ruff: noqa: E501
"""Import the content of the old site (Wagtail 2.14 / coderedcms) into the new page tree.

Sources (both in the repo, produced from the DB export of the old site):
  docs/content-export/*.md   one Markdown file per old page
  docs/redirects.csv         old URL -> new URL mapping
  docs/content-overrides.csv editorial texts per new URL (Kurztext, Einleitung, SEO),
                             semicolon-separated, UTF-8 with BOM (opens in Excel)
  docs/content-neu/*.md      rewritten body texts per new URL (services, home, Unternehmen);
                             they replace the legacy body unless --originaltexte is given

Builds:
  /                                   HomePage
  /<kategorie>/                       ServiceIndexPage  (4 categories)
  /<kategorie>/<leistung>/            ServicePage       (22 services)
  /karriere/                          JobIndexPage
  /kontakt/  /impressum/  /datenschutz/  /agb/   StandardPage
plus ContactSettings/SiteSettings and all 301 redirects.

Destructive: replaces the whole page tree below the default site root.

Usage:
  uv run manage.py import_legacy
  uv run manage.py import_legacy --source /path/to/docs     # e.g. inside Docker
  uv run manage.py import_legacy --originaltexte            # legacy bodies, ignore content-neu/
"""

from __future__ import annotations

import csv
import re
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path

import markdown
from django.conf import settings
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from wagtail.contrib.redirects.models import Redirect
from wagtail.images.models import Image
from wagtail.models import Page, Site

from home.models import HomePage, StandardPage
from jobs.models import JobIndexPage
from services.models import RelatedService, ServiceIndexPage, ServicePage
from site_settings.models import ContactSettings, FooterLink, SiteSettings

DEFAULT_SOURCE = Path(settings.BASE_DIR).parent / "docs"

# New slug -> frontend icon name (web/src/lib/icons.ts)
ICONS = {
    "gebaeudereinigung": "sparkles",
    "baureinigung": "building",
    "containerreinigung": "layers",
    "desinfektion": "shield",
    "glasreinigung": "window",
    "grundreinigung": "sparkles",
    "industriereinigung": "building",
    "sonderreinigung": "check",
    "polsterreinigung": "layers",
    "unterhaltsreinigung": "sparkles",
    "gebaeudedienste": "wrench",
    "gruenanlagenpflege": "leaf",
    "hausmeisterdienste": "wrench",
    "winterdienst": "snowflake",
    "handwerkerdienste": "hammer",
    "bauhilfsarbeiten": "hammer",
    "bodenverlegerarbeiten": "grid",
    "fliesenlegerarbeiten": "grid",
    "malerarbeiten": "brush",
    "trockenbau": "building",
    "bodenversiegelung": "layers",
    "services": "briefcase",
    "entruempelung": "truck",
    "arbeitnehmerueberlassung": "users",
    "transportarbeiten": "truck",
    "wachdienste": "shield",
}

# Company facts for "Unternehmen" and the home page. Every item restates something the
# old site says; the source file in docs/content-export/ is noted. Do not add claims here
# that are not backed by the company.
FEATURES = [
    (
        "check",
        "Meisterbetrieb",
        "Fachliche Leitung durch einen Meister des Gebäudereinigerhandwerks.",
        "home.md",
    ),
    (
        "shield",
        "Qualität nach ISO 9001",
        "Zertifiziertes Qualitätsmanagement für eine vertragsgemäße und hygienische Reinigung.",
        "gebäudereinigung__unterhaltsreinigung.md; ISO 9001 von der Firma bestätigt (30.10.2026)",
    ),
    (
        "leaf",
        "Umwelt nach ISO 14001",
        "Zertifiziertes Umweltmanagement, strenge Umweltleitlinien und umweltgerechte Entsorgung über zertifizierte Entsorgungsunternehmen.",
        "gebäudereinigung__unterhaltsreinigung.md, services__entrümpelung.md; ISO 14001 von der Firma bestätigt (30.10.2026)",
    ),
    (
        "users",
        "Geschultes Fachpersonal",
        "Fachgeschulte Mitarbeiter mit leistungsstarken, hocheffizienten Geräten.",
        "gebäudereinigung__desinfektion.md, gebäudedienste__winterdienst.md",
    ),
    (
        "clock",
        "Langjährige Erfahrung",
        "Jahrelanges Know-how, um auf die verschiedensten Kundenbedürfnisse einzugehen.",
        "gebäudereinigung__*.md",
    ),
    (
        "map-pin",
        "Firmensitz in Stuttgart",
        "Logistisches und technisches Zentrum mit Personal und Ausstattung am Firmensitz in Stuttgart.",
        "home.md",
    ),
]

LEGAL = ["impressum", "datenschutz", "agb"]
SKIP = {"/kontaktformular/", "/kontaktformular/form/", "/danke/", "/stellenangebote/", "/kontakt/"}


def fix_spelling(text: str) -> str:
    """Small corrections of the old texts (keep this list short and obvious)."""
    return re.sub(r"\bIFSG\b", "IfSG", text)


def join_de(items: list[str]) -> str:
    """'a, b und c' – German enumeration."""
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " und " + items[-1]


@dataclass
class LegacyPage:
    title: str
    old_path: str
    new_path: str
    seo_title: str = ""
    description: str = ""
    body_md: str = ""
    children: list[LegacyPage] = field(default_factory=list)

    @property
    def slug(self) -> str:
        return self.new_path.strip("/").split("/")[-1] or "home"


class Command(BaseCommand):
    help = "Import pages, settings and redirects of the old site."

    def add_arguments(self, parser):
        parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="docs/ directory")
        parser.add_argument(
            "--originaltexte",
            action="store_true",
            help="Fließtexte der Altseite verwenden und docs/content-neu/ ignorieren",
        )

    # ------------------------------------------------------------------ parsing

    @staticmethod
    def load_overrides(source: Path) -> dict[str, dict[str, str]]:
        """docs/content-overrides.csv -> {new path: {column: value}} (empty values dropped)."""
        path = source / "content-overrides.csv"
        if not path.is_file():
            return {}
        with path.open(newline="", encoding="utf-8-sig") as f:
            return {
                row["pfad"]: {k: v.strip() for k, v in row.items() if v and v.strip()}
                for row in csv.DictReader(f, delimiter=";")
            }

    @staticmethod
    def load_rewrites(source: Path) -> dict[str, str]:
        """docs/content-neu/*.md -> {new path: body markdown below the '---' line}."""
        folder = source / "content-neu"
        rewrites: dict[str, str] = {}
        for md_file in sorted(folder.glob("*.md")) if folder.is_dir() else []:
            if md_file.name == "README.md":
                continue
            head, sep, body = md_file.read_text(encoding="utf-8").partition("\n---\n")
            path = re.search(r"^- Pfad: `([^`]+)`", head, re.M)
            if not (sep and path):
                raise CommandError(f"{md_file}: Kopf mit '- Pfad:' und Trennlinie '---' fehlt.")
            rewrites[path.group(1)] = body.strip()
        return rewrites

    def load(self, source: Path) -> tuple[dict[str, LegacyPage], dict[str, str]]:
        export = source / "content-export"
        csv_path = source / "redirects.csv"
        if not export.is_dir() or not csv_path.is_file():
            raise CommandError(f"Expected {export}/ and {csv_path} – use --source.")

        mapping: dict[str, str] = {}
        with csv_path.open(newline="") as f:
            for row in csv.DictReader(f):
                mapping[row["alt"]] = row["neu"]

        pages: dict[str, LegacyPage] = {}
        for md_file in sorted(export.glob("*.md")):
            if md_file.name == "README.md":
                continue
            text = md_file.read_text()
            head, _, body = text.partition("\n---\n")
            title = re.search(r"^# (.+)$", head, re.M)
            old = re.search(r"Alte URL: `([^`]+)`", head)
            if not (title and old):
                continue
            old_path = old.group(1)
            seo = re.search(r"^- SEO-Titel: (.+)$", head, re.M)
            desc = re.search(r"^- Meta-Description: (.+)$", head, re.M)
            pages[old_path] = LegacyPage(
                title=fix_spelling(title.group(1).strip()),
                old_path=old_path,
                new_path=mapping.get(old_path, old_path),
                seo_title=seo.group(1).strip() if seo else "",
                description=desc.group(1).strip() if desc else "",
                body_md=fix_spelling(body.strip()),
            )
        return pages, mapping

    def to_html(self, md: str, title: str, mapping: dict[str, str]) -> str:
        lines = md.splitlines()
        # Drop the leading "## <title>" (and duplicates of it) – the page title renders it.
        while lines and (not lines[0].strip() or lines[0].lstrip("# ").strip() == title):
            lines.pop(0)
        md = "\n".join(lines)
        if md.strip() == "_(kein Fließtext)_":
            return ""

        # Only h2/h3 are allowed in the new rich text; the old site used h4/h5 as body text.
        md = re.sub(r"^#{4,6}\s+", "### ", md, flags=re.M)

        # Lines joined with "  \n" (old <br> lists) become proper bullet lists.
        blocks = re.split(r"\n\s*\n", md)
        out = []
        for block in blocks:
            rows = block.split("\n")
            if (
                len(rows) >= 2
                and all(r.endswith("  ") for r in rows[:-1])
                and not any(r.lstrip().startswith(("#", "-", "*", ">", "|")) for r in rows)
            ):
                out.append("\n".join(f"- {r.strip()}" for r in rows if r.strip()))
            else:
                out.append(block)
        md = "\n\n".join(out)

        # Rewrite absolute links to the old site to the new paths.
        def relink(m: re.Match) -> str:
            path = urllib.parse.unquote(urllib.parse.urlparse(m.group(2)).path) or "/"
            if not path.endswith("/"):
                path += "/"
            return f"[{m.group(1)}]({mapping.get(path, path)})"

        md = re.sub(r"\[([^\]]+)\]\((https?://(?:www\.)?grabnar\.de[^)]*)\)", relink, md)
        return self.normalize_headings(markdown.markdown(md, output_format="html"))

    @staticmethod
    def normalize_headings(html: str) -> str:
        """Shift headings so the body starts at <h2> (the page title is the <h1>).

        Old service texts jump from the title straight to <h3> ("Unsere Dienstleistungen
        im Einzelnen"), which breaks the heading order for screen readers (WCAG 1.3.1).
        """
        levels = [int(n) for n in re.findall(r"<h([1-6])\b", html)]
        if not levels:
            return html
        shift = 2 - min(levels)
        if shift == 0:
            return html

        def repl(m: re.Match) -> str:
            level = min(6, max(2, int(m.group(2)) + shift))
            return f"<{m.group(1)}h{level}"

        return re.sub(r"<(/?)h([1-6])", repl, html)

    @staticmethod
    def teaser(html: str, limit: int = 190) -> str:
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) <= limit:
            return text
        sentences = re.split(r"(?<=[.!?])\s+", text)
        result = ""
        for s in sentences:
            if len(result) + len(s) + 1 > limit:
                break
            result = f"{result} {s}".strip()
        return result or text[: limit - 1].rsplit(" ", 1)[0] + "…"

    @classmethod
    def split_lead(cls, html: str, limit: int = 190) -> tuple[str, str]:
        """Take the first sentence(s) of the first paragraph as teaser and remove them
        from the body, so the hero teaser is not repeated at the start of the text."""
        m = re.search(r"<p>(.*?)</p>", html, re.S)
        if not m:
            return cls.teaser(html, limit), html
        paragraph = m.group(1)
        plain = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", paragraph)).strip()
        sentences = re.split(r"(?<=[.!?])\s+", plain)
        lead = sentences[0]
        for sentence in sentences[1:]:
            if len(lead) + len(sentence) + 1 > limit:
                break
            lead = f"{lead} {sentence}"
        if len(lead) > limit or "<" in paragraph:  # long first sentence or inline markup
            return cls.teaser(html, limit), html
        rest = plain[len(lead) :].strip()
        new_p = f"<p>{rest}</p>" if rest else ""
        return lead, html[: m.start()] + new_p + html[m.end() :]

    @staticmethod
    def import_logo(source: Path) -> Image | None:
        """docs/assets/logo-mbgrabnar.png -> Wagtail image (reused if already imported)."""
        path = source / "assets" / "logo-mbgrabnar.png"
        if not path.is_file():
            return None
        title = "Logo M. B. Grabnar GmbH"
        existing = Image.objects.filter(title=title).first()
        if existing:
            return existing
        with path.open("rb") as f:
            image = Image(title=title)
            image.file.save(path.name, ImageFile(f, name=path.name), save=False)
            image._set_image_file_metadata()
            image.save()
        return image

    # ------------------------------------------------------------------ building

    @transaction.atomic
    def handle(self, *args, source: Path, originaltexte: bool = False, **options):
        pages, mapping = self.load(source)
        overrides = self.load_overrides(source)
        rewrites = {} if originaltexte else self.load_rewrites(source)
        used_rewrites: set[str] = set()

        def rewritten(path: str, title: str) -> str | None:
            """HTML of the rewritten body for a new path, if there is one."""
            if path not in rewrites:
                return None
            used_rewrites.add(path)
            return self.to_html(rewrites[path], title, mapping)

        if "/" not in pages:
            raise CommandError("home.md (alte URL '/') fehlt im Export.")
        legacy_home = pages["/"]

        order = list(mapping)  # old-site tree order
        # Categories = live pages one level below "/" that have children in the mapping.
        categories: list[LegacyPage] = []
        for old_path, page in pages.items():
            if old_path.count("/") == 2 and old_path not in SKIP and old_path != "/":
                kids = [
                    p
                    for p in pages.values()
                    if p.old_path.startswith(old_path) and p.old_path.count("/") == 3
                ]
                if kids:
                    page.children = sorted(kids, key=lambda p: order.index(p.old_path))
                    categories.append(page)
        categories.sort(key=lambda p: order.index(p.old_path))

        site = Site.objects.get(is_default_site=True)
        old_root = site.root_page
        root = Page.get_first_root_node()

        home_html = self.to_html(legacy_home.body_md, "Home", mapping)
        # First quote in the old home text is the company motto.
        motto_match = re.search(r"<blockquote>\s*<p>(.+?)</p>", home_html, re.S)
        motto = motto_match.group(1).strip() if motto_match else "Gebäudereinigung aus Stuttgart"
        home_html = re.sub(r"<blockquote>.*?</blockquote>", "", home_html, count=1, flags=re.S)
        # Drop the trailing category link list – the service grid replaces it.
        home_html = re.sub(r"(<h3><a [^>]+>[^<]+</a></h3>\s*)+$", "", home_html.strip())

        home = HomePage(
            title="Startseite",
            slug="home-import",
            seo_title=legacy_home.seo_title,
            search_description=legacy_home.description,
            hero=[
                (
                    "hero",
                    {
                        "headline": motto,
                        "subline": (
                            "Ihr Meisterbetrieb für Gebäudereinigung, Gebäudedienste und "
                            "Handwerkerleistungen in Stuttgart und der Region."
                        ),
                        "image": None,
                        "links": [],
                    },
                )
            ],
        )
        root.add_child(instance=home)
        site.root_page = home
        site.save()
        if old_root.pk != home.pk and old_root.depth > 1:
            old_root.delete()
        home.slug = "home"
        home.save()

        # --- Kontakt first, so CTAs can link to it --------------------------
        danke = pages.get("/danke/")
        danke_html = self.to_html(danke.body_md, "Kontaktformular", mapping) if danke else ""
        success = self.teaser(danke_html, 200) or "Vielen Dank! Wir melden uns umgehend bei Ihnen."
        kontakt_legacy = pages.get("/kontakt/")
        contact = StandardPage(
            title="Kontakt",
            slug="kontakt",
            show_in_menus=True,
            seo_title=kontakt_legacy.seo_title if kontakt_legacy else "",
            search_description=kontakt_legacy.description if kontakt_legacy else "",
            intro="Nehmen Sie Kontakt mit uns auf. Bei uns treffen Sie auf offene Ohren.",
            body=[
                (
                    "contact_form",
                    {
                        "heading": "Ihre Anfrage",
                        "intro": "",
                        "variant": "contact",
                        "success_message": success,
                    },
                ),
                ("map", {"heading": "So finden Sie uns", "zoom": 15}),
            ],
        )

        # Save Kontakt now: CTAs below reference it, and an unsaved page would be
        # stored as a null reference. It is moved to the end of the menu later.
        home.add_child(instance=contact)

        def cta(heading: str) -> tuple:
            return (
                "cta",
                {
                    "heading": heading,
                    "text": "Wir beraten Sie gern und erstellen Ihnen ein individuelles Angebot.",
                    "link": {
                        "label": "Kontakt aufnehmen",
                        "page": contact,
                        "url": "",
                        "style": "primary",
                    },
                },
            )

        # --- Categories and services ------------------------------------------
        created_services: list[list[ServicePage]] = []
        category_pages: list[ServiceIndexPage] = []
        for cat in categories:
            cat_html = self.to_html(cat.body_md, cat.title, mapping)
            cat_html = re.sub(r"<h3><a [^>]+>[^<]+</a></h3>\s*", "", cat_html).strip()
            cat_page = ServiceIndexPage(
                title=cat.title,
                slug=cat.slug,
                show_in_menus=True,
                icon=ICONS.get(cat.slug, ""),
                seo_title=cat.seo_title,
                search_description=cat.description,
                intro="",
            )
            if cat_html:
                cat_page.intro = self.teaser(cat_html, 590)
            home.add_child(instance=cat_page)
            category_pages.append(cat_page)

            services: list[ServicePage] = []
            for svc in cat.children:
                html = rewritten(svc.new_path, svc.title) or self.to_html(
                    svc.body_md, svc.title, mapping
                )
                if overrides.get(svc.new_path, {}).get("kurztext"):
                    # Editorial summary: keep the full original text in the body.
                    lead = overrides[svc.new_path]["kurztext"]
                else:
                    lead, html = self.split_lead(html)
                page = ServicePage(
                    title=svc.title,
                    slug=svc.slug,
                    show_in_menus=True,
                    icon=ICONS.get(svc.slug, ""),
                    teaser=lead,
                    seo_title=svc.seo_title or f"{svc.title} in Stuttgart – M. B. Grabnar GmbH",
                    search_description=svc.description or self.teaser(lead, 155),
                    body=[("rich_text", html), cta(f"{svc.title} anfragen")] if html else [],
                )
                cat_page.add_child(instance=page)
                services.append(page)
            created_services.append(services)

            if not cat_page.intro:
                cat_page.intro = (
                    f"Im Bereich {cat.title} bieten wir Ihnen: "
                    f"{join_de([s.title for s in services])}."
                )
            cat_page.body = [
                (
                    "service_grid",
                    {
                        "heading": f"Unsere Leistungen im Bereich {cat.title}",
                        "intro": "",
                        "source": "category",
                        "category": cat_page,
                        "services": [],
                    },
                ),
                cta("Angebot anfragen"),
            ]
            if not cat_page.teaser:
                cat_page.teaser = ", ".join(s.title for s in services[:4]) + (
                    " und mehr" if len(services) > 4 else ""
                )

        # Related services: the next two siblings (wrapping around).
        for services in created_services:
            for i, page in enumerate(services):
                for offset in (1, 2):
                    other = services[(i + offset) % len(services)]
                    if other.pk != page.pk:
                        RelatedService.objects.create(page=page, service=other)
                page.save_revision().publish()

        # --- Unternehmen (new; the old site had none) ---------------------------
        about = StandardPage(
            title="Unternehmen",
            slug="unternehmen",
            show_in_menus=True,
            seo_title="Über uns – M. B. Grabnar GmbH, Meisterbetrieb aus Stuttgart",
            search_description=(
                "Etablierter Stuttgarter Dienstleister und Meisterbetrieb: Gebäudereinigung, "
                "Gebäudedienste und Handwerkerleistungen aus einer Hand."
            ),
            intro=(
                "Etablierter Stuttgarter Dienstleister und Meisterbetrieb des "
                "Gebäudereinigerhandwerks."
            ),
            body=[
                (
                    "rich_text",
                    rewritten("/unternehmen/", "Unternehmen") or f"<h2>{motto}</h2>" + home_html,
                ),
                (
                    "feature_list",
                    {
                        "heading": "Was uns auszeichnet",
                        "features": [
                            {"icon": i, "title": t, "text": x} for i, t, x, _src in FEATURES
                        ],
                    },
                ),
                # Seal from the site settings; invisible until it is uploaded there.
                ("certificate", {}),
                (
                    "service_grid",
                    {
                        "heading": "Unsere Leistungsbereiche",
                        "intro": "",
                        "source": "categories",
                        "category": None,
                        "services": [],
                    },
                ),
                cta("Lernen Sie uns kennen"),
            ],
        )
        home.add_child(instance=about)

        # --- Karriere -----------------------------------------------------------
        jobs = JobIndexPage(
            title="Karriere",
            slug="karriere",
            show_in_menus=True,
            intro="Werden Sie Teil unseres Teams – aktuelle Stellenangebote der M. B. Grabnar GmbH.",
            body=[
                (
                    "job_list",
                    {
                        "heading": "Offene Stellen",
                        "show_filter": True,
                        "empty_text": (
                            "Derzeit sind keine Stellen ausgeschrieben. "
                            "Initiativbewerbungen sind jederzeit willkommen."
                        ),
                    },
                ),
                (
                    "contact_form",
                    {
                        "heading": "Initiativbewerbung",
                        "intro": "Schicken Sie uns Ihre Unterlagen – wir melden uns bei Ihnen.",
                        "variant": "application",
                        "success_message": "Vielen Dank für Ihre Bewerbung! Wir melden uns zeitnah.",
                    },
                ),
            ],
        )
        home.add_child(instance=jobs)
        contact.move(home, pos="last-child")
        contact.refresh_from_db()

        # --- Legal pages ----------------------------------------------------------
        legal_pages = []
        for slug in LEGAL:
            legacy = pages.get(f"/{slug}/")
            if not legacy:
                continue
            html = self.to_html(legacy.body_md, legacy.title, mapping)
            html = re.sub(r"^\s*<h2>[^<]*</h2>", "", html)  # duplicate long heading (AGB)
            page = StandardPage(
                title={"agb": "AGB"}.get(slug, legacy.title),
                slug=slug,
                body=[("rich_text", html)],
            )
            home.add_child(instance=page)
            legal_pages.append(page)

        # --- Home body -------------------------------------------------------------
        home_intro = rewritten("/", "Startseite")
        if not home_intro:
            first_paragraph = re.search(r"<p>.*?</p>", home_html, re.S)
            home_intro = (first_paragraph.group(0) if first_paragraph else home_html) + (
                '<p><a href="/unternehmen/">Mehr über uns</a></p>'
            )
        home.hero = [
            (
                "hero",
                {
                    **home.hero[0].value,
                    "links": [
                        {
                            "label": "Angebot anfragen",
                            "page": contact,
                            "url": "",
                            "style": "primary",
                        },
                        {
                            "label": "Unsere Leistungen",
                            "page": category_pages[0],
                            "url": "",
                            "style": "secondary",
                        },
                    ],
                },
            )
        ]
        home.body = [
            (
                "service_grid",
                {
                    "heading": "Unsere Leistungen",
                    "intro": "Gebäudemanagement aus einer Hand – vom Meisterbetrieb aus Stuttgart.",
                    "source": "categories",
                    "category": None,
                    "services": [],
                },
            ),
            ("rich_text", home_intro),
            (
                "feature_list",
                {
                    "heading": "Warum M. B. Grabnar",
                    "features": [
                        {"icon": i, "title": t, "text": x} for i, t, x, _src in FEATURES[:3]
                    ],
                },
            ),
            cta("Maßgeschneidertes Gebäudemanagement für Ihr Objekt"),
        ]
        for page in [home, *category_pages, about, jobs, contact, *legal_pages]:
            page.save_revision().publish()

        # --- Settings ---------------------------------------------------------------
        cs = ContactSettings.for_site(site)
        cs.company_name = "M. B. Grabnar Gebäudereinigungs- und Handwerker-Service GmbH"
        cs.street, cs.postal_code, cs.city = "Julius-Hölder-Straße 4", "70597", "Stuttgart"
        cs.phone = "+49 (0) 711 2 36 33 30"
        cs.fax = "+49 (0) 711 2 36 33 31"
        cs.email = "info@grabnar.de"
        cs.opening_hours = "Mo–Fr 08:00–17:00 Uhr"
        cs.service_area = "Stuttgart und Region"
        cs.save()

        ss = SiteSettings.for_site(site)
        ss.tagline = motto
        ss.footer_text = (
            "Meisterbetrieb für Gebäudereinigung, Gebäudedienste und Handwerkerleistungen "
            "in Stuttgart."
        )
        ss.logo = self.import_logo(source)
        ss.save()
        ss.footer_links.all().delete()
        for page in legal_pages:
            FooterLink.objects.create(settings=ss, label=page.title, page=page)

        # --- Redirects -----------------------------------------------------------------
        by_url = {p.url: p for p in Page.objects.live().specific() if p.url}
        Redirect.objects.filter(site=site).delete()
        created = 0
        for old, new in mapping.items():
            if old == new:
                continue
            target = by_url.get(new)
            if target is None:
                self.stderr.write(f"Kein Ziel für Redirect {old} -> {new}")
                continue
            Redirect.objects.create(
                old_path=Redirect.normalise_path(old),
                site=site,
                redirect_page=target,
                is_permanent=True,
            )
            created += 1

        # --- Editorial overrides (docs/content-overrides.csv) ---------------------------
        applied = 0
        for path, row in overrides.items():
            target = by_url.get(path)
            if target is None:
                self.stderr.write(f"content-overrides.csv: keine Seite für {path}")
                continue
            target = target.specific
            changed = False
            for column, attr in (
                ("seo_titel", "seo_title"),
                ("meta_beschreibung", "search_description"),
                ("einleitung", "intro"),
                ("kurztext", "teaser"),
            ):
                if column in row and hasattr(target, attr):
                    setattr(target, attr, row[column])
                    changed = True
            if changed:
                target.save_revision().publish()
                applied += 1

        for path in sorted(set(rewrites) - used_rewrites):
            self.stderr.write(f"content-neu: keine Seite für {path}")

        n_services = sum(len(s) for s in created_services)
        self.stdout.write(
            self.style.SUCCESS(
                f"Importiert: {len(category_pages)} Kategorien, {n_services} Leistungen, "
                f"{len(legal_pages)} Rechtstexte, {created} Redirects, "
                f"{applied} Seiten mit redaktionellen Texten, "
                f"{len(used_rewrites)} Neutexte"
                f"{' (ignoriert: --originaltexte)' if originaltexte else ''}."
            )
        )
