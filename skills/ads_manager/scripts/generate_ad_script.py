"""Stage 3: Generate 3 ad script variants from different psychological angles,
each grounded in the same proven concept pattern but approaching the audience
from a different emotional entry point.

Variants:
1. Fear/loss aversion — "You're losing money while you wait"
2. Aspiration/gain — "Imagine knowing the move before it happens"
3. Social proof — "Join 10,000+ traders who already..."

Usage: python -m skills.ads_manager.scripts.generate_ad_script
"""
import json
import os
import re
from datetime import date
from pathlib import Path

from tools.llm_client import ask

IN_PATH = Path("data/ads/ad_concepts.json")
VAULT = Path(os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian_vault")) / "Ads"
VAULT.mkdir(parents=True, exist_ok=True)

OUR_DATA = """
CrowdWisdomTrading provides institutional-grade market commentary and trade
alerts for retail traders. Differentiators: analyst team with sell-side
background, same-day actionable commentary (not lagging recaps), transparent
track record.
"""

ANGLES = [
    {
        "name": "fear",
        "label": "Fear / Loss Aversion",
        "instruction": (
            "Use FEAR and LOSS AVERSION as the primary emotional lever. "
            "Open with what the viewer is losing by NOT having this solution. "
            "Make the cost of inaction feel immediate and concrete."
        ),
    },
    {
        "name": "aspiration",
        "label": "Aspiration / Gain",
        "instruction": (
            "Use ASPIRATION and DESIRE as the primary emotional lever. "
            "Open with the end-state the viewer wants — paint the picture of "
            "what life looks like AFTER they have this solution working for them."
        ),
    },
    {
        "name": "social_proof",
        "label": "Social Proof",
        "instruction": (
            "Use SOCIAL PROOF as the primary emotional lever. "
            "Open with evidence that other traders like them are already benefiting. "
            "Use phrases like 'thousands of traders', 'our analyst community', etc."
        ),
    },
]

BASE_PROMPT = (
    "You are a senior direct-response copywriter. You will be given (a) a proven "
    "ad concept pattern (pain point / hook / offer mechanism / CTA) observed in "
    "the market, (b) our own product's real value props, and (c) an ANGLE instruction. "
    "Write an ORIGINAL 30-45 second video ad script using that specific angle. "
    "Never reuse the competitor's specific copy or claims. "
    "Structure: HOOK (first 3 seconds), BODY (problem -> mechanism -> proof), CTA. "
    "Also suggest visual direction for each section in [brackets]."
)


def pick_best_concept(concepts: list[dict]) -> dict:
    keywords = ["signal", "analysis", "commentary", "education", "learn", "strategy", "trading"]
    scored = sorted(
        concepts,
        key=lambda c: sum(k in (c.get("pain_point", "") + c.get("offer_mechanism", "")).lower() for k in keywords),
        reverse=True,
    )
    return scored[0] if scored else {}


def main() -> None:
    if not IN_PATH.exists():
        print(f"{IN_PATH} not found — run extract_ad_concepts.py first.")
        return
    concepts = json.loads(IN_PATH.read_text())
    if not concepts:
        print("No concepts to work from.")
        return

    best = pick_best_concept(concepts)

    for angle in ANGLES:
        prompt = (
            f"ANGLE: {angle['label']}\n"
            f"INSTRUCTION: {angle['instruction']}\n\n"
            f"Proven concept pattern:\n{json.dumps(best, indent=2)}\n\n"
            f"Our product:\n{OUR_DATA}"
        )
        script = ask(BASE_PROMPT, prompt)

        slug = re.sub(r"[^a-z0-9]+", "-", best.get("pain_point", "concept")[:30].lower()).strip("-")
        out_path = VAULT / f"{date.today().isoformat()}_{slug}_{angle['name']}.md"
        out_path.write_text(
            f"# Ad Script — {angle['label']}\n\n"
            f"**Date:** {date.today().isoformat()}  \n"
            f"**Angle:** {angle['label']}  \n"
            f"**Based on concept from:** {best.get('advertiser', 'unknown')}\n\n"
            f"## Source concept\n```json\n{json.dumps(best, indent=2)}\n```\n\n"
            f"## Script\n{script}\n",
            encoding="utf-8",
        )
        print(f"  [{angle['name']}] Written to {out_path.name}")

    print(f"3 ad script variants generated in {VAULT}")


if __name__ == "__main__":
    main()
