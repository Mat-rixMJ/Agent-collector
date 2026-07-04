"""Hermes Agent integration — runs skills through the actual Hermes AIAgent runtime.

This script invokes each marketing agent skill through Hermes' AIAgent library,
giving the agent access to its full tool suite (web, terminal, file ops) while
using our SKILL.md files as the system prompt.

Usage: python hermes_runner.py
"""
import sys
import os
from pathlib import Path

# Ensure Hermes' own tools module resolves before our local tools/ package
site_packages = next(
    (p for p in sys.path if "site-packages" in p), None
)
if site_packages:
    sys.path.insert(0, site_packages)

# Bypass Hermes' minimum context check (our model has 64K ctx configured via Ollama)
import agent.agent_init as _ai
_ai.MINIMUM_CONTEXT_LENGTH = 0

from run_agent import AIAgent  # noqa: E402

# Restore normal path for our modules
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(override=True)


SKILLS_DIR = Path("skills")
VAULT = Path(os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian_vault"))

# Map each skill to what we want Hermes to do
SKILL_TASKS = {
    "marketing_manager": (
        "Run competitor research for crowdwisdomtrading.com against these 5 competitors: "
        "Warrior Trading, Bullish Bears, The Trading Channel, Investors Underground, FundedNext. "
        "For each, find their positioning, pricing, and content strategy. "
        "Then write a strategy brief with target audience segments and positioning statements."
    ),
    "ads_manager": (
        "Search the Meta Ads Library for active ads in the retail trading / prop firm niche. "
        "Extract the pain points, hooks, and CTAs from the best-performing ads. "
        "Then write 3 original ad scripts for CrowdWisdomTrading using different angles: "
        "fear/loss, aspiration/gain, and social proof."
    ),
    "influencer_outreach": (
        "Find retail-trading YouTube creators with large audiences. "
        "Save their channel info. Then draft personalized cold outreach messages "
        "asking their honest opinion about crowdwisdomtrading.com."
    ),
    "content_repurposer": (
        "Take these YouTube video URLs and repurpose them into social content: "
        "https://www.youtube.com/watch?v=JFMxDgmW8cw, "
        "https://www.youtube.com/watch?v=8nFTkjPk80k, "
        "https://www.youtube.com/watch?v=bpM9D1kQaAs. "
        "For each video, extract key insights and create: a Twitter thread, "
        "a LinkedIn post, and a short-form video script."
    ),
}


def run_skill_with_hermes(skill_name: str, task: str) -> str:
    """Run a skill through the Hermes AIAgent runtime."""
    skill_md = SKILLS_DIR / skill_name / "SKILL.md"
    system_prompt = ""
    if skill_md.exists():
        system_prompt = skill_md.read_text(encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"HERMES AGENT :: {skill_name}")
    print(f"{'='*60}")

    agent = AIAgent(
        model=os.getenv("HERMES_MODEL", "qwen2.5-64k"),
        base_url="http://localhost:11434/v1",
        api_key="ollama",
        quiet_mode=True,
        ephemeral_system_prompt=system_prompt,
        max_iterations=5,
        skip_context_files=True,
        skip_memory=True,
        disabled_toolsets=["terminal", "browser"],
    )

    result = agent.run_conversation(user_message=task)
    response = result.get("final_response", "No response")
    print(f"\n[{skill_name}] Response preview: {response[:200]}...")

    # Save to vault
    out_dir = VAULT / skill_name.replace("_", " ").title().replace(" ", "")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"hermes_output.md").write_text(
        f"# Hermes Agent Output — {skill_name}\n\n{response}\n",
        encoding="utf-8",
    )
    return response


def main():
    print("Starting Hermes Agent pipeline...")
    print(f"Model: {os.getenv('OLLAMA_MODEL', 'qwen2.5:7b')} via Ollama")
    print(f"Skills: {list(SKILL_TASKS.keys())}")

    for skill_name, task in SKILL_TASKS.items():
        try:
            run_skill_with_hermes(skill_name, task)
        except Exception as e:
            print(f"[{skill_name}] FAILED: {e}")

    print("\n" + "="*60)
    print("Hermes Agent pipeline complete.")
    print(f"Outputs in: {VAULT}")


if __name__ == "__main__":
    main()
