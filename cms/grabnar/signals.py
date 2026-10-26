"""Trigger a frontend rebuild when content changes.

Publishing/unpublishing a page, or saving site settings, posts to
FRONTEND_BUILD_HOOK_URL (deploy/rebuild-hook.py on the same host). The hook
itself debounces; we only dedupe within one request via a thread-local flag.
"""

from __future__ import annotations

import logging
import threading

import requests
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from wagtail.contrib.redirects.models import Redirect
from wagtail.signals import page_published, page_unpublished

from site_settings.models import ContactSettings, SiteSettings

log = logging.getLogger(__name__)
_state = threading.local()


def trigger_frontend_build(reason: str) -> None:
    url = settings.FRONTEND_BUILD_HOOK_URL
    if not url:
        log.debug("Frontend build hook disabled (reason=%s)", reason)
        return
    if getattr(_state, "fired", False):
        return
    _state.fired = True
    try:
        requests.post(
            url,
            json={"reason": reason},
            headers={"X-Hook-Secret": settings.FRONTEND_BUILD_HOOK_SECRET},
            timeout=5,
        )
        log.info("Frontend rebuild requested (%s)", reason)
    except requests.RequestException as exc:  # never break publishing
        log.warning("Frontend build hook failed: %s", exc)
    finally:
        _state.fired = False


@receiver(page_published)
def _on_published(sender, instance, **kwargs):
    trigger_frontend_build(f"published:{instance.pk}")


@receiver(page_unpublished)
def _on_unpublished(sender, instance, **kwargs):
    trigger_frontend_build(f"unpublished:{instance.pk}")


@receiver(post_save, sender=ContactSettings)
@receiver(post_save, sender=SiteSettings)
@receiver(post_save, sender=Redirect)
def _on_settings_saved(sender, instance, **kwargs):
    trigger_frontend_build(f"{sender.__name__.lower()}:{instance.pk}")
