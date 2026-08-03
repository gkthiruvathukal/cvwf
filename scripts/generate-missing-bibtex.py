#!/usr/bin/env python3
"""One-off companion to find-missing-pubs.py: for a curated list of
confirmed-missing titles, re-fetches each publication directly from George's
Scholar author profile (unambiguous - tied to his specific citation entry,
not a fuzzy keyword search) and hand-builds a clean BibTeX entry from the
verified fields.

Note: scholarly's own `scholarly.bibtex()` helper doesn't work for
author-profile-sourced publications (it only populates real bibtex data for
publications found via `search_pubs()`, and that path was tested and found
unreliable here - `search_pubs()` returned a *different, wrong* paper as the
top result for a same-topic title). Hence the hand-built approach below,
using only fields scholarly.fill() verifiably returns for the exact
publication tied to George's profile.

Output is grouped by category into missing-<category>.bib at the repo root -
working files for manually reviewing and importing into Zotero, not part of
the site (gitignored, see .gitignore).
"""

import re
import time
import unicodedata

from scholarly import scholarly

PROFILE = "Ls7yS0IAAAAJ"
ARXIV_ID_RE = re.compile(r"arxiv[.org/abs:]*\s*(\d{4}\.\d{4,5})", re.IGNORECASE)

CATEGORIES = {
    "arxiv-papers": [
        "Beyond local code optimization: Multi-agent reasoning for software system optimization",
        "Operationalizing research software for supply chain security",
        "Can LLMs Write Correct TLA+ Specifications? Evaluating Natural-Language-to-TLA+ Generation",
        "An Empirical Investigation of Pre-Trained Deep Learning Model Reuse in the Scientific Process",
        "TLA-Bench: An Execution-Grounded Benchmark and Dataset for Natural-Language to TLA+ Specification Generation",
        "TLA-Prover: Verifiable TLA+ Specification Synthesis via Preference-Optimized Low-Rank Adaptation",
        "Now's the Time: Computer Science Must Evolve to Emphasize Software and Systems Engineering with Artificial Intelligence (AI)",
        "HeyFriend Helper: A Conversational AI Web-App for Resource Access Among Low-Income Chicago Residents",
        "Naming practices of pre-trained models in hugging face",
        "Impact of architectural modifications on deep learning adversarial robustness",
        "2023 low-power computer vision challenge (lpcvc) summary",
        "From attack to defense: Insights into deep learning security measures in black-box settings",
        "Analysis of failures and risks in deep learning model converters: A case study in the onnx ecosystem",
        "Exploring naming conventions (and defects) of pre-trained deep learning models in hugging face and other model hubs",
    ],
    "conference-papers": [
        "Interoperability in deep learning: A user survey and failure analysis of onnx model converters",
        "What do we know about Hugging Face? A systematic literature review and quantitative validation of qualitative claims",
        "An automated approach for improving the inference latency and energy efficiency of pretrained CNNs by removing irrelevant pixels with focused convolutions",
        "Wip: An engaging undergraduate intro to model checking in software engineering using TLA+",
    ],
    "journal-papers": [
        "Engaging more students in formal methods education: A practical approach using temporal logic of actions",
        "Crowdsourcing: A Roundtable Discussion",
        "Evaluation of Novel AI Architectures for Uncertainty Estimation",
        "Containerization on a Self-supervised active foveated approach to Computer Vision",
    ],
    "books": [],
}


def bibtex_authors(author_str):
    """'First M Last and First2 Last2' -> 'Last, First M and Last2, First2'."""
    parts = []
    for name in author_str.split(" and "):
        tokens = name.strip().split()
        if len(tokens) >= 2:
            parts.append(f"{tokens[-1]}, {' '.join(tokens[:-1])}")
        else:
            parts.append(name.strip())
    return " and ".join(parts)


def strip_diacritics(text):
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(c for c in normalized if not unicodedata.combining(c))


def citation_key(bib, year):
    first_author_last = strip_diacritics(
        bib["author"].split(" and ")[0].strip().split()[-1].lower()
    )
    words = re.split(r"\s+", bib["title"].lower())
    first_word = ""
    for word in words:
        first_word = re.sub(r"[^a-z]", "", word)
        if first_word:
            break
    return f"{first_author_last}_{first_word or 'untitled'}_{year}"


def escape(text):
    return text.replace("{", "").replace("}", "")


