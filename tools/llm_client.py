"""LLM client. Supports OpenRouter, NVIDIA build, and local Ollama.
All expose OpenAI-compatible /chat/completions endpoints.

Rate limit strategy:
- On 429, reads Retry-After header and sleeps that exact duration
- Rotates between free models to spread load
- 7 attempts with increasing backoff (covers ~3min of rate limiting)
- Falls back to Ollama if all cloud attempts fail
"""
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


def _call_api(url: str, headers: dict, payload: dict) -> requests.Response:
    """Single API call with timeout."""
    return requests.post(url, headers=headers, json=payload, timeout=300)


def chat(messages: list[dict], temperature: float = 0.7, max_tokens: int = 1200) -> str:
    global _rotation_idx
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
