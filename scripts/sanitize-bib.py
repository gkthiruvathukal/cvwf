#!/usr/bin/env python3
"""Promotes Zotero's tex.* Extra-field annotations (e.g. author+an, arxiv, code)
to top-level BibLaTeX fields. Adapted from ../cv/tools/sanitize-zotero-bib.py;
batches over every bibliography/*-raw.bib produced by fetch-zotero.sh.
"""

import glob
import os
import re

import bibtexparser
from bibtexparser.bparser import BibTexParser

BIB_DIR = "bibliography"


def expand_tex_fields(entry):
    if "type" in entry:
        del entry["type"]

    if "note" in entry:
        note_entry = entry.pop("note")
        new_fields = {}
        new_note_lines = []

        for line in note_entry.splitlines():
            tex_match = re.match(r"tex\.([\w\+\_\\]+):\s*(.*)", line)
            if tex_match:
                key, value = tex_match.groups()
                key = key.replace("\\_", "_")
                new_fields[key] = value.strip()
            else:
                new_note_lines.append(line)

        entry.update(new_fields)
        if new_note_lines:
            entry["extra"] = "\n".join(new_note_lines)

    return entry


def sanitize(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as bib_file:
        parser = BibTexParser(common_strings=True)
        parser.ignore_nonstandard_types = False
        bib_database = bibtexparser.load(bib_file, parser)

    for entry in bib_database.entries:
        expand_tex_fields(entry)

    with open(output_path, "w", encoding="utf-8") as bib_file:
        bibtexparser.dump(bib_database, bib_file)

    print(f"{input_path} -> {output_path} ({len(bib_database.entries)} entries)")


if __name__ == "__main__":
    for raw_path in sorted(glob.glob(os.path.join(BIB_DIR, "*-raw.bib"))):
        clean_path = raw_path.replace("-raw.bib", ".bib")
        sanitize(raw_path, clean_path)
