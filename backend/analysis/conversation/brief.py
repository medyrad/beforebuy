import re

from rest_framework.exceptions import ValidationError


_DIGIT_TRANSLATION = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_LIST_FIELDS = {"use_cases": 200, "hard_constraints": 200, "unknowns": 200, "contradictions": 300}
_TEXT_FIELDS = {"category": 120, "selected_product_label": 160}


def normalize_digits(value: str) -> str:
    return value.translate(_DIGIT_TRANSLATION)


def normalize_money_toman(value):
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ValidationError("بودجه نامعتبر است.")
    if isinstance(value, int):
        if value < 0:
            raise ValidationError("بودجه منفی نیست.")
        return value
    normalized = normalize_digits(str(value))
    digits = re.sub(r"[\s,٬،_تومان]", "", normalized)
    if not digits.isdigit():
        raise ValidationError("بودجه باید عدد صحیح تومان باشد.")
    return int(digits)


def validate_brief_changes(changes: dict) -> dict:
    if not isinstance(changes, dict) or not changes:
        raise ValidationError("حداقل یک تغییر لازم است.")
    allowed = {"recipient_context", "category", "selected_product_label", "budget_toman", *_LIST_FIELDS}
    unknown = set(changes) - allowed
    if unknown:
        raise ValidationError({key: ["فیلد پشتیبانی نمی‌شود."] for key in sorted(unknown)})
    result = {}
    if "recipient_context" in changes:
        value = changes["recipient_context"]
        if value not in {None, "SELF", "GIFT", "HOUSEHOLD"}:
            raise ValidationError({"recipient_context": ["مقدار نامعتبر است."]})
        result["recipient_context"] = value
    if "budget_toman" in changes:
        result["budget_toman"] = normalize_money_toman(changes["budget_toman"])
    for field, limit in _TEXT_FIELDS.items():
        if field in changes:
            value = changes[field]
            if value is not None:
                value = str(value).strip()
                if not value or len(value) > limit:
                    raise ValidationError({field: ["طول مقدار نامعتبر است."]})
            result[field] = value
    for field, item_limit in _LIST_FIELDS.items():
        if field in changes:
            values = changes[field]
            if not isinstance(values, list) or len(values) > 20:
                raise ValidationError({field: ["حداکثر ۲۰ مورد مجاز است."]})
            clean = [str(item).strip() for item in values]
            if any(not item or len(item) > item_limit for item in clean):
                raise ValidationError({field: [f"هر مورد باید ۱ تا {item_limit} نویسه باشد."]})
            result[field] = clean
    return result
