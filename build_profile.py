#!/usr/bin/env python3
"""
Builds the black futuristic profile dashboard for github.com/LoPedrozo.
(Design adapted from github.com/aslamrekik, electric-blue theme.)

Outputs (in ./profile):
  dashboard.svg      the whole profile as one animated SVG
  btn-*.svg          clickable buttons shown under it in README.md

Live data comes from the GitHub GraphQL API (env GH_TOKEN, needs read:user).
If the token is missing or a call fails, fallback values are used so the
build never breaks. Standard library only: no pip install needed.
"""
import base64, datetime as dt, json, math, os, textwrap, urllib.request
from xml.sax.saxutils import escape

# Works with a flat repo (all files in the root) or with scripts/ + profile/ folders
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == "scripts" else HERE
OUT = os.path.join(ROOT, "profile") if os.path.isdir(os.path.join(ROOT, "profile")) else ROOT
ICONS = os.path.join(HERE, "icons.json")
USER = os.environ.get("GH_USER", "LoPedrozo")
TOKEN = os.environ.get("GH_TOKEN", "")

# ── palette (electric blue) ─────────────────────────────────────────────
BG, SURF, SURF2 = "#000000", "#04070B", "#07111C"
LINE, OXB, BURG = "#0C2236", "#0E2A44", "#0B4F8A"
WINE, CRIM, BLUSH = "#1E7FD6", "#00B4FF", "#D2F1FF"
MUTED, DIM = "#9EC3D9", "#557489"
DEEP, HDR = "#0A3A66", "#0A1E30"
MONO = "'JetBrains Mono','Fira Code','Cascadia Code',Consolas,'DejaVu Sans Mono','Courier New',monospace"
W, PAD = 1000, 40
CW = W - 2 * PAD  # content width

# ── content ──────────────────────────────────────────────────────────────
NAME = "LORENZO PEDROZO"
ROLES = "FULL-STACK DEVELOPER // PROJECT MANAGER // TECH INTERN @ MBRF"
STATUS = "> status: working at MBRF & building full-stack apps in Curitiba"
# 3D symbol in the header. AI: neural, robot, chat, sparkle, chip.
# Frontend: atom, brackets, browser, layers. Full-stack & personal: database, football, monogram.
# Geometric: icosahedron, dodecahedron, octahedron, tetrahedron, cube, tesseract, pyramid, star,
# prism, gem, globe, torus, geodesic, mobius, dna. Advanced: hypercube (4D), knot, sierpinski.
SHAPE = "robot"
PROFILE = [
    ("user", "Lorenzo Garcia Pedrozo"),
    ("role", "Full-Stack Developer (in training)"),
    ("", "Project Manager @ LIGA APP"),
    ("now", "Technology Intern @ MBRF · Logistics Projects"),
    ("education", "Software Engineering @ Universidade Positivo → 2028"),
    ("base", "Curitiba, Brazil"),
    ("languages", "[ Portuguese, English ]"),
    ("core_stack", "React · TypeScript · C# / .NET · Python"),
    ("focus", "full-stack web · project management · UI/UX"),
    ("motto", "learn by building → ship it → iterate"),
]
PROJECTS = [
    dict(title="LIGA APP", tag="PROJECT MANAGER · MVP OCT 2026", wide=True,
         desc="MVP for Formigueiro Metais, a metals company: calculates and corrects the chemical composition of "
              "secondary aluminium alloys, with AI-generated explanations. As project manager I co-lead a 9-person "
              "team in Scrumban: client relationship, sprint ceremonies, code review, QA and deploy.",
         stack="React · TypeScript · FastAPI · Supabase · SciPy · Gemini"),
    dict(title="NOVANT FOOTBALL GEAR", tag="E-COMMERCE · DEPLOYED", wide=True,
         desc="E-commerce SPA for football gear: dynamic product catalog, hybrid cart synchronization "
              "(guest + logged-in), OAuth authentication and a responsive checkout flow. Deployed on Vercel.",
         stack="React · TypeScript · Supabase · Tailwind · Vercel"),
    dict(title="MINHAS FINANÇAS", tag="FINTECH · DASHBOARD",
         desc="Personal finance dashboard with interactive charts, categorized entries and Row Level "
              "Security so every user only sees their own data.",
         stack="React · TypeScript · Supabase · PostgreSQL · Recharts"),
    dict(title="FADARY BEAUTY SHOWCASE", tag="UI / UX",
         desc="Responsive institutional website for a beauty brand, focused on reusable components "
              "and smooth animations.",
         stack="React · TypeScript · Tailwind · Framer Motion · Vite"),
    dict(title="TASK MANAGEMENT API", tag="BACKEND", wide=True,
         desc="Modular RESTful API with full CRUD, database integration and clear separation of "
              "concerns between layers.",
         stack="C# · ASP.NET Core · Entity Framework · SQLite"),
]
PRINCIPLES = [
    ("LEARN BY BUILDING", "every new concept turns into a real, deployed project"),
    ("END-TO-END OWNERSHIP", "from React/TS interfaces to C# REST APIs and a real database"),
    ("SHIP AS A TEAM", "clear roles, sprint rituals, code review and QA before every deploy"),
    ("UI THAT FEELS GOOD", "responsive layouts, reusable components and smooth motion"),
]
BUTTONS = [  # (file, label) — links live in README.md
    ("btn-linkedin", "LINKEDIN ↗"), ("btn-email", "EMAIL ↗"),
    ("btn-novant", "NOVANT ↗"), ("btn-financas", "FINANÇAS ↗"), ("btn-tarefas", "TASK API ↗"), ("btn-fadary", "FADARY ↗"),
]
LANG_HIDE = {"HTML", "CSS", "Jupyter Notebook", "Dockerfile", "Batchfile", "Shell", "PowerShell", "PLpgSQL"}

