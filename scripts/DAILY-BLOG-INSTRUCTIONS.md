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
   tag to the entry's `tag` ("Playbook").
   Keep the Google Analytics 4 tag (G-16PBDPE8HK) in the `<head>` exactly as in the template; every page must have it.
2. Writing rules (voice matters most):
   - Write as the site owner, in the first person ("I"), as his own article: his take, his advice, his
     recommendations. Confident, direct, practical, like an operator talking to other sellers. It must not
     read as a summary or breakdown of someone else's posts. Never "Mansour says..." as the frame of the piece.
   - Lead with the lesson as the author's own point of view. Bring in the source person only as supporting
     evidence where their specific example or numbers appear ("Mansour Norouzi shared a case where...").
   - Never present the source person's experiences, data, results or tests as the author's own. Anything that
     happened at their company is attributed to them. General advice and frameworks can be written as the
     author's own recommendations.
   - Use only facts in the entry's `brief`. Never invent numbers, quotes, results, or experiences of the author.
   - Link the source person's name to their LinkedIn profile the first time it appears. Keep their name out of
     the title and the hero intro.
   - At most one short direct quote (under 15 words), and only if it appears in quotes in the brief.
   - 700-1,100 words. Structure: the lesson and why it matters, how it works (with the credited example),
     how I'd apply it, a short "What to do this week" list, the standard CTA box, then one italic line
     crediting the source's public LinkedIn posts.
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
