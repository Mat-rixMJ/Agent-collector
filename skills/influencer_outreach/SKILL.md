---
name: influencer_outreach
description: >
  Use when a kanban card has skill "influencer_outreach" — finding retail-
  trading influencers with 200K+ subscribers and drafting personalized cold
  outreach asking their opinion on crowdwisdomtrading.com.
---

# Influencer Cold Outreach Agent

## Stage 1 — Find influencers
Run `scripts/find_influencers.py`. Searches YouTube (primary; extend the same
pattern to X/IG/TikTok with additional Apify actors) for "retail trading" /
"day trading" / "swing trading" creators, filters to 200K+ subscribers, and
saves a full dossier per influencer to `data/influencers/influencers.json`:
handle, platform, subscriber count, average views, engagement rate if
derivable, recent video topics, public contact email if listed in their
channel "About" page, and a one-line note on their content angle (technical
analysis vs. psychology vs. signals vs. news commentary).

## Stage 2 — Draft outreach
Run `scripts/draft_outreach.py`. For each influencer, writes a short,
non-salesy cold email/DM that:
- References something specific and recent from their content (proves it's
  not a mass blast)
- Asks for their honest opinion on crowdwisdomtrading.com — framed as wanting
  feedback, not pitching a sponsorship
- Is under 120 words

Never fabricate a "recent video" reference — if the dossier has no specific
recent content, the draft must be generic rather than inventing a fake detail.
Output → `obsidian_vault/Outreach/<handle>.md`.

Move card to Review when both stages complete — a human reviews/sends, this
agent never sends automatically.

## Scripts (run in order)
- `python -m skills.influencer_outreach.scripts.find_influencers`
- `python -m skills.influencer_outreach.scripts.draft_outreach`

## Tools available
- Terminal: you can execute the scripts above
- File system: you can read/write to obsidian_vault/Outreach/ and data/influencers/
