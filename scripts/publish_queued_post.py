#!/usr/bin/env python3
"""Register a written blog post on the site.

Usage: python3 scripts/publish_queued_post.py <slug> [--date YYYY-MM-DD] [--read-time N]

Run this AFTER blog/<slug>.html exists. It:
  1. Adds a card for the post to the top of "New This Week" on blog/index.html
     and moves the oldest card there to the top of the main grid (keeps 6 featured).
  2. Adds the post URL to sitemap.xml.
  3. Moves the topic from "queue" to "published" in scripts/topic-queue.json.
It refuses to run twice for the same slug.
"""
import argparse, datetime, html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
QUEUE = ROOT / "scripts" / "topic-queue.json"
INDEX = ROOT / "blog" / "index.html"
SITEMAP = ROOT / "sitemap.xml"
BASE = "https://www.kompoundcommerce.com/blog/"

LINK_TEXT = {"guide": "Read guide →", "tutorial": "Read tutorial →", "blog": "Read article →", "tool": "Open tool →"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--read-time", type=int)
    a = ap.parse_args()

    post = ROOT / "blog" / f"{a.slug}.html"
    if not post.exists():
        sys.exit(f"ERROR: {post} does not exist. Write the post first.")

    q = json.loads(QUEUE.read_text())
    if any(p.get("slug") == a.slug for p in q["published"]):
        sys.exit(f"ERROR: {a.slug} is already published.")
    idx = next((i for i, t in enumerate(q["queue"]) if t["slug"] == a.slug), None)
    if idx is None:
        sys.exit(f"ERROR: {a.slug} is not in the queue.")
    topic = q["queue"][idx]

    if a.read_time is None:
        words = len(re.sub(r"<[^>]+>", " ", post.read_text()).split())
        a.read_time = max(3, round(words / 230))

    d = datetime.date.fromisoformat(a.date)
    date_label = f"{d.strftime('%b')} {d.day}, {d.year}"
    cat = topic.get("category", "blog")
    tag = topic.get("tag") or cat.capitalize()
    e = html.escape

    # ---- blog index ----
    page = INDEX.read_text()
    url = f"/blog/{a.slug}.html"
    if url in page:
        sys.exit(f"ERROR: {url} is already on blog/index.html.")
    card = (
        f'      <a class="featured-card blog-card" href="{url}" data-type="{cat}">\n'
        f'        <div class="blog-card-thumb"><span class="emoji">{topic.get("emoji", "📝")}</span>'
        f'<span class="blog-card-tag tag-{cat}">{e(tag)}</span></div>\n'
        f'        <div class="blog-card-body">\n'
        f'          <span class="featured-label">New</span>\n'
        f'          <div class="blog-card-date">{date_label} · {a.read_time} min read</div>\n'
        f'          <h3>{e(topic["title"])}</h3>\n'
        f'          <p>{e(topic["description"])}</p>\n'
        f'          <span class="blog-card-link">{LINK_TEXT.get(cat, "Read article →")}</span>\n'
        f'        </div>\n'
        f'      </a>\n'
    )
    anchor = '<div class="featured-grid" id="featuredGrid">\n'
    if anchor not in page:
        sys.exit("ERROR: featured grid not found in blog/index.html.")
    page = page.replace(anchor, anchor + "\n" + card, 1)

    # move the last featured card into the top of the main grid
    start = page.index(anchor)
    end = page.index('<div class="blog-grid">', start)
    section = page[start:end]
    cards = list(re.finditer(r'      <a class="featured-card blog-card".*?      </a>\n', section, re.S))
    if len(cards) > 6:
        last = cards[-1]
        moved = last.group(0).replace('class="featured-card blog-card"', 'class="blog-card"', 1)
        section = section[:last.start()] + section[last.end():]
        page = page[:start] + section + page[end:]
        grid = '<div class="blog-grid">\n'
        page = page.replace(grid, grid + "\n" + moved, 1)
    INDEX.write_text(page)

    # ---- sitemap ----
    sm = SITEMAP.read_text()
    loc = f"{BASE}{a.slug}.html"
    if loc not in sm:
        entry = (f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{a.date}</lastmod>\n"
                 f"    <changefreq>monthly</changefreq>\n    <priority>0.8</priority>\n  </url>\n")
        sm = sm.replace("</urlset>", entry + "</urlset>", 1)
        SITEMAP.write_text(sm)

    # ---- queue ----
    pub = {k: topic[k] for k in ("slug", "title", "category", "emoji") if k in topic}
    pub.update({"date": a.date, "readTime": a.read_time})
    if "series" in topic:
        pub["series"] = topic["series"]
    q["published"].append(pub)
    del q["queue"][idx]
    QUEUE.write_text(json.dumps(q, indent=2, ensure_ascii=False) + "\n")

    print(f"Registered {a.slug}: {loc} ({a.read_time} min read, {date_label})")


if __name__ == "__main__":
    main()
