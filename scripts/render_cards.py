#!/usr/bin/env python3
"""
Render the profile README cards as animated SVGs into cards/.

Look: dark cards with MERN accents (MongoDB green, React cyan, amber), Geist and
Geist Mono. Each card is a standalone SVG shown through <img>, so it may only use
what GitHub allows there: inline CSS animations, SMIL and fonts embedded as data
URIs (no JS, no external requests).

Live numbers come from data/stats.json (scripts/fetch_stats.py). Text that is
about you (tagline, terminal lines, tile blurbs, featured repos) is set below.

    python scripts/render_cards.py          # animated
    STATIC=1 python scripts/render_cards.py # end state, for previews
"""
import base64
import datetime as dt
import json
import os
import re
from html import escape

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "data", "stats.json")
OUT = os.path.join(ROOT, "cards")
FONTS = os.path.join(ROOT, "fonts")
STATIC = bool(os.environ.get("STATIC"))

# ---- about you -------------------------------------------------------------------
FIRST, LAST = "Sunil", "Dondey"
ROLE = "FULL STACK DEVELOPER · SPEEDY ACCOUNTS"
BLURB = ["I build full stack apps with MERN and Next.js,", "from online stores to billing dashboards."]
SITE = "sunil-s-portfolio.vercel.app"
STACK_LINES = ["MongoDB  Express  React  Node.js", "Next.js  TypeScript  Tailwind"]
STATUS = "building @ Speedy Accounts, Raipur"
FEATURED = [  # (repo, description) shown under "What I'm building"
    ("Zenith-Console-Cafe", "Site and admin for a PS5 gaming cafe: live stations, auto billing, food orders and party bookings."),
    ("BNB-Enterprises", "Website for a solar energy vendor, built with Next.js 16 and Motion animations."),
    ("A2Z-Hub-Ecommerse", "E-commerce store with its own frontend and backend, deployed on Vercel."),
]

# ---- tokens ----------------------------------------------------------------------
CARD = "#11161d"
BORDER = "#262d36"
TEXT = "#e6edf3"
SOFT = "#aab4c0"
MUTED = "#7d8590"
RULE = "#262d36"
DIM = "#3a424d"
GREEN = "#00ed64"   # MongoDB
CYAN = "#61dafb"    # React
AMBER = "#ffb224"
ON = "#0b0f14"      # text on bright tiles
LEVELS = ["#1c232d", "#0b4a2a", "#08803f", "#00b85a", GREEN]  # GitHub data-level 0..4
LANG = {"TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572a5", "HTML": "#e34c26", "CSS": "#663399"}
W = 880
GAP = 12            # gap baked into the SVGs so rows tile evenly
SANS = "Geist, system-ui, -apple-system, 'Segoe UI', sans-serif"
MONO = "'Geist Mono', ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
FONT_FILES = {"sans": ("Geist", 400, "geist-400.woff"), "bold": ("Geist", 600, "geist-600.woff"),
              "mono": ("Geist Mono", 400, "geistmono-400.woff")}

CSS = """
@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes pop{0%{opacity:0;transform:scale(.3)}70%{opacity:1;transform:scale(1.15)}100%{opacity:1;transform:none}}
@keyframes drop{0%{opacity:0;transform:translateY(70px) scale(.7) rotate(-6deg)}60%{opacity:1;transform:translateY(-8px) scale(1.03) rotate(1.5deg)}100%{opacity:1;transform:none}}
@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}
@keyframes nudge{0%,100%{transform:none}50%{transform:translate(3px,-3px)}}
@keyframes sheen{0%{transform:translateX(-200px) skewX(-20deg)}25%,100%{transform:translateX(420px) skewX(-20deg)}}
.r{opacity:0;transform-box:fill-box;animation:rise .7s cubic-bezier(.2,.7,.2,1) both}
.f{opacity:0;animation:fade .8s ease-out both}
.g{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .8s cubic-bezier(.2,.7,.2,1) both}
.p{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .4s ease-out both}
.d{opacity:0;transform-box:fill-box;transform-origin:50% 60%;animation:drop 1s cubic-bezier(.2,.8,.2,1) both}
.b{animation:blink 1s step-end infinite}
.live{animation:pulse 1.6s ease-in-out infinite}
.nu{transform-box:fill-box;animation:nudge 1.8s ease-in-out infinite}
.sh{animation:sheen 5s ease-in-out infinite}
@media (prefers-reduced-motion:reduce){.r,.f,.g,.p,.d,.live,.nu,.b{animation:none!important;opacity:1!important;transform:none!important}.sh{display:none}}
"""
STATIC_CSS = ".r,.f,.g,.p,.d,.live,.nu,.b{animation:none!important;opacity:1!important;transform:none!important}.sh{display:none}"


