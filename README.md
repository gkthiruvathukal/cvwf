# George K. Thiruvathukal — Web-First CV

[![Deploy CV](https://github.com/gkthiruvathukal/cvwf/actions/workflows/deploy.yml/badge.svg)](https://github.com/gkthiruvathukal/cvwf/actions/workflows/deploy.yml)

Live at [cv.gkt.sh](https://cv.gkt.sh).

A web-first CV built with Astro, replacing the LaTeX-based build in `../cv`. The web page is the primary artifact; the PDF is generated *from* it via headless Chrome rather than the other way around. This exists because LaTeX is a print-era tool, and print is no longer the default output for a CV.

Design rationale and the original implementation plan live at `/Users/gkt/.claude/plans/enchanted-dancing-finch.md`.

## Architecture

- **[Astro](https://docs.astro.build)**, static output, islands architecture — ships ~0 client JS by default, which fits a content-heavy, mostly-static CV. The one bit of client JS is the publication type filter on `/publications/` (plain inline `<script>`, no framework).
- **Content collections** (`src/content.config.ts`) are the single source of truth for every section of the CV. Pages read from them via `getCollection()`/`getEntry()`; nothing is hand-coded into a page template.
- **Tailwind CSS v4** (`@tailwindcss/vite`) for styling. Current styling is intentionally minimal/clean, not the final visual design — see [Deferred work](#deferred-work).
- **Playwright** prints the `/cv/` route to PDF (`scripts/generate-pdf.mjs`). One layout is maintained for both the web page and the PDF; the PDF is literally "print this page" with `@media print` rules in `src/styles/global.css`.

## Directory structure

```
├── src/
│   ├── content.config.ts        # Zod schema for every collection
│   ├── content/
│   │   ├── personal/            # hand-authored
│   │   ├── education/           # hand-authored
│   │   ├── appointments/        # hand-authored (academic/industry/internship)
│   │   ├── chair-highlights/    # hand-authored
│   │   ├── recognition/         # hand-authored
│   │   ├── funding/             # hand-authored
│   │   ├── students/            # hand-authored
│   │   ├── service/             # hand-authored
│   │   ├── media/               # hand-authored
│   │   ├── publications/all.json        # GENERATED - not in git, see below
│   │   └── bibliometrics/bibliometrics.json  # GENERATED - not in git, see below
│   ├── layouts/BaseLayout.astro
│   ├── components/              # EntryRow, LineItem, PublicationEntry
│   └── pages/
│       ├── index.astro          # landing page
│       ├── publications/index.astro  # filterable publication list
│       └── cv.astro             # full CV, canonical section order - the PDF print target
├── scripts/
│   ├── fetch-zotero.sh          # Zotero groups -> bibliography/*-raw.bib
│   ├── sanitize-bib.py          # promotes tex.* Extra-field annotations to top-level fields
│   ├── bib-to-json.py           # bibliography/*.bib -> src/content/publications/all.json
│   ├── fetch-scholar-metrics.py # Google Scholar -> bibliometrics/scholar record
│   ├── fetch-github-stats.py    # GitHub contributions -> bibliometrics/github record
│   └── generate-pdf.mjs         # build + Playwright print /cv/ -> dist/cv-thiruvathukal.pdf
├── data/zotero-bibs.txt         # the 8 Zotero group URLs
└── bibliography/                # bib cache, GENERATED, not in git
```

## Data pipeline

Publication and bibliometric data is **not checked into git** — it's regenerated from Zotero, Google Scholar, and GitHub on demand (same pattern the LaTeX repo uses). From a fresh clone, run:

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install bibtexparser scholarly requests beautifulsoup4 pyyaml

./scripts/fetch-zotero.sh                                        # -> bibliography/*-raw.bib
python3 scripts/sanitize-bib.py                                  # -> bibliography/*.bib
python3 scripts/bib-to-json.py                                    # -> src/content/publications/all.json
python3 scripts/fetch-scholar-metrics.py --profile Ls7yS0IAAAAJ   # -> src/content/bibliometrics/bibliometrics.json
python3 scripts/fetch-github-stats.py --username gkthiruvathukal --first-year 2011
```

`fetch-scholar-metrics.py` is dual-mode: run locally like above, it scrapes Google Scholar live and pushes the result to GitHub repo variables (`gh variable set`, requires the `gh` CLI authenticated against this repo) so CI can reuse them. In CI (`GITHUB_ACTIONS=true`), it skips scraping - Google reliably blocks/CAPTCHAs requests from GitHub-hosted runner IPs - and reads those cached variables from the environment instead. **Run the local command at least once after creating the repo** to seed `CV_GSCHOLAR_ID`/`CV_GSCHOLAR_CITATIONS`/`CV_GSCHOLAR_H_INDEX`/`CV_GSCHOLAR_I10_INDEX`, or the first CI build will fail with a clear error telling you to do exactly that.

Everything else in `src/content/` (personal info, education, appointments, chair highlights, recognition, funding, students, service, media) is hand-authored YAML, transcribed once from `../cv/data/*.tex`, and checked into git normally — it is the actual source of truth going forward, not a cache. Edit those files directly; there is no script that regenerates them.

## Auditing for missing publications

Zotero can lag behind Google Scholar, which auto-indexes new work faster than anyone manually curates a reference library. Two scripts help close that gap:

```sh
python3 scripts/find-missing-pubs.py --profile Ls7yS0IAAAAJ --since-year 2023
```

Fetches George's full Scholar publication list, filters out service/editorial noise (program committees, editorial notices, Scholar merge errors) and arXiv preprints already in the corpus under a different title, and prints recent candidates with no good title match in `src/content/publications/all.json` — a shortlist to review by hand, not something to trust blindly (Scholar's own data includes duplicates, name collisions, and truncated venue names).

Once you've picked which candidates are real and confirmed their category (book/journal/conference/arXiv), hand-curate the title list at the top of `scripts/generate-missing-bibtex.py` (`CATEGORIES` dict) and run it:

```sh
python3 scripts/generate-missing-bibtex.py
```

Writes `missing-books.bib`, `missing-journal-papers.bib`, `missing-conference-papers.bib`, `missing-arxiv-papers.bib` at the repo root (gitignored — these are working files for importing into Zotero, not part of the site). It re-fetches each publication directly from George's Scholar profile page (not a keyword search — that was tested and found unreliable, since a same-topic title can rank above the actual paper) and hand-builds BibTeX from the verified fields Scholar returns. Entries with a truncated venue name or unresolvable arXiv ID get a `note` flagging that before importing.

## Content collections reference

| Collection | Source | Key fields |
| :--- | :--- | :--- |
| `personal` | hand-authored | name, title, address, contact, social links |
| `education` | hand-authored | dateRange, degree, institution, field, thesisTitle/thesisType, `category: degree \| lifelong-learning` |
| `appointments` | hand-authored | dateRange, title, institution, location, `type: academic \| industry \| internship` |
| `chair-highlights` | hand-authored | text (flat bullet list) |
| `recognition` | hand-authored | year, award, institution, location |
| `funding` | hand-authored | sponsorOrGrantId, role, title, amount, dateRange, `category: research-award \| university-funding \| gift` |
| `students` | hand-authored | name, degree, role, institution, dateRange, links, `group: loyola \| other-institutions \| masters-thesis` |
| `service` | hand-authored | role, body, dateRange, `category: university \| departmental \| panel \| conference-committee \| editorial-board` |
| `media` | hand-authored | outlet, title, url, date, `medium: television \| print` |
| `publications` | generated | full BibLaTeX field set, `pubType`, `citeKey`, `authors: {name, role}[]` (`role` parsed from `author+an`: `self`/`graduate`/`undergrad`/`null`) |
| `bibliometrics` | generated | one `scholar` record, one `github` record |

Every hand-authored collection has an explicit `order: number` field. **This is required** — Astro's content layer does not guarantee `getCollection()` preserves file/array order, so pages sort by `order` explicitly. `publications` sorts by `date` instead, since it has one.

## Commands

| Command | Action |
| :--- | :--- |
| `npm run dev` | Local dev server at `localhost:4321` |
| `npm run build` | Build the static site to `./dist/` |
| `npm run preview` | Preview the production build locally |
| `npm run pdf` | Build, then print `/cv/` to `dist/cv-thiruvathukal.pdf` via Playwright |
| `npx astro check` | Type-check content schemas and pages |

## Deployment

Hosted on GitHub Pages at the custom domain `cv.gkt.sh`, deployed by `.github/workflows/deploy.yml` on every push to `main`, weekly on a schedule (to pick up new Zotero/Scholar/GitHub data even without a code change), and on manual trigger.

One-time setup on GitHub, after the repo exists:

1. **Settings → Pages → Build and deployment → Source**: set to "GitHub Actions" (not "Deploy from a branch").
2. **Settings → Secrets and variables → Actions → Variables**: populate `CV_GSCHOLAR_ID`, `CV_GSCHOLAR_CITATIONS`, `CV_GSCHOLAR_H_INDEX`, `CV_GSCHOLAR_I10_INDEX` by running `python3 scripts/fetch-scholar-metrics.py --profile Ls7yS0IAAAAJ` locally once (see above) with the `gh` CLI authenticated against this repo.
3. **DNS**: at whatever registrar/DNS host manages `gkt.sh`, add a `CNAME` record: `cv` → `gkthiruvathukal.github.io`.
4. **Settings → Pages → Custom domain**: enter `cv.gkt.sh` (GitHub Pages also reads the `public/CNAME` file committed here, but setting it in the UI is what actually provisions the HTTPS certificate).

## Status

Phase 1 (data pipeline + full site skeleton) is complete: all CV sections render with real data, publications flow from Zotero, bibliometrics from Scholar/GitHub, and the PDF export works with a "Download PDF" link in the site nav.

Author-role highlighting (bold George's own name, italic + †/\* for graduate/undergraduate co-authors) is implemented and fully configurable via `src/config/author-highlight.ts`.

See `TODO.md` for open data-quality issues and remaining Phase 2 work (visual design, CI/CD, hosting).
