# TODO

## Data quality (found during the Phase 1 build)

- [ ] **Two Zotero groups return "Forbidden" from the API**: `gkt-misc` and `gkt-theses` (same behavior in `../cv`, so it's a Zotero permissions issue, not a pipeline bug). Nothing renders for these two publication types until group sharing/permissions are fixed on the Zotero side.
- [ ] **Duplicate grant ID in funding data**: two entries in `src/content/funding/funding.yaml` both use `NSF CCF-2515526` (`nsf-ccf-2515526-cross` and `nsf-ccf-2515526-nairr`) with different titles and amounts. Worth checking against the actual award records — likely one of these has the wrong grant number transcribed in the original LaTeX source.
- [ ] **Four publications share a citation key across two Zotero pub-type groups** (same paper cross-listed, e.g. an arXiv preprint techreport later published as an inproceedings paper under the same key): `ahlgren_not-so-secret_2025`, `fahara-ojeda_exact_2025`, `veselsky_establishing_2022`, `dematties_towards_2020`. The pipeline handles this safely today (ids are namespaced by pubType, see `AGENTS.md`), but it's worth deciding whether these should actually be de-duplicated in Zotero (keep only the published version) or intentionally kept as two separate entries (preprint + final version).
- [ ] **Minor rendering polish**: techreport/arXiv-preprint entries with no `venue`/`institution` field render as `no. arXiv:XXXX, <date>` on the publications list — a bit awkward phrasing, low priority.
- [ ] **Abstracts retain some raw LaTeX/Zotero export artifacts** (broken citation commands, stray backslashes) that `clean_latex()` in `bib-to-json.py` doesn't fully clean up. Low priority since abstracts aren't currently displayed on any page.

## Phase 2 — Visual design

- [ ] The "futuristic" visual design system (motion, glass/gradient styling, dark mode) — current styling is intentionally minimal/clean, not final.
- [ ] Reference/inspiration gathering for the visual direction hasn't happened yet.

## Phase 2 — Features

- [ ] Parse `author+an` (raw passthrough today as `authorAnnotations`) into structured per-author roles and render the highlighting (bold George's own name, italicize student co-authors) — explicitly requested, explicitly deferred until the basic pipeline was working.
- [ ] CI/CD: a GitHub Actions workflow to re-run the fetch scripts (Zotero/Scholar/GitHub), rebuild, and redeploy on a schedule — mirrors what `../cv` already does.
- [ ] Choose and set up a hosting/deployment target (GitHub Pages vs. Vercel vs. Netlify vs. Cloudflare Pages).

## Resolved

- [x] ~~No way to download the PDF from the site~~ — a "Download PDF" link now sits in the nav (`BaseLayout.astro`), pointing to `/cv-thiruvathukal.pdf`.
