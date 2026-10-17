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
        "dates": [d["date"] for d in days],
        "langs": sorted(([n, s, c] for n, (s, c) in langs.items()), key=lambda x: -x[1])[:6],
    }


def sample():
    import random
    random.seed(3)
    end = dt.date.today()
    dates = [(end - dt.timedelta(days=364 - i)).isoformat() for i in range(365)]
    return {"dates": dates, "commits": 642, "contribs": 731, "repos": 38, "stars": 24, "forks": 9, "prs": 57, "issues": 12,
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


MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def _smooth(pts):
    """Smooth cubic path through points (Catmull-Rom → Bezier)."""
    d = f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    for i in range(len(pts) - 1):
        p0, p1, p2 = pts[max(i - 1, 0)], pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.1f} {c1[1]:.1f} {c2[0]:.1f} {c2[1]:.1f} {p2[0]:.1f} {p2[1]:.1f}"
    return d


def build_pulse(s):
    """Original contribution visual: 12 months as glowing 3D ridgelines."""
    pairs = list(zip(s["dates"], s["days"]))
    by_month = {}
    for d, c in pairs:
        y, m, day = map(int, d.split("-"))
        by_month.setdefault((y, m), {})[day] = c
    months = sorted(by_month)[-12:]
    mx = max(s["days"] + [1])
    peak_d, peak_c = max(pairs, key=lambda x: x[1]) if pairs else ("", 0)

    x0, x1, top, gap, amp = 128, 760, 138, 24, 56
    body = '<text x="48" y="58" class="muted mono" font-size="13">// pulse.log — 12 months of shipping, one ridge per month</text>'
    rows = ""
    for i, key in enumerate(months):
        base = top + i * gap
        vals = by_month[key]
        dim = 31
        pts = [(x0 - 18, base)]
        sm = {d: (vals.get(d - 1, 0) * .5 + vals.get(d, 0) + vals.get(d + 1, 0) * .5) / 2 for d in range(1, dim + 1)}
        smx = max([(vals.get(d, 0) * 1.0) for d in range(1, dim + 1)] + [0])
        for day in range(1, dim + 1):
            v = max(sm[day], vals.get(day, 0) * .85)
            h = amp * (v / mx) ** .6
            pts.append((x0 + (day - 1) * (x1 - x0) / (dim - 1), base - h))
        pts.append((x1 + 18, base))
        line = _smooth(pts)
        fill = line + f" L{x1 + 18} {base + 3} L{x0 - 18} {base + 3} Z"
        hot = i == len(months) - 1
        col = "url(#ridge)" if not hot else "url(#ridgehot)"
        rows += f"""<g class="ridge" style="animation-delay:{.12 * i:.2f}s">
<path d="{fill}" fill="#0e0f13"/>
<path d="{fill}" fill="url(#ridgefill)" opacity="{.25 + .05 * i:.2f}"/>
<path class="trace" d="{line}" fill="none" stroke="{col}" stroke-width="{2.4 if hot else 1.5}" stroke-linejoin="round" style="animation-delay:{.12 * i:.2f}s"/>
<text x="{x0 - 30}" y="{base + 4}" text-anchor="end" class="mono" font-size="11" fill="{'#f5b544' if hot else '#5c6170'}">{MONTHS[key[1] - 1]} {str(key[0])[2:]}</text></g>"""
        if hot:
            rows += (f'<circle r="4.5" fill="#ffe0a3"><animateMotion dur="7s" repeatCount="indefinite" path="{line}"/></circle>'
                     f'<circle r="11" fill="#f5b544" opacity=".25"><animateMotion dur="7s" repeatCount="indefinite" path="{line}"/></circle>')
        if peak_c and peak_d.startswith(f"{key[0]}-{key[1]:02d}"):
            day = int(peak_d[-2:])
            px = x0 + (day - 1) * (x1 - x0) / 30
            py = base - amp * (peak_c * .85 / mx) ** .6
            rows += f"""<g class="fade" style="animation-delay:2s"><line x1="{px:.1f}" y1="{py:.1f}" x2="{px:.1f}" y2="{py - 26:.1f}" stroke="#4fd1c5" stroke-dasharray="2 3"/>
<circle class="pulse" cx="{px:.1f}" cy="{py:.1f}" r="4" fill="#4fd1c5"/>
<rect x="{px - 62:.1f}" y="{py - 50:.1f}" width="124" height="24" rx="12" fill="#15171d" stroke="#4fd1c5"/>
<text x="{px:.1f}" y="{py - 34:.1f}" text-anchor="middle" class="teal mono" font-size="11">peak · {peak_c} on {MONTHS[key[1] - 1]} {day}</text></g>"""
    body += rows

    # side panel
    days = s["days"]
    active = sum(1 for c in days if c)
    cur, best = streaks(days)
    month_tot = {k: sum(v.values()) for k, v in by_month.items() if k in months}
    bm = max(month_tot, key=month_tot.get) if month_tot else (0, 1)
    wk = [0] * 7
    for d, c in pairs:
        wk[dt.date.fromisoformat(d).weekday()] += c
    wmx = max(wk + [1])
    body += '<rect class="panel" x="812" y="78" width="364" height="338" rx="16"/>'
    facts = [("contributions", fmt(s["contribs"]), "amber"), ("active days", str(active), "teal"),
             ("longest streak", f"{best}d", "coral"), ("best month", f"{MONTHS[bm[1] - 1]} · {month_tot.get(bm, 0)}", "violet")]
    for i, (lab, val, col) in enumerate(facts):
        x, y = 836 + (i % 2) * 172, 128 + (i // 2) * 76
        body += f"""<g class="fade" style="animation-delay:{.6 + .12 * i:.2f}s"><text x="{x}" y="{y}" class="muted mono" font-size="11">{lab.upper()}</text>
<text x="{x}" y="{y + 36}" class="{col}" font-family="{T.SANS}" font-size="32" font-weight="700">{T.esc(val)}</text></g>"""
    body += '<text x="836" y="282" class="muted mono" font-size="11">WHEN I SHIP · BY WEEKDAY</text>'
    for i, lab in enumerate("MTWTFSS"):
        h = 6 + 74 * wk[i] / wmx
        x, base = 846 + i * 46, 392
        body += f"""<g class="rise" style="animation-delay:{1 + .06 * i:.2f}s">
<path d="M{x} {base} V{base - h} L{x + 7} {base - h - 5} H{x + 29} V{base - 5} L{x + 22} {base} Z" fill="#a99bff" fill-opacity=".3"/>
<rect x="{x}" y="{base - h:.1f}" width="22" height="{h:.1f}" fill="url(#barg)"/>
<path d="M{x} {base - h:.1f} L{x + 7} {base - h - 5:.1f} H{x + 29} L{x + 22} {base - h:.1f} Z" fill="#ffe0a3"/></g>
<text x="{x + 11}" y="{base + 18}" text-anchor="middle" class="muted mono" font-size="11">{lab}</text>"""
    body += T.wire3d(1128, 48, 18, "ico", dur=12, width=1.2)

    defs = """<linearGradient id="ridge" gradientUnits="userSpaceOnUse" x1="110" y1="0" x2="780" y2="0"><stop offset="0" stop-color="#4fd1c5"/><stop offset=".5" stop-color="#a99bff"/><stop offset="1" stop-color="#4fd1c5"/></linearGradient>
<linearGradient id="ridgehot" gradientUnits="userSpaceOnUse" x1="110" y1="0" x2="780" y2="0"><stop offset="0" stop-color="#f5b544"/><stop offset=".6" stop-color="#ff7a6b"/><stop offset="1" stop-color="#a99bff"/></linearGradient>
<linearGradient id="ridgefill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#a99bff" stop-opacity=".5"/><stop offset="1" stop-color="#a99bff" stop-opacity="0"/></linearGradient>
<linearGradient id="barg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f5b544"/><stop offset="1" stop-color="#ff7a6b"/></linearGradient>"""
    css = """
  .ridge { opacity: 0; animation: fade .7s ease forwards; }
  .trace { stroke-dasharray: 1400; stroke-dashoffset: 1400; animation: draw 2.6s cubic-bezier(.3,.7,.2,1) forwards; }
  .rise { transform-box: fill-box; transform-origin: bottom; animation: rise 1s cubic-bezier(.2,.8,.2,1) both; }
  @keyframes rise { from { transform: scaleY(0); } to { transform: scaleY(1); } }
"""
    out = T.svg(1200, 440, defs + body, css, f"Contribution pulse for {USER}")
    (T.ROOT / "pulse.svg").write_text(out, encoding="utf-8")
    print("wrote pulse.svg")


if __name__ == "__main__":
    data = sample() if "--sample" in sys.argv else fetch()
    build(data)
    build_pulse(data)
