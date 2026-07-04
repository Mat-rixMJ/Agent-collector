"""Stage 1: find retail-trading YouTube creators with 200K+ subscribers and
save full dossiers. Extend SEARCH_QUERIES / add actors for X, IG, TikTok using
the same pattern.
"""
import json
from pathlib import Path

from tools.apify_client import find_youtube_channels

OUT_PATH = Path("data/influencers/influencers.json")
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

MIN_SUBS = 200_000
SEARCH_QUERIES = [
    "day trading",
    "swing trading strategy",
    "retail trading psychology",
    "forex trading",
    "prop firm trading",
]


def normalize(channel: dict) -> dict:
    # The YouTube scraper returns video-level data from search; extract channel info
    subs = channel.get("subscriberCount") or channel.get("subscribers") or 0
    return {
        "platform": "youtube",
        "handle": channel.get("channelName") or channel.get("channelUsername") or channel.get("title"),
        "url": channel.get("channelUrl") or channel.get("url"),
        "subscribers": subs,
        "avg_views": channel.get("viewCount"),
        "description": channel.get("description", "")[:300],
        "contact_email": channel.get("email"),
        "recent_video_titles": [channel.get("title", "")],
    }


def main() -> None:
    all_channels = []
    for query in SEARCH_QUERIES:
        print(f"Searching YouTube channels: {query!r}")
        try:
            results = find_youtube_channels(query, min_subs=MIN_SUBS, max_results=20)
            all_channels.extend(normalize(c) for c in results)
        except Exception as e:
            print(f"  failed for {query!r}: {e}")

    # de-dupe by channel handle — the search scraper doesn't return sub counts,
    # so we keep all unique channels and note the limitation.
    # ponytail: sub-count filtering would need a separate channel-detail actor call
    seen = {}
    for c in all_channels:
        if c["handle"]:
            seen[c["handle"]] = c

    influencers = list(seen.values())
    OUT_PATH.write_text(json.dumps(influencers, indent=2))
    print(f"Found {len(influencers)} unique channels -> {OUT_PATH}")


if __name__ == "__main__":
    main()
