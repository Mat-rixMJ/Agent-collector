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
    return run_actor(
        "streamers/youtube-channel-scraper",
        {"startUrls": [{"url": f"https://www.youtube.com/results?search_query={query}"}],
         "maxResults": max_results},
    )


def get_youtube_transcript(video_url: str) -> dict:
    """Transcript + metadata for a single video. Swap actor_id as needed."""
    items = run_actor("pintostudio/youtube-transcript-scraper", {"videoUrl": video_url})
    return items[0] if items else {}


def rag_web_search(query: str, max_results: int = 5) -> list[dict]:
    """General-purpose competitor/web research via apify/rag-web-browser."""
    return run_actor("apify/rag-web-browser", {"query": query, "maxResults": max_results})
