---
name: ads-manager
description: Find working competitor ads, extract marketing psychology, write ad scripts for any target company
version: 1.0.0
metadata:
  hermes:
    tags: [marketing, ads, copywriting, meta-ads, direct-response]
    category: marketing
    requires_toolsets: [terminal]
---

# Ads Manager Agent

## When to Use
Use when you need to: find successful ads in the retail trading niche, extract their marketing patterns, generate new ad scripts, or evaluate/revise existing scripts.

## Procedure

### Stage 1 — Scrape Working Ads
```bash
python -m skills.ads_manager.scripts.scrape_meta_ads
```
Pulls live Meta Ad Library ads for retail-trading / prop-firm keywords. Filters to last 30 days. Ranks by "still running = working" heuristic. Saves top 20 to `data/ads/meta_ads_shortlist.json`.

### Stage 2 — Extract Marketing Psychology
```bash
python -m skills.ads_manager.scripts.extract_ad_concepts
```
For each shortlisted ad, extracts: pain point, hook, offer mechanism, CTA. Saves structured concepts to `data/ads/ad_concepts.json`.

### Stage 3 — Generate 3 Ad Script Variants
```bash
python -m skills.ads_manager.scripts.generate_ad_script
```
Picks the best concept and writes 3 original scripts using different angles:
1. **Fear/loss aversion** — what the viewer is losing by NOT acting
2. **Aspiration/gain** — what life looks like AFTER the solution
3. **Social proof** — evidence others are already benefiting

Each script goes to `obsidian_vault/Ads/<date>_<slug>_<angle>.md`.

### Stage 4 — Score Scripts
```bash
python -m skills.ads_manager.scripts.score_ad_scripts
```
Evaluates each script on 5 criteria (hook strength, pain clarity, mechanism, proof, CTA urgency). Scores out of 50. Writes `obsidian_vault/Ads/_scorecard.md`.

### Stage 5 — Auto-Revise Weak Scripts
```bash
python -m skills.ads_manager.scripts.revise_ad_script
```
If any script scores below 40/50, rewrites the weakest section using the scorer's feedback. Saves as `*_revised.md`.

### Review Outputs
```bash
cat obsidian_vault/Ads/_scorecard.md
```

## Pitfalls
- Meta Ads actor requires `adActiveStatus: "ALL"` (uppercase)
- Date comparisons must handle both timezone-aware and naive datetimes
- Never copy competitor ad text verbatim — use the pattern, not the words

## Verification
- `data/ads/meta_ads_shortlist.json` should have 5-20 ads
- `data/ads/ad_concepts.json` should have structured concept extractions
- `obsidian_vault/Ads/` should have 3+ script variants + scorecard
- Top script should score 35+/50
