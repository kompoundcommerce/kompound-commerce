# Daily Blog Publishing — Claude Code Instructions

## Quick Start (Run Daily)

Tell Claude Code:

```
Write and publish today's blog post for Kompound Commerce.
Pick the next topic from scripts/topic-queue.json, write the full HTML blog post
following the template in blog/amazon-fba-fees-explained-2026.html, update
blog/index.html and sitemap.xml, then commit and push.
```

## How It Works

1. **Topic Queue** (`scripts/topic-queue.json`): Contains 20 pre-planned topics with titles, descriptions, keywords, categories, and emojis. Topics move from `queue` → `published` after publishing.

2. **Blog Template**: All posts follow the same HTML structure as existing posts in `/blog/`. Key elements:
   - Full SEO meta tags (title, description, keywords, canonical, OG tags)
   - JSON-LD structured data with datePublished
   - Inline CSS (same style block as other posts)
   - Nav bar, article hero, article content, CTA, footer
   - Use `.callout`, `.warning-box`, `.ai-callout` for special sections

3. **Updates Required Per Post**:
   - Create `blog/{slug}.html` (the actual post)
   - Add card to top of `blog/index.html` blog grid
   - Add URL entry to `sitemap.xml`
   - Move topic from queue to published in `scripts/topic-queue.json`

4. **Google Search Console**: Run `./scripts/gsc-submit.sh <url>` after publishing (requires service account credentials at `scripts/gsc-credentials.json`).

## Category Reference

| Category | Tag Class | Link Text | Color |
|----------|-----------|-----------|-------|
| guide | tag-guide | Read guide → | Orange |
| tutorial | tag-tutorial | Read tutorial → | Green |
| blog | tag-blog | Read article → | Purple |
| tool | tag-tool | Open tool → | Blue |

## Cron Setup (Optional)

```bash
# Run daily at 8am via Claude Code
0 8 * * * cd /path/to/kompound-commerce && claude -p "Write and publish today's blog post. Pick next topic from scripts/topic-queue.json, write full HTML, update index and sitemap, commit and push."
```
