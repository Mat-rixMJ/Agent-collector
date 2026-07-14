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

import requests
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
        "pain_point": "Beginner day traders lose money copying alerts from expensive gurus with no plan.",
        "hook": "Your guru is charging $297/mo and you are still in the red. There is a better way.",
        "offer_mechanism": "Crowd-sourced trading intelligence and pre-market analysis for $49/mo.",
        "cta": "Join CrowdWisdomTrading for $49/mo",
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
        "offer_mechanism": "Pre-market watchlist and alert service so you never miss a move, for $49/mo.",
        "cta": "Get alerts on your phone",
        "notes": "Time-scarcity angle targeting employed traders."
    },
    {
        "pain_point": "Crypto traders jump between strategies and never build consistent results.",
        "hook": "Consistency beats brilliance in crypto. Here is the repeatable system top traders use.",
        "offer_mechanism": "Daily crypto market bias and community-verified setups for $49/mo.",
        "cta": "Join the CWT crypto community",
        "notes": "Consistency angle for crypto-crossover audience."
    },
    {
        "pain_point": "Traders waste hours watching YouTube instead of having a clear market bias before open.",
        "hook": "Stop spending your morning on YouTube. Get a clear directional bias in 5 minutes.",
        "offer_mechanism": "CWT pre-market report and bias summary delivered to Telegram by 8am for $49/mo.",
        "cta": "Get your morning edge",
        "notes": "Time efficiency angle for morning routine improvement."
    },
    {
        "pain_point": "Funded traders fail to scale because they do not have a risk-adjusted position sizing system.",
        "hook": "Passing the challenge is step one. Keeping the account is the real test.",
        "offer_mechanism": "Post-funding position sizing guidance and community support for $49/mo.",
        "cta": "Protect your funded account",
        "notes": "Post-challenge retention angle for funded traders."
    },
    {
        "pain_point": "Retail traders ignore the news and get blindsided by earnings and macro events.",
        "hook": "Macro events move markets. Most retail traders find out after the fact.",
        "offer_mechanism": "Weekly macro calendar and event-driven trade ideas delivered via Telegram for $49/mo.",
        "cta": "Trade the news, not the reaction",
        "notes": "Macro awareness angle for fundamentals-interested traders."
    },
    {
        "pain_point": "Solo traders feel isolated and have no one to review their trades or strategy with.",
        "hook": "Trading alone is hard. Trading with 5,000 people who share your setups is better.",
        "offer_mechanism": "Active Discord trading community with daily shared setups and peer review for $49/mo.",
        "cta": "Join the community",
        "notes": "Isolation angle with community belonging as the hook."
    },
    {
        "pain_point": "Algorithmic trading beginners buy expensive bots that lose money on live accounts.",
        "hook": "Most retail trading bots are backtested on history they will never see again.",
        "offer_mechanism": "Human-curated alerts that beat algo noise for $49/mo.",
        "cta": "Ditch the bot. Trade with intelligence.",
        "notes": "Anti-algo angle for bot-skeptic audience."
    },
    {
        "pain_point": "Traders get faked out by false breakouts because they trade without volume context.",
        "hook": "Volume does not lie. Price action without volume is just noise.",
        "offer_mechanism": "Volume-confirmed breakout alerts and pre-market analysis for $49/mo.",
        "cta": "Trade breakouts with confidence",
        "notes": "Volume analysis angle for technical traders."
    },
    {
        "pain_point": "Traders keep journaling but never identify the actual patterns causing their losses.",
        "hook": "You have a journal. You still lose. The pattern is not in the entries.",
        "offer_mechanism": "Community trade review sessions and pattern coaching calls for $49/mo.",
        "cta": "Find your edge with us",
        "notes": "Journaling-frustration angle targeting self-improvement-focused traders."
    },
    {
        "pain_point": "Day traders overtrade during low-volume sessions and give back all their gains.",
        "hook": "The best trade is sometimes no trade. But knowing which session to skip requires data.",
        "offer_mechanism": "Session quality scores and optimal trading window alerts for $49/mo.",
        "cta": "Trade only the A-grade setups",
        "notes": "Overtrading prevention angle for experienced but losing traders."
    },
    {
        "pain_point": "Traders spend more on courses than they make in their first year of trading.",
        "hook": "You spent $2,000 on courses. You lost $3,000 trading. Something has to change.",
        "offer_mechanism": "One affordable community membership that replaces five expensive courses for $49/mo.",
        "cta": "Stop buying courses. Start trading.",
        "notes": "Course-fatigue angle targeting over-educated under-performing traders."
    },
    {
        "pain_point": "Prop firm candidates fail the evaluation because their risk management breaks under pressure.",
        "hook": "You know the rules. You break them when it matters. That is the real problem.",
        "offer_mechanism": "Accountability partner system and daily risk check-in community for $49/mo.",
        "cta": "Pass your next challenge",
        "notes": "Accountability angle for repeat prop firm challenge takers."
    },
    {
        "pain_point": "Traders chase momentum and buy tops because they have no systematic entry criteria.",
        "hook": "Buying the top is not a strategy. It is a symptom of having no system.",
        "offer_mechanism": "Rule-based entry alert system with community confirmation for $49/mo.",
        "cta": "Get a real system",
        "notes": "FOMO/chasing angle for impulsive traders."
    },
    {
        "pain_point": "Experienced traders plateau and cannot figure out why their edge has stopped working.",
        "hook": "You used to be profitable. The market changed. Your system did not.",
        "offer_mechanism": "Monthly strategy adaptation workshops and live market analysis for $49/mo.",
        "cta": "Adapt your edge with CWT",
        "notes": "Plateauing experienced trader angle for advanced audience."
    },
]


