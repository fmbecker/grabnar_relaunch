"""StreamField blocks shared by all page types.

Block contract: every block here has exactly one TypeScript type in
web/src/lib/types.ts and one component in web/src/components/blocks/.
Keep the three in sync when changing anything.
"""

from __future__ import annotations

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

    label = blocks.CharBlock(label=_("Beschriftung"), max_length=60)
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
        if bool(result.get("page")) == bool(result.get("url")):
            raise blocks.StructBlockValidationError(
                non_block_errors=[_("Bitte entweder eine interne Seite oder eine URL angeben.")]
            )
        return result

    def get_api_representation(self, value, context=None):
        page = value.get("page")
        return {
            "label": value.get("label"),
            "href": page.url if page else value.get("url"),
            "external": page is None,
            "style": value.get("style"),
        }


class HeroBlock(blocks.StructBlock):
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

    class Meta:
        icon = "pick"
        label = _("Call-to-Action")


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


class BodyStreamBlock(blocks.StreamBlock):
    """The body of every page type. HeroBlock is a separate field on HomePage."""

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
    map = MapBlock()
    gallery = GalleryBlock()

    class Meta:
        block_counts = {"contact_form": {"max_num": 1}, "job_list": {"max_num": 1}}
