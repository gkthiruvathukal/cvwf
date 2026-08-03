#!/usr/bin/env python3
"""Pulls citation/h-index/i10-index from a Google Scholar profile, writing
src/content/bibliometrics/bibliometrics.json (scholar record). Adapted from
../cv/tools/scholarly-metrics.py, including its dual-mode behavior:

- Locally (not GITHUB_ACTIONS): scrapes live via the `scholarly` package,
  then pushes the fresh values to GitHub repo variables via `gh variable
  set` so CI can pick them up.
- In CI (GITHUB_ACTIONS=true): reads those same repo variables from the
  environment instead of scraping. Google Scholar reliably blocks/CAPTCHAs
  requests from GitHub-hosted runner IPs, so live scraping in CI is not an
  option - this is the same workaround the LaTeX repo's Actions workflow
  already relies on (see .github/workflows/deploy.yml).

Merges with the github record already present in the output file rather
than overwriting it.
"""

import argparse
import json
import os
import subprocess
from datetime import datetime, timezone

OUTPUT_PATH = "src/content/bibliometrics/bibliometrics.json"

REQUIRED_VARS = [
    "CV_GSCHOLAR_ID",
    "CV_GSCHOLAR_CITATIONS",
    "CV_GSCHOLAR_H_INDEX",
    "CV_GSCHOLAR_I10_INDEX",
]


def load_existing():
    try:
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            records = json.load(f)
            return {r["id"]: r for r in records if "id" in r}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def scholar_url(scholar_id):
    return f"https://scholar.google.com/citations?hl=en&user={scholar_id}"


def fetch_from_github_vars():
    values = {var: os.environ.get(var) for var in REQUIRED_VARS}
    missing = [var for var, value in values.items() if not value]
    if missing:
        raise SystemExit(
            "Running in GitHub Actions but these repo variables aren't set: "
            + ", ".join(missing)
            + " (Settings -> Secrets and variables -> Actions -> Variables). "
            "Run this script locally once first to populate them."
        )
    return {
        "scholarProfileId": values["CV_GSCHOLAR_ID"],
        "citations": int(values["CV_GSCHOLAR_CITATIONS"]),
        "hIndex": int(values["CV_GSCHOLAR_H_INDEX"]),
        "i10Index": int(values["CV_GSCHOLAR_I10_INDEX"]),
    }


def fetch_live(profile_id):
    from scholarly import scholarly

    author = scholarly.search_author_id(profile_id)
    author = scholarly.fill(author, sections=["basics", "indices"])
    return {
        "scholarProfileId": author["scholar_id"],
        "citations": author["citedby"],
        "hIndex": author["hindex"],
        "i10Index": author["i10index"],
    }


def push_to_github_vars(metrics):
    updates = {
        "CV_GSCHOLAR_ID": metrics["scholarProfileId"],
        "CV_GSCHOLAR_CITATIONS": metrics["citations"],
        "CV_GSCHOLAR_H_INDEX": metrics["hIndex"],
        "CV_GSCHOLAR_I10_INDEX": metrics["i10Index"],
    }
    for key, value in updates.items():
        subprocess.run(["gh", "variable", "set", key, "--body", str(value)], check=True)
    print("Pushed fresh values to GitHub repo variables for CI to consume.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--profile",
        help="Google Scholar profile ID (required when running locally)",
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Skip pushing fresh values to GitHub repo variables (local runs only)",
    )
    args = parser.parse_args()

    in_ci = os.environ.get("GITHUB_ACTIONS") == "true"

    if in_ci:
        print("Running in GitHub Actions - using cached repo variables, not scraping live.")
        metrics = fetch_from_github_vars()
    else:
        if not args.profile:
            raise SystemExit("--profile is required when running locally")
        print("Running locally - scraping Google Scholar live.")
        metrics = fetch_live(args.profile)
        if not args.no_push:
            push_to_github_vars(metrics)

    records = load_existing()
    records["scholar"] = {
        "id": "scholar",
        "scholarProfileId": metrics["scholarProfileId"],
        "scholarUrl": scholar_url(metrics["scholarProfileId"]),
        "citations": metrics["citations"],
        "hIndex": metrics["hIndex"],
        "i10Index": metrics["i10Index"],
        "lastUpdated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(list(records.values()), f, indent=2)
        f.write("\n")

    print(
        f"citations={metrics['citations']} hIndex={metrics['hIndex']} i10Index={metrics['i10Index']}"
    )


if __name__ == "__main__":
    main()
