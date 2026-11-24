"""Image serialisation for the API: fixed renditions the frontend relies on."""

from __future__ import annotations

from typing import Any

# WebP quality 70 (Wagtail default 80): ~25 % smaller, keeps the mobile hero LCP under 2.5 s.
_WEBP = "format-webp|webpquality-70"

# One set per aspect ratio, each ordered small to large. Every candidate the frontend puts
# into one <img srcset> MUST have the same aspect ratio: with mixed ratios the visible crop
# of the same photo depends on the viewport and on the device's pixel density, so the picture
# is cut differently on a retina screen than on a plain one. Guarded by
# test_rendition_sets_have_one_aspect_ratio_each; see docs/07-web-standards.md, finding 4.
RENDITION_SETS = {
    # 4:3 – images that sit in a box in the flow: cards, text/image, gallery.
    "card": ("fill-400x300", "fill-800x600", "fill-1200x900", "fill-1600x1200"),
    # 2:1 – stages an image covers edge to edge: hero, page head.
    "stage": ("fill-800x400", "fill-1200x600", "fill-1600x800", "fill-2000x1000"),
}
# Uncropped, for opening a gallery image on its own. Never part of a srcset.
SINGLE_RENDITIONS = {"full": "width-1600"}


def _rendition(image, spec: str) -> dict[str, Any]:
    rendition = image.get_rendition(f"{spec}|{_WEBP}")
    return {"url": rendition.url, "width": rendition.width, "height": rendition.height}


def image_api_representation(image) -> dict[str, Any] | None:
    if image is None:
        return None
    # Nine renditions per image. Wagtail stores each one after the first build, so only a
    # newly uploaded image costs anything here.
    renditions: dict[str, Any] = {
        name: [_rendition(image, spec) for spec in specs] for name, specs in RENDITION_SETS.items()
    }
    renditions.update({name: _rendition(image, spec) for name, spec in SINGLE_RENDITIONS.items()})
    return {
        "id": image.pk,
        "title": image.title,
        "alt": getattr(image, "alt_text", "") or image.title,
        "width": image.width,
        "height": image.height,
        "renditions": renditions,
    }


def logo_api_representation(image, height: int = 80) -> dict[str, Any] | None:
    """Logo/seal: uncropped, fixed height, original format (keeps PNG transparency, SVG stays SVG).

    Two renditions for <img srcset> (1x/2x). Never uses the cropping renditions above.
    """
    if image is None:
        return None
    r1 = image.get_rendition(f"height-{height}")
    r2 = image.get_rendition(f"height-{height * 2}")
    return {
        "url": r1.url,
        "url2x": r2.url,
        "width": r1.width,
        "height": r1.height,
        "alt": getattr(image, "alt_text", "") or image.title,
    }
