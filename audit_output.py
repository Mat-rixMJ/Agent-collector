"""Quick audit of all pipeline outputs."""
from pathlib import Path
import json

print("=== PIPELINE DATA AUDIT ===")
print()

# 1. Config
config = json.loads(Path("data/config.json").read_text(encoding="utf-8"))
print(f"Company: {config['company_name']}")
print(f"Target Site: {config['target_site']}")
print(f"Niche: {config['niche']}")
print()

# 2. Competitors
comp_dir = Path("obsidian_vault/Competitors")
comps = [f.stem for f in comp_dir.glob("*.md") if f.stem != "_synthesis"]
print(f"Competitors researched ({len(comps)}): {comps}")
for f in comp_dir.glob("*.md"):
    if f.stem == "_synthesis":
        continue
    text = f.read_text(encoding="utf-8")
    has_pricing = "not publicly" in text.lower() or "not disclosed" in text.lower()
    word_count = len(text.split())
    print(f"  {f.stem}: {word_count} words, pricing={'MISSING' if has_pricing else 'FOUND'}")
print()

# 3. Ads
ads_dir = Path("obsidian_vault/Ads")
ad_files = list(ads_dir.glob("*.md")) if ads_dir.exists() else []
print(f"Ad scripts generated: {len(ad_files)}")
concepts_path = Path("data/ads/ad_concepts.json")
concepts = json.loads(concepts_path.read_text(encoding="utf-8")) if concepts_path.exists() else []
print(f"Ad concepts extracted: {len(concepts)}")
print()

# 4. Influencers
inf = json.loads(Path("data/influencers/influencers.json").read_text(encoding="utf-8"))
print(f"Influencers found: {len(inf)}")
subs_zero = sum(1 for i in inf if i.get("subscribers", 0) == 0)
print(f"  With 0 subscribers (data missing): {subs_zero}/{len(inf)}")
low_views = sum(1 for i in inf if i.get("avg_views", 0) < 1000)
print(f"  With <1000 avg views (micro): {low_views}/{len(inf)}")
for i in inf:
    print(f"  - {i['handle']:30s} avg_views={i.get('avg_views', 'N/A'):>10} subs={i.get('subscribers', 'N/A')}")
print()

# 5. Content
content_dir = Path("obsidian_vault/Content")
content_files = [f for f in content_dir.glob("*.md") if not f.name.startswith("_")] if content_dir.exists() else []
print(f"Content pieces repurposed: {len(content_files)}")
print()

# 6. Outreach
outreach_dir = Path("obsidian_vault/Outreach")
outreach_files = list(outreach_dir.glob("*.md")) if outreach_dir.exists() else []
print(f"Outreach drafts: {len(outreach_files)}")
print()

# 7. PDF
pdf = Path("output/marketing_report.pdf")
print(f"PDF exists: {pdf.exists()}, size: {pdf.stat().st_size if pdf.exists() else 0} bytes")
