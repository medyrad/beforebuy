_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def _toman(value: int) -> str:
    return f"{value:,}".translate(_DIGITS).replace(",", "٬")


def deterministic_headline(result) -> str:
    outcome = result.primary_outcome
    if outcome == "BUDGET_MISMATCH":
        return "قیمت واردشده از بودجهٔ شما بیشتر است؛ نیاز به خرید و مناسب‌بودن این مدل جداگانه بررسی شده‌اند."
    if outcome == "PHONE_PURCHASE_JUSTIFIED_WITHIN_BUDGET":
        text = "با توجه به وضعیت گوشی فعلی و فایده‌ای که گفته‌اید، خرید یا تعویض گوشی برای شما قابل توجیه و در بودجه است."
    elif outcome == "PHONE_PURCHASE_JUSTIFIED_BUDGET_UNKNOWN":
        text = "با توجه به وضعیت گوشی فعلی و فایده‌ای که گفته‌اید، خرید یا تعویض گوشی قابل توجیه است؛ بودجه هنوز روشن نیست."
    elif outcome == "DISCRETIONARY_CHOICE_WITHIN_BUDGET":
        text = "این خرید برای شما یک انتخاب شخصی روشن و در محدودهٔ بودجه است."
    elif outcome == "DISCRETIONARY_CHOICE_BUDGET_UNKNOWN":
        text = "این خرید برای شما یک انتخاب شخصی روشن است؛ بودجه هنوز مشخص نشده است."
    elif outcome == "RECONSIDER_OR_WAIT":
        text = "پاسخ‌های فعلی بیشتر از خرید فوری، بازنگری یا کمی صبر را پشتیبانی می‌کنند."
    else:
        text = "پاسخ‌های فعلی برای یک جمع‌بندی قطعی دربارهٔ دلیل خرید کافی یا یکدست نیستند."
    if "TARGET_MODEL_CAPABILITY" in result.unknowns:
        text += " مناسب‌بودن این مدل برای نیاز شما هنوز تأیید نشده است."
    return text


_CURRENT_DEVICE = {
    "UNUSABLE": "گفته‌اید گوشی فعلی دیگر قابل استفاده نیست.",
    "SERIOUS_PROBLEM": "گفته‌اید گوشی فعلی مشکل جدی دارد.",
    "MINOR_ISSUES": "گفته‌اید گوشی فعلی فقط چند مشکل محدود دارد.",
    "WORKS_WELL": "گفته‌اید گوشی فعلی هنوز خوب کار می‌کند.",
}
_BENEFIT = {
    "RESTORE_ESSENTIAL_ACCESS": "هدف شما برگرداندن دسترسی ضروری است.",
    "SOLVE_MAJOR_LIMIT": "هدف شما برطرف‌کردن یک محدودیت مهم است.",
    "ENABLE_IMPORTANT_NEW_USE": "این خرید برای یک استفادهٔ تازه و مهم در نظر گرفته شده است.",
    "PERSONAL_ENJOYMENT": "هدف اعلام‌شدهٔ شما لذت شخصی از انتخاب تازه است.",
    "NO_CLEAR_BENEFIT": "در پاسخ‌ها فایدهٔ روشنی برای خرید مشخص نشده است.",
    "UNKNOWN": "فایدهٔ مورد انتظار هنوز روشن نیست.",
}


def deterministic_reason_blocks(result) -> list[dict]:
    by_type = {item["type"]: item for item in result.evidence}
    blocks = []
    for evidence_type, labels in (("CURRENT_DEVICE_STATE", _CURRENT_DEVICE), ("EXPECTED_BENEFIT", _BENEFIT)):
        item = by_type.get(evidence_type)
        if item and item.get("value") in labels:
            blocks.append({"kind": "deterministic_reason", "text_fa": labels[item["value"]], "evidence_ids": [item["id"]], "rule_ids": []})
    price = by_type.get("PURCHASE_PRICE")
    budget = by_type.get("STATED_BUDGET")
    if price and budget and isinstance(price.get("value"), int) and isinstance(budget.get("value"), int):
        relation = "در محدودهٔ" if result.dimensions["budget"] == "WITHIN_BUDGET" else "بالاتر از"
        blocks.append({
            "kind": "deterministic_reason",
            "text_fa": f"قیمت {_toman(price['value'])} تومان است و {relation} بودجهٔ {_toman(budget['value'])} تومان قرار می‌گیرد.",
            "evidence_ids": [price["id"], budget["id"]],
            "rule_ids": [rule for rule in result.matched_rule_ids if rule.startswith("BUD-")],
        })
    elif budget and budget.get("value") == "UNKNOWN":
        blocks.append({
            "kind": "deterministic_reason",
            "text_fa": "بودجه را نامعلوم ثبت کرده‌اید؛ بنابراین تناسب قیمت با بودجه محاسبه نشده است.",
            "evidence_ids": [budget["id"]],
            "rule_ids": [rule for rule in result.matched_rule_ids if rule.startswith("BUD-")],
        })
    return blocks
