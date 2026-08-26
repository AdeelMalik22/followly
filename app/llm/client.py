from openai import OpenAI
from .config import load_llm_config

_client_cache = {}

def get_llm_client():
    cfg = load_llm_config()
    key = (cfg.provider, cfg.model)
    if key not in _client_cache:
        _client_cache[key] = (
            OpenAI(api_key=cfg.api_key, base_url=cfg.base_url) if cfg.base_url
            else OpenAI(api_key=cfg.api_key),
            cfg.model,
        )
    return _client_cache[key]

def chat(messages: list[dict], tools=None, **kwargs):
    client, model = get_llm_client()
    params = {"model": model, "messages": messages, **kwargs}
    if tools:
        params["tools"] = tools
    return client.chat.completions.create(**params)
