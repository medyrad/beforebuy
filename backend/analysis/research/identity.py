from dataclasses import dataclass


class IdentityConflict(Exception):
    pass


@dataclass(frozen=True)
class VariantIdentity:
    brand: str
    model_name: str
    identifiers: dict
    attributes: dict
    bundle: bool
    condition: str


@dataclass(frozen=True)
class IdentityResult:
    status: str
    matched_identifier: str | None = None


def reconcile_variant(left, right):
    strong_identifiers = {"mpn", "gtin", "gtin13", "model_code"}
    common = set(left.identifiers) & set(right.identifiers) & strong_identifiers
    for key in common:
        if str(left.identifiers[key]).casefold() != str(right.identifiers[key]).casefold():
            raise IdentityConflict(f"identifier:{key}")
    if left.bundle != right.bundle:
        raise IdentityConflict("bundle")
    if left.condition != right.condition:
        raise IdentityConflict("condition")
    for key in {"capacity_gb", "ram_gb", "region", "size", "color", "warranty", "registration"}:
        if key in left.attributes and key in right.attributes and left.attributes[key] != right.attributes[key]:
            raise IdentityConflict(key)
    if common:
        return IdentityResult("MATCH", sorted(common)[0])
    return IdentityResult("AMBIGUOUS")
