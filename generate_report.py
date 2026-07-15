"""Generate a clean summary report from the pipeline output."""
from pathlib import Path
import json

vault = Path("obsidian_vault")
report = []
report.append("# Marketing Intelligence Agents — Run Report")
report.append("**Date:** 2026-07-04  ")
report.append("**Pipeline:** `main.py` (Hermes Agent orchestration loop)  ")
report.append("**LLM:** qwen2.5:7b via Ollama (local)  ")
report.append("**Data:** Apify actors  ")
report.append("")

# Kanban
report.append("---")
report.append("## Kanban Board Status")
report.append("")
board = json.loads(Path("kanban/board.json").read_text())
for col in board["columns"]:
    cards = [c for c in board["cards"] if c["column"] == col]
    report.append(f"### {col} ({len(cards)})")
    for c in cards:
        report.append(f"- {c['title']} *[{c['skill']}]*")
    report.append("")

# Competitors
report.append("---")
report.append("## 1. Marketing Manager — Competitor Research")
report.append("")
comp_dir = vault / "Competitors"
for f in sorted(comp_dir.glob("*.md")):
    if f.name == "_synthesis.md":
        continue
    content = f.read_text(encoding="utf-8")
    lines = content.strip().split("\n")
    report.append(f"### {f.stem.replace('_', ' ')}")
    # Show first ~15 lines as preview
    report.extend(lines[2:15])
    report.append("")

report.append("### Competitive Synthesis")
synth = (comp_dir / "_synthesis.md").read_text(encoding="utf-8")
report.extend(synth.strip().split("\n")[2:])
report.append("")

# Ads
report.append("---")
report.append("## 2. Ads Manager — Generated Ad Script")
report.append("")
for f in (vault / "Ads").glob("*.md"):
    report.append(f.read_text(encoding="utf-8"))
report.append("")

# Influencers
report.append("---")
report.append("## 3. Influencer Outreach Agent")
report.append("")
inf_data = json.loads(Path("data/influencers/influencers.json").read_text())
report.append(f"**Total channels discovered:** {len(inf_data)}")
report.append("")
report.append("| # | Channel | Platform | URL |")
report.append("|---|---------|----------|-----|")
for i, inf in enumerate(inf_data[:15], 1):
    handle = inf.get("handle", "unknown")
    url = inf.get("url", "")
    report.append(f"| {i} | {handle} | {inf['platform']} | {url} |")
if len(inf_data) > 15:
    report.append(f"| ... | *+{len(inf_data)-15} more channels* | | |")
report.append("")
report.append("### Sample Outreach Drafts (3 of {})".format(len(inf_data)))
report.append("")
outreach_dir = vault / "Outreach"
samples = sorted(outreach_dir.glob("*.md"))[:3]
for f in samples:
    report.append(f.read_text(encoding="utf-8"))
    report.append("---")
    report.append("")

# Content
report.append("---")
report.append('## 4. Content Repurposer — "Your Idea" Agent')
report.append("")
content_dir = vault / "Content"
content_files = sorted(content_dir.glob("*.md"))
report.append(f"**Videos processed:** {len(content_files)} of 5")
report.append("")
for f in content_files[:2]:
    text = f.read_text(encoding="utf-8")
    report.append(text[:2000])
    if len(text) > 2000:
        report.append("\n*(truncated for report — full version in obsidian_vault/Content/)*\n")
    report.append("---")
    report.append("")

# Footer
report.append("---")
report.append("## Pipeline Summary")
report.append("")
report.append("| Agent | Output | Files |")
report.append("|-------|--------|-------|")
report.append(f"| Marketing Manager | Competitor briefs + synthesis | {len(list(comp_dir.glob('*.md')))} files |")
report.append(f"| Ads Manager | Ad concepts + script | {len(list((vault/'Ads').glob('*.md')))} script |")
report.append(f"| Influencer Outreach | Channel dossiers + cold DMs | {len(inf_data)} channels, {len(list(outreach_dir.glob('*.md')))} drafts |")
report.append(f"| Content Repurposer | Repurposed social content | {len(content_files)} videos |")
report.append("")
report.append("*All outputs stored in `obsidian_vault/` as Markdown — human-readable knowledge base.*")

final = "\n".join(report)
Path("RUN_REPORT.md").write_text(final, encoding="utf-8")
print(f"✓ RUN_REPORT.md written ({len(final):,} chars, {len(final.splitlines())} lines)")
