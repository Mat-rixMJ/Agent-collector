"""Thin wrapper around the Apify Python SDK used by every skill's scripts.

Keeps actor names + polling logic in one place so ads_manager and
influencer_outreach scripts stay short and swappable.
"""
import os
from datetime import timedelta
from typing import Any

from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN")


def _client() -> ApifyClient:
    if not APIFY_TOKEN:
        raise RuntimeError("APIFY_TOKEN not set — copy .env.example to .env and fill it in.")
    return ApifyClient(APIFY_TOKEN)


def run_actor(actor_id: str, run_input: dict[str, Any], timeout_secs: int = 300) -> list[dict]:
    """Runs an Apify actor to completion and returns its dataset items as a list of dicts."""
    import logging
    logging.getLogger("apify_client").setLevel(logging.WARNING)

    client = _client()
    run = client.actor(actor_id).call(
        run_input=run_input,
        run_timeout=timedelta(seconds=timeout_secs),
    )
    if not run:
        return []
    dataset_id = run.default_dataset_id
    items = list(client.dataset(dataset_id).iterate_items())
    return items


# --- Actor presets used across this project (swap ids if you prefer a different scraper) ---

def scrape_meta_ads(search_terms: list[str], countries: list[str] | None = None,
                     max_results: int = 100) -> list[dict]:
    """Meta Ad Library ads for given keywords. Actor: solidcode/meta-ads-library-scraper"""
    if os.getenv("DEMO_MODE") == "true":
        import json
        from pathlib import Path
        print("  [DEMO] Loading cached raw Meta ads library data...")
        cache_path = Path("data/ads/meta_ads_raw.json")
        if cache_path.exists():
            return json.loads(cache_path.read_text(encoding="utf-8"))
        return []
    return run_actor(
        "solidcode/meta-ads-library-scraper",
        {
            "searchTerms": search_terms,
            "country": (countries or ["US"])[0],
            "adActiveStatus": "ALL",
            "scrapeAdDetails": True,
            "includeAboutPage": True,
            "maxResults": max_results,
        },
    )


def find_youtube_channels(query: str, min_subs: int = 200_000, max_results: int = 30) -> list[dict]:
    """Retail-trading YouTube channels above a subscriber threshold.
    Swap actor_id for whichever channel-search actor you prefer/have credits for.
    """
    if os.getenv("DEMO_MODE") == "true":
        print("  [DEMO] Bypassing search, will trigger cached influencers fallback...")
        return []
    return run_actor(
        "streamers/youtube-channel-scraper",
        {"startUrls": [{"url": f"https://www.youtube.com/results?search_query={query}"}],
         "maxResults": max_results},
    )


MOCK_TRANSCRIPTS = {
    "s532t5dF87o": [
        {"text": "Welcome back to the channel. Today we are talking about how to start day trading as a beginner."},
        {"text": "Day trading is not a get rich quick scheme. It is a business that requires discipline, patience, and practice."},
        {"text": "First, you must understand price action and basic chart patterns like support and resistance."},
        {"text": "Second, risk management is everything. Never risk more than one percent of your account on a single trade."},
        {"text": "Third, create a strict trading plan and stick to it. We recommend practicing on a simulator before using real money."}
    ],
    "4H-UjI4GsnM": [
        {"text": "In this video, we dive deep into retail trading psychology and why most traders fail."},
        {"text": "The main enemies of a day trader are fear and greed, which cause you to break your own rules."},
        {"text": "Traders often cut their wins short out of fear and let their losses run hoping the market will turn."},
        {"text": "To succeed, you must build a rule-based system and accept that losses are just a cost of doing business."},
        {"text": "Mastering your emotions and executing your plan consistently is what separates profitable traders from the rest."}
    ],
    "gM9zGsz-Dbg": [
        {"text": "Welcome to the ultimate forex trading course for beginners."},
        {"text": "The foreign exchange market is the largest financial market in the world, trading currencies 24 hours a day."},
        {"text": "We will cover major currency pairs like EURUSD and GBPUSD, and explain what pips, leverage, and margin mean."},
        {"text": "You will learn how to read charts, identify trends, and place buy and sell orders with proper stop losses."},
        {"text": "Remember, leverage can multiply your profits but it can also wipe out your account if you do not manage risk."}
    ],
    "p4CoC5S9fG0": [
        {"text": "Today we are detailing swing trading strategies that you can use while keeping a day job."},
        {"text": "Swing trading involves holding positions for several days to weeks to capture larger market trends."},
        {"text": "We use indicators like moving averages to identify the trend and RSI to spot oversold and overbought conditions."},
        {"text": "We look for support and resistance levels for our entry and exit signals, confirming with volume analysis."},
        {"text": "Swing trading is less stressful than day trading and allows you to capture bigger, more reliable moves."}
    ],
    "F3QpgX5428s": [
        {"text": "Let's talk about how to pass a prop firm challenge and trade with funded capital."},
        {"text": "Prop firms give you large accounts to trade with, but you must prove your risk management first."},
        {"text": "To pass the evaluation, you must reach a profit target while staying within daily and maximum drawdown limits."},
        {"text": "The best tip is to size your positions conservatively, risking only half a percent per trade."},
        {"text": "Focus on consistency and don't rush. Slow and steady wins the prop firm challenge."}
    ]
}


