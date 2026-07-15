"""LLM client. Supports OpenRouter, NVIDIA build, and local Ollama.
All expose OpenAI-compatible /chat/completions endpoints.

Rate limit strategy:
- On 429, reads Retry-After header and sleeps that exact duration
- Rotates between free models to spread load
- 7 attempts with increasing backoff (covers ~3min of rate limiting)
- Falls back to Ollama if all cloud attempts fail
"""
import json
import os
import time
import uuid
import sys
import requests
from pathlib import Path
from tools import config_manager
from dotenv import load_dotenv

load_dotenv()

_PROVIDERS = {
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "key_env": "OPENROUTER_API_KEY",
        "model_env": "OPENROUTER_MODEL",
    },
    "nvidia": {
        "url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "key_env": "NVIDIA_API_KEY",
        "model_env": "NVIDIA_MODEL",
    },
    "ollama": {
        "url": "http://localhost:11434/v1/chat/completions",
        "key_env": None,
        "model_env": "OLLAMA_MODEL",
    },
}

# Free models to rotate through on rate limits
_FREE_MODELS = [
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-4-31b-it:free",
    "qwen/qwen3-coder:free",
]
_rotation_idx = 0

MAX_RETRIES = 7

# --- Demo mode concept pool ---
# A mutable list used as a pointer so get_demo_response() can increment it across calls.
# Using a list because Python closures can't rebind a bare int from an inner scope.
_demo_extract_counter = [-1]

_CONCEPT_VARIANTS = [
    {
        "pain_point": "Retail traders blow prop firm challenges because they overtrade under pressure.",
        "hook": "Stop failing prop challenges. Here is the disciplined edge serious traders use.",
        "offer_mechanism": "Real-time community alerts and daily pre-market prep for just $49/mo.",
        "cta": "Start your CWT trial today",
        "notes": "Loss aversion angle targeting prop firm traders."
    },
    {
        "pain_point": "Beginner day traders lose money copying",
        "hook": "Tired of guessing the market direction?",
        "offer_mechanism": "company_name premium signals",
        "cta": "Join company_name today",
        "notes": "Price comparison angle targeting guru-fatigued traders."
    },
    {
        "pain_point": "Forex traders struggle to read institutional order flow without expensive tools.",
        "hook": "Retail forex traders are always one step behind institutions. Until now.",
        "offer_mechanism": "Daily institutional bias reports and real-time alerts delivered to Telegram for $49/mo.",
        "cta": "Get your first week free",
        "notes": "Institutional edge angle for forex audience."
    },
    {
        "pain_point": "Swing traders miss entries because they have no structured pre-market routine.",
        "hook": "Most swing traders check charts randomly. Top performers follow a strict morning plan.",
        "offer_mechanism": "Pre-market watchlists and swing trade setups delivered daily for $49/mo.",
        "cta": "Build your edge with CWT",
        "notes": "Routine-building angle for swing traders."
    },
    {
        "pain_point": "Options traders overpay for signals with no community accountability or support.",
        "hook": "Paying $200/mo for options alerts with zero community support? You deserve better.",
        "offer_mechanism": "Options flow alerts, daily market commentary, and Discord community for $49/mo.",
        "cta": "Switch to CWT and save",
        "notes": "Value comparison angle targeting options traders."
    },
    {
        "pain_point": "New traders blow their first account within weeks because they skip risk management basics.",
        "hook": "Your first account does not have to be your last. Here is what most gurus never teach.",
        "offer_mechanism": "Structured daily trade plans and 1% risk rule alerts from $49/mo.",
        "cta": "Start trading smarter today",
        "notes": "Beginner safety angle with education framing."
    },
    {
        "pain_point": "Part-time traders miss the best setups because they cannot watch charts all day.",
        "hook": "What if you could get pre-screened setups delivered before the market opens?",
        "advertiser": "Mock Advertiser",
        "pain_point": "Users struggle with generic mock data.",
        "hook": "Stop looking at old trading examples.",
        "offer_mechanism": "Dynamic generated mock.",
        "cta": "Click here.",
        "notes": "Mock data."
    }
]


def _call_api(url: str, headers: dict, payload: dict) -> requests.Response:
    """Single API call with timeout."""
    return requests.post(url, headers=headers, json=payload, timeout=300)


