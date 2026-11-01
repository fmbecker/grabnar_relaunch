"""StreamField blocks shared by all page types.

Block contract: every block here has exactly one TypeScript type in
web/src/lib/types.ts and one component in web/src/components/blocks/.
Keep the three in sync when changing anything.
"""

from __future__ import annotations

from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock

from blocks.images import image_api_representation

RICH_TEXT_FEATURES = ["bold", "italic", "h2", "h3", "ol", "ul", "link", "document-link"]


class ApiImageChooserBlock(ImageChooserBlock):
    """Image chooser that serialises to a renditions dict instead of an id."""

    def get_api_representation(self, value, context=None):
        return image_api_representation(value)


class LinkBlock(blocks.StructBlock):
    """Internal page or external URL plus label. Exactly one target required."""

    label = blocks.CharBlock(label=_("Beschriftung"), max_length=60, required=False)
    page = blocks.PageChooserBlock(label=_("Interne Seite"), required=False)
    url = blocks.URLBlock(label=_("Externe URL"), required=False)
    style = blocks.ChoiceBlock(
        label=_("Darstellung"),
        choices=[("primary", _("Primär")), ("secondary", _("Sekundär")), ("link", _("Textlink"))],
        default="primary",
    )

    class Meta:
        icon = "link"
        label = _("Link")

    def clean(self, value):
        result = super().clean(value)
        has_page, has_url = bool(result.get("page")), bool(result.get("url"))
        has_label = bool((result.get("label") or "").strip())
        if not self.required and not (has_page or has_url or has_label):
            return result  # optional link left completely empty
        errors = []
        if has_page == has_url:
            errors.append(_("Bitte entweder eine interne Seite oder eine URL angeben."))
        if not has_label:
            errors.append(_("Bitte eine Beschriftung angeben."))
        if errors:
            raise blocks.StructBlockValidationError(non_block_errors=errors)
        return result

    def get_api_representation(self, value, context=None):
        page = value.get("page")
        if not page and not value.get("url"):
            return None  # optional link left empty
        return {
            "label": value.get("label"),
            "href": page.url if page else value.get("url"),
            "external": page is None,
            "style": value.get("style"),
        }


class HeroBlock(blocks.StructBlock):
    motto = blocks.CharBlock(
        label=_("Motto"),
        required=False,
        max_length=160,
        help_text=_("Kurzes Zitat über der Überschrift, ohne Anführungszeichen."),
    )
    headline = blocks.CharBlock(label=_("Überschrift"), max_length=120)
    subline = blocks.TextBlock(label=_("Unterzeile"), required=False, max_length=300)
    image = ApiImageChooserBlock(label=_("Bild"), required=False)
    links = blocks.ListBlock(LinkBlock(), label=_("Buttons"), min_num=0, max_num=2)

    class Meta:
        icon = "image"
        label = _("Hero")


class RichTextBlock(blocks.RichTextBlock):
    class Meta:
        icon = "pilcrow"
        label = _("Fließtext")

    def __init__(self, **kwargs):
        kwargs.setdefault("features", RICH_TEXT_FEATURES)
        super().__init__(**kwargs)


class TextImageBlock(blocks.StructBlock):
    heading = blocks.CharBlock(label=_("Überschrift"), required=False, max_length=120)
    text = blocks.RichTextBlock(label=_("Text"), features=RICH_TEXT_FEATURES)
    image = ApiImageChooserBlock(label=_("Bild"))
    image_position = blocks.ChoiceBlock(
        label=_("Bildposition"),
        choices=[("left", _("Links")), ("right", _("Rechts"))],
        default="right",
    )
    link = LinkBlock(label=_("Link"), required=False)

    class Meta:
        icon = "doc-full"
        label = _("Text + Bild")


