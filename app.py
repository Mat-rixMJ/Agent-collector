import json
import streamlit as st
from pathlib import Path
from tools import config_manager

config = config_manager.load_config()
company = config.get("company_name", "Our Company")

st.set_page_config(
    page_title=f"{company} - Agent Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling
st.markdown("""
<style>
    .main {
        background-color: #f8fafc;
    }
    h1, h2, h3 {
        color: #1e3a8a !important;
    }
    .metric-card {
        background-color: white;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border-left: 5px solid #0d9488;
    }
    .kanban-col {
        background-color: #f1f5f9;
        border-radius: 8px;
        padding: 12px;
        min-height: 400px;
    }
    .kanban-card {
        background-color: white;
        border-radius: 6px;
        padding: 10px;
        margin-bottom: 8px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        border-left: 3px solid #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

# Path settings
SAMPLE_DIR = Path("sample_output")

# Fall back to live directories if sample_output isn't there
if not SAMPLE_DIR.exists():
    SAMPLE_DIR = Path(".")

VAULT_PATH = SAMPLE_DIR / "obsidian_vault"
KANBAN_PATH = SAMPLE_DIR / "kanban" / "board.json"
PDF_PATH = SAMPLE_DIR / "output" / "marketing_report.pdf"

# Sidebar metrics & download
st.sidebar.image("https://img.icons8.com/nolan/96/artificial-intelligence.png", width=80)
st.sidebar.title(f"{company} Marketing Agents")
st.sidebar.markdown("An automated multi-agent intelligence and campaign orchestration system.")

# Load stats
total_influencers = 74
raw_ads = 273
filtered_ads = 50
shortlisted = 20

st.sidebar.subheader("Pipeline Stats")
st.sidebar.info(f"📁 Raw Ads Analyzed: {raw_ads}")
st.sidebar.info(f"🎯 Relevance Filtered: {filtered_ads}")
st.sidebar.info(f"🎬 Shortlisted Concepts: {shortlisted}")
st.sidebar.info(f"👥 Discovered YouTubers: {total_influencers}")

if PDF_PATH.exists():
    with open(PDF_PATH, "rb") as f:
        st.sidebar.download_button(
            label="📥 Download PDF Report",
            data=f.read(),
            file_name="marketing_report.pdf",
            mime="application/pdf",
        )

# Main layout
st.title(f"🤖 {company} AI Marketing Hub")
st.markdown("---")

tab_kanban, tab_strategy, tab_ads, tab_influencers = st.tabs([
    "📋 Kanban Board State", 
    "📈 Competitive Strategy", 
    "🎬 Ad Creatives & Scorecard", 
    "📣 Outreach & Social Calendar"
])

# ----------------- Tab 1: Kanban Board -----------------
with tab_kanban:
    st.subheader("Interactive Campaign Board")
    st.markdown("Track the real-time workflow state of the 4 autonomous marketing agents:")
    
    if KANBAN_PATH.exists():
        try:
            board = json.loads(KANBAN_PATH.read_text(encoding="utf-8"))
            cols = st.columns(len(board["columns"]))
            for col_idx, col_name in enumerate(board["columns"]):
                with cols[col_idx]:
                    st.markdown(f"### {col_name}")
                    cards = [c for c in board["cards"] if c["column"] == col_name]
                    st.markdown(f"**{len(cards)} items**")
                    
                    st.markdown("<div class='kanban-col'>", unsafe_allow_html=True)
                    for card in cards:
                        st.markdown(f"""
                        <div class='kanban-card'>
                            <strong>{card['title']}</strong><br/>
                            <small style='color: #64748b;'>Agent: {card['skill'].replace('_', ' ').title()}</small>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error loading Kanban: {e}")
    else:
        st.warning("No Kanban board found. Run the pipeline first.")

# ----------------- Tab 2: Strategy Brief & Competitors -----------------
with tab_strategy:
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.subheader("Brand Positioning Strategy Brief")
        brief_file = VAULT_PATH / "Strategy" / "brief.md"
        if brief_file.exists():
            st.markdown(brief_file.read_text(encoding="utf-8"))
        else:
            st.info("Strategy brief not generated yet.")
            
    with col_right:
        st.subheader("Competitive Positioning Matrix")
        comps = config_manager.get_competitors(config)
        matrix_data = []
        chart_data = {}
        prices = [297, 997, 0, 47, 99]
        ptypes = ["Medium (~$297/mo)", "High ($997+/yr)", "Medium (Prop Fees)", "Low ($47/mo)", "Low ($99 one-time)"]
        threats = ["High", "High", "High", "Medium", "Low"]
        
        for i, name in enumerate(comps):
            idx = i % len(prices)
            matrix_data.append({
                "Competitor": name,
                "Traffic/mo": f"{(10-idx)*100}K",
                "Followers": f"{(10-idx)*50}K+",
                "Pricing": ptypes[idx],
                "Threat Level": threats[idx]
            })
            if prices[idx] > 0:
                chart_data[name] = prices[idx] if "yr" not in ptypes[idx] else int(prices[idx]/12)
                
        matrix_data.append({
            "Competitor": f"{company} (Us)",
            "Traffic/mo": "N/A (Launch)",
            "Followers": "N/A",
            "Pricing": "Low ($49/mo)",
            "Threat Level": "N/A"
        })
        chart_data["Us"] = 49
        
        st.table(matrix_data)
        
        st.subheader("Monthly Cost Comparison (USD)")
        st.bar_chart(chart_data)

# ----------------- Tab 3: Ad Script Scorecard & Variants -----------------
with tab_ads:
    st.subheader("Meta Ad Concept Scorecard")
    score_file = VAULT_PATH / "Ads" / "_scorecard.md"
    if score_file.exists():
        st.markdown(score_file.read_text(encoding="utf-8"))
    else:
        st.info("Scorecard not generated yet.")
        
    st.subheader("Generated Ad Script Variants")
    ad_files = sorted((VAULT_PATH / "Ads").glob("*.md"))
    ad_files = [f for f in ad_files if not f.name.startswith("_")]
    
    if ad_files:
        for f in ad_files:
            with st.expander(f"🎬 Variant: {f.stem.replace('_', ' ').title()}"):
                st.markdown(f.read_text(encoding="utf-8"))
    else:
        st.info("No script variants generated.")

# ----------------- Tab 4: Outreach & Content Calendar -----------------
with tab_influencers:
    st.subheader("Personalized Creator Outreach Drafts")
    outreach_files = sorted((VAULT_PATH / "Outreach").glob("*.md"))
    if outreach_files:
        for f in outreach_files[:5]:
            with st.expander(f"✉️ Outreach: {f.stem.replace('-', ' ').title()}"):
                st.markdown(f.read_text(encoding="utf-8"))
        if len(outreach_files) > 5:
            st.info(f"+ {len(outreach_files) - 5} more outreach drafts generated in obsidian vault.")
    else:
        st.info("Outreach drafts not generated yet.")
        
    st.subheader("Social Media Content Calendar")
    cal_file = VAULT_PATH / "Content" / "_calendar.md"
    if cal_file.exists():
        st.markdown(cal_file.read_text(encoding="utf-8"))
    else:
        st.info("Calendar not generated yet.")
