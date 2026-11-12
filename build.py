#!/usr/bin/env python3
"""Build fleurbouwer.nl from the YAML files in data/ into _site/.

    python3 build.py            # production build (clean URLs)
    python3 build.py --preview  # links point at index.html files, for local or preview viewing

Requires: pip install pyyaml jinja2
"""
import re
import shutil
import sys
from datetime import date
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape

ROOT = Path(__file__).parent
OUT = ROOT / "_site"
PREVIEW = "--preview" in sys.argv

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
KINDS = {"book": "Book", "paper": "Paper", "grant": "Grant", "media": "Media", "outreach": "Outreach", "talk": "Talk", "lab": "Lab", "music": "Music"}
OUTREACH_KINDS = {"media", "outreach"}  # shown on the Outreach page, not the News page
MEDIUMS = {"video": "Video", "audio": "Radio and podcasts", "print": "Print and online", "event": "Event"}
KINDS_NL = {"talk": "Lezing", "music": "Muziek", "book": "Boek", "paper": "Artikel", "grant": "Beurs", "media": "Media", "outreach": "Publieksactiviteit", "lab": "Lab"}
MONTHS_NL = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
             "augustus", "september", "oktober", "november", "december"]

# Old WordPress addresses that should keep working (old news posts are added automatically).
REDIRECTS = {
    "about-fleur/": "team/",
    "latest/": "news/",
    "media/": "outreach/#media",
    "publications/": None,  # same address on the new site
}


