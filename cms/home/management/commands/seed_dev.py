# ruff: noqa: E501
"""Create a complete example site so the frontend can be developed without real content.

Idempotent: deletes and recreates the tree under the default site's root.
Usage: uv run manage.py seed_dev [--superuser]
"""

from __future__ import annotations

import datetime as dt
import io

from django.contrib.auth import get_user_model
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.images.models import Image
from wagtail.models import Page, Site
from wagtail.rich_text import RichText

from home.models import HomePage, StandardPage
from jobs.models import JobIndexPage, JobPage
from services.models import RelatedService, ServiceIndexPage, ServicePage
from site_settings.models import ContactSettings, FooterLink, SiteSettings, SocialLink

SERVICES = [
    (
        "unterhaltsreinigung",
        "Unterhaltsreinigung",
        "sparkles",
        "Regelmäßige Reinigung von Büros, Praxen, Treppenhäusern und Gewerbeflächen.",
    ),
    (
        "glasreinigung",
        "Glasreinigung",
        "window",
        "Streifenfreie Fenster, Glasfassaden und Schaufenster – auch in großer Höhe.",
    ),
    (
        "fassadenreinigung",
        "Fassadenreinigung",
        "building",
        "Schonende Reinigung von Fassaden, inkl. Umkehr-Osmose-Verfahren.",
    ),
    (
        "teppichreinigung",
        "Teppichreinigung",
        "layers",
        "Tiefenreinigung von Teppichböden und Polstern.",
    ),
    (
        "hausmeisterservice",
        "Hausmeisterservice",
        "wrench",
        "Objektbetreuung, Kleinreparaturen, Kontrollgänge.",
    ),
    ("winterdienst", "Winterdienst", "snowflake", "Räum- und Streudienst mit Haftungsübernahme."),
    (
        "handwerkerservice",
        "Handwerkerservice",
        "hammer",
        "Kleine Reparaturen und Instandhaltung aus einer Hand.",
    ),
    (
        "entruempelung",
        "Entrümpelung",
        "truck",
        "Entrümpelung und Kleintransporte, besenrein übergeben.",
    ),
]


def _rich(html: str) -> RichText:
    return RichText(html)


def _placeholder_image(title: str, color: tuple[int, int, int]) -> Image:
    from PIL import Image as PILImage

    buf = io.BytesIO()
    PILImage.new("RGB", (1600, 1000), color).save(buf, format="PNG")
    buf.seek(0)
    name = f"{title.lower().replace(' ', '-')}.png"
    img = Image(title=title, width=1600, height=1000)
    img.file.save(name, ImageFile(buf, name=name), save=True)
    return img


