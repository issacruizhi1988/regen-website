#!/usr/bin/env python3
"""Generate one static page per coach at /coaches/<slug>/ from content/coaches.json.

Static pages give every coach a clean, shareable link whose WhatsApp/social
preview shows that coach's photo and name. Netlify runs this on every deploy
(see netlify.toml), so edits made in /admin appear automatically.
Run locally with: python3 tools/build.py

It also does the SEO work that browsers would otherwise do in JavaScript:
  * prerenders content (team grid, FAQ, reviews, coach profiles ...) into the static
    pages between <!--pre:NAME--> ... <!--/pre:NAME--> markers, using the same markup
    as assets/js/site.js, so crawlers that do not run JS still read it;
  * writes JSON-LD (<!--pre:ld-->) and canonical / og:url (<!--pre:canon-->) in each <head>;
  * generates sitemap.xml, robots.txt and llms.txt (git-ignored, rebuilt on every deploy).
Every step replaces what is between the markers, so running it twice changes nothing.
"""
import html, json, os, re, shutil
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = ("https://fonts.googleapis.com/css2?family=Inter+Tight:ital,wght@0,500;0,600;0,700;0,800;1,700"
         "&family=Inter:wght@300;400;500;600&display=swap")

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<!--pre:canon--><!--/pre:canon-->
<meta property="og:type" content="profile">
<meta property="og:site_name" content="ReGen Performance">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{image}">
<meta property="og:image:width" content="900">
<meta property="og:image:height" content="900">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0A0A0A">
<link rel="icon" type="image/png" href="/assets/img/favicon-32.png">
<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{fonts}" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/site.css">
<!--pre:ld--><!--/pre:ld-->
</head>
<body data-page="coaches" data-coach="{slug}">
<main>
  <div class="wrap" style="padding-top:2rem">
    <a class="link-arrow" href="/coaches.html"><span style="transform:rotate(180deg)">→</span> All coaches</a>
  </div>
  <div id="coach-root"><!--pre:coach--><!--/pre:coach--></div>

  <section class="cta-band" id="cta-section" hidden>
    <div class="glow"></div>
    <div class="wrap-narrow reveal">
      <div class="hero-vline"></div>
      <span class="eyebrow">Start Your Journey</span>
      <h2 class="h2" style="margin-top:1rem">Book a Free<br><em>Discovery Call</em></h2>
      <p class="lead">Thirty minutes. No pressure, just clarity on what your body needs and where to start.</p>
      <div class="btn-row"><a class="btn btn-gold" id="cta-wa" href="/" target="_blank" rel="noopener">WhatsApp</a><a class="btn btn-ghost" href="/coaches.html">Meet the Team</a></div>
    </div>
  </section>
