"""URL configuration.

Wagtail does *not* serve public pages here – the Astro frontend does.
Only the admin, the API and media/documents are exposed.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from wagtail import urls as wagtail_urls
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls

from grabnar.api import NavigationAPIView, RedirectsAPIView, SettingsAPIView, api_router

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("api/v2/settings/", SettingsAPIView.as_view(), name="api_settings"),
    path("api/v2/redirects/", RedirectsAPIView.as_view(), name="api_redirects"),
    path("api/v2/navigation/", NavigationAPIView.as_view(), name="api_navigation"),
    path("api/v2/", api_router.urls),
    path("api/forms/", include("forms_api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Wagtail's page-serving routes must stay registered: page.url / the API's html_url
# are built via reverse("wagtail_serve"). HeadlessMixin turns any real hit into a
# redirect to the Astro frontend, and in production Nginx never proxies "/" here.
urlpatterns += [path("", include(wagtail_urls))]
