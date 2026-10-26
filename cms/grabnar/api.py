"""Wagtail API v2 router plus small custom endpoints the frontend needs.

Endpoints (all under /api/v2/):
  pages/            Wagtail pages (type filter, fields, html_path lookup)
  images/           Wagtail images
  documents/        Wagtail documents
  settings/         ContactSettings + SiteSettings for the default site
  redirects/        wagtail.contrib.redirects, resolved to frontend paths
  navigation/       main menu derived from the page tree (show_in_menus)
"""

from __future__ import annotations

from rest_framework.response import Response
from rest_framework.views import APIView
from wagtail.api.v2.router import WagtailAPIRouter
from wagtail.api.v2.views import PagesAPIViewSet
from wagtail.contrib.redirects.models import Redirect
from wagtail.documents.api.v2.views import DocumentsAPIViewSet
from wagtail.images.api.v2.views import ImagesAPIViewSet
from wagtail.models import Page, Site

from site_settings.models import ContactSettings, SiteSettings


class GrabnarPagesAPIViewSet(PagesAPIViewSet):
    """Default PagesAPIViewSet; listed explicitly so filters can be extended later."""

    # Allow the frontend to filter/select by these in list requests.
    known_query_parameters = PagesAPIViewSet.known_query_parameters.union(["show_in_menus"])


class SettingsAPIView(APIView):
    def get(self, request):
        site = Site.find_for_request(request) or Site.objects.get(is_default_site=True)
        contact = ContactSettings.for_site(site)
        site_settings = SiteSettings.for_site(site)
        return Response({"contact": contact.to_api(), "site": site_settings.to_api()})


class RedirectsAPIView(APIView):
    """Flat list the frontend turns into an Nginx map / _redirects file at build time."""

    def get(self, request):
        site = Site.find_for_request(request) or Site.objects.get(is_default_site=True)
        items = []
        for r in Redirect.objects.filter(site__in=[site, None]).select_related("redirect_page"):
            target = r.redirect_page.url if r.redirect_page else r.redirect_link
            if not target:
                continue
            items.append(
                {
                    "from": r.old_path,
                    "to": target,
                    "status": 301 if r.is_permanent else 302,
                }
            )
        return Response({"items": items})


class NavigationAPIView(APIView):
    """Two-level main navigation from pages flagged 'show in menus'."""

    def get(self, request):
        site = Site.find_for_request(request) or Site.objects.get(is_default_site=True)
        root = site.root_page.specific
        top = root.get_children().live().public().in_menu().specific()

        def entry(page: Page) -> dict:
            return {"id": page.pk, "title": page.title, "href": page.url}

        items = []
        for page in top:
            node = entry(page)
            children = page.get_children().live().public().in_menu().specific()
            node["children"] = [entry(c) for c in children]
            items.append(node)
        return Response({"home": entry(root), "items": items})


api_router = WagtailAPIRouter("wagtailapi")
api_router.register_endpoint("pages", GrabnarPagesAPIViewSet)
api_router.register_endpoint("images", ImagesAPIViewSet)
api_router.register_endpoint("documents", DocumentsAPIViewSet)
