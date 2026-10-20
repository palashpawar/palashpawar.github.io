#!/usr/bin/env python3
"""Save my GitHub contribution calendar and latest public repos to data/github.json.

The contribution calendar is only available through GitHub's GraphQL API, which
needs a token, so the home page can't fetch it from the browser. A daily
workflow runs this with its built-in GITHUB_TOKEN. Rewrites the file only when
the data changed.
"""
import json
import os
import pathlib
import sys
import urllib.request
from datetime import datetime, timezone

LOGIN = "palashpawar"
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "github.json"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
    repositories(first: 6, orderBy: {field: PUSHED_AT, direction: DESC},
                 privacy: PUBLIC, ownerAffiliations: OWNER, isFork: false) {
      nodes { name description url pushedAt stargazerCount primaryLanguage { name color } }
    }
  }
}
"""


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN is not set")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json", "User-Agent": LOGIN},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp)
    if body.get("errors"):
        sys.exit(f"GraphQL error: {body['errors']}")

    user = body["data"]["user"]
    cal = user["contributionsCollection"]["contributionCalendar"]
    data = {
        "total": cal["totalContributions"],
        # one [date, count] per day, oldest first
        "days": [[d["date"], d["contributionCount"]] for w in cal["weeks"] for d in w["contributionDays"]],
        "repos": [{
            "name": r["name"],
            "description": r["description"] or "",
            "url": r["url"],
            "pushedAt": r["pushedAt"],
            "stars": r["stargazerCount"],
            "language": (r["primaryLanguage"] or {}).get("name"),
            "color": (r["primaryLanguage"] or {}).get("color"),
        } for r in user["repositories"]["nodes"]],
    }

    old = json.loads(OUT.read_text()) if OUT.exists() else {}
    if {k: old.get(k) for k in data} == data:
        print("GitHub data unchanged.")
        return
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"), **data}) + "\n")
    print(f"Wrote {OUT.name}: {data['total']} contributions, {len(data['repos'])} repos")


if __name__ == "__main__":
    main()
