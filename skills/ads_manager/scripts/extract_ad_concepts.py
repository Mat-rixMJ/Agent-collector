"""Stage 2: LLM pass extracting pain/hook/offer/CTA from each shortlisted ad."""
import json
from pathlib import Path

from tools.llm_client import ask

IN_PATH = Path("data/ads/meta_ads_shortlist.json")
OUT_PATH = Path("data/ads/ad_concepts.json")

SYSTEM_PROMPT = (
    "You are a direct-response marketing analyst. Given one ad's text/creative "
    "metadata, extract strictly as JSON with keys: pain_point, hook, offer_mechanism, "
    "cta, notes. Keep each value to 1-2 sentences. No markdown, just the JSON object."
)


def extract(ad: dict) -> dict:
    ad_text = ad.get("ad_creative_body") or ad.get("body") or ad.get("headline") or ""
    advertiser = ad.get("page_name") or ad.get("advertiser") or "unknown"
    raw = ask(SYSTEM_PROMPT, f"Advertiser: {advertiser}\nAd text: {ad_text}")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"pain_point": "", "hook": "", "offer_mechanism": "", "cta": "", "notes": raw}
    parsed["advertiser"] = advertiser
    return parsed


def main() -> None:
    if not IN_PATH.exists():
        print(f"{IN_PATH} not found — run scrape_meta_ads.py first.")
        return
    ads = json.loads(IN_PATH.read_text())
    concepts = []
    for ad in ads:
        try:
            concepts.append(extract(ad))
        except Exception as e:
            print(f"  failed to extract: {e}")
    OUT_PATH.write_text(json.dumps(concepts, indent=2))
    print(f"Extracted {len(concepts)} concepts -> {OUT_PATH}")


if __name__ == "__main__":
    main()
