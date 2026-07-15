"""Stage 2: LLM pass extracting pain/hook/offer/CTA from each shortlisted ad."""
import json
from pathlib import Path

from tools.llm_client import ask
from tools import config_manager

IN_PATH = Path("data/ads/meta_ads_shortlist.json")
OUT_PATH = Path("data/ads/ad_concepts.json")

config = config_manager.load_config()
niche = config.get("niche", "unknown")

SYSTEM_PROMPT = (
    "You are a direct-response marketing analyst. Given one ad's text/creative "
    "metadata, extract strictly as JSON with keys: pain_point, hook, offer_mechanism, "
    "cta, notes. Keep each value to 1-2 sentences. No markdown, just the JSON object."
)


def is_relevant_trading_ad(advertiser: str, ad_text: str) -> bool:
    company_name = config.get("company_name", "Our Company")
    prompt = (
        f"You are an ad classification filter. Analyze if this ad's target audience and offer strictly match [{company_name}: {niche}]. "
        "Does the target audience and offer match? Answer strictly 'yes' or 'no'. Do not include any other words."
    )
    try:
        res = ask(prompt, f"Advertiser: {advertiser}\nAd text: {ad_text}").strip().lower()
        return res.startswith("yes")
    except Exception as e:
        print(f"  Relevance check failed for {advertiser}: {e}")
        return True # Fallback to true to be safe if LLM fails


def extract(ad: dict) -> dict:
    ad_text = ad.get("adText_cleaned") or ad.get("adText") or ad.get("ad_creative_body") or ad.get("body") or ad.get("headline") or ""
    if not ad_text and ad.get("adCreativeBodies"):
        bodies = ad.get("adCreativeBodies")
        if isinstance(bodies, list):
            ad_text = " ".join(filter(None, bodies))
        elif isinstance(bodies, str):
            ad_text = bodies
            
    advertiser = ad.get("page_name") or ad.get("pageName") or ad.get("advertiser") or "unknown"
    
    # Run LLM relevance filter first
    if not is_relevant_trading_ad(advertiser, ad_text):
        print(f"  [LLM FILTER] Discarded off-niche ad by {advertiser}")
        return {}

    raw = ask(SYSTEM_PROMPT, f"Advertiser: {advertiser}\nAd text: {ad_text}")
    try:
        # Try to find JSON block in the raw string if LLM returned markdown
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            parsed = json.loads(raw[start:end])
        else:
            parsed = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        parsed = {"pain_point": "", "hook": "", "offer_mechanism": "", "cta": "", "notes": raw}
        
    parsed["advertiser"] = advertiser
    return parsed


def main() -> None:
    if not IN_PATH.exists():
        print(f"{IN_PATH} not found — run scrape_meta_ads.py first.")
        return
    ads = json.loads(IN_PATH.read_text(encoding="utf-8"))
    concepts = []
    discarded_count = 0
    for ad in ads:
        try:
            concept = extract(ad)
            if concept:
                concepts.append(concept)
            else:
                discarded_count += 1
        except Exception as e:
            print(f"  failed to extract: {e}")
            
    OUT_PATH.write_text(json.dumps(concepts, indent=2), encoding="utf-8")
    print(f"Extracted {len(concepts)} concepts | Discarded {discarded_count} off-niche -> {OUT_PATH}")


if __name__ == "__main__":
    main()
