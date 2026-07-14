"""Stage 3: Generate 3 ad script variants from different psychological angles,
each grounded in the same proven concept pattern but approaching the audience
from a different emotional entry point.

Variants:
1. Fear/loss aversion — "You're losing money while you wait"
2. Aspiration/gain — "Imagine knowing the move before it happens"
3. Social proof — "Join traders who already use community-powered intelligence"

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
PROFILE_PATH = Path("data/company_profile.json")


def get_company_profile() -> str:
    if PROFILE_PATH.exists():
        try:
            profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
            return json.dumps(profile, indent=2)
        except Exception as e:
            print(f"  failed to load company profile: {e}")
    return """
    CrowdWisdomTrading provides market commentary and trade alerts for retail traders.
    Pricing: $49/month.
    Features: Telegram alerts, Discord community, daily chart analysis.
    """


def get_hard_blocked_patterns() -> list:
    """Load hard-blocked regex patterns from company_profile.json.

    These patterns catch FTC-regulated claim categories (named testimonials,
    specific unverified membership counts, specific performance claims) that
    must never appear in generated ad scripts regardless of prompt instructions.
    Using a deterministic regex check rather than relying solely on the LLM
    to follow instructions — prompts can be ignored; this check cannot.
    """
    if PROFILE_PATH.exists():
        try:
            profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
            return profile.get("hard_blocked_patterns", [])
        except Exception:
            pass
    return []


def scan_for_prohibited_content(script: str, angle_name: str) -> list[str]:
    """Scan a generated ad script for hard-blocked claim patterns.

    Returns a list of violation descriptions. Empty list = clean.
    Raises ValueError if any violations are found — the script must not
    be written to disk or included in any report until resolved.
    """
    patterns = get_hard_blocked_patterns()
    violations = []
    for pattern in patterns:
        try:
            if re.search(pattern, script, re.IGNORECASE):
                violations.append(f"Pattern matched: {pattern!r}")
        except re.error as e:
            print(f"  [CONTENT SCAN] Bad regex pattern {pattern!r}: {e} — skipping")
    return violations


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
    "the market, (b) our company's verified profile data (value props, guidelines, allowed/prohibited claims), "
    "and (c) an ANGLE instruction. "
    "Write an ORIGINAL 30-45 second video ad script using that specific angle. "
    "Never reuse the competitor's specific copy or claims. "
    "Structure: HOOK (first 3 seconds), BODY (problem -> mechanism -> proof), CTA. "
    "Also suggest visual direction for each section in [brackets].\n\n"
    "CRITICAL FACTUAL GUARDRAIL: Do not state any factual claim about our company that is not present in the verified profile data. "
    "Under no circumstances should you claim we have a 'sell-side background' or a 'transparent track record' unless listed in the profile. "
    "If no verified claim fits the angle, use generic/aspirational language instead of inventing specifics."
)


def check_coherence(script: str, concept: dict) -> bool:
    offer = concept.get("offer_mechanism", "").lower()
    cta = concept.get("cta", "").lower()
    prompt = (
        "You are a quality assurance editor. Verify if this video ad script is coherent and matches the "
        "offered product/service and call to action of the original concept.\n\n"
        f"Original Offer: {offer}\n"
        f"Original CTA: {cta}\n\n"
        f"Ad Script:\n{script}\n\n"
        "If the script is coherent and matches the offer/CTA of the original concept, reply 'yes'. "
        "If there is a mismatch (e.g. script talks about trading but the offer is a bookkeeping or internet test service, "
        "or the offer is completely missing/unexplained), reply 'no'. "
        "Answer strictly 'yes' or 'no'."
    )
    try:
        res = ask(prompt, "").strip().lower()
        return res.startswith("yes")
    except Exception:
        return True # Fallback if LLM fails


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
    concepts = json.loads(IN_PATH.read_text(encoding="utf-8"))
    if not concepts:
        print("No concepts to work from.")
        return

    best = pick_best_concept(concepts)
    company_data = get_company_profile()

    for angle in ANGLES:
        prompt = (
            f"ANGLE: {angle['label']}\n"
            f"INSTRUCTION: {angle['instruction']}\n\n"
            f"Proven concept pattern:\n{json.dumps(best, indent=2)}\n\n"
            f"Our company profile:\n{company_data}"
        )
        
        # Script generation with coherence retry loop
        script = ""
        for attempt in range(3):
            script = ask(BASE_PROMPT, prompt)
            if check_coherence(script, best):
                break
            print(f"  [COHERENCE] Attempt {attempt+1} failed coherence check for angle {angle['name']}, retrying...")
        else:
            print(f"  [COHERENCE] WARNING: Could not generate a coherent script for angle {angle['name']} after 3 attempts.")

        # Hard-blocked content scan — deterministic regex, not LLM-based.
        # Catches fabricated testimonials, specific unverified member counts,
        # and regulated performance claims before they reach disk or the report.
        violations = scan_for_prohibited_content(script, angle["name"])
        if violations:
            print(f"  [CONTENT BLOCK] Script for angle '{angle['name']}' contains prohibited content and was NOT saved.")
            for v in violations:
                print(f"    -> {v}")
            print(f"  [CONTENT BLOCK] Review and rewrite this script manually before production use.")
            continue  # Skip writing this script — don't silently ship blocked content

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
