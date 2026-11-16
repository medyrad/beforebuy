from .copilot_catalog import CATALOG as OPENAI_CATALOG

GAPGPT_MODEL = "gapgpt-deepseek-v4.1-flash"
GAPGPT_CATALOG = {GAPGPT_MODEL: {
    "id": GAPGPT_MODEL,
    "provider": "gapgpt",
    "protocol": "CHAT_COMPLETIONS",
    "streaming": True,
    "structured_output": False,
    "tool_output": False,
    "image_input": False,
    "input_usd_per_million": "0.15",
    "cached_input_usd_per_million": "0.015",
    "output_usd_per_million": "0.60",
    "verified_on": "2026-11-15",
    "source": "https://aigap.app/platform-v2/docs/models/deepseek-v4-1-flash-iran",
}}

OPENROUTER_MODEL = 'baidu/ernie-5.5-flash-preview:free'
OPENROUTER_CATALOG = {OPENROUTER_MODEL: {
    'id': OPENROUTER_MODEL, 'provider': 'openrouter', 'hosting_provider': 'baidu',
    'protocol': 'CHAT_COMPLETIONS', 'streaming': True, 'structured_output': True,
    'image_input': False, 'verified_on': '2026-11-16',
    'source': 'https://openrouter.ai/api/v1/models/baidu/ernie-5.5-flash-preview:free/endpoints',
    'readiness': 'TECHNICALLY_SUPPORTED_ACCOUNT_UNVERIFIED',
}}
CATALOGS = {"gapgpt": GAPGPT_CATALOG, "openai": OPENAI_CATALOG, 'openrouter': OPENROUTER_CATALOG}
DEFAULT_MODELS = {"gapgpt": GAPGPT_MODEL, "openai": "gpt-6-luna", 'openrouter': OPENROUTER_MODEL}


def catalog_for(provider, saved_model):
    catalog = CATALOGS.get(provider, {})
    return {"items": list(catalog.values()), "source": "DOCUMENTATION_UNVERIFIED",
            "saved_status": "ACCOUNT_UNVERIFIED" if saved_model in catalog else "UNAVAILABLE"}
