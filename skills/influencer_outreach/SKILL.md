---
name: influencer-outreach
description: Find influencers in any niche and draft personalized cold outreach
version: 1.0.0
metadata:
  hermes:
    tags: [marketing, influencer, outreach, youtube, cold-email]
    category: marketing
    requires_toolsets: [terminal]
---

# Influencer Cold Outreach Agent

## When to Use
Use when you need to: discover content creators in your target niche, build influencer dossiers, or draft personalized cold outreach asking their opinion about your product.

## Procedure

### Stage 1 — Find Influencers
```bash
python -m skills.influencer_outreach.scripts.find_influencers
```
Searches YouTube for "retail trading" / "day trading" / "swing trading" / "forex trading" / "prop firm trading" creators. Saves dossiers to `data/influencers/influencers.json` with:
- Channel name, URL, platform
- Recent video titles (for personalization)
- View counts
- Description/content angle

### Stage 2 — Draft Outreach
```bash
python -m skills.influencer_outreach.scripts.draft_outreach
```
For each influencer (capped at 15 per run):
- Checks memory — skips already-drafted influencers
- Generates 2 variants: email format + short DM format
- References recent video titles when available
- Saves to `obsidian_vault/Outreach/<handle>.md`
- Marks as "drafted" in memory for next-run dedup

### Review Outputs
```bash
cat data/influencers/influencers.json | python -c "import sys,json; d=json.load(sys.stdin); print(f'{len(d)} influencers found')"
ls obsidian_vault/Outreach/
```

## Pitfalls
- YouTube search actor returns videos, not channels — we extract channel info from video results
- Subscriber counts aren't available from search results (would need separate channel scrape)
- NEVER fabricate a "recent video" reference — if no specific content is available, write a generic but warm opener
- Keep emails under 120 words, DMs under 60 words
- This agent never sends messages automatically — human reviews and sends

## Verification
- `data/influencers/influencers.json` should have 50+ unique channels
- `obsidian_vault/Outreach/` should have .md files with both Email and DM sections
- No outreach should mention a video title that doesn't exist in the dossier
