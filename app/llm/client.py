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
    configured_fallbacks = [m.strip() for m in os.environ.get("LLM_FALLBACK_MODELS", "").split(",") if m.strip()]
    default_fallbacks = ["meta-llama/llama-3.1-8b-instruct:free"] if primary_model != "meta-llama/llama-3.1-8b-instruct:free" else []
    models = [primary_model] + configured_fallbacks + default_fallbacks
    retries = max(0, int(os.environ.get("LLM_MAX_RETRIES", "2")))
    last_error = None
    for model in models:
        for attempt in range(retries + 1):
            try:
                params = {"model": model, "messages": messages, **kwargs}
                if tools:
                    params["tools"] = tools
                response = client.chat.completions.create(**params)
                if not response.choices:
                    provider_error = getattr(response, "error", None)
                    detail = str(provider_error) if provider_error else "provider returned no choices"
                    error = RuntimeError(f"Invalid LLM response: {detail}")
                    error.status_code = provider_error.get("code") if isinstance(provider_error, dict) else None
                    raise error
                return response
            except Exception as exc:
                last_error = exc
                status_code = getattr(exc, "status_code", None)
                if status_code is None and "code': 502" in str(exc):
                    status_code = 502
                if status_code not in {408, 429, 500, 502, 503, 504}:
                    break
                if attempt < retries:
                    time.sleep(2 ** attempt)
    raise last_error