class ServiceGridBlock(blocks.StructBlock):
    """Tiles for service categories or services.

    source = "categories": all ServiceIndexPages (e.g. on the home page)
    source = "category":   the ServicePages below one chosen category
    source = "manual":     hand-picked ServicePages
    """

    heading = blocks.CharBlock(label=_("Überschrift"), required=False, max_length=120)
    intro = blocks.TextBlock(label=_("Einleitung"), required=False, max_length=400)
    source = blocks.ChoiceBlock(
        label=_("Inhalt"),
        choices=[
            ("categories", _("Alle Leistungskategorien")),
            ("category", _("Leistungen einer Kategorie")),
            ("manual", _("Ausgewählte Leistungen")),
        ],
        default="categories",
    )
    category = blocks.PageChooserBlock(
        label=_("Kategorie"),
        page_type="services.ServiceIndexPage",
        required=False,
        help_text=_("Nur für „Leistungen einer Kategorie“."),
    )
    services = blocks.ListBlock(
        blocks.PageChooserBlock(page_type="services.ServicePage"),
        label=_("Leistungen"),
        min_num=0,
        help_text=_("Nur für „Ausgewählte Leistungen“."),
    )

    class Meta:
        icon = "grip"
        label = _("Leistungs-Kacheln")

    def clean(self, value):
        result = super().clean(value)
        if result.get("source") == "category" and not result.get("category"):
            raise blocks.StructBlockValidationError(
                block_errors={"category": ValidationError(_("Bitte eine Kategorie wählen."))}
            )
        return result

    def get_api_representation(self, value, context=None):
        from services.models import ServiceIndexPage, ServicePage

        source = value.get("source") or "categories"
        if source == "categories":
            pages = ServiceIndexPage.objects.live().public().order_by("path").specific()
        elif source == "category" and value.get("category"):
            pages = ServicePage.objects.live().public().child_of(value["category"]).order_by("path")
        else:
            pages = [p.specific for p in value.get("services", []) if p and p.live]
        return {
            "heading": value.get("heading"),
            "intro": value.get("intro"),
            "kind": "categories" if source == "categories" else "services",
            "services": [p.specific.api_summary() for p in pages],
        }


class FeatureBlock(blocks.StructBlock):
    icon = blocks.CharBlock(
        label=_("Icon-Name"),
        max_length=40,
        help_text=_("Name eines Icons aus dem Frontend-Iconset, z. B. 'sparkles'."),
    )
    title = blocks.CharBlock(label=_("Titel"), max_length=80)
    text = blocks.TextBlock(label=_("Text"), max_length=300)


class FeatureListBlock(blocks.StructBlock):
    heading = blocks.CharBlock(label=_("Überschrift"), required=False, max_length=120)
    features = blocks.ListBlock(FeatureBlock(), label=_("Merkmale"), min_num=3, max_num=6)

    class Meta:
        icon = "list-ul"
        label = _("Merkmal-Liste")


class StatBlock(blocks.StructBlock):
    value = blocks.CharBlock(
        label=_("Wert"), max_length=20, help_text=_("z. B. '1985' oder '150+'")
    )
    label = blocks.CharBlock(label=_("Beschriftung"), max_length=60)


class StatsBlock(blocks.StructBlock):
    stats = blocks.ListBlock(StatBlock(), label=_("Kennzahlen"), min_num=2, max_num=4)

    class Meta:
        icon = "order"
        label = _("Kennzahlen")


class TestimonialBlock(blocks.StructBlock):
    quote = blocks.TextBlock(label=_("Zitat"), max_length=600)
    name = blocks.CharBlock(label=_("Name"), max_length=80)
    company = blocks.CharBlock(label=_("Firma / Funktion"), required=False, max_length=120)

    class Meta:
        icon = "openquote"
        label = _("Kundenstimme")


class FaqItemBlock(blocks.StructBlock):
    question = blocks.CharBlock(label=_("Frage"), max_length=200)
    answer = blocks.RichTextBlock(label=_("Antwort"), features=RICH_TEXT_FEATURES)


class FaqBlock(blocks.StructBlock):
    heading = blocks.CharBlock(label=_("Überschrift"), required=False, max_length=120)
    items = blocks.ListBlock(FaqItemBlock(), label=_("Fragen"), min_num=1)

    class Meta:
        icon = "help"
        label = _("FAQ")


