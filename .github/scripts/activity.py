"""Build an animated activity card from live GitHub data.

Run by .github/workflows/profile.yml. Usage:
    python activity.py OUTPUT.svg            # live data (needs GITHUB_TOKEN)
    python activity.py OUTPUT.svg --sample   # offline preview
"""
import json, os, sys, urllib.request
from datetime import datetime, timezone
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

USER = os.environ.get("PROFILE_USER", "AzimAminz")
HIDE = {USER.lower(), "silverlink"}  # repos kept off the card
HERE = os.path.dirname(os.path.abspath(__file__))

INK, INK2, BRICK, SAND, SLATE = "#1F2A44", "#2A3858", "#B5452F", "#EDE4D3", "#8A97AB"
RAMP = ["#B5452F", "#C9704F", "#D99A74", "#E3BE9E", "#8A97AB", "#5E6C85"]

LORA = TTFont(f"{HERE}/fonts/Lora-SemiBold.ttf")
INTER = TTFont(f"{HERE}/fonts/Inter-Regular.otf")
INTER_MED = TTFont(f"{HERE}/fonts/Inter-Medium.otf")


def text(font, s, size, x, y, fill, track=0.0, anchor="start"):
    gs, cmap, upm, hmtx = font.getGlyphSet(), font.getBestCmap(), font["head"].unitsPerEm, font["hmtx"]
    sc = size / upm
    names = [cmap.get(ord(c)) or cmap.get(ord("?")) for c in s]
    w = sum(hmtx[n][0] * sc + track for n in names)
    if anchor == "end":
        x -= w
    out, cx = [], 0.0
    for n in names:
        pen = SVGPathPen(gs)
        gs[n].draw(TransformPen(pen, (sc, 0, 0, -sc, x + cx, y)))
        if d := pen.getCommands():
            out.append(d)
        cx += hmtx[n][0] * sc + track
    return f'<path fill="{fill}" d="{" ".join(out)}"/>'


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
        "User-Agent": "profile-activity-card"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def live():
    repos = api(f"/users/{USER}/repos?per_page=100&sort=pushed&type=owner")
    repos = [r for r in repos if not r["fork"] and r["name"].lower() not in HIDE]
    langs = {}
    for r in repos[:40]:
        for k, v in api(f"/repos/{USER}/{r['name']}/languages").items():
            langs[k] = langs.get(k, 0) + v
    recent = [(r["name"], r["language"] or "Mixed", r["pushed_at"]) for r in repos[:5]]
    return langs, recent, len(repos), sum(r["stargazers_count"] for r in repos)


def sample():
    langs = {"PHP": 900, "JavaScript": 820, "Java": 520, "Kotlin": 300, "Dart": 220, "CSS": 160, "Blade": 90}
    recent = [("CharityStride", "PHP", "2026-10-22T02:31:04Z"), ("SmartCampusConnect", "Java", "2026-09-28T06:53:57Z"),
              ("Portfolio", "TypeScript", "2026-09-21T23:45:17Z"), ("rosfinah-co", "PHP", "2026-08-13T08:16:05Z"),
              ("chat-app-nodejs", "JavaScript", "2026-07-06T06:33:20Z")]
    return langs, recent, 24, 12


def ago(iso):
    d = (datetime.now(timezone.utc) - datetime.fromisoformat(iso.replace("Z", "+00:00"))).days
    if d < 1: return "updated today"
    if d == 1: return "updated yesterday"
    if d < 30: return f"updated {d} days ago"
    if d < 60: return "updated a month ago"
    if d < 365: return f"updated {d // 30} months ago"
    return "updated over a year ago"


def build(langs, recent, n_repos, stars):
    W, H = 1200, 430
    total = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:6]
    css = """<style>
.bar{transform-box:fill-box;transform-origin:left;transform:scaleX(0);animation:grow 1.1s cubic-bezier(.2,.8,.2,1) forwards}
.in{opacity:0;animation:in .6s cubic-bezier(.2,.8,.2,1) forwards}
.row{opacity:0;animation:slide .7s cubic-bezier(.2,.8,.2,1) forwards}
.pulse{transform-box:fill-box;transform-origin:center;animation:pulse 2s ease-out infinite}
@keyframes grow{to{transform:scaleX(1)}}
@keyframes in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes slide{from{opacity:0;transform:translateX(24px)}to{opacity:1;transform:none}}
@keyframes pulse{0%{opacity:.7;transform:scale(1)}100%{opacity:0;transform:scale(3)}}
@media (prefers-reduced-motion:reduce){.bar,.in,.row,.pulse{animation:none;opacity:1;transform:none}.pulse{opacity:0}}
</style>"""
    b = [css, f'<rect width="{W}" height="{H}" rx="14" fill="{INK}"/>']

    # left column: languages
    b.append(f'<g class="in">{text(LORA, "Languages across my repositories", 26, 56, 70, SAND)}</g>')
    y = 118
    for i, (name, v) in enumerate(top):
        pct = v / total * 100
        d = 0.25 + i * 0.12
        b.append(f'<g class="in" style="animation-delay:{d}s">{text(INTER_MED, name, 15, 56, y, SAND, 0.2)}'
                 f'{text(INTER, f"{pct:.1f}%", 15, 540, y, SLATE, anchor="end")}</g>')
        b.append(f'<rect x="56" y="{y+10}" width="484" height="8" rx="4" fill="{INK2}"/>')
        b.append(f'<rect class="bar" style="animation-delay:{d+0.1}s" x="56" y="{y+10}" width="{max(6, 484*v/top[0][1]):.1f}" height="8" rx="4" fill="{RAMP[i % len(RAMP)]}"/>')
        y += 46

    b.append(f'<line x1="600" y1="48" x2="600" y2="{H-48}" stroke="{SLATE}" stroke-opacity=".25"/>')

    # right column: recent activity
    b.append(f'<g class="in" style="animation-delay:.15s">{text(LORA, "Recently active", 26, 648, 70, SAND)}</g>')
    y = 120
    for i, (name, lang, when) in enumerate(recent):
        d = 0.5 + i * 0.15
        row = [f'<rect x="648" y="{y-26}" width="496" height="46" rx="10" fill="{INK2}"/>']
        if i == 0:
            row.append(f'<circle class="pulse" cx="672" cy="{y-3}" r="6" fill="{BRICK}"/>')
        row.append(f'<circle cx="672" cy="{y-3}" r="6" fill="{BRICK if i == 0 else SLATE}"/>')
        row.append(text(INTER_MED, name[:30], 16, 692, y + 2, SAND, 0.2))
        row.append(text(INTER, f"{lang}, {ago(when)}", 13, 1128, y + 1, SLATE, anchor="end"))
        b.append(f'<g class="row" style="animation-delay:{d}s">{"".join(row)}</g>')
        y += 56

    stamp = datetime.now(timezone.utc).strftime("%d %b %Y")
    foot = f"{n_repos} public repositories, {stars} stars. Refreshed {stamp} by GitHub Actions."
    b.append(f'<g class="in" style="animation-delay:1.4s">{text(INTER, foot, 13, 56, H-34, SLATE)}</g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">'
            f'<title>Live GitHub activity for {USER}</title>{"".join(b)}</svg>')


if __name__ == "__main__":
    data = sample() if "--sample" in sys.argv else live()
    open(sys.argv[1], "w").write(build(*data))
    print("wrote", sys.argv[1])
