"""Wagtail API v2 router plus small custom endpoints the frontend needs.

Endpoints (all under /api/v2/):
  pages/            Wagtail pages (type filter, fields, html_path lookup)
  images/           Wagtail images
  documents/        Wagtail documents
  settings/         ContactSettings + SiteSettings for the default site
  redirects/        wagtail.contrib.redirects, resolved to frontend paths
  navigation/       main menu derived from the page tree (show_in_menus)
  page_preview/     draft content for wagtail-headless-preview (?content_type=&token=)
"""

from __future__ import annotations

from django.apps import apps
from django.core.signing import BadSignature
from django.http import Http404
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


class PagePreviewAPIViewSet(GrabnarPagesAPIViewSet):
    """Serialises the unsaved draft behind a headless-preview token.

    The Astro SSR route /preview/ calls
    GET /api/v2/page_preview/?content_type=services.servicepage&token=...
    The token is signed by HeadlessPreviewMixin, so it cannot be guessed; drafts
    are only reachable for whoever got the URL from the Wagtail admin.
    """

    known_query_parameters = GrabnarPagesAPIViewSet.known_query_parameters.union(
        ["content_type", "token"]
    )

    def get_object(self):
        if hasattr(self, "_preview_page"):
            return self._preview_page
        content_type = self.request.GET.get("content_type", "")
        token = self.request.GET.get("token", "")
        try:
            app_label, model_name = content_type.split(".")
            model = apps.get_model(app_label, model_name)
        except (ValueError, LookupError) as exc:
            raise Http404("Unknown content_type") from exc
        if not hasattr(model, "get_page_from_preview_token"):
            raise Http404("Not a previewable page type")
        try:
            page = model.get_page_from_preview_token(token)
        except BadSignature as exc:
            raise Http404("Invalid token") from exc
        if page is None:
            raise Http404("Preview expired")
        if not page.pk:
            page.pk = 0  # unsaved new page; serializer needs an id
        self._preview_page = page
        return page

    def get_serializer_class(self):
        # Detail mode for the concrete page type: all api_fields, like /pages/<id>/.
        return self._get_serializer_class(
            self.request.wagtailapi_router, type(self.get_object()), [], show_details=True
        )

    def listing_view(self, request):
        page = self.get_object()
        serializer = self.get_serializer_class()(page, context=self.get_serializer_context())
        response = Response(serializer.data)
        response["Cache-Control"] = "no-store"
        response["X-Robots-Tag"] = "noindex"
        return response

    def detail_view(self, request, pk):
        return self.listing_view(request)


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
api_router.register_endpoint("page_preview", PagePreviewAPIViewSet)
api_router.register_endpoint("images", ImagesAPIViewSet)
api_router.register_endpoint("documents", DocumentsAPIViewSet)
