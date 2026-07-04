"""Stage 1: pull live Meta Ad Library ads for the retail-trading niche,
keep ones first seen in the last 30 days, save raw + a ranked shortlist.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from tools.apify_client import scrape_meta_ads

OUT_DIR = Path("data/ads")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEARCH_TERMS = [
    "trading signals",
    "prop firm challenge",
    "learn day trading",
    "forex trading course",
    "trading bot",
]


def within_last_30_days(ad: dict) -> bool:
    date_str = ad.get("ad_delivery_start_time") or ad.get("startDate") or ad.get("startedRunningOn")
    if not date_str:
        return False
    try:
        started = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        # Make comparison timezone-aware
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return False
    return started >= datetime.now(timezone.utc) - timedelta(days=30)


def rank(ads: list[dict]) -> list[dict]:
    # Heuristic: ads still active are more likely to be working (advertiser
    # keeps paying for them). Longer active duration = stronger signal.
    def days_active(ad: dict) -> int:
        date_str = ad.get("ad_delivery_start_time") or ad.get("startDate") or ad.get("startedRunningOn")
        if not date_str:
            return 0
        try:
            started = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - started).days
        except (ValueError, TypeError):
            return 0

    return sorted(ads, key=days_active, reverse=True)


def main() -> None:
    all_ads = []
    for term in SEARCH_TERMS:
        print(f"Searching Meta Ads Library: {term!r}")
        try:
            results = scrape_meta_ads([term], max_results=50)
            all_ads.extend(results)
        except Exception as e:
            print(f"  failed for {term!r}: {e}")

    (OUT_DIR / "meta_ads_raw.json").write_text(json.dumps(all_ads, indent=2, default=str))

    recent = [a for a in all_ads if within_last_30_days(a)]
    shortlist = rank(recent)[:20]
    (OUT_DIR / "meta_ads_shortlist.json").write_text(json.dumps(shortlist, indent=2, default=str))

    print(f"Total ads scraped: {len(all_ads)} | last-30-day: {len(recent)} | shortlisted: {len(shortlist)}")


if __name__ == "__main__":
    main()
