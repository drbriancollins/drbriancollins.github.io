"""Build the static site from data/*.json.

Usage:
    python tools/build.py

Standard library only. Writes index.html, one folder per page (so URLs are
/publications/, /grants/ ...), 404.html and sitemap.xml at the repo root.
Edit the JSON files in data/, run this script, then commit and push.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://drbriancollins.github.io"
SITE = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
PUBS = json.loads((ROOT / "data" / "publications.json").read_text(encoding="utf-8"))
SKILLS = json.loads((ROOT / "data" / "skills.json").read_text(encoding="utf-8"))

NAV = [
    ("", "About"),
    ("publications", "Publications"),
    ("grants", "Grants"),
    ("student-supervision", "Supervision"),
    ("technical-skills", "Skills"),
    ("certificates", "Certificates"),
    ("other", "Media & Service"),
]

FAVICON = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
    "%3Crect width='64' height='64' rx='14' fill='%231f6f5c'/%3E"
    "%3Ctext x='32' y='42' font-family='Arial,sans-serif' font-size='28' font-weight='700' "
    "text-anchor='middle' fill='white'%3EBC%3C/text%3E%3C/svg%3E"
)

e = lambda s: html.escape(s, quote=False)  # noqa: E731


def page(slug, title, description, body):
    depth = "../" if slug else ""
    current = ' aria-current="page"'
    nav = "".join(
        f'<a href="{depth}{s + "/" if s else ""}"{current if s == slug else ""}>{e(label)}</a>'
        for s, label in NAV
    )
    full_title = f"{title} | {SITE['name']}" if slug else f"{SITE['name']}, {SITE['postnominals']}"
    links = " · ".join(f'<a href="{l["url"]}" rel="noopener">{e(l["label"])}</a>' for l in SITE["links"])
    canonical = f"{BASE_URL}/{slug + '/' if slug else ''}"
    return f"""<!doctype html>
<html lang="en-AU">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full_title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="canonical" href="{canonical}">
<link rel="icon" href="{FAVICON}">
<link rel="stylesheet" href="{depth}assets/style.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{depth or './'}">{e(SITE['name'])}<span>{e(SITE['postnominals'])}</span></a>
    <nav aria-label="Main">{nav}</nav>
  </div>
</header>
<main id="main" class="wrap">
{body}
</main>
<footer class="site-footer">
  <div class="wrap">
    <p>{links}</p>
    <p class="muted">© {e(SITE['name'])} · Last updated {e(SITE['updated'])}</p>
  </div>
</footer>
</body>
</html>
"""


def ul(items, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f"<ul{c}>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def ol(items, cls="entries"):
    return f'<ol class="{cls}">' + "".join(f"<li>{i}</li>" for i in items) + "</ol>"


def page_head(title, lead=""):
    return f'<h1>{e(title)}</h1>' + (f'<p class="lead">{lead}</p>' if lead else "")


def build_index():
    stats = "".join(
        f'<div class="stat"><strong>{e(s["value"])}</strong><span class="label">{e(s["label"])}</span>'
        f'<span class="sub">{e(s.get("sub", ""))}</span></div>'
        for s in SITE["stats"]
    )
    about = "".join(f"<p>{e(p)}</p>" for p in SITE["about"])
    about = about.replace(
        "Sample code is on GitHub.",
        'Sample code is on <a href="https://github.com/drbriancollins/MySampleWork" rel="noopener">GitHub</a>.',
    )
    expertise = "".join(
        f'<div class="card"><h3>{e(g["group"])}</h3>{ul([e(i) for i in g["items"]])}</div>' for g in SITE["expertise"]
    )
    career = "".join(
        f'<li><span class="dates">{e(c["dates"])}</span><div><strong>{e(c["role"])}</strong>'
        f'<span class="org">{e(c["org"])}</span></div></li>'
        for c in SITE["career"]
    )
    teaching = "".join(
        f'<li><span class="dates">{e(t["dates"])}</span><div><strong>{e(t["role"])}</strong>'
        f'<span class="org">{e(t["org"])}</span>{ul([e(d) for d in t["details"]], "details")}</div></li>'
        for t in SITE["teaching"]
    )
    links = "".join(f'<a class="button" href="{l["url"]}" rel="noopener">{e(l["label"])}</a>' for l in SITE["links"])
    body = f"""
<section class="hero">
  <h1>{e(SITE['name'])}<span class="post">, {e(SITE['postnominals'])}</span></h1>
  <p class="headline">{e(SITE['headline'])}</p>
  <p class="muted">{e(SITE['location'])}</p>
  <div class="buttons">{links}</div>
