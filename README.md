# ReGen Performance Website — Owner's Guide

This is a plain, no-build website. There's nothing to "compile" — you edit content, and the site updates. Follow the steps below in order the first time you set this up. After that, you'll only ever need step (E) and (F).

## A) What's in this folder

- **Pages** — `index.html`, `coaches.html`, `results.html`, etc. These are the actual web pages. You shouldn't need to edit these directly.
- **`content/`** — all the editable text: coach profiles, reviews, resources, FAQ, WhatsApp number. This is what the admin panel edits for you.
- **`admin/`** — the admin panel (Decap CMS) you'll log into to edit `content/` without touching code.
- **`assets/`** — images, styles, and site scripts.
- **`netlify.toml`** — hosting configuration for Netlify. You shouldn't need to touch this.

## B) Preview the site on your own computer

1. Open the Terminal app.
2. Navigate into this folder, e.g. `cd path/to/regen-website`
3. Run:
   ```
   python3 -m http.server 8000
   ```
4. Open your browser to **http://localhost:8000**
5. Press `Ctrl+C` in Terminal to stop the preview when you're done.

## C) First deploy (one-time setup)

**1. Put the code on GitHub**

Create a new, empty repository on GitHub named `regen-website` (github.com → New repository). Do not add a README/license there. Then in Terminal, inside this folder, run:

```
git init
git add .
git commit -m "Initial site"
git branch -M main
git remote add origin https://github.com/issacruizhi1988/regen-website.git
git push -u origin main
```

Replace `USERNAME` with your actual GitHub username.

**2. Connect it to Netlify**

1. Go to [netlify.com](https://www.netlify.com) and log in (or sign up).
2. Click **Add new site → Import an existing project → Deploy with GitHub**.
3. Pick the `regen-website` repository.
4. Leave **Build command** empty and set **Publish directory** to `.` (a single dot).
5. Click **Deploy**. Netlify will give you a `*.netlify.app` address — the site is now live.

## D) Enable the admin panel (`/admin`)

This lets you (or ReGen staff) log in and edit content from a browser, no code required.

1. **Point the admin panel at your repo.** Open `admin/config.yml` in this folder and change the `repo:` line to your GitHub username, e.g.:
   ```
   repo: your-username/regen-website
   ```
   Commit and push that change (`git add admin/config.yml && git commit -m "Set repo" && git push`).

2. **Create a GitHub OAuth App.**
   - In GitHub, go to **Settings → Developer settings → OAuth Apps → New OAuth App**.
   - Homepage URL: your Netlify site address (e.g. `https://your-site-name.netlify.app`).
   - Authorization callback URL: `https://api.netlify.com/auth/done`
   - Click **Register application**, then **Generate a new client secret**. Keep this tab open — you'll need the Client ID and Client Secret in the next step.

3. **Install the provider in Netlify.**
   - In your Netlify site, go to **Site configuration → Access & security → OAuth**.
   - Under **Authentication providers**, click **Install provider**, choose **GitHub**, and paste in the Client ID and Client Secret from GitHub.
   - Save.

4. **Log in.** Visit `https://your-site-name.netlify.app/admin/`, click **Login with GitHub**, and authorize it. You should see the admin dashboard with Coaches, Client Stories, Google Reviews, Resources, Videos, and Site Settings.

   *(These steps match Decap CMS's current GitHub-backend + Netlify OAuth setup. If the Netlify menu names ever shift slightly, look for "OAuth" under your site's security/access settings — the concept is the same.)*

## E) Everyday editing

Once logged into `/admin/`:

- **Add a coach** → Coaches → Coaches → add a new item to the list → fill in name, photo, bio, WhatsApp, etc. → **Save**, then **Publish**.
- **Add a Google review** → Google Reviews → add a new item under Reviews → name, star rating, text, date → **Publish**.
- **Add a client story** → Client Stories → add a new item → name, headline, story, optional YouTube video ID → **Publish**.
- **Add a resource (Knowledge Nugget)** → Resources → add a new item → slug, title, emoji, summary, body → **Publish**.

Every **Publish** commits straight to GitHub, and Netlify rebuilds the live site automatically within a minute or two.

## F) Changing the WhatsApp number

Go to **Site Settings** in the admin panel and update **WhatsApp Number** (digits + country code, e.g. `6591875632`) and **WhatsApp Display Number** (e.g. `+65 9187 5632`). This number is used sitewide, including the floating WhatsApp button. A coach's own WhatsApp button uses the number on that coach's own profile in the **Coaches** collection instead.
