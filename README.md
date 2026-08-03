# George K. Thiruvathukal — Web-First CV

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

Everything else in `src/content/` (personal info, education, appointments, chair highlights, recognition, funding, students, service, media) is hand-authored YAML, transcribed once from `../cv/data/*.tex`, and checked into git normally — it is the actual source of truth going forward, not a cache. Edit those files directly; there is no script that regenerates them.

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

## Status

Phase 1 (data pipeline + full site skeleton) is complete: all CV sections render with real data, publications flow from Zotero, bibliometrics from Scholar/GitHub, and the PDF export works with a "Download PDF" link in the site nav.

Author-role highlighting (bold George's own name, italic + †/\* for graduate/undergraduate co-authors) is implemented and fully configurable via `src/config/author-highlight.ts`.

See `TODO.md` for open data-quality issues and remaining Phase 2 work (visual design, CI/CD, hosting).
