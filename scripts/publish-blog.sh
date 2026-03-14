#!/bin/bash
# =============================================================================
# Daily Blog Publisher for Kompound Commerce
# =============================================================================
#
# This script automates daily blog publishing:
#   1. Picks the next topic from the queue (scripts/topic-queue.json)
#   2. Generates a blog post HTML file using Claude Code
#   3. Updates blog/index.html with a new card
#   4. Updates sitemap.xml with the new URL
#   5. Submits the new URL to Google Search Console Indexing API
#   6. Commits and pushes to the repository
#
# Usage:
#   ./scripts/publish-blog.sh
#
# Prerequisites:
#   - jq installed (sudo apt install jq)
#   - git configured with push access
#   - For Google indexing: scripts/gsc-credentials.json (service account key)
#
# To run daily via cron:
#   0 8 * * * cd /path/to/kompound-commerce && ./scripts/publish-blog.sh >> scripts/publish.log 2>&1
#
# To run daily via Claude Code:
#   claude -p "Run ./scripts/publish-blog.sh and if the blog HTML doesn't exist yet, write it first based on the topic queue"
#
# =============================================================================

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

QUEUE_FILE="scripts/topic-queue.json"
BLOG_DIR="blog"
SITEMAP="sitemap.xml"
BLOG_INDEX="blog/index.html"
TODAY=$(date +%Y-%m-%d)
MONTH_YEAR=$(date +"%-b %Y")  # e.g. "Mar 2026"

echo "========================================="
echo "Kompound Commerce Blog Publisher"
echo "Date: $TODAY"
echo "========================================="

# ---- Check prerequisites ----
if ! command -v jq &> /dev/null; then
  echo "ERROR: jq is required. Install with: sudo apt install jq"
  exit 1
fi

# ---- Get next topic from queue ----
NEXT_TOPIC=$(jq -r '.queue[0]' "$QUEUE_FILE")
if [ "$NEXT_TOPIC" = "null" ] || [ -z "$NEXT_TOPIC" ]; then
  echo "ERROR: No topics left in the queue! Add more to $QUEUE_FILE"
  exit 1
fi

SLUG=$(echo "$NEXT_TOPIC" | jq -r '.slug')
TITLE=$(echo "$NEXT_TOPIC" | jq -r '.title')
DESCRIPTION=$(echo "$NEXT_TOPIC" | jq -r '.description')
CATEGORY=$(echo "$NEXT_TOPIC" | jq -r '.category')
EMOJI=$(echo "$NEXT_TOPIC" | jq -r '.emoji')
KEYWORDS=$(echo "$NEXT_TOPIC" | jq -r '.keywords')

BLOG_FILE="$BLOG_DIR/${SLUG}.html"
BLOG_URL="https://www.kompoundcommerce.com/blog/${SLUG}.html"

echo "Next topic: $TITLE"
echo "Slug: $SLUG"
echo "Category: $CATEGORY"
echo "File: $BLOG_FILE"

# ---- Check if blog post already exists ----
if [ -f "$BLOG_FILE" ]; then
  echo "WARNING: $BLOG_FILE already exists. Skipping creation."
  echo "Remove the file or advance the queue manually."
  exit 1
fi

# ---- Generate the blog post ----
# This is where Claude Code writes the actual content.
# When running via `claude -p`, the AI generates the HTML.
# When running standalone, it outputs a placeholder reminder.
echo ""
echo "ACTION REQUIRED: Write the blog post HTML file."
echo "  File: $BLOG_FILE"
echo "  Title: $TITLE"
echo "  Description: $DESCRIPTION"
echo "  Category: $CATEGORY"
echo "  Keywords: $KEYWORDS"
echo "  Date: $TODAY"
echo ""
echo "Use this command with Claude Code to auto-generate:"
echo "  claude -p \"Write a blog post for Kompound Commerce about: $TITLE. Description: $DESCRIPTION. Save to $BLOG_FILE. Follow the exact HTML template format used in blog/amazon-fba-fees-explained-2026.html. Use date $TODAY, category $CATEGORY, keywords: $KEYWORDS.\""
echo ""

if [ ! -f "$BLOG_FILE" ]; then
  echo "Blog file not yet created. Exiting — run with Claude Code to generate content."
  echo "After generating the blog HTML, re-run this script to update index/sitemap."
  exit 0
fi