def build_arxiv_entry(bib, key):
    arxiv_id_match = ARXIV_ID_RE.search(bib.get("journal", "")) or ARXIV_ID_RE.search(
        bib.get("citation", "")
    )
    lines = [f"@misc{{{key},"]
    lines.append(f"      title={{{escape(bib['title'])}}},")
    lines.append(f"      author={{{bibtex_authors(bib['author'])}}},")
    lines.append(f"      year={{{bib['pub_year']}}},")
    if arxiv_id_match:
        lines.append(f"      eprint={{{arxiv_id_match.group(1)}}},")
        lines.append("      archivePrefix={arXiv},")
    else:
        lines.append(
            "      note={Scholar did not give a resolvable arXiv ID for this one - verify venue/url before importing},"
        )
    if bib.get("pub_url"):
        lines.append(f"      url={{{bib['pub_url']}}},")
    lines.append("}")
    return "\n".join(lines)


def build_inproceedings_entry(bib, key):
    booktitle = bib.get("conference") or bib.get("citation", "")
    booktitle = re.sub(r",?\s*\d{4}\s*$", "", booktitle).strip()  # drop trailing ", 2024"
    truncated = booktitle.endswith("…")

    lines = [f"@inproceedings{{{key},"]
    lines.append(f"      title={{{escape(bib['title'])}}},")
    lines.append(f"      author={{{bibtex_authors(bib['author'])}}},")
    lines.append(f"      booktitle={{{escape(booktitle)}}},")
    if bib.get("pages"):
        lines.append(f"      pages={{{bib['pages']}}},")
    lines.append(f"      year={{{bib['pub_year']}}},")
    if bib.get("publisher"):
        lines.append(f"      organization={{{bib['publisher']}}},")
    if bib.get("pub_url"):
        lines.append(f"      url={{{bib['pub_url']}}},")
    if truncated:
        lines.append(
            "      note={Scholar truncated this venue name - confirm the full name from the url before importing},"
        )
    lines.append("}")
    return "\n".join(lines)


def build_article_entry(bib, key):
    lines = [f"@article{{{key},"]
    lines.append(f"      title={{{escape(bib['title'])}}},")
    lines.append(f"      author={{{bibtex_authors(bib['author'])}}},")
    lines.append(f"      journal={{{escape(bib.get('journal', ''))}}},")
    if bib.get("volume"):
        lines.append(f"      volume={{{bib['volume']}}},")
    if bib.get("number"):
        lines.append(f"      number={{{bib['number']}}},")
    if bib.get("pages"):
        lines.append(f"      pages={{{bib['pages']}}},")
    lines.append(f"      year={{{bib['pub_year']}}},")
    if bib.get("publisher"):
        lines.append(f"      publisher={{{bib['publisher']}}},")
    if bib.get("pub_url"):
        lines.append(f"      url={{{bib['pub_url']}}},")
    lines.append("}")
    return "\n".join(lines)


BUILDERS = {
    "arxiv-papers": build_arxiv_entry,
    "conference-papers": build_inproceedings_entry,
    "journal-papers": build_article_entry,
}


def main():
    print(f"Fetching publication list for {PROFILE}...")
    author = scholarly.search_author_id(PROFILE)
    author = scholarly.fill(author, sections=["publications"])
    # Scholar itself sometimes has un-deduplicated entries sharing a title (seen
    # in practice: two "WIP..." entries differing only in title casing, one
    # with real citation data and one blank). Prefer the one with a citation.
    by_title = {}
    for p in author["publications"]:
        norm_title = p["bib"].get("title", "").strip().lower()
        existing = by_title.get(norm_title)
        if existing is None or (
            not existing["bib"].get("citation") and p["bib"].get("citation")
        ):
            by_title[norm_title] = p

    for category, titles in CATEGORIES.items():
        if not titles:
            with open(f"missing-{category}.bib", "w", encoding="utf-8") as f:
                f.write("% none found in this discovery run\n")
            print(f"missing-{category}.bib: 0 entries (wrote placeholder)")
            continue

        builder = BUILDERS[category]
        entries = []
        for title in titles:
            pub = by_title.get(title.strip().lower())
            if pub is None:
                print(f"  ! could not re-find on Scholar: {title}")
                continue
            try:
                filled = scholarly.fill(pub)
                bib = filled["bib"]
                if filled.get("pub_url"):
                    bib["pub_url"] = filled["pub_url"]
                if not bib.get("author"):
                    print(f"  ! no author field returned, skipping: {title}")
                    continue
                year = bib.get("pub_year", "n.d.")
                key = citation_key(bib, year)
                entries.append(builder(bib, key))
                print(f"  ok: {title}")
            except Exception as e:
                print(f"  ! failed ({e}): {title}")
            time.sleep(3)

        with open(f"missing-{category}.bib", "w", encoding="utf-8") as f:
            f.write("\n\n".join(entries))
            f.write("\n")
        print(f"missing-{category}.bib: {len(entries)}/{len(titles)} entries")


if __name__ == "__main__":
    main()
