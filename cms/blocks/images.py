"""Image serialisation for the API: fixed renditions the frontend relies on."""

from __future__ import annotations

from typing import Any

# name -> Wagtail filter spec. Frontend builds <picture>/srcset from these.
RENDITIONS = {
    "thumb": "fill-400x300|format-webp",
    "card": "fill-800x600|format-webp",
    "wide": "fill-1600x900|format-webp",
    "hero": "fill-2000x1000|format-webp",
    "full": "width-1600|format-webp",
}


def image_api_representation(image) -> dict[str, Any] | None:
    if image is None:
        return None
    renditions = {}
    for name, spec in RENDITIONS.items():
        rendition = image.get_rendition(spec)
        renditions[name] = {
            "url": rendition.url,
            "width": rendition.width,
            "height": rendition.height,
        }
    return {
        "id": image.pk,
        "title": image.title,
        "alt": getattr(image, "alt_text", "") or image.title,
        "width": image.width,
        "height": image.height,
        "renditions": renditions,
    }


def logo_api_representation(image) -> dict[str, Any] | None:
    """Logo: uncropped, fixed height, original format (keeps PNG transparency).

    Two renditions for <img srcset> (1x/2x). Never uses the cropping renditions above.
    """
    if image is None:
        return None
    r1 = image.get_rendition("height-80")
    r2 = image.get_rendition("height-160")
    return {
        "url": r1.url,
        "url2x": r2.url,
        "width": r1.width,
        "height": r1.height,
        "alt": getattr(image, "alt_text", "") or image.title,
    }