FALLBACK = dict(total=0, cur=0, longest=0, commits=0, prs=0, repos=0, stars=0,
                langs=[("TypeScript", 60.0), ("C#", 20.0), ("JavaScript", 15.0), ("Python", 5.0)],
                days=[])


# ── data ─────────────────────────────────────────────────────────────────
def gql(query, variables=None):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "User-Agent": "profile-builder"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if body.get("errors"):
        raise RuntimeError(body["errors"])
    return body["data"]


def fetch():
    d = dict(FALLBACK)
    if not TOKEN:
        print("no token: using fallback data")
        return d
    try:
        u = gql("""query($l:String!){user(login:$l){createdAt
          pullRequests{totalCount}
          repositories(ownerAffiliations:OWNER,isFork:false,first:100,privacy:PUBLIC){totalCount
            nodes{stargazerCount languages(first:10,orderBy:{field:SIZE,direction:DESC}){edges{size node{name}}}}}}}""",
                {"l": USER})["user"]
        d["prs"] = u["pullRequests"]["totalCount"]
        d["repos"] = u["repositories"]["totalCount"]
        d["stars"] = sum(n["stargazerCount"] for n in u["repositories"]["nodes"])
        sizes = {}
        for n in u["repositories"]["nodes"]:
            for e in n["languages"]["edges"]:
                if e["node"]["name"] not in LANG_HIDE:
                    sizes[e["node"]["name"]] = sizes.get(e["node"]["name"], 0) + e["size"]
        tot = sum(sizes.values()) or 1
        d["langs"] = [(k, 100 * v / tot) for k, v in sorted(sizes.items(), key=lambda x: -x[1])][:5]

        # contributions, year by year since account creation
        start = int(u["createdAt"][:4])
        now = dt.datetime.utcnow()
        days, commits_year = {}, 0
        for y in range(start, now.year + 1):
            c = gql("""query($l:String!,$f:DateTime!,$t:DateTime!){user(login:$l){
              contributionsCollection(from:$f,to:$t){totalCommitContributions restrictedContributionsCount
                contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}""",
                    {"l": USER, "f": f"{y}-01-01T00:00:00Z",
                     "t": (now if y == now.year else dt.datetime(y, 12, 31, 23, 59, 59)).strftime("%Y-%m-%dT%H:%M:%SZ")}
                    )["user"]["contributionsCollection"]
            if y == now.year:
                commits_year = c["totalCommitContributions"] + c["restrictedContributionsCount"]
            for w in c["contributionCalendar"]["weeks"]:
                for day in w["contributionDays"]:
                    days[day["date"]] = day["contributionCount"]
        seq = sorted(days.items())
        d["days"] = seq
        d["total"] = sum(v for _, v in seq)
        d["commits"] = commits_year
        # streaks
        longest = run = 0
        for _, v in seq:
            run = run + 1 if v > 0 else 0
            longest = max(longest, run)
        cur, i = 0, len(seq) - 1
        if i >= 0 and seq[i][1] == 0:
            i -= 1  # today not counted yet
        while i >= 0 and seq[i][1] > 0:
            cur += 1
            i -= 1
        d["cur"], d["longest"] = cur, longest
        print("live data ok:", {k: d[k] for k in ("total", "cur", "longest", "commits", "prs", "repos")})
    except Exception as e:  # never break the build
        print("API error, using fallback where needed:", e)
    return d


# ── svg helpers ──────────────────────────────────────────────────────────
def t(x, y, s, size=12, fill=BLUSH, weight=400, anchor="start", ls=0, extra=""):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{MONO}" font-size="{size}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}" letter-spacing="{ls}" {extra}>{escape(s)}</text>')


def chamfer(x, y, w, h, c=12, fill=SURF, stroke=LINE, sw=1, extra=""):
    p = f"M{x+c},{y} H{x+w} V{y+h-c} L{x+w-c},{y+h} H{x} V{y+c} Z"
    return f'<path d="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>'


def section(y, num, name):
    label = f"◢ {num} // {name}"
    lw = len(label) * 10.2 + 18
    return (t(PAD, y, label, 14, CRIM, 700, ls=1.5) +
            f'<rect x="{PAD+lw:.0f}" y="{y-5}" width="{CW-lw:.0f}" height="1" fill="url(#fadeLine)"/>')


def wrap(s, chars):
    return textwrap.wrap(s, chars)


# ── 3D wireframe (pre-rendered as animated vector paths) ────────────────
def _ring(n, r, y=0.0, phase=0.0):
    return [(r * math.cos(2 * math.pi * k / n + phase), y, r * math.sin(2 * math.pi * k / n + phase)) for k in range(n)]


def _loop(start, n):
    return [(start + k, start + (k + 1) % n) for k in range(n)]


def _extrude(outlines, depth, joins=None):
    """Closed 2D outlines -> front + back copies joined at the corners (or every `joins`-th point)."""
    v, e = [], []
    for pts in outlines:
        n, a = len(pts), len(v)
        v += [(x, y, -depth / 2) for x, y in pts] + [(x, y, depth / 2) for x, y in pts]
        e += _loop(a, n) + _loop(a + n, n)
        e += [(a + k, a + n + k) for k in range(0, n, joins or 1)]
    return v, e


def _nearest(v):
    """Edges between every pair of vertices at the minimum distance (regular polyhedra)."""
    d = min(math.dist(a, b) for i, a in enumerate(v) for b in v[i + 1:])
    return [(i, j) for i in range(len(v)) for j in range(i + 1, len(v))
            if abs(math.dist(v[i], v[j]) - d) < 1e-6]


