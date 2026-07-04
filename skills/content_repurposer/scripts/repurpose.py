"""Bonus 'Your idea' agent: repurpose the brief's raw YouTube data sources into
platform-native social assets (X thread, LinkedIn post, short-form video script).
"""
import os
import re
from pathlib import Path

from tools.apify_client import get_youtube_transcript
from tools.llm_client import ask

VAULT = Path(os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian_vault")) / "Content"
VAULT.mkdir(parents=True, exist_ok=True)

# The 6 URLs listed under "Data Sources" in the brief.
DATA_SOURCE_URLS = [
    "https://www.youtube.com/watch?v=JFMxDgmW8cw",
    "https://www.youtube.com/watch?v=8nFTkjPk80k",
    "https://www.youtube.com/watch?v=bpM9D1kQaAs",
    "https://www.youtube.com/watch?v=g-qW8fQimyg",
    "https://www.youtube.com/watch?v=vqFUuLO06qc",
    # note: g-qW8fQimyg appears twice in the brief — deduped here
]

EXTRACT_PROMPT = (
    "You are a content strategist. Given a video transcript, extract the 3-5 "
    "most quotable, insight-dense moments — the parts a marketing team would "
    "want to repurpose. For each, give a one-sentence summary (attribute as "
    "'the video discusses/argues' — do not present it as a verbatim quote "
    "unless the transcript text is short enough to quote exactly)."
)

REPURPOSE_PROMPT = (
    "Given this insight from a trading-education/market-commentary video, write "
    "three platform-native assets:\n"
    "1) TWITTER THREAD: 5-7 tweets, hook tweet first\n"
    "2) LINKEDIN POST: 150-250 words, more analytical/professional tone\n"
    "3) SHORT-FORM VIDEO SCRIPT: 30-45 seconds, HOOK/BODY/CTA structure with "
    "[visual direction] cues in brackets\n"
    "Clearly label each section with a markdown header."
)


def video_id(url: str) -> str:
    match = re.search(r"v=([\w-]+)", url)
    return match.group(1) if match else url


def process(url: str) -> None:
    vid = video_id(url)
    print(f"Processing {vid}...")
    data = get_youtube_transcript(url)
    # Transcript actor returns {"data": [{"text": "...", "start": "..."}, ...]}
    segments = data.get("data") or data.get("transcript") or []
    if isinstance(segments, list):
        transcript = " ".join(seg.get("text", "") for seg in segments if isinstance(seg, dict))
    else:
        transcript = str(segments)
    if not transcript.strip():
        print(f"  no transcript available for {vid} — skipping.")
        return

    insights_raw = ask(EXTRACT_PROMPT, transcript[:8000])
    assets = ask(REPURPOSE_PROMPT, insights_raw)

    note = (
        f"# Content repurposing — {vid}\n\n"
        f"Source: {url}\n\n"
        f"## Extracted insights\n{insights_raw}\n\n"
        f"## Repurposed assets\n{assets}\n"
    )
    (VAULT / f"{vid}.md").write_text(note, encoding="utf-8")


def main() -> None:
    for url in DATA_SOURCE_URLS:
        try:
            process(url)
        except Exception as e:
            print(f"  failed for {url}: {e}")
    print(f"Done. Notes written to {VAULT}")


if __name__ == "__main__":
    main()
