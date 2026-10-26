"""Delete applications (incl. uploaded CVs) older than FORMS_APPLICATION_RETENTION_DAYS.

Run nightly via cron/systemd timer – see deploy/.
"""

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from forms_api.models import ApplicationSubmission


class Command(BaseCommand):
    help = "Purge old application submissions (GDPR retention)."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=settings.FORMS_APPLICATION_RETENTION_DAYS)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, days: int, dry_run: bool, **options):
        cutoff = timezone.now() - timedelta(days=days)
        qs = ApplicationSubmission.objects.filter(created_at__lt=cutoff)
        count = qs.count()
        if dry_run:
            self.stdout.write(f"Would delete {count} application(s) older than {days} days.")
            return
        for sub in qs:
            if sub.cv:
                sub.cv.delete(save=False)
            sub.delete()
        self.stdout.write(
            self.style.SUCCESS(f"Deleted {count} application(s) older than {days} days.")
        )