def fonts(keys):
    out = []
    for k in keys:
        fam, weight, fn = FONT_FILES[k]
        b64 = base64.b64encode(open(os.path.join(FONTS, fn), "rb").read()).decode()
        out.append(f"@font-face{{font-family:'{fam}';font-weight:{weight};src:url(data:font/woff;base64,{b64}) format('woff')}}")
    return "".join(out)


def svg(name, w, h, body, keys, label, left=0, right=0, bottom=GAP):
    if left:
        body = f'<g transform="translate({left:.3f} 0)">{body}</g>'
    w, h = w + left + right, h + bottom
    css = fonts(keys) + CSS + (STATIC_CSS if STATIC else "")
    doc = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}" height="{h}" viewBox="0 0 {w:.3f} {h}" '
           f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title><style>{css}</style>{body}</svg>')
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"wrote cards/{name} ({len(doc) // 1024} KB)")


def d(s):
    return f'style="animation-delay:{s:.2f}s"'


def wrap(text, n):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > n:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line] if line else lines


def frame(w, h):
    return (f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="14" fill="{CARD}" '
            f'stroke="{BORDER}"/>')


# ---- hero: name + typing terminal --------------------------------------------------
def typed(x, y, text, begin, dur, color, size=13):
    """One terminal line revealed left to right by a clip wipe (SMIL works inside <img>)."""
    t = f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{color}" xml:space="preserve">{escape(text)}</text>'
    if STATIC:
        return t
    typed.n = getattr(typed, "n", 0) + 1
    cid = f"type{typed.n}"
    return (f'<clipPath id="{cid}"><rect x="{x}" y="{y - 14}" height="20" width="0">'
            f'<animate attributeName="width" from="0" to="360" begin="{begin:.2f}s" dur="{dur:.2f}s" fill="freeze"/>'
            f'</rect></clipPath><g clip-path="url(#{cid})">{t}</g>')


