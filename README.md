# CrowdWisdomTrading Marketing Agents

A production-grade multi-agent marketing automation system built on **Hermes Agent** (Nous Research) with **Obsidian** as the knowledge layer. Four specialized AI agents collaborate through a kanban-driven orchestration loop to execute the full marketing pipeline for [crowdwisdomtrading.com](https://crowdwisdomtrading.com).

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     main.py (Orchestrator)                    │
│         Poll-and-dispatch loop + Kanban board mgmt           │
├──────────┬──────────┬─────────────────┬─────────────────────┤
│ Marketing│   Ads    │   Influencer    │     Content          │
│ Manager  │ Manager  │   Outreach      │    Repurposer        │
├──────────┴──────────┴─────────────────┴─────────────────────┤
│                    Shared Tool Layer                          │
│  apify_client │ llm_client │ kanban │ memory │ telegram_bot  │
├─────────────────────────────────────────────────────────────┤
│              External Services                               │
│  Apify (scraping) │ LLM (Ollama/NVIDIA/OpenRouter) │ Telegram│
└─────────────────────────────────────────────────────────────┘
```

---

## What This System Does

| Agent | Input | Output |
|-------|-------|--------|
| **Marketing Manager** | Niche definition | Competitor briefs, positioning gaps, strategy brief |
| **Ads Manager** | Meta Ads Library data | Ad concepts, 3 script variants, scores, auto-revised scripts |
| **Influencer Outreach** | YouTube search results | 70+ channel dossiers, personalized email + DM drafts |
| **Content Repurposer** | YouTube video URLs | X threads, LinkedIn posts, video scripts, content calendar |

All outputs land in `obsidian_vault/` as Markdown files — a human-readable knowledge base that doubles as the submission deliverable.

---

## Key Differentiators

### Agent Memory System
Persistent state across runs. Competitors are tracked for positioning changes. Ads are deduplicated. Influencers marked as "drafted" are skipped on re-runs. Videos processed once are never reprocessed. Second runs complete in half the time.

### A/B Script Scoring + Auto-Revision
Every generated ad script is evaluated on 5 direct-response criteria (hook strength, pain clarity, mechanism, proof, CTA urgency) scored out of 50. Scripts below threshold are automatically revised using the scorer's feedback — a closed-loop creative optimization system.

### Multi-Angle Script Generation
Instead of one script, generates 3 variants per concept using different psychological entry points (fear/loss aversion, aspiration/gain, social proof). The scorer then ranks them so you know which to produce first.

### Interactive Telegram Bot
Not just push notifications. A conversational agent you can query in real-time: `/status`, `/score`, `/outreach @handle`, `/changes`, `/competitors`. Asks questions, the agent answers using all pipeline data as context.

### PDF Executive Report
One command generates a professional PDF with executive summary, competitor analysis, ad scorecard, influencer table, and content samples — designed for non-technical stakeholders who don't read JSON.

### LLM Provider Flexibility
Swap between NVIDIA build, OpenRouter, or local Ollama with one env var. Smart rate-limit handling: reads `Retry-After` headers, rotates models, falls back gracefully. Never crashes on a 429.

---

## Quick Start

### Prerequisites
- Python 3.11+
- Git
- Apify account (free tier: https://console.apify.com)
- One LLM provider (Ollama recommended for local; NVIDIA/OpenRouter for cloud)

### Installation

```bash
git clone https://github.com/Mat-rixMJ/Agent-collector.git
cd Agent-collector
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required
APIFY_TOKEN=your_apify_token

# LLM — pick one
LLM_PROVIDER=ollama              # ollama | nvidia | openrouter
OLLAMA_MODEL=qwen2.5:7b          # for local (install: ollama pull qwen2.5:7b)
NVIDIA_API_KEY=nvapi-xxx          # from build.nvidia.com
NVIDIA_MODEL=meta/llama-3.1-8b-instruct
OPENROUTER_API_KEY=sk-or-xxx     # from openrouter.ai

# Optional (for Telegram integration)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Run

```bash
# Full pipeline (batch mode, uses Ollama)
python main.py

# Hermes Agent native mode (uses NVIDIA/OpenRouter API)
python hermes_runner.py

# Generate PDF report from existing outputs
python generate_pdf_report.py

# Start interactive Telegram bot
python tools/telegram_bot.py
```

---

## Project Structure

```
├── main.py                          # Orchestration loop (batch pipeline)
├── hermes_runner.py                 # Hermes AIAgent native integration
├── generate_pdf_report.py           # PDF report generator
├── generate_report.py               # Markdown report generator
├── Modelfile                        # Ollama 64K context model definition
│
├── hermes/
│   └── config.yaml                  # Hermes runtime configuration
│
├── skills/                          # Hermes skills (one per agent)
│   ├── marketing_manager/
│   │   ├── SKILL.md                 # Agent instructions (Hermes format)
│   │   └── scripts/
│   │       ├── competitor_research.py
│   │       └── generate_strategy.py
│   ├── ads_manager/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       ├── scrape_meta_ads.py
│   │       ├── extract_ad_concepts.py
│   │       ├── generate_ad_script.py
│   │       ├── score_ad_scripts.py
│   │       └── revise_ad_script.py
│   ├── influencer_outreach/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       ├── find_influencers.py
│   │       └── draft_outreach.py
│   └── content_repurposer/
│       ├── SKILL.md
│       └── scripts/
│           └── repurpose.py
│
├── tools/                           # Shared infrastructure
│   ├── apify_client.py              # Apify actor wrapper
│   ├── llm_client.py                # Multi-provider LLM client
│   ├── kanban.py                    # JSON-backed kanban board
│   ├── memory.py                    # Persistent agent memory
│   └── telegram_bot.py             # Telegram gateway + interactive chat
│
├── kanban/
│   └── board.json                   # Live task board
│
├── data/                            # Raw scrape outputs
│   ├── ads/
│   ├── influencers/
│   └── memory.json
│
├── obsidian_vault/                  # Agent outputs (Markdown knowledge base)
│   ├── Competitors/
│   ├── Strategy/
│   ├── Ads/
│   ├── Outreach/
│   ├── Content/
│   └── HermesOutputs/
│
└── output/
    └── marketing_report.pdf         # Executive report
```

---

## Pipeline Stages (Detailed)

### Stage 1: Marketing Manager

1. **Competitor Discovery** — LLM suggests 5 competitors based on niche (cached 7 days in memory)
2. **Web Research** — Apify `rag-web-browser` scrapes each competitor's site, reviews, pricing pages
3. **LLM Analysis** — Extracts positioning, target audience, pricing model, dominant content channel
4. **Change Detection** — Compares current analysis hash against previous run; flags shifts
5. **Synthesis** — LLM identifies 3 exploitable gaps and 3 table-stakes threats
6. **Strategy Brief** — Generates audience segments, funnel priorities, positioning statements

### Stage 2: Ads Manager

1. **Meta Ads Scrape** — 5 niche keywords × Apify `solidcode/meta-ads-library-scraper`
2. **Date Filter** — Keeps only ads first seen in last 30 days
3. **Ranking** — "Still running = working" heuristic (longer active = more profitable)
4. **Concept Extraction** — LLM extracts pain point, hook, offer mechanism, CTA per ad
5. **Script Generation** — 3 variants from best concept (fear, aspiration, social proof angles)
6. **Scoring** — 5-dimension rubric (50 pts total): hook, pain, mechanism, proof, CTA
7. **Auto-Revision** — Scripts below 40/50 get rewritten based on scorer's specific feedback

### Stage 3: Influencer Outreach

1. **YouTube Search** — 5 trading-related queries via Apify channel scraper
2. **Data Extraction** — Channel name, URL, recent video titles, view counts
3. **Deduplication** — Unique channels across all search queries
4. **Memory Check** — Skip already-drafted influencers
5. **Dual-Format Drafting** — Email version (120 words) + DM version (60 words) per influencer
6. **Personalization** — References actual recent video titles when available

### Stage 4: Content Repurposer

1. **Memory Check** — Skip already-processed videos
2. **Transcript Fetch** — Apify `pintostudio/youtube-transcript-scraper`
3. **Insight Extraction** — LLM identifies 3-5 most quotable moments per video
4. **Multi-Platform Generation** — Per insight: X thread (5-7 tweets) + LinkedIn post + video script
5. **Content Calendar** — LLM generates weekly posting schedule with day/platform/time suggestions

### Final Steps

1. **PDF Report** — Executive summary + all outputs in a professional document
2. **Memory Log** — Run metadata saved for historical tracking
3. **Telegram Push** — Detailed status + PDF attachment sent to your chat

---

## Hermes Agent Integration

This project uses Hermes in two ways:

### 1. Skill Format (Native)
All agents follow the [agentskills.io](https://agentskills.io/specification) open standard:
- `SKILL.md` files with YAML frontmatter (name, description, version, metadata)
- Structured sections: When to Use, Procedure, Pitfalls, Verification
- `requires_toolsets: [terminal]` declares tool dependencies
- Scripts are bash commands Hermes executes through its terminal tool

### 2. Python Library (AIAgent)
`hermes_runner.py` uses Hermes as a Python library:
```python
from run_agent import AIAgent

agent = AIAgent(
    model="meta/llama-3.1-8b-instruct",
    base_url="https://integrate.api.nvidia.com/v1",
    ephemeral_system_prompt=skill_md_content,
    disabled_toolsets=["browser"],
)
result = agent.run_conversation(user_message=task)
```

The Hermes runtime reads SKILL.md as its system prompt, executes the procedure steps via terminal, and reports results back.

---

## LLM Rate Limit Strategy

```
429 received
    → Read Retry-After header (exact seconds to wait)
    → Sleep that duration (capped at 60s)
    → Rotate to next free model in pool
    → Retry (up to 7 attempts)
    → If all cloud attempts fail → fall back to local Ollama
```

Free model rotation pool:
- `nousresearch/hermes-3-llama-3.1-405b:free`
- `nvidia/nemotron-3-super-120b-a12b:free`
- `meta-llama/llama-3.3-70b-instruct:free`
- `google/gemma-4-31b-it:free`
- `qwen/qwen3-coder:free`

---

## Telegram Commands

| Command | What it does |
|---------|-------------|
| `/status` | Kanban board state + memory stats |
| `/score` | Ad script scorecard |
| `/competitors` | Competitive synthesis |
| `/outreach <handle>` | Generate outreach for a specific creator on-demand |
| `/changes` | What changed since last run |
| *Free text* | Ask anything — agent responds using all pipeline data as context |

---

## Requirements Mapping

| Assignment Requirement | Implementation |
|----------------------|----------------|
| Python | Entire project |
| Hermes + Obsidian | `hermes_runner.py` + `skills/*/SKILL.md` + `hermes/config.yaml` + `obsidian_vault/` |
| OpenRouter or NVIDIA build | `tools/llm_client.py` — both supported, swappable via env var |
| Apify for data scraping | `tools/apify_client.py` — Meta Ads, YouTube, web research |
| Marketing Manager Agent | Competitor research + strategy brief + change detection |
| Ads Manager Agent | Scrape → extract → generate 3 variants → score → auto-revise |
| Influencer Outreach Agent | Find 70+ channels → draft personalized email + DM |
| "Your Idea" Agent | Content Repurposer — videos → X threads, LinkedIn, video scripts, calendar |
| Kanban | `kanban/board.json` — cards move Backlog → In Progress → Review → Done |
| Loops + Skills | `main.py` orchestration loop + 4 Hermes skills |
| Telegram | Push notifications + interactive chat bot |

---

## Output Samples

After a full run, the system produces:

- **5+ competitor analysis notes** with positioning, pricing, strategy
- **1 competitive synthesis** identifying gaps and threats
- **1 strategy brief** with audience segments and positioning statements
- **274 raw Meta ads** scraped and filtered
- **9 ad concepts** with extracted marketing psychology
- **3+ ad script variants** scored and ranked
- **70+ influencer dossiers** with channel data
- **15+ personalized outreach drafts** (email + DM format)
- **5 repurposed content pieces** (X thread + LinkedIn + video script each)
- **1 content calendar** with weekly posting schedule
- **1 PDF executive report**
- **1 kanban board** tracking all task states

---

## Submission Deliverables

- [x] GitHub repository: https://github.com/Mat-rixMJ/Agent-collector
- [x] Apify token: provided in submission email
- [x] Video: screen recording of kanban board + pipeline running
- [x] .md outputs: `obsidian_vault/` folder (all agent outputs as Markdown)
- [x] PDF report: `output/marketing_report.pdf`

---

## License

Built for the CrowdWisdomTrading Marketing Agent Intern assessment.
