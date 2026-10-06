# George K. Thiruvathukal — Web-First CV

[![Deploy CV](https://github.com/gkthiruvathukal/cvwf/actions/workflows/deploy.yml/badge.svg)](https://github.com/gkthiruvathukal/cvwf/actions/workflows/deploy.yml)

Live at [cv.gkt.sh](https://cv.gkt.sh).

A web-first CV built with Astro, replacing the LaTeX-based build in `../cv`. The web page is the primary artifact; the PDF is generated *from* it via headless Chrome rather than the other way around. This exists because LaTeX is a print-era tool, and print is no longer the default output for a CV.

Design rationale and the original implementation plan live at `/Users/gkt/.claude/plans/enchanted-dancing-finch.md`.

## Architecture

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for a component/interaction diagram covering the full data pipeline, build, and deploy flow.

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
│   ├── components/              # EntryRow, LineItem, PublicationEntry, AuthorList,
│   │                             # AuthorHighlightLegend, Icon, BuildDate
│   ├── config/author-highlight.ts  # co-author role highlighting styles (see AGENTS.md)
│   └── pages/
│       ├── index.astro          # landing page
│       ├── publications/index.astro  # filterable publication list
│       └── cv.astro             # full CV, canonical section order - the PDF print target
├── scripts/
│   ├── build-local.sh           # runs everything below, in order, then npm run pdf
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

Publication and bibliometric data is **not checked into git** — it's regenerated from Zotero, Google Scholar, and GitHub on demand (same pattern the LaTeX repo uses). From a fresh clone, run the whole pipeline plus build and PDF in one shot:

```sh
npm run build:local   # scripts/build-local.sh
```

That script (venv setup, all five fetch/convert steps, `npm install`, `npm run pdf`) requires the `gh` CLI authenticated against this repo, since `fetch-scholar-metrics.py` pushes scraped values to GitHub repo variables for CI to reuse later (see below). Read it top to bottom if you want to understand or run the pipeline step by step — it's the same commands laid out individually below (Python 3.10+ is required for `bibtexparser` 2.x):

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install "bibtexparser>=2" requests beautifulsoup4 pyyaml

./scripts/fetch-zotero.sh                                        # -> bibliography/*-raw.bib
python3 scripts/sanitize-bib.py                                  # -> bibliography/*.bib
python3 scripts/bib-to-json.py                                    # -> src/content/publications/all.json
# scholarly needs bibtexparser 1.x, so use a separate venv for it:
python3 -m venv .venv-scholar && .venv-scholar/bin/pip install scholarly "bibtexparser<2" requests pyyaml
.venv-scholar/bin/python scripts/fetch-scholar-metrics.py --profile Ls7yS0IAAAAJ   # -> src/content/bibliometrics/bibliometrics.json
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
| `npm run build:local` | Full pipeline from a fresh clone: venv + fetch/convert scripts, `npm install`, `npm run pdf` |
| `npm run dev` | Local dev server at `localhost:4321` |
| `npm run build` | Build the static site to `./dist/` |
| `npm run preview` | Preview the production build locally |
| `npm run pdf` | Build, then print `/cv/` to `dist/cv-thiruvathukal.pdf` via Playwright |
| `npm run docx` | Convert the built `/cv/` page to `dist/cv-thiruvathukal.docx` with pandoc (run after `npm run pdf`; needs `pandoc`) |
| `npx astro check` | Type-check content schemas and pages |

## Deployment

Hosted on GitHub Pages at the custom domain `cv.gkt.sh`, deployed by `.github/workflows/deploy.yml` on every push to `main`, on every `v*` tag push, weekly on a schedule (to pick up new Zotero/Scholar/GitHub data even without a code change), and on manual trigger.

One-time setup on GitHub, after the repo exists:

1. **Settings → Pages → Build and deployment → Source**: set to "GitHub Actions" (not "Deploy from a branch").
2. **Settings → Secrets and variables → Actions → Variables**: populate `CV_GSCHOLAR_ID`, `CV_GSCHOLAR_CITATIONS`, `CV_GSCHOLAR_H_INDEX`, `CV_GSCHOLAR_I10_INDEX` by running `.venv-scholar/bin/python scripts/fetch-scholar-metrics.py --profile Ls7yS0IAAAAJ` locally once (see above) with the `gh` CLI authenticated against this repo.
3. **DNS**: at whatever registrar/DNS host manages `gkt.sh`, add a `CNAME` record: `cv` → `gkthiruvathukal.github.io`.
4. **Settings → Environments → github-pages → Deployment branches and tags**: allow both the `main` branch and the tag pattern `v*`. By default the environment only accepts `main`, so a tag-triggered run (which creates a release and refreshes the version badge) builds fine but its deploy job is rejected.
5. **Settings → Pages → Custom domain**: enter `cv.gkt.sh` (GitHub Pages also reads the `public/CNAME` file committed here, but setting it in the UI is what actually provisions the HTTPS certificate).

## Word version

`dist/cv-thiruvathukal.docx` ("Download Word" in the nav) is derived from the same built `/cv/` page as the PDF, so the content, ordering and metrics always match. `scripts/generate-docx.mjs` runs [pandoc](https://pandoc.org) over `dist/cv/index.html` with two committed files in `templates/`:

- **`templates/reference.docx`** - the Word styles (Title, Heading 1/2, body text, tables, hyperlinks, and the centered "CV Header" style used for the role/address/contact block). It starts from pandoc's default blue-headings/black-text template. **To restyle the output, open this file in Word and edit the styles** (Home → Styles → right-click → Modify), then save; the next build picks it up. No code changes needed.
- **`templates/cv-docx.lua`** - a pandoc filter that translates the page's markup into Word constructs: date rows become a two-column table, publication entries become one tight paragraph each, the Impact Summary stat tiles become a table, bold/italic come from the page's `font-medium`/`italic` classes, and the nav and icons are dropped. If you change which Tailwind classes carry meaning in `cv.astro` or its components, update the filter to match.

Requires `pandoc` (`brew install pandoc` locally; CI installs it via apt). Run order matters: `npm run pdf` then `npm run docx` - a later `astro build` clears `dist/`, which deletes both the PDF and the `.docx`. `npm run build:local` and CI do this in the right order.

## Versioning and the build badge

The CV's version is the **latest git tag** (e.g. `v0.5`), shown with the build date as a two-segment badge (tag icon + version | date) by `src/components/BuildDate.astro`. That one component is rendered on the landing page, `/cv/` (and therefore the PDF, which prints that page), and `/publications/`, so all outputs always agree. The badge's tooltip carries the full timestamp (Central time); the PDF shows version and date only.

- **Cut a release:** `git tag v0.6 && git push --tags`. Pushing a `v*` tag triggers a deploy, and the next build of every output (site, PDF, Word) shows the new version. The same run also creates a **GitHub Release** for the tag with `cv-thiruvathukal-<tag>.pdf` and `cv-thiruvathukal-<tag>.docx` attached (the `release` job in `deploy.yml`), so every tagged version keeps a downloadable snapshot. Commits between tags don't change it; there is no version number in `package.json` to keep in sync.
- **How it's computed:** `git describe --tags --abbrev=0` at build time. CI checks out with `fetch-depth: 0` so tags are present; without that the shallow clone has none and the badge silently falls back to date-only.
- **Fallback:** if git or tags are unavailable (e.g. building from a tarball), only the date segment renders; the build never fails over it.

### Keeping impact metrics current

Everything reaching the web pages and the PDF (citations, h-index, i10, GitHub contributions, publication count) is regenerated by the pipeline on every build, but the sources differ in how fresh they are:

| Metric | CI build | Local `build:local` |
|---|---|---|
| Publications / Zotero | live fetch each build | live fetch |
| GitHub contributions | live fetch each build | live fetch |
| Google Scholar (citations, h, i10) | **cached** repo variables `CV_GSCHOLAR_*` (Google blocks CI runner IPs) | live scrape, then pushes new values to the repo variables |

So the Scholar numbers only change when someone runs the scrape locally (`npm run build:local`, or just the Scholar step above) with `gh` authenticated. The weekly scheduled build rebuilds with whatever values were last pushed. Refresh them after a notable change in citations, then push or re-run the workflow to publish.

## Status

Phase 1 (data pipeline + full site skeleton) is complete: all CV sections render with real data, publications flow from Zotero, bibliometrics from Scholar/GitHub, and the PDF export works with a "Download PDF" link in the site nav.

Author-role highlighting (bold George's own name, italic + †/\* for graduate/undergraduate co-authors) is implemented and fully configurable via `src/config/author-highlight.ts`.

CI/CD and hosting are also done: `deploy.yml` re-runs the full pipeline and redeploys on every push, tag, weekly schedule, and manual trigger (see [Deployment](#deployment)). The only open Phase 2 work is visual design. See `TODO.md` for that and open data-quality issues, and [`ARCHITECTURE.md`](ARCHITECTURE.md) for how all the pieces fit together.