def _call_api(url: str, headers: dict, payload: dict) -> requests.Response:
    """Single API call with timeout."""
    return requests.post(url, headers=headers, json=payload, timeout=300)


def get_demo_response(messages: list[dict]) -> str:
    prompt = messages[-1]["content"] if messages else ""
    sys_prompt = messages[0]["content"] if len(messages) > 1 and messages[0]["role"] == "system" else ""
    combined = (sys_prompt + "\n" + prompt).lower()

    if "warrior trading" in combined:
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
    elif "synthesis" in combined or "synthesize" in combined:
        return """# Competitive Strategy & Gap Analysis

## Market Gaps
1. **Affordable Entry-Level Subscriptions:** Competitors charge high annual fees ($997+) or expensive monthly rates ($297+). There is a massive gap for a low-cost, high-value monthly option at $49/mo.
2. **Community-First Learning:** Many platforms are centered around a single guru. Building a decentralized, peer-to-peer sharing community offers a unique value proposition.
3. **Unbiased Strategy Reviews:** Competitors promote their own indicator systems. CrowdWisdomTrading can stand out by providing transparent, crowd-sourced trading alerts."""
    elif "strategy brief" in combined or "brand profile" in combined:
        return """# Marketing Strategy Brief: CrowdWisdomTrading

## 1. Brand Positioning
CrowdWisdomTrading (CWT) is the ultimate community-driven retail trading hub. We offer real-time trading alerts, daily pre-market analysis, and educational resources for just $49/mo, contrasting sharply with high-cost competitor plans.

## 2. Target Audience
Retail traders, forex enthusiasts, and prop firm evaluators looking for a collaborative, high-accuracy signaling community without paying thousands of dollars in upfront fees.

## 3. Compliance Notice
All marketing materials must state: *Trading contains substantial risk. Past performance is not indicative of future results. CrowdWisdomTrading is not a registered broker-dealer or financial advisor.*"""
    elif "classification filter" in combined or "yes or no" in combined or "coherence" in combined or "coherent" in combined:
        return "yes"
    elif "extract" in combined or "json" in combined:
        # A.2 fix: guarantee all 20 extracted ad concepts are distinct.
        # md5(prompt[:120]) collapsed because all 20 cached demo ads share the same
        # system prompt prefix, giving every call the same hash and thus the same concept.
        # A monotonic counter is the right approach in demo mode — ads are fixtures anyway,
        # so sequential assignment ensures distinct pain_points across all 20 concepts.
        _demo_extract_counter[0] = (_demo_extract_counter[0] + 1) % len(_CONCEPT_VARIANTS)
        chosen = _CONCEPT_VARIANTS[_demo_extract_counter[0]]
        return json.dumps(chosen)
    elif "angle" in combined or "script" in combined:
        if "fear" in combined:
            return """# Ad Script — Fear & Loss Aversion Angle

## Script
[Visual: A close-up of a trader staring at a red chart, looking stressed.]
Narrator (Voiceover): "Are you tired of blowing trading accounts? Watching your hard-earned cash disappear on failed prop challenges?"
[Visual: Text on screen reads: '$297/mo? Not anymore.']
Narrator: "Stop paying gurus thousands. Join CrowdWisdomTrading. Real-time community alerts, support, and pre-market prep for just $49 a month."
[Visual: CTA button reads 'Claim Your Trial Now'.]
Narrator: "Click the link and stop trading alone."
"""
        elif "aspiration" in combined:
            return """# Ad Script — Aspiration & Gain Angle

## Script
[Visual: A trader waking up, opening a laptop, and looking satisfied at a blue chart.]
Narrator (Voiceover): "Imagine trading with a global community of experts backing your every play."
[Visual: Screen shows real-time chat alerts and support signals.]
Narrator: "No expensive memberships. Just $49 a month for institutional-grade market prep and high-accuracy alerts."
[Visual: CTA button reads 'Join the Crowd'].
Narrator: "Unlock your potential with CrowdWisdomTrading today."
"""
        else:
            # A.3 fix: removed fabricated named customer quotes ("Trader 1: ...") and
            # unverified specific membership count (10,000+). These are FTC-regulated
            # claim categories. Replaced with generic community language that doesn't
            # assert specific unverified facts. Real testimonials must be inserted from
            # a verified-claims source before production use.
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
    elif "score" in combined or "rubric" in combined:
        # A.4 fix: differentiate between two callers that both contain "score":
        #   1. score_ad_scripts.score_script() — asks for JSON with keys hook, pain, etc.
        #      SCORING_PROMPT says "Output as clean JSON" → return a JSON score dict.
        #   2. generate_pdf_report / summary context → return the Markdown scorecard table.
        if "output as clean json" in combined or ("hook" in combined and "pain" in combined and "mechanism" in combined):
            # Individual per-script scoring call — return parseable JSON
            import random as _random
            _seed = abs(hash(prompt[:80])) % 10
            total = 28 + _seed  # Range 28-37 — realistic spread across scripts
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
        # Summary scorecard context — return Markdown table with real filenames
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
        return """# Ad Script — Revised Version

## Script
[Visual: A trader looking at a chart, then opening the CrowdWisdomTrading dashboard.]
Narrator (Voiceover): "Blowing trading accounts? Guru fees are eating your profits. Let's change that."
Narrator: "Get institutional-grade pre-market analysis and real-time alerts. All for just $49 a month."
"""
    elif "outreach" in combined or "email" in combined or "dm" in combined:
        return """# Cold Outreach Draft

## Email Version
Subject: Sponsored segment proposal / Affiliate partnership with CrowdWisdomTrading

Hi [Creator],
We love your channel. We want to propose a paid sponsorship segment ($500 base rate + 30% affiliate commission) to showcase CWT to your audience.

## Direct Message (DM) Version
Hey [Creator], love your recent video on prop firm challenges! We'd love to partner with you for a sponsored segment on your channel. We pay a competitive base rate plus affiliate commissions. Drop us an email if interested!
"""
    elif "repurpose" in combined or "calendar" in combined or "linkedin" in combined or "twitter" in combined:
        return """# Repurposed Content Calendar Item

## X Thread
1/ Most retail day traders fail because they don't have a plan. Here's a simple 3-step checklist to save your account...

## LinkedIn Post
Trading is a business, not a gamble. Proper risk management means never risking more than 1% per trade...

## Short-Form Video Script
[Visual: Text reads 'Rule #1 of Day Trading']
Speaker: "Never risk more than 1%. If you do, you're gambling..."
"""
    elif "executive summary" in combined or "funnel" in combined or "ingestion" in combined:
        return """We successfully conducted competitive research across 5 major trading-education platforms, identifying pricing and positioning gaps for CrowdWisdomTrading's launch.

By analyzing raw ad concepts, we created 3 optimized ad script variants targeting pain points in prop challenges, scored and refined for maximum conversions.

Finally, we identified 74 high-potential influencer partners and created targeted outreach campaigns to accelerate brand adoption."""
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
