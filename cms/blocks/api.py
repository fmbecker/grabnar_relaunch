"""DRF fields for Wagtail APIField declarations."""

from rest_framework import serializers

from blocks.images import image_api_representation


class ImageRenditionsField(serializers.Field):
    """Serialises an image ForeignKey as the shared renditions dict (or null)."""

    def __init__(self, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(**kwargs)

    def to_representation(self, value):
        return image_api_representation(value)


class RichTextField(serializers.Field):
    """Expands Wagtail's internal link/embed markup to real HTML (like RichTextBlock does)."""

    def __init__(self, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(**kwargs)

    def to_representation(self, value):
        from wagtail.rich_text import expand_db_html

        return expand_db_html(value or "")
