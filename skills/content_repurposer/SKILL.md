---
name: content_repurposer
description: >
  Use when a kanban card has skill "content_repurposer" — turning the raw
  YouTube data sources provided in the brief into distributable social content
  (this is the "Your idea!!" bonus scope for this assignment).
---

# Content Repurposing Agent ("Your idea" scope)

**Why this agent exists:** the brief lists 6 YouTube URLs under "Data Sources"
with no stated purpose. A marketing team's actual job with raw market-commentary
video is repurposing it into distributed content — not just watching it. This
agent closes that loop end-to-end with no manual editing step.

## Pipeline (`scripts/repurpose.py`)
1. Pull transcript + metadata for each URL in `DATA_SOURCE_URLS` via Apify.
2. LLM pass: extract the 3–5 most quotable/insight-dense moments per video.
3. For each insight, generate three platform-native assets:
   - a Twitter/X thread (5-7 tweets)
   - a LinkedIn post (150-250 words, more analytical tone)
   - a 30-45s short-form video script (hook + body + CTA, with [visual] cues)
4. Save everything to `obsidian_vault/Content/<video-id>.md`, one file per
   source video with all three formats side by side for quick review.

Never present a paraphrase as a direct quote from the video — attribute
insights to "the video discusses..." rather than fabricated verbatim quotes,
since transcript extraction can be imperfect.

## Scripts
- `python -m skills.content_repurposer.scripts.repurpose`

## Tools available
- Terminal: you can execute the script above
- File system: you can read/write to obsidian_vault/Content/
