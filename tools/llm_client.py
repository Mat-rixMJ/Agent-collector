"""LLM client. Supports OpenRouter, NVIDIA build, and local Ollama.
All expose OpenAI-compatible /chat/completions endpoints, so one thin wrapper
covers all — just swap LLM_PROVIDER in .env.
"""
import os

import requests
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

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


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=20))
def chat(messages: list[dict], temperature: float = 0.7, max_tokens: int = 1200) -> str:
    provider = os.getenv("LLM_PROVIDER", "openrouter")
    cfg = _PROVIDERS[provider]
    api_key = os.getenv(cfg["key_env"]) if cfg["key_env"] else "ollama"
    model = os.getenv(cfg["model_env"])
    if cfg["key_env"] and not api_key:
        raise RuntimeError(f"{cfg['key_env']} not set in .env")

    headers = {"Content-Type": "application/json"}
    if api_key != "ollama":
        headers["Authorization"] = f"Bearer {api_key}"

    resp = requests.post(
        cfg["url"],
        headers=headers,
        json={"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def ask(system_prompt: str, user_prompt: str, **kwargs) -> str:
    return chat(
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
        **kwargs,
    )
