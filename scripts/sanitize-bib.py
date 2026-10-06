#!/usr/bin/env python3
"""Promotes Zotero's tex.* Extra-field annotations (e.g. author+an, arxiv, code)
to top-level BibLaTeX fields. Adapted from ../cv/tools/sanitize-zotero-bib.py;
batches over every bibliography/*-raw.bib produced by fetch-zotero.sh.
"""

import glob
import os
import re

import bibtexparser
from bibtexparser.model import Field

BIB_DIR = "bibliography"


def expand_tex_fields(entry):
    entry.pop("type", None)

    note_entry = entry.pop("note", None)
    if note_entry is not None:
        new_fields = {}
        new_note_lines = []

        for line in note_entry.value.splitlines():
            tex_match = re.match(r"tex\.([\w\+\_\\]+):\s*(.*)", line)
            if tex_match:
                key, value = tex_match.groups()
                key = key.replace("\\_", "_")
                new_fields[key] = value.strip()
            else:
                new_note_lines.append(line)

        for key, value in new_fields.items():
            entry.set_field(Field(key, value))
        if new_note_lines:
            entry.set_field(Field("extra", "\n".join(new_note_lines)))

    return entry


def sanitize(input_path, output_path):
    library = bibtexparser.parse_file(input_path)
    if library.failed_blocks:
        raise SystemExit(f"{input_path}: {len(library.failed_blocks)} block(s) failed to parse")

    for entry in library.entries:
        expand_tex_fields(entry)

    bibtexparser.write_file(output_path, library)

    print(f"{input_path} -> {output_path} ({len(library.entries)} entries)")


if __name__ == "__main__":
    for raw_path in sorted(glob.glob(os.path.join(BIB_DIR, "*-raw.bib"))):
        clean_path = raw_path.replace("-raw.bib", ".bib")
        sanitize(raw_path, clean_path)
