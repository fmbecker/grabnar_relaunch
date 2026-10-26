from __future__ import annotations

import uuid
from pathlib import Path

from django.db import models
from django.utils.translation import gettext_lazy as _


def _application_upload_path(instance: ApplicationSubmission, filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    return f"applications/{instance.created_at:%Y/%m}/{uuid.uuid4().hex}{suffix}"


class SubmissionBase(models.Model):
    created_at = models.DateTimeField(_("Eingegangen"), auto_now_add=True)
    name = models.CharField(_("Name"), max_length=120)
    email = models.EmailField(_("E-Mail"))
    phone = models.CharField(_("Telefon"), max_length=40, blank=True)
    message = models.TextField(_("Nachricht"), blank=True, max_length=4000)
    source_path = models.CharField(_("Absendende Seite"), max_length=200, blank=True)
    ip_hash = models.CharField(max_length=64, blank=True, editable=False)
    notified = models.BooleanField(_("Benachrichtigung versendet"), default=False, editable=False)

    class Meta:
        abstract = True
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} ({self.created_at:%d.%m.%Y %H:%M})"


class ContactSubmission(SubmissionBase):
    company = models.CharField(_("Firma"), max_length=120, blank=True)
    service = models.CharField(_("Gewünschte Leistung"), max_length=120, blank=True)

    class Meta(SubmissionBase.Meta):
        verbose_name = _("Kontaktanfrage")
        verbose_name_plural = _("Kontaktanfragen")


class ApplicationSubmission(SubmissionBase):
    job_title = models.CharField(_("Stelle"), max_length=200, blank=True)
    job_page_id = models.IntegerField(_("Stellen-ID"), null=True, blank=True)
    cv = models.FileField(_("Lebenslauf"), upload_to=_application_upload_path, blank=True)

    class Meta(SubmissionBase.Meta):
        verbose_name = _("Bewerbung")
        verbose_name_plural = _("Bewerbungen")
