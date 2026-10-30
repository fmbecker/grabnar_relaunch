from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.models import Orderable

from blocks.images import image_api_representation, logo_api_representation


@register_setting(icon="mail")
class ContactSettings(BaseSiteSetting):
    company_name = models.CharField(_("Firmenname"), max_length=160)
    street = models.CharField(_("Straße / Nr."), max_length=120)
    postal_code = models.CharField(_("PLZ"), max_length=10)
    city = models.CharField(_("Ort"), max_length=80)
    phone = models.CharField(_("Telefon"), max_length=40)
    fax = models.CharField(_("Fax"), max_length=40, blank=True)
    email = models.EmailField(_("E-Mail"))
    opening_hours = models.TextField(
        _("Erreichbarkeit"), blank=True, help_text=_("Eine Zeile pro Eintrag.")
    )
    latitude = models.DecimalField(
        _("Breitengrad"), max_digits=9, decimal_places=6, null=True, blank=True
    )
    longitude = models.DecimalField(
        _("Längengrad"), max_digits=9, decimal_places=6, null=True, blank=True
    )
    service_area = models.CharField(
        _("Einsatzgebiet"), max_length=200, blank=True, help_text=_("z. B. 'Stuttgart und Region'")
    )

    panels = [
        MultiFieldPanel(
            [
                FieldPanel("company_name"),
                FieldPanel("street"),
                FieldPanel("postal_code"),
                FieldPanel("city"),
            ],
            _("Anschrift"),
        ),
        MultiFieldPanel(
            [FieldPanel("phone"), FieldPanel("fax"), FieldPanel("email")], _("Kontakt")
        ),
        FieldPanel("opening_hours"),
        FieldPanel("service_area"),
        MultiFieldPanel([FieldPanel("latitude"), FieldPanel("longitude")], _("Kartenposition")),
    ]

    class Meta:
        verbose_name = _("Kontaktdaten")

    def to_api(self) -> dict:
        return {
            "company_name": self.company_name,
            "street": self.street,
            "postal_code": self.postal_code,
            "city": self.city,
            "phone": self.phone,
            "fax": self.fax,
            "email": self.email,
            "opening_hours": [
                line.strip() for line in self.opening_hours.splitlines() if line.strip()
            ],
            "latitude": float(self.latitude) if self.latitude is not None else None,
            "longitude": float(self.longitude) if self.longitude is not None else None,
            "service_area": self.service_area,
        }


