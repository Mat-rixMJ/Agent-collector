---
name: content-repurposer
description: Repurpose YouTube videos into Twitter threads, LinkedIn posts, and short-form video scripts
version: 1.0.0
metadata:
  hermes:
    tags: [marketing, content, social-media, youtube, repurposing]
    category: marketing
    requires_toolsets: [terminal]
---

# Content Repurposing Agent

## When to Use
Use when you have YouTube video URLs that need to be turned into distributable social media content across multiple platforms.

## Procedure

### Step 1 — Process Videos
```bash
python -m skills.content_repurposer.scripts.repurpose
```
For each video URL in the configured list:
1. Checks memory — skips already-processed videos
2. Pulls transcript via Apify's youtube-transcript-scraper
3. Extracts 3-5 most quotable/insight-dense moments via LLM
4. Generates three platform-native assets per insight:
   - **Twitter/X thread** (5-7 tweets, hook first, each under 280 chars)
   - **LinkedIn post** (150-250 words, analytical tone, 3 hashtags)
   - **Short-form video script** (30-45s, HOOK/BODY/CTA + [visual] cues)
5. Saves all to `obsidian_vault/Content/<video-id>.md`
6. Generates a weekly content calendar: `obsidian_vault/Content/_calendar.md`
7. Marks video as processed in memory

### Step 2 — Review Calendar
```bash
cat obsidian_vault/Content/_calendar.md
```
The calendar suggests which assets to post on which day/platform.

### Data Sources
These are the YouTube URLs from the brief:
- https://www.youtube.com/watch?v=JFMxDgmW8cw
- https://www.youtube.com/watch?v=8nFTkjPk80k
- https://www.youtube.com/watch?v=bpM9D1kQaAs
- https://www.youtube.com/watch?v=g-qW8fQimyg
- https://www.youtube.com/watch?v=vqFUuLO06qc

## Pitfalls
- Transcript actor returns `{data: [{text, start, dur}, ...]}` — join all `.text` fields
- Never present a paraphrase as a direct quote — attribute as "the video discusses..."
- Some videos may not have transcripts available — skip gracefully
- Memory prevents re-processing on subsequent runs (by design)

## Verification
- `obsidian_vault/Content/` should have one .md per processed video
- Each file should contain: Extracted insights + Twitter thread + LinkedIn post + Video script
- `obsidian_vault/Content/_calendar.md` should have a weekly posting schedule
