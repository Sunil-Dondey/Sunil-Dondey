#!/usr/bin/env python3
"""
Collect everything the profile cards need and write data/stats.json.

  * daily contributions from the public calendar GitHub serves for the profile page
    (falls back to the GraphQL API when GITHUB_TOKEN is set and the page fails)
  * repo counts, account age and the most recently pushed projects (REST API)

Standard library only, so the workflow needs no pip install.
Run by .github/workflows/refresh-profile.yml every day.
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.request
from html import unescape

USER = os.environ.get("PROFILE_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "Sunil-Dondey"
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "data", "stats.json")
UA = {"User-Agent": "profile-cards-bot/1.0"}


def get(url, headers=None, data=None):
    req = urllib.request.Request(url, data=data, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def api_headers():
    h = {"Accept": "application/vnd.github+json"}
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    return h


# ---- contributions ---------------------------------------------------------------
def days_from_page():
    html = get(f"https://github.com/users/{USER}/contributions")
    tips = {
        m.group(1): unescape(m.group(2)).strip()
        for m in re.finditer(r'<tool-tip[^>]*\bfor="([^"]+)"[^>]*>([^<]*)</tool-tip>', html)
    }
    days = []
    for td in re.findall(r"<td\b[^>]*ContributionCalendar-day[^>]*>", html):
        attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', td))
        if "data-date" not in attrs:
            continue
        m = re.match(r"(\d[\d,]*)\s+contribution", tips.get(attrs.get("id", ""), ""))
        days.append({
            "date": attrs["data-date"],
            "count": int(m.group(1).replace(",", "")) if m else 0,
            "level": int(attrs.get("data-level") or 0),
        })
    if not days:
        raise RuntimeError("no calendar cells found, the page markup may have changed")
    return days


LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3, "FOURTH_QUARTILE": 4}


def days_from_graphql():
    if not TOKEN:
        raise RuntimeError("no GITHUB_TOKEN for the GraphQL fallback")
    q = ("query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{"
         "weeks{contributionDays{date contributionCount contributionLevel}}}}}}")
    body = json.dumps({"query": q, "variables": {"u": USER}}).encode()
    res = json.loads(get("https://api.github.com/graphql", api_headers(), body))
    weeks = res["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    return [
        {"date": d["date"], "count": d["contributionCount"], "level": LEVELS.get(d["contributionLevel"], 0)}
        for w in weeks for d in w["contributionDays"]
    ]


def fetch_days():
    try:
        days = days_from_page()
    except Exception as e:
        print(f"calendar page failed ({e}), trying GraphQL", file=sys.stderr)
        days = days_from_graphql()
    return sorted(days, key=lambda d: d["date"])


def streaks(days):
    end = len(days) - 1
    if days[end]["count"] == 0:
        end -= 1  # today isn't over yet, so it can't break the streak
    cur = 0
    while end - cur >= 0 and days[end - cur]["count"] > 0:
        cur += 1
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    return cur, longest


# ---- repos -------------------------------------------------------------------------
def fetch_repos():
    url = f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&sort=pushed"
    repos = json.loads(get(url, api_headers()))
    return [r for r in repos if r["name"].lower() != USER.lower()]  # skip this profile repo


def main():
    days = fetch_days()
    cur, longest = streaks(days)
    best = max(days, key=lambda d: d["count"])
    monthly = {}
    for d in days:
        monthly[d["date"][:7]] = monthly.get(d["date"][:7], 0) + d["count"]

    user = json.loads(get(f"https://api.github.com/users/{USER}", api_headers()))
    repos = fetch_repos()
    own = [r for r in repos if not r["fork"]]
    created = dt.date.fromisoformat(user["created_at"][:10])
    today = dt.date.today()
    years = today.year - created.year - ((today.month, today.day) < (created.month, created.day))

    data = {
        "user": user["login"],
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": sum(d["count"] for d in days),
        "active_days": sum(1 for d in days if d["count"] > 0),
        "current_streak": cur,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": [{"month": k, "total": v} for k, v in sorted(monthly.items())],
        "projects": len(own),
        "public_repos": user["public_repos"],
        "years_on_github": years,
        "member_since": created.year,
        "recent": [{"name": r["name"], "language": r["language"]} for r in own if r["language"]][:3],
        "repos": {
            r["name"]: {"stars": r["stargazers_count"], "language": r["language"], "homepage": r["homepage"]}
            for r in repos
        },
        "days": days,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1)
    print(f"{USER}: {data['total']} contributions, streak {cur} (longest {longest}), "
          f"{data['projects']} projects, best day {best['count']}")


if __name__ == "__main__":
    main()
