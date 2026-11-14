import re


PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
GROUPING = {",", "٬", " "}


class MoneyValidationError(ValueError):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def normalize_toman(value, *, allow_zero: bool) -> int:
    if isinstance(value, bool):
        raise MoneyValidationError("MALFORMED_AMOUNT")
    if isinstance(value, int):
        amount = value
    else:
        raw = str(value).strip()
        if any(ch.isalpha() for ch in raw):
            if re.search(r"[eE]", raw) and re.fullmatch(r"[۰-۹0-9]+[eE][+-]?[۰-۹0-9]+", raw):
                raise MoneyValidationError("SCIENTIFIC_NOTATION")
            raise MoneyValidationError("AMBIGUOUS_CURRENCY")
        if raw.startswith("-"):
            raise MoneyValidationError("NEGATIVE_AMOUNT")
        if "." in raw:
            raise MoneyValidationError("DECIMAL_AMOUNT")
        has_persian = bool(re.search(r"[۰-۹]", raw))
        has_latin = bool(re.search(r"[0-9]", raw))
        if has_persian and has_latin:
            raise MoneyValidationError("MIXED_GROUPING")
        normalized = raw.translate(PERSIAN_DIGITS)
        separators = {ch for ch in normalized if ch in GROUPING}
        if len(separators) > 1:
            raise MoneyValidationError("MIXED_GROUPING")
        if separators:
            separator = next(iter(separators))
            parts = normalized.split(separator)
            if not parts[0].isdigit() or not 1 <= len(parts[0]) <= 3 or any(
                len(part) != 3 or not part.isdigit() for part in parts[1:]
            ):
                raise MoneyValidationError("MALFORMED_AMOUNT")
            normalized = "".join(parts)
        if not normalized.isascii() or not normalized.isdigit():
            raise MoneyValidationError("MALFORMED_AMOUNT")
        amount = int(normalized)
    if amount < 0:
        raise MoneyValidationError("NEGATIVE_AMOUNT")
    if amount == 0 and not allow_zero:
        raise MoneyValidationError("NON_POSITIVE_PRICE")
    return amount


def normalize_budget(value) -> int | None:
    if value is None or value == "UNKNOWN":
        return None
    return normalize_toman(value, allow_zero=True)
