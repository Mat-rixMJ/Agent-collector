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
from tools import config_manager

IN_PATH = Path("data/influencers/influencers.json")
VAULT = Path(os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian_vault")) / "Outreach"
VAULT.mkdir(parents=True, exist_ok=True)

MAX_PER_RUN = 15  # ponytail: cap LLM calls per run; 15 × ~5s = ~75s

EMAIL_PROMPT = (
    "You write short, professional cold outreach EMAILS (under 140 words) from "
    "{company_name} to {niche} content creators, proposing a paid collaboration "
    "(such as a sponsored video segment or affiliate partnership). "
    "You must clearly state our value proposition: we offer competitive base rates, "
    "a high-converting affiliate commission structure, and free lifetime premium access "
    "for them and their audience. "
    "If given a specific recent video title, reference it naturally in the opening line "
    "to show genuine interest. If no specific content is given, do NOT invent one. "
    "End with a clear, low-friction next step (e.g., 'Let me know if you're open to checking out details, or reply to set up a brief chat'). "
    "Format: Subject line, then body. No corporate jargon or pushy sales pitch."
)

DM_PROMPT = (
    "You write ultra-short platform DMs (under 70 words) from "
    "{company_name} to {niche} creators. Casual, peer-to-peer tone. "
    "Start your message exactly with 'Hi {handle},' or 'Hey {handle},'. "
    "Propose a paid partnership or affiliate collaboration, highlighting the "
    "benefit (competitive sponsor fee + free premium access). "
    "Reference their recent video if given. End with a simple CTA like 'Let me know if you'd be open to a quick chat about this!' "
    "No emoji spam."
)


def draft(influencer: dict) -> tuple[str, str]:
    """Returns (email_draft, dm_draft)."""
    recent = influencer.get("recent_video_titles") or []
    context = f"Recent video: {recent[0]}" if recent and isinstance(recent[0], str) and recent[0] else "No specific recent content available."
    handle = influencer.get("handle", "unknown")
    subs = influencer.get("subscribers") or influencer.get("avg_views") or "unknown"

    user_context = (
        f"Creator: {handle} ({subs} followers/views)\n"
        f"Content focus: {influencer.get('description', '')[:200]}\n{context}"
    )

    email = ask(EMAIL_PROMPT.format(company_name=influencer.get("_company_name", "us"), niche=influencer.get("_niche", "creators")), user_context)
    dm_prompt_formatted = DM_PROMPT.format(
        company_name=influencer.get("_company_name", "us"), 
        niche=influencer.get("_niche", "creators"),
        handle=handle
    )
    dm = ask(dm_prompt_formatted, user_context)

    # Post-generation assertion: ensure the generated DM actually addresses the handle
    if handle.lower() not in dm.lower() and handle != "unknown":
        print(f"  [DM CHECK] Greeting mismatch for {handle}. Regenerating once...")
        dm = ask(dm_prompt_formatted, user_context)
        if handle.lower() not in dm.lower():
            print(f"  [DM CHECK] Second mismatch for {handle}. Falling back to generic greeting.")
            lines = dm.split("\n")
            if lines and ("Hi" in lines[0] or "Hey" in lines[0] or "Hello" in lines[0]):
                lines[0] = "Hi there,"
            else:
                lines.insert(0, "Hi there,")
            dm = "\n".join(lines)

    return email, dm


def main() -> None:
    if not IN_PATH.exists():
        print(f"{IN_PATH} not found — run find_influencers.py first.")
        return
    influencers = json.loads(IN_PATH.read_text())

    config = config_manager.load_config()
    company_name = config.get("company_name", "Our Company")
    niche = config.get("niche", "your niche")

    drafted_count = 0
    skipped_count = 0

    for inf in influencers:
        inf["_company_name"] = company_name
        inf["_niche"] = niche
        
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
