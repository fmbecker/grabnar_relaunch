"""Extract readable content per live page (subtree of page 37) to Markdown.

Usage: python extract.py grabnar-export.json docs/content-export
The raw export (pages + image metadata of the legacy Wagtail 2.14 DB) is not in this
public repo because it contains personal e-mail addresses; Felix keeps a copy.
"""
import json, sys, re, urllib.parse, pathlib
from markdownify import markdownify as md

src, out = sys.argv[1], pathlib.Path(sys.argv[2])
d = json.load(open(src))
P = {p["id"]: p for p in d["pages"]}
IMG = {i["id"]: i for i in d["images"]}
root = P[37]["data"]["path"]

def walk(v, acc):
    if isinstance(v, list):
        for b in v:
            if isinstance(b, dict) and "type" in b:
                t, val = b["type"], b.get("value")
                if t in ("html", "text") and isinstance(val, str):
                    acc["html"].append(val)
                elif t == "image" and isinstance(val, dict):
                    acc["img"].append(val.get("image"))
                elif t == "hero" and isinstance(val, dict) and val.get("background_image"):
                    acc["img"].append(val["background_image"])
                elif t == "reusable_content":
                    acc["reusable"] += 1
                if t in ("quote", "card") and isinstance(val, dict):
                    acc["html"].append(" ".join(str(x) for x in val.values() if isinstance(x, str) and len(x) > 3))
                walk(val, acc)
            else:
                walk(b, acc)
    elif isinstance(v, dict):
        for x in v.values():
            walk(x, acc)

rows, index = [], []
for p in sorted(d["pages"], key=lambda p: p["data"]["path"]):
    if not p["data"]["path"].startswith(root):
        continue
    body = p["data"].get("body")
    body = json.loads(body) if isinstance(body, str) else (body or [])
    acc = {"html": [], "img": [], "reusable": 0}
    walk(body, acc)
    raw = "\n".join(acc["html"])
    raw = re.sub(r"<(/?)h4\b", r"<\1p", raw)  # old site used <h4> as body text
    raw = re.sub(r"<br\s*/?>", "<br>\n", raw)
    text = md(raw, heading_style="ATX", strip=["span", "div", "img", "iframe", "script", "style"])
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    text = re.sub(r"^\s*(\\?\s*)?$", "", text, flags=re.M)
    url = urllib.parse.unquote(p["url"] or "")
    path = urllib.parse.urlparse(url).path or "/"
    slug = "home" if path == "/" else path.strip("/").replace("/", "__").lower()
    imgs = [IMG[i]["file"] for i in acc["img"] if i in IMG]
    words = len(re.findall(r"\w+", text))
    fname = f"{slug}.md"
    meta = [f"# {p['title']}", "", f"- Alte URL: `{path}` (Seite {p['id']}, {p['type']}, live={p['live']})"]
    if p["seo_title"]: meta.append(f"- SEO-Titel: {p['seo_title']}")
    if p["search_description"]: meta.append(f"- Meta-Description: {' '.join(p['search_description'].split())}")
    if imgs: meta.append("- Bilder: " + ", ".join(f"`{x}`" for x in imgs))
    if acc["reusable"]: meta.append(f"- Enthält {acc['reusable']} wiederverwendbare(n) Inhaltsblock/-blöcke (CodeRed Reusable Content, nicht im Export)")
    (out / fname).write_text("\n".join(meta) + "\n\n---\n\n" + (text or "_(kein Fließtext)_") + "\n")
    index.append((p["data"]["depth"] - P[37]["data"]["depth"], path, p["title"], p["type"], p["live"], words, fname))
    rows.append((p["id"], path, p["title"], p["type"], p["live"], words))

lines = ["# Content-Export der Altseite", "", "Automatisch extrahiert aus `grabnar-export.json` (Wagtail 2.14 / coderedcms 0.22, Teilbaum der Live-Startseite, Seite 37). Nur Fließtext aus HTML-/Text-Blöcken; Layout-Wrapper sind entfernt.", "", "| Alte URL | Titel | Typ | Live | Wörter | Datei |", "|---|---|---|---|---|---|"]
for depth, path, title, typ, live, words, fname in index:
    lines.append(f"| `{path}` | {'↳ ' * depth}{title} | {typ} | {'ja' if live else 'nein'} | {words} | [{fname}]({fname}) |")
(out / "README.md").write_text("\n".join(lines) + "\n")
json.dump(rows, open(out / ".pages.json", "w"), ensure_ascii=False)
print(len(index), "Seiten exportiert")
