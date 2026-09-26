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
/admin/                Decap CMS
/assets/css/site.css   Design system
/assets/js/site.js     Chrome + JSON rendering helpers
/assets/img/           logo-*.png, icons, coaches/<slug>.jpg, resources/*
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
Every profile uses one standard layout (reference: `issac-tan`). Empty fields hide their section. Coaches are shown in random order (`RG.shuffle`) so no one is always first. `order` is unused.
```json
{ "coaches": [ {
  "slug": "issac-tan", "name": "Issac Tan", "photo": "/assets/img/coaches/issac-tan.jpg",
  "specialty": "one-line tagline, <= 60 chars",
  "intro": "one first-person sentence",
  "bio": "2 sentences for cards",
  "motto": "",
  "focus": ["3-5 short tags"],
  "approach": "markdown, 1-4 short paragraphs",
  "since": "2011",
  "experience": [ { "role": "", "org": "", "period": "" } ],
  "highlights": [ "up to 6 key certifications" ],
  "credentials": [ { "group": "", "items": [ "" ] } ],
  "pricing": [ { "label": "", "price": "", "note": "" } ],
  "whatsapp": "6591875632", "instagram": "issactanruizhi", "location": "",
  "videos": [ { "title": "", "youtubeId": "" } ],
  "more": "markdown, collapsed 'More about' section",
  "notionUrl": ""
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
{ "googleUrl": "", "rating": "", "count": "", "reviews": [ { "name": "", "rating": 5, "text": "", "date": "", "coaches": ["slug"], "featured": false } ] }
```
Reviews are verbatim. `coaches` puts a review on those coaches' profiles. `featured` (about 12, balanced across coaches) shows first on Results and rotates on Home.
```
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
