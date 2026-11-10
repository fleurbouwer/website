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
KINDS = {"paper": "Paper", "grant": "Grant", "media": "Media", "outreach": "Outreach", "lab": "Lab"}
KINDS_NL = {"paper": "Artikel", "grant": "Beurs", "media": "Media", "outreach": "Publieksactiviteit", "lab": "Lab"}
MONTHS_NL = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
             "augustus", "september", "oktober", "november", "december"]

# Old WordPress addresses that should keep working.
REDIRECTS = {
    "about-fleur/": "team/",
    "latest/": "news/",
    "media/": "news/#media",
    "new-paper-in-cognition-modelling-processing-of-rhythmic-patterns/": "news/",
    "new-paper-do-musicians-have-better-short-term-memory-than-nonmusicians-a-multilab-study/": "news/",
    "new-paper-eeg-responses-to-rhythm-at-different-tempi/": "news/",
    "waarom-tellen-dansers-af-met-5678/": "news/",
    "nemo-blijf-nieuwsgierig/": "news/",
    "3-october-university/": "news/",
    "waarom-lijken-veel-liedjes-zo-op-elkaar/": "news/",
    "snaartjes-festival-2024/": "news/",
    "waarom-zijn-meau-en-flemming-zo-populair-bij-kinderen/": "news/",
    "launch-of-toontjehoger/": "outreach/",
    "item-on-amsterdam-dance-event-in-atlas-tv/": "news/",
    "nemo-childrens-lecture/": "news/",
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
    if isinstance(d, str):
        d = date.fromisoformat(d)
    names = MONTHS_NL if lang == "nl" else MONTHS
    return f"{names[d.month - 1]} {d.year}"


def main():
    site = load("site")
    themes = load("themes")
    pubs = load("publications")
    news = sorted(load("news"), key=lambda n: str(n["date"]), reverse=True)
    team = load("team")
    outreach = load("outreach")

    themes_by_id = {t["id"]: t for t in themes}
    everyone = [dict(p) for p in team["current"]] + [dict(p, alumnus=True) for p in team["alumni"]]
    for t in themes:
        t["pubs"] = [p for p in pubs if t["id"] in p.get("themes", [])]
        t["news"] = [n for n in news if n.get("theme") == t["id"]]
        t["people"] = [p for p in everyone if t["id"] in p.get("themes", [])]
        for key in ("intro",):
            t[key] = t[key].strip()
        for pr in t["projects"]:
            pr["text"] = pr["text"].strip()

    years = sorted({p["year"] for p in pubs}, reverse=True)
    pubs_by_year = [(y, [p for p in pubs if p["year"] == y]) for y in years]

    nav = [
        {"path": "research/", "label": "Research"},
        {"path": "publications/", "label": "Publications"},
        {"path": "team/", "label": "Team"},
        {"path": "news/", "label": "News & media"},
        {"path": "outreach/", "label": "Outreach"},
        {"path": "book/", "label": "Book"},
        {"path": "contact/", "label": "Contact"},
    ]
    nav_nl = [
        {"path": "research/", "label": "Onderzoek"},
        {"path": "publications/", "label": "Publicaties"},
        {"path": "team/", "label": "Team"},
        {"path": "news/", "label": "Nieuws"},
        {"path": "book/", "label": "Boek"},
        {"path": "contact/", "label": "Contact"},
    ]

    env = Environment(loader=FileSystemLoader(ROOT / "templates"),
                      autoescape=select_autoescape(["html"]), trim_blocks=True, lstrip_blocks=True)
    env.filters["boldme"] = boldme
    env.filters["month"] = month

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "static", OUT / "static")

    common = dict(site=site, themes=themes, themes_by_id=themes_by_id, pubs=pubs, pubs_by_year=pubs_by_year,
                  news=news, team=team, outreach=outreach, kinds=KINDS, kinds_nl=KINDS_NL)

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
    render("research.html", "research/index.html", title="Research", section="research/")
    for t in themes:
        render("theme.html", f"research/{t['id']}/index.html", t=t, title=t["title"],
               description=t["short"], section="research/")
    render("publications.html", "publications/index.html", title="Publications", section="publications/")
    render("team.html", "team/index.html", title="Team", section="team/")
    render("news.html", "news/index.html", title="News and media", section="news/")
    render("outreach.html", "outreach/index.html", title="Outreach and teaching", section="outreach/")
    render("book.html", "book/index.html", title="Book", section="book/")
    render("contact.html", "contact/index.html", title="Contact", section="contact/")
    render("nl.html", "nl/index.html", title="In het Nederlands", lang="nl", section="nl/",
           description="Fleur Bouwer onderzoekt muziek, ritme en het brein aan de Universiteit Leiden.")
    render("404.html", "404.html", title="Page not found")

    for old, new in REDIRECTS.items():
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
