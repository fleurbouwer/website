# fleurbouwer.nl

The website of Dr Fleur Bouwer, Leiden University. Built and maintained with help from Claude (Anthropic); every change is approved by Fleur.

## How it works

All content lives in plain text files in `data/`:

| File | What is in it |
| --- | --- |
| `data/site.yml` | Name, contact, home-page heading, bio, footer links |
| `data/projects.yml` | Research projects, with text, funding and collaborators |
| `data/publications.yml` | Publications; each lists the projects it belongs to |
| `data/team.yml` | Current team, alumni, selected students |
| `data/news.yml` | News and media items |
| `data/outreach.yml` | Outreach tiles, lectures and the book |

`build.py` turns these into the web pages in `_site/`, using the templates in `templates/` and the styles in `static/css/site.css`. When something is pushed to the `main` branch, GitHub builds and publishes the site automatically (see `.github/workflows/pages.yml`).

## Editing by hand

Edit a file in `data/` on github.com (pencil icon), keep the indentation as it is, and commit to `main`. The site updates within a few minutes. To check locally: `pip install pyyaml jinja2 && python3 build.py --preview`, then open `_site/index.html`.

Photos go in `static/img/`. Fonts (Bricolage Grotesque, Source Serif 4) are self-hosted under the SIL Open Font License; no external services, cookies or tracking are used.
