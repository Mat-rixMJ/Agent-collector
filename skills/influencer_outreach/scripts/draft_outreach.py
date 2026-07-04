"""Stage 2: personalized cold-outreach draft per influencer dossier.

Improvements:
- Memory-aware: skips already-drafted influencers on re-runs
- Generates 2 variants: email format + short DM format
- Limits to 15 influencers per run to control LLM usage
- References recent video titles when available
"""
import json
import os
import re
from pathlib import Path

from tools.llm_client import ask
from tools import memory

IN_PATH = Path("data/influencers/influencers.json")
VAULT = Path(os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian_vault")) / "Outreach"
VAULT.mkdir(parents=True, exist_ok=True)

MAX_PER_RUN = 15  # ponytail: cap LLM calls per run; 15 × ~5s = ~75s

EMAIL_PROMPT = (
    "You write short, genuine cold outreach EMAILS (under 120 words) from "
    "CrowdWisdomTrading to trading content creators, asking for their honest "
    "opinion on crowdwisdomtrading.com — not pitching a paid sponsorship. "
    "If given a specific recent video title, reference it naturally in the "
    "opening line. If no specific content is given, do NOT invent one. "
    "Format: Subject line, then body. No corporate tone."
)

DM_PROMPT = (
    "You write ultra-short platform DMs (under 60 words) from "
    "CrowdWisdomTrading to trading creators. Casual tone, like you'd "
    "DM a peer. Ask their opinion on crowdwisdomtrading.com. "
    "Reference their recent content if given. No emojis spam."
)


def draft(influencer: dict) -> tuple[str, str]:
    """Returns (email_draft, dm_draft)."""
    recent = influencer.get("recent_video_titles") or []
    context = f"Recent video: {recent[0]}" if recent and isinstance(recent[0], str) and recent[0] else "No specific recent content available."
    handle = influencer.get("handle", "unknown")
    subs = influencer.get("subscribers") or influencer.get("avg_views") or "unknown"

    user_context = (
        f"Creator: {handle} ({subs} followers/views)\n"
        f"Content angle: {influencer.get('description', '')[:200]}\n{context}"
    )

    email = ask(EMAIL_PROMPT, user_context)
    dm = ask(DM_PROMPT, user_context)
    return email, dm


def main() -> None:
    if not IN_PATH.exists():
        print(f"{IN_PATH} not found — run find_influencers.py first.")
        return
    influencers = json.loads(IN_PATH.read_text())

    drafted_count = 0
    skipped_count = 0

    for inf in influencers:
        if drafted_count >= MAX_PER_RUN:
            print(f"  Hit cap of {MAX_PER_RUN} drafts per run. Remaining will be drafted next run.")
            break

        handle = inf.get("handle", "unknown")
        mem_key = f"outreach:{handle}"

        # Skip already-drafted influencers
        if memory.was_processed(mem_key):
            skipped_count += 1
            continue

        try:
            email, dm = draft(inf)
        except Exception as e:
            print(f"  failed for {handle}: {e}")
            continue

        slug = re.sub(r"[^a-z0-9]+", "-", handle.lower()).strip("-")
        note = (
            f"# Outreach — {handle}\n\n"
            f"- Platform: {inf.get('platform', 'youtube')}\n"
            f"- URL: {inf.get('url', '')}\n"
            f"- Contact: {inf.get('contact_email') or 'not public — use platform DM'}\n\n"
            f"## Email Version\n{email}\n\n"
            f"## DM Version\n{dm}\n"
        )
        (VAULT / f"{slug}.md").write_text(note, encoding="utf-8")
        memory.mark_processed(mem_key, {"status": "drafted"})
        drafted_count += 1

    print(f"Drafted: {drafted_count} | Skipped (already done): {skipped_count} | "
          f"Remaining: {len(influencers) - drafted_count - skipped_count}")
    print(f"Outreach files in {VAULT}")


if __name__ == "__main__":
    main()
