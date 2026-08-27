from openai import OpenAI
from .config import load_llm_config
import os
import time

_client_cache = {}

def get_llm_client():
    cfg = load_llm_config()
    key = (cfg.provider, cfg.model)
    if key not in _client_cache:
        _client_cache[key] = (
            OpenAI(api_key=cfg.api_key, base_url=cfg.base_url,
                   timeout=float(os.environ.get("LLM_TIMEOUT_SECONDS", "30"))) if cfg.base_url
            else OpenAI(api_key=cfg.api_key,
                        timeout=float(os.environ.get("LLM_TIMEOUT_SECONDS", "30"))),
            cfg.model,
        )
    return _client_cache[key]

def chat(messages: list[dict], tools=None, **kwargs):
    client, primary_model = get_llm_client()
    models = [primary_model] + [m.strip() for m in os.environ.get("LLM_FALLBACK_MODELS", "").split(",") if m.strip()]
    retries = max(0, int(os.environ.get("LLM_MAX_RETRIES", "2")))
    last_error = None
    for model in models:
        for attempt in range(retries + 1):
            try:
                params = {"model": model, "messages": messages, **kwargs}
                if tools:
                    params["tools"] = tools
                return client.chat.completions.create(**params)
            except Exception as exc:
                last_error = exc
                status_code = getattr(exc, "status_code", None)
                if status_code not in {408, 429, 500, 502, 503, 504}:
                    break
                if attempt < retries:
                    time.sleep(2 ** attempt)
    raise last_error
