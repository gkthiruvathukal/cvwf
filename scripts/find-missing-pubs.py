#!/usr/bin/env python3
"""One-off discovery tool (not part of the build pipeline): compares George's
full Google Scholar publication list against what's already in
src/content/publications/all.json (derived from Zotero), and reports Scholar
entries with no reasonable title match in our corpus - candidates for adding
to Zotero. Filters to a recent-years window by default since Scholar's full
list includes decades of auto-indexed items that were never meant to be
curated onto the CV.
"""

import argparse
import difflib
import json
import re

from scholarly import scholarly

CORPUS_PATH = "src/content/publications/all.json"

ARXIV_ID_RE = re.compile(r"arxiv[.org/abs:]*\s*(\d{4}\.\d{4,5})", re.IGNORECASE)

# Scholar's per-author publication list includes service credits, editorial
# notices, and outright merge errors alongside real publications. These are
# not publications and would otherwise show up as false "missing" candidates.
NOISE_PATTERNS = re.compile(
    r"program committee|external reviewers?|editorial board|associate editors?"
    r"|workshop organi[sz]ation|workshop chairs?|cover image|session \d|"
    r"name and affiliation|^\(no title\)|proceeding|^workshop on |^eduhpc \d"
    r"|^bdcloud \d|^sbac-pad \d|^se4science \d|^icws \d|special interest group"
    r"|round\s?table discussion$",
    re.IGNORECASE,
)


def normalize(title):
    title = title.lower()
    title = re.sub(r"[^a-z0-9]+", " ", title)
    return re.sub(r"\s+", " ", title).strip()


def load_existing():
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        records = json.load(f)
    titles = {normalize(r["title"]) for r in records}
    arxiv_ids = set()
    for r in records:
        for field in ("number", "eprint", "arxiv", "url", "code", "website"):
            val = r.get(field) or ""
            m = ARXIV_ID_RE.search(val)
            if m:
                arxiv_ids.add(m.group(1))
    return titles, arxiv_ids


def best_match_ratio(title, existing_norm_titles):
    norm = normalize(title)
    best = 0.0
    for existing in existing_norm_titles:
        ratio = difflib.SequenceMatcher(None, norm, existing).ratio()
        if ratio > best:
            best = ratio
        if best > 0.97:
            break
    return best


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, help="Google Scholar profile ID")
    parser.add_argument(
        "--since-year", type=int, default=2023, help="Only report items from this year onward"
    )
    parser.add_argument(
        "--threshold", type=float, default=0.85, help="Title similarity ratio below which a Scholar entry counts as missing"
    )
    args = parser.parse_args()

    print(f"Fetching full publication list for {args.profile}...")
    author = scholarly.search_author_id(args.profile)
    author = scholarly.fill(author, sections=["publications"])
    pubs = author["publications"]
    print(f"{len(pubs)} total publications on Scholar")

    existing_titles, existing_arxiv_ids = load_existing()
    print(f"{len(existing_titles)} titles, {len(existing_arxiv_ids)} arXiv IDs already in {CORPUS_PATH}")

    candidates = []
    skipped_noise = 0
    skipped_arxiv_dupe = 0
    for pub in pubs:
        bib = pub.get("bib", {})
        title = bib.get("title", "")
        citation = bib.get("citation", "")
        year_str = bib.get("pub_year", "")
        try:
            year = int(year_str)
        except (ValueError, TypeError):
            year = None
        if year is not None and year < args.since_year:
            continue
        if NOISE_PATTERNS.search(title) or NOISE_PATTERNS.search(citation):
            skipped_noise += 1
            continue
        arxiv_match = ARXIV_ID_RE.search(citation)
        if arxiv_match and arxiv_match.group(1) in existing_arxiv_ids:
            skipped_arxiv_dupe += 1
            continue
        ratio = best_match_ratio(title, existing_titles)
        if ratio < args.threshold:
            candidates.append((year or 0, title, citation, ratio, pub))

    candidates.sort(key=lambda c: c[0], reverse=True)

    print(f"(skipped {skipped_noise} service/editorial noise entries, {skipped_arxiv_dupe} already-covered arXiv IDs under a different title)")
    print(f"\n{len(candidates)} candidates since {args.since_year} with no good match (threshold {args.threshold}):\n")
    for year, title, citation, ratio, _ in candidates:
        print(f"[{year}] (best match {ratio:.2f}) {title}")
        print(f"    {citation}")

    return candidates


if __name__ == "__main__":
    main()