def shape(name, t=0.0):
    """Vertices + edges; t in [0,1) is the animation phase (only hypercube uses it)."""
    p = (1 + 5 ** 0.5) / 2
    if name == "tetrahedron":
        v = [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]
    elif name == "octahedron":
        v = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    elif name == "cube":
        v = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    elif name == "dodecahedron":
        v = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
        for a in (-1, 1):
            for b in (-1, 1):
                v += [(0, a / p, b * p), (a / p, b * p, 0), (a * p, 0, b / p)]
    elif name == "tesseract":  # cube inside a cube, corners joined
        c = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
        v = c + [(x * .5, y * .5, z * .5) for x, y, z in c]
        e = [(i, j) for i in range(8) for j in range(i + 1, 8) if sum(a != b for a, b in zip(c[i], c[j])) == 1]
        return v, e + [(i + 8, j + 8) for i, j in e] + [(i, i + 8) for i in range(8)]
    elif name in ("globe", "torus"):
        rings, segs = (5, 12) if name == "globe" else (8, 12)
        v, e = [], []
        for r in range(rings):
            for k in range(segs):
                a = 2 * math.pi * k / segs
                if name == "globe":
                    lat = math.pi * (r + 1) / (rings + 1) - math.pi / 2
                    v.append((math.cos(lat) * math.cos(a), math.sin(lat), math.cos(lat) * math.sin(a)))
                else:
                    b = 2 * math.pi * r / rings
                    R = 1 + .42 * math.cos(b)
                    v.append((R * math.cos(a), .42 * math.sin(b), R * math.sin(a)))
                e.append((r * segs + k, r * segs + (k + 1) % segs))
                if r + 1 < rings or name == "torus":
                    e.append((r * segs + k, ((r + 1) % rings) * segs + k))
        if name == "globe":  # poles close the meridians
            v += [(0, -1, 0), (0, 1, 0)]
            e += [(len(v) - 2, k) for k in range(segs)] + [(len(v) - 1, (rings - 1) * segs + k) for k in range(segs)]
        return v, e
    elif name == "pyramid":
        v = [(-1, -.7, -1), (1, -.7, -1), (1, -.7, 1), (-1, -.7, 1), (0, 1.1, 0)]
        return v, _loop(0, 4) + [(k, 4) for k in range(4)]
    elif name == "star":  # two interlocking tetrahedra
        t = [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]
        v = t + [(-x, -y, -z) for x, y, z in t]
        return v, [(i + o, j + o) for o in (0, 4) for i in range(4) for j in range(i + 1, 4)]
    elif name == "prism":
        v = _ring(6, 1, -.9) + _ring(6, 1, .9)
        return v, _loop(0, 6) + _loop(6, 6) + [(k, k + 6) for k in range(6)]
    elif name == "gem":
        v = _ring(8, .55, .6, math.pi / 8) + _ring(8, 1, .2) + [(0, -1.1, 0)]
        return v, (_loop(0, 8) + _loop(8, 8) + [(k, 8 + k) for k in range(8)]
                   + [(k, 8 + (k + 1) % 8) for k in range(8)] + [(8 + k, 16) for k in range(8)])
    elif name == "dna":  # double helix with base-pair rungs
        n, v, e = 30, [], []
        for strand in (0, math.pi):
            a = len(v)
            v += [(.55 * math.cos(3 * math.pi * k / n + strand), 2.2 * k / n - 1.1,
                   .55 * math.sin(3 * math.pi * k / n + strand)) for k in range(n + 1)]
            e += [(a + k, a + k + 1) for k in range(n)]
        return v, e + [(k, k + n + 1) for k in range(0, n + 1, 3)]
    elif name == "atom":  # three electron orbits around a nucleus, React style
        v, e = [], []
        for tilt in (0, math.pi / 3, 2 * math.pi / 3):
            a = len(v)
            for x, _, z in _ring(28, 1):
                x, y = x * math.cos(tilt), x * math.sin(tilt)
                v.append((x, y, z * .38))
            e += _loop(a, 28)
        a = len(v)
        v += [(.16, 0, 0), (-.16, 0, 0), (0, .16, 0), (0, -.16, 0), (0, 0, .16), (0, 0, -.16)]
        return v, e + [(a + i, a + j) for i in range(6) for j in range(i + 1, 6) if j != i + 1 or i % 2]
    elif name == "chat":  # speech bubble with typing dots
        body = [(-1.1, .75), (1.1, .75), (1.25, .6), (1.25, -.45), (1.1, -.6), (-.35, -.6),
                (-.8, -1.05), (-.75, -.6), (-1.1, -.6), (-1.25, -.45), (-1.25, .6)]
        dots = [[(cx + .15 * math.cos(2 * math.pi * k / 6), .08 + .15 * math.sin(2 * math.pi * k / 6)) for k in range(6)]
                for cx in (-.55, 0, .55)]
        return _extrude([body] + dots, .45)
    elif name == "monogram":  # extruded "LP" initials
        L = [(-1.55, 1.1), (-1.05, 1.1), (-1.05, -.65), (-.2, -.65), (-.2, -1.1), (-1.55, -1.1)]
        P = [(.15, -1.1), (.15, 1.1), (1.05, 1.1), (1.45, .8), (1.45, .25), (1.05, -.05), (.65, -.05), (.65, -1.1)]
        hole = [(.65, .7), (.95, .7), (1.05, .6), (1.05, .45), (.95, .35), (.65, .35)]
        return _extrude([L, P, hole], .5)
    elif name == "hypercube":  # 4D cube rotating through the 4th dimension, then projected
        c = [(x, y, z, w) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1) for w in (-1, 1)]
        a = 2 * math.pi * t
        v = []
        for x, y, z, w in c:
            x, w = x * math.cos(a) - w * math.sin(a), x * math.sin(a) + w * math.cos(a)
            k = 2.6 / (2.6 - w)
            v.append((x * k, y * k, z * k))
        return v, [(i, j) for i in range(16) for j in range(i + 1, 16) if sum(p != q for p, q in zip(c[i], c[j])) == 1]
    elif name == "geodesic":  # icosahedron subdivided once, pushed onto the sphere
        v, e = shape("icosahedron")
        es = set(e)
        faces = [(i, j, k) for i, j in e for k in range(len(v)) if k > j and (i, k) in es and (j, k) in es]
        v, mid, e = [tuple(c / math.dist((0, 0, 0), q) for c in q) for q in v], {}, []
        def m(i, j):
            if (i, j) not in mid:
                q = [(a + b) / 2 for a, b in zip(v[i], v[j])]
                v.append(tuple(c / math.dist((0, 0, 0), q) for c in q))
                mid[(i, j)] = len(v) - 1
            return mid[(i, j)]
        for i, j, k in faces:
            a, b, c = m(i, j), m(j, k), m(i, k)
            e += [(i, a), (a, j), (j, b), (b, k), (k, c), (c, i), (a, b), (b, c), (c, a)]
        return v, list(dict.fromkeys(tuple(sorted(x)) for x in e))
    elif name == "mobius":
        n, w, v = 36, .38, []
        for side in (1, -1):
            for k in range(n):
                u = 2 * math.pi * k / n
                r = 1 + side * w * math.cos(u / 2)
                v.append((r * math.cos(u), side * w * math.sin(u / 2), r * math.sin(u)))
        e = [(k, k + 1) for k in range(n - 1)] + [(n - 1, n)] + [(n + k, n + k + 1) for k in range(n - 1)] + [(2 * n - 1, 0)]
        return v, e + [(k, n + k) for k in range(0, n, 2)]
    elif name == "knot":  # trefoil
        n, v = 150, []
        for k in range(n):
            u = 2 * math.pi * k / n
            v.append((math.sin(u) + 2 * math.sin(2 * u), math.cos(u) - 2 * math.cos(2 * u), -math.sin(3 * u)))
        return v, _loop(0, n)
    elif name == "sierpinski":  # tetrahedron fractal, depth 2
        v, e, idx = [], [], {}
        def vid(q):
            key = tuple(round(c, 6) for c in q)
            if key not in idx:
                idx[key] = len(v)
                v.append(q)
            return idx[key]
        def tet(pts, d):
            if d == 0:
                ids = [vid(q) for q in pts]
                e.extend((ids[i], ids[j]) for i in range(4) for j in range(i + 1, 4))
                return
            for a in pts:
                tet([tuple((c1 + c2) / 2 for c1, c2 in zip(a, b)) for b in pts], d - 1)
        tet([(0, 1.2, 0)] + [(math.cos(k * 2 * math.pi / 3), -.4, math.sin(k * 2 * math.pi / 3)) for k in range(3)], 2)
        return v, e
    elif name == "neural":  # a small neural network: 3-5-5-2
        v, layers = [], []
        for xi, cnt in zip((-1.2, -.4, .4, 1.2), (3, 5, 5, 2)):
            layers.append(list(range(len(v), len(v) + cnt)))
            r = .25 + .13 * cnt
            v += [(xi, r * math.cos(2 * math.pi * k / cnt + .3), r * math.sin(2 * math.pi * k / cnt + .3)) for k in range(cnt)]
        return v, [(i, j) for a, b in zip(layers, layers[1:]) for i in a for j in b]
    elif name == "robot":  # chatbot head
        sq = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        head = [(-.8, .7), (.8, .7), (1, .5), (1, -.55), (.8, -.75), (-.8, -.75), (-1, -.55), (-1, .5)]
        return _extrude([head, sq(-.6, .25, -.2, -.1), sq(.2, .25, .6, -.1), sq(-.4, -.35, .4, -.5),
                         sq(-.07, .7, .07, 1.05), [(0, 1.05), (.15, 1.2), (0, 1.35), (-.15, 1.2)],
                         sq(-1.2, .25, -1, -.3), sq(1, .25, 1.2, -.3)], .7)
    elif name == "chip":  # AI processor
        v, e = _extrude([[(-.8, .7), (-.7, .8), (.8, .8), (.8, -.8), (-.8, -.8)],
                         [(-.42, .42), (.42, .42), (.42, -.42), (-.42, -.42)]], .22)
        for k in (-.5, -.17, .17, .5):  # pins on all four sides
            for x0, y0, x1, y1 in ((k, .8, k, 1.15), (k, -.8, k, -1.15), (.8, k, 1.15, k), (-.8, k, -1.15, k)):
                v += [(x0, y0, 0), (x1, y1, 0)]
                e.append((len(v) - 2, len(v) - 1))
        return v, e
    elif name == "sparkle":  # the AI "sparkle" star
        star = lambda cx, cy, r: [(cx + r * math.cos(u) ** 3, cy + r * math.sin(u) ** 3)
                                  for u in (2 * math.pi * k / 40 for k in range(40))]
        return _extrude([star(-.15, -.15, 1.25), star(.95, .95, .38)], .3, joins=5)
    elif name == "brackets":  # </>
        lt = [(-.45, .85), (-1.35, 0), (-.45, -.85), (-.28, -.62), (-.98, 0), (-.28, .62)]
        return _extrude([lt, [(-x, y) for x, y in lt], [(.2, 1), (.42, 1), (-.2, -1), (-.42, -1)]], .4)
    elif name == "browser":  # web page wireframe
        sq = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        dot = lambda cx: [(cx + .06 * math.cos(2 * math.pi * k / 6), .8 + .06 * math.sin(2 * math.pi * k / 6)) for k in range(6)]
        return _extrude([sq(-1.3, .95, 1.3, -.95), sq(-1.3, .95, 1.3, .65), dot(-1.12), dot(-.94), dot(-.76),
                         sq(-1.1, .48, 1.1, .05), sq(-1.1, -.15, -.45, -.75), sq(-.33, -.15, .33, -.75),
                         sq(.45, -.15, 1.1, -.75)], .16)
    elif name == "layers":  # stacked UI components
        v = _ring(4, 1.2, -.55, math.pi / 4) + _ring(4, 1.2, 0, math.pi / 4) + _ring(4, 1.2, .55, math.pi / 4)
        return v, _loop(0, 4) + _loop(4, 4) + _loop(8, 4)
    elif name == "database":
        v = _ring(24, 1, .9) + _ring(24, 1, .3) + _ring(24, 1, -.3) + _ring(24, 1, -.9)
        return v, (_loop(0, 24) + _loop(24, 24) + _loop(48, 24) + _loop(72, 24)
                   + [(k + 24 * r, k + 24 * r + 24) for k in (0, 6, 12, 18) for r in range(3)])
    elif name == "football":  # truncated icosahedron, the classic soccer ball
        iv, ie = shape("icosahedron")
        v = [tuple(a + (b - a) * f for a, b in zip(iv[i], iv[j])) for i, j in ie for f in (1 / 3, 2 / 3)]
        return v, _nearest(v)
    else:  # icosahedron
        v = [(-1, p, 0), (1, p, 0), (-1, -p, 0), (1, -p, 0), (0, -1, p), (0, 1, p),
             (0, -1, -p), (0, 1, -p), (p, 0, -1), (p, 0, 1), (-p, 0, -1), (-p, 0, 1)]
    return v, _nearest(v)


