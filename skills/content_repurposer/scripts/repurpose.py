"""Content repurposing agent: turns YouTube data sources into platform-native
social content (X thread, LinkedIn post, short-form video script).

Improvements:
- Memory-aware: skips already-processed videos on re-runs
- Generates a content calendar after processing
"""
import os
import re
from pathlib import Path

from tools.apify_client import get_youtube_transcript
from tools.llm_client import ask
from tools import memory

VAULT = Path(os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian_vault")) / "Content"
VAULT.mkdir(parents=True, exist_ok=True)

# Curated default list of highly relevant retail-trading videos (used as fallback)
DEFAULT_TRADING_VIDEOS = [
    "https://www.youtube.com/watch?v=s532t5dF87o", # How to Start Day Trading
    "https://www.youtube.com/watch?v=4H-UjI4GsnM", # Retail Trading Psychology
    "https://www.youtube.com/watch?v=gM9zGsz-Dbg", # Forex Trading Course
    "https://www.youtube.com/watch?v=p4CoC5S9fG0", # Swing Trading Strategies
    "https://www.youtube.com/watch?v=F3QpgX5428s", # Prop Firm Trading Tips
]

EXTRACT_PROMPT = (
    "You are a content strategist. Given a video transcript, extract the 3-5 "
    "most quotable, insight-dense moments — the parts a marketing team would "
    "want to repurpose. For each, give a one-sentence summary (attribute as "
    "'the video discusses/argues' — do not present it as a verbatim quote)."
)

REPURPOSE_PROMPT = (
    "Given this insight from a trading-education/market-commentary video, write "
    "three platform-native assets:\n"
    "1) TWITTER THREAD: 5-7 tweets, hook tweet first, each under 280 chars\n"
    "2) LINKEDIN POST: 150-250 words, analytical/professional tone, include 3 hashtags\n"
    "3) SHORT-FORM VIDEO SCRIPT: 30-45 seconds, HOOK/BODY/CTA structure with "
    "[visual direction] cues in brackets\n"
    "Clearly label each section with a markdown header."
)

CALENDAR_PROMPT = (
    "You are a social media strategist. Given a list of content assets, "
    "create a 1-week posting calendar (Mon-Sun). Assign each asset to a "
    "day and platform (Twitter, LinkedIn, TikTok/Reels). Spread content "
    "evenly. Format as a markdown table with columns: Day | Platform | Asset | Best Time."
)


def video_id(url: str) -> str:
    match = re.search(r"v=([\w-]+)", url)
    return match.group(1) if match else url


def process(url: str) -> bool:
    vid = video_id(url)

    # Memory: skip already-processed videos
    if memory.was_processed(f"video:{vid}"):
        print(f"  [SKIP] {vid} already processed (in memory)")
        return False

    print(f"Processing {vid}...")
    data = get_youtube_transcript(url)
    segments = data.get("data") or data.get("transcript") or []
    if isinstance(segments, list):
        transcript = " ".join(seg.get("text", "") for seg in segments if isinstance(seg, dict))
    else:
        transcript = str(segments)
    if not transcript.strip():
        print(f"  no transcript available for {vid} — skipping.")
        return False

    insights_raw = ask(EXTRACT_PROMPT, transcript[:8000])
    assets = ask(REPURPOSE_PROMPT, insights_raw)

    note = (
        f"# Content repurposing — {vid}\n\n"
        f"Source: {url}\n\n"
        f"## Extracted insights\n{insights_raw}\n\n"
        f"## Repurposed assets\n{assets}\n"
    )
    (VAULT / f"{vid}.md").write_text(note, encoding="utf-8")
    memory.mark_processed(f"video:{vid}", {"url": url})
    return True


def generate_calendar() -> None:
    """Generate a content calendar from all processed content."""
    content_files = list(VAULT.glob("*.md"))
    content_files = [f for f in content_files if not f.name.startswith("_")]

    if not content_files:
        return

    # Gather asset summaries
    summaries = []
    for f in content_files[:5]:
        text = f.read_text(encoding="utf-8")
        # Extract just the first few lines of each asset type
        summaries.append(f"Video {f.stem}: {text[text.find('## Repurposed'):text.find('## Repurposed')+500]}")

    calendar = ask(CALENDAR_PROMPT, "\n\n".join(summaries))
    (VAULT / "_calendar.md").write_text(
        f"# Content Calendar\n\n*Auto-generated posting schedule*\n\n{calendar}\n",
        encoding="utf-8",
    )
    print(f"Content calendar written to {VAULT / '_calendar.md'}")


def main() -> None:
    import json
    urls = []
    
    # Try loading discovered video URLs first
    discovered_path = Path("data/influencers/discovered_videos.json")
    if discovered_path.exists():
        try:
            discovered = json.loads(discovered_path.read_text(encoding="utf-8"))
            if discovered:
                urls = [u for u in discovered if "watch?v=" in u]
                print(f"Loaded {len(urls)} discovered video URLs for repurposing.")
        except Exception as e:
            print(f"Failed to load discovered videos: {e}")
            
    if not urls:
        urls = DEFAULT_TRADING_VIDEOS
        print("Using curated fallback retail-trading videos for repurposing.")
        
    # Deduplicate and limit to 5
    urls = list(dict.fromkeys(urls))[:5]

    processed_count = 0
    for url in urls:
        try:
            if process(url):
                processed_count += 1
        except Exception as e:
            print(f"  failed for {url}: {e}")

    if processed_count > 0 or list(VAULT.glob("*.md")):
        generate_calendar()

    print(f"Done. {processed_count} new videos processed. Notes in {VAULT}")


if __name__ == "__main__":
    main()
