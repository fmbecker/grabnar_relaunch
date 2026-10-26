# ruff: noqa: E501
"""Development data: the real content of the old site plus demo extras.

Runs import_legacy (real pages, settings, redirects) and then adds what the
old site does not have yet, so every block/page type can be developed:
placeholder images, example job ads, an optional admin user.

Usage: uv run manage.py seed_dev [--superuser]
"""

from __future__ import annotations

import datetime as dt
import io

from django.contrib.auth import get_user_model
from django.core.files.images import ImageFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.images.models import Image

from jobs.models import JobIndexPage, JobPage
from services.models import ServiceIndexPage, ServicePage

DEMO_JOBS = [
    (
        "beispiel-vorarbeiter-unterhaltsreinigung",
        "Vorarbeiter (m/w/d) Unterhaltsreinigung",
        "Affalterbach",
        "FULL_TIME",
    ),
    ("beispiel-reinigungskraft", "Reinigungskraft (m/w/d)", "Pleidelsheim", "PART_TIME"),
    ("beispiel-objektleitung", "Objektleitung (m/w/d)", "Stuttgart", "FULL_TIME"),
]


def placeholder_image(title: str, color: tuple[int, int, int]) -> Image:
    from PIL import Image as PILImage

    buf = io.BytesIO()
    PILImage.new("RGB", (1600, 1000), color).save(buf, format="PNG")
    buf.seek(0)
    name = f"{title.lower().replace(' ', '-')}.png"
    img = Image(title=title, width=1600, height=1000)
    img.file.save(name, ImageFile(buf, name=name), save=True)
    return img


class Command(BaseCommand):
    help = "import_legacy + demo images/jobs for frontend development."

    def add_arguments(self, parser):
        parser.add_argument("--superuser", action="store_true", help="create admin/admin")

    @transaction.atomic
    def handle(self, *args, superuser: bool, **options):
        call_command("import_legacy", stdout=self.stdout)

        palette = [(31, 82, 138), (18, 63, 107), (63, 134, 196), (15, 50, 84)]
        for i, cat in enumerate(ServiceIndexPage.objects.order_by("path")):
            cat.hero_image = placeholder_image(f"Platzhalter {cat.slug}", palette[i % 4])
            cat.save_revision().publish()
            for svc in ServicePage.objects.child_of(cat).specific():
                svc.hero_image = cat.hero_image
                svc.save_revision().publish()

        index = JobIndexPage.objects.first()
        for slug, title, location, etype in DEMO_JOBS:
            job = JobPage(
                title=title,
                slug=slug,
                location=location,
                employment_type=etype,
                teaser=f"Beispielanzeige: Zur Verstärkung unseres Teams in {location} suchen wir ab sofort.",
                tasks="<ul><li>Beispielaufgabe 1</li><li>Beispielaufgabe 2</li></ul>",
                requirements="<ul><li>Erfahrung in der Gebäudereinigung</li><li>Zuverlässigkeit</li></ul>",
                benefits="<ul><li>Unbefristeter Vertrag</li></ul>",
                valid_through=dt.date.today() + dt.timedelta(days=90),
            )
            index.add_child(instance=job)
            job.save_revision().publish()

        if superuser:
            User = get_user_model()
            if not User.objects.filter(username="admin").exists():
                User.objects.create_superuser("admin", "admin@example.com", "admin")
                self.stdout.write("Superuser admin/admin created (dev only!)")
        self.stdout.write(self.style.SUCCESS("Demo-Bilder und Beispiel-Stellen ergänzt."))