def hero(data):
    h = 420
    px, py, pw, ph = 476, 40, 364, 340   # terminal panel
    tx, lh = px + 20, 23
    lines, t = [], 0.9
    recent = data["recent"][:2]

    def cmd(cmd_text):
        nonlocal t
        y = py + 62 + len(lines) * lh
        dur = 0.045 * len(cmd_text) + 0.15
        lines.append(f'<text class="f" {d(t)} x="{tx}" y="{y}" font-family="{MONO}" font-size="13" fill="{GREEN}">~ $</text>'
                     + typed(tx + 36, y, cmd_text, t + 0.1, dur, TEXT))
        t += dur + 0.25

    def out(text, color=SOFT):
        nonlocal t
        y = py + 62 + len(lines) * lh
        lines.append(f'<text class="f" {d(t)} x="{tx}" y="{y}" font-family="{MONO}" font-size="13" fill="{color}" '
                     f'xml:space="preserve">{escape(text)}</text>')
        t += 0.12

    cmd("whoami")
    out(f"{FIRST} {LAST}, full stack developer", TEXT)
    cmd("cat stack.txt")
    for s in STACK_LINES:
        out(s, CYAN)
    cmd("ls ~/projects --recent")
    for r in recent:
        out(f"{r['name'][:24]:<26}{r['language'] or ''}")
    cmd("./status")
    out(STATUS, AMBER)
    y_last = py + 62 + len(lines) * lh
    lines.append(f'<g class="f" {d(t)}><text x="{tx}" y="{y_last}" font-family="{MONO}" font-size="13" fill="{GREEN}">~ $</text>'
                 f'<rect class="b" x="{tx + 36}" y="{y_last - 12}" width="8" height="15" fill="{TEXT}"/></g>')

    dots = "".join(f'<circle cx="{px + 22 + i * 16}" cy="{py + 18}" r="5" fill="{c}"/>'
                   for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]))
    body = f"""
<defs>
  <linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="420" y2="0">
    <stop offset="0" stop-color="{TEXT}"/><stop offset=".4" stop-color="{TEXT}"/>
    <stop offset=".5" stop-color="{CYAN}"/><stop offset=".6" stop-color="{TEXT}"/><stop offset="1" stop-color="{TEXT}"/>
    {'' if STATIC else '<animateTransform attributeName="gradientTransform" type="translate" values="-420 0;520 0;520 0" keyTimes="0;.45;1" dur="7s" begin="1.4s" repeatCount="indefinite"/>'}
  </linearGradient>
</defs>
{frame(W, h)}
<g class="f" {d(0)}>
  <circle class="live" cx="52" cy="53" r="4.5" fill="{GREEN}"/>
  <text x="66" y="57" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">{escape(ROLE)}</text>
</g>
<text class="r" {d(0.15)} x="42" y="178" font-family="{SANS}" font-weight="600" font-size="100" letter-spacing="-4" fill="{TEXT}">{FIRST}</text>
<text class="r" {d(0.3)} x="42" y="274" font-family="{SANS}" font-weight="600" font-size="100" letter-spacing="-4" fill="url(#shine)">{LAST}<tspan fill="{GREEN}">.</tspan></text>
<g class="r" {d(0.5)}>
  {''.join(f'<text x="46" y="{322 + i * 26}" font-family="{SANS}" font-size="17" fill="{SOFT}">{escape(l)}</text>' for i, l in enumerate(BLURB))}
</g>
<g class="f" {d(0.75)}>
  <text x="46" y="392" font-family="{MONO}" font-size="13" fill="{TEXT}">{SITE}</text>
  <text class="nu" x="{46 + len(SITE) * 7.8 + 6:.0f}" y="392" font-family="{MONO}" font-size="13" fill="{GREEN}">&#8599;</text>
</g>
<g class="f" {d(0.6)}>
  <rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="10" fill="#0b0f14" stroke="{BORDER}"/>
  <line x1="{px}" y1="{py + 36}" x2="{px + pw}" y2="{py + 36}" stroke="{BORDER}"/>
  {dots}
  <text x="{px + pw / 2 + 24}" y="{py + 22}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="{MUTED}">sunil@raipur: ~</text>
</g>
{''.join(lines)}
"""
    svg("hero.svg", W, h, body, ["sans", "bold", "mono"],
        f"{FIRST} {LAST}. Full stack developer at Speedy Accounts. {' '.join(BLURB)}")


# ---- three tiles -------------------------------------------------------------------
TW, TH = W / 3 - 8, 200


def count_up(num, word, x, y, begin, dur=1.1, frames=18):
    """Number counts up from 0 using SMIL <set> frames, easing out."""
    attrs = f'font-family="{SANS}" font-weight="600" font-size="46" letter-spacing="-1.5" fill="{ON}"'
    tail = f'<tspan font-weight="400" font-size="22" letter-spacing="0" dx="8">{escape(word)}</tspan>'
    if STATIC or not re.fullmatch(r"\d+", num):
        return f'<text x="{x}" y="{y}" {attrs}>{escape(num)}{tail}</text>'
    out, val = [], int(num)
    for i in range(frames + 1):
        shown = num if i == frames else str(round(val * (1 - (1 - i / frames) ** 3)))
        off = "" if i == frames else f'<set attributeName="opacity" to="0" begin="{begin + dur * (i + 1) / frames:.3f}s"/>'
        out.append(f'<text x="{x}" y="{y}" {attrs} opacity="0">{shown}{tail}'
                   f'<set attributeName="opacity" to="1" begin="{begin + dur * i / frames:.3f}s"/>{off}</text>')
    return "".join(out)


