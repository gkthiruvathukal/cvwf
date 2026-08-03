#!/usr/bin/env python3
"""Converts sanitized BibLaTeX files (bibliography/*.bib) into a single
src/content/publications/all.json consumed by the Astro content collection.

Each bib file maps to one pubType. `author+an` (per-author role annotation,
e.g. "3=myself;7=graduate", 1-based position into the author list) is parsed
into a role per author - see ROLE_MAP and src/config/author-highlight.ts for
how those roles are rendered.
"""

import json
import os
import re

import bibtexparser
from bibtexparser.bparser import BibTexParser

BIB_TYPE_MAP = {
    "gkt-books.bib": "book",
    "gkt-inproceedings.bib": "inproceedings",
    "gkt-incollection.bib": "incollection",
    "gkt-journal.bib": "journal",
    "gkt-magazine.bib": "magazine",
    "gkt-techreport.bib": "techreport",
}

OUTPUT_PATH = "src/content/publications/all.json"

ROLE_MAP = {"myself": "self", "graduate": "graduate", "undergrad": "undergrad"}

BRACE_RE = re.compile(r"[{}]")
LATEX_ESCAPES = {
    r"\&": "&",
    r"\%": "%",
    r"\_": "_",
    r"\$": "$",
    r"\#": "#",
}


def clean_latex(text):
    """Best-effort strip of BibTeX brace-protection and common escapes.
    Does not attempt a full LaTeX-to-text conversion - abstracts in particular
    may retain some raw markup artifacts from the Zotero export."""
    if not text:
        return text
    for escaped, plain in LATEX_ESCAPES.items():
        text = text.replace(escaped, plain)
    return BRACE_RE.sub("", text).strip()


def parse_authors(raw_author):
    if not raw_author:
        return []
    names = []
    for part in raw_author.split(" and "):
        part = clean_latex(part.strip())
        if "," in part:
            last, first = [p.strip() for p in part.split(",", 1)]
            names.append(f"{first} {last}".strip())
        else:
            names.append(part)
    return names


def to_bool(value):
    return value.strip() in ("1", "true", "True") if value else None


def parse_author_roles(annotation):
    """Parses 'author+an' (e.g. '1=graduate;4=myself') into {1-based position: role}."""
    roles = {}
    if not annotation:
        return roles
    for part in annotation.split(";"):
        part = part.strip()
        if "=" not in part:
            continue
        pos, raw_role = part.split("=", 1)
        try:
            position = int(pos.strip())
        except ValueError:
            continue
        role = ROLE_MAP.get(raw_role.strip())
        if role:
            roles[position] = role
    return roles


def entry_to_record(entry, pub_type):
    cite_key = entry.get("ID")
    names = parse_authors(entry.get("author", ""))
    role_by_position = parse_author_roles(entry.get("author+an"))
    record = {
        "id": f"{pub_type}-{cite_key}",
        "citeKey": cite_key,
        "pubType": pub_type,
        "title": clean_latex(entry.get("title", "")),
        "authors": [
            {"name": name, "role": role_by_position.get(i + 1)}
            for i, name in enumerate(names)
        ],
        "date": entry.get("date", ""),
    }

    venue = (
        entry.get("journaltitle")
        or entry.get("booktitle")
        or entry.get("institution")
        or entry.get("eventtitle")
    )
    if venue:
        record["venue"] = clean_latex(venue)

    optional_str_fields = {
        "publisher": "publisher",
        "location": "location",
        "volume": "volume",
        "number": "number",
        "pages": "pages",
        "doi": "doi",
        "url": "url",
        "isbn": "isbn",
        "issn": "issn",
        "abstract": "abstract",
        "abbr": "abbr",
        "arxiv": "arxiv",
        "code": "code",
        "website": "website",
        "eprint": "eprint",
        "eprinttype": "eprinttype",
        "extra": "extra",
    }
    for bib_key, json_key in optional_str_fields.items():
        value = entry.get(bib_key)
        if value:
            record[json_key] = clean_latex(value) if json_key != "doi" else value

    keywords = entry.get("keywords")
    if keywords:
        record["keywords"] = [k.strip() for k in keywords.split(",") if k.strip()]

    for bib_key, json_key in (("selected", "selected"), ("bibtex_show", "bibtexShow")):
        value = to_bool(entry.get(bib_key))
        if value is not None:
            record[json_key] = value

    return record


def sort_key(record):
    match = re.match(r"\d{4}", record.get("date", ""))
    return match.group(0) if match else "0000"


def main():
    all_records = []
    for filename, pub_type in BIB_TYPE_MAP.items():
        path = f"bibliography/{filename}"
        with open(path, "r", encoding="utf-8") as bib_file:
            parser = BibTexParser(common_strings=True)
            parser.ignore_nonstandard_types = False
            db = bibtexparser.load(bib_file, parser)

        records = [entry_to_record(e, pub_type) for e in db.entries]
        all_records.extend(records)
        print(f"{path}: {len(records)} entries -> pubType={pub_type}")

    all_records.sort(key=sort_key, reverse=True)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as out_file:
        json.dump(all_records, out_file, indent=2, ensure_ascii=False)
        out_file.write("\n")

    print(f"Wrote {len(all_records)} total records to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
