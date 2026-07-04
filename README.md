# CrowdWisdomTrading Marketing Agents (Hermes Agent + Obsidian)

Multi-agent marketing system for crowdwisdomtrading.com, built on **Hermes Agent**
(Nous Research's open-source agent runtime) using its native **skills**, **kanban
board**, **Telegram gateway**, and an **Obsidian vault** as the human-readable
knowledge base. Data collection uses **Apify**. LLM calls go through **OpenRouter**.

## Why this stack maps to the brief

| Requirement | How it's met |
|---|---|
| Hermes + Obsidian | Hermes is the runtime/orchestrator; `obsidian_vault/` is the readable memory layer agents write research, ad scripts, and influencer dossiers into |
| OpenRouter / NVIDIA build | `tools/llm_client.py` — swap `LLM_PROVIDER` env var |
| Apify | `tools/apify_client.py` wraps the actors used for ads + influencer discovery |
| Kanban | `kanban/board.json` + `tools/kanban.py` — Hermes' built-in kanban tool tracks each agent's tasks (To Do → In Progress → Review → Done) |
| Loops + skills | Each agent is a Hermes **skill** (`skills/*/SKILL.md`) invoked in an orchestration loop (`main.py`) that re-runs until the kanban board is clear |
| Telegram | `tools/telegram_bot.py` — chat with the agent team, get run summaries pushed to you |

## Project layout

```
crowdwisdom-marketing-agents/
├── main.py                        # orchestration loop (the "manager of managers")
├── hermes/
│   └── config.yaml                # Hermes runtime config: model, telegram, obsidian vault path
├── skills/                        # one Hermes skill per agent (SKILL.md = model-invoked spec)
│   ├── marketing_manager/
│   ├── ads_manager/
│   ├── influencer_outreach/
│   └── content_repurposer/        # <- "Your idea" bonus agent, see below
├── tools/                         # shared Python clients used by every skill's scripts
│   ├── apify_client.py
│   ├── llm_client.py
│   ├── telegram_bot.py
│   └── kanban.py
├── kanban/board.json              # live task board, mirrors Hermes' kanban view
├── obsidian_vault/                # created at runtime — Markdown notes agents write
└── data/                          # raw JSON scrape outputs (ads, influencers, competitors)
```

## Agent team

### 1. Marketing Manager Agent (`skills/marketing_manager`)
- Owns overall strategy: audience, positioning, funnel stage priorities.
- Runs competitor research (scrapes competitor sites/socials via Apify's
  `rag-web-browser` + relevant scrapers) and writes a competitor brief to Obsidian.
- Assigns/prioritizes kanban cards for the other two agents.

### 2. Ads Manager Agent (`skills/ads_manager`)
Three-stage pipeline, each a separate script (so it can be looped/retried independently):
1. `scrape_meta_ads.py` — pulls live Meta Ad Library ads for the trading/fintech
   niche via Apify (`solidcode/meta-ads-library-scraper`), filters to ads first
   seen in the last 30 days, saves to `data/ads/meta_ads_raw.json`.
2. `extract_ad_concepts.py` — LLM pass that extracts the pain point, hook, offer,
   and creative angle from each ad → `data/ads/ad_concepts.json`.
3. `generate_ad_script.py` — takes the strongest concept + CrowdWisdomTrading's own
   data/voice and writes a ready-to-shoot ad script (hook/body/CTA) to
   `obsidian_vault/Ads/`.

### 3. Influencer Cold Outreach Agent (`skills/influencer_outreach`)
1. `find_influencers.py` — uses Apify actors (YouTube channel search + TikTok/IG
   profile scrapers) to find retail-trading creators with 200K+ subscribers,
   saves full profile dossiers (handle, platform, subs, engagement, contact email
   if public, recent content themes) to `data/influencers/influencers.json`.
2. `draft_outreach.py` — LLM-personalizes a cold email/DM per influencer asking
   for their honest opinion on crowdwisdomtrading.com, referencing something
   specific from their recent content. Output → `obsidian_vault/Outreach/`.

### 4. Content Repurposing Agent — "Your idea" (`skills/content_repurposer`)
The brief lists 6 YouTube videos as "data sources" with no stated use — the
obvious job for a marketing team is **repurposing**, not just watching. This
agent:
- Pulls transcripts for the provided YouTube links via Apify.
- Extracts the strongest 3–5 quotable insights/soundbites per video.
- Turns each into a platform-native asset: a Twitter/X thread, a LinkedIn post,
  and a 30–45s short-form video script — all saved to `obsidian_vault/Content/`.
- This closes the loop between "here's raw market commentary" and "here's
  distributed content" without any manual editing.

## Orchestration loop (`main.py`)

```python
while kanban.has_open_cards():
    for skill in [marketing_manager, ads_manager, influencer_outreach, content_repurposer]:
        card = kanban.next_card_for(skill)
        if card:
            result = skill.run(card)
            kanban.move(card, to="Review" if result.ok else "Blocked")
    telegram_bot.push_summary(kanban.snapshot())
```
This is intentionally simple (a poll-and-dispatch loop) rather than a heavyweight
DAG, because Hermes already handles retries/skill-selection internally — `main.py`
just seeds the board and keeps nudging it forward, which is what "using loops"
in the eval criteria is checking for.

## Setup

```bash
git clone <your-repo-url>
cd crowdwisdom-marketing-agents
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in APIFY_TOKEN, OPENROUTER_API_KEY, TELEGRAM_BOT_TOKEN
python main.py
```

Install Hermes Agent separately (self-hosted runtime) and point it at this repo's
`skills/` folder — see https://hermes-agent.org for install docs. `hermes/config.yaml`
here documents the exact settings (model, telegram, obsidian vault path) to paste
into `~/.hermes/config.yaml`.

## Submission checklist (per the brief)
- [ ] GitHub repo link
- [ ] Apify token used pasted into submission email (so they can rerun) — **do not
      commit real tokens to the repo**, only `.env.example` should be committed
- [ ] Screen recording of the Hermes kanban board moving cards across the loop
- [ ] `.md` exports of each agent's output (Obsidian vault notes double as this)
