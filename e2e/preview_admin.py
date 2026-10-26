"""E2E: Wagtail admin -> headless preview (Astro SSR).

Prerequisites: CMS seeded (manage.py seed_dev --superuser, admin/admin) and started with
FRONTEND_URL pointing at a running preview server (pnpm dev, or node web/dist/server/entry.mjs).
Run: python3 e2e/preview_admin.py [screenshot-dir]    (needs: pip install playwright)

1. Existing page: change title without saving -> preview shows draft, live API unchanged.
2. New, never-saved page: open preview panel, then type -> preview updates live.
"""
import re, sys
from playwright.sync_api import sync_playwright, expect

import os
CMS = os.environ.get("CMS_URL", "http://127.0.0.1:8000")
OUT = sys.argv[1] if len(sys.argv) > 1 else "."


def open_preview_panel(page):
    toggle = page.locator("button[data-side-panel-toggle='preview']")
    if toggle.get_attribute("aria-expanded") != "true":
        toggle.click()


def preview_frame(page):
    outer = page.frame_locator("iframe#w-preview-iframe")
    return outer.frame_locator("iframe").first


with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1600, "height": 1000}, locale="de-DE")
    page.goto(f"{CMS}/admin/login/")
    page.fill("#id_username", "admin"); page.fill("#id_password", "admin")
    page.click("button[type=submit]")
    page.wait_for_url(re.compile(r"/admin/$"))

    # 1) existing page
    pid = page.evaluate("""async () => (await (await fetch('/api/v2/pages/?slug=winterdienst')).json()).items[0].id""")
    page.goto(f"{CMS}/admin/pages/{pid}/edit/")
    open_preview_panel(page)
    expect(preview_frame(page).locator("h1")).to_have_text("Winterdienst", timeout=20000)  # initial render
    page.click("#id_title")
    page.keyboard.press("End")
    page.keyboard.type(" – Vorschau-Test", delay=40)  # real keystrokes trigger Wagtail's change detection
    page.keyboard.press("Tab")
    frame = preview_frame(page)
    expect(frame.locator("h1")).to_have_text("Winterdienst – Vorschau-Test", timeout=20000)
    expect(frame.get_by_text("Vorschau – diese Version ist noch nicht veröffentlicht.")).to_be_visible()
    page.screenshot(path=f"{OUT}/preview-admin-existing.png")
    live = page.evaluate(f"""async () => (await (await fetch('/api/v2/pages/{pid}/')).json()).title""")
    assert live == "Winterdienst", live
    print("1) bestehende Seite: Vorschau zeigt Entwurf, Live-Titel unverändert:", live)

    # 2) new page, panel open while typing -> live update
    cat_id = page.evaluate("""async () => (await (await fetch('/api/v2/pages/?slug=gebaeudedienste')).json()).items[0].id""")
    page.goto(f"{CMS}/admin/pages/add/services/servicepage/{cat_id}/")
    open_preview_panel(page)
    expect(preview_frame(page).locator("h1")).to_be_visible(timeout=20000)  # placeholder render
    page.click("#id_title")
    page.keyboard.type("Neue Leistung im Entwurf", delay=40)
    page.keyboard.press("Tab")
    page.click("#id_teaser")
    page.keyboard.type("Diese Seite wurde noch nie gespeichert.", delay=20)
    page.keyboard.press("Tab")
    frame = preview_frame(page)
    expect(frame.locator("h1")).to_have_text("Neue Leistung im Entwurf", timeout=20000)
    expect(frame.get_by_text("Diese Seite wurde noch nie gespeichert.")).to_be_visible()
    page.screenshot(path=f"{OUT}/preview-admin-new.png")
    print("2) neue Seite: Vorschau aktualisiert sich beim Tippen")
    b.close()
