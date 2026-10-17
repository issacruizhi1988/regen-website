#!/usr/bin/env python3
"""Generate one static page per coach at /coaches/<slug>/ from content/coaches.json.

Static pages give every coach a clean, shareable link whose WhatsApp/social
preview shows that coach's photo and name. Netlify runs this on every deploy
(see netlify.toml), so edits made in /admin appear automatically.
Run locally with: python3 tools/build.py
"""
import html, json, os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = ("https://fonts.googleapis.com/css2?family=Inter+Tight:ital,wght@0,500;0,600;0,700;0,800;1,700"
         "&family=Inter:wght@300;400;500;600&display=swap")

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} · ReGen Performance</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="profile">
<meta property="og:site_name" content="ReGen Performance">
<meta property="og:title" content="{name} · ReGen Performance">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
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
</head>
<body data-page="coaches" data-coach="{slug}">
<main>
  <div class="wrap" style="padding-top:2rem">
    <a class="link-arrow" href="/coaches.html"><span style="transform:rotate(180deg)">→</span> All coaches</a>
  </div>
  <div id="coach-root">
    <noscript><div class="wrap" style="padding:2rem 1.5rem"><h1 class="h2">{name}</h1><p class="lead">{specialty}</p><p class="body">{bio}</p></div></noscript>
    <div class="skeleton">Loading profile</div>
  </div>

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


def main():
    coaches = json.load(open(os.path.join(ROOT, "content/coaches.json"), encoding="utf-8"))["coaches"]
    site = json.load(open(os.path.join(ROOT, "content/site.json"), encoding="utf-8"))
    base = (os.environ.get("URL") or site.get("siteUrl") or "").rstrip("/")
    out_dir = os.path.join(ROOT, "coaches")
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir)
    for k in coaches:
        slug = k["slug"]
        e = lambda v: html.escape(str(v or ""), quote=True)
        desc = k.get("intro") or k.get("bio") or k.get("specialty") or "ReGen Performance coach in Singapore."
        page = TEMPLATE.format(
            name=e(k["name"]), slug=e(slug), specialty=e(k.get("specialty")), bio=e(k.get("bio")),
            desc=e(desc), url=e(f"{base}/coaches/{slug}/"),
            image=e(base + (k.get("photo") or "/assets/img/team-share.jpg")), fonts=FONTS)
        os.makedirs(os.path.join(out_dir, slug), exist_ok=True)
        with open(os.path.join(out_dir, slug, "index.html"), "w", encoding="utf-8") as f:
            f.write(page)
    print(f"Built {len(coaches)} coach pages for {base or '(no base URL)'}")


if __name__ == "__main__":
    main()
