"""Builds stats.svg from live GitHub data, in the same style as the other cards.

Runs daily in GitHub Actions (needs GITHUB_TOKEN). Locally: `python3 stats.py --sample`.
"""
import datetime as dt
import json
import os
import sys
import urllib.request

import build_svgs as T  # shared theme: fonts, code background, 3D helpers

USER = os.environ.get("GH_USER", "KanungoShubham")

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    pullRequests { totalCount }
    issues { totalCount }
    repositories(ownerAffiliations: OWNER, privacy: PUBLIC, first: 100, isFork: false) {
      totalCount
      nodes {
        stargazerCount
        forkCount
        languages(first: 8, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } }
      }
    }
    contributionsCollection {
      totalCommitContributions
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount date } }
      }
    }
  }
}"""


def fetch():
    token = os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    data = json.load(urllib.request.urlopen(req))
    if "errors" in data:
        raise SystemExit(data["errors"])
    u = data["data"]["user"]
    repos = u["repositories"]["nodes"]
    langs = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]
            langs.setdefault(n, [0, e["node"]["color"] or "#8b8f9c"])[0] += e["size"]
    cc = u["contributionsCollection"]
    days = [d for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
    return {
        "commits": cc["totalCommitContributions"] + cc["restrictedContributionsCount"],
        "contribs": cc["contributionCalendar"]["totalContributions"],
        "repos": u["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos),
        "forks": sum(r["forkCount"] for r in repos),
        "prs": u["pullRequests"]["totalCount"],
        "issues": u["issues"]["totalCount"],
        "followers": u["followers"]["totalCount"],
        "days": [d["contributionCount"] for d in days],
        "langs": sorted(([n, s, c] for n, (s, c) in langs.items()), key=lambda x: -x[1])[:6],
    }


def sample():
    import random
    random.seed(3)
    return {"commits": 642, "contribs": 731, "repos": 38, "stars": 24, "forks": 9, "prs": 57, "issues": 12,
            "followers": 41, "days": [random.choice([0, 0, 1, 2, 3, 5, 8]) for _ in range(365)],
            "langs": [["TypeScript", 52, "#3178c6"], ["JavaScript", 21, "#f1e05a"], ["PHP", 11, "#4F5D95"],
                      ["CSS", 8, "#663399"], ["HTML", 5, "#e34c26"], ["Python", 3, "#3572A5"]]}


def streaks(days):
    cur = 0
    for c in reversed(days[:-1] if days and days[-1] == 0 else days):
        if c == 0:
            break
        cur += 1
    best = run = 0
    for c in days:
        run = run + 1 if c else 0
        best = max(best, run)
    return cur, best


def fmt(n):
    return f"{n / 1000:.1f}k" if n >= 1000 else str(n)


def build(s):
    cur, best = streaks(s["days"])
    year = dt.date.today().year
    tiles = [
        ("COMMITS · LAST 12 MO", fmt(s["commits"]), "amber", f'{fmt(s["contribs"])} total contributions'),
        ("PUBLIC REPOS", fmt(s["repos"]), "teal", f'★ {fmt(s["stars"])} stars · ⑂ {fmt(s["forks"])} forks'),
        ("PULL REQUESTS", fmt(s["prs"]), "violet", f'{fmt(s["issues"])} issues opened'),
        ("CURRENT STREAK", f"{cur}d", "coral", f"best streak {best} days"),
    ]
    body = f'<text x="48" y="58" class="muted mono" font-size="13">// github.stats({year}) — refreshed daily</text>'
    body += f'<text x="1152" y="58" text-anchor="end" class="muted mono" font-size="13">@{USER} · {fmt(s["followers"])} followers</text>'
    for i, (lab, val, col, sub) in enumerate(tiles):
        x = 24 + i * 194
        body += f'''<g class="fade" style="animation-delay:{.15 * i:.2f}s">
<rect class="panel" x="{x}" y="78" width="182" height="150" rx="16"/>
<text x="{x + 20}" y="106" class="muted mono" font-size="11">{lab}</text>
<text x="{x + 20}" y="170" class="{col}" font-family="{T.SANS}" font-size="50" font-weight="700">{val}</text>
<text x="{x + 20}" y="204" class="muted" font-size="12">{T.esc(sub)}</text></g>'''

    # last 26 weeks as a 3D-ish isometric bar skyline
    days = s["days"][-182:]
    weeks = [sum(days[i:i + 7]) for i in range(0, len(days), 7)]
    mx = max(weeks + [1])
    body += '<rect class="panel" x="24" y="240" width="764" height="160" rx="16"/>'
    body += '<text x="44" y="266" class="muted mono" font-size="11">WEEKLY ACTIVITY · LAST 26 WEEKS</text>'
    for i, wv in enumerate(weeks):
        hgt = 6 + 92 * wv / mx
        x, base = 52 + i * 27.5, 384
        top = base - hgt
        a = .35 + .65 * wv / mx
        body += f'''<g class="rise" style="animation-delay:{.03 * i:.2f}s" opacity="{a:.2f}">
<path d="M{x} {base} V{top} L{x + 8} {top - 6} H{x + 26} V{base - 6} L{x + 18} {base} Z" fill="#a99bff" fill-opacity=".35"/>
<rect x="{x}" y="{top}" width="18" height="{hgt}" fill="url(#barg)"/>
<path d="M{x} {top} L{x + 8} {top - 6} H{x + 26} L{x + 18} {top} Z" fill="#ffe0a3"/></g>'''

    # languages
    total = sum(l[1] for l in s["langs"]) or 1
    body += '<rect class="panel" x="800" y="78" width="376" height="322" rx="16"/>'
    body += '<text x="824" y="106" class="muted mono" font-size="11">TOP LANGUAGES · BY CODE SIZE</text>'
    x = 824
    for n, sz, c in s["langs"]:
        w = 328 * sz / total
        body += f'<rect class="grow" x="{x:.1f}" y="124" width="{max(w - 2, 1):.1f}" height="12" fill="{c}"/>'
        x += w
    for i, (n, sz, c) in enumerate(s["langs"]):
        y = 172 + i * 36
        pct = 100 * sz / total
        body += f'''<g class="fade" style="animation-delay:{.4 + .1 * i:.2f}s"><circle cx="832" cy="{y - 5}" r="6" fill="{c}"/>
<text x="848" y="{y}" class="ink" font-size="15" font-weight="700">{T.esc(n)}</text>
<text x="1152" y="{y}" text-anchor="end" class="muted mono" font-size="13">{pct:.1f}%</text>
<rect x="848" y="{y + 8}" width="304" height="4" rx="2" fill="#262a35"/>
<rect class="grow" x="848" y="{y + 8}" width="{304 * pct / 100:.1f}" height="4" rx="2" fill="{c}"/></g>'''

    css = """
  .rise { transform-box: fill-box; transform-origin: bottom; animation: rise 1s cubic-bezier(.2,.8,.2,1) both; }
  @keyframes rise { from { transform: scaleY(0); } to { transform: scaleY(1); } }
  .grow { transform-box: fill-box; transform-origin: left; animation: grow 1.4s ease-out both .3s; }
  @keyframes grow { from { transform: scaleX(0); } to { transform: scaleX(1); } }
"""
    extra_defs = '<linearGradient id="barg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f5b544"/><stop offset="1" stop-color="#ff7a6b"/></linearGradient>'
    out = T.svg(1200, 424, extra_defs + body, css, f"GitHub stats for {USER}")
    (T.ROOT / "stats.svg").write_text(out, encoding="utf-8")
    print("wrote stats.svg")


if __name__ == "__main__":
    build(sample() if "--sample" in sys.argv else fetch())