def tile(name, label, color, num, word, blurb, delay, pos):
    blurb_svg = "".join(
        f'<text class="r" {d(delay + 0.7 + i * 0.1)} x="24" y="{146 + i * 20}" font-family="{SANS}" '
        f'font-size="14" fill="{ON}" opacity=".85">{escape(l)}</text>' for i, l in enumerate(wrap(blurb, 34)))
    body = f"""
<defs>
  <clipPath id="clip-{name}"><rect width="{TW}" height="{TH}" rx="14"/></clipPath>
  <linearGradient id="gl-{name}" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset=".5" stop-color="#fff" stop-opacity=".4"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
</defs>
<g class="d" {d(delay)}>
  <g clip-path="url(#clip-{name})">
    <rect width="{TW}" height="{TH}" fill="{color}"/>
    <circle cx="{TW - 34}" cy="{TH - 30}" r="70" fill="none" stroke="{ON}" stroke-opacity=".12" stroke-width="18"/>
    <rect class="sh" style="animation-delay:{delay + 1.3:.2f}s" x="0" y="-20" width="80" height="{TH + 40}" fill="url(#gl-{name})" transform="translate(-200 0)"/>
  </g>
  <text class="f" {d(delay + 0.3)} x="24" y="38" font-family="{MONO}" font-size="12" letter-spacing="1.2" fill="{ON}">{label}</text>
  <text class="f nu" {d(delay + 0.4)} x="{TW - 36}" y="38" font-family="{MONO}" font-size="14" fill="{ON}">&#8599;</text>
  {count_up(num, word, 22, 108, delay + 0.4)}
  {blurb_svg}
</g>
"""
    svg(f"{name}.svg", TW, TH, body, ["sans", "bold", "mono"], f"{label}: {num} {word}. {blurb}",
        left=4 * pos, right=8 - 4 * pos)


def stack_tile(delay, pos):
    """STACK tile: the four MERN letters drop in one by one."""
    name, label = "stack", "STACK"
    xs = [22, 64, 95, 128]  # hand-kerned for Geist 600 at 46px (M is wider than E and R)
    letters = "".join(
        f'<text class="p" {d(delay + 0.45 + i * 0.12)} x="{xs[i]}" y="108" font-family="{SANS}" '
        f'font-weight="600" font-size="46" fill="{ON}">{ch}</text>' for i, ch in enumerate("MERN"))
    blurb = "MongoDB, Express, React and Node, plus Next.js, TypeScript and Tailwind."
    lines = "".join(
        f'<text class="r" {d(delay + 0.9 + i * 0.1)} x="24" y="{146 + i * 20}" font-family="{SANS}" '
        f'font-size="14" fill="{ON}" opacity=".85">{escape(l)}</text>' for i, l in enumerate(wrap(blurb, 34)))
    body = f"""
<defs><clipPath id="clip-{name}"><rect width="{TW}" height="{TH}" rx="14"/></clipPath>
  <linearGradient id="gl-{name}" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset=".5" stop-color="#fff" stop-opacity=".4"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>
<g class="d" {d(delay)}>
  <g clip-path="url(#clip-{name})">
    <rect width="{TW}" height="{TH}" fill="{CYAN}"/>
    <g transform="translate({TW - 46} {TH - 44})" fill="none" stroke="{ON}" stroke-opacity=".14" stroke-width="5">
      <ellipse rx="62" ry="24"/><ellipse rx="62" ry="24" transform="rotate(60)"/><ellipse rx="62" ry="24" transform="rotate(120)"/>
    </g>
    <rect class="sh" style="animation-delay:{delay + 1.3:.2f}s" x="0" y="-20" width="80" height="{TH + 40}" fill="url(#gl-{name})" transform="translate(-200 0)"/>
  </g>
  <text class="f" {d(delay + 0.3)} x="24" y="38" font-family="{MONO}" font-size="12" letter-spacing="1.2" fill="{ON}">{label}</text>
  <text class="f nu" {d(delay + 0.4)} x="{TW - 36}" y="38" font-family="{MONO}" font-size="14" fill="{ON}">&#8599;</text>
  {letters}
  {lines}
</g>
"""
    svg(f"{name}.svg", TW, TH, body, ["sans", "bold", "mono"], f"{label}: MERN. {blurb}",
        left=4 * pos, right=8 - 4 * pos)


