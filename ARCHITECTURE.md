# ReGen Performance website: architecture contract

A static site with no build step. Pages are plain HTML files. Shared chrome (nav, footer, WhatsApp button) and content are rendered by `assets/js/site.js`, which reads the JSON files in `/content`. Decap CMS (`/admin`) edits those same JSON files through GitHub, and Netlify redeploys on every commit.

## Folder layout
```
/index.html            Home
/philosophy.html       The ReGen Method (content from the ebook)
/coaches.html          Coach grid
/coach.html?c=<slug>   Single coach profile
/results.html          Video testimonials + Google reviews + client results
/resources.html        Knowledge Nuggets list
/resource.html?r=<slug> Single resource
/book.html             Discovery call, WhatsApp, location, pricing, FAQ
/ebook/index.html      Original "Built From Within" ebook (kept as-is)
/admin/                Decap CMS
/assets/css/site.css   Design system
/assets/js/site.js     Chrome + JSON rendering helpers
/assets/img/           logo-*.png, icons, coaches/<slug>.jpg, ebook/*, resources/*
/content/*.json        All editable content
```

## Rules for content JSON
- UTF-8. Keep the owner's wording exactly. Do not rewrite or summarise, except where a field is explicitly marked "short".
- Strip Notion hashtag spam (#FitnessTransformation …) and emoji that is used as bullet decoration. Keep everything else.
- WhatsApp numbers are digits only with country code, e.g. `"6591875632"`.
- Image paths are root-relative, e.g. `"/assets/img/coaches/issac-tan.jpg"`.
- Long text fields (`body`, `about`, `story`, `answer`) are Markdown strings.
- Unknown values: use `""`, never invented content.

### content/site.json
```json
{
  "whatsapp": "6591875632",
  "whatsappDisplay": "+65 9187 5632",
  "whatsappMessage": "Hi ReGen, I'd like to book a free 30-minute discovery call.",
  "instagram": { "handle": "@regenperformance.sg", "url": "https://www.instagram.com/regenperformance.sg" },
  "youtube": { "handle": "@ReGenPerformanceEducation", "url": "https://www.youtube.com/@ReGenPerformanceEducation" },
  "location": { "name": "Platinum Fitness", "address": "22 Martin Road, Level 4, Singapore 239058", "note": "Just above Common Man Coffee", "mapsUrl": "" },
  "quote": { "text": "", "author": "" },
  "mission": { "title": "", "body": "" },
  "offer": [ "" ],
  "discoveryCall": { "title": "30-Minute Discovery Call", "price": "Free", "body": "" },
  "pricing": [ { "label": "", "price": "", "note": "" } ],
  "faq": [ { "question": "", "answer": "" } ]
}
```

### content/coaches.json
```json
{ "coaches": [ {
  "slug": "issac-tan",
  "name": "Issac Tan",
  "specialty": "short: one line, <= 70 chars",
  "bio": "short: 2-3 sentences for the card, taken from the coach's own words",
  "about": "markdown: full profile text from Notion",
  "motto": "",
  "credentials": [ "" ],
  "photo": "/assets/img/coaches/issac-tan.jpg",
  "whatsapp": "6591875632",
  "instagram": "issactanruizhi",
  "location": "",
  "pricing": [ { "label": "", "price": "" } ],
  "videos": [ { "title": "", "youtubeId": "" } ],
  "notionUrl": "",
  "order": 1
} ] }
```

### content/testimonials.json
```json
{ "testimonials": [ {
  "name": "Li Ju",
  "headline": "",
  "story": "markdown",
  "youtubeId": "SA8zILNJasU",
  "coach": "slug or empty",
  "featured": true
} ] }
```

### content/reviews.json
```json
{ "googleUrl": "", "rating": "", "count": "", "reviews": [ { "name": "", "rating": 5, "text": "", "date": "" } ] }
```

### content/resources.json
```json
{ "resources": [ {
  "slug": "breathing", "title": "Breathing", "emoji": "🫁",
  "summary": "short: 1-2 sentences", "body": "markdown", "cover": "", "notionUrl": ""
} ] }
```

### content/videos.json
```json
{ "methodology": [ { "title": "", "youtubeId": "", "description": "" } ] }
```

## Brand
Colours: `#070707` ink, `#ede8dc` cream, `#fafaf8` white, `#c4a052` gold, `#d4b06a` gold-bright, `#7a736a` muted, `#111009` card, `#191612` card2, borders `rgba(196,160,82,.11)` / `.26`.
Fonts: Playfair Display (headings, italic gold `<em>` for emphasis), DM Sans 300 (body), DM Mono (uppercase, wide-tracked labels).
Tone: calm, premium, educational. Short sentences. The body is not broken; it just isn't working as a system yet.
