#!/usr/bin/env python3
"""
Kompound Commerce — Reddit Auto-Reply Bot

Monitors target subreddits for posts matching e-commerce/Amazon seller keywords,
then posts helpful replies that provide genuine value while subtly building
brand awareness. Replies are chosen from templates and customized per post.

Usage:
    python reddit_bot.py                  # Run once (scan & reply)
    python reddit_bot.py --daemon         # Run continuously on a schedule
    python reddit_bot.py --dry-run        # Preview matches without posting
"""

import praw
import json
import csv
import os
import re
import sys
import time
import random
import logging
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
TEMPLATES_PATH = SCRIPT_DIR / "reply-templates.json"
LOG_CSV = SCRIPT_DIR / "auto-reply-log.csv"
REPLIED_IDS_PATH = SCRIPT_DIR / ".replied_ids"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(SCRIPT_DIR / "bot.log"),
    ],
)
log = logging.getLogger("reddit-bot")


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def load_templates():
    with open(TEMPLATES_PATH) as f:
        return json.load(f)


def load_replied_ids():
    """Load the set of post/comment IDs we have already replied to."""
    if REPLIED_IDS_PATH.exists():
        return set(REPLIED_IDS_PATH.read_text().splitlines())
    return set()


def save_replied_id(post_id):
    with open(REPLIED_IDS_PATH, "a") as f:
        f.write(post_id + "\n")


# ---------------------------------------------------------------------------
# Reddit client
# ---------------------------------------------------------------------------
def create_reddit_client(config):
    creds = config["reddit"]["credentials"]
    return praw.Reddit(
        client_id=creds["client_id"],
        client_secret=creds["client_secret"],
        username=creds["username"],
        password=creds["password"],
        user_agent=creds["user_agent"],
    )


# ---------------------------------------------------------------------------
# Post matching
# ---------------------------------------------------------------------------
def matches_keywords(text, keywords):
    """Return list of matched keywords found in the text."""
    text_lower = text.lower()
    return [kw for kw in keywords if kw.lower() in text_lower]


def classify_topic(text, matched_keywords):
    """Classify the post into a topic bucket for template selection."""
    text_lower = text.lower()

    topic_signals = {
        "ppc": ["ppc", "acos", "tacos", "amazon ads", "sponsored products", "amazon advertising", "campaign", "bid"],
        "listing": ["listing", "seo", "keyword", "title", "bullet", "a+ content", "conversion", "images", "ranking", "amazon seo"],
        "fees": ["fba fees", "fee", "profit margin", "fba calculator", "referral fee", "storage fee", "costs"],
        "launch": ["product launch", "new product", "launch strategy", "first product", "just started"],
        "walmart": ["walmart", "walmart marketplace", "walmart seller", "multichannel"],
        "account_health": ["suspended", "suspension", "account health", "deactivated", "restricted", "policy violation"],
        "buy_box": ["buy box", "buybox", "winning the buy box", "pricing strategy"],
        "general": ["amazon seller", "private label", "fba", "ecommerce", "e-commerce"],
        "tiktok": ["tiktok shop", "tiktok seller", "social commerce"],
        "tools": ["helium 10", "jungle scout", "tool", "software", "ai tool"],
    }

    scores = {}
    for topic, signals in topic_signals.items():
        score = sum(1 for s in signals if s in text_lower)
        # Boost score if a matched keyword aligns with the topic
        score += sum(1 for kw in matched_keywords if kw.lower() in " ".join(signals))
        if score > 0:
            scores[topic] = score

    if not scores:
        return "general"

    return max(scores, key=scores.get)


def should_skip_post(post, config, replied_ids):
    """Return (True, reason) if the post should be skipped, else (False, None)."""
    reddit_cfg = config["reddit"]
    limits = reddit_cfg["safety_limits"]
    filtering = reddit_cfg["filtering"]

    # Already replied
    if filtering["skip_if_already_replied"] and post.id in replied_ids:
        return True, "already replied"

    # Post too short
    body = post.selftext or ""
    if len(body) < filtering["min_post_length_chars"]:
        return True, f"post body too short ({len(body)} chars)"

    # Post age
    post_age = datetime.now(timezone.utc) - datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
    if post_age < timedelta(minutes=limits["min_post_age_minutes"]):
        return True, "post too new"
    if post_age > timedelta(hours=limits["max_post_age_hours"]):
        return True, "post too old"

    # Score
    if post.score < limits["min_post_score"]:
        return True, f"score too low ({post.score})"

    # Flair
    if post.link_flair_text and post.link_flair_text in filtering["skip_flaired_posts"]:
        return True, f"skipped flair: {post.link_flair_text}"

    # Check if it looks like a question or discussion (not a link/meme dump)
    if filtering["require_question_mark_or_flair"]:
        combined = (post.title + " " + body).lower()
        question_signals = ["?", "help", "advice", "how do", "how to", "what should", "any tips", "recommend", "struggling", "issue", "problem", "question"]
        if not any(s in combined for s in question_signals):
            return True, "doesn't appear to be a question or help request"

    return False, None


