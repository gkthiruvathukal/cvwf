# Working on this repository

This is George K. Thiruvathukal's web-first CV. Read `README.md` first for architecture and the data pipeline. The original design rationale and implementation plan are at `/Users/gkt/.claude/plans/enchanted-dancing-finch.md`. Open items are tracked in `TODO.md`.

## Rules for this codebase

1. **Never hand-edit generated data.** `src/content/publications/all.json` and `src/content/bibliometrics/bibliometrics.json` are produced by `scripts/bib-to-json.py`, `scripts/fetch-scholar-metrics.py`, and `scripts/fetch-github-stats.py`. If something in those files is wrong, fix it upstream (the Zotero record, or the scripts' field mapping) and re-run the pipeline — don't patch the JSON directly, it will be overwritten on the next fetch. Everything else under `src/content/` (personal, education, appointments, chair-highlights, recognition, funding, students, service, media) is hand-authored YAML with no generator — edit those directly.

2. **Every hand-authored collection needs an `order: number` field, and every page must sort by it explicitly.** Astro's content layer (`getCollection()`) does **not** guarantee it returns entries in file/array order — this was discovered mid-build when Academic Appointments rendered in a scrambled order despite the YAML being written chronologically. `publications` is the exception: it sorts by `date` string instead (see `cv.astro` and `publications/index.astro` for the pattern). If you add a new collection that needs a stable display order, add the `order` field to its Zod schema in `src/content.config.ts` and populate it in the YAML — don't rely on file order.

3. **Publication `id`s are namespaced `${pubType}-${citeKey}`, not just the bare citation key.** Some Zotero citation keys collide across the different pub-type groups (e.g. an arXiv preprint techreport and its later published inproceedings version were both entered under the same key). Collapsing this namespacing will reintroduce duplicate-id warnings/silent overwrites in the content collection. `citeKey` is kept as a separate field if you need the original key.

4. **Pipeline run order matters and nothing in it is committed to git**: `fetch-zotero.sh` → `sanitize-bib.py` → `bib-to-json.py`, and separately `fetch-scholar-metrics.py` / `fetch-github-stats.py`. All of `bibliography/` and the two generated content JSON files are gitignored (matching `../cv/.gitignore`'s pattern of never committing fetched bibliography data) — a fresh clone must run the pipeline (see README) before `astro build`/`astro dev` will work, because the `file()` content loader errors if the JSON doesn't exist.

5. **BibLaTeX brace-protection and LaTeX escapes are cleaned in `bib-to-json.py`'s `clean_latex()`**, which is a best-effort strip of `{}`/`\&`/`\_`/etc, not a full LaTeX-to-text converter. Some abstracts retain raw markup artifacts from the Zotero export (broken citation commands, stray backslashes) — this is a known, low-priority cosmetic issue (see `TODO.md`), not something to "fix" by writing a heavier parser unless asked.

6. **`author+an` (per-author role annotation: self/graduate/undergrad) is parsed in `bib-to-json.py`'s `parse_author_roles()` into `authors[].role`** (`"self" | "graduate" | "undergrad" | null`, null when an author has no annotation - most external/senior co-authors). Rendering lives in `AuthorList.astro`, which reads all styling (CSS classes, symbols, whether it's superscripted) from `src/config/author-highlight.ts` - change highlighting there, not by hand-editing the component. `AuthorHighlightLegend.astro` auto-shows the legend on any publication list that has at least one highlighted author, and hides itself otherwise.

7. **The PDF is the web page, printed.** `scripts/generate-pdf.mjs` builds the site, serves `dist/`, and calls `page.pdf()` on the `/cv/` route with `@media print` CSS from `src/styles/global.css` (`.no-print` hides nav, `.avoid-break` prevents mid-entry page breaks). Do not create a second, separately-templated PDF layout — if the PDF needs to look different, change the print CSS or `cv.astro`, not a parallel render path.

## Development

When starting the dev server, use background mode:

```
astro dev --background
```

Manage the background server with `astro dev stop`, `astro dev status`, and `astro dev logs`.

## Astro documentation

Full documentation: https://docs.astro.build

Consult these guides before working on related tasks:

- [Adding pages, dynamic routes, or middleware](https://docs.astro.build/en/guides/routing/)
- [Working with Astro components](https://docs.astro.build/en/basics/astro-components/)
- [Using React, Vue, Svelte, or other framework components](https://docs.astro.build/en/guides/framework-components/)
- [Adding or managing content](https://docs.astro.build/en/guides/content-collections/)
- [Adding styles or using Tailwind](https://docs.astro.build/en/guides/styling/)
- [Supporting multiple languages](https://docs.astro.build/en/guides/internationalization/)
