"""Generates the profile SVG cards. Run: python3 build_svgs.py"""
import base64, pathlib

ROOT = pathlib.Path(__file__).parent
AV = base64.b64encode((ROOT / "assets/avatar.jpg").read_bytes()).decode()

import math, re

LOCAL_FONTS = ROOT / "assets/fonts"


def _font(name):
    f = LOCAL_FONTS / name
    return base64.b64encode(f.read_bytes()).decode()


FONTS = "".join(
    f"@font-face{{font-family:'{fam}';font-weight:{wt};src:url(data:font/woff2;base64,{_font(fn)}) format('woff2')}}"
    for fam, wt, fn in [
        ("SKSans", 500, "space-grotesk-latin-500-normal.woff2"),
        ("SKSans", 700, "space-grotesk-latin-700-normal.woff2"),
        ("SKMono", 400, "jetbrains-mono-latin-400-normal.woff2"),
        ("SKMono", 700, "jetbrains-mono-latin-700-normal.woff2"),
    ]
)

SANS = "'SKSans', 'Segoe UI', -apple-system, Helvetica, Arial, sans-serif"
MONO = "'SKMono', 'SF Mono', Consolas, Menlo, monospace"

BASE = FONTS + f"""
  .code {{ animation: codescroll 60s linear infinite; }}
  @keyframes codescroll {{ to {{ transform: translateY(-440px); }} }}
  .codeb {{ animation: codescroll 80s linear infinite reverse; }}
  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; opacity: 1 !important; }} }}
  .bg {{ fill: #0e0f13; }}
  .panel {{ fill: #15171d; stroke: #262a35; stroke-width: 1; }}
  .grid {{ stroke: #1c1f27; stroke-width: 1; }}
  .ink {{ fill: #ece9e1; font-family: {SANS}; }}
  .muted {{ fill: #8b8f9c; font-family: {SANS}; }}
  .mono {{ font-family: {MONO}; }}
  .amber {{ fill: #f5b544; }} .teal {{ fill: #4fd1c5; }} .coral {{ fill: #ff7a6b; }} .violet {{ fill: #a99bff; }}
  .fade {{ opacity: 0; animation: fade .8s ease forwards; }}
  @keyframes fade {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
  .draw {{ stroke-dasharray: 1200; stroke-dashoffset: 1200; animation: draw 2.4s ease forwards; }}
  @keyframes draw {{ to {{ stroke-dashoffset: 0; }} }}
  .blink {{ animation: blink 1s steps(1) infinite; }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
  .pulse {{ animation: pulse 1.8s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
  @keyframes pulse {{ 0%,100% {{ opacity: 1; transform: scale(1); }} 50% {{ opacity: .35; transform: scale(1.6); }} }}
"""


CODE = [
    "const shubham = {",
    "  role: \"Full Stack Developer\",",
    "  stack: [\"Next.js\", \"Node.js\", \"PostgreSQL\"],",
    "  focus: \"AI-powered SaaS\",",
    "};",
    "",
    "export async function ship(idea: Idea) {",
    "  const journey = await map(idea.users);",
    "  const system = design(journey, { tokens });",
    "  return build(system).deploy(\"aws\");",
    "}",
    "",
    "// lighthouse: 62 -> 91",
    "app.get(\"/api/jobs\", auth(\"employer\"), list);",
    "await db.tx(async (t) => {",
    "  await t.stock.deduct(cart);",
    "  await t.ledger.append(sale);",
    "});",
    "<Dashboard theme=\"dark\" ai />",
    "git push origin main  # shipped",
]
KW = r"\b(const|export|async|function|await|return|import|from|type|interface)\b"
TOK = re.compile(r'(//.*|#.*)|("[^"]*")|' + KW + r'|(\b\d+\b)|(<\/?\w+|\/>|=>)|(\b\w+(?=\())')
COLORS = {1: "#5c6170", 2: "#4fd1c5", 3: "#ff7a6b", 4: "#f5b544", 5: "#a99bff", 6: "#7aa2ff"}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def code_line(s):
    out, i = "", 0
    for m in TOK.finditer(s):
        out += esc(s[i:m.start()])
        g = next(k for k in range(1, 7) if m.group(k))
        out += f'<tspan fill="{COLORS[g]}">{esc(m.group(0))}</tspan>'
        i = m.end()
    return out + esc(s[i:])