INNER = {"icosahedron", "dodecahedron", "octahedron", "tetrahedron", "cube", "pyramid", "star", "prism", "gem"}


def _chains(e):
    """Group edges into connected runs so each run is one 'M x y L x y x y ...' path command."""
    adj, used, out = {}, set(), []
    for k, (i, j) in enumerate(e):
        adj.setdefault(i, []).append((k, j))
        adj.setdefault(j, []).append((k, i))
    for k, (i, j) in enumerate(e):
        if k in used:
            continue
        used.add(k)
        run, end = [i, j], j
        while True:
            nxt = next(((kk, o) for kk, o in adj[end] if kk not in used), None)
            if not nxt:
                break
            used.add(nxt[0])
            run.append(nxt[1])
            end = nxt[1]
        out.append(run)
    return out


def wire_frames(cx, cy, r, frames, spin=1, tilt=0.45, phase=0.0, kind=SHAPE):
    shapes = [shape(kind, f / frames) for f in range(frames)]
    chains = _chains(shapes[0][1])
    n = max(math.dist((0, 0, 0), q) for v, _ in shapes for q in v)
    paths, pts = [], []
    for f, (v, _) in enumerate(shapes):
        a = spin * 2 * math.pi * f / frames + phase
        b = tilt + 0.18 * math.sin(2 * math.pi * f / frames)
        proj = []
        for x, y, z in v:
            x, y, z = x / n, -y / n, z / n  # model space is y-up, screen is y-down
            x, z = x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)
            y, z = y * math.cos(b) - z * math.sin(b), y * math.sin(b) + z * math.cos(b)
            k = 3.2 / (3.2 + z)
            proj.append((cx + x * r * k, cy + y * r * k))
        paths.append("".join(f"M{proj[c[0]][0]:.1f} {proj[c[0]][1]:.1f}L" + " ".join(f"{proj[i][0]:.1f} {proj[i][1]:.1f}" for i in c[1:])
                             for c in chains))
        pts.append(proj)
    return paths, pts


