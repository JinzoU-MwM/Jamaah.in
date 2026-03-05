# Progress Context — 2026-03-05 (SEO Landing Cluster)

## Objective
Improve Google indexing by adding richer, crawlable landing pages outside SPA hash routing and wiring internal links/sitemap/schema.

## What was implemented
1. Added static SEO landing pages in `frontend-svelte/public/`:
- `software-travel-umrah.html`
- `fitur-ocr-siskopatuh.html`
- `fitur-rooming-jamaah.html`
- `manifest-mutawwif-digital.html`

2. Updated SPA landing internal links:
- File: `frontend-svelte/src/lib/pages/LandingPage.svelte`
- Added nav link (`Panduan`) to static landing.
- Added new section `Pelajari Use Case Jamaah.in` with 4 guide cards linking to all static landing pages.
- Added matching styles and responsive behavior.

3. Updated crawl/index infra:
- File: `frontend-svelte/public/sitemap.xml`
- Added all 4 static URLs with `lastmod=2026-03-05`.

- File: `frontend-svelte/public/robots.txt`
- Explicit `Allow` entries for all 4 static SEO pages, plus existing sitemap line.

4. Updated root metadata/schema:
- File: `frontend-svelte/index.html`
- Added alternate links to 4 static pages.
- Extended JSON-LD with `WebSite` + `hasPart` pointing to 4 pages.
- Extended organization JSON-LD catalog listing 4 page links.

## Build/verification
- Frontend build succeeded multiple times using `npm run build` in `frontend-svelte`.
- Public URL checks returned `HTTP/1.1 200 OK` for:
  - `https://jamaah.web.id/`
  - `https://jamaah.web.id/software-travel-umrah.html`
  - `https://jamaah.web.id/fitur-ocr-siskopatuh.html`
  - `https://jamaah.web.id/fitur-rooming-jamaah.html`
  - `https://jamaah.web.id/manifest-mutawwif-digital.html`

## Git/deploy
- Commit pushed to `main`: `0c1aa33`
- Commit message: `feat(frontend): add SEO landing cluster and indexing links`
- Deploy is GitHub Actions based (`.github/workflows/deploy.yml`) on push to main.

## Notes
- Local workspace still has unrelated existing changes:
  - `PRODUCT_INFO.md` (modified)
  - `.serena/memories/progress/` (untracked memory files)
- During session, GH CLI status check failed in this shell due to missing `gh` auth (`gh auth status` -> not logged in).
