# CrowdWisdomTrading Marketing Agent Intern Assessment

This document contains the original requirements, submission deliverables, and mapping for the CrowdWisdomTrading Marketing Agent Intern take-home assessment.

## Requirements Mapping

| Assignment Requirement | Implementation |
|----------------------|----------------|
| Python | Entire project codebase |
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

## Submission Deliverables

- **GitHub Repository:** https://github.com/Mat-rixMJ/Agent-collector
- **Apify Token:** Provided in the submission email.
- **Video:** Screen recording of the Kanban board and pipeline execution.
- **Markdown Outputs:** The generated `obsidian_vault/` folder containing all compiled Markdown files.
- **PDF Report:** The final output file `output/marketing_report.pdf`.

## Original Assessment Context
This multi-agent system was originally built to automate the end-to-end competitive intelligence, creative generation, influencer research, and content repurposing processes for CrowdWisdomTrading's launch.