def wireframe(cx, cy, r, dur=16, kind=SHAPE):
    out = []
    layers = ((r, 1, CRIM, 0.95, 1.4), (r * 0.46, -1, WINE, 0.8, 1))
    for rr, spin, col, op, sw in layers if kind in INNER else layers[:1]:
        paths, pts = wire_frames(cx, cy, rr, 60, spin, kind=kind)
        vals = ";".join(paths + [paths[0]])
        out.append(f'<path fill="none" stroke="{col}" stroke-width="{sw}" stroke-linejoin="round" opacity="{op}" filter="url(#glow)">'
                   f'<animate attributeName="d" dur="{dur}s" repeatCount="indefinite" values="{vals}"/></path>')
        if rr == r:
            for k in range(len(pts[0]) if len(pts[0]) <= 20 else 0):  # no vertex dots on dense meshes
                xs = ";".join(f"{p[k][0]:.1f}" for p in pts + [pts[0]])
                ys = ";".join(f"{p[k][1]:.1f}" for p in pts + [pts[0]])
                out.append(f'<circle r="2.6" fill="{BLUSH}"><animate attributeName="cx" dur="{dur}s" repeatCount="indefinite" values="{xs}"/>'
                           f'<animate attributeName="cy" dur="{dur}s" repeatCount="indefinite" values="{ys}"/></circle>')
    # orbit rings
    out.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{r*1.35:.0f}" ry="{r*0.32:.0f}" fill="none" stroke="{OXB}" stroke-width="1" stroke-dasharray="3 7">'
               f'<animateTransform attributeName="transform" type="rotate" from="-12 {cx} {cy}" to="348 {cx} {cy}" dur="40s" repeatCount="indefinite"/></ellipse>')
    return "".join(out)


