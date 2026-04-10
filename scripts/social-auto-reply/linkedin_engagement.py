#!/usr/bin/env python3
"""
Kompound Commerce — LinkedIn Engagement Helper

LinkedIn's API doesn't support automated commenting on others' posts, so this
script helps you work efficiently by:

1. Generating ready-to-paste comment replies based on topic keywords
2. Tracking your daily engagement (comments, reactions, DMs)
3. Suggesting which posts to engage with based on your target audience
4. Logging all engagement for ROI tracking

Usage:
    python linkedin_engagement.py generate --topic ppc
    python linkedin_engagement.py generate --topic "listing optimization"
    python linkedin_engagement.py log --action comment --source "John's post about ACOS"
    python linkedin_engagement.py stats
    python linkedin_engagement.py suggest
"""

import json
import csv
import os
import sys
import random
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
ENGAGEMENT_LOG = SCRIPT_DIR / "linkedin-engagement-log.csv"
COMMENT_TEMPLATES_PATH = SCRIPT_DIR / "linkedin-comment-templates.json"


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def load_comment_templates():
    with open(COMMENT_TEMPLATES_PATH) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Generate comment replies
# ---------------------------------------------------------------------------
COMMENT_BANK = {
    "ppc": [
        "Great breakdown on PPC strategy. One thing I'd add — Top of Search placement modifiers are massively underused. Bumping that to 30-50% can significantly improve conversion rates since those spots convert 2-3x better than rest of search. Have you tested that with your campaigns?",
        "This is spot on. The search term report is the single most underrated tool in Seller Central. We typically see sellers save 20-30% of their ad spend just by negating irrelevant terms weekly. The key is being consistent with it — set a weekly calendar reminder.",
        "Really solid advice here. I'd also emphasize the importance of knowing your break-even ACOS before you even start running ads. Too many sellers just pick a target ACOS without understanding their actual margins. Once you know your break-even, everything else falls into place.",
        "Agreed on all of this. One more thing worth mentioning — Sponsored Brand Video ads are still significantly cheaper than Sponsored Products in most categories, and they get great placement. If you have Brand Registry and aren't running SBV, you're leaving money on the table.",
    ],
    "listing": [
        "Great points on listing optimization. I'd add that your main image is doing most of the heavy lifting for click-through rate. Before optimizing anything else, make sure your main image stands out on the search results page. A/B test it with Manage Your Experiments if you have Brand Registry.",
        "This is solid advice. One thing that often gets overlooked — backend search terms. You get 249 bytes and a lot of sellers either don't use them or waste them repeating words already in their title and bullets. Use all 249 bytes with unique, relevant terms.",
        "Completely agree. The title is where most sellers lose — either they keyword stuff it (hurts CTR) or they write it for humans only (hurts discoverability). The sweet spot is front-loading your main keyword while keeping it readable. Amazon weights the first 80 characters most heavily.",
    ],
    "fees": [
        "Fees are definitely the silent margin killer. One thing a lot of sellers miss — the low-inventory-level fee that Amazon rolled out. If your weeks of cover drops below their threshold, you get hit with extra fees. Worth checking your inventory performance dashboard regularly.",
        "Good discussion. I always tell sellers to calculate their TRUE net margin, not just the obvious fees. Factor in: referral fee, FBA fulfillment, storage (especially Q4), PPC spend as % of revenue, returns/refunds, and any software tools. The real margin is usually 10-15% lower than what sellers think.",
    ],
    "launch": [
        "Great launch strategy. One thing I'd emphasize — your listing needs to be 100% ready BEFORE you turn on PPC. I see too many sellers start driving traffic to a half-finished listing with 2 images and no A+ Content. You're literally paying to show people a bad listing. Get the foundation right first.",
        "Solid plan. I'd add that Vine is basically mandatory now for new launches. Yes it costs $200, but those first 15-30 reviews make a massive difference in conversion rate. Without reviews, you're paying for clicks that don't convert, which costs you way more than $200.",
    ],
    "walmart": [
        "Walmart Marketplace is such an underrated opportunity right now. The competition is a fraction of what it is on Amazon, and CPCs on Walmart Connect are still really cheap. If you're already on Amazon, the expansion is relatively straightforward — the hard part is just getting approved and adapting your listing content.",
        "Good points. One thing worth noting — don't just copy your Amazon listings to Walmart. Their content scoring system is different, and the title formatting requirements are stricter. Invest time in optimizing specifically for Walmart's algorithm and you'll rank much faster than sellers who just port over their Amazon content.",
    ],
    "general": [
        "Really appreciate you sharing this — it's a challenge a lot of sellers face. The fundamentals always come back to: strong listing, efficient PPC, and knowing your true margins. Get those three right and everything else is optimization on top of a solid foundation.",
        "Great discussion in the comments here. For anyone reading this who's early in their Amazon journey — focus on one product first. Get it profitable and ranking organically before you start expanding your catalog. Spreading too thin too fast is one of the most common mistakes I see.",
        "Solid post. One underrated piece of advice — join the Amazon seller forums and subreddits. The community knowledge is incredibly valuable, especially for category-specific insights. No course or tool can replace real seller experience sharing.",
        "This resonates. The sellers who succeed long-term are the ones who treat it like a real business — tracking their numbers, testing systematically, and investing in the things that actually move the needle (listing quality, PPC efficiency, product differentiation).",
    ],
    "account_health": [
        "Account health issues are stressful, but most are fixable with the right approach. The key to a good Plan of Action: be specific about the root cause, show what you've already done to fix it, and detail the systems you're putting in place to prevent recurrence. Amazon wants to see you take ownership.",
        "Good advice here. I'd add — never submit a rushed appeal. Take 24-48 hours to really understand the violation, gather supporting documentation (invoices, supply chain docs), and write a clear, professional POA. First impressions matter with Amazon's appeals team.",
    ],
    "tiktok": [
        "TikTok Shop is still in the early innings and the opportunity is real. The biggest mindset shift for Amazon sellers: it's content-driven discovery, not search-driven. Your success depends on great video content and creator partnerships, not keyword optimization.",
        "Great point about TikTok. The affiliate program is the lowest-risk way to start — you only pay on actual sales. Start with micro-influencers (10K-50K followers) in your niche. They're way more affordable than big creators and often have better engagement rates.",
    ],
}