# ---- contribution graph ----------------------------------------------------------------
def heatmap(data):
    days = data["days"]
    lead = (dt.date.fromisoformat(days[0]["date"]).weekday() + 1) % 7  # sunday first
    cell, step, gx, gy = 12, 15, 44, 96
    cells, months, seen = [], [], set()
    for i, day in enumerate(days):
        col, row = divmod(i + lead, 7)
        date = dt.date.fromisoformat(day["date"])
        if row == 0 and date.day <= 7 and (date.year, date.month) not in seen:
            seen.add((date.year, date.month))
            months.append((col, date.strftime("%b")))
        c = day["count"]
        cells.append(
            f'<rect class="p" style="animation-delay:{0.8 + col * 0.025 + row * 0.02:.2f}s" x="{gx + col * step}" '
            f'y="{gy + row * step}" width="{cell}" height="{cell}" rx="3" fill="{LEVELS[min(day["level"], 4)]}">'
            f'<title>{day["date"]}: {c} contribution{"" if c == 1 else "s"}</title></rect>')
    ncols = (len(days) + lead + 6) // 7
    right = gx + ncols * step - 3
    base = gy + 7 * step
    labels = "".join(f'<text x="{gx + col * step}" y="{base + 18}" font-family="{MONO}" font-size="11" fill="{MUTED}">{m}</text>'
                     for col, m in months if col < ncols - 10)
    lx = right - len(LEVELS) * 14
    legend = "".join(f'<rect x="{lx + i * 14}" y="{base + 8}" width="11" height="11" rx="2.5" fill="{c}"/>'
                     for i, c in enumerate(LEVELS))
    h = base + 46
    body = f"""
{frame(W, h)}
<text class="r" {d(0.6)} x="42" y="62" font-family="{SANS}" font-weight="600" font-size="30" letter-spacing="-.8" fill="{TEXT}">A year of shipping, <tspan fill="{GREEN}">in green</tspan></text>
<text class="f" {d(0.6)} x="{right}" y="60" text-anchor="end" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">UPDATED DAILY</text>
{''.join(cells)}
<g class="f" {d(2.2)}>{labels}
<text x="{lx - 8}" y="{base + 18}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{MUTED}">less</text>{legend}
<text x="{lx + len(LEVELS) * 14 + 2}" y="{base + 18}" font-family="{MONO}" font-size="11" fill="{MUTED}">more</text></g>
"""
    svg("heatmap.svg", W, h, body, ["bold", "mono"],
        f"Contribution graph: {data['total']:,} contributions in the last year")


# ---- monthly activity ------------------------------------------------------------------
def activity(data):
    h = 330
    monthly = data["monthly"][-12:]
    full = monthly[:-1] or monthly
    best = max(full, key=lambda m: m["total"])
    top = max(m["total"] for m in monthly)
    x0, x1, base, maxh, gap = 42, 590, 280, 130, 10
    bw = (x1 - x0 - gap * (len(monthly) - 1)) / len(monthly)
    bars = []
    for i, m in enumerate(monthly):
        partial = i == len(monthly) - 1
        bh = max(4, round(m["total"] / top * maxh))
        x = x0 + i * (bw + gap)
        fill = GREEN if m is best else (DIM if partial else "#c9d1d9")
        mon = dt.date.fromisoformat(m["month"] + "-01").strftime("%b")
        delay = 1.6 + i * 0.07
        bars.append(f'<rect class="g" {d(delay)} x="{x:.1f}" y="{base - bh}" width="{bw:.1f}" height="{bh}" rx="4" fill="{fill}">'
                    f'<title>{mon}: {m["total"]:,}</title></rect>'
                    f'<text class="f" {d(delay)} x="{x + bw / 2:.1f}" y="{base + 22}" text-anchor="middle" '
                    f'font-family="{MONO}" font-size="11" fill="{MUTED}">{mon}</text>')
        if m is best:
            bars.append(f'<text class="p" {d(2.6)} x="{x + bw / 2:.1f}" y="{base - bh - 10}" text-anchor="middle" '
                        f'font-family="{MONO}" font-size="11" fill="{GREEN}">{m["total"]:,}</text>')
    cur, longest = data["current_streak"], data["longest_streak"]
    if cur >= longest:
        streak = (f"{cur}", "day streak, and the longest yet")
    else:
        streak = (f"{longest}", f"day best streak · {cur} running now")
    stats = [
        (streak[0], streak[1]),
        (f'{data["active_days"]}<tspan fill="{MUTED}" font-weight="400"> / {len(data["days"])}</tspan>', "days with a contribution"),
        (f'{data["best_day"]["count"]}', "on the busiest day"),
    ]
    side = []
    for i, (big, small) in enumerate(stats):
        y = 96 + i * 88
        side.append(f'<g class="r" {d(2.0 + i * 0.15)}><text x="640" y="{y}" font-family="{SANS}" font-weight="600" '
                    f'font-size="36" letter-spacing="-1" fill="{TEXT}">{big}</text><text x="640" y="{y + 24}" '
                    f'font-family="{SANS}" font-size="13" fill="{MUTED}">{escape(small)}</text></g>')
        if i < 2:
            side.append(f'<rect class="f" {d(2.0)} x="640" y="{y + 42}" width="200" height="1" fill="{RULE}"/>')
    body = f"""
{frame(W, h)}
<text class="f" {d(1.3)} x="42" y="58" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">THE LAST 12 MONTHS ON GITHUB</text>
<text class="r" {d(1.4)} x="40" y="108" font-family="{SANS}" font-weight="600" font-size="44" letter-spacing="-1.5" fill="{TEXT}">{data["total"]:,} <tspan font-weight="400" fill="{SOFT}">contributions</tspan></text>
<line x1="610" y1="40" x2="610" y2="{h - 40}" stroke="{RULE}"/>
{''.join(bars)}
{''.join(side)}
"""
    svg("activity.svg", W, h, body, ["sans", "bold", "mono"],
        f"{data['total']:,} contributions in the last 12 months, best month {best['total']}")


