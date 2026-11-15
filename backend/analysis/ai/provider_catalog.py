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

CATALOGS = {"gapgpt": GAPGPT_CATALOG, "openai": OPENAI_CATALOG}
DEFAULT_MODELS = {"gapgpt": GAPGPT_MODEL, "openai": "gpt-6-luna"}


def catalog_for(provider, saved_model):
    catalog = CATALOGS.get(provider, {})
    return {"items": list(catalog.values()), "source": "DOCUMENTATION_UNVERIFIED",
            "saved_status": "ACCOUNT_UNVERIFIED" if saved_model in catalog else "UNAVAILABLE"}
