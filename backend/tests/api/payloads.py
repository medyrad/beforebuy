def valid_analysis_payload(**overrides):
    payload = {
        "product_label": "گوشی نمونه",
        "price_toman": "۲۰٬۰۰۰٬۰۰۰",
        "budget_toman": "۲۵٬۰۰۰٬۰۰۰",
        "answers": {
            "Q-001": "UNUSABLE",
            "Q-002": "RESTORE_ESSENTIAL_ACCESS",
            "Q-003": ["GENERAL_USE"],
            "Q-004": "WITHIN_2_WEEKS",
            "Q-006": ["NONE"],
            "F-003": "NO_INFORMATION",
        },
    }
    payload.update(overrides)
    return payload