def generate_comments(topic, count=3):
    """Generate ready-to-paste comments for a given topic."""
    topic_lower = topic.lower().strip()

    # Find matching topic
    matched_topic = None
    for key in COMMENT_BANK:
        if key in topic_lower or topic_lower in key:
            matched_topic = key
            break

    if not matched_topic:
        # Check for partial keyword matches
        keyword_map = {
            "ppc": ["ppc", "acos", "ads", "advertising", "campaign", "bid", "sponsored"],
            "listing": ["listing", "seo", "keyword", "title", "image", "conversion", "optimize"],
            "fees": ["fee", "margin", "profit", "cost", "fba fee", "storage"],
            "launch": ["launch", "new product", "first product", "starting"],
            "walmart": ["walmart", "wfs", "multichannel"],
            "account_health": ["suspend", "account", "health", "appeal", "reinstate"],
            "tiktok": ["tiktok", "social commerce", "creator"],
        }
        for key, keywords in keyword_map.items():
            if any(kw in topic_lower for kw in keywords):
                matched_topic = key
                break

    if not matched_topic:
        matched_topic = "general"

    comments = COMMENT_BANK[matched_topic]
    selected = random.sample(comments, min(count, len(comments)))

    print(f"\n{'='*60}")
    print(f"LinkedIn Comments — Topic: {matched_topic.upper()}")
    print(f"{'='*60}")
    for i, comment in enumerate(selected, 1):
        print(f"\n--- Option {i} ---")
        print(comment)
        print()

    return selected


