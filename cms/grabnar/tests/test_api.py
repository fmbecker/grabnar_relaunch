# ruff: noqa: E501
"""Smoke tests against the seeded site: the API shape the frontend depends on."""

import pytest
from django.core.cache import cache
from django.core.management import call_command

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module", autouse=True)
def seeded(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("seed_dev", verbosity=0)
        cache.clear()  # site-root-path cache was primed before seeding


def test_home_has_hero_and_blocks(client):
    data = client.get("/api/v2/pages/", {"type": "home.HomePage", "fields": "*"}).json()
    page = data["items"][0]
    assert page["hero"][0]["value"]["headline"]
    assert {b["type"] for b in page["body"]} >= {"service_grid", "cta"}
    grid = next(b for b in page["body"] if b["type"] == "service_grid")
    assert len(grid["value"]["services"]) == 8
    assert "renditions" in grid["value"]["services"][0]["image"]


def test_navigation_settings_redirects(client):
    nav = client.get("/api/v2/navigation/").json()
    assert [i["href"] for i in nav["items"]] == [
        "/leistungen/",
        "/unternehmen/",
        "/kontakt/",
        "/karriere/",
    ]
    settings = client.get("/api/v2/settings/").json()
    assert settings["contact"]["phone"]
    assert client.get("/api/v2/redirects/").json() == {"items": []}


def test_job_list_block_and_job_page(client):
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
