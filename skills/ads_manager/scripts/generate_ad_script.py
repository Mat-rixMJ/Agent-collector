"""Stage 3: pick the concept most relevant to CrowdWisdomTrading's actual
product and write an original ad script grounded in that pattern.
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

# Fill in with CrowdWisdomTrading's real value props / proof points before running for real.
OUR_DATA = """
CrowdWisdomTrading provides institutional-grade market commentary and trade
alerts for retail traders. Differentiators: analyst team with sell-side
background, same-day actionable commentary (not lagging recaps), transparent
track record.
"""

SYSTEM_PROMPT = (
    "You are a senior direct-response copywriter. You will be given (a) a proven "
    "ad concept pattern (pain point / hook / offer mechanism / CTA) observed in "
    "the market, and (b) our own product's real value props. Write an ORIGINAL "
    "30-45 second video ad script for our product that uses the same psychological "
    "pattern but our own claims, proof points, and voice — never reuse the "
    "competitor's specific copy or claims. Structure: HOOK (first 3 seconds), "
    "BODY (problem -> our mechanism -> proof), CTA. Also suggest a visual direction "
    "for each section in [brackets]."
)


def pick_best_concept(concepts: list[dict]) -> dict:
    # Simple relevance heuristic: prefer concepts whose pain point mentions
    # signals/education/analysis — swap for an LLM ranking pass if you want more rigor.
    keywords = ["signal", "analysis", "commentary", "education", "learn", "strategy"]
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
    script = ask(
        SYSTEM_PROMPT,
        f"Proven concept pattern:\n{json.dumps(best, indent=2)}\n\nOur product:\n{OUR_DATA}",
    )

    slug = re.sub(r"[^a-z0-9]+", "-", best.get("pain_point", "concept")[:40].lower()).strip("-")
    out_path = VAULT / f"{date.today().isoformat()}_{slug}.md"
    out_path.write_text(
        f"# Ad Script — {date.today().isoformat()}\n\n"
        f"**Based on concept from:** {best.get('advertiser', 'unknown')}\n\n"
        f"## Source concept\n```json\n{json.dumps(best, indent=2)}\n```\n\n"
        f"## Script\n{script}\n",
        encoding="utf-8",
    )
    print(f"Ad script written to {out_path}")


if __name__ == "__main__":
    main()
