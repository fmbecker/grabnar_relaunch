from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.api import APIField
from wagtail.fields import StreamField
from wagtail.models import Page
from wagtail_headless_preview.models import HeadlessMixin

from blocks.api import ImageRenditionsField
from blocks.blocks import BodyStreamBlock, HeroBlock


class BasePage(HeadlessMixin, Page):
    """Abstract base: SEO fields + API exposure shared by all page types.

    HeadlessMixin makes 'view live' and previews go to the Astro frontend.
    """

    og_image = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name=_("Social-Media-Bild"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_("Wird beim Teilen in sozialen Netzwerken angezeigt (1200×630 empfohlen)."),
    )
    hide_from_sitemap = models.BooleanField(_("Nicht in Sitemap aufnehmen"), default=False)

    promote_panels = Page.promote_panels + [
        MultiFieldPanel(
            [FieldPanel("og_image"), FieldPanel("hide_from_sitemap")], _("Teilen & Sitemap")
        ),
    ]

    api_fields = [
        APIField("seo_title"),
        APIField("search_description"),
        APIField("og_image", serializer=ImageRenditionsField()),
        APIField("hide_from_sitemap"),
        APIField("last_published_at"),
    ]

    class Meta:
        abstract = True

    def get_sitemap_urls(self, request=None):
        return [] if self.hide_from_sitemap else super().get_sitemap_urls(request)


class HomePage(BasePage):
    hero = StreamField(
        [("hero", HeroBlock())],
        verbose_name=_("Hero"),
        min_num=1,
        max_num=1,
        use_json_field=True,
    )
    body = StreamField(BodyStreamBlock(), verbose_name=_("Inhalt"), blank=True, use_json_field=True)

    content_panels = Page.content_panels + [FieldPanel("hero"), FieldPanel("body")]
    api_fields = BasePage.api_fields + [APIField("hero"), APIField("body")]

    parent_page_types = ["wagtailcore.Page"]
    subpage_types = [
        "home.StandardPage",
        "services.ServiceIndexPage",
        "jobs.JobIndexPage",
    ]
    max_count = 1

    class Meta:
        verbose_name = _("Startseite")


class StandardPage(BasePage):
    intro = models.TextField(_("Einleitung"), blank=True, max_length=600)
    body = StreamField(BodyStreamBlock(), verbose_name=_("Inhalt"), blank=True, use_json_field=True)

    content_panels = Page.content_panels + [FieldPanel("intro"), FieldPanel("body")]
    api_fields = BasePage.api_fields + [APIField("intro"), APIField("body")]

    parent_page_types = ["home.HomePage", "home.StandardPage"]
    subpage_types = ["home.StandardPage"]

    class Meta:
        verbose_name = _("Standardseite")
