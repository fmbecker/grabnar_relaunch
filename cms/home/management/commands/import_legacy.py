# ruff: noqa: E501
"""Import the content of the old site (Wagtail 2.14 / coderedcms) into the new page tree.

Sources (both in the repo, produced from the DB export of the old site):
  docs/content-export/*.md   one Markdown file per old page
  docs/redirects.csv         old URL -> new URL mapping

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
"""

from __future__ import annotations

import csv
import re
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path

import markdown
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from wagtail.contrib.redirects.models import Redirect
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

LEGAL = ["impressum", "datenschutz", "agb"]
SKIP = {"/kontaktformular/", "/kontaktformular/form/", "/danke/", "/stellenangebote/", "/kontakt/"}


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

    # ------------------------------------------------------------------ parsing

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
                title=title.group(1).strip(),
                old_path=old_path,
                new_path=mapping.get(old_path, old_path),
                seo_title=seo.group(1).strip() if seo else "",
                description=desc.group(1).strip() if desc else "",
                body_md=body.strip(),
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
        return markdown.markdown(md, output_format="html")

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

    # ------------------------------------------------------------------ building

    @transaction.atomic
    def handle(self, *args, source: Path, **options):
        pages, mapping = self.load(source)
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
                html = self.to_html(svc.body_md, svc.title, mapping)
                page = ServicePage(
                    title=svc.title,
                    slug=svc.slug,
                    show_in_menus=True,
                    icon=ICONS.get(svc.slug, ""),
                    teaser=self.teaser(html),
                    seo_title=svc.seo_title or f"{svc.title} in Stuttgart – M. B. Grabnar GmbH",
                    search_description=svc.description or self.teaser(html, 155),
                    body=[("rich_text", html), cta(f"{svc.title} anfragen")] if html else [],
                )
                cat_page.add_child(instance=page)
                services.append(page)
            created_services.append(services)

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
        home.add_child(instance=contact)

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
            ("rich_text", home_html),
            cta("Maßgeschneidertes Gebäudemanagement für Ihr Objekt"),
        ]
        for page in [home, *category_pages, jobs, contact, *legal_pages]:
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

        n_services = sum(len(s) for s in created_services)
        self.stdout.write(
            self.style.SUCCESS(
                f"Importiert: {len(category_pages)} Kategorien, {n_services} Leistungen, "
                f"{len(legal_pages)} Rechtstexte, {created} Redirects."
            )
        )