def _get_demo_response(system: str, prompt: str) -> str:
    config = config_manager.load_config()
    company = config.get("company_name", "Our Company")
    combined = (system + "\n" + prompt).lower()

    if "classification filter" in combined or "yes or no" in combined or "coherence" in combined or "coherent" in combined:
        return "yes"

    elif "extract" in combined and "pain_point" in combined:
        _demo_extract_counter[0] = (_demo_extract_counter[0] + 1) % len(_CONCEPT_VARIANTS)
        chosen = _CONCEPT_VARIANTS[_demo_extract_counter[0]]
        return json.dumps(chosen)

    elif ("score" in combined or "rubric" in combined) and "revising an ad script" not in combined:
        if "output as clean json" in combined or ("hook" in combined and "pain" in combined and "mechanism" in combined):
            import random as _random
            _seed = abs(hash(prompt[:80])) % 10
            total = 28 + _seed
            hook = min(10, 6 + _seed % 4)
            pain = min(10, 7 + _seed % 3)
            mech = min(10, 5 + _seed % 4)
            proof = min(10, 4 + _seed % 3)
            cta = total - hook - pain - mech - proof
            cta = max(3, min(10, cta))
            verdict = "Ready to shoot" if total >= 32 else "Needs revision" if total >= 25 else "Kill it"
            return json.dumps({
                "hook": hook,
                "pain": pain,
                "mechanism": mech,
                "proof": proof,
                "cta": cta,
                "total": total,
                "verdict": verdict,
                "top_improvement": "Add a specific dollar figure or time frame to the hook to increase specificity."
            })
        from pathlib import Path as _Path
        ads_vault = _Path(os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian_vault")) / "Ads"
        script_files = sorted([f.stem for f in ads_vault.glob("*.md") if not f.name.startswith("_")])
        if len(script_files) >= 3:
            fear_name = next((s for s in script_files if "fear" in s), script_files[0])
            asp_name = next((s for s in script_files if "aspiration" in s), script_files[1] if len(script_files) > 1 else script_files[0])
            sp_name = next((s for s in script_files if "social" in s), script_files[2] if len(script_files) > 2 else script_files[0])
        else:
            fear_name, asp_name, sp_name = "ad_script_fear", "ad_script_aspiration", "ad_script_social_proof"
        return f"""# Ad Script Scorecard

Ranked by total score (out of 50). Higher = more likely to convert.

| Rank | Script | Total | Verdict |
|------|--------|-------|---------|
| 1 | {fear_name} | 38/50 | Ready to shoot |
| 2 | {asp_name} | 36/50 | Ready to shoot |
| 3 | {sp_name} | 30/50 | Needs revision |

---

## Detailed Scores

### #1: {fear_name}
- Hook Strength: 8/10
- Pain Clarity: 9/10
- Mechanism: 7/10
- Proof Elements: 6/10
- CTA Urgency: 8/10
- **Total: 38/50**
- **Verdict: Ready to shoot**

---

## A/B Test Plan for Ad Script Variants

### Testing Parameters
- **Budget Split:** Equal 33% split ($50/day per variant).
- **Target Audience:** Retail traders, Forex, and Prop Firm enthusiasts.
- **Duration:** 14 days.
"""

    elif "revise" in combined or "revision" in combined:
        return f"""# Ad Script — Revised Version

## Script
[Visual: A person looking at a chart, then opening the {company} dashboard.]
Narrator: "Are you tired of guessing the market direction?"
[Visual: Screen recording showing {company} signals hitting targets.]
Narrator: "Stop guessing. Start knowing. Our community provides the exact setups you need."
[Visual: Text on screen: Join today.]
Narrator: "Join {company} today."
"""

    elif "cold outreach EMAILS" in system:
        return f"""Subject: Sponsored segment proposal / Affiliate partnership with {company}

Hi,

I love the recent videos you've been putting out. I'm reaching out from {company} because our audience overlaps heavily with yours. We're looking to sponsor a segment in an upcoming video or set up an affiliate partnership. We offer competitive base rates and a high-converting affiliate commission structure, plus free lifetime premium access for you and your audience.

Let me know if you're open to checking out details, or reply to set up a brief chat!

Best,
The {company} Team"""

    elif "Synthesize these competitor summaries" in prompt:
        return f"""We successfully conducted competitive research across 5 major platforms, identifying pricing and positioning gaps for {company}'s launch.

1. **Pricing:** Most competitors charge $100-$200/mo. At a lower price point, {company} is highly disruptive.
2. **Community:** Competitors offer basic Discord rooms. We can emphasize our interactive, mentor-led environment.
3. **Unbiased Strategy Reviews:** Competitors promote their own indicator systems. {company} can stand out by providing transparent, crowd-sourced alerts."""

    elif "synthesis" in combined or "synthesize" in combined:
        return """# Competitive Strategy & Gap Analysis

## Market Gaps
1. **Affordable Entry-Level Subscriptions:** Competitors charge high annual fees ($997+) or expensive monthly rates ($297+). There is a massive gap for a low-cost, high-value monthly option at $49/mo.
2. **Community-First Learning:** Many platforms are centered around a single guru. Building a decentralized, peer-to-peer sharing community offers a unique value proposition.
3. **Unbiased Strategy Reviews:** Competitors promote their own indicator systems. CrowdWisdomTrading can stand out by providing transparent, crowd-sourced trading alerts."""

    elif "Marketing Strategy Brief" in system or "marketing strategist" in system:
        return f"""# Marketing Strategy Brief: {company}

{company} is the ultimate community-driven hub. We offer real-time alerts, daily analysis, and educational resources, contrasting sharply with high-cost competitor plans.

## Target Audience Segments
- **Beginners:** Overwhelmed by jargon.
- **Intermediate:** Struggling with consistency.
- **Pros:** Looking for community and networking.

## Positioning Statements
- More affordable than the rest.
- Better community support.
- Transparent and real-time.

## Compliance and Regulatory Notice
All marketing materials must state: *Trading contains substantial risk. Past performance is not indicative of future results. {company} is not a registered broker-dealer or financial advisor.*"""

    elif "original 30-45 second video ad script" in combined:
        if "FEAR and LOSS AVERSION" in prompt:
            return f"""[Visual: Red charts and frustrated person]
Narrator: "Stop paying gurus thousands. Join {company}. Real-time community alerts, support, and pre-market prep."
[Visual: Logo]
Narrator: "Click here to stop losing."
"""
        elif "ASPIRATION and DESIRE" in prompt:
            return f"""[Visual: Green charts and happy person]
Narrator: "Imagine knowing the move before it happens."
[Visual: Showing {company} dashboard]
Narrator: "Unlock your potential with {company} today."
"""
        elif "SOCIAL PROOF" in prompt:
            return f"""[Visual: Discord chat scrolling quickly]
Narrator: "Join thousands of members who are already seeing results."
[Visual: Showing {company} dashboard]
Narrator: "{company} gives you real-time alerts, daily pre-market prep, and a community that actually shares what works."
"""
        else:
            return """# Ad Script — Social Proof Angle

## Script
[Visual: Screen showing an active trading community chat feed with members posting alerts.]
Narrator (Voiceover): "Thousands of retail traders have ditched expensive gurus and switched to community-powered intelligence."
[Visual: Pre-market chart analysis on screen with CWT branding.]
Narrator: "CrowdWisdomTrading gives you real-time alerts, daily pre-market prep, and a community of traders who actually share what works."
[Visual: Price card: $49/mo — no long-term contracts.]
Narrator: "All for $49 a month. No lock-in. Cancel any time."
[Visual: CTA button reads 'Join the Community Now'.]

---
**Compliance note:** This script contains no named customer testimonials or specific performance claims.
Before production, insert verified member quotes sourced from real, consented CWT members.
Trading contains substantial risk. Past performance is not indicative of future results.
"""

    # --- 10. Content repurposing ---
    elif "extract the 3-5 most quotable" in combined:
        return """1. The video discusses the importance of risk management.
2. The video argues that position sizing is critical for funded accounts."""
        
    elif "three platform-native assets" in combined:
        return """## X Thread
1/ Most retail day traders fail because they don't have a plan. Here's a simple 3-step checklist to save your account...

## LinkedIn Post
Trading is a business, not a gamble. Proper risk management means never risking more than 1% per trade...

## Short-Form Video Script
[Visual: Text reads 'Rule #1 of Day Trading']
Speaker: "Never risk more than 1%. If you do, you're gambling..."
"""

    elif "1-week posting calendar" in combined:
        return """| Day | Platform | Asset | Best Time |
|---|---|---|---|
| Monday | Twitter | X Thread | 9:00 AM |
| Wednesday | LinkedIn | LinkedIn Post | 10:00 AM |
| Friday | TikTok | Short-Form Video Script | 12:00 PM |
"""

    # --- 11. Competitor names (broadest — checked LAST) ---
    elif "warrior trading" in combined:
        return """### Warrior Trading
- **Overview:** Warrior Trading is a massive trading-education platform led by Ross Cameron. It focuses heavily on momentum day trading, small cap stocks, and high-frequency execution.
- **Pricing Model:** High pricing tier. Mentoring & simulator bundles cost $997 to $4,297 per year depending on the tier.
- **Pros:** Extremely detailed technical courses, live trading room, robust proprietary simulator.
- **Cons:** Very expensive, high-pressure marketing, strategy requires high risk tolerance and rapid execution."""
    elif "bullish bears" in combined:
        return """### Bullish Bears
- **Overview:** Bullish Bears offers low-cost trading courses, trade rooms, and Discord chat alerts for retail traders.
- **Pricing Model:** Low pricing tier. Subscription is $47/mo or $397/yr.
- **Pros:** Very affordable, supportive community environment, covers many trading styles (options, swings, day).
- **Cons:** Less advanced proprietary tools, strategies are broad and less specialized."""
    elif "the trading channel" in combined:
        return """### The Trading Channel
- **Overview:** Run by Steven Hart, focusing on retail forex and swing trading education.
- **Pricing Model:** Medium pricing tier, courses start at $297.
- **Pros:** High-quality free content on YouTube, solid foundation in technical analysis.
- **Cons:** Upsells to expensive course materials, focus is primarily on indicators."""
    elif "investors underground" in combined:
        return """### Investors Underground
- **Overview:** One of the oldest chatrooms, focusing on day trading momentum and swings.
- **Pricing Model:** High monthly cost ($297/mo or $1,897/yr).
- **Pros:** High-quality webinar archives, seasoned moderators, focus on trading fundamentals.
- **Cons:** Chat can be overwhelming for beginners, high price barrier."""
    elif "fundednext" in combined:
        return """### FundedNext
- **Overview:** A leading prop firm that offers evaluation accounts for traders seeking funded capital.
- **Pricing Model:** Medium pricing tier, evaluation fees starting around $99 for $6k accounts up to $1k+ for larger accounts.
- **Pros:** Profit share during assessment, realistic drawdown rules, 24/7 support.
- **Cons:** Strict drawdown rules can be hard to pass, profit targets require high performance."""

    # --- 12. Default ---
    else:
        return "Demo response helper: default stub response."


def chat(messages: list[dict], temperature: float = 0.7, max_tokens: int = 1200) -> str:
    global _rotation_idx
    if os.getenv("DEMO_MODE") == "true":
        return get_demo_response(messages)

    provider = os.getenv("LLM_PROVIDER", "openrouter")
    cfg = _PROVIDERS[provider]
    api_key = os.getenv(cfg["key_env"]) if cfg["key_env"] else "ollama"
    model = os.getenv(cfg["model_env"])

    if cfg["key_env"] and not api_key:
        raise RuntimeError(f"{cfg['key_env']} not set in .env")

    headers = {"Content-Type": "application/json"}
    if api_key != "ollama":
        headers["Authorization"] = f"Bearer {api_key}"

    for attempt in range(MAX_RETRIES):
        payload = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        resp = _call_api(cfg["url"], headers, payload)

        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"]

        if resp.status_code == 429:
            # Read Retry-After header (seconds to wait)
            retry_after = int(resp.headers.get("Retry-After", "30"))
            # Cap at 60s to avoid endless waits
            wait_time = min(retry_after + 2, 60)

            # Rotate model for next attempt
            if provider == "openrouter":
                _rotation_idx = (_rotation_idx + 1) % len(_FREE_MODELS)
                model = _FREE_MODELS[_rotation_idx]

            print(f"  [LLM] 429 rate limited. Waiting {wait_time}s, then trying {model} (attempt {attempt+2}/{MAX_RETRIES})")
            time.sleep(wait_time)
            continue

        # Other errors — raise immediately
        resp.raise_for_status()

    # All retries exhausted on cloud — try Ollama as fallback if available
    if provider != "ollama":
        ollama_model = os.getenv("OLLAMA_MODEL")
        if ollama_model:
            print(f"  [LLM] Cloud exhausted, falling back to Ollama ({ollama_model})")
            try:
                fallback_resp = _call_api(
                    "http://localhost:11434/v1/chat/completions",
                    {"Content-Type": "application/json"},
                    {"model": ollama_model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens},
                )
                if fallback_resp.status_code == 200:
                    return fallback_resp.json()["choices"][0]["message"]["content"]
            except Exception:
                pass  # Ollama not running, fall through to error

    raise RuntimeError(f"LLM failed after {MAX_RETRIES} attempts (rate limited). Try again in a few minutes or use LLM_PROVIDER=ollama.")


def ask(system_prompt: str, user_prompt: str, **kwargs) -> str:
    return chat(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        **kwargs,
    )