</main>
<script src="https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"></script>
<script src="/assets/js/site.js"></script>
<script src="/assets/js/coach.js"></script>
</body>
</html>
"""




# ---------------------------------------------------------------- helpers
def load(name):
    with open(os.path.join(ROOT, "content", name + ".json"), encoding="utf-8") as f:
        return json.load(f)


def E(v):
    """HTML-escape exactly like RG.esc in assets/js/site.js."""
    return (str(v if v is not None else "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;"))


def wa(number, message=""):
    n = re.sub(r"\D", "", str(number or ""))
    return "https://wa.me/" + n + ("?text=" + quote(message, safe="-_.!~*'()") if message else "")


def ig_url(handle):
    h = re.sub(r"/.*$", "", re.sub(r"^https?://(www\.)?instagram\.com/", "", str(handle or "").lstrip("@")))
    return "https://www.instagram.com/" + h if h else ""


def first_name(k):
    return k.get("firstName") or (k.get("name") or "").split(" ")[0] or "there"


def initials(name):
    return "".join(w[0] for w in str(name or "").split()[:2]).upper()


def photo(src, name):
    if src:
        return '<img src="%s" alt="%s" loading="lazy">' % (E(src), E(name))
    return '<div class="photo-placeholder"><span>%s</span></div>' % E(initials(name))


def stars(n):
    try:
        n = round(float(n)) or 5
    except (TypeError, ValueError):
        n = 5
    n = max(0, min(5, n))
    return ('<span class="stars" aria-label="%d out of 5 stars">%s<span style="opacity:.25">%s</span></span>'
            % (n, "★★★★★"[:n], "★★★★★"[:5 - n]))


def inline_md(t):
    t = E(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?![\*\w])", r"<em>\1</em>", t)
    return t


def md_blocks(text):
    """Simple Markdown: paragraphs and '- ' bullet lists. Returns [('p', text) | ('ul', [items])]."""
    blocks, para, items = [], [], []

    def flush():
        nonlocal para, items
        if para:
            blocks.append(("p", para)); para = []
        if items:
            blocks.append(("ul", items)); items = []

    for line in str(text or "").replace("\r", "").split("\n"):
        if not line.strip():
            flush()
        elif re.match(r"^\s*[-*] +", line):
            if para:
                blocks.append(("p", para)); para = []
            items.append(re.sub(r"^\s*[-*] +", "", line).strip())
        else:
            if items:
                blocks.append(("ul", items)); items = []
            para.append(line.strip())
    flush()
    return blocks


def md_html(text):
    out = []
    for kind, v in md_blocks(text):
        if kind == "p":
            out.append("<p>" + "<br>".join(inline_md(x) for x in v) + "</p>")
        else:
            out.append("<ul>\n" + "\n".join("<li>" + inline_md(x) + "</li>" for x in v) + "\n</ul>")
    return "\n".join(out)


def md_plain(text):
    parts = []
    for kind, v in md_blocks(text):
        if kind == "p":
            parts.append(" ".join(re.sub(r"\*+", "", x) for x in v))
        else:
            for x in v:
                x = re.sub(r"\*+", "", x)
                parts.append(x if re.search(r"[.!?:]$", x) else x + ".")
    return " ".join(parts)


def team_order(coaches, order):
    """Deterministic version of RG.teamOrder: fixed first / middle / last, the rest in file order."""
    by = {k["slug"]: k for k in coaches}
    pick = lambda a: [by[s] for s in (a or []) if s in by]
    first, mid, last = pick(order.get("first")), pick(order.get("middle")), pick(order.get("last"))
    used = {k["slug"] for k in first + mid + last}
    out = first + [k for k in coaches if k["slug"] not in used]
    if mid:
        total = len(out) + len(mid) + len(last)
        at = max(len(first), min(len(out), (total - len(mid)) // 2))
        out[at:at] = mid
    return out + last


def set_block(page, name, content, before="</head>"):
    """Replace what sits between the <!--pre:NAME--> markers; add the markers before `before` if absent."""
    a, b = "<!--pre:%s-->" % name, "<!--/pre:%s-->" % name
    pat = re.compile(re.escape(a) + r".*?" + re.escape(b), re.S)
    block = a + content + b
    if pat.search(page):
        return pat.sub(lambda m: block, page, count=1)
    assert before in page, "no %s to insert %s before" % (before, name)
    return page.replace(before, block + "\n" + before, 1)


def ld(*objs):
    """JSON-LD script tags (one per object). '<' is escaped so the JSON can never close the tag."""
    out = []
    for o in objs:
        data = json.dumps(o, ensure_ascii=False, indent=2).replace("<", "\\u003c")
        out.append('\n<script type="application/ld+json">\n' + data + "\n</script>")
    return "".join(out) + "\n"


def canon(url):
    return '\n<link rel="canonical" href="%s">\n<meta property="og:url" content="%s">\n' % (E(url), E(url))


def crumbs(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u}
                                for i, (n, u) in enumerate(items)]}


# ---------------------------------------------------------------- prerendered fragments (same markup as the JS)
def team_card(k):
    href = "/coaches/%s/" % quote(k["slug"], safe="-_.!~*'()")
    return ('<a class="team-member reveal" href="%s"><span class="coach-photo">%s</span>'
            '<span class="team-name">%s</span><span class="team-spec">%s</span></a>'
            % (href, photo(k.get("photo"), k.get("name")), E(k.get("name")), E(k.get("specialty"))))


def coach_card(k, site):
    href = "/coaches/%s/" % quote(k["slug"], safe="-_.!~*'()")
    first = first_name(k)
    wa_href = wa(k.get("whatsapp") or site.get("whatsapp"),
                 "Hi %s, I found you on the ReGen Performance website and I'd like to book a free discovery call." % first)
    focus = [f for f in (k.get("focus") or []) if f][:3]
    mid = ('<div class="focus-list focus-sm">' + "".join('<span class="focus">%s</span>' % E(f) for f in focus) + "</div>"
           if focus else '<p class="coach-bio">%s</p>' % E(k.get("bio")))
    return ('<article class="coach-card reveal">'
            '<a class="coach-photo" href="%s" aria-label="%s profile">%s</a>'
            '<div class="coach-body"><h3 class="coach-name"><a href="%s">%s</a></h3>'
            '<div class="coach-specialty">%s</div>%s'
            '<div class="coach-actions"><a class="btn btn-gold btn-sm" href="%s" target="_blank" rel="noopener">WhatsApp %s</a>'
            '<a class="link-arrow" href="%s">Profile <span>→</span></a></div></div></article>'
            % (href, E(k.get("name")), photo(k.get("photo"), k.get("name")), href, E(k.get("name")),
               E(k.get("specialty")), mid, wa_href, E(first), href))


def faq_html(site):
    return "".join('<details><summary>%s</summary><div class="prose">%s</div></details>'
                   % (E(f["question"]), md_html(f["answer"])) for f in site.get("faq", []))


def mrt_sentence(loc):
    mrt = [m for m in (loc.get("nearbyMrt") or []) if m]
    walk = ""
    if mrt:
        walk = ", a short walk from " + (", ".join(mrt[:-1]) + " and " + mrt[-1] if len(mrt) > 1 else mrt[0]) + " MRT"
    return "Find us inside Platinum Fitness at Robertson Quay" + walk + ". Convenient for River Valley, Clarke Quay and Tiong Bahru."


def visit_html(site):
    loc = site.get("location", {})
    map_url = loc.get("mapsUrl") or ("https://www.google.com/maps/search/?api=1&query=" +
                                     quote((loc.get("name") or "") + " " + (loc.get("address") or ""), safe="-_.!~*'()"))
    return ('<span class="card-label">Visit</span><p><strong>%s</strong><br>%s%s</p><p>%s</p>'
            '<a class="link-arrow" href="%s" target="_blank" rel="noopener">Get directions <span>→</span></a>'
            % (E(loc.get("name")), E(loc.get("address")), "<br>" + E(loc["note"]) if loc.get("note") else "",
               E(mrt_sentence(loc)), E(map_url)))


def home_reviews_html(reviews):
    seen, picked = set(), []
    for v in reviews:
        if not v.get("featured"):
            continue
        key = (v.get("coaches") or [None])[0] or v.get("name")
        if key in seen:
            continue
        seen.add(key); picked.append(v)
    return "".join('<figure class="review reveal">%s<p>%s</p><figcaption class="review-by">%s</figcaption></figure>'
                   % (stars(v.get("rating")), E(v.get("text")), E(v.get("name"))) for v in picked[:3])


def results_reviews_html(reviews, coaches):
    by = {k["slug"]: k for k in coaches}
    ordered = [v for v in reviews if v.get("featured")] + [v for v in reviews if not v.get("featured")]
    out = []
    for v in ordered[:6]:
        names = [by[s]["name"] for s in (v.get("coaches") or []) if s in by]
        out.append('<figure class="review">%s<p>%s</p><figcaption class="review-by">%s%s%s</figcaption></figure>'
                   % (stars(v.get("rating")), E(v.get("text")), E(v.get("name")),
                      "<span>%s</span>" % E(v["date"]) if v.get("date") else "",
                      '<em class="review-coach">%s</em>' % E(" & ".join(names)) if names else ""))
    return "".join(out)


def coach_profile_html(k, site, services=()):
    lst = lambda a: [x for x in (a or []) if x and (not isinstance(x, str) or x.strip())]
    first = first_name(k)
    wa_link = wa(k.get("whatsapp") or site.get("whatsapp"),
                 "Hi %s, I found you on the ReGen Performance website and I'd like to book a free discovery call." % first)
    ig = ig_url(k.get("instagram"))
    groups = lst(k.get("credentials"))
    if groups and isinstance(groups[0], str):
        groups = [{"group": "Certifications", "items": groups}]
    groups = [g for g in groups if lst(g.get("items"))]
    cert_count = sum(len(lst(g["items"])) for g in groups)
    highlights = lst(k.get("highlights"))
    if not highlights and cert_count <= 8:
        highlights = []

    def sec(id_, label, html_):
        return ('<section class="coach-sec" id="%s"><div class="label-rule">%s</div>%s</section>' % (id_, label, html_)) if html_ else ""

    about = ((('<p class="coach-intro">%s</p>' % E(k["intro"])) if k.get("intro") else "") +
             (('<div class="prose">%s</div>' % md_html(k["approach"])) if k.get("approach") else
              (('<div class="prose">%s</div>' % md_html(k["about"])) if k.get("about") else "")) +
             (('<div class="focus-list">%s</div>' % "".join('<span class="focus">%s</span>' % E(f) for f in lst(k.get("focus")))) if lst(k.get("focus")) else ""))
    ach = ('<ul class="ach-list">%s</ul>' % "".join("<li>%s</li>" % E(a) for a in lst(k.get("achievements")))) if lst(k.get("achievements")) else ""
    exp = ('<ol class="timeline">%s</ol>' % "".join(
        '<li><span class="timeline-period">%s</span><span class="timeline-role">%s</span>%s</li>'
        % (E(x.get("period")), E(x.get("role")), '<span class="timeline-org">%s</span>' % E(x["org"]) if x.get("org") else "")
        for x in lst(k.get("experience")))) if lst(k.get("experience")) else ""
    cred = ""
    if cert_count:
        if highlights:
            cred += '<ul class="cred-highlights">%s</ul>' % "".join("<li>%s</li>" % E(h) for h in highlights)
        gh = "".join('<div class="cred-group"><span class="card-label">%s</span><ul>%s</ul></div>'
                     % (E(g.get("group")), "".join("<li>%s</li>" % E(i) for i in lst(g["items"]))) for g in groups)
        cred += ('<details class="cred-all"><summary>See all %d certifications</summary><div class="cred-groups">%s</div></details>' % (cert_count, gh)
                 if highlights else '<div class="cred-groups">%s</div>' % gh)
    paid = [p for p in lst(k.get("pricing")) if not re.search(r"discovery call|free consultation", p.get("label", ""), re.I)]
    price = ('<div class="price-card"><div class="price-row price-lead"><span>30-Minute Discovery Call</span><b>Free</b></div>' +
             "".join('<div class="price-row"><span>%s%s</span><b>%s</b></div>'
                     % (E(p.get("label")), "<small>%s</small>" % E(p["note"]) if p.get("note") else "", E(p.get("price"))) for p in paid) +
             ("" if paid else '<p class="coach-note">Ask %s about session packages on your discovery call.</p>' % E(first)) +
             '<a class="btn btn-gold" href="%s" target="_blank" rel="noopener">WhatsApp %s</a>' % (wa_link, E(first)) +
             ('<p class="coach-note">%s</p>' % E(k["location"]) if k.get("location") else "") + "</div>")

    body = (sec("about", "About " + E(first), about) + sec("achievements", E(k.get("achievementsTitle") or "Achievements"), ach) +
            sec("experience", "Experience", exp) + sec("credentials", "Credentials", cred) +
            sec("sessions", "Sessions &amp; Pricing", price) +
            '<p class="coach-results-link"><a class="link-arrow" href="/results.html">See client results <span>→</span></a></p>')
    return ('<header class="coach-hero wrap"><div class="coach-photo coach-hero-photo">%s</div><div class="coach-hero-body">'
            '<span class="eyebrow">ReGen Coach</span><h1 class="h1 coach-hero-name">%s</h1>%s%s%s'
            '<div class="btn-row"><a class="btn btn-gold" href="%s" target="_blank" rel="noopener">WhatsApp %s</a>%s</div></div></header>'
            '<div class="wrap-narrow coach-body">%s</div>'
            % (photo(k.get("photo"), k.get("name")), E(k.get("name")),
               '<p class="coach-hero-spec">%s</p>' % E(k["specialty"]) if k.get("specialty") else "",
               offers_html(k, services),
               '<p class="coach-motto">"%s"</p>' % E(k["motto"]) if k.get("motto") else "",
               wa_link, E(first),
               ('<a class="btn btn-ghost" href="%s" target="_blank" rel="noopener">@%s</a>' % (ig, E(str(k["instagram"]).lstrip("@")))) if ig else "",
               body))


# ---------------------------------------------------------------- services
def creds_text(k):
    """All credential items of a coach joined into one string (same logic as assets/js/coach.js)."""
    parts = []
    for g in k.get("credentials") or []:
        parts += [g] if isinstance(g, str) else [i for i in (g.get("items") or []) if i]
    return " ".join(parts)


def coach_offers(k, svc):
    m = svc.get("coachMatch") or "*"
    return m == "*" or bool(re.search(m, creds_text(k), re.I))


def service_coaches(svc, ordered):
    return [k for k in ordered if coach_offers(k, svc)]


def service_url(svc, base):
    return "%s/%s/" % (base, svc["slug"])


def offers_html(k, services):
    mine = [s for s in services if coach_offers(k, s)]
    if not mine:
        return ""
    return ('<p class="coach-motto coach-offers">Offers: ' +
            " · ".join('<a href="/%s/">%s</a>' % (E(s["slug"]), E(s.get("short") or s["name"])) for s in mine) + "</p>")


def home_services_html(services):
    return "".join('<a class="card" href="/%s/"><span class="card-label">%s</span><span class="card-title">%s</span>'
                   '<span class="card-text">%s</span><span class="link-arrow">Learn more <span>→</span></span></a>'
                   % (E(s["slug"]), E(s.get("benefit") or "%02d" % (i + 1)), E(s["name"]), E(s["card"]), ) for i, s in enumerate(services))


SERVICE_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{desc}">
<!--pre:canon--><!--/pre:canon-->
<meta property="og:type" content="website">
<meta property="og:site_name" content="ReGen Performance">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0A0A0A">
<link rel="icon" type="image/png" href="/assets/img/favicon-32.png">
<link rel="apple-touch-icon" href="/assets/img/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{fonts}" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/site.css">
<!--pre:ld--><!--/pre:ld-->
</head>
<body data-page="services">
<main>
{body}
</main>
<script src="/assets/js/site.js"></script>
</body>
</html>
"""


