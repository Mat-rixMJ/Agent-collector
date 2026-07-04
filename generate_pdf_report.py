"""Analyse all extracted data and generate a clean PDF report for non-tech stakeholders.

Usage: python generate_pdf_report.py
Output: output/marketing_report.pdf
"""
import json
from pathlib import Path
from datetime import date

from fpdf import FPDF
from tools.llm_client import ask

VAULT = Path("obsidian_vault")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


class Report(FPDF):
    def __init__(self):
        super().__init__()
        import os
        font_dir = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
        self.add_font("Arial", "", os.path.join(font_dir, "arial.ttf"))
        self.add_font("Arial", "B", os.path.join(font_dir, "arialbd.ttf"))
        self.add_font("Arial", "I", os.path.join(font_dir, "ariali.ttf"))

    def header(self):
        self.set_font("Arial", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "CrowdWisdomTrading - Marketing Intelligence Report", align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def chapter_title(self, title):
        self.set_font("Arial", "B", 16)
        self.set_text_color(30, 60, 120)
        self.ln(5)
        self.cell(0, 10, title)
        self.ln(12)

    def section_title(self, title):
        self.set_font("Arial", "B", 12)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, title)
        self.ln(9)

    def body_text(self, text):
        self.set_font("Arial", "", 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5.5, text)
        self.ln(3)

    def bullet(self, text):
        self.set_font("Arial", "", 10)
        self.set_text_color(30, 30, 30)
        self.cell(5)
        self.multi_cell(0, 5.5, f"\u2022 {text}")
        self.ln(1)


def get_executive_summary() -> str:
    """Use LLM to create a plain-English executive summary from all data."""
    # Gather key data points
    competitors = []
    for f in sorted((VAULT / "Competitors").glob("*.md")):
        if f.name != "_synthesis.md":
            competitors.append(f.stem.replace("_", " "))

    synth = (VAULT / "Competitors" / "_synthesis.md").read_text(encoding="utf-8")

    inf_data = json.loads(Path("data/influencers/influencers.json").read_text())
    ads_data = []
    ads_path = Path("data/ads/ad_concepts.json")
    if ads_path.exists():
        ads_data = json.loads(ads_path.read_text())

    content_files = list((VAULT / "Content").glob("*.md"))

    prompt = f"""Write a 200-word executive summary for a marketing report. 
The audience is a non-technical CEO. Use plain language, no jargon.

Key findings:
- Researched {len(competitors)} competitors: {', '.join(competitors)}
- Competitive synthesis: {synth[:500]}
- Found {len(ads_data)} ad concepts from Meta Ads Library in the retail trading niche
- Discovered {len(inf_data)} potential influencer partners on YouTube
- Repurposed {len(content_files)} videos into social media content

Write the summary in 3 short paragraphs: market landscape, opportunities, next steps."""

    return ask("You write clear executive summaries for business leaders.", prompt)