# ---- Update blog/index.html ----
echo "Updating blog index..."

# Determine tag class and link text
TAG_CLASS="tag-guide"
LINK_TEXT="Read guide →"
case "$CATEGORY" in
  tutorial)
    TAG_CLASS="tag-tutorial"
    LINK_TEXT="Read tutorial →"
    ;;
  blog)
    TAG_CLASS="tag-blog"
    LINK_TEXT="Read article →"
    ;;
  tool)
    TAG_CLASS="tag-tool"
    LINK_TEXT="Open tool →"
    ;;
esac

CATEGORY_UPPER=$(echo "$CATEGORY" | sed 's/.*/\u&/')
READ_TIME="14"  # Default; can be calculated from word count

# Build the new card HTML
NEW_CARD="    <a class=\"blog-card\" href=\"/blog/${SLUG}.html\" data-type=\"${CATEGORY}\">
      <div class=\"blog-card-thumb\"><span class=\"emoji\">${EMOJI}</span><span class=\"blog-card-tag ${TAG_CLASS}\">${CATEGORY_UPPER}</span></div>
      <div class=\"blog-card-body\">
        <div class=\"blog-card-date\">${MONTH_YEAR} · ${READ_TIME} min read</div>
        <h3>${TITLE}</h3>
        <p>${DESCRIPTION}</p>
        <span class=\"blog-card-link\">${LINK_TEXT}</span>
      </div>
    </a>"

# Insert the new card at the top of the blog grid
sed -i "/<div class=\"blog-grid\" id=\"blogGrid\">/a\\
\\
${NEW_CARD}" "$BLOG_INDEX"

echo "Blog index updated."

# ---- Update sitemap.xml ----
echo "Updating sitemap..."

SITEMAP_ENTRY="  <url>\n    <loc>${BLOG_URL}</loc>\n    <lastmod>${TODAY}</lastmod>\n    <changefreq>monthly</changefreq>\n    <priority>0.8</priority>\n  </url>"

sed -i "/<\/urlset>/i\\${SITEMAP_ENTRY}" "$SITEMAP"

echo "Sitemap updated."

# ---- Move topic from queue to published ----
echo "Updating topic queue..."

PUBLISHED_ENTRY=$(jq --arg date "$TODAY" --arg rt "$READ_TIME" '.queue[0] + {date: $date, readTime: ($rt | tonumber)}' "$QUEUE_FILE")
jq --argjson entry "$PUBLISHED_ENTRY" '.published += [$entry] | .queue = .queue[1:]' "$QUEUE_FILE" > "${QUEUE_FILE}.tmp"
mv "${QUEUE_FILE}.tmp" "$QUEUE_FILE"

echo "Topic moved from queue to published."

# ---- Submit to Google Search Console Indexing API ----
echo ""
echo "Google Search Console Indexing..."

GSC_CREDS="scripts/gsc-credentials.json"
if [ -f "$GSC_CREDS" ]; then
  # Use the indexing script if credentials exist
  if [ -f "scripts/gsc-submit.sh" ]; then
    bash scripts/gsc-submit.sh "$BLOG_URL"
  else
    echo "WARNING: gsc-submit.sh not found. Run scripts/gsc-submit.sh setup first."
  fi
else
  echo "SKIP: No Google credentials found at $GSC_CREDS"
  echo "To enable auto-indexing:"
  echo "  1. Create a Google Cloud service account"
  echo "  2. Enable the Indexing API"
  echo "  3. Add the service account as an owner in Search Console"
  echo "  4. Download the JSON key to $GSC_CREDS"
  echo ""
  echo "Manual submission: Go to Google Search Console → URL Inspection → Submit: $BLOG_URL"
fi

# ---- Git commit and push ----
echo ""
echo "Committing changes..."

git add "$BLOG_FILE" "$BLOG_INDEX" "$SITEMAP" "$QUEUE_FILE"
git commit -m "Add blog post: ${TITLE}

Published: ${TODAY}
Category: ${CATEGORY}
URL: ${BLOG_URL}"

echo ""
echo "========================================="
echo "DONE! Published: $TITLE"
echo "URL: $BLOG_URL"
echo "========================================="
echo ""
echo "Next steps:"
echo "  - git push to deploy"
echo "  - Verify at $BLOG_URL"
echo "  - Submit sitemap to Google Search Console if not auto-submitted"
