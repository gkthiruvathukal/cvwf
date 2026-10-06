#!/bin/bash
# Runs the full local pipeline end to end: Python venv + deps, Zotero fetch,
# bib sanitize/convert, Scholar + GitHub bibliometrics, then the Astro build
# and Playwright PDF export. This is what README.md's "Data pipeline" section
# describes by hand, wired into one script so a fresh clone is one command.
#
# Requires: python3, node/npm, and the gh CLI authenticated against this repo
# (fetch-scholar-metrics.py pushes CV_GSCHOLAR_* to GitHub repo variables).
set -euo pipefail

cd "$(dirname "$0")/.."

SCHOLAR_PROFILE="Ls7yS0IAAAAJ"
GITHUB_USERNAME="gkthiruvathukal"
GITHUB_FIRST_YEAR="2011"

echo "==> Python venv"
# bibtexparser 2.x needs Python >= 3.10; on older Pythons pip silently installs 1.x.
python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' \
  || { echo "python3 >= 3.10 required (found $(python3 --version))" >&2; exit 1; }
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet "bibtexparser>=2" scholarly requests beautifulsoup4 pyyaml

echo "==> Fetching Zotero bibliography groups"
./scripts/fetch-zotero.sh

echo "==> Sanitizing BibLaTeX (promoting tex.* Extra-field annotations)"
python3 scripts/sanitize-bib.py

echo "==> Converting bibliography to publications content collection"
python3 scripts/bib-to-json.py

echo "==> Fetching Google Scholar metrics"
python3 scripts/fetch-scholar-metrics.py --profile "$SCHOLAR_PROFILE"

echo "==> Fetching GitHub contribution stats"
python3 scripts/fetch-github-stats.py --username "$GITHUB_USERNAME" --first-year "$GITHUB_FIRST_YEAR"

deactivate

echo "==> Installing npm dependencies"
npm install

echo "==> Building site and generating PDF"
npm run pdf

echo "==> Done. Site: dist/  PDF: dist/cv-thiruvathukal.pdf"
echo "    Run 'npm run preview' to serve the built site locally."