def build_pdf():
    print("Generating executive summary via LLM...")
    exec_summary = get_executive_summary()

    pdf = Report()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # --- Cover page ---
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Arial", "B", 28)
    pdf.set_text_color(30, 60, 120)
    pdf.cell(0, 15, "Marketing Intelligence", align="C")
    pdf.ln(12)
    pdf.cell(0, 15, "Report", align="C")
    pdf.ln(20)
    pdf.set_font("Arial", "", 14)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 10, "CrowdWisdomTrading.com", align="C")
    pdf.ln(8)
    pdf.cell(0, 10, f"Generated: {date.today().isoformat()}", align="C")
    pdf.ln(8)
    pdf.cell(0, 10, "Prepared by: AI Marketing Agent Team", align="C")

    # --- Executive Summary ---
    pdf.add_page()
    pdf.chapter_title("Executive Summary")
    pdf.body_text(exec_summary)

    # --- Competitor Analysis ---
    pdf.add_page()
    pdf.chapter_title("1. Competitive Landscape")

    comp_dir = VAULT / "Competitors"
    for f in sorted(comp_dir.glob("*.md")):
        if f.name == "_synthesis.md":
            continue
        content = f.read_text(encoding="utf-8")
        name = f.stem.replace("_", " ")
        pdf.section_title(name)
        # Strip markdown headers, keep text
        lines = [l for l in content.split("\n") if not l.startswith("#") and l.strip()]
        pdf.body_text("\n".join(lines[:20]))

    pdf.section_title("Key Takeaways")
    synth = (comp_dir / "_synthesis.md").read_text(encoding="utf-8")
    lines = [l for l in synth.split("\n") if not l.startswith("#") and l.strip()]
    pdf.body_text("\n".join(lines))

    # --- Ads Analysis ---
    pdf.add_page()
    pdf.chapter_title("2. Advertising Analysis")

    ads_path = Path("data/ads/ad_concepts.json")
    if ads_path.exists():
        concepts = json.loads(ads_path.read_text())
        pdf.body_text(
            f"We analyzed the Meta Ads Library and found {len(concepts)} "
            f"active ad concepts in the retail trading niche from the last 30 days."
        )
        pdf.ln(3)
        for i, c in enumerate(concepts[:5], 1):
            pdf.section_title(f"Ad Concept #{i}")
            pdf.bullet(f"Pain Point: {c.get('pain_point', 'N/A')}")
            pdf.bullet(f"Hook: {c.get('hook', 'N/A')}")
            pdf.bullet(f"Offer: {c.get('offer_mechanism', 'N/A')}")
            pdf.bullet(f"CTA: {c.get('cta', 'N/A')}")
            pdf.ln(3)

    pdf.section_title("Generated Ad Script")
    for f in (VAULT / "Ads").glob("*.md"):
        content = f.read_text(encoding="utf-8")
        # Strip markdown formatting
        lines = [l for l in content.split("\n") if not l.startswith("#") and not l.startswith("```")]
        pdf.body_text("\n".join(lines[:40]))

    # --- Influencer Outreach ---
    pdf.add_page()
    pdf.chapter_title("3. Influencer Discovery")

    inf_data = json.loads(Path("data/influencers/influencers.json").read_text())
    pdf.body_text(
        f"Identified {len(inf_data)} retail-trading YouTube creators as potential "
        f"outreach targets. Below are the top channels discovered:"
    )
    pdf.ln(3)

    # Simple table
    pdf.set_font("Arial", "B", 9)
    pdf.cell(8, 7, "#", border=1)
    pdf.cell(55, 7, "Channel", border=1)
    pdf.cell(80, 7, "Recent Video", border=1)
    pdf.cell(0, 7, "Views", border=1)
    pdf.ln()
    pdf.set_font("Arial", "", 9)
    for i, inf in enumerate(inf_data[:20], 1):
        handle = (inf.get("handle") or "unknown")[:25]
        video = ""
        titles = inf.get("recent_video_titles") or []
        if titles:
            video = titles[0][:35] if isinstance(titles[0], str) else ""
        views = str(inf.get("avg_views") or "N/A")
        pdf.cell(8, 6, str(i), border=1)
        pdf.cell(55, 6, handle, border=1)
        pdf.cell(80, 6, video, border=1)
        pdf.cell(0, 6, views, border=1)
        pdf.ln()

    pdf.ln(5)
    pdf.section_title("Sample Outreach Message")
    outreach_files = sorted((VAULT / "Outreach").glob("*.md"))
    if outreach_files:
        sample = outreach_files[0].read_text(encoding="utf-8")
        lines = [l for l in sample.split("\n") if not l.startswith("#") and l.strip()]
        pdf.body_text("\n".join(lines))

    # --- Content Repurposing ---
    pdf.add_page()
    pdf.chapter_title("4. Content Repurposing")

    content_files = sorted((VAULT / "Content").glob("*.md"))
    pdf.body_text(
        f"Processed {len(content_files)} YouTube videos from the provided data sources. "
        f"Each video was transcribed, key insights extracted, and repurposed into "
        f"3 platform-native formats: Twitter/X thread, LinkedIn post, and short-form video script."
    )
    pdf.ln(3)

    if content_files:
        content = content_files[0].read_text(encoding="utf-8")
        lines = content.split("\n")
        # Find insights section
        pdf.section_title(f"Sample: {content_files[0].stem}")
        text_lines = [l for l in lines if not l.startswith("#") and l.strip()]
        pdf.body_text("\n".join(text_lines[:30]))

    # --- Save ---
    out_path = OUTPUT_DIR / "marketing_report.pdf"
    pdf.output(str(out_path))
    print(f"\n{'='*50}")
    print(f"PDF Report generated: {out_path}")
    print(f"{'='*50}")


if __name__ == "__main__":
    build_pdf()
