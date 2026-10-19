#!/usr/bin/env python3
"""Snapshot the ESPN data behind the Sports page into data/sports.json.

sports.html fetches ESPN live, but ESPN's feeds are undocumented and have already
dropped cross-site access once, so a scheduled job saves this snapshot as a fallback.
The team list is read from sports.html so there is only one list to maintain.

The file is rewritten only when the data changed, so the job doesn't commit
every hour.
"""
import json
import pathlib
import re
import sys
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "sports.html"
OUT = ROOT / "data" / "sports.json"
API = "https://site.api.espn.com/apis/site/v2/sports"
UPCOMING_KEPT = 3  # next few fixtures, so the snapshot still has a "next game" a few days later


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def teams_from_page():
    """[(path, id, soccer)] from the `teams` array in sports.html."""
    rows = re.findall(r'\["([a-z\-/.0-9]+)", (\d+), "[^"]*", (true|false)', PAGE.read_text())
    if not rows:
        sys.exit("Couldn't find the teams list in sports.html")
    return [(path, int(team_id), soccer == "true") for path, team_id, soccer in rows]


def schedule_urls(path, team_id, soccer):
    # same feeds the page uses: soccer needs results + fixtures across all competitions
    base = f"{API}/{'soccer/all' if soccer else path}/teams/{team_id}/schedule"
    return [base, base + "?fixture=true"] if soccer else [base]


def slim_logos(logos):
    """Just the standard and dark-background logo URLs (all the page uses)."""
    keep = []
    for want in ("default", "dark"):
        hit = next((l for l in logos if want in l.get("rel", []) and "scoreboard" not in l.get("rel", [])), None)
        if hit:
            keep.append({"rel": ["full", want], "href": hit["href"]})
    return keep


def slim_event(ev):
    comp = ev["competitions"][0]
    status = comp["status"]["type"]
    return {
        "id": ev["id"],
        "date": ev["date"],
        "timeValid": ev.get("timeValid", True),
        "league": {k: (ev.get("league") or {}).get(k) for k in ("name", "abbreviation")},
        "competitions": [{
            "neutralSite": comp.get("neutralSite", False),
            "status": {"type": {"completed": status.get("completed", False), "state": status.get("state")}},
            "competitors": [{
                "homeAway": c.get("homeAway"),
                "winner": c.get("winner"),
                "score": (c["score"].get("displayValue") if isinstance(c.get("score"), dict) else c.get("score")),
                "shootoutScore": c.get("shootoutScore"),
                "team": {
                    "id": c["team"]["id"],
                    "displayName": c["team"].get("displayName"),
                    "shortDisplayName": c["team"].get("shortDisplayName"),
                    "logos": slim_logos(c["team"].get("logos", [])),
                },
            } for c in comp["competitors"]],
        }],
    }


def snapshot_team(path, team_id, soccer):
    feeds = [get(u) for u in schedule_urls(path, team_id, soccer)]
    events = {ev["id"]: ev for f in feeds for ev in f.get("events", [])}.values()
    done = sorted((e for e in events if e["competitions"][0]["status"]["type"].get("completed")), key=lambda e: e["date"])
    todo = sorted((e for e in events if not e["competitions"][0]["status"]["type"].get("completed")), key=lambda e: e["date"])
    team = next((f["team"] for f in feeds if f.get("team", {}).get("standingSummary")), feeds[0].get("team", {}))
    return {
        "team": {k: team.get(k) for k in ("displayName", "logo", "recordSummary", "standingSummary", "clubhouse")},
        "events": [slim_event(e) for e in done[-1:] + todo[:UPCOMING_KEPT]],
    }


def ap_ranks():
    data = get(f"{API}/football/college-football/rankings")
    polls = data.get("rankings", [])
    poll = next((p for p in polls if "AP" in p.get("name", "")), polls[0] if polls else None)
    return {str(r["team"]["id"]): r["current"] for r in (poll or {}).get("ranks", [])}


def main():
    old = json.loads(OUT.read_text()) if OUT.exists() else {}
    teams, failed = {}, []
    for path, team_id, soccer in teams_from_page():
        key = f"{path}|{team_id}"
        try:
            teams[key] = snapshot_team(path, team_id, soccer)
        except Exception as e:  # keep the last good copy for this team
            failed.append(f"{key}: {e}")
            if key in old.get("teams", {}):
                teams[key] = old["teams"][key]
    try:
        ap = ap_ranks()
    except Exception as e:
        failed.append(f"rankings: {e}")
        ap = old.get("ap", {})

    for f in failed:
        print("could not refresh", f)
    if failed and len(failed) > len(teams):
        sys.exit("ESPN requests failed; keeping the existing snapshot")

    data = {"ap": ap, "teams": teams}
    if old and {"ap": old.get("ap"), "teams": old.get("teams")} == data:
        print("Sports data unchanged.")
        return
    data = {"updated": datetime.now(timezone.utc).isoformat(timespec="seconds"), **data}
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    print(f"Wrote {OUT.relative_to(ROOT)} ({len(teams)} teams)")


if __name__ == "__main__":
    main()
