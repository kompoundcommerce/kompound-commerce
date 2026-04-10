# Social Media Auto-Reply System — Kompound Commerce

Automated and semi-automated engagement tools for Reddit and LinkedIn to drive inbound leads from Amazon sellers, e-commerce operators, and marketplace brands.

---

## Overview

| Platform | Automation Level | What It Does |
|----------|-----------------|--------------|
| **Reddit** | Fully automated | Monitors subreddits for relevant posts, auto-replies with helpful answers that build brand awareness |
| **LinkedIn** | Semi-automated | Generates ready-to-paste comments, tracks daily engagement, provides engagement checklists |

---

## Quick Start

### 1. Install dependencies

```bash
cd scripts/social-auto-reply
pip install -r requirements.txt
```

### 2. Configure Reddit credentials

1. Go to https://www.reddit.com/prefs/apps
2. Create a **script** application
3. Copy the client ID and secret
4. Edit `config.json` and fill in the `reddit.credentials` section:

```json
"credentials": {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "username": "your_reddit_username",
    "password": "your_reddit_password",
    "user_agent": "KompoundCommerceBot/1.0"
}
```

### 3. Test with a dry run

```bash
python reddit_bot.py --dry-run
```

This scans subreddits and shows what the bot WOULD reply to, without actually posting.

---

## Reddit Bot

### Usage

```bash
# Single scan — find matches and reply
python reddit_bot.py

# Dry run — preview without posting
python reddit_bot.py --dry-run

# Daemon mode — scan every 30 minutes continuously
python reddit_bot.py --daemon

# Custom interval (every 45 minutes)
python reddit_bot.py --daemon --interval 2700
```

### How It Works

1. Scans 9 target subreddits (AmazonSeller, FulfillmentByAmazon, ecommerce, etc.)
2. Matches posts against 25+ e-commerce keywords (PPC, ACOS, FBA fees, etc.)
3. Classifies the post topic (PPC, listing optimization, fees, launch, etc.)
4. Selects an appropriate reply template with genuine, helpful advice
5. Personalizes the reply with relevant blog links and resources
6. Posts the reply with rate limiting and safety checks

### Safety Limits (configurable in config.json)

- Max 5 replies per hour
- Max 20 replies per day
- Minimum 5 minutes between replies (+ random jitter)
- Skips posts less than 10 minutes old or more than 24 hours old
- Skips posts with low scores
- Never replies to the same post twice
- Only replies to questions/help requests (not memes, rants, etc.)

### Reply Quality

All replies are **genuinely helpful** — they provide real, actionable advice first, with a subtle mention of Kompound Commerce resources (blog posts, FBA calculator) as additional value. No hard selling, no spammy links.

Topics covered: PPC/ACOS optimization, listing optimization, FBA fees, product launches, Walmart expansion, account suspensions, Buy Box strategy, TikTok Shop, seller tools.

---

## LinkedIn Engagement Helper

LinkedIn doesn't allow automated commenting via API, so this tool helps you engage efficiently.

### Usage

```bash
# Generate ready-to-paste comments for a topic
python linkedin_engagement.py generate --topic ppc
python linkedin_engagement.py generate --topic "listing optimization"
python linkedin_engagement.py generate --topic fees --count 5

# Log your engagement actions
python linkedin_engagement.py log --action comment --source "John's ACOS post"
python linkedin_engagement.py log --action reaction --source "FBA seller group post"
python linkedin_engagement.py log --action dm --source "Jane - supplements seller"

# View your engagement stats
python linkedin_engagement.py stats

# Get daily engagement checklist
python linkedin_engagement.py suggest
```

### Daily Workflow

1. Run `python linkedin_engagement.py suggest` for your daily checklist
2. Search the suggested hashtags/keywords on LinkedIn
3. Use `python linkedin_engagement.py generate --topic <topic>` to generate comments
4. Copy/paste and personalize before posting
5. Log each engagement with `python linkedin_engagement.py log`
6. Check your progress with `python linkedin_engagement.py stats`

---

## Files

| File | Purpose |
|------|---------|
| `config.json` | Main configuration — credentials, subreddits, keywords, limits |
| `reddit_bot.py` | Automated Reddit reply bot |
| `reply-templates.json` | Reddit reply templates organized by topic |
| `linkedin_engagement.py` | LinkedIn engagement helper (comment generation, tracking) |
| `requirements.txt` | Python dependencies |
| `auto-reply-log.csv` | Auto-generated log of all Reddit replies |
| `linkedin-engagement-log.csv` | Auto-generated log of LinkedIn engagement |
| `.replied_ids` | Tracks which Reddit posts have been replied to |

---

## Customization

### Adding new subreddits or keywords

Edit `config.json` → `reddit.subreddits` and `reddit.keywords`.

### Adding new reply templates

Edit `reply-templates.json`. Each topic has an array of template objects with a `name` and `text` field. Use these placeholders in template text:

- `{subreddit}` — the subreddit name
- `{post_title}` — the post title
- `{blog_url}` — auto-selected relevant blog post URL
- `{website}` — kompoundcommerce.com
- `{fba_calculator}` — link to the FBA calculator
- `{brand_name}` — Kompound Commerce

### Adjusting rate limits

Edit `config.json` → `reddit.safety_limits`. Be conservative — Reddit will shadowban accounts that spam.

---

## Best Practices

1. **Always provide value first** — Replies should help the poster, with brand mentions secondary
2. **Stay within rate limits** — Better to post 10 great replies than 50 mediocre ones
3. **Monitor for downvotes** — If replies get downvoted, review your templates and targeting
4. **Rotate templates** — Don't post the same reply repeatedly in the same subreddit
5. **Start with dry runs** — Always `--dry-run` first when changing keywords or subreddits
6. **Respect subreddit rules** — Some subs ban self-promotion; adjust templates accordingly