def service_page_html(svc, services, ordered, site, reviews, base):
    wa_href = wa(site.get("whatsapp"), site.get("whatsappMessage") or "Hi ReGen, I'd like to book a free 30-minute discovery call.")
    wa_btn = '<a class="btn btn-gold" href="%s" target="_blank" rel="noopener">WhatsApp Us</a>' % E(wa_href)
    coaches = service_coaches(svc, ordered)
    who = "".join('<div class="card"><span class="card-text">%s</span></div>' % E(x) for x in svc.get("whoFor", []))
    steps_src = svc.get("whatToExpect", [])
    steps = "".join('<div class="card"><span class="step-num">%d</span><span class="card-text">%s</span></div>' % (i + 1, E(x))
                    for i, x in enumerate(steps_src))
    cols = "grid-3" if len(steps_src) % 3 == 0 else "grid-2"
    faq = "".join('<details><summary>%s</summary><div class="prose">%s</div></details>' % (E(f["question"]), md_html(f["answer"]))
                  for f in svc.get("faq", []))
    others = [s for s in services if s["slug"] != svc["slug"]]
    return (
        '<section class="page-hero">\n    <div class="glow"></div><div class="grain"></div>\n    <div class="wrap">\n'
        '      <span class="eyebrow">%s</span>\n      <h1 class="h2">%s</h1>\n      <p class="lead">%s</p>\n%s'
        '      <div class="btn-row" style="margin-top:2rem">%s<a class="btn btn-ghost" href="#coaches">Meet the Coaches</a></div>\n'
        '    </div>\n  </section>\n\n'
        '  <section class="section">\n    <div class="wrap">\n'
        '      <div class="section-head reveal"><span class="eyebrow">Who It\'s For</span><h2 class="h2">Is This <em>For You?</em></h2></div>\n'
        '      <div class="grid grid-2 reveal">%s</div>\n    </div>\n  </section>\n\n'
        '  <section class="section">\n    <div class="wrap">\n'
        '      <div class="section-head reveal"><span class="eyebrow">What to Expect</span><h2 class="h2">How It <em>Works</em></h2></div>\n'
        '      <div class="grid %s reveal steps">%s</div>\n    </div>\n  </section>\n\n'
        '  <section class="section">\n    <div class="wrap-narrow">\n'
        '      <div class="section-head reveal"><span class="eyebrow">Why ReGen</span><h2 class="h2">One System, <em>Every Session</em></h2></div>\n'
        '      <div class="prose reveal"><p>%s</p></div>\n'
        '      <p class="reveal" style="margin-top:1.6rem">Rated %s from %s Google reviews. <a class="link-arrow" href="%s" target="_blank" rel="noopener">Read them on Google <span>→</span></a></p>\n'
        '    </div>\n  </section>\n\n'
        '  <section class="section" id="coaches">\n    <div class="wrap">\n'
        '      <div class="section-head reveal"><span class="eyebrow">Our Team</span><h2 class="h2">Coaches Who <em>Offer This</em></h2></div>\n'
        '      <div class="coach-grid">%s</div>\n    </div>\n  </section>\n\n'
        '  <section class="section">\n    <div class="wrap-narrow">\n'
        '      <div class="section-head reveal"><span class="eyebrow">Questions</span><h2 class="h2">Common <em>Questions</em></h2></div>\n'
        '      <div class="faq">%s</div>\n    </div>\n  </section>\n\n'
        '  <section class="cta-band">\n    <div class="glow"></div>\n    <div class="wrap-narrow reveal">\n'
        '      <div class="hero-vline"></div>\n      <span class="eyebrow">Start Your Journey</span>\n'
        '      <h2 class="h2" style="margin-top:1rem">Book a Free<br><em>Discovery Call</em></h2>\n'
        '      <p class="lead">Thirty minutes. No pressure, just clarity on what your body needs and where to start.</p>\n'
        '      <div class="btn-row">%s</div>\n    </div>\n  </section>\n\n'
        '  <section class="section">\n    <div class="wrap">\n      <div class="label-rule">Also Part of Every ReGen Session</div>\n'
        '      <p style="display:flex;flex-wrap:wrap;gap:1.2rem 2rem;margin-top:1rem">%s</p>\n    </div>\n  </section>'
        % (E(svc["eyebrow"]), E(svc["h1"]), E(svc["lead"]),
           ('      <p class="coach-note">%s</p>\n' % E(svc["credentialNote"])) if svc.get("credentialNote") else "",
           wa_btn, who, cols, steps, E(svc["why"]), E(reviews.get("rating")), E(reviews.get("count")), E(reviews.get("googleUrl")),
           "".join(coach_card(k, site) for k in coaches), faq, wa_btn,
           "".join('<a class="link-arrow" href="/%s/">%s <span>→</span></a>' % (E(o["slug"]), E(o["name"])) for o in others)))