# ---------------------------------------------------------------------------
# Reply generation
# ---------------------------------------------------------------------------
def pick_template(topic, templates):
    """Pick a reply template for the given topic."""
    topic_templates = templates.get(topic, templates.get("general", []))
    if not topic_templates:
        topic_templates = templates["general"]
    return random.choice(topic_templates)


def personalize_reply(template_text, post, topic, config):
    """Fill in template placeholders with post-specific details."""
    blog = config.get("blog_resources", {})
    brand = config["brand"]

    # Map topics to relevant blog links
    topic_to_blog = {
        "ppc": blog.get("ppc_help", ""),
        "listing": blog.get("listing_seo", ""),
        "fees": blog.get("fba_fees", ""),
        "launch": blog.get("product_launch", ""),
        "walmart": blog.get("walmart", ""),
        "account_health": blog.get("account_health", ""),
        "buy_box": blog.get("buy_box", ""),
        "tools": blog.get("ai_tools", ""),
        "tiktok": blog.get("walmart", ""),
        "general": blog.get("ppc_help", ""),
    }

    blog_path = topic_to_blog.get(topic, "")
    blog_url = f"{brand['website']}{blog_path}" if blog_path else ""

    replacements = {
        "{subreddit}": post.subreddit.display_name,
        "{post_title}": post.title,
        "{blog_url}": blog_url,
        "{website}": brand["website"],
        "{fba_calculator}": brand["fba_calculator"],
        "{brand_name}": brand["name"],
    }

    text = template_text
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)

    return text


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
class RateLimiter:
    def __init__(self, config):
        limits = config["reddit"]["safety_limits"]
        self.max_per_hour = limits["max_replies_per_hour"]
        self.max_per_day = limits["max_replies_per_day"]
        self.min_delay = limits["min_delay_between_replies_seconds"]
        self.replies_this_hour = 0
        self.replies_today = 0
        self.hour_start = datetime.now(timezone.utc)
        self.day_start = datetime.now(timezone.utc)
        self.last_reply_time = None

    def can_reply(self):
        now = datetime.now(timezone.utc)
        # Reset hourly counter
        if (now - self.hour_start).total_seconds() > 3600:
            self.replies_this_hour = 0
            self.hour_start = now
        # Reset daily counter
        if (now - self.day_start).total_seconds() > 86400:
            self.replies_today = 0
            self.day_start = now

        if self.replies_this_hour >= self.max_per_hour:
            return False, "hourly limit reached"
        if self.replies_today >= self.max_per_day:
            return False, "daily limit reached"
        return True, None

    def wait_if_needed(self):
        if self.last_reply_time:
            elapsed = (datetime.now(timezone.utc) - self.last_reply_time).total_seconds()
            remaining = self.min_delay - elapsed
            if remaining > 0:
                # Add small random jitter (0-60s) to look natural
                jitter = random.uniform(0, 60)
                wait = remaining + jitter
                log.info(f"Rate limit: waiting {wait:.0f}s before next reply")
                time.sleep(wait)

    def record_reply(self):
        self.replies_this_hour += 1
        self.replies_today += 1
        self.last_reply_time = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# CSV logging
# ---------------------------------------------------------------------------
def log_reply_csv(platform, source, title, url, template_name, reply_text, status):
    file_exists = LOG_CSV.exists()
    with open(LOG_CSV, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "platform", "subreddit_or_source", "post_title", "post_url", "reply_template_used", "reply_text", "status"])
        writer.writerow([
            datetime.now(timezone.utc).isoformat(),
            platform,
            source,
            title[:100],
            url,
            template_name,
            reply_text[:200],
            status,
        ])


