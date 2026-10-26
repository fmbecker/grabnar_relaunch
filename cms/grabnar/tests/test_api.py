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
