#!/usr/bin/env python3
"""Fetch the latest men's FIFA World Ranking for the national teams on the Sports page
and write it to data/fifa-rankings.json.

FIFA's ranking API doesn't allow cross-origin requests, so the page can't call it from
the browser; run this script (by hand or from a scheduled job) to refresh the file.
"""
import json
import pathlib
import urllib.request

COUNTRIES = ["USA", "FRA", "IND"]  # FIFA country codes
URL = "https://inside.fifa.com/api/rankings/by-country?gender=1&countryCode={}&footballType=football&locale=en"
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "fifa-rankings.json"


def latest(code):
    req = urllib.request.Request(URL.format(code), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        history = json.load(resp)["rankings"]  # one entry per ranking release
    entry = max(history, key=lambda e: e["PubDate"])
    return {
        "rank": entry["Rank"],
        "previousRank": entry.get("PrevRank"),
        "points": entry.get("TotalPoints"),
        "published": entry["PubDate"],
    }


def main():
    teams = {code: latest(code) for code in COUNTRIES}
    data = {"published": max(t["published"] for t in teams.values()), "teams": teams}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2) + "\n")
    for code, t in teams.items():
        print(f"{code}: #{t['rank']} (prev #{t['previousRank']}), {t['points']} pts")


if __name__ == "__main__":
    main()
