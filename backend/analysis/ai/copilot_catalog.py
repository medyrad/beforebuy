"""Documentation metadata, not an account availability or quality claim."""
CATALOG = {'gpt-6-luna': {
    'id': 'gpt-6-luna', 'responses': True, 'streaming': True, 'structured_output': True, 'image_input': True,
    'context_tokens': 1050000, 'max_output_tokens': 128000, 'verified_on': '2026-11-15',
    'input_usd_per_million': '0.10', 'output_usd_per_million': '0.50',
    'cached_input_usd_per_million': '0.01', 'cache_write_12h_usd_per_million': '0.25',
    'source': 'https://developers.openai.com/api/docs/models/gpt-6-luna'}}


def discover_models(account_ids, *, saved_model):
    supported = [m for m in CATALOG.values() if all(m.get(k) for k in
        ('responses', 'streaming', 'structured_output', 'image_input', 'input_usd_per_million', 'output_usd_per_million'))]
    items = supported if account_ids is None else [m for m in supported if m['id'] in account_ids]
    available = any(m['id'] == saved_model for m in items)
    return {'items': items, 'source': 'DOCUMENTATION_UNVERIFIED' if account_ids is None else 'ACCOUNT_INTERSECTION',
            'saved_status': 'UNAVAILABLE' if not available else 'ACCOUNT_UNVERIFIED' if account_ids is None else 'AVAILABLE'}
