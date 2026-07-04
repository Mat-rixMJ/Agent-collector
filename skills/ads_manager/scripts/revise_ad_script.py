"""Stage 5: Auto-revise the top script if it scored below threshold.

Reads the scorecard, finds improvement suggestions, and rewrites the
weakest sections. This creates a feedback loop between scoring and generation.

Usage: python -m skills.ads_manager.scripts.revise_ad_script
"""
import os
import re
from pathlib import Path

from tools.llm_client import ask

VAULT = Path(os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian_vault")) / "Ads"
SCORECARD = VAULT / "_scorecard.md"
THRESHOLD = 40  # only revise if below this score


def parse_scorecard() -> list[dict]:
    """Extract scores from the scorecard markdown."""
    if not SCORECARD.exists():
        return []
    text = SCORECARD.read_text(encoding="utf-8")
    results = []
    current = {}
    for line in text.split("\n"):
        if line.startswith("### #"):
            if current:
                results.append(current)
            filename = line.split(": ", 1)[1] if ": " in line else ""
            current = {"file": filename, "total": 0, "improvement": ""}
        elif "**Total:" in line:
            match = re.search(r"(\d+)/50", line)
            if match:
                current["total"] = int(match.group(1))
        elif "Top Improvement:" in line:
            current["improvement"] = line.split("Top Improvement:", 1)[1].strip()
    if current:
        results.append(current)
    return results


REVISION_PROMPT = (
    "You are a senior direct-response copywriter revising an ad script. "
    "The script was scored by a media buyer. Apply their specific improvement "
    "suggestion to rewrite the script. Keep the same structure (HOOK/BODY/CTA) "
    "and angle, but make the specific fix they requested. Output the full revised script."
)


def main() -> None:
    scores = parse_scorecard()
    if not scores:
        print("No scorecard found — run score_ad_scripts.py first.")
        return

    # Find scripts that need revision (below threshold)
    needs_revision = [s for s in scores if s["total"] < THRESHOLD and s["improvement"]]

    if not needs_revision:
        print(f"All scripts score >= {THRESHOLD}/50. No revision needed.")
        return

    for entry in needs_revision[:2]:  # Limit to top 2 revisions per run
        script_path = VAULT / entry["file"]
        if not script_path.exists():
            continue

        print(f"Revising: {entry['file']} (scored {entry['total']}/50)")
        original = script_path.read_text(encoding="utf-8")
        improvement = entry["improvement"]

        revised = ask(
            REVISION_PROMPT,
            f"Original script:\n{original}\n\n"
            f"Improvement to apply: {improvement}",
        )

        revised_path = script_path.with_stem(script_path.stem + "_revised")
        revised_path.write_text(
            f"# REVISED Ad Script\n\n"
            f"**Original:** {entry['file']}  \n"
            f"**Original score:** {entry['total']}/50  \n"
            f"**Applied fix:** {improvement}\n\n"
            f"## Revised Script\n{revised}\n",
            encoding="utf-8",
        )
        print(f"  Revised version saved: {revised_path.name}")

    print("Auto-revision complete.")


if __name__ == "__main__":
    main()
