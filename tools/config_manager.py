import json
import os
import re
from pathlib import Path

CONFIG_PATH = Path("data/config.json")
PROFILE_PATH = Path("data/company_profile.json")

def load_config() -> dict:
    """Loads the main configuration schema. 
    Falls back to environment variables and company_profile.json for backward compatibility."""
    
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"Error loading config.json: {e}")
            
    # Fallback legacy logic
    target_site = os.getenv("TARGET_SITE", "unknown")
    niche = os.getenv("NICHE", "unknown")
    
    profile = {}
    if PROFILE_PATH.exists():
        try:
            profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
            
    return {
        "company_name": profile.get("company_name", "Unknown Company"),
        "target_site": target_site,
        "niche": niche,
        "competitors": [],
        "youtube_search_queries": [],
        "meta_ads_search_queries": [],
        "verified_claims": profile.get("verified_claims", {}),
        "positioning_guidelines": profile.get("positioning_guidelines", ""),
        "hard_blocked_patterns": profile.get("hard_blocked_patterns", [])
    }

def _ask_llm_list(prompt: str, fallback_message: str) -> list[str]:
    """Helper to ask LLM and parse a JSON list from the response."""
    from tools.llm_client import ask
    
    try:
        response = ask(prompt, fallback_message)
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            items = json.loads(match.group(0))
            if isinstance(items, list) and len(items) > 0:
                return items[:5]
    except Exception as e:
        print(f"LLM operation failed: {e}")
    return []

def get_competitors(config: dict) -> list[str]:
    """Returns the list of competitors. If empty, uses LLM to discover them based on the niche."""
    competitors = config.get("competitors", [])
    if competitors:
        return competitors
        
    cache_path = Path("data/discovered_competitors.json")
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            pass
        
    print(f"No competitors configured. Using LLM to discover competitors for niche: '{config.get('niche')}'...")
    from tools.llm_client import ask
    prompt = (
        f"You are a marketing strategist. We are launching a new product in this niche: '{config.get('niche')}'. "
        f"Our target site is '{config.get('target_site')}'. "
        "Identify exactly 5 specific, direct competitors that target the same audience. "
        "Do NOT list broad categories or entirely different businesses. "
        "Return ONLY a JSON list of strings, for example: [\"Competitor 1\", \"Competitor 2\"]."
    )
    
    try:
        response = ask(prompt, "Please provide the 5 competitors as a JSON array of strings.")
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            comps = json.loads(match.group(0))
            if isinstance(comps, list) and len(comps) > 0:
                # Deduplicate based on normalized names
                deduped = []
                seen_normalized = set()
                for c in comps:
                    norm = re.sub(r'(?i)\b(academy|inc|com|\.com|llc)\b', '', str(c)).lower().strip()
                    if norm not in seen_normalized:
                        seen_normalized.add(norm)
                        deduped.append(c)
                
                final_comps = deduped[:5]
                print(f"LLM discovered competitors: {final_comps}")
                cache_path.write_text(json.dumps(final_comps), encoding="utf-8")
                return final_comps
    except Exception as e:
        print(f"LLM discovery failed: {e}")
        
    print("Falling back to generic placeholder competitors.")
    return ["Competitor A", "Competitor B"]

def get_youtube_queries(config: dict) -> list[str]:
    """Returns YouTube search queries. If empty, uses LLM to generate them based on the niche."""
    queries = config.get("youtube_search_queries", [])
    if queries:
        return queries
        
    cache_path = Path("data/youtube_queries.json")
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            pass
            
    print(f"No YouTube queries configured. Using LLM to generate queries for niche: '{config.get('niche')}'...")
    from tools.llm_client import ask
    prompt = (
        f"Generate exactly 5 YouTube search queries a person interested in '{config.get('niche')}' content would type into YouTube search. "
        "DO NOT use terms like 'influencers', 'creators', or 'channels'. We want topic-level searches (e.g. 'coding bootcamp review', 'learn to code'). "
        f"Must include the actual product category ({config.get('niche')}) as a hard filter, not a general vertical. "
        "Market context: Focus on India-relevant search terms (e.g., using terms popular in India). "
        "Return ONLY a JSON list of strings, for example: [\"query 1\", \"query 2\"]."
    )
    
    try:
        response = ask(prompt, "Please provide the 5 search queries as a JSON array of strings.")
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            q = json.loads(match.group(0))
            if isinstance(q, list) and len(q) > 0:
                print(f"LLM generated YouTube queries: {q[:5]}")
                cache_path.write_text(json.dumps(q[:5]), encoding="utf-8")
                return q[:5]
    except Exception as e:
        print(f"LLM query generation failed: {e}")
        
    return [config.get("niche", "general topics")]

def get_meta_ads_queries(config: dict) -> list[str]:
    """Returns Meta Ads search queries. If empty, uses LLM to generate them based on the niche."""
    queries = config.get("meta_ads_search_queries", [])
    if queries:
        return queries
        
    cache_path = Path("data/meta_ads_queries.json")
    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            pass
            
    print(f"No Meta Ads queries configured. Using LLM to generate queries for niche: '{config.get('niche')}'...")
    from tools.llm_client import ask
    prompt = (
        f"We need to find competitor ads on Facebook/Meta Ads Library in the exact niche: '{config.get('niche')}'. "
        f"Generate exactly 5 short search keywords to find competitor ads. Must include the actual product category ({config.get('niche')}) as a hard filter, not a general vertical. "
        "Market context: Target market is India. Default to India-region search intent. "
        "Return ONLY a JSON list of strings, for example: [\"keyword 1\", \"keyword 2\"]."
    )
    
    try:
        response = ask(prompt, "Please provide the 5 search keywords as a JSON array of strings.")
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            q = json.loads(match.group(0))
            if isinstance(q, list) and len(q) > 0:
                print(f"LLM generated Meta Ads queries: {q[:5]}")
                cache_path.write_text(json.dumps(q[:5]), encoding="utf-8")
                return q[:5]
    except Exception as e:
        print(f"LLM query generation failed: {e}")
        
    return [config.get("niche", "general topics")]
