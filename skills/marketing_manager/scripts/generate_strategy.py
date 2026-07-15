"""Generate a marketing strategy brief from competitor research + product data.

Reads the competitor synthesis, combines with CrowdWisdomTrading's positioning,
and produces a focused strategy brief a marketing lead would actually use.

Usage: python -m skills.marketing_manager.scripts.generate_strategy
"""
import os
from pathlib import Path

from tools.llm_client import ask

VAULT = Path(os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian_vault"))
STRATEGY_DIR = VAULT / "Strategy"
STRATEGY_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PROMPT = """You are a senior marketing strategist for a retail trading education platform.
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
Include a standard compliance reminder stating that all marketing materials (ad copy, scripts, influencer briefs) for financial services/retail trading must undergo legal compliance review (e.g., SEC, FCA, or SEBI rules depending on jurisdiction) before deployment. Mention that clear disclaimers regarding the risk of trading are required.

Be specific and actionable. Reference competitors by name where relevant."""


def main() -> None:
    synth_path = VAULT / "Competitors" / "_synthesis.md"
    if not synth_path.exists():
        print("No competitor synthesis found — run competitor_research.py first.")
        return

    synthesis = synth_path.read_text(encoding="utf-8")

    our_product = os.getenv("NICHE", "retail trading, market commentary")
    
    profile_path = Path("data/company_profile.json")
    if profile_path.exists():
        try:
            import json
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            product_context = json.dumps(profile, indent=2)
        except Exception:
            product_context = f"Niche: {our_product}"
    else:
        product_context = f"Niche: {our_product}"

    brief = ask(
        SYSTEM_PROMPT,
        f"Competitor Research:\n{synthesis[:1500]}\n\nOur Product:\n{product_context}",
        max_tokens=1000,
    )

    output = f"# Marketing Strategy Brief\n\n*Auto-generated from competitor research*\n\n{brief}\n"
    (STRATEGY_DIR / "brief.md").write_text(output, encoding="utf-8")
    print(f"Strategy brief written to {STRATEGY_DIR / 'brief.md'}")


if __name__ == "__main__":
    main()
