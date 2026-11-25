#!/usr/bin/env python3
"""Build original GrizzlyFX profile graphics from public GitHub data only."""
import argparse
import collections
import datetime as dt
import html
import json
import os
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OWNER = "solo19978"
GOLD = "#E6B450"
WHITE = "#F4F1E9"
MUTED = "#B4B5B8"
BG = "#111214"
PANEL = "#191B1F"
LINE = "#34312B"


def api(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "GrizzlyFX-public-profile"}
    if os.environ.get("GH_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
    request = urllib.request.Request("https://api.github.com" + path, headers=headers)
    with urllib.request.urlopen(request, timeout=40) as response:
        return json.load(response)


def pages(path):
    result = []
    sep = "&" if "?" in path else "?"
    for page in range(1, 101):
        batch = api(f"{path}{sep}per_page=100&page={page}")
        if not isinstance(batch, list):
            raise ValueError("Expected a paginated list")
        result.extend(batch)
        if len(batch) < 100:
            return result
    raise RuntimeError("Pagination limit reached; refusing to publish partial counts")


def collect():
    today = dt.datetime.now(dt.timezone.utc).date()
    start = today - dt.timedelta(days=83)
    # /users/:user/repos exposes public repositories. Recheck the flags anyway.
    repos = [r for r in pages(f"/users/{OWNER}/repos?type=owner")
             if not r["private"] and not r["fork"] and r["name"] != OWNER]
    counts = collections.Counter()
    projects = []
    for repo in sorted(repos, key=lambda r: r["name"]):
        query = urllib.parse.urlencode({"author": OWNER, "since": str(start) + "T00:00:00Z"})
        try:
            commits = pages(f"/repos/{repo['full_name']}/commits?{query}")
        except urllib.error.HTTPError as exc:
            if exc.code == 409 and repo["size"] == 0:
                commits = []
            else:
                raise
        for commit in commits:
            date = commit["commit"]["author"]["date"][:10]
            if str(start) <= date <= str(today):
                counts[date] += 1
        projects.append({"name": repo["name"], "url": repo["html_url"],
                         "language": repo["language"], "stars": repo["stargazers_count"]})
    return {"updated": str(today), "window_start": str(start), "owner": OWNER,
            "scope": "Public owned non-fork repositories, excluding the profile repository; default-branch commits attributed to solo19978 by GitHub. UTC dates.",
            "projects": projects, "daily": [
                {"date": str(start + dt.timedelta(days=i)), "commits": counts[str(start + dt.timedelta(days=i))]}
                for i in range(84)]}


def text(x, y, value, size=16, color=WHITE, weight=400, extra=""):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" {extra}>{html.escape(str(value))}</text>'


def rect(x, y, w, h, fill=PANEL, radius=12, stroke=LINE):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>'


def svg(w, h, title, body):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">
<title id="title">{html.escape(title)}</title><desc id="desc">Original GrizzlyFX design in charcoal and gold.</desc>
<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#1D1D1D"/><stop offset="1" stop-color="#0D0E10"/></linearGradient><linearGradient id="gold"><stop stop-color="#E6B450"/><stop offset="1" stop-color="#F9DA94"/></linearGradient><pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M 40 0 L 0 0 0 40" fill="none" stroke="#E6B450" stroke-opacity=".045"/></pattern></defs>
<style>text{{font-family:Arial,Helvetica,sans-serif}} .mono{{font-family:monospace;letter-spacing:1.8px}} .pulse{{animation:pulse 4s ease-in-out infinite}} @keyframes pulse{{0%,100%{{opacity:.35}}50%{{opacity:1}}}} @media(prefers-reduced-motion:reduce){{.pulse{{animation:none}}}}</style>
<rect width="{w}" height="{h}" rx="18" fill="url(#bg)"/><rect width="{w}" height="{h}" rx="18" fill="url(#grid)"/><rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="18" fill="none" stroke="{LINE}"/>{body}</svg>\n'''


def header(mobile=False):
    w, h = (600, 380) if mobile else (1000, 360)
    b = text(36, 45, "GFX / INDEPENDENT TOOLS & CREATIVE SYSTEMS", 11 if mobile else 12, GOLD, 600, 'class="mono"')
    b += f'<path d="M36 65 H{w-36}" stroke="{LINE}"/>'
    b += text(34, 150 if mobile else 153, "GRIZZLYFX", 64 if mobile else 76, WHITE, 800, 'letter-spacing="-3"')
    b += text(38, 192 if mobile else 195, "Build tools. Make room to create.", 23 if mobile else 25, GOLD)
    b += text(38, 235 if mobile else 242, "DESKTOP SOFTWARE  /  WORKFLOW AUTOMATION", 12 if mobile else 13, MUTED, extra='class="mono"')
    b += text(38, 263 if mobile else 268, "CREATIVE CONTROL  /  PRACTICAL DESIGN", 12 if mobile else 13, MUTED, extra='class="mono"')
    b += f'<path d="M36 {h-55} H{w-36}" stroke="{LINE}"/>'
    b += f'<circle class="pulse" cx="43" cy="{h-29}" r="4" fill="{GOLD}"/>'
    b += text(58, h-24, "SOLO19978", 12, GOLD, extra='class="mono"')
    b += text(w-240, h-24, "IDEA → BUILD → REFINE", 11, MUTED, extra='class="mono"')
    if not mobile:
        b += '<g transform="translate(808 175)">'
        for r, op in [(105, .12), (80, .26), (54, .6)]:
            b += f'<circle r="{r}" fill="none" stroke="{GOLD}" stroke-opacity="{op}" stroke-dasharray="{r*3} 20"/>'
        b += f'<path d="M-25 14 L0 -30 L25 14 L0 42 Z M-25 14 H25 M0 -30 V42" fill="none" stroke="{GOLD}" stroke-width="2"/>'
        b += f'<circle class="pulse" cx="80" r="5" fill="{GOLD}"/></g>'
    return svg(w, h, "GrizzlyFX — Build tools. Make room to create.", b)


def telemetry(data, mobile=False):
    w, h = (600, 660) if mobile else (1000, 470)
    daily = data["daily"]
    total = sum(d["commits"] for d in daily)
    peak = max((d["commits"] for d in daily), default=0)
    values = [(len(data["projects"]), "PUBLIC PROJECTS"), (total, "COMMITS / 12 WEEKS"),
              (sum(d["commits"] > 0 for d in daily), "ACTIVE DAYS / 84"),
              (sum(r["stars"] for r in data["projects"]), "PROJECT STARS")]
    b = text(32, 40, "PUBLIC BUILD ACTIVITY", 17, WHITE, 700, 'class="mono"')
    b += text(32, 66, "GitHub snapshot · " + data["updated"] + " UTC", 12, MUTED)
    cw = 256 if mobile else 216
    for i, (value, label) in enumerate(values):
        x = 32 + (i % 2 if mobile else i) * (cw + 24)
        y = 91 + (i // 2 * 107 if mobile else 0)
        b += rect(x, y, cw, 86)
        b += text(x+16, y+25, label, 10, MUTED, extra='class="mono"')
        b += text(x+16, y+65, value, 33, GOLD, 700)
    cy = 360 if mobile else 245
    chartw, charth = w-64, 125
    b += text(32, cy-25, "AUTHORED COMMITS · DAILY", 11, MUTED, extra='class="mono"')
    for i in range(4):
        yy = cy + i * charth / 3
        b += f'<path d="M32 {yy} H{w-32}" stroke="#34312B" stroke-dasharray="3 5"/>'
    step = chartw / 84
    for i, day in enumerate(daily):
        bh = day["commits"] / max(peak, 1) * charth
        if bh:
            b += f'<rect x="{32+i*step:.2f}" y="{cy+charth-bh:.2f}" width="{max(1, step-1.5):.2f}" height="{bh:.2f}" rx="1" fill="{GOLD}"><title>{day["date"]}: {day["commits"]} commits</title></rect>'
    b += text(32, cy+charth+23, data["window_start"], 11, MUTED)
    b += text(w-133, cy+charth+23, data["updated"], 11, MUTED)
    b += text(w-150, cy-25, f"PEAK {peak} / DAY", 10, GOLD, extra='class="mono"')
    fy = h-53
    b += text(32, fy, "Public owned projects · profile repository excluded", 12, MUTED)
    b += text(32, fy+22, "Default-branch history · refreshed daily by GitHub Actions", 12, MUTED)
    return svg(w, h, f"Public GitHub activity: {len(data['projects'])} projects and {total} authored commits in 12 weeks. Updated {data['updated']} UTC.", b)


def landscape(data):
    b = text(32, 40, "THE BUILD LANDSCAPE", 17, WHITE, 700, 'class="mono"')
    b += text(32, 66, "The same 84 days, viewed in three dimensions. Height = authored commits.", 13, MUTED)
    peak = max((d["commits"] for d in data["daily"]), default=1) or 1
    for week in range(12):
        for day in range(7):
            n = data["daily"][week*7+day]["commits"]
            x, y = 220 + week*39 - day*21, 142 + week*8 + day*12
            z = 3 + n / peak * 95
            b += f'<g><title>{data["daily"][week*7+day]["date"]}: {n} commits</title><path d="M{x-18} {y} l18 9 v{-z} l-18 -9 Z" fill="{"#7A5D2C" if n else "#292723"}"/><path d="M{x} {y+9} l18 -9 v{-z} l-18 9 Z" fill="{"#AA8038" if n else "#383128"}"/><path d="M{x-18} {y-z} l18 -9 l18 9 l-18 9 Z" fill="{GOLD if n else "#464033"}" stroke="#141414" stroke-width="1"/></g>'
    b += text(780, 164, "12", 50, GOLD, 700)
    b += text(782, 192, "WEEKS OF BUILDS", 11, MUTED, extra='class="mono"')
    b += text(32, 355, "PUBLIC PROJECT HISTORY / " + data["updated"], 11, MUTED, extra='class="mono"')
    return svg(1000, 385, "Isometric activity landscape for the last 12 weeks of public project commits", b)


def project(kind):
    quota = kind == "quota"
    title = "QUOTA SENTINEL" if quota else "LOUPEDECK"
    subtitle = "Desktop usage monitor" if quota else "Power Profiles"
    b = text(28, 39, "01 / DESKTOP SOFTWARE" if quota else "02 / CREATIVE CONTROL", 10, GOLD, extra='class="mono"')
    b += text(27, 85, title, 30, WHITE, 800)
    b += text(28, 114, subtitle, 18, MUTED)
    if quota:
        for cx, color in [(183, GOLD), (295, "#95B8D1")]:
            b += f'<circle cx="{cx}" cy="192" r="33" stroke="#303237" stroke-width="10" fill="none"/><circle cx="{cx}" cy="192" r="33" stroke="{color}" stroke-width="10" stroke-dasharray="150 208" transform="rotate(-90 {cx} 192)" fill="none"/><circle cx="{cx}" cy="192" r="4" fill="{color}"/>'
        b += text(28, 267, "RUST / TAURI / WINDOWS", 11, GOLD, extra='class="mono"')
        b += text(28, 296, "Claude Code + Codex usage at a glance.", 15, MUTED)
    else:
        for i in range(12):
            x, y = 163 + i%4*39, 147+i//4*33
            b += rect(x, y, 31, 25, "#332D21" if i in (0, 5, 10) else "#23252A", 4, "#615032" if i in (0, 5, 10) else LINE)
            b += f'<path d="M{x+10} {y+12} h11" stroke="{GOLD if i in (0,5,10) else MUTED}"/>'
        for x in (130, 342):
            for y in (159,192,225):
                b += f'<circle cx="{x}" cy="{y}" r="9" fill="#23252A" stroke="#615032"/>'
        b += text(28, 267, "LOUPEDECK LIVE / .LP5", 11, GOLD, extra='class="mono"')
        b += text(28, 296, "Familiar controls. Faster creative workflows.", 15, MUTED)
    b += text(28, 332, "EXPLORE PROJECT ↗", 11, GOLD, 700, 'class="mono"')
    return svg(480, 355, title + " — " + subtitle + ". Stylised project illustration.", b)


def workflow():
    b = text(32, 38, "HOW I BUILD", 17, WHITE, 700, 'class="mono"')
    items = [("01 / UNDERSTAND", "Find the friction", "Start with the real workflow."),
             ("02 / MAKE", "Build the tool", "Keep the interface clear."),
             ("03 / REFINE", "Test and improve", "Make everyday use easier.")]
    for i,(eyebrow,title,desc) in enumerate(items):
        x = 32+i*319
        b += rect(x, 65, 296, 119)
        b += text(x+17, 92, eyebrow, 10, GOLD, extra='class="mono"')
        b += text(x+17, 126, title, 22, WHITE, 700)
        b += text(x+17, 157, desc, 14, MUTED)
        if i<2:
            b += f'<path d="M{x+298} 124 h17 m-5 -4 l5 4 -5 4" fill="none" stroke="{GOLD}"/>'
    return svg(1000, 214, "Understand the workflow, build a clear tool, then test and refine it", b)


def build(data):
    assets = ROOT / "assets"
    assets.mkdir(exist_ok=True)
    files = {"header.svg":header(), "header-mobile.svg":header(True),
             "activity.svg":telemetry(data), "activity-mobile.svg":telemetry(data, True),
             "landscape.svg":landscape(data), "project-quota.svg":project("quota"),
             "project-loupedeck.svg":project("loupedeck"), "workflow.svg":workflow()}
    for name, content in files.items():
        (assets/name).write_text(content)
    (assets/"public-activity.json").write_text(json.dumps(data, indent=2)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-json", type=Path, help="Rebuild from a previously verified public snapshot")
    args = parser.parse_args()
    data = json.loads(args.from_json.read_text()) if args.from_json else collect()
    build(data)
    print(f"Built profile graphics from {len(data['projects'])} public projects; snapshot {data['updated']}.")