# ── sections ─────────────────────────────────────────────────────────────
def header():
    H, hz = 330, 238
    o = [f'<rect width="{W}" height="{H}" fill="url(#hdrGlow)"/>']
    # grid floor: vanishing lines + moving horizontal lines
    o.append(f'<g stroke="{OXB}" stroke-width="1" opacity="0.8">')
    for x in range(-1400, 2500, 120):
        o.append(f'<line x1="{W/2}" y1="{hz}" x2="{x}" y2="{H}"/>')
    for k in range(7):
        ys = ";".join(f"{hz + (H - hz) * (s / 11) ** 2:.1f}" for s in range(12))
        o.append(f'<line x1="0" x2="{W}" y1="{hz}" y2="{hz}"><animate attributeName="y1" values="{ys}" dur="3.5s" begin="{-k*0.5:.1f}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="y2" values="{ys}" dur="3.5s" begin="{-k*0.5:.1f}s" repeatCount="indefinite"/></line>')
    o.append('</g>')
    o.append(f'<rect y="{hz-2}" width="{W}" height="{H-hz+2}" fill="url(#floorFade)"/>')
    o.append(f'<rect y="{hz}" width="{W}" height="1.2" fill="url(#fadeLineC)"/>')
    # HUD corners + tags
    o.append(f'<path d="M20 40 V20 H40 M{W-40} 20 H{W-20} V40" stroke="{WINE}" stroke-width="1.5" fill="none"/>')
    o.append(t(52, 34, "[ SYS://LORENZO.DEV ]  BUILD 2026", 11, DIM, ls=1))
    o.append(f'<circle cx="{W-118}" cy="30" r="4" fill="{CRIM}"><animate attributeName="opacity" values="1;.2;1" dur="1.6s" repeatCount="indefinite"/></circle>')
    o.append(t(W - 108, 34, "ONLINE", 11, CRIM, 700, ls=2))
    # name with glow
    o.append(t(PAD + 8, 122, NAME, 52, CRIM, 800, ls=6, extra='filter="url(#glowBig)" opacity=".75"'))
    o.append(t(PAD + 8, 122, NAME, 52, BLUSH, 800, ls=6))
    o.append(t(PAD + 10, 158, ROLES, 14, CRIM, 600, ls=1.6))
    # typing line
    line = STATUS
    tw = len(line) * 9.05
    o.append(f'<clipPath id="typeClip"><rect x="{PAD+8}" y="178" height="30" width="0">'
             f'<animate attributeName="width" values="0;{tw:.0f};{tw:.0f};0" keyTimes="0;.45;.9;1" dur="7s" repeatCount="indefinite"/></rect></clipPath>')
    o.append(f'<g clip-path="url(#typeClip)">{t(PAD + 10, 198, line, 15, MUTED)}</g>')
    o.append(f'<rect y="185" width="9" height="17" fill="{CRIM}"><animate attributeName="x" values="{PAD+10};{PAD+12+tw:.0f};{PAD+12+tw:.0f};{PAD+10}" keyTimes="0;.45;.9;1" dur="7s" repeatCount="indefinite"/>'
             f'<animate attributeName="opacity" values="1;0;1" dur=".9s" repeatCount="indefinite"/></rect>')
    o.append(wireframe(850, 132, 96))
    return "".join(o), H


def profile(y0, avatar_b64):
    o = [section(y0 + 20, "01", "SYSTEM.PROFILE")]
    cx, cy, r = PAD + 130, y0 + 170, 104
    o.append(f'<clipPath id="avClip"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="{r+22}" fill="url(#avGlow)"/>')
    o.append(f'<image href="data:image/jpeg;base64,{avatar_b64}" x="{cx-r}" y="{cy-r}" width="{2*r}" height="{2*r}" clip-path="url(#avClip)"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="{r+3}" fill="none" stroke="url(#ringGrad)" stroke-width="5"/>')
    for rr, dash, dur, rev, col in ((r + 16, "18 10", 24, False, CRIM), (r + 27, "4 14", 36, True, WINE), (r + 36, "60 200", 12, False, BLUSH)):
        a, b = (360, 0) if rev else (0, 360)
        o.append(f'<circle cx="{cx}" cy="{cy}" r="{rr}" fill="none" stroke="{col}" stroke-width="1.6" stroke-dasharray="{dash}" opacity=".85">'
                 f'<animateTransform attributeName="transform" type="rotate" from="{a} {cx} {cy}" to="{b} {cx} {cy}" dur="{dur}s" repeatCount="indefinite"/></circle>')
    # terminal window
    x, y, w, h = 330, y0 + 48, W - PAD - 330, 262
    o.append(chamfer(x, y, w, h, 14, SURF, LINE))
    o.append(f'<rect x="{x}" y="{y}" width="{w}" height="30" fill="{SURF2}"/>')
    for i, c in enumerate((CRIM, WINE, BURG)):
        o.append(f'<circle cx="{x+20+i*16}" cy="{y+15}" r="4.5" fill="{c}"/>')
    o.append(t(x + w / 2, y + 19, "~/lorenzo/profile.yaml", 11, DIM, anchor="middle"))
    for i, (k, v) in enumerate(PROFILE):
        yy = y + 58 + i * 20.5
        if k:
            o.append(t(x + 22, yy, f"{k}", 13, CRIM, 600))
            o.append(t(x + 150, yy, ":", 13, DIM))
        o.append(t(x + 166, yy, v, 13, BLUSH))
    return "".join(o), 330


def projects(y0):
    o = [section(y0 + 20, "02", "FEATURED.BUILDS")]
    y, gap, h = y0 + 44, 16, 150
    cells, col = [], 0
    for p in PROJECTS:
        if p.get("wide"):
            cells.append((PAD, y, CW, p)); y += h + gap; col = 0
        else:
            cw = (CW - gap) / 2
            cells.append((PAD + col * (cw + gap), y, cw, p))
            col += 1
            if col == 2:
                col, y = 0, y + h + gap
    if col:
        y += h + gap
    for i, (x, yy, w, p) in enumerate(cells):
        o.append(f'<g class="fade" style="animation-delay:{0.15*i:.2f}s">')
        o.append(chamfer(x, yy, w, h, 16, SURF, LINE))
        o.append(f'<rect x="{x}" y="{yy+16}" width="3" height="{h-32}" fill="url(#vGrad)"/>')
        o.append(t(x + 22, yy + 32, p["title"], 15, BLUSH, 700, ls=1))
        tag = p["tag"]; tw = len(tag) * 6.6 + 18
        o.append(f'<rect x="{x+w-tw-16:.1f}" y="{yy+17}" width="{tw:.1f}" height="21" rx="3" fill="none" stroke="{WINE}"/>')
        o.append(t(x + w - tw / 2 - 16, yy + 31.5, tag, 10, CRIM, 700, "middle", 0.6))
        chars = int((w - 44) / 7.25)
        for j, ln in enumerate(wrap(p["desc"], chars)[:4]):
            o.append(t(x + 22, yy + 58 + j * 17, ln, 12, MUTED))
        o.append(t(x + 22, yy + h - 16, "▸ " + p["stack"], 11, WINE, 600))
        o.append('</g>')
    return "".join(o), y - y0 + 6


