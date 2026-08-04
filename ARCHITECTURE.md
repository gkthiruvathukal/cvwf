# Architecture

Component/interaction diagram for the CV site. See `README.md` for the prose walkthrough of the data pipeline and commands — this doc focuses on how the pieces fit together.

The system has three distinct runtime contexts, easy to conflate but worth keeping separate: an **offline data pipeline** (runs on demand or in CI, never in the browser), an **Astro build** (turns content + code into static HTML), and **CI/CD + hosting** (what actually runs the pipeline and build, and serves the result).

```mermaid
flowchart TB
    subgraph sources["External sources"]
        zotero["Zotero groups\n(8 BibLaTeX exports)"]
        scholar["Google Scholar\nprofile"]
        github["GitHub\ncontributions API"]
    end

    subgraph pipeline["Offline data pipeline (scripts/)"]
        fetchZotero["fetch-zotero.sh"]
        sanitize["sanitize-bib.py"]
        bibToJson["bib-to-json.py"]
        fetchScholar["fetch-scholar-metrics.py"]
        fetchGithub["fetch-github-stats.py"]
    end

    zotero --> fetchZotero --> sanitize --> bibToJson
    scholar --> fetchScholar
    github --> fetchGithub

    subgraph content["src/content/ (content collections)"]
        pubJson["publications/all.json\nGENERATED"]
        bibJson["bibliometrics/bibliometrics.json\nGENERATED"]
        yaml["personal, education, appointments,\nchair-highlights, recognition, funding,\nstudents, service, media\nHAND-AUTHORED YAML"]
    end

    bibToJson --> pubJson
    fetchScholar --> bibJson
    fetchGithub --> bibJson

    configTs["content.config.ts\nZod schemas + file() loaders"]
    pubJson --> configTs
    bibJson --> configTs
    yaml --> configTs

    subgraph astro["Astro build"]
        subgraph pages["src/pages/"]
            index["index.astro\n(landing)"]
            pubsPage["publications/index.astro\n(filterable list)"]
            cv["cv.astro\n(full CV, canonical\nsection order)"]
        end
        layout["BaseLayout.astro\n(nav, print/no-print shell)"]
        subgraph components["src/components/"]
            entryRow["EntryRow"]
            lineItem["LineItem"]
            pubEntry["PublicationEntry"]
            authorList["AuthorList"]
            legend["AuthorHighlightLegend"]
            icon["Icon"]
            buildDate["BuildDate"]
        end
        highlightConfig["src/config/\nauthor-highlight.ts"]
    end

    configTs -->|getCollection / getEntry| index
    configTs -->|getCollection / getEntry| pubsPage
    configTs -->|getCollection / getEntry| cv

    index --> layout
    pubsPage --> layout
    cv --> layout

    cv --> entryRow & lineItem & pubEntry & legend & buildDate
    pubsPage --> pubEntry
    pubsPage --> legend
    index --> buildDate
    pubEntry --> authorList
    authorList --> highlightConfig
    legend --> highlightConfig

    dist["dist/\n(static site,\nnpx astro build)"]
    astro --> dist

    subgraph pdfGen["scripts/generate-pdf.mjs"]
        serve["serves dist/ over HTTP"]
        chrome["Playwright headless Chrome\nprints /cv/ under @media print"]
    end
    dist --> serve --> chrome --> pdf["dist/cv-thiruvathukal.pdf"]

    subgraph cicd["CI/CD — .github/workflows/deploy.yml"]
        trigger["Triggers:\npush to main, v* tags,\nweekly cron, manual dispatch"]
        run["Runs pipeline scripts,\nnpm run pdf,\nuploads dist/ as Pages artifact"]
    end
    trigger --> run
    run -.orchestrates.-> pipeline
    run -.orchestrates.-> pdfGen

    pagesHost["GitHub Pages\ncv.gkt.sh"]
    run --> pagesHost
```

## Walkthrough

**Pipeline** (`scripts/`, gitignored outputs, re-run on demand or by CI): `fetch-zotero.sh` pulls raw BibLaTeX per Zotero group, `sanitize-bib.py` promotes `tex.*` Extra-field annotations (like `author+an`) to top-level fields, and `bib-to-json.py` merges everything into `src/content/publications/all.json` — parsing per-author roles along the way (see `AuthorList.astro` below). `fetch-scholar-metrics.py` and `fetch-github-stats.py` independently populate `src/content/bibliometrics/bibliometrics.json`. None of this runs at request time; it's a build-time data refresh.

**Content layer** (`src/content.config.ts`): the single ingestion boundary. Every page reads through `getCollection()`/`getEntry()` against Zod-typed collections — generated JSON and hand-authored YAML are indistinguishable to a page once they're through this layer. This is also where the `order`-field sorting requirement lives (see `AGENTS.md` rule 2).

**Pages + components** (`src/pages/`, `src/components/`): three pages share one `BaseLayout.astro` shell. `cv.astro` is the canonical, most section-complete page (also the PDF print target); `publications/index.astro` is a filtered subset with client-side JS for the type filter; `index.astro` is a landing page with headline stats. Shared rendering logic (`EntryRow`, `LineItem`, `PublicationEntry`) keeps section markup consistent; `AuthorList.astro` and `AuthorHighlightLegend.astro` both read their styling from `src/config/author-highlight.ts`, the single place to change how co-author roles are highlighted.

**Build output + PDF**: `astro build` produces static `dist/`. `scripts/generate-pdf.mjs` then serves that same `dist/` and has Playwright screenshot the `/cv/` route under print media to `dist/cv-thiruvathukal.pdf` — one layout, two outputs. `npm run pdf` runs both steps; a bare `astro build` afterward would wipe the PDF (see `AGENTS.md` rule 7).

**CI/CD + hosting**: `.github/workflows/deploy.yml` is the only place all of the above actually gets chained end-to-end — it re-runs the full pipeline, then `npm run pdf`, then deploys `dist/` to GitHub Pages. It fires on pushes to `main`, on `v*` tag pushes, weekly (to pick up upstream data changes with no code change), and on manual dispatch. The live site is `cv.gkt.sh`, a GitHub Pages custom domain.
