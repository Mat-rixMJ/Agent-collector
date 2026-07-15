# Autonomous Multi-Agent Marketing & Intelligence Pipeline

[![CI Pipeline](https://github.com/Mat-rixMJ/Agent-collector/actions/workflows/ci.yml/badge.svg)](https://github.com/Mat-rixMJ/Agent-collector/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

An autonomous, multi-agent intelligence and campaign distribution engine designed to execute end-to-end competitive research, Meta ad library scraping, script writing, video scoring, cold outreach, and multi-format content distribution.

---

## ⚡ See It in Action (No Setup Required)

* **Live Interactive Dashboard:** [View Live Streamlit Dashboard](https://marketing-agents-dashboard.streamlit.app) *(Visualizes the current Kanban states, scorecard, competitor comparisons, and outreach drafts in your browser).*
* **Zero-Setup Sample Outputs:** Explore the raw agent outputs produced in a full pipeline run:
  * 📋 [Visual Kanban Task Board](file:///sample_output/kanban/board.json)
  * 📈 [Competitor Intelligence Briefs](file:///sample_output/obsidian_vault/Competitors/) & [Strategy Brief](file:///sample_output/obsidian_vault/Strategy/brief.md)
  * 🎬 [Ad Script Scorecard](file:///sample_output/obsidian_vault/Ads/_scorecard.md) & [Generated Script Variants](file:///sample_output/obsidian_vault/Ads/)
  * ✉️ [Influencer Discovery & Outreach Drafts](file:///sample_output/obsidian_vault/Outreach/)
  * 📅 [Social Media Content Calendar](file:///sample_output/obsidian_vault/Content/_calendar.md)
  * 📄 [Generated PDF Executive Report](file:///sample_output/output/marketing_report.pdf)

---

## 📸 Demo Walkthrough

### Terminal Execution (`python main.py --demo`)
![Terminal Run Demo](https://raw.githubusercontent.com/Mat-rixMJ/Agent-collector/main/docs/terminal_demo.gif)

### Interactive Telegram Bot & Polished Report
| Telegram Status Webhook | Generated PDF Cover Page | FPDF pricing chart |
| :---: | :---: | :---: |
| ![Telegram Bot](https://raw.githubusercontent.com/Mat-rixMJ/Agent-collector/main/docs/telegram_screenshot.png) | ![PDF Cover](https://raw.githubusercontent.com/Mat-rixMJ/Agent-collector/main/docs/pdf_cover_screenshot.png) | ![PDF Chart](https://raw.githubusercontent.com/Mat-rixMJ/Agent-collector/main/docs/pdf_chart_screenshot.png) |

---

## 🛠️ What it Produces in a Single Run

1. **Competitor Discovery & Synthesis:** Auto-scrapes pricing and positioning details for the top 5 competitors in a retail trading niche, identifying exploitable gaps.
2. **Meta Ads Analysis & Concept Mining:** Scrapes the Meta Ads Library, filters for niche relevance, and extracts direct-response hooks and offers.
3. **Ad Script Writing & Priority Scoring:** Drafts 3 video ad script variants (Loss Aversion, Gain, Social Proof), grades them on a 50-point rubric, and automatically rewrites weak scripts.
4. **Influencer Outreach Campaigns:** Finds YouTube creators in the niche and drafts personalized email and DM partnership pitches referencing their recent video titles.
5. **Content Repurposing & Distribution Calendar:** Transcribes discovered videos and structures them into X threads, LinkedIn posts, and short video scripts.
6. **Polished Stakeholder PDF:** Compiles all intelligence into a branded executive report with custom positioning matrices and charts.

---

## 📐 System Architecture

The pipeline consists of 4 specialized agents coordinated by a poll-and-dispatch orchestrator running over a JSON-backed Kanban board.

```mermaid
graph TD
    Orch[main.py Orchestrator] --> KB[Kanban Board JSON]
    Orch --> M1[Marketing Manager Agent]
    Orch --> M2[Ads Manager Agent]
    Orch --> M3[Influencer Outreach Agent]
    Orch --> M4[Content Repurposer Agent]
    
    M1 & M2 & M3 & M4 --> SharedTools[Shared Tool Layer]
    
    SharedTools --> Apify[Apify Scraping SDK]
    SharedTools --> LLM[LLM Abstraction Layer]
    SharedTools --> Mem[Persistent Memory System]
    SharedTools --> Tele[Telegram Bot Gateway]
    
    LLM --> NV[NVIDIA API]
    LLM --> OR[OpenRouter API]
    LLM --> OL[Local Ollama]
```

---

## 🌟 Key Differentiators

### 🧠 Persistent Agent Memory
Prevents redundant work by caching state across runs. Competitors are tracked for positioning changes, Meta ads are deduplicated, cold outreach prospects are marked "drafted", and processed YouTube source videos are skipped. Subsequent runs execute in a fraction of the time.

### 🔄 Closed-Loop Creative Optimization
Ad scripts are evaluated against a strict 50-point copywriting rubric (evaluating hook strength, pain clarity, mechanism explanation, proof elements, and CTA urgency). Any script scoring below 40/50 is fed back to the copywriter agent along with the specific improvement notes and automatically rewritten.

### 🛡️ Production-Grade Error Handling & Failovers
Our LLM client is resilient to API outages and rate limits. On receiving a HTTP `429 (Too Many Requests)`, it reads the `Retry-After` header, backs off, rotates to a different free model, and retries. If all cloud providers fail, it automatically falls back to a local Ollama model.

### 💬 Conversational Telegram Bot Gateway
Enables interactive control over the pipeline. Interact with the active memory in real-time using custom slash commands (`/status`, `/score`, `/competitors`, `/changes`) or chat with the agent in free-text.

---

## 🚀 Quick Start

### 1. Zero-Setup Demo Mode (Recommended)
You can run the full 4-agent pipeline end-to-end **without requiring any API keys or scraper tokens**:
```bash
# Clone the repository
git clone https://github.com/Mat-rixMJ/Agent-collector.git
cd Agent-collector

# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run in offline demo mode (completes in ~10 seconds)
python main.py --demo
```
This runs the full pipeline scripts, writes outputs to `obsidian_vault/`, and generates `output/marketing_report.pdf` exactly like a live run, using deterministic mock responses and local fixtures.

---

### 2. Live Production Mode
To run the live scapers and connect to cloud LLMs:

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in your keys:
   * `APIFY_TOKEN` (from [Apify](https://console.apify.com))
   * `LLM_PROVIDER` (choose `nvidia` or `openrouter`)
   * `NVIDIA_API_KEY` or `OPENROUTER_API_KEY`
   * `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID` (optional, for webhooks)

3. Run the live pipeline:
   ```bash
   python main.py --fresh
   ```

---

## 🧪 Testing

The repository includes a comprehensive pytest suite covering the Kanban board, agent memory layer, script scoring parser, and LLM fallback logic.

```bash
# Run the test suite
pytest
```

---

## 📐 What I'd Do Differently at Scale

If deploying this system into a high-throughput production environment:
1. **Queue-Based Orchestration:** Replace the local poll-and-dispatch JSON Kanban loop with a message broker like RabbitMQ or Celery to handle parallel agent executions and distributed tasks.
2. **Relational Database Storage:** Migrate the local `memory.json` file to a database like PostgreSQL with Redis caching for faster querying, transaction safety, and persistent analytics.
3. **Async IO & Batching:** Rewrite scraper invocations and LLM requests using `asyncio` or `httpx` to run requests concurrently, reducing overall execution duration.
4. **Structured JSON LLM Outputs:** Transition from raw text parsing to strict structured outputs utilizing libraries like Pydantic or Instructor to guarantee JSON schemas and eliminate parser failures.
5. **Real-time Observability:** Integrate tracing tools like LangSmith or Phoenix to monitor agent steps, prompt effectiveness, latency, and tokens spent.

---

## 📜 License
This project is licensed under the permissive MIT License. See [LICENSE](file:///LICENSE) for details.

*For original intern assessment deliverables and requirements mapping, see [ASSESSMENT.md](file:///ASSESSMENT.md).*
