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

## Operator Playbook Series (Nov 2026)

The front of the queue holds the "operator-playbook" series: one article a day, each breaking down one
lesson from Mansour Norouzi (Amazon) or Joel Contartese (TikTok Shop), based on their public LinkedIn posts.
Each queue entry has a `source` (name, role, LinkedIn profile) and a `brief` (the facts to use).

Daily steps:
1. Take `queue[0]`. Write `blog/{slug}.html` using `blog/operator-playbook-amazon-tiktok-shop.html` as the
   template: copy its `<head>` structure, the `<style>` block unchanged, nav, hero and footer. Set the title,
   description, keywords, canonical URL, JSON-LD `datePublished`/`dateModified` to today, and the hero
   tag to the entry's `tag` ("Operator Breakdown").
2. Writing rules:
   - 700-1,100 words, original writing in Kompound Commerce's voice ("we"). Not a copy of the posts.
   - Use only facts in the entry's `brief`. Never invent numbers, quotes, results or claims about the person.
     Attribute every figure to the person ("Mansour reported...", "At Bloom, Joel found...").
   - Link the person's name to their LinkedIn profile the first time it appears.
   - At most one short direct quote (under 15 words), and only if it appears in quotes in the brief.
   - Structure: what the lesson is and who it's from, how it works with their example, how a seller can apply it,
     a short "What to do this week" list, the standard CTA box, then a Sources line linking their LinkedIn profile.
   - Use `.callout` for the single most important takeaway. No emoji in the article body.
3. Run `python3 scripts/publish_queued_post.py {slug}` to update blog/index.html, sitemap.xml and the queue.
4. Commit with message `Add blog post: {title}` and push to `main`. Vercel deploys on push.

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
