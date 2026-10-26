from __future__ import annotations

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.api import APIField
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page, PageManager, PageQuerySet

from blocks.api import RichTextField as RichTextAPIField
from blocks.blocks import RICH_TEXT_FEATURES, BodyStreamBlock
from home.models import BasePage


class JobIndexPage(BasePage):
    intro = models.TextField(_("Einleitung"), blank=True, max_length=600)
    body = StreamField(
        BodyStreamBlock(),
        verbose_name=_("Inhalt"),
        blank=True,
        use_json_field=True,
        help_text=_("Tipp: Block „Stellenliste“ einfügen, um offene Stellen anzuzeigen."),
    )

    content_panels = Page.content_panels + [FieldPanel("intro"), FieldPanel("body")]
    api_fields = BasePage.api_fields + [APIField("intro"), APIField("body")]

    parent_page_types = ["home.HomePage"]
    subpage_types = ["jobs.JobPage"]
    max_count = 1

    class Meta:
        verbose_name = _("Karriere-Übersicht")


class JobPageQuerySet(PageQuerySet):
    def current(self):
        today = timezone.localdate()
        return self.filter(
            models.Q(valid_through__isnull=True) | models.Q(valid_through__gte=today)
        ).order_by("-first_published_at")


JobPageManager = PageManager.from_queryset(JobPageQuerySet)


class JobPage(BasePage):
    class EmploymentType(models.TextChoices):
        FULL_TIME = "FULL_TIME", _("Vollzeit")
        PART_TIME = "PART_TIME", _("Teilzeit")
        MINI_JOB = "MINI_JOB", _("Minijob")
        TEMPORARY = "TEMPORARY", _("Befristet")
        APPRENTICE = "APPRENTICE", _("Ausbildung")

    location = models.CharField(_("Arbeitsort"), max_length=120)
    employment_type = models.CharField(
        _("Beschäftigungsart"), max_length=20, choices=EmploymentType.choices
    )
    start_date = models.CharField(
        _("Beginn"), max_length=60, default="ab sofort", help_text=_("Freitext, z. B. 'ab sofort'.")
    )
    teaser = models.TextField(_("Kurzbeschreibung"), max_length=200)
    tasks = RichTextField(_("Aufgaben"), features=RICH_TEXT_FEATURES)
    requirements = RichTextField(_("Anforderungen"), features=RICH_TEXT_FEATURES)
    benefits = RichTextField(_("Wir bieten"), features=RICH_TEXT_FEATURES, blank=True)
    salary_note = models.CharField(_("Vergütung (optional)"), max_length=120, blank=True)
    valid_through = models.DateField(
        _("Gültig bis"), null=True, blank=True, help_text=_("Leer = unbefristet ausgeschrieben.")
    )
    show_apply_form = models.BooleanField(_("Bewerbungsformular anzeigen"), default=True)

    objects = JobPageManager()

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("location"),
                FieldPanel("employment_type"),
                FieldPanel("start_date"),
                FieldPanel("salary_note"),
                FieldPanel("valid_through"),
            ],
            _("Eckdaten"),
        ),
        FieldPanel("teaser"),
        FieldPanel("tasks"),
        FieldPanel("requirements"),
        FieldPanel("benefits"),
        FieldPanel("show_apply_form"),
    ]
    api_fields = BasePage.api_fields + [
        APIField("location"),
        APIField("employment_type"),
        APIField("employment_type_label", serializer=serializers.ReadOnlyField()),
        APIField("start_date"),
        APIField("teaser"),
        APIField("tasks", serializer=RichTextAPIField()),
        APIField("requirements", serializer=RichTextAPIField()),
        APIField("benefits", serializer=RichTextAPIField()),
        APIField("salary_note"),
        APIField("valid_through"),
        APIField("show_apply_form"),
        APIField("first_published_at"),
    ]

    parent_page_types = ["jobs.JobIndexPage"]
    subpage_types: list[str] = []

    class Meta:
        verbose_name = _("Stellenanzeige")

    @property
    def employment_type_label(self) -> str:
        return self.get_employment_type_display()

    def api_summary(self) -> dict:
        return {
            "id": self.pk,
            "title": self.title,
            "href": self.url,
            "location": self.location,
            "employment_type": self.employment_type,
            "employment_type_label": self.employment_type_label,
            "start_date": self.start_date,
            "teaser": self.teaser,
            "valid_through": self.valid_through.isoformat() if self.valid_through else None,
        }