@register_setting(icon="cog")
class SiteSettings(BaseSiteSetting, ClusterableModel):
    logo = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name=_("Logo"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    tagline = models.CharField(_("Claim"), max_length=120, blank=True)
    footer_text = models.TextField(_("Footer-Text"), blank=True, max_length=400)
    default_og_image = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name=_("Standard-Social-Media-Bild"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    # Combined ISO 9001/14001 seal: shown in the footer and by the "Zertifikat" block once uploaded.
    certificate_seal = models.ForeignKey(
        "wagtailimages.Image",
        verbose_name=_("Zertifikats-Siegel"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_(
            "SVG oder PNG mit transparentem Hintergrund. Leer = kein Siegel auf der Website."
        ),
    )
    certificate_label = models.CharField(
        _("Text zum Siegel"),
        max_length=120,
        blank=True,
        default="Zertifiziert nach ISO 9001 und ISO 14001",
        help_text=_("Steht neben dem Siegel und dient als Alternativtext."),
    )
    certificate_document = models.ForeignKey(
        "wagtaildocs.Document",
        verbose_name=_("Zertifikat als PDF (optional)"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_("Wird beim Siegel verlinkt."),
    )

    # Umami (self-hosted, cookieless). Tracking stays off until script URL and website ID are set.
    analytics_script_url = models.URLField(
        _("Umami-Script-URL"),
        blank=True,
        help_text=_("z. B. https://statistik.grabnar.de/script.js – leer lassen = kein Tracking."),
    )
    analytics_website_id = models.CharField(
        _("Umami-Website-ID"),
        max_length=64,
        blank=True,
        help_text=_("UUID aus Umami → Einstellungen → Websites."),
    )
    analytics_host_url = models.URLField(
        _("Umami-Host-URL (optional)"),
        blank=True,
        help_text=_("Nur nötig, wenn Daten an eine andere Adresse gehen als das Script."),
    )
    analytics_domains = models.CharField(
        _("Nur auf diesen Domains zählen"),
        max_length=255,
        blank=True,
        default="www.grabnar.de,grabnar.de",
        help_text=_("Kommagetrennt. Verhindert Zählungen von Staging und lokalen Builds."),
    )
    analytics_performance = models.BooleanField(_("Ladezeiten (Web Vitals) erfassen"), default=True)
    analytics_do_not_track = models.BooleanField(
        _("„Do Not Track“ der Besucher respektieren"), default=True
    )

    panels = [
        MultiFieldPanel(
            [FieldPanel("logo"), FieldPanel("tagline"), FieldPanel("default_og_image")], _("Marke")
        ),
        FieldPanel("footer_text"),
        InlinePanel("footer_links", label=_("Footer-Links")),
        InlinePanel("social_links", label=_("Social-Media-Links")),
        MultiFieldPanel(
            [
                FieldPanel("certificate_seal"),
                FieldPanel("certificate_label"),
                FieldPanel("certificate_document"),
            ],
            _("Zertifizierung"),
        ),
        MultiFieldPanel(
            [
                FieldPanel("analytics_script_url"),
                FieldPanel("analytics_website_id"),
                FieldPanel("analytics_host_url"),
                FieldPanel("analytics_domains"),
                FieldPanel("analytics_performance"),
                FieldPanel("analytics_do_not_track"),
            ],
            _("Statistik (Umami)"),
        ),
    ]

    class Meta:
        verbose_name = _("Website-Einstellungen")

    def to_api(self) -> dict:
        return {
            "logo": logo_api_representation(self.logo),
            "tagline": self.tagline,
            "footer_text": self.footer_text,
            "default_og_image": image_api_representation(self.default_og_image),
            "footer_links": [
                {
                    "label": link.label,
                    "href": link.page.url if link.page else link.url,
                    "external": link.page is None,
                }
                for link in self.footer_links.all()
                if link.page or link.url
            ],
            "social_links": [
                {"platform": s.platform, "url": s.url} for s in self.social_links.all()
            ],
            "certificate": self.certificate_api(),
            "analytics": self.analytics_api(),
        }

    def certificate_api(self, height: int = 64) -> dict | None:
        """Seal for the frontend, or None while no seal is uploaded."""
        if not self.certificate_seal:
            return None
        seal = logo_api_representation(self.certificate_seal, height=height)
        seal["alt"] = self.certificate_label or seal["alt"]
        return {
            "label": self.certificate_label,
            "seal": seal,
            "document_url": self.certificate_document.url if self.certificate_document else "",
        }

    def analytics_api(self) -> dict | None:
        """Umami tracker config for the frontend, or None while tracking is not set up."""
        if not (self.analytics_script_url and self.analytics_website_id.strip()):
            return None
        domains = [d.strip() for d in self.analytics_domains.split(",") if d.strip()]
        return {
            "provider": "umami",
            "script_url": self.analytics_script_url,
            "website_id": self.analytics_website_id.strip(),
            "host_url": self.analytics_host_url,
            "domains": ",".join(domains),
            "performance": self.analytics_performance,
            "do_not_track": self.analytics_do_not_track,
        }


class FooterLink(Orderable):
    settings = ParentalKey(SiteSettings, on_delete=models.CASCADE, related_name="footer_links")
    label = models.CharField(_("Beschriftung"), max_length=60)
    page = models.ForeignKey(
        "wagtailcore.Page",
        verbose_name=_("Seite"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    url = models.URLField(_("Externe URL"), blank=True)

    panels = [FieldPanel("label"), FieldPanel("page"), FieldPanel("url")]


class SocialLink(Orderable):
    class Platform(models.TextChoices):
        FACEBOOK = "facebook", "Facebook"
        INSTAGRAM = "instagram", "Instagram"
        LINKEDIN = "linkedin", "LinkedIn"
        XING = "xing", "XING"
        YOUTUBE = "youtube", "YouTube"
        GOOGLE = "google", "Google Unternehmensprofil"

    settings = ParentalKey(SiteSettings, on_delete=models.CASCADE, related_name="social_links")
    platform = models.CharField(_("Plattform"), max_length=20, choices=Platform.choices)
    url = models.URLField(_("URL"))

    panels = [FieldPanel("platform"), FieldPanel("url")]