# ---------------------------------------------------------------------------
# Engagement logging
# ---------------------------------------------------------------------------
def log_engagement(action, source, notes=""):
    """Log an engagement action to CSV."""
    file_exists = ENGAGEMENT_LOG.exists()
    with open(ENGAGEMENT_LOG, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "action", "source", "notes"])
        writer.writerow([
            datetime.now(timezone.utc).isoformat(),
            action,
            source,
            notes,
        ])
    print(f"Logged: {action} — {source}")


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------
def show_stats():
    """Show engagement stats for today and this week."""
    if not ENGAGEMENT_LOG.exists():
        print("No engagement data yet. Start logging with: python linkedin_engagement.py log")
        return

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())

    today_counts = {}
    week_counts = {}
    total_counts = {}

    with open(ENGAGEMENT_LOG) as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts = datetime.fromisoformat(row["timestamp"])
            action = row["action"]

            total_counts[action] = total_counts.get(action, 0) + 1
            if ts >= today_start:
                today_counts[action] = today_counts.get(action, 0) + 1
            if ts >= week_start:
                week_counts[action] = week_counts.get(action, 0) + 1

    config = load_config()
    targets = config["linkedin"]["daily_engagement_targets"]

    print(f"\n{'='*50}")
    print("LinkedIn Engagement Stats")
    print(f"{'='*50}")

    print(f"\nToday ({now.strftime('%A, %B %d')}):")
    for action, target_key in [("comment", "comments_on_posts"), ("reaction", "reactions"), ("reply", "direct_replies")]:
        done = today_counts.get(action, 0)
        target = targets.get(target_key, "?")
        bar_filled = min(done, target) if isinstance(target, int) else done
        bar_total = target if isinstance(target, int) else 10
        bar = "█" * bar_filled + "░" * max(0, bar_total - bar_filled)
        print(f"  {action:>10}: {done}/{target} [{bar}]")

    print(f"\nThis week:")
    for action in sorted(week_counts):
        print(f"  {action:>10}: {week_counts[action]}")

    print(f"\nAll time:")
    for action in sorted(total_counts):
        print(f"  {action:>10}: {total_counts[action]}")
    print()


# ---------------------------------------------------------------------------
# Suggest posts to engage with
# ---------------------------------------------------------------------------
def suggest_engagement():
    """Print a checklist of daily engagement tasks."""
    config = load_config()
    hashtags = config["linkedin"]["monitoring"]["hashtags"]
    keywords = config["linkedin"]["monitoring"]["keywords"]

    print(f"\n{'='*60}")
    print("Daily LinkedIn Engagement Checklist")
    print(f"{'='*60}")

    print("\n1. SEARCH these hashtags and comment on 2-3 posts each:")
    for tag in hashtags[:5]:
        print(f"   [ ] {tag}")

    print("\n2. SEARCH these keywords and engage with relevant posts:")
    for kw in random.sample(keywords, min(5, len(keywords))):
        print(f"   [ ] \"{kw}\"")

    print("\n3. REACT to 20-25 posts from your feed (likes, celebrates, etc.)")

    print("\n4. CHECK notifications and reply to any comments on your posts")

    print("\n5. SEND 3-5 follow-up DMs to warm connections")
    print("   (Use templates from scripts/linkedin-outreach/message-templates.md)")

    print("\n6. POST your own content (see weekly calendar in content-hooks.md)")

    print("\nTIP: Use 'python linkedin_engagement.py generate --topic <topic>'")
    print("     to generate ready-to-paste comments for any topic.")
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Kompound Commerce LinkedIn Engagement Helper")
    subparsers = parser.add_subparsers(dest="command")

    # Generate comments
    gen_parser = subparsers.add_parser("generate", help="Generate ready-to-paste comments")
    gen_parser.add_argument("--topic", required=True, help="Topic: ppc, listing, fees, launch, walmart, general, etc.")
    gen_parser.add_argument("--count", type=int, default=3, help="Number of comment options to generate")

    # Log engagement
    log_parser = subparsers.add_parser("log", help="Log an engagement action")
    log_parser.add_argument("--action", required=True, choices=["comment", "reaction", "reply", "dm", "post"], help="Type of engagement")
    log_parser.add_argument("--source", required=True, help="Where/who you engaged with")
    log_parser.add_argument("--notes", default="", help="Optional notes")

    # Stats
    subparsers.add_parser("stats", help="Show engagement statistics")

    # Suggest
    subparsers.add_parser("suggest", help="Get daily engagement suggestions")

    args = parser.parse_args()

    if args.command == "generate":
        generate_comments(args.topic, args.count)
    elif args.command == "log":
        log_engagement(args.action, args.source, args.notes)
    elif args.command == "stats":
        show_stats()
    elif args.command == "suggest":
        suggest_engagement()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
