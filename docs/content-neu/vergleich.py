# ruff: noqa: E501  (HTML template lines)
"""Build the review page (old vs. new text) for docs/content-neu/.

Usage (needs the `markdown` package from the CMS environment):
  cd cms && uv run python ../docs/content-neu/vergleich.py /path/to/vergleich.html

The page is published as a claude.ai artifact; reviewers set a status and a
comment per page, stored in the artifact's database (collection "reviews",
one document per file stem).
"""

from __future__ import annotations

import csv
import html
import json
import re
import sys
from pathlib import Path

import markdown

DOCS = Path(__file__).resolve().parent.parent
NEU = DOCS / "content-neu"
CATEGORIES = {
    "gebaeudereinigung": "Gebäudereinigung",
    "gebaeudedienste": "Gebäudedienste",
    "handwerkerdienste": "Handwerkerdienste",
    "services": "Services",
}


def head_field(head: str, name: str) -> str:
    m = re.search(rf"^- {name}: (.+)$", head, re.M)
    return m.group(1).strip() if m else ""


def body_html(md: str, title: str) -> str:
    lines = md.strip().splitlines()
    while lines and (not lines[0].strip() or lines[0].lstrip("# ").strip() == title):
        lines.pop(0)
    out = markdown.markdown("\n".join(lines), output_format="html")
    # Links cannot be followed from the review page: show them as marked text.
    out = re.sub(
        r'<a href="([^"]*)">(.*?)</a>',
        lambda m: f'<span class="lnk" title="Link: {html.escape(m.group(1))}">{m.group(2)}</span>',
        out,
    )
    return re.sub(r"<h[1-6]>", "<h3>", re.sub(r"</h[1-6]>", "</h3>", out))


def words(fragment: str) -> int:
    return len(re.sub(r"<[^>]+>", " ", fragment).split())


def load_pages() -> list[dict]:
    with (DOCS / "content-overrides.csv").open(encoding="utf-8-sig") as f:
        overrides = {r["pfad"]: r for r in csv.DictReader(f, delimiter=";")}
    with (DOCS / "redirects.csv").open() as f:
        order = [r["neu"] for r in csv.DictReader(f)]
    pages = []
    for md_file in NEU.glob("*.md"):
        if md_file.name == "README.md":
            continue
        head, _, body = md_file.read_text(encoding="utf-8").partition("\n---\n")
        title = re.search(r"^# (.+)$", head, re.M).group(1).strip()
        path = head_field(head, "Pfad").strip("`")
        source = head_field(head, "Quelle").strip("`")
        old_text = (DOCS / source).read_text(encoding="utf-8").partition("\n---\n")[2]
        old_title = re.search(r"^## (.+)$", old_text, re.M)
        hint = head_field(head, "Hinweise")
        alt = body_html(old_text, old_title.group(1) if old_title else title)
        neu = body_html(body, title)
        segment = path.strip("/").split("/")[0]
        pages.append(
            {
                "key": md_file.stem,
                "anchor": md_file.stem.replace("__", "--"),
                "title": title,
                "path": path,
                "group": CATEGORIES.get(segment, "Allgemein"),
                "status_file": head_field(head, "Status"),
                "hint": "" if hint.lower() in ("", "keine") else hint,
                "kurztext": overrides.get(path, {}).get("kurztext", ""),
                "einleitung": overrides.get(path, {}).get("einleitung", ""),
                "alt": alt,
                "neu": neu,
                "alt_words": words(alt),
                "neu_words": words(neu),
            }
        )
    rank = {"/": -2, "/unternehmen/": -1}
    pages.sort(
        key=lambda p: rank.get(p["path"], order.index(p["path"]) if p["path"] in order else 99)
    )
    return pages


def render(pages: list[dict]) -> str:
    template = (NEU / "vergleich.template.html").read_text(encoding="utf-8")
    nav, sections = [], []
    group = None
    for p in pages:
        if p["group"] != group:
            group = p["group"]
            nav.append(f'<li class="nav-group">{html.escape(group)}</li>')
        nav.append(
            f'<li><a href="#{p["anchor"]}" data-key="{p["key"]}">'
            f'<span class="dot" aria-hidden="true"></span>{html.escape(p["title"])}</a></li>'
        )
        hint = (
            f'<div class="hint"><span class="hint-label">Hinweis</span>'
            f"<p>{html.escape(p['hint'])}</p></div>"
            if p["hint"]
            else ""
        )
        lead = ""
        if p["kurztext"] or p["einleitung"]:
            label = "Kurztext im Seitenkopf" if p["kurztext"] else "Einleitung"
            lead = (
                f'<p class="lead"><span class="lead-label">{label}</span>'
                f"{html.escape(p['kurztext'] or p['einleitung'])}</p>"
            )
        delta = p["neu_words"] - p["alt_words"]
        sections.append(
            f"""
<section class="page" id="{p["anchor"]}" data-key="{p["key"]}" data-status="offen">
  <header class="page-head">
    <div class="page-title">
      <span class="eyebrow">{html.escape(p["group"])}</span>
      <h2>{html.escape(p["title"])}</h2>
      <code class="path">{html.escape(p["path"])}</code>
    </div>
    <span class="pill" data-pill>Offen</span>
  </header>
  {hint}
  {lead}
  <div class="compare">
    <article class="col col-alt" aria-label="Alter Text">
      <div class="col-head"><span class="tag tag-alt">Alt</span><span class="count">{p["alt_words"]} Wörter</span></div>
      <div class="prose">{p["alt"]}</div>
    </article>
    <article class="col col-neu" aria-label="Neuer Text">
      <div class="col-head"><span class="tag tag-neu">Neu</span><span class="count">{p["neu_words"]} Wörter ({delta:+d})</span></div>
      <div class="prose">{p["neu"]}</div>
    </article>
  </div>
  <form class="review" data-review>
    <fieldset class="seg">
      <legend>Bewertung</legend>
      <label><input type="radio" name="s-{p["anchor"]}" id="s-{p["anchor"]}-offen" value="offen" checked> Offen</label>
      <label><input type="radio" name="s-{p["anchor"]}" id="s-{p["anchor"]}-ok" value="freigegeben"> Freigegeben</label>
      <label><input type="radio" name="s-{p["anchor"]}" id="s-{p["anchor"]}-aend" value="aenderung"> Änderung gewünscht</label>
    </fieldset>
    <label class="note-label" for="n-{p["anchor"]}">Anmerkung</label>
    <textarea id="n-{p["anchor"]}" rows="3" placeholder="Was soll geändert werden? Antwort auf den Hinweis oben …"></textarea>
    <div class="review-foot">
      <button type="submit">Speichern</button>
      <span class="saved" data-saved aria-live="polite"></span>
    </div>
  </form>
</section>"""
        )
    return (
        template.replace("{{NAV}}", "\n".join(nav))
        .replace("{{SECTIONS}}", "\n".join(sections))
        .replace("{{COUNT}}", str(len(pages)))
        .replace("{{KEYS}}", json.dumps([p["key"] for p in pages]))
    )


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("vergleich.html")
    out.write_text(render(load_pages()), encoding="utf-8")
    print(f"{out} geschrieben")
