from dataclasses import dataclass
import os

@dataclass
class LLMConfig:
    provider: str
    model: str
    api_key: str
    base_url: str | None = None

PROVIDER_DEFAULTS = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "model_env": "OPENROUTER_MODEL",
        "default_model": "meta-llama/llama-3.1-8b-instruct:free",
    },
    "openai": {
        "base_url": None,
        "key_env": "OPENAI_API_KEY",
        "model_env": "OPENAI_MODEL",
        "default_model": "gpt-4o-mini",
    },
    "anthropic": {
        "base_url": None,
        "key_env": "ANTHROPIC_API_KEY",
        "model_env": "ANTHROPIC_MODEL",
        "default_model": "claude-sonnet-4-5",
    },
}

def load_llm_config() -> LLMConfig:
    provider = os.environ.get("LLM_PROVIDER", "openrouter").lower()
    if provider not in PROVIDER_DEFAULTS:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}")

    cfg = PROVIDER_DEFAULTS[provider]
    api_key = os.environ.get(cfg["key_env"])
    if not api_key:
        raise RuntimeError(f"Missing {cfg['key_env']} in environment")

    model = os.environ.get(cfg["model_env"], cfg["default_model"])
    return LLMConfig(provider=provider, model=model, api_key=api_key, base_url=cfg["base_url"])