def get_youtube_transcript(video_url: str) -> dict:
    """Transcript + metadata for a single video. Swap actor_id as needed."""
    import re
    match = re.search(r"(?:v=|\/)([\w-]+)", video_url)
    vid = match.group(1) if match else video_url

    if os.getenv("DEMO_MODE") == "true":
        print(f"  [DEMO] Returning mock transcript for YouTube video: {vid}")
        if vid in MOCK_TRANSCRIPTS:
            return {"data": MOCK_TRANSCRIPTS[vid]}
        return {"data": [{"text": "Hello, welcome to this video about retail trading signals and strategy."}]}

    try:
        items = run_actor("pintostudio/youtube-transcript-scraper", {"videoUrl": video_url})
        if items and (items[0].get("data") or items[0].get("transcript")):
            return items[0]
    except Exception as e:
        print(f"  Apify transcript scraper failed for {video_url}: {e}. Trying local fallback...")

    # Local fallback for the 5 curated trading videos
    if vid in MOCK_TRANSCRIPTS:
        print(f"  [FALLBACK] Using pre-written mock transcript for video {vid}")
        return {"data": MOCK_TRANSCRIPTS[vid]}

    return {}


def rag_web_search(query: str, max_results: int = 5) -> list[dict]:
    """General-purpose competitor/web research via apify/rag-web-browser."""
    if os.getenv("DEMO_MODE") == "true":
        print(f"  [DEMO] Performing offline web search for: '{query}'")
        # Return content scoped ONLY to the specific competitor in the query.
        # A single blob containing all competitor names caused keyword collisions
        # in the LLM demo dispatcher, returning Warrior Trading's profile for
        # every competitor. Each mock now contains only the queried company.
        q = query.lower()
        if "warrior trading" in q:
            content = (
                "Warrior Trading was founded by Ross Cameron and focuses on momentum "
                "day trading of small-cap stocks. Their premium trading room and simulator "
                "bundle costs $997 to $4,297 per year. They offer live trading rooms, "
                "detailed technical courses, and a proprietary stock simulator."
            )
        elif "bullish bears" in q:
            content = (
                "Bullish Bears offers low-cost trading courses and Discord trade alerts "
                "for retail traders at $47/mo or $397/yr. They cover options, swing trading, "
                "and day trading strategies. The platform is known for its supportive community "
                "and beginner-friendly approach."
            )
        elif "the trading channel" in q:
            content = (
                "The Trading Channel is run by Steven Hart and focuses on retail forex and "
                "swing trading education. Courses start at $297. They have a large YouTube "
                "presence with free technical analysis content. Upsells to more expensive "
                "course bundles are common."
            )
        elif "investors underground" in q:
            content = (
                "Investors Underground is one of the oldest day trading chatrooms, "
                "focusing on momentum and swing trading. Pricing is $297/mo or $1,897/yr. "
                "They offer high-quality webinar archives and seasoned moderators, but the "
                "high price is a barrier for beginners."
            )
        elif "fundednext" in q:
            content = (
                "FundedNext is a leading prop trading firm offering evaluation accounts "
                "for traders seeking funded capital. Evaluation fees start at $99 for $6k "
                "accounts and scale up to $1,000+ for larger accounts. Profit share starts "
                "during the assessment phase. Strict drawdown rules apply."
            )
        else:
            content = f"General market research results for: {query}. No specific competitor data found."
        return [{"url": f"https://example.com/search?q={query}", "markdown": content}]
    try:
        return run_actor("apify/rag-web-browser", {"query": query, "maxResults": max_results})
    except Exception as e:
        print(f"  Apify web search failed for {query!r}: {e}. Returning empty list.")
        return []
