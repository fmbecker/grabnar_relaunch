from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from rest_framework import serializers
from wagtail.admin.panels import FieldPanel, InlinePanel
from wagtail.api import APIField
from wagtail.fields import StreamField
from wagtail.models import Orderable, Page

from blocks.api import ImageRenditionsField
from blocks.blocks import BodyStreamBlock
from home.models import BasePage


class ServiceIndexPage(BasePage):
    """A service category (e.g. Gebäudereinigung) directly below the home page."""

    icon = models.CharField(
        _("Icon-Name"),
        max_length=40,
        blank=True,
        help_text=_("Icon aus dem Frontend-Iconset, z. B. 'sparkles', 'building', 'hammer'."),
    )
    teaser = models.TextField(
        _("Kurzbeschreibung"),
        max_length=200,
        blank=True,
        help_text=_("Erscheint auf der Kategorie-Kachel der Startseite."),
    )
    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name=_("Titelbild"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    intro = models.TextField(_("Einleitung"), blank=True, max_length=600)
    body = StreamField(BodyStreamBlock(), verbose_name=_("Inhalt"), blank=True, use_json_field=True)

    content_panels = Page.content_panels + [
        FieldPanel("icon"),
        FieldPanel("teaser"),
        FieldPanel("hero_image"),
        FieldPanel("intro"),
        FieldPanel("body"),
    ]
    api_fields = BasePage.api_fields + [
        APIField("icon"),
        APIField("teaser"),
        APIField("hero_image", serializer=ImageRenditionsField()),
        APIField("intro"),
        APIField("body"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = ["services.ServicePage"]

    class Meta:
        verbose_name = _("Leistungskategorie")
        verbose_name_plural = _("Leistungskategorien")

    def api_summary(self) -> dict:
        from blocks.images import image_api_representation

        children = ServicePage.objects.live().public().child_of(self).order_by("path")
        return {
            "title": self.title,
            "href": self.url,
            "teaser": self.teaser or self.intro[:200],
            "icon": self.icon,
            "image": image_api_representation(self.hero_image),
            "children": [{"title": c.title, "href": c.url} for c in children],
        }


class ServicePage(BasePage):
    icon = models.CharField(
        _("Icon-Name"),
        max_length=40,
        blank=True,
        help_text=_("Icon aus dem Frontend-Iconset, z. B. 'sparkles', 'window', 'snowflake'."),
    )
    teaser = models.TextField(
        _("Kurzbeschreibung"),
        max_length=200,
        help_text=_("Erscheint auf Kacheln und in Übersichten."),
    )
    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name=_("Titelbild"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    body = StreamField(BodyStreamBlock(), verbose_name=_("Inhalt"), blank=True, use_json_field=True)

    content_panels = Page.content_panels + [
        FieldPanel("icon"),
        FieldPanel("teaser"),
        FieldPanel("hero_image"),
        FieldPanel("body"),
        InlinePanel("related_services", label=_("Verwandte Leistungen"), max_num=4),
    ]
    api_fields = BasePage.api_fields + [
        APIField("icon"),
        APIField("teaser"),
        APIField("hero_image", serializer=ImageRenditionsField()),
        APIField("body"),
        APIField("related", serializer=serializers.ReadOnlyField()),
    ]

    parent_page_types = ["services.ServiceIndexPage"]
    subpage_types: list[str] = []

    class Meta:
        verbose_name = _("Leistung")

    @property
    def related(self) -> list[dict]:
        return [
            r.service.api_summary()
            for r in self.related_services.select_related("service")
            if r.service and r.service.live
        ]

    def api_summary(self) -> dict:
        from blocks.images import image_api_representation

        return {
            "title": self.title,
            "href": self.url,
            "teaser": self.teaser,
            "icon": self.icon,
            "image": image_api_representation(self.hero_image),
        }


class RelatedService(Orderable):
    page = ParentalKey(ServicePage, on_delete=models.CASCADE, related_name="related_services")
    service = models.ForeignKey(
        ServicePage, verbose_name=_("Leistung"), on_delete=models.CASCADE, related_name="+"
    )

    panels = [FieldPanel("service")]
