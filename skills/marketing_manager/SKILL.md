---
name: marketing-manager
description: Competitor research and strategy briefs for any target company/niche
version: 1.0.0
metadata:
  hermes:
    tags: [marketing, research, strategy, competitor-analysis]
    category: marketing
    requires_toolsets: [terminal]
---

# Marketing Manager Agent

## When to Use
Use when you need to: research competitors in the retail trading education space, write a marketing strategy brief, or prioritize tasks for the ads and influencer teams.

## Procedure

### Step 1: Competitor Research
Run the competitor research script to scrape and analyze competitors:
```bash
python -m skills.marketing_manager.scripts.competitor_research
```
This will:
- Search 5 competitors via Apify's rag-web-browser
- Extract positioning, pricing, and content strategy per competitor
- Detect changes from previous runs using agent memory
- Write notes to `obsidian_vault/Competitors/<name>.md`
- Write synthesis to `obsidian_vault/Competitors/_synthesis.md`

### Step 2: Strategy Brief
Generate the strategy brief from the research:
```bash
python -m skills.marketing_manager.scripts.generate_strategy
```
This produces `obsidian_vault/Strategy/brief.md` with:
- Target audience segments
- Funnel priorities (TOFU/MOFU/BOFU)
- This week's key message
- Positioning statements vs. named competitors

### Step 3: Review Outputs
Read the synthesis and brief:
```bash
cat obsidian_vault/Competitors/_synthesis.md
cat obsidian_vault/Strategy/brief.md
```
Summarize the key findings for the user.

## Pitfalls
- Apify free-tier can't access Trustpilot/Reddit (403 blocks) — this is expected, use other sources
- If LLM rate-limits, the scripts auto-retry with exponential backoff
- Don't invent competitor numbers — if data is thin, say "unclear from available data"

## Verification
- `obsidian_vault/Competitors/` should have 5+ .md files
- `obsidian_vault/Competitors/_synthesis.md` should list 3 gaps and 3 threats
- `obsidian_vault/Strategy/brief.md` should have audience segments and positioning