class CtaBlock(blocks.StructBlock):
    heading = blocks.CharBlock(label=_("Überschrift"), max_length=120)
    text = blocks.TextBlock(label=_("Text"), required=False, max_length=300)
    link = LinkBlock(label=_("Button"))
    style = blocks.ChoiceBlock(
        label=_("Darstellung"),
        choices=[
            ("contact", _("Abschlussband mit Telefonnummer")),
            ("career", _("Karriere-Hinweis")),
        ],
        default="contact",
    )

    class Meta:
        icon = "pick"
        label = _("Call-to-Action")

    def get_api_representation(self, value, context=None):
        from wagtail.models import Site

        from site_settings.models import ContactSettings

        data = super().get_api_representation(value, context)
        site = Site.objects.filter(is_default_site=True).first()
        data["phone"] = ContactSettings.for_site(site).phone if site else ""
        return data


class ContactFormBlock(blocks.StructBlock):
    heading = blocks.CharBlock(label=_("Überschrift"), required=False, max_length=120)
    intro = blocks.TextBlock(label=_("Einleitung"), required=False, max_length=400)
    variant = blocks.ChoiceBlock(
        label=_("Formulartyp"),
        choices=[("contact", _("Kontakt / Anfrage")), ("application", _("Bewerbung"))],
        default="contact",
    )
    success_message = blocks.CharBlock(
        label=_("Erfolgsmeldung"),
        max_length=200,
        default=_("Vielen Dank! Wir melden uns schnellstmöglich bei Ihnen."),
    )

    class Meta:
        icon = "mail"
        label = _("Formular")


class JobListBlock(blocks.StructBlock):
    heading = blocks.CharBlock(label=_("Überschrift"), required=False, max_length=120)
    show_filter = blocks.BooleanBlock(label=_("Filter anzeigen"), required=False, default=True)
    empty_text = blocks.CharBlock(
        label=_("Text, wenn keine Stellen offen sind"),
        max_length=200,
        default=_(
            "Derzeit sind keine Stellen ausgeschrieben. Initiativbewerbungen sind willkommen."
        ),
    )

    class Meta:
        icon = "group"
        label = _("Stellenliste")

    def get_api_representation(self, value, context=None):
        from jobs.models import JobPage

        return {
            "heading": value.get("heading"),
            "show_filter": value.get("show_filter"),
            "empty_text": value.get("empty_text"),
            "jobs": [j.api_summary() for j in JobPage.objects.live().public().current()],
        }


def _default_job_embed_url() -> str:
    return settings.JOB_EMBED_DEFAULT_URL


class JobEmbedBlock(blocks.StructBlock):
    """Job ads from an external applicant portal (Europersonal), embedded as an iframe.

    Privacy: the iframe is not part of the static HTML. Visitors first see a notice and load the
    portal with a click (two-click solution), so no request goes to the provider without consent.
    Only hosts in settings.JOB_EMBED_ALLOWED_HOSTS are accepted.
    """

    heading = blocks.CharBlock(
        label=_("Überschrift"), required=False, max_length=120, default="Offene Stellen"
    )
    intro = blocks.TextBlock(label=_("Einleitung"), required=False, max_length=400)
    provider = blocks.CharBlock(
        label=_("Anbieter (für den Datenschutzhinweis)"), max_length=60, default="Europersonal"
    )
    url = blocks.URLBlock(
        label=_("Adresse des Stellenportals"),
        default=_default_job_embed_url,
        help_text=_("Nur https und freigegebene Anbieter (JOB_EMBED_ALLOWED_HOSTS)."),
    )
    height = blocks.IntegerBlock(
        label=_("Höhe des Rahmens in Pixel"), default=1700, min_value=400, max_value=4000
    )

    class Meta:
        icon = "group"
        label = _("Stellenangebote (externes Portal)")

    def clean(self, value):
        value = super().clean(value)
        parts = urlsplit(value.get("url") or "")
        if parts.scheme != "https" or parts.hostname not in settings.JOB_EMBED_ALLOWED_HOSTS:
            allowed = ", ".join(settings.JOB_EMBED_ALLOWED_HOSTS)
            raise blocks.StructBlockValidationError(
                block_errors={
                    "url": ValidationError(
                        _("Nur https-Adressen dieser Anbieter: %(hosts)s") % {"hosts": allowed}
                    )
                }
            )
        return value

    def get_api_representation(self, value, context=None):
        return {
            "heading": value.get("heading") or "",
            "intro": value.get("intro") or "",
            "provider": value.get("provider") or "",
            "url": value.get("url") or "",
            "host": urlsplit(value.get("url") or "").hostname or "",
            "height": value.get("height") or 1700,
        }


