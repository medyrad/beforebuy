from unittest import TestCase

from analysis.research.identity import IdentityConflict, VariantIdentity, reconcile_variant


class VariantIdentityTests(TestCase):
    def test_exact_identifier_and_attributes_match(self):
        left = VariantIdentity("Samsung", "Galaxy A56", {"mpn": "SM-A566B"}, {"capacity_gb": 256, "ram_gb": 8, "region": "GLOBAL"}, False, "NEW")
        right = VariantIdentity("samsung", "Galaxy A56 5G", {"mpn": "SM-A566B"}, {"capacity_gb": 256, "ram_gb": 8, "region": "GLOBAL"}, False, "NEW")
        self.assertEqual(reconcile_variant(left, right).status, "MATCH")

    def test_region_capacity_bundle_warranty_condition_and_identifier_conflicts_do_not_merge(self):
        base = VariantIdentity("Samsung", "Galaxy A56", {"mpn": "SM-A566B"}, {"capacity_gb": 256, "region": "GLOBAL", "warranty": "18m"}, False, "NEW")
        conflicts = [
            VariantIdentity("Samsung", "Galaxy A56", {"mpn": "OTHER"}, base.attributes, False, "NEW"),
            VariantIdentity("Samsung", "Galaxy A56", base.identifiers, base.attributes | {"capacity_gb": 128}, False, "NEW"),
            VariantIdentity("Samsung", "Galaxy A56", base.identifiers, base.attributes | {"region": "VN"}, False, "NEW"),
            VariantIdentity("Samsung", "Galaxy A56", base.identifiers, base.attributes, True, "NEW"),
            VariantIdentity("Samsung", "Galaxy A56", base.identifiers, base.attributes | {"warranty": "none"}, False, "NEW"),
            VariantIdentity("Samsung", "Galaxy A56", base.identifiers, base.attributes, False, "REFURBISHED"),
        ]
        for candidate in conflicts:
            with self.subTest(candidate=candidate), self.assertRaises(IdentityConflict):
                reconcile_variant(base, candidate)

    def test_similar_names_without_shared_identifier_are_ambiguous(self):
        left = VariantIdentity("Nike", "Run Swift 3", {}, {"size": "42"}, False, "NEW")
        right = VariantIdentity("Nike", "Run Swift III", {}, {"size": "42"}, False, "NEW")
        self.assertEqual(reconcile_variant(left, right).status, "AMBIGUOUS")