def load(name):
    with open(ROOT / "data" / f"{name}.yml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def boldme(authors):
    """Set Fleur's name in bold in an author list."""
    html = str(escape(authors))
    html = re.sub(r"(Bouwer,\s*F\.\s*L\.)", r"<strong>\1</strong>", html)
    return Markup(html)


def month(d, lang="en"):
    """Show a date as 'March 2026'. Accepts a date, 'YYYY-MM' or 'YYYY'."""
    names = MONTHS_NL if lang == "nl" else MONTHS
    if isinstance(d, int) or (isinstance(d, str) and len(d) == 4):
        return str(d)
    if isinstance(d, str) and len(d) == 7:
        return f"{names[int(d[5:7]) - 1]} {d[:4]}"
    if isinstance(d, str):
        d = date.fromisoformat(d)
    return f"{names[d.month - 1]} {d.year}"


def summary(text, limit=240):
    """First sentence(s) of a text, up to about `limit` characters."""
    if not text or len(text) <= limit:
        return text
    cut = text[:limit]
    ends = [m.end() - 1 for m in re.finditer(r"(?<!\bProf)(?<!\bDr)(?<!\be\.g)(?<!\bi\.e)[.!?] ", cut)]
    end = ends[-1] if ends else -1
    if end > 80:
        return cut[:end + 1]
    return cut[:cut.rfind(" ")] + "…"


def main():
    site = load("site")
    projects = load("projects")
    pubs = load("publications")
    news = sorted(load("news"), key=lambda n: str(n["date"]), reverse=True)
    team = load("team")
    outreach = load("outreach")

    projects_by_id = {p["id"]: p for p in projects}
    everyone = [dict(p) for p in team["current"]] + [dict(p, alumnus=True) for p in team["alumni"]]
    for pr in projects:
        pr["pubs"] = [p for p in pubs if pr["id"] in p.get("projects", [])]
        pr["news"] = [n for n in news if n.get("project") == pr["id"] and n["kind"] not in OUTREACH_KINDS]
        pr["people"] = [p for p in everyone if pr["id"] in p.get("projects", [])]
        pr["paragraphs"] = [x.strip() for x in pr["text"].strip().split("\n\n")]

    for n in news:
        n["dir"] = "outreach/" if n["kind"] in OUTREACH_KINDS else "news/"
        if n.get("body"):
            n["paragraphs"] = [x.strip() for x in n["body"].strip().split("\n\n")]
        if n.get("slug"):
            REDIRECTS[n["slug"] + "/"] = n["dir"] + n["slug"] + "/"
        elif n.get("old_slug"):
            REDIRECTS[n["old_slug"] + "/"] = n["dir"]
    media = [n for n in news if n["kind"] in OUTREACH_KINDS]
    # playable clips (YouTube or an audio file on this site) first, then the rest; newest first within each
    watch = [n for n in media if n.get("medium") in ("video", "audio")]
    watch = [n for n in watch if n.get("youtube") or n.get("audio")] + [n for n in watch if not (n.get("youtube") or n.get("audio"))]
    press = [n for n in media if n.get("medium") == "print"]
    events = [n for n in media if n.get("medium") == "event"]
    news = [n for n in news if n["kind"] not in OUTREACH_KINDS]
    news_kinds = {k: v for k, v in KINDS.items() if k not in OUTREACH_KINDS and any(n["kind"] == k for n in news)}
    pinned = [n for n in news if n.get("pinned")]
    news_by_year = []
    for n in [n for n in news if not n.get("pinned")]:
        y = str(n["date"])[:4]
        if not news_by_year or news_by_year[-1][0] != y:
            news_by_year.append((y, []))
        news_by_year[-1][1].append(n)
    latest = [n for n in news if not n.get("pinned")]

    years = sorted({p["year"] for p in pubs}, reverse=True)
    pubs_by_year = [(y, [p for p in pubs if p["year"] == y]) for y in years]
    outreach["book"]["paragraphs"] = [x.strip() for x in outreach["book"]["text"].strip().split("\n\n")]
    tiles = sorted(outreach["tiles"], key=lambda t: not t.get("featured"))

    nav = [
        {"path": "research/", "label": "Projects"},
        {"path": "publications/", "label": "Publications"},
        {"path": "team/", "label": "Team"},
        {"path": "news/", "label": "News"},
        {"path": "outreach/", "label": "Outreach"},
        {"path": "book/", "label": "Book"},
        {"path": "contact/", "label": "Contact"},
    ]
    nav_nl = [
        {"path": "research/", "label": "Projecten"},
        {"path": "publications/", "label": "Publicaties"},
        {"path": "team/", "label": "Team"},
        {"path": "news/", "label": "Nieuws"},
        {"path": "outreach/", "label": "Voor publiek"},
        {"path": "book/", "label": "Boek"},
        {"path": "contact/", "label": "Contact"},
    ]

    env = Environment(loader=FileSystemLoader(ROOT / "templates"),
                      autoescape=select_autoescape(["html"]), trim_blocks=True, lstrip_blocks=True)
    env.filters["boldme"] = boldme
    env.filters["month"] = month
    env.filters["summary"] = summary

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "static", OUT / "static")

    common = dict(site=site, projects=projects, projects_by_id=projects_by_id, pubs=pubs, pubs_by_year=pubs_by_year,
                  news=news, pinned=pinned, latest=latest, news_by_year=news_by_year, team=team, outreach=outreach, tiles=tiles,
                  media=media, watch=watch, press=press, events=events, news_kinds=news_kinds, mediums=MEDIUMS,
                  kinds=KINDS, kinds_nl=KINDS_NL)

    def render(template, path, **ctx):
        depth = path.count("/")
        prefix = "../" * depth

        def u(target):
            if target.startswith("http"):
                return target
            if PREVIEW and (target == "" or target.endswith("/")):
                target = target + "index.html"
            elif PREVIEW and "/#" in target:
                target = target.replace("/#", "/index.html#")
            return prefix + target if (prefix or target) else "./"

        lang = ctx.get("lang", "en")
        html = env.get_template(template).render(
            **common, u=u, path=path.replace("index.html", ""),
            nav=nav_nl if lang == "nl" else nav, **ctx)
        dest = OUT / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")

    render("home.html", "index.html", section="", description=site["hero_text"])
    render("research.html", "research/index.html", title="Projects", section="research/")
    for pr in projects:
        render("project.html", f"research/{pr['id']}/index.html", pr=pr, title=pr["title"],
               description=pr["short"], section="research/")
    render("publications.html", "publications/index.html", title="Publications", section="publications/")
    render("team.html", "team/index.html", title="Team", section="team/")
    render("news.html", "news/index.html", title="News", section="news/")
    for n in news + media:
        if n.get("slug"):
            render("article.html", f"{n['dir']}{n['slug']}/index.html", n=n, title=n["title"],
                   description=n.get("text") or n["title"], section=n["dir"], lang_item=n.get("lang"))
    render("outreach.html", "outreach/index.html", title="Outreach", section="outreach/")
    render("book.html", "book/index.html", title="What Is Music For?", section="book/",
           description="What Is Music For?, a popular science book by Fleur Bouwer (Bristol University Press, March 2027).")
    render("contact.html", "contact/index.html", title="Contact", section="contact/")
    render("nl.html", "nl/index.html", title="In het Nederlands", lang="nl", section="nl/",
           description="Fleur Bouwer onderzoekt muziek, ritme en het brein aan de Universiteit Leiden.")
    render("404.html", "404.html", title="Page not found")

    for old, new in REDIRECTS.items():
        if new is None:
            continue
        dest = OUT / old / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        if PREVIEW:
            rel = new.replace("/#", "/index.html#") if "#" in new else new + "index.html"
            target = "../" * old.count("/") + rel
        else:
            target = "/" + new
        dest.write_text(env.get_template("redirect.html").render(target=target), encoding="utf-8")

    (OUT / ".nojekyll").write_text("")
    print(f"Built {sum(1 for _ in OUT.rglob('*.html'))} pages into {OUT}")


if __name__ == "__main__":
    main()
