"""Build a full-width, animated toolkit grid grouped by category.

Icons come from skillicons.dev and are embedded as data URIs, so the card
renders as one self-contained image that scales to any width.
    python toolkit.py OUTPUT.svg            # fetch real icons
    python toolkit.py OUTPUT.svg --sample   # offline preview with placeholders
"""
import base64, os, sys, urllib.request
from activity import text, LORA, INTER, INK, INK2, BRICK, SAND, SLATE

GROUPS = [
    ("Frontend", ["html", "css", "js", "ts", "react", "nextjs", "tailwind"]),
    ("Backend", ["php", "laravel", "nodejs", "express", "java", "spring"]),
    ("Mobile", ["kotlin", "androidstudio", "flutter", "dart"]),
    ("Database", ["mysql", "postgres"]),
    ("DevOps", ["docker", "git", "github"]),
    ("Tools", ["postman", "vscode", "figma"]),
]
NAMES = {"js": "JavaScript", "ts": "TypeScript", "nextjs": "Next.js", "nodejs": "Node.js", "androidstudio": "Android",
         "postgres": "PostgreSQL", "vscode": "VS Code", "mysql": "MySQL", "php": "PHP", "html": "HTML", "css": "CSS",
         "tailwind": "Tailwind", "spring": "Spring", "github": "GitHub"}


def icon(name, sample):
    if sample:
        return None
    url = f"https://skillicons.dev/icons?i={name}&theme=dark"
    req = urllib.request.Request(url, headers={"User-Agent": "profile-toolkit-card"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return "data:image/svg+xml;base64," + base64.b64encode(r.read()).decode()


def build(sample):
    W, cols, gap, pad = 1200, 3, 20, 0
    pw = (W - gap * (cols - 1)) / cols          # panel width
    isz, igap, per = 52, 14, 5                   # icon size, gap, icons per row
    rows_needed = [-(-len(g[1]) // per) for g in GROUPS]
    row_h = [76 + max(rows_needed[r*cols:(r+1)*cols]) * (isz + 34) for r in range(2)]
    row_y = [0, row_h[0] + gap]
    H = sum(row_h) + gap
    css = """<style>
.p{opacity:0;animation:in .6s cubic-bezier(.2,.8,.2,1) forwards}
.i{transform-box:fill-box;transform-origin:center;opacity:0;animation:pop .5s cubic-bezier(.3,1.4,.5,1) forwards}
@keyframes in{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
@keyframes pop{from{opacity:0;transform:scale(.4)}to{opacity:1;transform:none}}
@media (prefers-reduced-motion:reduce){.p,.i{animation:none;opacity:1;transform:none}}
</style>"""
    b = [css]
    for gi, (title, items) in enumerate(GROUPS):
        col, row = gi % cols, gi // cols
        x, y = col * (pw + gap), row_y[row]; ph = row_h[row]
        d = gi * 0.12
        panel = [f'<rect x="{x:.1f}" y="{y}" width="{pw:.1f}" height="{ph}" rx="14" fill="{INK}"/>',
                 f'<rect x="{x+24:.1f}" y="{y+52}" width="28" height="3" fill="{BRICK}"/>',
                 text(LORA, title, 24, x + 24, y + 40, SAND)]
        b.append(f'<g class="p" style="animation-delay:{d:.2f}s">{"".join(panel)}</g>')
        for ii, name in enumerate(items):
            r, c = divmod(ii, per)
            ix = x + 24 + c * (isz + igap + 4)
            iy = y + 72 + r * (isz + 34)
            src = icon(name, sample)
            img = (f'<image href="{src}" x="{ix:.1f}" y="{iy}" width="{isz}" height="{isz}"/>' if src else
                   f'<rect x="{ix:.1f}" y="{iy}" width="{isz}" height="{isz}" rx="12" fill="{INK2}" stroke="{BRICK}"/>')
            label = text(INTER, NAMES.get(name, name.capitalize())[:10], 11, ix + isz / 2, iy + isz + 18, SLATE)
            # centre the label under the icon
            b.append(f'<g class="i" style="animation-delay:{d + 0.25 + ii * 0.07:.2f}s">{img}'
                     f'<g transform="translate({-label_w(name)/2:.1f},0)">{label}</g></g>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">'
            f'<title>Toolkit grouped by frontend, backend, mobile, database, DevOps and tools</title>{"".join(b)}</svg>')


def label_w(name):
    s = NAMES.get(name, name.capitalize())[:10]
    hm, cm, sc = INTER["hmtx"], INTER.getBestCmap(), 11 / INTER["head"].unitsPerEm
    return sum(hm[cm[ord(ch)]][0] * sc for ch in s if ord(ch) in cm)


if __name__ == "__main__":
    open(sys.argv[1], "w").write(build("--sample" in sys.argv))
    print("wrote", sys.argv[1])