# ---- featured repos ------------------------------------------------------------------
RW, RH = W / 3 - 8, 176


def repo_card(i, name, desc, info):
    lang = info.get("language") or "Code"
    meta = [lang]
    if info.get("stars"):
        meta.append(f"★ {info['stars']}")
    if info.get("homepage"):
        meta.append("live")
    delay = 3.6 + i * 0.12
    desc_lines = wrap(desc, 34)[:4]
    body = f"""
{frame(RW, RH)}
<g class="r" {d(delay)}>
  <circle cx="29" cy="34" r="5" fill="{LANG.get(lang, GREEN)}"/>
  <text x="42" y="39" font-family="{SANS}" font-weight="600" font-size="16.5" fill="{TEXT}">{escape(name[:26])}</text>
  {''.join(f'<text x="24" y="{70 + j * 20}" font-family="{SANS}" font-size="14" fill="{SOFT}">{escape(l)}</text>' for j, l in enumerate(desc_lines))}
  <text x="24" y="{RH - 22}" font-family="{MONO}" font-size="12" fill="{MUTED}">{escape('  ·  '.join(meta))}</text>
</g>
"""
    svg(f"repo-{name.lower()}.svg", RW, RH, body, ["sans", "bold", "mono"], f"{name}: {desc}",
        left=4 * i, right=8 - 4 * i)


def section_title(theme):
    fg, accent = (TEXT, GREEN) if theme == "dark" else ("#1f2328", "#00a650")
    body = (f'<text class="r" {d(3.4)} x="2" y="44" font-family="{SANS}" font-weight="600" font-size="28" '
            f'letter-spacing="-.6" fill="{fg}">What I\'m <tspan fill="{accent}">building</tspan></text>')
    svg(f"title-{theme}.svg", W, 60, body, ["bold"], "What I'm building", bottom=0)


if __name__ == "__main__":
    data = json.load(open(DATA, encoding="utf-8"))
    hero(data)
    heatmap(data)
    activity(data)
    tile("build", "BUILD", GREEN, str(data["projects"]), "projects",
         "Public and open source, from e-commerce stores to a gaming-cafe billing app.", 2.4, 0)
    stack_tile(2.6, 1)
    tile("work", "WORK", AMBER, str(data["years_on_github"]), "years",
         f"On GitHub since {data['member_since']}. Now full stack at Speedy Accounts, Raipur.", 2.8, 2)
    section_title("dark")
    section_title("light")
    for i, (name, desc) in enumerate(FEATURED):
        repo_card(i, name, desc, data["repos"].get(name, {}))
