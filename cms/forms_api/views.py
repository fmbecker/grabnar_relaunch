"""Public form endpoints used by the Astro frontend's React islands.

POST /api/forms/contact/      JSON or form-encoded
POST /api/forms/application/  multipart (optional cv upload)

Spam protection without third parties:
  * honeypot field `website` must be empty
  * `started_at` (epoch ms set when the form rendered) must be >= 3 s old
"""

from __future__ import annotations

import hashlib
import logging
import time

from django.conf import settings
from django.core.mail import send_mail
from django.utils.translation import gettext as _
from rest_framework import serializers, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from forms_api.models import ApplicationSubmission, ContactSubmission

log = logging.getLogger(__name__)
MIN_FILL_SECONDS = 3


class AntiSpamMixin(serializers.Serializer):
    website = serializers.CharField(required=False, allow_blank=True, write_only=True)  # honeypot
    started_at = serializers.IntegerField(required=False, write_only=True)
    consent = serializers.BooleanField()

    def validate_website(self, value):
        if value:
            raise serializers.ValidationError("spam")
        return value

    def validate_started_at(self, value):
        if value and (time.time() * 1000 - value) < MIN_FILL_SECONDS * 1000:
            raise serializers.ValidationError("too fast")
        return value

    def validate_consent(self, value):
        if not value:
            raise serializers.ValidationError(_("Bitte stimmen Sie der Datenverarbeitung zu."))
        return value


class ContactSerializer(AntiSpamMixin, serializers.ModelSerializer):
    class Meta:
        model = ContactSubmission
        fields = [
            "name",
            "email",
            "phone",
            "company",
            "service",
            "message",
            "source_path",
            "website",
            "started_at",
            "consent",
        ]
        extra_kwargs = {"message": {"required": True, "allow_blank": False}}


class ApplicationSerializer(AntiSpamMixin, serializers.ModelSerializer):
    class Meta:
        model = ApplicationSubmission
        fields = [
            "name",
            "email",
            "phone",
            "job_title",
            "job_page_id",
            "message",
            "cv",
            "source_path",
            "website",
            "started_at",
            "consent",
        ]

    def validate_cv(self, file):
        if file is None:
            return file
        if file.size > settings.FORMS_MAX_UPLOAD_BYTES:
            raise serializers.ValidationError(_("Die Datei ist zu groß (max. 10 MB)."))
        if file.content_type not in settings.FORMS_ALLOWED_UPLOAD_TYPES:
            raise serializers.ValidationError(_("Bitte nur PDF- oder Word-Dateien hochladen."))
        return file


def _strip_meta(data: dict) -> dict:
    return {k: v for k, v in data.items() if k not in {"website", "started_at", "consent"}}


def _ip_hash(request) -> str:
    ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", ""))
    ip = ip.split(",")[0].strip()
    return hashlib.sha256(f"{ip}{settings.SECRET_KEY}".encode()).hexdigest() if ip else ""


def _notify(subject: str, body: str) -> bool:
    to = settings.FORMS_NOTIFY_EMAIL
    if not to:
        log.warning("FORMS_NOTIFY_EMAIL not set; submission stored but no mail sent")
        return False
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to], fail_silently=False)
        return True
    except Exception:  # noqa: BLE001 - never lose the submission because mail failed
        log.exception("Failed to send form notification")
        return False


class BaseFormView(APIView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    serializer_class: type[serializers.ModelSerializer]
    subject: str

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            # Honeypot/timing failures look like success to the bot.
            errors = serializer.errors
            if "website" in errors or "started_at" in errors:
                return Response({"ok": True}, status=status.HTTP_201_CREATED)
            return Response({"ok": False, "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        instance = serializer.Meta.model(**_strip_meta(serializer.validated_data))
        instance.ip_hash = _ip_hash(request)
        instance.save()
        instance.notified = _notify(self.subject, self.render_mail(instance))
        instance.save(update_fields=["notified"])
        return Response({"ok": True, "id": instance.pk}, status=status.HTTP_201_CREATED)

    def render_mail(self, instance) -> str:
        lines = [
            f"{f.verbose_name}: {getattr(instance, f.name)}" for f in self.mail_fields(instance)
        ]
        return (
            "\n".join(lines)
            + f"\n\nAdmin: {settings.WAGTAILADMIN_BASE_URL}/django-admin/forms_api/"
        )

    def mail_fields(self, instance):
        skip = {"id", "ip_hash", "notified", "cv"}
        return [f for f in instance._meta.fields if f.name not in skip]


class ContactView(BaseFormView):
    serializer_class = ContactSerializer
    subject = "Neue Kontaktanfrage über www.grabnar.de"


class ApplicationView(BaseFormView):
    serializer_class = ApplicationSerializer
    subject = "Neue Bewerbung über www.grabnar.de"

    def render_mail(self, instance) -> str:
        body = super().render_mail(instance)
        if instance.cv:
            body += f"\nLebenslauf: {settings.WAGTAILADMIN_BASE_URL}{instance.cv.url}"
        return body
