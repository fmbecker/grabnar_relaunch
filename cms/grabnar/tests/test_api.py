# ruff: noqa: E501
"""Smoke tests against the seeded site (real legacy content + demo extras)."""

import pytest
from django.core.cache import cache
from django.core.management import call_command

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module", autouse=True)
def seeded(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("seed_dev", verbosity=0)
        cache.clear()  # site-root-path cache was primed before seeding


def test_navigation_has_categories_with_children(client):
    nav = client.get("/api/v2/navigation/").json()
    assert [i["href"] for i in nav["items"]] == [
        "/gebaeudereinigung/",
        "/gebaeudedienste/",
        "/handwerkerdienste/",
        "/services/",
        "/unternehmen/",
        "/karriere/",
        "/kontakt/",
    ]
    assert [len(i["children"]) for i in nav["items"][:4]] == [9, 3, 6, 4]


def test_home_shows_categories(client):
    page = client.get("/api/v2/pages/", {"type": "home.HomePage", "fields": "*"}).json()["items"][0]
    assert page["hero"][0]["value"]["headline"].startswith("Zusammenkommen")
    grid = next(b for b in page["body"] if b["type"] == "service_grid")["value"]
    assert grid["kind"] == "categories" and len(grid["services"]) == 4
    assert grid["services"][0]["children"][0]["href"].startswith("/gebaeudereinigung/")


def test_service_page_content_and_list(client):
    data = client.get(
        "/api/v2/pages/", {"type": "services.ServicePage", "slug": "wachdienste", "fields": "*"}
    ).json()
    page = data["items"][0]
    assert page["meta"]["html_url"].endswith("/services/wachdienste/")
    assert "<li>Citystreifen</li>" in page["body"][0]["value"]
    assert page["teaser"] and len(page["related"]) == 2


def test_category_grid_lists_its_services(client):
    data = client.get(
        "/api/v2/pages/",
        {"type": "services.ServiceIndexPage", "slug": "gebaeudedienste", "fields": "body"},
    ).json()
    grid = data["items"][0]["body"][0]["value"]
    assert grid["kind"] == "services"
    assert [s["title"] for s in grid["services"]] == [
        "Grau- und Grünanlagenpflege",
        "Hausmeisterdienste",
        "Winterdienst",
    ]


def test_settings_and_redirects(client):
    contact = client.get("/api/v2/settings/").json()["contact"]
    assert contact["street"] == "Julius-Hölder-Straße 4" and contact["postal_code"] == "70597"
    items = client.get("/api/v2/redirects/").json()["items"]
    assert len(items) == 28
    assert {
        "from": "/Gebäudereinigung/Baureinigung",
        "to": "/gebaeudereinigung/baureinigung/",
        "status": 301,
    } in items


def test_job_list_block(client):
    data = client.get("/api/v2/pages/", {"type": "jobs.JobIndexPage", "fields": "body"}).json()
    jobs = next(b for b in data["items"][0]["body"] if b["type"] == "job_list")["value"]["jobs"]
    assert len(jobs) == 3 and jobs[0]["employment_type_label"]


def test_contact_form_spam_and_success(client):
    base = {
        "name": "A",
        "email": "a@example.com",
        "message": "Hi",
        "consent": True,
        "started_at": 1,
    }
    assert (
        client.post("/api/forms/contact/", base, content_type="application/json").status_code == 201
    )
    bot = client.post(
        "/api/forms/contact/", {**base, "website": "x"}, content_type="application/json"
    )
    assert bot.status_code == 201  # looks like success to the bot
    bad = client.post(
        "/api/forms/contact/", {**base, "consent": False}, content_type="application/json"
    )
    assert bad.status_code == 400 and "consent" in bad.json()["errors"]
    from forms_api.models import ContactSubmission

    assert ContactSubmission.objects.count() == 1


def test_page_preview_returns_unsaved_draft(client):
    from services.models import ServicePage

    page = ServicePage.objects.get(slug="winterdienst")
    page.title = "Winterdienst (Entwurf)"
    page.teaser = "Geänderter Teaser nur in der Vorschau."
    preview = page.create_page_preview()

    res = client.get(
        "/api/v2/page_preview/", {"content_type": "services.servicepage", "token": preview.token}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["title"] == "Winterdienst (Entwurf)"
    assert data["teaser"] == "Geänderter Teaser nur in der Vorschau."
    assert data["meta"]["type"] == "services.ServicePage"
    assert res["Cache-Control"] == "no-store"
    # live page is untouched
    assert ServicePage.objects.get(slug="winterdienst").title == "Winterdienst"


def test_page_preview_rejects_bad_tokens(client):
    bad = client.get(
        "/api/v2/page_preview/", {"content_type": "services.servicepage", "token": "id=1:forged"}
    )
    assert bad.status_code == 404
    wrong_type = client.get("/api/v2/page_preview/", {"content_type": "auth.user", "token": "x"})
    assert wrong_type.status_code == 404


def test_preview_settings_are_picked_up():
    from wagtail_headless_preview.settings import headless_preview_settings

    assert headless_preview_settings.CLIENT_URLS["default"].endswith("/preview/")


def test_all_pages_pass_admin_validation():
    """Every imported page must be saveable in the Wagtail admin (StreamField clean).

    Regression: CTA links pointed at a not-yet-saved page and were stored as null,
    which made the editor refuse to save or preview those pages.
    """
    from wagtail.fields import StreamField
    from wagtail.models import Page

    failures = []
    for page in Page.objects.filter(depth__gt=1).specific():
        for field in page._meta.get_fields():
            if isinstance(field, StreamField):
                value = getattr(page, field.name)
                try:
                    field.stream_block.clean(value)
                except Exception as exc:  # noqa: BLE001
                    failures.append(f"{page.url_path} {field.name}: {exc}")
    assert not failures, "\n".join(failures)


def test_service_teaser_not_repeated_in_body(client):
    data = client.get(
        "/api/v2/pages/", {"type": "services.ServicePage", "fields": "teaser,body", "limit": 50}
    ).json()
    assert len(data["items"]) == 22
    for page in data["items"]:
        body = page["body"][0]["value"] if page["body"] else ""
        assert page["teaser"], page["title"]
        assert page["teaser"] not in body, f"teaser repeated in body: {page['title']}"


def test_spelling_fix_and_category_intro(client):
    titles = [
        p["title"]
        for p in client.get("/api/v2/pages/", {"type": "services.ServicePage", "limit": 50}).json()[
            "items"
        ]
    ]
    assert "Desinfektion nach IfSG §17/3" in titles and not any("IFSG" in t for t in titles)
    cat = client.get(
        "/api/v2/pages/",
        {"type": "services.ServiceIndexPage", "slug": "gebaeudedienste", "fields": "intro"},
    ).json()["items"][0]
    # Editorial intro from docs/content-overrides.csv replaces the generated one.
    assert cat["intro"].startswith("Damit Ihr Objekt das ganze Jahr")


def test_content_overrides_applied(client):
    """Every row of docs/content-overrides.csv ends up on its page; SEO lengths stay sane."""
    import csv
    from pathlib import Path

    from django.conf import settings
    from wagtail.models import Page

    path = Path(settings.BASE_DIR).parent / "docs" / "content-overrides.csv"
    with path.open(encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    assert len(rows) >= 30
    by_url = {p.url: p.specific for p in Page.objects.live() if p.url}
    for row in rows:
        page = by_url[row["pfad"]]
        assert page.seo_title == row["seo_titel"] and len(page.seo_title) <= 60, row["pfad"]
        assert page.search_description == row["meta_beschreibung"], row["pfad"]
        assert len(page.search_description) <= 160, row["pfad"]
        if row["kurztext"]:
            assert page.teaser == row["kurztext"], row["pfad"]


def test_unternehmen_page(client):
    page = client.get(
        "/api/v2/pages/", {"type": "home.StandardPage", "slug": "unternehmen", "fields": "body"}
    ).json()["items"][0]
    types = [b["type"] for b in page["body"]]
    assert types == ["rich_text", "feature_list", "service_grid", "cta"]
    assert "Meisterbetrieb" in [f["title"] for f in page["body"][1]["value"]["features"]]
