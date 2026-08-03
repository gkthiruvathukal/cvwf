#!/usr/bin/env python3
"""Scrapes GitHub's public contribution-graph HTML per year and sums commit
counts, writing src/content/bibliometrics/bibliometrics.json (github record).
Adapted from ../cv/tools/github-commits.py; merges with the scholar record
already present in that file rather than overwriting it.
"""

import argparse
import json
import re
from datetime import date

import requests
from bs4 import BeautifulSoup

OUTPUT_PATH = "src/content/bibliometrics/bibliometrics.json"


def get_argparse():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", required=True, help="GitHub username")
    parser.add_argument("--first-year", type=int, required=True)
    parser.add_argument(
        "--last-year", type=int, default=date.today().year, required=False
    )
    return parser


def fetch_contributions(username, first_year, last_year):
    total = 0
    for year in range(first_year, last_year + 1):
        end_date = f"{year}-12-31"
        url = f"https://github.com/users/{username}/contributions?to={end_date}"
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, features="html.parser")
        for heading in soup.find_all("h2", class_="f4"):
            match = re.search(r"[\d,]+", heading.string or "")
            if match:
                total += int(match.group().replace(",", ""))
    return total


def load_existing():
    try:
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            records = json.load(f)
            return {r["id"]: r for r in records if "id" in r}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def main():
    args = get_argparse().parse_args()
    contributions = fetch_contributions(args.username, args.first_year, args.last_year)

    records = load_existing()
    records["github"] = {
        "id": "github",
        "username": args.username,
        "contributions": contributions,
        "startYear": args.first_year,
        "endYear": args.last_year,
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(list(records.values()), f, indent=2)
        f.write("\n")

    print(f"{args.username}: {contributions} contributions ({args.first_year}-{args.last_year})")


if __name__ == "__main__":
    main()