# ---------------------------------------------------------------------------
# Main scan loop
# ---------------------------------------------------------------------------
def scan_and_reply(reddit, config, templates, rate_limiter, dry_run=False):
    """Scan target subreddits for matching posts and reply."""
    subreddits = config["reddit"]["subreddits"]
    keywords = config["reddit"]["keywords"]
    replied_ids = load_replied_ids()
    replies_made = 0

    for sub_name in subreddits:
        try:
            subreddit = reddit.subreddit(sub_name)
            log.info(f"Scanning r/{sub_name} ...")
        except Exception as e:
            log.warning(f"Could not access r/{sub_name}: {e}")
            continue

        # Scan new and hot posts
        posts = list(subreddit.new(limit=25)) + list(subreddit.hot(limit=15))
        seen = set()

        for post in posts:
            if post.id in seen:
                continue
            seen.add(post.id)

            combined_text = f"{post.title} {post.selftext or ''}"
            matched = matches_keywords(combined_text, keywords)
            if not matched:
                continue

            skip, reason = should_skip_post(post, config, replied_ids)
            if skip:
                log.debug(f"Skipping '{post.title[:60]}' — {reason}")
                continue

            can, limit_reason = rate_limiter.can_reply()
            if not can:
                log.info(f"Rate limit hit: {limit_reason}. Stopping scan.")
                return replies_made

            topic = classify_topic(combined_text, matched)
            template = pick_template(topic, templates)
            reply_text = personalize_reply(template["text"], post, topic, config)

            log.info(f"{'[DRY RUN] ' if dry_run else ''}Match in r/{sub_name}: \"{post.title[:70]}\"")
            log.info(f"  Topic: {topic} | Keywords: {matched[:5]} | Template: {template['name']}")

            if dry_run:
                log.info(f"  Reply preview:\n{reply_text[:300]}...")
                log_reply_csv("reddit", sub_name, post.title, f"https://reddit.com{post.permalink}", template["name"], reply_text, "dry_run")
            else:
                try:
                    rate_limiter.wait_if_needed()
                    post.reply(reply_text)
                    rate_limiter.record_reply()
                    save_replied_id(post.id)
                    replied_ids.add(post.id)
                    replies_made += 1
                    log.info(f"  Replied successfully! ({replies_made} this session)")
                    log_reply_csv("reddit", sub_name, post.title, f"https://reddit.com{post.permalink}", template["name"], reply_text, "posted")
                except praw.exceptions.RedditAPIException as e:
                    log.error(f"  Reddit API error: {e}")
                    log_reply_csv("reddit", sub_name, post.title, f"https://reddit.com{post.permalink}", template["name"], reply_text, f"error: {e}")
                    # Back off on rate limit errors
                    if "RATELIMIT" in str(e).upper():
                        log.warning("  Reddit rate limited. Sleeping 10 minutes.")
                        time.sleep(600)
                except Exception as e:
                    log.error(f"  Unexpected error: {e}")

    return replies_made


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Kompound Commerce Reddit Auto-Reply Bot")
    parser.add_argument("--dry-run", action="store_true", help="Preview matches without posting replies")
    parser.add_argument("--daemon", action="store_true", help="Run continuously, scanning every 30 minutes")
    parser.add_argument("--interval", type=int, default=1800, help="Scan interval in seconds for daemon mode (default: 1800)")
    args = parser.parse_args()

    config = load_config()
    templates = load_templates()

    if any(v.startswith("YOUR_") for v in config["reddit"]["credentials"].values()):
        log.error("Reddit credentials not configured! Edit config.json with your Reddit API credentials.")
        log.error("Get credentials at: https://www.reddit.com/prefs/apps")
        sys.exit(1)

    reddit = create_reddit_client(config)
    rate_limiter = RateLimiter(config)

    log.info(f"Kompound Commerce Reddit Bot starting ({'dry run' if args.dry_run else 'live'})")
    log.info(f"Monitoring {len(config['reddit']['subreddits'])} subreddits for {len(config['reddit']['keywords'])} keywords")

    if args.daemon:
        log.info(f"Daemon mode: scanning every {args.interval}s")
        while True:
            try:
                count = scan_and_reply(reddit, config, templates, rate_limiter, dry_run=args.dry_run)
                log.info(f"Scan complete. {count} replies posted. Next scan in {args.interval}s.")
                time.sleep(args.interval)
            except KeyboardInterrupt:
                log.info("Bot stopped by user.")
                break
            except Exception as e:
                log.error(f"Scan error: {e}. Retrying in 5 minutes.")
                time.sleep(300)
    else:
        count = scan_and_reply(reddit, config, templates, rate_limiter, dry_run=args.dry_run)
        log.info(f"Done. {count} replies posted.")


if __name__ == "__main__":
    main()
