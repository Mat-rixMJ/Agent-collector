"""Generate a marketing strategy brief from competitor research + product data.

Reads the competitor synthesis, combines with the target company's positioning,
and produces a focused strategy brief a marketing lead would actually use.

Usage: python -m skills.marketing_manager.scripts.generate_strategy
"""
import os
from pathlib import Path

from tools.llm_client import ask
from tools import config_manager

VAULT = Path(os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian_vault"))
STRATEGY_DIR = VAULT / "Strategy"
STRATEGY_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """You are a senior marketing strategist for a {niche} platform.
Given competitor research and product info, produce a focused strategy brief.

Structure your output exactly as:
## Target Audience Segments
(3 segments with demographics + psychographics)

## Funnel Priorities
- TOFU (awareness): what content/channels to focus on
- MOFU (consideration): what to offer
- BOFU (conversion): what closes the deal

## This Week's Key Message
(One sentence that all content should reinforce)

## Positioning Statements
(3 statements differentiating us from specific competitors)

## Recommended Actions with Resource Estimates
Provide 5 prioritized action items for the team this week. For each action item, include:
- Resource Level: (Low / Moderate / High effort/budget)
- Timeline: (e.g. 1-2 weeks)
- Expected Impact: (Low / Medium / High)

## Compliance and Regulatory Notice
Include a standard compliance reminder stating that all marketing materials (ad copy, scripts, influencer briefs) must undergo legal compliance review before deployment. Tailor disclaimers to the specific industry and jurisdiction of the company.

IMPORTANT: Use the company_name from the product context EXACTLY as provided. Do not modify or misspell it.

Be specific and actionable. Reference competitors by name where relevant."""


def main() -> None:
    synth_path = VAULT / "Competitors" / "_synthesis.md"
    if not synth_path.exists():
        print("No competitor synthesis found — run competitor_research.py first.")
        return

    synthesis = synth_path.read_text(encoding="utf-8")

    config = config_manager.load_config()
    our_product = config.get("niche", "general topics")
    
    # We serialize the entire config minus some noisy LLM queries as the product context
    context_dict = {
        "company_name": config.get("company_name"),
        "target_site": config.get("target_site"),
        "verified_claims": config.get("verified_claims")
    }
    import json
    product_context = json.dumps(context_dict, indent=2)

    brief = ask(
        SYSTEM_PROMPT.format(niche=our_product),
        f"Competitor Research:\n{synthesis[:1500]}\n\nOur Product:\n{product_context}",
        max_tokens=1000,
    )

    output = f"# Marketing Strategy Brief\n\n*Auto-generated from competitor research*\n\n{brief}\n"
    (STRATEGY_DIR / "brief.md").write_text(output, encoding="utf-8")
    print(f"Strategy brief written to {STRATEGY_DIR / 'brief.md'}")


if __name__ == "__main__":
    main()