def principles(y0):
    o = [section(y0 + 20, "03", "OPERATING.PRINCIPLES")]
    gap, h = 14, 150
    w = (CW - 3 * gap) / 4
    for i, (title, desc) in enumerate(PRINCIPLES):
        x, y = PAD + i * (w + gap), y0 + 44
        o.append(chamfer(x, y, w, h, 14, SURF, LINE))
        o.append(t(x + 18, y + 38, f"[0{i+1}]", 22, CRIM, 800, extra='filter="url(#glow)"'))
        for j, ln in enumerate(wrap(title, 22)):
            o.append(t(x + 18, y + 64 + j * 16, ln, 12, BLUSH, 700, ls=0.5))
        ty = y + 64 + len(wrap(title, 22)) * 16 + 6
        for j, ln in enumerate(wrap(desc, 30)[:4]):
            o.append(t(x + 18, ty + j * 15, ln, 11, MUTED))
    return "".join(o), h + 64


def stack(y0, icons):
    o = [section(y0 + 20, "04", "TECH.STACK")]
    per, gap = 11, 10
    s = (CW - (per - 1) * gap) / per
    for i, ic in enumerate(icons):
        r, c = divmod(i, per)
        x, y = PAD + c * (s + gap), y0 + 44 + r * (s + gap)
        o.append(f'<g class="fade" style="animation-delay:{0.05*i:.2f}s">')
        o.append(chamfer(x, y, s, s, 9, SURF, LINE))
        sc = 26 / 24
        o.append(f'<path d="{ic["path"]}" fill="{BLUSH}" transform="translate({x+s/2-13:.1f},{y+14:.1f}) scale({sc:.3f})"/>')
        o.append(t(x + s / 2, y + s - 12, ic["label"], 9, MUTED, anchor="middle"))
        o.append('</g>')
    rows = math.ceil(len(icons) / per)
    return "".join(o), 44 + rows * (s + gap) + 16


def telemetry(y0, d):
    o = [section(y0 + 20, "05", "TELEMETRY")]
    y = y0 + 44
    # stat tiles 3x2
    tiles = [("TOTAL CONTRIBUTIONS", d["total"]), ("CURRENT STREAK", f'{d["cur"]} d'), ("LONGEST STREAK", f'{d["longest"]} d'),
             ("COMMITS THIS YEAR", d["commits"]), ("PULL REQUESTS", d["prs"]), ("PUBLIC REPOS", d["repos"])]
    lw, gap, th = 568, 12, 80
    tw = (lw - 2 * gap) / 3
    for i, (lab, val) in enumerate(tiles):
        r, c = divmod(i, 3)
        x, yy = PAD + c * (tw + gap), y + r * (th + gap)
        o.append(chamfer(x, yy, tw, th, 12, SURF, LINE))
        o.append(t(x + 18, yy + 42, str(val), 28, CRIM if i in (1, 2) else BLUSH, 800,
                   extra='filter="url(#glow)"' if i == 1 else ""))
        o.append(t(x + 18, yy + 64, lab, 10, DIM, 600, ls=1))
    # languages
    lx, lwid, lh = PAD + lw + 16, CW - lw - 16, 2 * th + gap
    o.append(chamfer(lx, y, lwid, lh, 12, SURF, LINE))
    o.append(t(lx + 18, y + 26, "// LANGUAGES", 11, CRIM, 700, ls=1))
    shades = [CRIM, WINE, BURG, DEEP, OXB]
    langs = d["langs"][:5]
    tot = sum(p for _, p in langs) or 1
    bx, bw = lx + 18, lwid - 36
    o.append(f'<rect x="{bx}" y="{y+38}" width="{bw}" height="8" rx="4" fill="{SURF2}"/>')
    cx = bx
    for i, (name, pct) in enumerate(langs):
        sw = bw * pct / tot
        o.append(f'<rect x="{cx:.1f}" y="{y+38}" width="{max(sw,1.5):.1f}" height="8" fill="{shades[i]}">'
                 f'<animate attributeName="width" from="0" to="{max(sw,1.5):.1f}" dur="1.4s" fill="freeze"/></rect>')
        cx += sw
        ly = y + 72 + i * 20
        o.append(f'<rect x="{bx}" y="{ly-9}" width="10" height="10" fill="{shades[i]}"/>')
        o.append(t(bx + 18, ly, name, 12, BLUSH))
        o.append(t(bx + bw, ly, f"{pct:.1f}%", 12, MUTED, anchor="end"))
    y += lh + 20
    # heatmap (last 52 weeks)
    o.append(chamfer(PAD, y, CW, 200, 14, SURF, LINE))
    o.append(t(PAD + 18, y + 26, "// CONTRIBUTIONS · LAST 12 MONTHS", 11, CRIM, 700, ls=1))
    today = dt.date.today()
    days = dict(d["days"])
    start = today - dt.timedelta(days=7 * 51 + (today.weekday() + 1) % 7)
    vals = [days.get((start + dt.timedelta(i)).isoformat(), 0) for i in range((today - start).days + 1)]
    mx = max(vals) if vals and max(vals) else 1
    lv = [SURF2, OXB, BURG, WINE, CRIM]
    cs, cg = 13, 3.6
    gx0 = PAD + (CW - 52 * (cs + cg)) / 2
    for i, v in enumerate(vals):
        wk, wd = divmod(i, 7)
        lvl = 0 if v == 0 else min(4, 1 + int(3 * v / mx))
        o.append(f'<rect x="{gx0 + wk*(cs+cg):.1f}" y="{y+42+wd*(cs+cg):.1f}" width="{cs}" height="{cs}" rx="2.5" fill="{lv[lvl]}"/>')
    # scanning beam
    o.append(f'<rect y="{y+38}" width="46" height="{7*(cs+cg)+4:.0f}" fill="url(#beam)"><animate attributeName="x" values="{gx0-60:.0f};{gx0+52*(cs+cg)+10:.0f}" dur="5s" repeatCount="indefinite"/></rect>')
    o.append(t(PAD + CW - 150, y + 186, "less", 10, DIM, anchor="end"))
    for i, c in enumerate(lv):
        o.append(f'<rect x="{PAD + CW - 142 + i*16}" y="{y+176}" width="11" height="11" rx="2" fill="{c}"/>')
    o.append(t(PAD + CW - 18, y + 186, "more", 10, DIM, anchor="end"))
    y += 200
    return "".join(o), y - y0 + 10


