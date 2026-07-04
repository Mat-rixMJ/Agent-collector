---
name: ads_manager
description: >
  Use when a kanban card has skill "ads_manager" — finding successful competitor/
  niche ads, extracting their marketing psychology, and writing new ad scripts
  for crowdwisdomtrading.com based on what's proven to work.
---

# Ads Manager Agent

Three-stage pipeline, run in order (each stage is idempotent — safe to re-run):

## Stage 1 — Find working ads
Run `scripts/scrape_meta_ads.py`. Pulls live Meta Ad Library ads for retail-
trading / prop-firm / trading-signals keywords, keeps only ads first seen in
the last 30 days, ranks by a simple "still running = working" heuristic (ads
still active after 2+ weeks are more likely profitable), saves top ~20 to
`data/ads/meta_ads_raw.json`.

## Stage 2 — Extract the marketing psychology
Run `scripts/extract_ad_concepts.py`. For each ad, an LLM pass extracts:
- the pain point being targeted
- the hook (first line / visual concept)
- the core offer/mechanism
- the CTA
Saves structured concepts to `data/ads/ad_concepts.json`.

## Stage 3 — Write our own ad script
Run `scripts/generate_ad_script.py`. Picks the concept(s) most relevant to
crowdwisdomtrading.com's actual product (market commentary, trade signals,
educational content), and writes a full ad script (hook/body/CTA + suggested
visual direction) grounded in that pattern but using CrowdWisdomTrading's own
value props — never copies competitor copy verbatim. Output →
`obsidian_vault/Ads/<date>_<concept-slug>.md`.

Move the kanban card to Review after Stage 3 completes; a human approves before
anything goes to production.

## Scripts (run in order)
- `python -m skills.ads_manager.scripts.scrape_meta_ads`
- `python -m skills.ads_manager.scripts.extract_ad_concepts`
- `python -m skills.ads_manager.scripts.generate_ad_script`
- `python -m skills.ads_manager.scripts.score_ad_scripts`
- `python -m skills.ads_manager.scripts.revise_ad_script`

## Tools available
- Terminal: you can execute the scripts above
- File system: you can read/write to obsidian_vault/Ads/ and data/ads/
