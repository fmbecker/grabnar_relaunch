"""Send an HTML report (read from stdin) with the site's SMTP settings (EMAIL_URL).

Used by deploy/umami/send-monthly-report.sh, so reports go out through the same mail
configuration as the contact forms:

    node deploy/umami/monthly-report.mjs | docker compose … exec -T cms \\
        python manage.py send_report_mail --to a@x.de,b@y.de --subject "…"
"""

import sys

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.management.base import BaseCommand, CommandError
from django.utils.html import strip_tags


class Command(BaseCommand):
    help = "Send an HTML report from stdin by e-mail."

    def add_arguments(self, parser):
        parser.add_argument("--to", required=True, help="Comma-separated recipients")
        parser.add_argument("--subject", required=True)

    def handle(self, *args, to: str, subject: str, **options):
        recipients = [a.strip() for a in to.split(",") if a.strip()]
        if not recipients:
            raise CommandError("No recipients given (--to).")
        html = sys.stdin.read()
        if "<html" not in html.lower():
            raise CommandError(
                "stdin does not contain an HTML document – report generation failed?"
            )
        text = strip_tags(html.split("<body", 1)[-1])
        text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        message = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=recipients,
        )
        message.attach_alternative(html, "text/html")
        message.send()
        self.stdout.write(f"Report sent to {len(recipients)} recipient(s).")