def service_ld(svc, services, site, base):
    url = service_url(svc, base)
    wa_href = wa(site.get("whatsapp"), site.get("whatsappMessage") or "")
    service = {"@context": "https://schema.org", "@type": "Service", "name": svc["name"], "serviceType": svc.get("short") or svc["name"],
               "description": svc["metaDescription"], "url": url,
               "areaServed": ["Robertson Quay", "River Valley", "Clarke Quay", "Singapore"],
               "provider": {"@id": base + "/#business"},
               "availableChannel": {"@type": "ServiceChannel", "serviceUrl": wa_href, "name": "WhatsApp"}}
    faq = {"@context": "https://schema.org", "@type": "FAQPage",
           "mainEntity": [{"@type": "Question", "name": f["question"],
                           "acceptedAnswer": {"@type": "Answer", "text": md_plain(f["answer"])}} for f in svc.get("faq", [])]}
    return [service, faq, crumbs([("Home", base + "/"), (svc["name"], url)])]


# ---------------------------------------------------------------- JSON-LD
def business_ld(site, reviews, coaches, base, services=()):
    loc = site.get("location", {})
    geo = loc.get("geo") or {}
    b = {"@context": "https://schema.org", "@type": "LocalBusiness", "@id": base + "/#business",
         "additionalType": "https://en.wikipedia.org/wiki/Personal_trainer",
         "name": "ReGen Performance", "url": base + "/",
         "description": "Personal training, pain rehab and strength coaching at Platinum Fitness, Robertson Quay, Singapore.",
         "logo": base + "/assets/img/logo-full-white.png", "image": base + "/assets/img/team-share.jpg",
         "telephone": site.get("phoneDisplay") or site.get("whatsappDisplay"), "priceRange": "$$",
         "address": {"@type": "PostalAddress", "streetAddress": "22 Martin Road, #04-01", "addressLocality": "Singapore",
                     "postalCode": "239058", "addressCountry": "SG"}}
    if geo.get("lat") is not None:
        b["geo"] = {"@type": "GeoCoordinates", "latitude": geo["lat"], "longitude": geo["lng"]}
    if reviews.get("googleUrl"):
        b["hasMap"] = reviews["googleUrl"]
    b["sameAs"] = [u for u in [(site.get("instagram") or {}).get("url"), (site.get("youtube") or {}).get("url"), reviews.get("googleUrl")] if u]
    b["areaServed"] = ["Robertson Quay", "River Valley", "Clarke Quay", "Singapore"]
    if loc.get("openingHours"):
        b["openingHoursSpecification"] = [dict({"@type": "OpeningHoursSpecification"}, **h) for h in loc["openingHours"]]
    if services:
        b["makesOffer"] = [{"@type": "Offer", "itemOffered": {"@type": "Service", "name": sv["name"], "url": service_url(sv, base)}}
                           for sv in services]
        b["knowsAbout"] = ["Personal training", "Injury rehabilitation", "Sports massage", "Osteopathic manual therapy", "Strength training"]
    b["employee"] = [{"@id": "%s/coaches/%s/#person" % (base, k["slug"])} for k in coaches]
    return b


