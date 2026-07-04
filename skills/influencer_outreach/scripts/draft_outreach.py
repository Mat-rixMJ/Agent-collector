"""Stage 2: personalized cold-outreach draft per influencer dossier."""
import json
import os
import re
from pathlib import Path

from tools.llm_client import ask

IN_PATH = Path("data/influencers/influencers.json")
VAULT = Path(os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian_vault")) / "Outreach"
VAULT.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = (
    "You write short, genuine cold outreach messages (under 120 words) from "
    "CrowdWisdomTrading to trading content creators, asking for their honest "
    "opinion on crowdwisdomtrading.com — not pitching a paid sponsorship. "
    "If given a specific recent video title, reference it naturally in the "
    "opening line to prove this isn't a mass blast. If no specific recent "
    "content is given, do NOT invent one — write a slightly more general but "
    "still warm opener. No corporate tone, no exclamation-point spam."
)


def draft(influencer: dict) -> str:
    recent = influencer.get("recent_video_titles") or []
    context = f"Recent video: {recent[0]}" if recent else "No specific recent content available."
    return ask(
        SYSTEM_PROMPT,
        f"Creator: {influencer['handle']} ({influencer['subscribers']:,} subs)\n"
        f"Content angle: {influencer.get('description', '')[:200]}\n{context}",
    )


def main() -> None:
    if not IN_PATH.exists():
        print(f"{IN_PATH} not found — run find_influencers.py first.")
        return
    influencers = json.loads(IN_PATH.read_text())
    for inf in influencers:
        try:
            message = draft(inf)
        except Exception as e:
            print(f"  failed for {inf['handle']}: {e}")
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", inf["handle"].lower()).strip("-")
        note = (
            f"# Outreach draft — {inf['handle']}\n\n"
            f"- Platform: {inf['platform']}\n- Subscribers: {inf['subscribers']:,}\n"
            f"- URL: {inf.get('url', '')}\n- Contact: {inf.get('contact_email') or 'not public — use platform DM'}\n\n"
            f"## Draft message\n{message}\n"
        )
        (VAULT / f"{slug}.md").write_text(note, encoding="utf-8")
    print(f"Drafted outreach for {len(influencers)} influencers -> {VAULT}")


if __name__ == "__main__":
    main()
