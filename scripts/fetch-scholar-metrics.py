#!/usr/bin/env python3
"""Pulls citation/h-index/i10-index from a Google Scholar profile via the
`scholarly` package, writing src/content/bibliometrics/bibliometrics.json
(scholar record). Adapted from ../cv/tools/scholarly-metrics.py; merges with
the github record already present in that file rather than overwriting it.
"""

import argparse
import json
from datetime import datetime, timezone

from scholarly import scholarly

OUTPUT_PATH = "src/content/bibliometrics/bibliometrics.json"


def load_existing():
    try:
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            records = json.load(f)
            return {r["id"]: r for r in records if "id" in r}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True, help="Google Scholar profile ID")
    args = parser.parse_args()

    author = scholarly.search_author_id(args.profile)
    author = scholarly.fill(author, sections=["basics", "indices"])

    records = load_existing()
    records["scholar"] = {
        "id": "scholar",
        "scholarProfileId": author["scholar_id"],
        "scholarUrl": f"https://scholar.google.com/citations?hl=en&user={author['scholar_id']}",
        "citations": author["citedby"],
        "hIndex": author["hindex"],
        "i10Index": author["i10index"],
        "lastUpdated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(list(records.values()), f, indent=2)
        f.write("\n")

    print(
        f"citations={author['citedby']} hIndex={author['hindex']} i10Index={author['i10index']}"
    )


if __name__ == "__main__":
    main()