def person_ld(k, base):
    url = "%s/coaches/%s/" % (base, k["slug"])
    p = {"@context": "https://schema.org", "@type": "Person", "@id": url + "#person", "name": k["name"],
         "jobTitle": "Personal Trainer", "image": base + (k.get("photo") or "/assets/img/team-share.jpg"), "url": url,
         "worksFor": {"@id": base + "/#business"}}
    ig = ig_url(k.get("instagram"))
    if ig:
        p["sameAs"] = [ig]
    if k.get("focus"):
        p["knowsAbout"] = [f for f in k["focus"] if f]
    creds = [h for h in (k.get("highlights") or []) if h]
    if not creds:
        for g in k.get("credentials") or []:
            creds += [g] if isinstance(g, str) else [i for i in g.get("items", []) if i]
    if creds:
        p["hasCredential"] = [{"@type": "EducationalOccupationalCredential", "name": c} for c in creds[:6]]
    return p


# ---------------------------------------------------------------- main
def main():
    site, reviews, resources = load("site"), load("reviews"), load("resources")
    services = sorted(load("services")["services"], key=lambda x: x.get("order", 99))
    coaches = load("coaches")["coaches"]
    base = (os.environ.get("URL") or site.get("siteUrl") or "").rstrip("/")
    loc = site.get("location", {})
    ordered = team_order(coaches, site.get("coachOrder") or {})
    rv = reviews.get("reviews", [])

    def read(name):
        with open(os.path.join(ROOT, name), encoding="utf-8") as f:
            return f.read()

    def write(name, text):
        path = os.path.join(ROOT, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    # ---- static pages: canonical + og:url on every indexable page, prerender, JSON-LD
    static = {"index.html": "/", "coaches.html": "/coaches.html", "results.html": "/results.html",
              "philosophy.html": "/philosophy.html", "resources.html": "/resources.html"}
    for fname, path in static.items():
        page = set_block(read(fname), "canon", canon(base + path), before='<link rel="icon"')
        lds = []
        if fname == "index.html":
            page = set_block(page, "services", home_services_html(services))
            page = set_block(page, "team", "".join(team_card(k) for k in ordered))
            page = set_block(page, "faq", faq_html(site))
            page = set_block(page, "visit", visit_html(site))
            page = set_block(page, "reviews", home_reviews_html(rv))
            lds = [business_ld(site, reviews, ordered, base, services),
                   {"@context": "https://schema.org", "@type": "WebSite", "@id": base + "/#website", "url": base + "/",
                    "name": "ReGen Performance", "publisher": {"@id": base + "/#business"}},
                   {"@context": "https://schema.org", "@type": "FAQPage",
                    "mainEntity": [{"@type": "Question", "name": f["question"],
                                    "acceptedAnswer": {"@type": "Answer", "text": md_plain(f["answer"])}} for f in site.get("faq", [])]}]
        elif fname == "coaches.html":
            page = set_block(page, "coaches", "".join(coach_card(k, site) for k in ordered))
            lds = [{"@context": "https://schema.org", "@type": "ItemList", "name": "ReGen Performance coaches",
                    "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": k["name"],
                                         "url": "%s/coaches/%s/" % (base, k["slug"])} for i, k in enumerate(ordered)]},
                   crumbs([("Home", base + "/"), ("Coaches", base + "/coaches.html")])]
        elif fname == "results.html":
            page = set_block(page, "reviews", results_reviews_html(rv, coaches))
        if lds:
            page = set_block(page, "ld", ld(*lds))
        write(fname, page)

    # ---- one page per coach
    out_dir = os.path.join(ROOT, "coaches")
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    for k in coaches:
        slug = k["slug"]
        e = lambda v: html.escape(str(v or ""), quote=True)
        url = f"{base}/coaches/{slug}/"
        desc = k.get("intro") or k.get("bio") or k.get("specialty") or "ReGen Performance coach in Singapore."
        title = f"{k['name']}, Personal Trainer in Robertson Quay, Singapore | ReGen Performance"
        page = TEMPLATE.format(
            name=e(k["name"]), slug=e(slug), specialty=e(k.get("specialty")), bio=e(k.get("bio")),
            title=e(title), desc=e(desc), url=e(url),
            image=e(base + (k.get("photo") or "/assets/img/team-share.jpg")), fonts=FONTS)
        page = set_block(page, "canon", canon(url))
        page = set_block(page, "coach", coach_profile_html(k, site, services))
        page = set_block(page, "ld", ld(person_ld(k, base), crumbs([("Home", base + "/"), ("Coaches", base + "/coaches.html"), (k["name"], url)])))
        write(f"coaches/{slug}/index.html", page)

    # ---- one page per service
    for svc in services:
        d = os.path.join(ROOT, svc["slug"])
        if os.path.isdir(d):
            shutil.rmtree(d)
        url = service_url(svc, base)
        page = SERVICE_PAGE.format(title=E(svc["title"]), desc=E(svc["metaDescription"]), fonts=FONTS,
                                   image=E(base + "/assets/img/team-share.jpg"),
                                   body=service_page_html(svc, services, ordered, site, reviews, base))
        page = set_block(page, "canon", canon(url))
        page = set_block(page, "ld", ld(*service_ld(svc, services, site, base)))
        write(svc["slug"] + "/index.html", page)

    # ---- sitemap.xml, robots.txt, llms.txt (generated on every deploy, git-ignored)
    urls = [base + "/"] + [service_url(sv, base) for sv in services]
    urls += [base + p for p in ["/coaches.html", "/results.html", "/philosophy.html", "/resources.html"]]
    urls += [f"{base}/coaches/{k['slug']}/" for k in coaches]
    urls += [f"{base}/resource.html?r={r['slug']}" for r in resources.get("resources", [])]
    top = {base + "/": "1.0"}
    top.update({service_url(sv, base): "0.9" for sv in services})
    prio = lambda u: "<priority>%s</priority>" % top[u] if u in top else ""
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
          "".join("  <url><loc>%s</loc>%s</url>\n" % (html.escape(u, quote=False), prio(u)) for u in urls) + "</urlset>\n")
    bots = ["GPTBot", "ClaudeBot", "PerplexityBot", "Google-Extended", "Applebot"]
    write("robots.txt", "User-agent: *\nAllow: /\n\n" + "".join("User-agent: %s\nAllow: /\n\n" % b for b in bots) +
          "Sitemap: %s/sitemap.xml\n" % base)

    mrt = [m for m in (loc.get("nearbyMrt") or []) if m]
    rating = "Google rating: %s out of 5 from %s reviews (%s)." % (reviews.get("rating"), reviews.get("count"), reviews.get("googleUrl"))
    lines = ["# ReGen Performance", "",
             "> ReGen Performance is a personal training and rehab coaching team in Robertson Quay, Singapore. "
             "It is not a gym. Coaches help clients move without pain, recover from injury and build lasting strength. "
             "Google Business category: Personal trainer.", "",
             "## Location", "- Address: %s (%s)" % (loc.get("address"), loc.get("name")),
             "- Inside Platinum Fitness, just above Common Man Coffee." if "Common Man" in (loc.get("note") or "") else None,
             ("- Nearest MRT stations: %s." % ", ".join(mrt)) if mrt else None,
             "- Serves Robertson Quay, River Valley, Clarke Quay and nearby areas of Singapore.", "",
             "## How to book",
             "- WhatsApp %s (%s)." % (site.get("phoneDisplay") or site.get("whatsappDisplay"), wa(site.get("whatsapp"))),
             "- Free 30-minute discovery call to discuss goals and movement needs.", "",
             "## Reviews", "- " + rating, "",
             "## Coaches"]
    lines += ["- [%s](%s/coaches/%s/): %s" % (k["name"], base, k["slug"], k.get("specialty") or "") for k in ordered]
    lines += ["", "## Services"]
    for sv in services:
        note = (" " + sv["credentialNote"]) if sv.get("credentialNote") else ""
        lines.append("- [%s](%s): %s%s" % (sv["name"], service_url(sv, base), sv["card"], note))
    lines += ["", "## Pages", "- [Home](%s/)" % base, "- [Coaches](%s/coaches.html)" % base,
              "- [Client results and Google reviews](%s/results.html)" % base,
              "- [The ReGen Method](%s/philosophy.html)" % base, "- [Resources](%s/resources.html)" % base]
    write("llms.txt", "\n".join(l for l in lines if l is not None).rstrip() + "\n")
    print(f"Built {len(coaches)} coach and {len(services)} service pages for {base or '(no base URL)'}")


if __name__ == "__main__":
    main()