</section>
<section class="stats" aria-label="Highlights">{stats}</section>
<section><h2>About</h2>{about}</section>
<section><h2>Expertise</h2><div class="cards">{expertise}</div></section>
<section><h2>Career</h2><ol class="timeline">{career}</ol></section>
<section><h2>Education and certification</h2>{ul([e(x) for x in SITE['education']])}</section>
<section><h2>Teaching</h2><ol class="timeline">{teaching}</ol></section>
"""
    return page("", SITE["name"], f"{SITE['name']}, {SITE['postnominals']}: {SITE['headline']}.", body)


def build_publications():
    total = sum(len(s["items"]) for s in PUBS["sections"])
    toc = "".join(
        f'<a href="#{re.sub(r"[^a-z]+", "-", s["title"].lower()).strip("-")}">{e(s["title"])} ({len(s["items"])})</a>'
        for s in PUBS["sections"]
    )
    secs = "".join(
        f'<section id="{re.sub(r"[^a-z]+", "-", s["title"].lower()).strip("-")}">'
        f'<h2>{e(s["title"])} <span class="count">({len(s["items"])})</span></h2>{ol(s["items"])}</section>'
        for s in PUBS["sections"]
    )
    scholar = next(l["url"] for l in SITE["links"] if l["label"] == "Google Scholar")
    lead = (
        f"{SITE['stats'][0]['value']} peer-reviewed papers, 3 books and 66 conference presentations. "
        f'Citation metrics are on <a href="{scholar}" rel="noopener">Google Scholar</a>.'
    )
    body = page_head("Publications and presentations", lead) + f'<p class="note">{e(PUBS["note"])}</p>'
    body += f'<nav class="toc" aria-label="Sections">{toc}</nav>' + secs
    return page("publications", "Publications", f"Full list of {total} publications and presentations by {SITE['name']}.", body)


ROLE_RE = re.compile(r"\((Project Co-Lead|Project Lead|Principal Investigator|Theme Lead|Supervisor)\)")


def build_grants():
    items = [ROLE_RE.sub(lambda m: f"(<strong>{m.group(1)}</strong>)", e(g)) for g in SITE["grants"]]
    body = page_head("Research grants") + ul([e(s) for s in SITE["grants_summary"]], "summary") + ol(items)
    return page("grants", "Research grants", f"Funded research projects led or contributed to by {SITE['name']}.", body)


def build_supervision():
    def fmt(s):
        name, rest = s.split(". ", 1)
        return f"<strong>{e(name)}</strong>. {e(rest)}"

    body = page_head("Student supervision") + ul([e(s) for s in SITE["supervision_summary"]], "summary")
    body += ol([fmt(s) for s in SITE["supervision"]])
    return page("student-supervision", "Student supervision", f"Postgraduate research supervision by {SITE['name']}.", body)


def build_skills():
    cards = []
    for c in SKILLS["categories"]:
        rows = "".join(f'<dt>{e(l["level"])}</dt><dd>{e(l["items"])}</dd>' for l in c["levels"])
        cards.append(f'<div class="card"><h3>{e(c["name"])}</h3><dl>{rows}</dl></div>')
    body = page_head("Technical skills", "Proficiency: Advanced · Working proficiency · Familiarity")
    body += f'<div class="cards wide">{"".join(cards)}</div>'
    return page("technical-skills", "Technical skills", f"Technical skills of {SITE['name']}.", body)


def build_certificates():
    cert = "".join(f'<li><strong>{e(c["name"])}</strong>, {e(c["issuer"])}</li>' for c in SITE["certification"])
    parts = [page_head("Certification and training"), "<h2>Professional certification</h2>", f"<ul>{cert}</ul>"]
    parts.append("<h2>Completed training</h2>")
    for p in SITE["training"]:
        n = sum(len(g["courses"]) for g in p["groups"])
        groups = "".join(
            f'<h4>{e(g["topic"])}</h4>{ul([e(c) for c in g["courses"]], "courses")}' for g in p["groups"]
        )
        parts.append(f'<details open><summary>{e(p["provider"])} <span class="count">({n} courses)</span></summary>{groups}</details>')
    return page("certificates", "Certification and training", f"Professional certification and training completed by {SITE['name']}.", "".join(parts))


def build_other():
    media = [
        (f'<a href="{m["url"]}" rel="noopener">{e(m["text"])}</a>' if m["url"] else e(m["text"])) for m in SITE["media"]
    ]
    body = page_head("Media and professional service")
    body += "<h2>In the media</h2>" + ul(media)
    body += "<h2>Scientific committees and boards</h2>" + ul([e(c) for c in SITE["committees"]])
    body += f'<h2>Peer review</h2><p>{e(SITE["peer_review"])}</p>'
    return page("other", "Media and service", f"Media coverage and professional service of {SITE['name']}.", body)


def build_404():
    body = page_head("Page not found", 'The page you asked for does not exist. Go to the <a href="/">home page</a>.')
    return page("404", "Page not found", "Page not found.", body).replace('href="../', 'href="/')


def write(rel, text):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8", newline="\n")


def main():
    write("index.html", build_index())
    write("publications/index.html", build_publications())
    write("grants/index.html", build_grants())
    write("student-supervision/index.html", build_supervision())
    write("technical-skills/index.html", build_skills())
    write("certificates/index.html", build_certificates())
    write("other/index.html", build_other())
    write("404.html", build_404())
    urls = "".join(f"<url><loc>{BASE_URL}/{s + '/' if s else ''}</loc></url>" for s, _ in NAV)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")
    print("Built", len(NAV), "pages + 404")


if __name__ == "__main__":
    main()