def footer(y0):
    o = [f'<rect x="{PAD}" y="{y0+10}" width="{CW}" height="1" fill="url(#fadeLineC)"/>',
         t(W / 2, y0 + 42, "> END_OF_TRANSMISSION", 13, CRIM, 700, "middle", 3),
         t(W / 2, y0 + 62, f"last sync {dt.date.today().isoformat()} · auto-generated by GitHub Actions", 10, DIM, anchor="middle")]
    return "".join(o), 84


DEFS = f"""
<defs>
  <filter id="glow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="2.2" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <filter id="glowBig" x="-10%" y="-60%" width="120%" height="220%"><feGaussianBlur stdDeviation="9"/></filter>
  <radialGradient id="hdrGlow" cx="72%" cy="38%" r="70%"><stop offset="0" stop-color="{HDR}"/><stop offset=".55" stop-color="{SURF}"/><stop offset="1" stop-color="{BG}"/></radialGradient>
  <radialGradient id="avGlow"><stop offset=".78" stop-color="{CRIM}" stop-opacity=".45"/><stop offset="1" stop-color="{CRIM}" stop-opacity="0"/></radialGradient>
  <linearGradient id="floorFade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{BG}" stop-opacity=".95"/><stop offset=".6" stop-color="{BG}" stop-opacity=".2"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></linearGradient>
  <linearGradient id="fadeLine"><stop offset="0" stop-color="{CRIM}"/><stop offset="1" stop-color="{CRIM}" stop-opacity="0"/></linearGradient>
  <linearGradient id="fadeLineC"><stop offset="0" stop-color="{CRIM}" stop-opacity="0"/><stop offset=".5" stop-color="{CRIM}"/><stop offset="1" stop-color="{CRIM}" stop-opacity="0"/></linearGradient>
  <linearGradient id="vGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CRIM}"/><stop offset="1" stop-color="{BURG}"/></linearGradient>
  <linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CRIM}"/><stop offset=".5" stop-color="{BURG}"/><stop offset="1" stop-color="{WINE}"/></linearGradient>
  <linearGradient id="beam"><stop offset="0" stop-color="{CRIM}" stop-opacity="0"/><stop offset=".8" stop-color="{CRIM}" stop-opacity=".35"/><stop offset="1" stop-color="{BLUSH}" stop-opacity=".7"/></linearGradient>
  <pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#fff" opacity=".025"/></pattern>
  <linearGradient id="sweep" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CRIM}" stop-opacity="0"/><stop offset="1" stop-color="{CRIM}" stop-opacity=".06"/></linearGradient>
</defs>
<style>
  .fade {{ opacity:0; animation: fadeIn .8s ease-out forwards; }}
  @keyframes fadeIn {{ from {{ opacity:0; transform: translateY(6px); }} to {{ opacity:1; transform: none; }} }}
</style>"""


def dashboard(d):
    with open(os.path.join(OUT, "avatar-src.jpg"), "rb") as f:
        av = base64.b64encode(f.read()).decode()
    with open(ICONS) as f:
        icons = json.load(f)
    parts, y = [], 0
    s, h = header(); parts.append(s); y += h
    for fn in (lambda y: profile(y, av), projects, principles, lambda y: stack(y, icons), lambda y: telemetry(y, d), footer):
        s, h = fn(y); parts.append(s); y += h
    H = int(y)
    frame = (f'<rect x="8" y="8" width="{W-16}" height="{H-16}" fill="none" stroke="{OXB}" stroke-width="1"/>'
             f'<path d="M8 60 V8 H60 M{W-60} 8 H{W-8} V60 M{W-8} {H-60} V{H-8} H{W-60} M60 {H-8} H8 V{H-60}" stroke="{CRIM}" stroke-width="2" fill="none"/>')
    overlay = (f'<rect width="{W}" height="{H}" fill="url(#scan)" pointer-events="none"/>'
               f'<rect width="{W}" height="140" fill="url(#sweep)"><animate attributeName="y" values="-140;{H}" dur="9s" repeatCount="indefinite"/></rect>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
            f'<title>Lorenzo Pedrozo · Full-Stack Developer · Project Manager</title>'
            f'{DEFS}<rect width="{W}" height="{H}" fill="{BG}"/>{"".join(parts)}{frame}{overlay}</svg>')


def button(label):
    w, h = int(len(label) * 9.2 + 44), 44
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CRIM}"/><stop offset="1" stop-color="{BURG}"/></linearGradient></defs>'
            f'<path d="M10 1 H{w-1} V{h-11} L{w-11} {h-1} H1 V11 Z" fill="{BG}" stroke="url(#g)" stroke-width="1.6"/>'
            f'<rect x="1" y="14" width="3" height="{h-28}" fill="{CRIM}"/>'
            f'{t(w/2, h/2 + 5, label, 13, BLUSH, 700, "middle", 1.5)}</svg>')


def main():
    d = fetch()
    with open(os.path.join(OUT, "dashboard.svg"), "w", encoding="utf-8") as f:
        f.write(dashboard(d))
    for name, label in BUTTONS:
        with open(os.path.join(OUT, f"{name}.svg"), "w", encoding="utf-8") as f:
            f.write(button(label))
    print("built", os.path.getsize(os.path.join(OUT, "dashboard.svg")) // 1024, "KB")


if __name__ == "__main__":
    main()
