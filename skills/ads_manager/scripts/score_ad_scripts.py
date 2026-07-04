"""Stage 4: Score and rank generated ad scripts using direct-response criteria.

Evaluates each ad script against proven copywriting metrics and recommends
which to produce first. This closes the loop between "creative generation"
and "creative prioritization" — the kind of thing a senior media buyer does.

Usage: python -m skills.ads_manager.scripts.score_ad_scripts
"""
import json
import os
from pathlib import Path

from tools.llm_client import ask

VAULT = Path(os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian_vault")) / "Ads"
SCORES_PATH = VAULT / "_scorecard.md"

SCORING_PROMPT = """You are a senior direct-response ad buyer who has spent $50M+ on paid social.
Score this ad script on these 5 criteria (1-10 each):

1. HOOK STRENGTH: Does the first line stop the scroll? Is it specific, not generic?
2. PAIN CLARITY: Is the problem named concretely (not vague "struggle" language)?
3. MECHANISM: Does it explain *why* this solution works (not just *what* it is)?
4. PROOF ELEMENTS: Are there specific numbers, credentials, or social proof?
5. CTA URGENCY: Is there a reason to act now vs. later?

After scoring, give:
- TOTAL: sum of all 5 scores (out of 50)
- VERDICT: "Ready to shoot" / "Needs revision" / "Kill it"
- TOP IMPROVEMENT: The single change that would most improve performance

Output as clean JSON with keys: hook, pain, mechanism, proof, cta, total, verdict, top_improvement
No markdown, just the JSON object."""


def score_script(script_text: str) -> dict:
    raw = ask(SCORING_PROMPT, script_text)
    try:
        # Try to extract JSON from response
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
    except json.JSONDecodeError:
        pass
    return {"total": 0, "verdict": "Parse error", "raw": raw}


def main() -> None:
    scripts = list(VAULT.glob("*.md"))
    scripts = [f for f in scripts if not f.name.startswith("_")]

    if not scripts:
        print("No ad scripts found in obsidian_vault/Ads/")
        return

    results = []
    for script_path in scripts:
        print(f"Scoring: {script_path.name}")
        content = script_path.read_text(encoding="utf-8")
        score = score_script(content)
        score["file"] = script_path.name
        results.append(score)

    # Sort by total score descending
    results.sort(key=lambda x: x.get("total", 0), reverse=True)

    # Write scorecard
    lines = ["# Ad Script Scorecard\n"]
    lines.append("Ranked by total score (out of 50). Higher = more likely to convert.\n")
    lines.append("| Rank | Script | Total | Verdict |")
    lines.append("|------|--------|-------|---------|")
    for i, r in enumerate(results, 1):
        lines.append(f"| {i} | {r['file'][:40]} | {r.get('total', '?')}/50 | {r.get('verdict', '?')} |")

    lines.append("\n---\n")
    lines.append("## Detailed Scores\n")

    for i, r in enumerate(results, 1):
        lines.append(f"### #{i}: {r['file']}")
        lines.append(f"- Hook Strength: {r.get('hook', '?')}/10")
        lines.append(f"- Pain Clarity: {r.get('pain', '?')}/10")
        lines.append(f"- Mechanism: {r.get('mechanism', '?')}/10")
        lines.append(f"- Proof Elements: {r.get('proof', '?')}/10")
        lines.append(f"- CTA Urgency: {r.get('cta', '?')}/10")
        lines.append(f"- **Total: {r.get('total', '?')}/50**")
        lines.append(f"- **Verdict: {r.get('verdict', '?')}**")
        lines.append(f"- Top Improvement: {r.get('top_improvement', 'N/A')}")
        lines.append("")

    SCORES_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nScorecard written to {SCORES_PATH}")
    print(f"Top script: {results[0]['file']} ({results[0].get('total', '?')}/50)")


if __name__ == "__main__":
    main()
