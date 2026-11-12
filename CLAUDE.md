# Instructions for maintaining fleurbouwer.nl

This is Fleur Bouwer's academic website (Leiden University, music cognition). Fleur sends updates in plain language; you turn them into edits of the YAML files in `data/`.

Rules:
- Nothing goes to `main` (= live) without Fleur's explicit OK in chat for that change. Prepare changes on a branch, show her the new entry as text (small changes) or a rendered preview (bigger changes), then merge.
- Content changes go in `data/*.yml` only; touch templates or CSS only when the layout must change.
- New publication from a DOI: look up the full reference, add it to `data/publications.yml` with `projects`, and add a short news item if Fleur wants one.
- New team member: add to `data/team.yml`; move people to `alumni` when they leave. Only use photos that the person has agreed to.
- Keep the AI note in the footer (`site.yml: ai_note`).
- Write for a general audience on project pages; a project text is overarching, funding is a plain list (name + years); keep Dutch items marked `lang: nl`.
- Run `python3 build.py --preview` and check the result before proposing a merge.
- Pinned news (`pinned: true` in `data/news.yml`) stays on top of the home and news pages; unpin when it is no longer current.