def code_bg(w, h):
    """Faint, slowly scrolling editor text with line numbers — two columns."""
    lh = 22
    reps = (h // (lh * len(CODE))) + 3
    def column(x, offset, cls):
        rows = ""
        lines = CODE[offset:] + CODE[:offset]
        for n in range(len(lines) * reps):
            y = 30 + n * lh
            rows += (f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="12" fill="#3a3f4d">{(n % 99) + 1:>2}</text>'
                     f'<text x="{x + 30}" y="{y}" font-family="{MONO}" font-size="12" fill="#8b8f9c">{code_line(lines[n % len(lines)])}</text>')
        return f'<g class="{cls}">{rows}</g>'
    return (f'<g opacity=".16">{column(28, 0, "code")}{column(w // 2 + 40, 9, "codeb")}</g>'
            f'<rect width="{w}" height="{h}" fill="url(#veil)"/>')


def floor(w, h, depth=110, color="#4fd1c5", n=9, dur=4):
    """Synthwave-style perspective grid floor moving toward the viewer."""
    y0, vx = h - depth, w / 2
    g = f'<g opacity=".5"><line x1="0" y1="{y0}" x2="{w}" y2="{y0}" stroke="{color}" stroke-opacity=".5"/>'
    for x in range(-w, 2 * w + 1, 90):
        g += f'<line x1="{vx + (x - vx) * .12:.1f}" y1="{y0}" x2="{x}" y2="{h}" stroke="{color}" stroke-opacity=".35"/>'
    ys = ";".join(f"{y0 + depth * (k / 12) ** 2:.1f}" for k in range(13))
    for i in range(n):
        b = -dur * i / n
        g += (f'<line x1="0" x2="{w}" y1="{y0}" y2="{y0}" stroke="{color}" stroke-opacity=".55">'
              f'<animate attributeName="y1" values="{ys}" dur="{dur}s" begin="{b:.2f}s" repeatCount="indefinite"/>'
              f'<animate attributeName="y2" values="{ys}" dur="{dur}s" begin="{b:.2f}s" repeatCount="indefinite"/>'
              f'<animate attributeName="opacity" values="0;.6;1" dur="{dur}s" begin="{b:.2f}s" repeatCount="indefinite"/></line>')
    return g + f'</g><rect x="0" y="{y0}" width="{w}" height="{depth}" fill="url(#floorfade)"/>'


def _ico():
    p = (1 + 5 ** .5) / 2
    v = [(-1, p, 0), (1, p, 0), (-1, -p, 0), (1, -p, 0), (0, -1, p), (0, 1, p), (0, -1, -p), (0, 1, -p),
         (p, 0, -1), (p, 0, 1), (-p, 0, -1), (-p, 0, 1)]
    e = sorted({tuple(sorted((i, j))) for i in range(12) for j in range(12)
                if i != j and abs(sum((a - b) ** 2 for a, b in zip(v[i], v[j])) - 4) < 1e-6})
    return v, e


def _sphere(lat=6, lon=12):
    v, e = [], []
    for i in range(1, lat):
        th = math.pi * i / lat
        for j in range(lon):
            ph = 2 * math.pi * j / lon
            v.append((math.sin(th) * math.cos(ph), math.cos(th), math.sin(th) * math.sin(ph)))
    for i in range(lat - 1):
        for j in range(lon):
            a = i * lon + j
            e.append((a, i * lon + (j + 1) % lon))
            if i < lat - 2:
                e.append((a, a + lon))
    top, bot = len(v), len(v) + 1
    v += [(0, 1, 0), (0, -1, 0)]
    e += [(top, j) for j in range(lon)] + [(bot, (lat - 2) * lon + j) for j in range(lon)]
    return v, e


def wire3d(cx, cy, r, shape="ico", frames=60, dur=14, stroke="url(#sun)", width=1.6, tilt=.45):
    """True 3D wireframe rotating on its Y axis, rendered as SMIL path frames."""
    v, e = _ico() if shape == "ico" else _sphere()
    scale = r / max(math.sqrt(x * x + y * y + z * z) for x, y, z in v)
    ds = []
    for f in range(frames + 1):
        a = 2 * math.pi * f / frames
        pts = []
        for x, y, z in v:
            x, z = x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)
            y, z = y * math.cos(tilt) - z * math.sin(tilt), y * math.sin(tilt) + z * math.cos(tilt)
            k = 3.2 / (3.2 + z * scale / r)
            pts.append((cx + x * scale * k, cy - y * scale * k))
        ds.append(" ".join(f"M{pts[i][0]:.1f} {pts[i][1]:.1f}L{pts[j][0]:.1f} {pts[j][1]:.1f}" for i, j in e))
    return (f'<path d="{ds[0]}" fill="none" stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" opacity=".9">'
            f'<animate attributeName="d" values="{";".join(ds)}" dur="{dur}s" repeatCount="indefinite"/></path>')


