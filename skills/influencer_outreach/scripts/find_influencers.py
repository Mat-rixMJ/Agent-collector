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
    video_urls = []
    for query in SEARCH_QUERIES:
        print(f"Searching YouTube channels: {query!r}")
        try:
            results = find_youtube_channels(query, min_subs=MIN_SUBS, max_results=20)
            for r in results:
                # Capture video URL if present in the raw result
                v_url = r.get("url") or r.get("videoUrl")
                if v_url and "watch?v=" in v_url and v_url not in video_urls:
                    video_urls.append(v_url)
                all_channels.append(normalize(r))
        except Exception as e:
            print(f"  failed for {query!r}: {e}")

    # Fallback to cache if no channels were retrieved (e.g. Apify failed)
    if not all_channels:
        if OUT_PATH.exists():
            print(f"Apify channel search returned 0 results. Falling back to cached influencers from {OUT_PATH}")
            try:
                influencers = json.loads(OUT_PATH.read_text(encoding="utf-8"))
                # Write back or just print
                print(f"Loaded {len(influencers)} cached influencers.")
            except Exception as e:
                print(f"  failed to load cached influencers: {e}")
                influencers = []
        else:
            influencers = []
    else:
        # de-dupe by channel handle
        seen = {}
        for c in all_channels:
            if c["handle"]:
                seen[c["handle"]] = c
        influencers = list(seen.values())
        OUT_PATH.write_text(json.dumps(influencers, indent=2), encoding="utf-8")

    # Save discovered video URLs to a dedicated JSON file for Content Repurposer
    video_out = OUT_PATH.parent / "discovered_videos.json"
    if video_urls:
        video_out.write_text(json.dumps(video_urls, indent=2), encoding="utf-8")
        print(f"Saved {len(video_urls)} discovered video URLs -> {video_out}")
    else:
        print("No new video URLs scraped. Keeping existing discovered_videos.json if present.")

    print(f"Total influencers: {len(influencers)} -> {OUT_PATH}")


if __name__ == "__main__":
    main()