class Command(BaseCommand):
    help = "Seed an example site for frontend development."

    def add_arguments(self, parser):
        parser.add_argument("--superuser", action="store_true", help="create admin/admin")

    @transaction.atomic
    def handle(self, *args, superuser: bool, **options):
        site = Site.objects.get(is_default_site=True)
        old_root = site.root_page

        root = Page.get_first_root_node()
        home = HomePage(
            title="Grabnar Gebäudereinigung",
            slug="home-seed",  # temporary; renamed after the old root is gone
            seo_title="Gebäudereinigung Stuttgart – Grabnar",
            search_description="Gebäudereinigung, Hausmeisterservice und Handwerk aus einer Hand – zuverlässig in Stuttgart und Region.",
            hero=[
                (
                    "hero",
                    {
                        "headline": "Sauber. Zuverlässig. Aus einer Hand.",
                        "subline": "Gebäudereinigung, Hausmeisterservice und Handwerk für Gewerbe und Hausverwaltungen in Stuttgart und Region.",
                        "image": _placeholder_image("Hero Platzhalter", (30, 64, 120)),
                        "links": [
                            {
                                "label": "Angebot anfragen",
                                "page": None,
                                "url": "https://example.invalid/kontakt",
                                "style": "primary",
                            },
                            {
                                "label": "Unsere Leistungen",
                                "page": None,
                                "url": "https://example.invalid/leistungen",
                                "style": "secondary",
                            },
                        ],
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

        # Services
        service_index = ServiceIndexPage(
            title="Leistungen",
            slug="leistungen",
            intro="Alles rund um Ihr Gebäude – von der täglichen Reinigung bis zum Winterdienst.",
            show_in_menus=True,
        )
        home.add_child(instance=service_index)
        service_pages: list[ServicePage] = []
        for slug, title, icon, teaser in SERVICES:
            page = ServicePage(
                title=title,
                slug=slug,
                icon=icon,
                teaser=teaser,
                hero_image=_placeholder_image(f"{title} Bild", (90, 110, 130)),
                body=[
                    (
                        "rich_text",
                        _rich(
                            f"<h2>{title} für Ihr Objekt</h2><p>Platzhaltertext. Hier beschreibt die Firma Umfang, Ablauf und Qualitätssicherung der Leistung {title}.</p><ul><li>Feste Ansprechpartner</li><li>Geschultes Personal</li><li>Dokumentierte Qualitätskontrollen</li></ul>"
                        ),
                    ),
                    (
                        "faq",
                        {
                            "heading": "Häufige Fragen",
                            "items": [
                                {
                                    "question": "Wie schnell können Sie starten?",
                                    "answer": _rich(
                                        "<p>In der Regel innerhalb von zwei Wochen nach Objektbegehung.</p>"
                                    ),
                                },
                                {
                                    "question": "Gibt es Mindestlaufzeiten?",
                                    "answer": _rich(
                                        "<p>Wir bieten flexible Verträge ab einem Monat Laufzeit.</p>"
                                    ),
                                },
                            ],
                        },
                    ),
                    (
                        "cta",
                        {
                            "heading": "Angebot für " + title + " anfragen",
                            "text": "Kostenlose Objektbegehung – wir melden uns innerhalb eines Werktags.",
                            "link": {
                                "label": "Jetzt anfragen",
                                "page": None,
                                "url": "https://example.invalid/kontakt",
                                "style": "primary",
                            },
                        },
                    ),
                ],
            )
            service_index.add_child(instance=page)
            service_pages.append(page)
        for i, page in enumerate(service_pages):
            for other in service_pages[i + 1 : i + 3]:
                RelatedService.objects.create(page=page, service=other)
            page.save_revision().publish()

        # Standard pages
        about = StandardPage(
            title="Unternehmen",
            slug="unternehmen",
            show_in_menus=True,
            intro="Familiengeführt, regional verwurzelt, seit Jahrzehnten für saubere Gebäude im Einsatz.",
            body=[
                (
                    "text_image",
                    {
                        "heading": "Über uns",
                        "text": _rich(
                            "<p>Platzhaltertext zur Firmengeschichte, Werten und Team.</p>"
                        ),
                        "image": _placeholder_image("Team Platzhalter", (120, 90, 80)),
                        "image_position": "right",
                    },
                ),
                (
                    "stats",
                    {
                        "stats": [
                            {"value": "19xx", "label": "gegründet"},
                            {"value": "100+", "label": "Mitarbeitende"},
                            {"value": "300+", "label": "betreute Objekte"},
                        ]
                    },
                ),
                (
                    "testimonial",
                    {
                        "quote": "Seit Jahren zuverlässig – Reinigung, Hausmeister und Winterdienst laufen bei uns über einen Ansprechpartner.",
                        "name": "M. Mustermann",
                        "company": "Hausverwaltung Beispiel GmbH",
                    },
                ),
                (
                    "gallery",
                    {
                        "heading": "Einblicke",
                        "images": [
                            _placeholder_image("Galerie 1", (60, 60, 60)),
                            _placeholder_image("Galerie 2", (80, 80, 80)),
                            _placeholder_image("Galerie 3", (100, 100, 100)),
                        ],
                    },
                ),
            ],
        )
        home.add_child(instance=about)
        contact = StandardPage(
            title="Kontakt",
            slug="kontakt",
            show_in_menus=True,
            intro="Wir freuen uns auf Ihre Anfrage – telefonisch, per E-Mail oder über das Formular.",
            body=[
                (
                    "contact_form",
                    {
                        "heading": "Anfrage senden",
                        "intro": "Beschreiben Sie kurz Ihr Objekt und die gewünschte Leistung.",
                        "variant": "contact",
                        "success_message": "Vielen Dank! Wir melden uns innerhalb eines Werktags.",
                    },
                ),
                ("map", {"heading": "So finden Sie uns", "zoom": 14}),
            ],
        )
        home.add_child(instance=contact)
        for slug, title in [("impressum", "Impressum"), ("datenschutz", "Datenschutzerklärung")]:
            p = StandardPage(
                title=title,
                slug=slug,
                body=[
                    (
                        "rich_text",
                        _rich(
                            f"<p>Platzhalter für {title} – wird aus der Altseite übernommen und rechtlich geprüft.</p>"
                        ),
                    )
                ],
            )
            home.add_child(instance=p)
            p.save_revision().publish()

        # Jobs
        job_index = JobIndexPage(
            title="Karriere",
            slug="karriere",
            show_in_menus=True,
            intro="Sichere Arbeitsplätze in der Region – wir freuen uns auf Ihre Bewerbung.",
            body=[
                (
                    "feature_list",
                    {
                        "heading": "Was wir bieten",
                        "features": [
                            {
                                "icon": "shield",
                                "title": "Sicherer Arbeitsplatz",
                                "text": "Unbefristete Verträge in einem etablierten Unternehmen.",
                            },
                            {
                                "icon": "clock",
                                "title": "Planbare Zeiten",
                                "text": "Feste Einsatzpläne, Teilzeit und Vollzeit möglich.",
                            },
                            {
                                "icon": "map-pin",
                                "title": "Wohnortnah",
                                "text": "Objekte in Stuttgart, Affalterbach, Pleidelsheim und Umgebung.",
                            },
                        ],
                    },
                ),
                (
                    "job_list",
                    {
                        "heading": "Offene Stellen",
                        "show_filter": True,
                        "empty_text": "Derzeit sind keine Stellen ausgeschrieben. Initiativbewerbungen sind willkommen.",
                    },
                ),
                (
                    "contact_form",
                    {
                        "heading": "Initiativbewerbung",
                        "intro": "Keine passende Stelle dabei? Schicken Sie uns Ihre Unterlagen.",
                        "variant": "application",
                        "success_message": "Vielen Dank für Ihre Bewerbung!",
                    },
                ),
            ],
        )
        home.add_child(instance=job_index)
        jobs = [
            (
                "vorarbeiter-unterhaltsreinigung-affalterbach",
                "Vorarbeiter (m/w/d) Unterhaltsreinigung",
                "Affalterbach",
                "FULL_TIME",
            ),
            (
                "reinigungskraft-pleidelsheim",
                "Reinigungskraft (m/w/d)",
                "Pleidelsheim",
                "PART_TIME",
            ),
            ("objektleitung-stuttgart", "Objektleitung (m/w/d)", "Stuttgart", "FULL_TIME"),
        ]
        for slug, title, location, etype in jobs:
            j = JobPage(
                title=title,
                slug=slug,
                location=location,
                employment_type=etype,
                teaser=f"Zur Verstärkung unseres Teams in {location} suchen wir ab sofort.",
                tasks="<ul><li>Platzhalter Aufgabe 1</li><li>Platzhalter Aufgabe 2</li></ul>",
                requirements="<ul><li>Erfahrung in der Gebäudereinigung</li><li>Zuverlässigkeit</li></ul>",
                benefits="<ul><li>Unbefristeter Vertrag</li><li>Pünktliche Bezahlung</li></ul>",
                valid_through=dt.date.today() + dt.timedelta(days=90),
            )
            job_index.add_child(instance=j)
            j.save_revision().publish()

        # Home body (after services exist so the grid resolves)
        home.body = [
            (
                "service_grid",
                {
                    "heading": "Unsere Leistungen",
                    "intro": "Ein Ansprechpartner für alles rund um Ihr Gebäude.",
                    "services": [],
                },
            ),
            (
                "feature_list",
                {
                    "heading": "Warum Grabnar",
                    "features": [
                        {
                            "icon": "users",
                            "title": "Feste Teams",
                            "text": "Dieselben Mitarbeitenden kennen Ihr Objekt.",
                        },
                        {
                            "icon": "check",
                            "title": "Qualität dokumentiert",
                            "text": "Regelmäßige Kontrollen und Protokolle.",
                        },
                        {
                            "icon": "phone",
                            "title": "Erreichbar",
                            "text": "Direkter Draht zu Ihrer Objektleitung.",
                        },
                    ],
                },
            ),
            (
                "testimonial",
                {"quote": "Platzhalter-Kundenstimme.", "name": "Kundin", "company": "Beispiel AG"},
            ),
            (
                "cta",
                {
                    "heading": "Kostenlose Objektbegehung",
                    "text": "Wir kommen vorbei und erstellen ein Angebot.",
                    "link": {
                        "label": "Termin anfragen",
                        "page": contact,
                        "url": "",
                        "style": "primary",
                    },
                },
            ),
        ]
        for page in (home, service_index, about, contact, job_index):
            page.save_revision().publish()

        # Settings
        cs = ContactSettings.for_site(site)
        cs.company_name = "M.B. Grabnar Gebäudereinigungs- und Handwerker-Service GmbH"
        cs.street, cs.postal_code, cs.city = "Musterstraße 1", "70000", "Stuttgart"
        cs.phone, cs.email = "0711 2 36 33 30", "info@grabnar.de"
        cs.opening_hours = "Mo–Fr 8:00–17:00 Uhr\nNotdienst nach Vereinbarung"
        cs.latitude, cs.longitude = 48.7758, 9.1829
        cs.service_area = "Stuttgart und Region"
        cs.save()
        ss = SiteSettings.for_site(site)
        ss.tagline = "Sauber. Zuverlässig. Aus einer Hand."
        ss.footer_text = "Gebäudereinigung und Handwerker-Service für Gewerbe, Hausverwaltungen und öffentliche Auftraggeber."
        ss.save()
        ss.footer_links.all().delete()
        for p in Page.objects.filter(slug__in=["impressum", "datenschutz"]):
            FooterLink.objects.create(settings=ss, label=p.title, page=p)
        ss.social_links.all().delete()
        SocialLink.objects.create(
            settings=ss,
            platform="google",
            url="https://maps.google.com/?q=Grabnar+Gebäudereinigung",
        )

        if superuser:
            User = get_user_model()
            if not User.objects.filter(username="admin").exists():
                User.objects.create_superuser("admin", "admin@example.com", "admin")
                self.stdout.write("Superuser admin/admin created (dev only!)")

        self.stdout.write(self.style.SUCCESS(f"Seeded {Page.objects.count() - 1} pages."))