def svg(w, h, body, extra_css="", label=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{label}">
<style>{BASE}{extra_css}</style>
<defs>
  <clipPath id="frame"><rect x="0" y="0" width="{w}" height="{h}" rx="22"/></clipPath>
  <linearGradient id="sun" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#f5b544"/><stop offset=".55" stop-color="#ff7a6b"/><stop offset="1" stop-color="#a99bff"/></linearGradient>
  <linearGradient id="sea" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#4fd1c5"/><stop offset="1" stop-color="#a99bff"/></linearGradient>
  <linearGradient id="trailg" gradientUnits="userSpaceOnUse" x1="90" y1="0" x2="1110" y2="0"><stop offset="0" stop-color="#8b8f9c"/><stop offset=".5" stop-color="#4fd1c5"/><stop offset=".8" stop-color="#f5b544"/><stop offset="1" stop-color="#34d399"/></linearGradient>
  <linearGradient id="veil" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0e0f13" stop-opacity=".2"/><stop offset=".5" stop-color="#0e0f13" stop-opacity=".55"/><stop offset="1" stop-color="#0e0f13" stop-opacity=".2"/></linearGradient>
  <linearGradient id="floorfade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0e0f13" stop-opacity=".9"/><stop offset=".5" stop-color="#0e0f13" stop-opacity=".2"/><stop offset="1" stop-color="#0e0f13" stop-opacity="0"/></linearGradient>
  <radialGradient id="aurora" cx=".8" cy="0" r=".9"><stop offset="0" stop-color="#a99bff" stop-opacity=".16"/><stop offset="1" stop-color="#a99bff" stop-opacity="0"/></radialGradient>
  <radialGradient id="glow" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#f5b544" stop-opacity=".22"/><stop offset="1" stop-color="#f5b544" stop-opacity="0"/></radialGradient>
</defs>
<g clip-path="url(#frame)">
<rect class="bg" width="{w}" height="{h}"/>
{code_bg(w, h)}
<rect width="{w}" height="{h}" fill="url(#aurora)"/>
{body}
</g>
<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="22" fill="none" stroke="#262a35"/>
</svg>"""


WRITE = __name__ == "__main__"


def write(name, content):
    if not WRITE:
        return
    (ROOT / name).write_text(content, encoding="utf-8")
    print("wrote", name, len(content) // 1024, "KB")


# ---------------------------------------------------------------- HERO
hero_css = """
  .ring { transform-origin: 250px 230px; animation: spin 24s linear infinite; }
  .ring2 { transform-origin: 250px 230px; animation: spin 36s linear infinite reverse; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .role { opacity: 0; animation: roles 9s infinite; }
  .r2 { animation-delay: 3s; } .r3 { animation-delay: 6s; }
  @keyframes roles { 0% { opacity: 0; transform: translateY(10px); } 4%,30% { opacity: 1; transform: translateY(0); } 34%,100% { opacity: 0; transform: translateY(-10px); } }
  .float { animation: float 6s ease-in-out infinite; }
  @keyframes float { 50% { transform: translateY(-6px); } }
"""
hero_body = f"""
{floor(1200, 440, depth=96, color="#f5b544")}
<circle cx="250" cy="230" r="260" fill="url(#glow)"/>
{wire3d(1112, 92, 44, "ico", dur=16)}
<!-- construction lines, like a sketch being laid out -->
<path class="draw" d="M40 70 H1160 M40 390 H1160 M520 40 V400" stroke="#2b2f3b" stroke-width="1" stroke-dasharray="4 6" fill="none"/>
<g class="ring"><circle cx="250" cy="230" r="158" fill="none" stroke="url(#sun)" stroke-width="2" stroke-dasharray="2 10" stroke-linecap="round"/></g>
<g class="ring2"><circle cx="250" cy="230" r="172" fill="none" stroke="#2f3442" stroke-width="1" stroke-dasharray="40 14"/>
  <circle cx="250" cy="58" r="5" fill="#4fd1c5"/></g>
<clipPath id="av"><circle cx="250" cy="230" r="140"/></clipPath>
<circle cx="250" cy="230" r="141" fill="#f4f2ec"/>
<image href="data:image/jpeg;base64,{AV}" xlink:href="data:image/jpeg;base64,{AV}" x="110" y="90" width="280" height="280" clip-path="url(#av)" preserveAspectRatio="xMidYMid slice"/>
<g class="float">
  <rect x="330" y="322" width="150" height="36" rx="18" fill="#15171d" stroke="#3a3f4d"/>
  <circle class="pulse" cx="352" cy="340" r="5" fill="#34d399"/>
  <text x="366" y="345" class="ink mono" font-size="13">open to work</text>
</g>

<text x="570" y="128" class="muted mono fade" font-size="16" style="animation-delay:.1s">&lt;hello world=&quot;Indore, India&quot; /&gt;</text>
<text x="566" y="196" class="ink fade" font-size="62" font-weight="800" letter-spacing="-1.5" style="animation-delay:.3s">Shubham <tspan fill="url(#sun)">Kanungo</tspan></text>

<g class="mono" font-size="22">
  <text x="570" y="246" class="teal">&gt;</text>
  <text x="594" y="246" class="ink role r1">Full Stack Web Application Developer</text>
  <text x="594" y="246" class="ink role r2">Technical Product Designer · UI/UX</text>
  <text x="594" y="246" class="ink role r3">Lead Frontend Engineer · AI SaaS</text>
</g>
<text x="570" y="294" class="muted fade" font-size="19" font-style="italic" style="animation-delay:.6s">Designing with code. Architecting with empathy.</text>

<g class="fade" style="animation-delay:.9s" font-size="14">
  <rect x="570" y="322" width="118" height="34" rx="17" fill="none" stroke="#f5b544"/><text x="629" y="344" text-anchor="middle" class="amber mono">7+ years</text>
  <rect x="700" y="322" width="168" height="34" rx="17" fill="none" stroke="#4fd1c5"/><text x="784" y="344" text-anchor="middle" class="teal mono">React · Next · Node</text>
  <rect x="880" y="322" width="142" height="34" rx="17" fill="none" stroke="#a99bff"/><text x="951" y="344" text-anchor="middle" class="violet mono">AI / LLM SaaS</text>
</g>
"""
write("hero.svg", svg(1200, 440, hero_body, hero_css, "Hi, I'm Shubham Kanungo, Full Stack Web Application Developer"))

# ---------------------------------------------------------------- ABOUT + HOW I WORK
about_css = """
  .step { opacity: .35; animation: step 10s infinite; }
  .s2 { animation-delay: 2s; } .s3 { animation-delay: 4s; } .s4 { animation-delay: 6s; } .s5 { animation-delay: 8s; }
  @keyframes step { 0%,18% { opacity: 1; } 22%,100% { opacity: .35; } }
  .runner { animation: run 10s linear infinite; }
  @keyframes run { from { transform: translateX(0); } to { transform: translateX(440px); } }
"""
build_items = [
    ("#f5b544", "Enterprise AI SaaS", "OCR + LLM pipelines that turn documents into data"),
    ("#4fd1c5", "Full-stack products", "Next.js · Node.js · PostgreSQL · AWS, owned end to end"),
    ("#ff7a6b", "Secure platforms", "JWT, RBAC, OTP, audit logs, payment flows"),
    ("#a99bff", "Design systems", "Component architecture that scales with the team"),
]
rows = ""
for i, (c, t, d) in enumerate(build_items):
    y = 128 + i * 66
    rows += f"""<g class="fade" style="animation-delay:{.2 + i * .15}s">
  <rect x="48" y="{y - 22}" width="36" height="36" rx="10" fill="{c}" fill-opacity=".14" stroke="{c}"/>
  <text x="66" y="{y + 2}" text-anchor="middle" class="mono" font-size="14" fill="{c}">0{i + 1}</text>
  <text x="100" y="{y - 4}" class="ink" font-size="18" font-weight="700">{t}</text>
  <text x="100" y="{y + 18}" class="muted" font-size="14">{d}</text></g>"""

steps = [("Journey", "map the friction"), ("Wireframe", "sketch the flow"), ("System", "tokens + parts"),
         ("Build", "type-safe code"), ("Ship", "measure, iterate")]
stp = ""
for i, (t, d) in enumerate(steps):
    x = 676 + i * 110
    stp += f"""<g class="step s{i + 1}">
  <circle cx="{x}" cy="196" r="22" fill="#15171d" stroke="url(#sun)" stroke-width="2"/>
  <text x="{x}" y="201" text-anchor="middle" class="ink mono" font-size="14" font-weight="700">{i + 1}</text>
  <text x="{x}" y="244" text-anchor="middle" class="ink" font-size="15" font-weight="700">{t}</text>
  <text x="{x}" y="264" text-anchor="middle" class="muted" font-size="12">{d}</text></g>"""

about_body = f"""
<rect class="panel" x="24" y="24" width="566" height="352" rx="18"/>
<text x="48" y="66" class="muted mono" font-size="13">// what_i_build.tsx</text>
{rows}
<rect class="panel" x="610" y="24" width="566" height="352" rx="18"/>
<text x="634" y="66" class="muted mono" font-size="13">// how_i_work.md</text>
<text x="634" y="110" class="ink" font-size="24" font-weight="800">I design the product <tspan class="amber">and</tspan> I build it.</text>
<text x="634" y="138" class="muted" font-size="15">One owner across the whole lifecycle — no handoff gaps.</text>
<line x1="676" y1="196" x2="1116" y2="196" stroke="#2f3442" stroke-width="2" stroke-dasharray="3 6"/>
<g class="runner"><circle cx="676" cy="196" r="5" fill="#4fd1c5"/></g>
{stp}
<g font-size="13" class="mono">
  <rect x="634" y="300" width="160" height="50" rx="12" fill="#f5b544" fill-opacity=".08" stroke="#3a3f4d"/>
  <text x="650" y="321" class="muted">Lead</text><text x="650" y="340" class="amber">frontend team</text>
  <rect x="806" y="300" width="160" height="50" rx="12" fill="#4fd1c5" fill-opacity=".08" stroke="#3a3f4d"/>
  <text x="822" y="321" class="muted">Run</text><text x="822" y="340" class="teal">code reviews</text>
  <rect x="978" y="300" width="174" height="50" rx="12" fill="#a99bff" fill-opacity=".08" stroke="#3a3f4d"/>
  <text x="994" y="321" class="muted">Mentor</text><text x="994" y="340" class="violet">junior developers</text>
</g>
"""
write("about.svg", svg(1200, 400, about_body, about_css, "What I build and how I work"))

# ---------------------------------------------------------------- STACK
stack_css = """
  .shine { animation: shine 5s ease-in-out infinite; }
  @keyframes shine { 0%,100% { opacity: .9; } 50% { opacity: 1; } }
  .chip { opacity: 0; animation: fade .5s ease forwards; }
"""
groups = [
    ("Frontend", "#f5b544", ["React.js", "Next.js 14+", "TypeScript", "JavaScript", "Tailwind CSS", "Framer Motion", "Expo / RN"]),
    ("Backend", "#4fd1c5", ["Node.js", "Express.js", "REST APIs", "Zod", "PHP · Laravel", "Razorpay", "Zoom API"]),
    ("Data & Cloud", "#ff7a6b", ["PostgreSQL", "MySQL", "AWS RDS", "S3 · CloudFront", "SES", "Elastic Beanstalk", "Amplify"]),
    ("AI & Security", "#a99bff", ["LLM integration", "OCR pipelines", "AI agent UX", "JWT", "NextAuth", "RBAC", "OTP"]),
    ("Design & UI", "#ece9e1", ["Figma", "Material UI", "Wireframing", "Prototyping", "Design systems", "User journeys", "Usability testing"]),
]
CH_W = 8.6  # approx px per char at 14px
st = '<text x="48" y="64" class="muted mono" font-size="13">// stack.json</text>'
st += '<text x="1152" y="64" text-anchor="end" class="muted mono" font-size="13">ship it with what fits the problem</text>'
delay = 0
for gi, (name, col, items) in enumerate(groups):
    y = 112 + gi * 62
    st += f'<text x="48" y="{y + 5}" class="mono" font-size="14" font-weight="700" fill="{col}">{name.replace("&","&amp;")}</text>'
    x = 200
    for it in items:
        w = int(len(it) * CH_W + 30)
        st += f'''<g class="chip" style="animation-delay:{delay:.2f}s"><rect x="{x}" y="{y - 17}" width="{w}" height="32" rx="9" fill="{col}" fill-opacity=".07" stroke="{col}" stroke-opacity=".55"/>
<text x="{x + w / 2}" y="{y + 4}" text-anchor="middle" class="ink" font-size="14">{it}</text></g>'''
        x += w + 10
        delay += .04
write("stack.svg", svg(1200, 420, st, stack_css, "Tech stack"))

# ---------------------------------------------------------------- ID + DASHBOARD
id_css = """
  .gauge { stroke-dasharray: 251; stroke-dashoffset: 251; animation: g 2.2s ease-out .4s forwards; }
  @keyframes g { to { stroke-dashoffset: 22.6; } }
  .bar { transform-box: fill-box; transform-origin: left; transform: scaleX(0); animation: bar 1.8s ease-out .6s forwards; }
  @keyframes bar { to { transform: scaleX(1); } }
  .scan { animation: scan 3.5s ease-in-out infinite; }
  @keyframes scan { 0%,100% { transform: translateY(0); } 50% { transform: translateY(300px); } }
  .swing { transform-origin: 224px -10px; animation: swing 6s ease-in-out infinite; }
  @keyframes swing { 0%,100% { transform: rotate(1.6deg) skewY(-.6deg); } 50% { transform: rotate(-1.6deg) skewY(.6deg); } }
  .num { opacity: 0; animation: fade .6s ease forwards 1.6s; }
"""
bars = ""
import random
random.seed(7)
x = 64
while x < 380:
    w = random.choice([2, 2, 3, 4, 6])
    bars += f'<rect x="{x}" y="372" width="{w}" height="30" fill="#ece9e1"/>'
    x += w + random.choice([2, 3, 4])

id_body = f"""
<!-- developer ID card -->
<g class="swing">
<path d="M200 -10 L214 24 M248 -10 L234 24" stroke="url(#sun)" stroke-width="6" stroke-linecap="round"/>
<rect x="24" y="24" width="400" height="402" rx="20" fill="#f4f2ec"/>
<path d="M44 24 H404 A20 20 0 0 1 424 44 V98 H24 V44 A20 20 0 0 1 44 24 Z" fill="url(#sun)"/>
<text x="48" y="58" font-family="{MONO}" font-size="13" fill="#0e0f13" font-weight="700">DEVELOPER ID</text>
<text x="400" y="58" text-anchor="end" font-family="{MONO}" font-size="13" fill="#0e0f13">SK-2016-IND</text>
<rect x="48" y="118" width="120" height="140" rx="12" fill="#fff" stroke="#d9d5ca"/>
<clipPath id="idav"><rect x="52" y="122" width="112" height="132" rx="9"/></clipPath>
<image href="data:image/jpeg;base64,{AV}" xlink:href="data:image/jpeg;base64,{AV}" x="40" y="118" width="136" height="136" clip-path="url(#idav)" preserveAspectRatio="xMidYMid slice"/>
<g font-family="{SANS}" fill="#0e0f13">
  <text x="188" y="142" font-size="11" fill="#7a7768" font-family="{MONO}">NAME</text>
  <text x="188" y="164" font-size="21" font-weight="800">Shubham Kanungo</text>
  <text x="188" y="192" font-size="11" fill="#7a7768" font-family="{MONO}">ROLE</text>
  <text x="188" y="210" font-size="14" font-weight="600">Full Stack Developer</text>
  <text x="188" y="238" font-size="11" fill="#7a7768" font-family="{MONO}">BASE</text>
  <text x="188" y="256" font-size="14" font-weight="600">Indore, India · Remote OK</text>
</g>
<line x1="48" y1="282" x2="400" y2="282" stroke="#d9d5ca" stroke-dasharray="4 4"/>
<g font-family="{MONO}" font-size="12" fill="#0e0f13">
  <text x="48" y="308" fill="#7a7768">CLEARANCE</text><text x="160" y="308" font-weight="700">Frontend · Backend · UX</text>
  <text x="48" y="332" fill="#7a7768">EDU</text><text x="160" y="332" font-weight="700">B.E. IT · UIT RGPV</text>
  <text x="48" y="356" fill="#7a7768">STATUS</text><circle cx="166" cy="352" r="4.5" fill="#16a34a" class="pulse"/><text x="178" y="356" font-weight="700" fill="#15803d">Immediate joiner</text>
</g>
<rect x="56" y="366" width="336" height="42" rx="6" fill="#0e0f13"/>
{bars}
<rect class="scan" x="24" y="96" width="400" height="2" fill="#ff7a6b" opacity=".55"/>
</g>

<!-- dashboard -->
<text x="456" y="56" class="muted mono" font-size="13">// impact.dashboard — outcomes, not deliverables</text>

<rect class="panel" x="452" y="74" width="352" height="170" rx="16"/>
<text x="476" y="104" class="muted mono" font-size="12">LIGHTHOUSE PERFORMANCE</text>
<circle cx="560" cy="180" r="40" fill="none" stroke="#262a35" stroke-width="10"/>
<circle class="gauge" cx="560" cy="180" r="40" fill="none" stroke="#34d399" stroke-width="10" stroke-linecap="round" transform="rotate(-90 560 180)"/>
<text x="560" y="188" text-anchor="middle" class="ink" font-size="24" font-weight="800">91</text>
<text x="630" y="166" class="muted" font-size="14">from</text>
<text x="630" y="196" class="ink" font-size="30" font-weight="800"><tspan class="coral">62</tspan> → <tspan fill="#34d399">91</tspan></text>
<text x="630" y="220" class="muted" font-size="13">SSR + lazy-loaded states</text>

<rect class="panel" x="820" y="74" width="356" height="170" rx="16"/>
<text x="844" y="104" class="muted mono" font-size="12">AUDIT FRICTION · AI WORKFLOW</text>
<text x="844" y="160" class="amber" font-size="52" font-weight="800">−70%</text>
<rect x="844" y="190" width="308" height="12" rx="6" fill="#262a35"/>
<rect class="bar" x="844" y="190" width="216" height="12" rx="6" fill="url(#sun)"/>
<text x="844" y="226" class="muted" font-size="13">1-click OCR + LLM GHG-scope classification</text>

<rect class="panel" x="452" y="256" width="232" height="170" rx="16"/>
<text x="476" y="286" class="muted mono" font-size="12">HIRING LIFECYCLE</text>
<text x="476" y="356" class="teal" font-size="56" font-weight="800">2.4×</text>
<text x="476" y="392" class="muted" font-size="13">faster · Jobstm</text>

<rect class="panel" x="696" y="256" width="232" height="170" rx="16"/>
<text x="720" y="286" class="muted mono" font-size="12">CHECKOUT TIME</text>
<text x="720" y="356" class="violet" font-size="56" font-weight="800">&lt;10s</text>
<text x="720" y="392" class="muted" font-size="13">POS flow · Sole &amp; Ledger</text>

<rect class="panel" x="940" y="256" width="236" height="170" rx="16"/>
<text x="964" y="286" class="muted mono" font-size="12">PRODUCER REVENUE</text>
<text x="964" y="356" class="coral" font-size="56" font-weight="800">+35%</text>
<text x="964" y="392" class="muted" font-size="13">farm-to-home · Aadidhara</text>
"""
write("id-dashboard.svg", svg(1200, 450, id_body, id_css, "Developer ID and impact dashboard"))

# ---------------------------------------------------------------- JOURNEY TIMELINE
jr_css = """
  .node { opacity: 0; animation: fade .6s ease forwards; }
  .trail { stroke-dasharray: 1100; stroke-dashoffset: 1100; animation: draw 3s ease forwards; }
"""
jobs = [
    ("2016", "Hello, World", "HTML · CSS · JavaScript", "#8b8f9c"),
    ("2018", "Backend era", "PHP · Laravel · MySQL", "#a99bff"),
    ("2020", "Web apps", "dashboards · data models", "#ff7a6b"),
    ("2021", "Full-stack JS", "React · Node.js · REST", "#4fd1c5"),
    ("2024", "AI + Next.js", "TypeScript · SSR · LLMs", "#f5b544"),
    ("2026", "AI Agents", "agents · AI automation", "#34d399"),
]
jr = '<text x="48" y="60" class="muted mono" font-size="13">// git log --stack --oneline</text>'
jr += '<path class="trail" d="M90 170 H1110" stroke="url(#trailg)" stroke-width="3" fill="none" stroke-linecap="round"/>'
for i, (yr, co, role, c) in enumerate(jobs):
    x = 90 + i * 204
    last = i == len(jobs) - 1
    dash = ' stroke-dasharray="4 4"' if last else ""
    jr += f"""<g class="node" style="animation-delay:{.3 + i * .35}s">
  <circle cx="{x}" cy="170" r="13" fill="#0e0f13" stroke="{c}" stroke-width="3"{dash}/>
  <circle cx="{x}" cy="170" r="5" fill="{c}"{' class="pulse"' if last else ''}/>
  <text x="{x}" y="132" text-anchor="middle" class="mono" font-size="15" font-weight="700" fill="{c}">{yr}</text>
  <text x="{x}" y="214" text-anchor="middle" class="ink" font-size="17" font-weight="700">{co}</text>
  <text x="{x}" y="238" text-anchor="middle" class="muted" font-size="13">{role}</text></g>"""
jr = floor(1200, 280, depth=70, color="#a99bff") + jr
write("journey.svg", svg(1200, 280, jr, jr_css, "Career timeline"))

# ---------------------------------------------------------------- CONNECT
cn_css = """
  .wave { animation: wave 2.4s ease-in-out infinite; transform-box: fill-box; transform-origin: 70% 80%; }
  @keyframes wave { 0%,60%,100% { transform: rotate(0); } 10%,30% { transform: rotate(14deg); } 20%,40% { transform: rotate(-8deg); } }
  .spin { transform-origin: 1050px 130px; animation: sp 18s linear infinite; }
  @keyframes sp { to { transform: rotate(360deg); } }
  .cta { animation: cta 3s ease-in-out infinite; }
  @keyframes cta { 50% { opacity: .75; } }
"""
cn = floor(1200, 260, depth=70, color="#ff7a6b") + f"""
<circle cx="1050" cy="120" r="220" fill="url(#glow)"/>
<text x="56" y="74" class="muted mono" font-size="14">// let's_collaborate()</text>
<text x="56" y="126" class="ink" font-size="38" font-weight="800">Have a product that needs to <tspan fill="url(#sun)">feel effortless?</tspan></text>
<text x="56" y="164" class="muted" font-size="17">Immediate joiner · open to remote, hybrid and on-site roles.</text>
<g class="cta">
  <rect x="56" y="188" width="360" height="44" rx="22" fill="url(#sun)"/>
  <text x="236" y="216" text-anchor="middle" font-family="{MONO}" font-size="15" font-weight="700" fill="#0e0f13">shubhamkanungo.vercel.app ↗</text>
</g>
{wire3d(1050, 130, 100, "sphere", dur=18, width=1.1)}
<circle cx="1050" cy="130" r="66" fill="#15171d" stroke="#3a3f4d"/>
<text x="1050" y="150" text-anchor="middle" class="ink" font-size="54" font-weight="800" letter-spacing="-2">S<tspan fill="url(#sun)">K</tspan></text>
<g class="wave"><circle cx="1116" cy="74" r="8" fill="#34d399"/></g>
"""
write("connect.svg", svg(1200, 260, cn, cn_css, "Let's connect"))
