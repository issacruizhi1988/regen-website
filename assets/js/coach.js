/* Coach profile renderer, shared by /coaches/<slug>/ pages. */
RG.ready(async function (site) {
  var slug = document.body.getAttribute("data-coach") || RG.param("c");
  var c = await RG.load("coaches");
  var all = c.coaches || [];
  var coach = all.find(function (k) { return k.slug === slug; });
  var root = document.getElementById("coach-root");
  var E = RG.esc;

  if (!coach) {
    root.innerHTML = '<div class="wrap" style="padding:3rem 1.5rem"><div class="empty">We couldn\'t find that coach.<br><br><a class="link-arrow" href="/coaches.html">Back to all coaches <span>→</span></a></div></div>';
    return;
  }

  var first = (coach.name || "").split(/\s+/)[0] || "there";
  document.title = coach.name + " · ReGen Performance";
  // Meta and link-preview tags are written by tools/build.py for each coach page.

  var waLink = RG.wa(coach.whatsapp || site.whatsapp, "Hi " + first + ", I found you on the ReGen Performance website and I'd like to book a free discovery call.");
  var ig = RG.igUrl(coach.instagram);
  var list = function (a) { return (a || []).filter(function (x) { return x && (typeof x === "string" ? x.trim() : true); }); };

  // Credentials may be grouped [{group, items}] or a flat list of strings.
  var groups = list(coach.credentials);
  if (groups.length && typeof groups[0] === "string") groups = [{ group: "Certifications", items: groups }];
  groups = groups.filter(function (g) { return list(g.items).length; });
  var certCount = groups.reduce(function (n, g) { return n + list(g.items).length; }, 0);
  var highlights = list(coach.highlights);
  if (!highlights.length && certCount <= 8) highlights = [];


  var facts = [];
  var years = /^\d{4}$/.test(coach.since || "") ? new Date().getFullYear() - Number(coach.since) : 0;
  if (years > 0) facts.push(["Experience", years + "+ years · since " + coach.since]);
  if (coach.location) facts.push(["Trains at", coach.location.split(",")[0]]);

  var sections = [];
  function section(id, label, title, html) {
    if (!html) return;
    sections.push([id, label]);
    return '<section class="coach-sec" id="' + id + '"><div class="label-rule">' + label + '</div>' + (title ? '<h2 class="h3 coach-sec-title">' + title + '</h2>' : '') + html + '</section>';
  }

  var aboutHtml =
    (coach.intro ? '<p class="coach-intro">' + E(coach.intro) + '</p>' : '') +
    (coach.approach ? '<div class="prose">' + RG.md(coach.approach) + '</div>' : (coach.about ? '<div class="prose">' + RG.md(coach.about) + '</div>' : '')) +
    (list(coach.focus).length ? '<div class="focus-list">' + list(coach.focus).map(function (f) { return '<span class="focus">' + E(f) + '</span>'; }).join("") + '</div>' : '');


  // Achievements: competition results and wins, plus photos (tap to enlarge).
  var gallery = list(coach.gallery).filter(function (g) { return g.src; });
  var achHtml = (list(coach.achievements).length ? '<ul class="ach-list">' + list(coach.achievements).map(function (a) { return '<li>' + E(a) + '</li>'; }).join("") + '</ul>' : '') +
    (gallery.length ? '<div class="photo-wall coach-gallery">' + gallery.map(function (g) {
      return '<button class="gallery-item wall-item" type="button" data-full="' + E(g.src) + '" data-caption="' + E(g.caption) + '" data-group="coach-gallery">' +
        '<img src="' + E(g.src.indexOf("/coaches/gallery/") >= 0 ? g.src.replace("/gallery/", "/gallery/thumbs/") : g.src) + '" alt="' + E(g.caption || coach.name) + '" decoding="async"></button>';
    }).join("") + '</div>' : '');

  var expHtml = list(coach.experience).length ? '<ol class="timeline">' + list(coach.experience).map(function (x) {
    return '<li><span class="timeline-period">' + E(x.period) + '</span><span class="timeline-role">' + E(x.role) + '</span>' + (x.org ? '<span class="timeline-org">' + E(x.org) + '</span>' : '') + '</li>';
  }).join("") + '</ol>' : '';

  var credHtml = "";
  if (certCount) {
    if (highlights.length) credHtml += '<ul class="cred-highlights">' + highlights.map(function (h) { return '<li>' + E(h) + '</li>'; }).join("") + '</ul>';
    var groupsHtml = groups.map(function (g) {
      return '<div class="cred-group"><span class="card-label">' + E(g.group) + '</span><ul>' + list(g.items).map(function (i) { return '<li>' + E(i) + '</li>'; }).join("") + '</ul></div>';
    }).join("");
    credHtml += highlights.length
      ? '<details class="cred-all"><summary>See all ' + certCount + ' certifications</summary><div class="cred-groups">' + groupsHtml + '</div></details>'
      : '<div class="cred-groups">' + groupsHtml + '</div>';
  }

  var priceHtml = '<div class="price-card">' +
    '<div class="price-row price-lead"><span>30-Minute Discovery Call</span><b>Free</b></div>' +
    list(coach.pricing).filter(function (p) { return !/discovery|consultation/i.test(p.label); }).map(function (p) {
      return '<div class="price-row"><span>' + E(p.label) + (p.note ? '<small>' + E(p.note) + '</small>' : '') + '</span><b>' + E(p.price) + '</b></div>';
    }).join("") +
    (list(coach.pricing).filter(function (p) { return !/discovery|consultation/i.test(p.label); }).length ? '' : '<p class="coach-note">Ask ' + E(first) + ' about session packages on your discovery call.</p>') +
    '<a class="btn btn-gold" href="' + waLink + '" target="_blank" rel="noopener">WhatsApp ' + E(first) + '</a>' +
    (coach.location ? '<p class="coach-note">' + E(coach.location) + '</p>' : '') + '</div>';

  var moreHtml = coach.more ? '<details class="cred-all"><summary>More about ' + E(first) + '</summary><div class="prose" style="margin-top:1.2rem">' + RG.md(coach.more) + '</div></details>' : '';

  var body =
    (section("about", "About " + E(first), "", aboutHtml) || "") +
    (section("achievements", "Achievements", "", achHtml) || "") +
    (section("experience", "Experience", "", expHtml) || "") +
    (section("credentials", "Credentials", "", credHtml) || "") +
    (section("sessions", "Sessions &amp; Pricing", "", priceHtml) || "") +
    (moreHtml ? '<section class="coach-sec">' + moreHtml + '</section>' : "") +
    '<p class="coach-results-link"><a class="link-arrow" href="/results.html">See client results <span>→</span></a></p>';

  var others = all.filter(function (k) { return k.slug !== slug; }).sort(function () { return Math.random() - 0.5; }).slice(0, 3);

  root.innerHTML =
    '<header class="coach-hero wrap">' +
      '<div class="coach-photo coach-hero-photo">' + RG.photo(coach.photo, coach.name) + '</div>' +
      '<div class="coach-hero-body">' +
        '<span class="eyebrow">ReGen Coach</span>' +
        '<h1 class="h1 coach-hero-name">' + E(coach.name) + '</h1>' +
        (coach.specialty ? '<p class="coach-hero-spec">' + E(coach.specialty) + '</p>' : '') +
        (coach.motto ? '<p class="coach-motto">"' + E(coach.motto) + '"</p>' : '') +
        (facts.length ? '<dl class="coach-facts">' + facts.map(function (f) { return '<div><dt>' + E(f[0]) + '</dt><dd>' + E(f[1]) + '</dd></div>'; }).join("") + '</dl>' : '') +
        '<div class="btn-row"><a class="btn btn-gold" href="' + waLink + '" target="_blank" rel="noopener">WhatsApp ' + E(first) + '</a>' +
        (ig ? '<a class="btn btn-ghost" href="' + ig + '" target="_blank" rel="noopener">@' + E(String(coach.instagram).replace(/^@/, "")) + '</a>' : '') +
        '<button class="btn btn-ghost share-btn" type="button">Share profile</button></div>' +
      '</div>' +
    '</header>' +
    '<nav class="coach-tabs" aria-label="Profile sections"><div class="wrap">' + sections.map(function (s) { return '<a href="#' + s[0] + '">' + s[1].replace(/^About .*/, "About") + '</a>'; }).join("") + '</div></nav>' +
    '<div class="wrap-narrow coach-body">' + body + '</div>' +
    (others.length ? '<section class="section"><div class="wrap"><div class="label-rule">Meet the Team</div><div class="coach-grid">' + others.map(RG.coachCard).join("") + '</div></div></section>' : '');


  // Never leave an empty cell in the gallery: stretch the last photo across leftover columns.
  var wall = root.querySelector(".coach-gallery");
  function fillGallery() {
    if (!wall) return;
    var items = wall.children, n = items.length, cols = getComputedStyle(wall).gridTemplateColumns.split(" ").length;
    for (var i = 0; i < n; i++) { items[i].style.gridColumn = ""; items[i].style.aspectRatio = ""; }
    var r = n % cols;
    if (r) { var span = cols - r + 1; items[n - 1].style.gridColumn = "span " + span; items[n - 1].style.aspectRatio = span + " / 1"; }
  }
  fillGallery(); window.addEventListener("resize", fillGallery);

  var share = root.querySelector(".share-btn");
  share.addEventListener("click", function () {
    var url = location.origin + "/coaches/" + slug + "/";
    var data = { title: coach.name + " · ReGen Performance", text: coach.name + ": " + (coach.specialty || "ReGen Performance coach"), url: url };
    if (navigator.share) { navigator.share(data).catch(function () {}); return; }
    var done = function () { share.textContent = "Link copied ✓"; setTimeout(function () { share.textContent = "Share profile"; }, 2200); };
    if (navigator.clipboard) navigator.clipboard.writeText(url).then(done, function () { prompt("Copy this link:", url); });
    else prompt("Copy this link:", url);
  });

  var cta = document.getElementById("cta-wa");
  cta.href = waLink; cta.textContent = "WhatsApp " + first;
  document.getElementById("cta-section").hidden = false;
  RG.reveal(root);
});