class MapBlock(blocks.StructBlock):
    heading = blocks.CharBlock(label=_("Überschrift"), required=False, max_length=120)
    zoom = blocks.IntegerBlock(label=_("Zoomstufe"), default=14, min_value=5, max_value=18)

    class Meta:
        icon = "site"
        label = _("Karte (Adresse aus Kontakt-Einstellungen)")


class GalleryBlock(blocks.StructBlock):
    heading = blocks.CharBlock(label=_("Überschrift"), required=False, max_length=120)
    images = blocks.ListBlock(ApiImageChooserBlock(), label=_("Bilder"), min_num=1, max_num=24)

    class Meta:
        icon = "image"
        label = _("Galerie")


class CertificateBlock(blocks.StructBlock):
    """Shows the certification seal from the site settings (Einstellungen → Website-Einstellungen
    → Zertifizierung). Renders nothing on the website while no seal is uploaded."""

    heading = blocks.CharBlock(
        label=_("Überschrift"), required=False, default="Zertifiziert nach ISO 9001 und ISO 14001"
    )
    text = blocks.TextBlock(
        label=_("Text"),
        required=False,
        default=(
            "Unser Qualitätsmanagement ist nach ISO 9001, unser Umweltmanagement nach "
            "ISO 14001 zertifiziert."
        ),
    )

    class Meta:
        icon = "success"
        label = _("Zertifikat")

    def get_api_representation(self, value, context=None):
        from wagtail.models import Site

        from site_settings.models import SiteSettings

        site = Site.objects.filter(is_default_site=True).first()
        certificate = SiteSettings.for_site(site).certificate_api(height=160) if site else None
        return {
            "heading": value.get("heading", ""),
            "text": value.get("text", ""),
            "seal": certificate["seal"] if certificate else None,
            "document_url": certificate["document_url"] if certificate else "",
        }


class FactsBlock(blocks.StructBlock):
    """Bar of short facts below the hero (Meisterbetrieb · ISO 9001 · …).
    "{anzahl}" in an item is replaced by the number of published service pages."""

    COUNT_PLACEHOLDER = "{anzahl}"

    items = blocks.ListBlock(
        blocks.CharBlock(max_length=40),
        label=_("Fakten"),
        min_num=2,
        max_num=6,
        help_text=_(
            "Kurze Stichworte. „{anzahl}“ wird durch die Zahl der veröffentlichten "
            "Leistungsseiten ersetzt, z. B. „{anzahl} Leistungen“."
        ),
    )

    class Meta:
        icon = "list-ul"
        label = _("Fakten-Leiste")

    def get_api_representation(self, value, context=None):
        items = list(value["items"])
        if any(self.COUNT_PLACEHOLDER in item for item in items):
            from services.models import ServicePage

            count = str(ServicePage.objects.live().public().count())
            items = [item.replace(self.COUNT_PLACEHOLDER, count) for item in items]
        return {"items": items}


class BodyStreamBlock(blocks.StreamBlock):
    """The body of every page type. HeroBlock is a separate field on HomePage."""

    facts = FactsBlock()
    rich_text = RichTextBlock()
    text_image = TextImageBlock()
    service_grid = ServiceGridBlock()
    feature_list = FeatureListBlock()
    stats = StatsBlock()
    testimonial = TestimonialBlock()
    faq = FaqBlock()
    cta = CtaBlock()
    contact_form = ContactFormBlock()
    job_list = JobListBlock()
    job_embed = JobEmbedBlock()
    map = MapBlock()
    gallery = GalleryBlock()
    certificate = CertificateBlock()

    class Meta:
        block_counts = {
            "contact_form": {"max_num": 1},
            "job_list": {"max_num": 1},
            "job_embed": {"max_num": 1},
        }
