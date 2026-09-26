/* ReGen Performance site runtime.
   Renders shared chrome and exposes helpers (window.RG) for page scripts.
   Pages set <body data-page="home|philosophy|coaches|results|ebook|book|resources"> */
(function () {
  "use strict";

  var NAV = [
    { href: "/", label: "Home", page: "home" },
    { href: "/philosophy.html", label: "Philosophy", page: "philosophy" },
    { href: "/coaches.html", label: "Coaches", page: "coaches" },
    { href: "/results.html", label: "Results", page: "results" },
    { href: "/ebook/", label: "Ebook", page: "ebook" }
  ];

  var WA_ICON = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.5 14.4c-.3-.1-1.8-.9-2-1-.3-.1-.5-.1-.7.1-.2.3-.8 1-.9 1.2-.2.2-.3.2-.6.1-.3-.1-1.3-.5-2.4-1.5-.9-.8-1.5-1.8-1.7-2.1-.2-.3 0-.5.1-.6l.4-.5c.2-.2.2-.3.3-.5.1-.2 0-.4 0-.5l-.9-2.2c-.2-.6-.5-.5-.7-.5h-.6c-.2 0-.5.1-.8.4-.3.3-1 1-1 2.5s1.1 2.9 1.2 3.1c.1.2 2.1 3.2 5.1 4.5.7.3 1.3.5 1.7.6.7.2 1.4.2 1.9.1.6-.1 1.8-.7 2-1.4.2-.7.2-1.3.2-1.4-.1-.2-.3-.3-.6-.4zM12 21.8c-1.8 0-3.5-.5-5-1.4l-.4-.2-3.7 1 1-3.6-.2-.4C2.7 15.6 2.2 13.8 2.2 12 2.2 6.6 6.6 2.2 12 2.2c2.6 0 5.1 1 6.9 2.9 1.8 1.8 2.9 4.3 2.9 6.9 0 5.4-4.4 9.8-9.8 9.8zM20.5 3.5C18.2 1.2 15.2 0 12 0 5.4 0 0 5.4 0 12c0 2.1.6 4.2 1.6 6L0 24l6.2-1.6c1.8 1 3.8 1.5 5.8 1.5 6.6 0 12-5.4 12-12 0-3.2-1.2-6.2-3.5-8.4z"/></svg>';

  var cache = {};
  function load(name) {
    if (!cache[name]) {
      cache[name] = fetch("/content/" + name + ".json", { cache: "no-cache" })
        .then(function (r) { if (!r.ok) throw new Error(name + " " + r.status); return r.json(); })
        .catch(function (e) { console.error("[RG] content load failed:", e); return {}; });
    }
    return cache[name];
  }

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function wa(number, message) {
    var n = String(number || "").replace(/\D/g, "");
    return "https://wa.me/" + n + (message ? "?text=" + encodeURIComponent(message) : "");
  }

  function igUrl(handle) {
    var h = String(handle || "").replace(/^@/, "").replace(/^https?:\/\/(www\.)?instagram\.com\//, "").replace(/\/.*$/, "");
    return h ? "https://www.instagram.com/" + h : "";
  }

  function ytId(v) {
    var s = String(v || "").trim();
    var m = s.match(/(?:youtu\.be\/|v=|embed\/|shorts\/)([\w-]{11})/);
    return m ? m[1] : (/^[\w-]{11}$/.test(s) ? s : "");
  }

  // Click-to-load YouTube embed: fast page loads, no third-party cookies until played.
  function video(id, title) {
    id = ytId(id);
    if (!id) return "";
    return '<div class="video" data-yt="' + id + '" role="button" tabindex="0" aria-label="Play video: ' + esc(title || "video") + '">' +
      '<img src="https://i.ytimg.com/vi/' + id + '/hqdefault.jpg" alt="" loading="lazy">' +
      '<span class="video-play"></span></div>';
  }
  function playVideo(el) {
    var id = el.getAttribute("data-yt");
    el.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1&rel=0" title="YouTube video" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>';
    el.removeAttribute("role"); el.removeAttribute("tabindex"); el.style.cursor = "default";
  }
  document.addEventListener("click", function (e) {
    var v = e.target.closest && e.target.closest(".video[data-yt]");
    if (v && !v.querySelector("iframe")) playVideo(v);
  });
  document.addEventListener("keydown", function (e) {
    if ((e.key === "Enter" || e.key === " ") && e.target.matches && e.target.matches(".video[data-yt]")) { e.preventDefault(); playVideo(e.target); }
  });

  // Lightbox for any .gallery-item[data-full]
  document.addEventListener("click", function (e) {
    var g = e.target.closest && e.target.closest(".gallery-item[data-full]");
    if (!g) return;
    var d = document.createElement("dialog");
    d.className = "lightbox";
    d.innerHTML = '<img src="' + esc(g.getAttribute("data-full")) + '" alt=""><button class="lightbox-close" aria-label="Close">×</button>';
    document.body.appendChild(d);
    d.addEventListener("click", function () { d.close(); });
    d.addEventListener("close", function () { d.remove(); });
    d.showModal();
  });

  // Markdown -> HTML (marked is loaded from CDN on pages that need it). Supports [youtube:ID] lines.
  function md(text) {
    var src = String(text || "").replace(/^\[youtube:([\w-]{11})\]\s*$/gm, function (_, id) { return "\n<!--yt:" + id + "-->\n"; });
    var html = window.marked ? window.marked.parse(src, { breaks: true }) : "<p>" + esc(src).replace(/\n\n+/g, "</p><p>").replace(/\n/g, "<br>") + "</p>";
    return html.replace(/<!--yt:([\w-]{11})-->/g, function (_, id) { return video(id); });
  }

  function stars(n) {
    n = Math.max(0, Math.min(5, Math.round(Number(n) || 5)));
    return '<span class="stars" aria-label="' + n + ' out of 5 stars">' + "★★★★★".slice(0, n) + '<span style="opacity:.25">' + "★★★★★".slice(0, 5 - n) + "</span></span>";
  }

  function initials(name) {
    return String(name || "").split(/\s+/).filter(Boolean).slice(0, 2).map(function (w) { return w[0]; }).join("").toUpperCase();
  }

  function photo(src, name) {
    return src
      ? '<img src="' + esc(src) + '" alt="' + esc(name) + '" loading="lazy">'
      : '<div class="photo-placeholder"><span>' + esc(initials(name)) + "</span></div>";
  }

  function renderChrome(site) {
    var page = document.body.getAttribute("data-page") || "";
    var waHref = wa(site.whatsapp || "6591875632", site.whatsappMessage || "Hi ReGen, I'd like to book a free 30-minute discovery call.");
    var ig = (site.instagram && site.instagram.url) || "https://www.instagram.com/regenperformance.sg";
    var yt = (site.youtube && site.youtube.url) || "https://www.youtube.com/@ReGenPerformanceEducation";

    var links = NAV.map(function (n) {
      return '<li><a href="' + n.href + '"' + (n.page === page ? ' aria-current="page"' : "") + ">" + n.label + "</a></li>";
    }).join("") + '<li><a class="btn btn-gold" href="/book.html"' + (page === "book" ? ' aria-current="page"' : "") + ">Book a Call</a></li>";

    var header = document.createElement("header");
    header.className = "site-nav";
    header.innerHTML =
      '<div class="wrap">' +
      '<a class="brand" href="/" aria-label="ReGen Performance home"><img src="/assets/img/logo-mark-gold.png" alt="" width="44" height="30"><span>Regen Performance</span></a>' +
      '<button class="nav-toggle" aria-label="Open menu" aria-expanded="false" aria-controls="nav-links"><span></span></button>' +
      '<ul class="nav-links" id="nav-links">' + links + "</ul></div>";
    document.body.insertBefore(header, document.body.firstChild);

    var bar = document.createElement("div");
    bar.className = "progress-bar";
    document.body.insertBefore(bar, document.body.firstChild);

    var toggle = header.querySelector(".nav-toggle");
    toggle.addEventListener("click", function () {
      var open = document.body.classList.toggle("nav-open");
      toggle.setAttribute("aria-expanded", open);
      toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
      document.body.style.overflow = open ? "hidden" : "";
    });
    header.querySelectorAll(".nav-links a").forEach(function (a) {
      a.addEventListener("click", function () { document.body.classList.remove("nav-open"); document.body.style.overflow = ""; });
    });

    var footer = document.createElement("footer");
    footer.className = "site-footer";
    footer.innerHTML =
      '<div class="wrap"><div class="footer-grid">' +
      '<div class="footer-brand"><img src="/assets/img/logo-full-gold.png" alt="ReGen Performance" width="78" height="64"><p>Movement and strength coaching in Singapore. The body is not broken. It is just not working as a system yet.</p></div>' +
      '<div class="footer-col"><h4>Explore</h4><ul>' +
      '<li><a href="/philosophy.html">The ReGen Method</a></li><li><a href="/coaches.html">Our Coaches</a></li><li><a href="/results.html">Client Results</a></li><li><a href="/resources.html">Resources</a></li><li><a href="/ebook/">Built From Within Ebook</a></li></ul></div>' +
      '<div class="footer-col"><h4>Follow</h4><ul>' +
      '<li><a href="' + esc(ig) + '" target="_blank" rel="noopener">Instagram</a></li><li><a href="' + esc(yt) + '" target="_blank" rel="noopener">YouTube</a></li></ul></div>' +
      '<div class="footer-col"><h4>Visit</h4><ul>' +
      "<li>" + esc((site.location && site.location.name) || "Platinum Fitness") + "</li>" +
      "<li>" + esc((site.location && site.location.address) || "22 Martin Road, Level 4, Singapore 239058") + "</li>" +
      '<li><a href="' + waHref + '" target="_blank" rel="noopener">WhatsApp ' + esc(site.whatsappDisplay || "+65 9187 5632") + "</a></li></ul></div>" +
      '</div><div class="footer-base"><span>© ' + new Date().getFullYear() + " ReGen Performance · Singapore</span><span>Built From Within</span></div></div>";
    document.body.appendChild(footer);

    if (page !== "book") {
      var f = document.createElement("a");
      f.className = "wa-float";
      f.href = waHref; f.target = "_blank"; f.rel = "noopener";
      f.setAttribute("aria-label", "WhatsApp us to book a free discovery call");
      f.innerHTML = WA_ICON + '<span class="wa-label">Free Discovery Call</span>';
      document.body.appendChild(f);
    }

    window.addEventListener("scroll", function () {
      var h = document.documentElement.scrollHeight - innerHeight;
      bar.style.width = (h > 0 ? (scrollY / h) * 100 : 0) + "%";
    }, { passive: true });
  }

  function observeReveal(root) {
    var els = (root || document).querySelectorAll(".reveal:not(.in)");
    if (!("IntersectionObserver" in window)) { els.forEach(function (el) { el.classList.add("in"); }); return; }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } });
    }, { rootMargin: "0px 0px -8% 0px" });
    els.forEach(function (el) {
      // Blocks taller than the screen would sit invisible mid-scroll, so show them at once.
      if (el.offsetHeight > innerHeight * 0.8) el.classList.add("in"); else io.observe(el);
    });
  }

  function param(name) { return new URLSearchParams(location.search).get(name) || ""; }

  var readyFns = [];
  window.RG = {
    load: load, esc: esc, wa: wa, igUrl: igUrl, ytId: ytId, video: video, md: md, stars: stars, photo: photo, param: param,
    reveal: observeReveal,
    ready: function (fn) { readyFns.push(fn); }
  };

  function boot() {
    load("site").then(function (site) {
      window.RG.site = site;
      renderChrome(site);
      return Promise.all(readyFns.map(function (fn) { try { return fn(site); } catch (e) { console.error(e); } }));
    }).then(function () {
      observeReveal();
      // Content rendered after load shifts layout, so re-apply any #anchor jump.
      if (location.hash.length > 1) {
        var t = document.getElementById(decodeURIComponent(location.hash.slice(1)));
        if (t) requestAnimationFrame(function () { t.scrollIntoView(); });
      }
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
