"""Competitor research: scrapes each competitor via Apify's rag-web-browser,
summarizes positioning/pricing/content strategy via LLM, writes Obsidian notes.

Usage: python -m skills.marketing_manager.scripts.competitor_research
"""
import json
import os
from pathlib import Path

from tools.apify_client import rag_web_search
from tools.llm_client import ask

VAULT = Path(os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian_vault")) / "Competitors"
VAULT.mkdir(parents=True, exist_ok=True)

# Edit this list — direct competitors to crowdwisdomtrading.com's niche
COMPETITORS = [
    "Warrior Trading",
    "Bullish Bears",
    "The Trading Channel",
    "Investors Underground",
    "FundedNext",  # prop-firm angle overlap
]

SYSTEM_PROMPT = (
    "You are a marketing analyst. Given raw web search snippets about a trading-"
    "education/signals competitor, extract: positioning (1 sentence), target "
    "audience, pricing model, and their dominant content format/channel. "
    "If the snippets don't contain enough info for a field, write 'unclear from "
    "available data' — never invent numbers. Output clean Markdown with headers."
)


def research_competitor(name: str) -> str:
    results = rag_web_search(f"{name} trading education pricing reviews", max_results=4)
    raw_text = "\n\n".join(
        f"Source: {r.get('url', '')}\n{r.get('markdown', r.get('text', ''))[:2000]}" for r in results
    )
    summary = ask(SYSTEM_PROMPT, f"Competitor: {name}\n\nRaw research:\n{raw_text}")
    note = f"# {name}\n\n{summary}\n\n---\n*Sources: {len(results)} pages via apify/rag-web-browser*\n"
    (VAULT / f"{name.replace(' ', '_')}.md").write_text(note, encoding="utf-8")
    return summary


def synthesize(summaries: dict[str, str]) -> None:
    joined = "\n\n".join(f"## {name}\n{s}" for name, s in summaries.items())
    synthesis = ask(
        "Synthesize these competitor summaries into: (1) 3 gaps crowdwisdomtrading.com "
        "could exploit, (2) 3 threats/table-stakes features to match. Be specific, "
        "reference the competitors by name.",
        joined,
    )
    (VAULT / "_synthesis.md").write_text(f"# Competitive Synthesis\n\n{synthesis}\n", encoding="utf-8")


def main() -> None:
    summaries = {}
    for name in COMPETITORS:
        print(f"Researching {name}...")
        try:
            summaries[name] = research_competitor(name)
        except Exception as e:
            print(f"  failed: {e}")
    if summaries:
        synthesize(summaries)
    print(f"Done. Notes written to {VAULT}")


if __name__ == "__main__":
    main()
