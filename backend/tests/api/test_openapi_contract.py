from pathlib import Path

import yaml
from django.test import SimpleTestCase
from django.urls import get_resolver


class OpenApiContractTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        contract = Path(__file__).resolve().parents[3] / "specs/001-purchase-decision-analysis/contracts/openapi.yaml"
        cls.document = yaml.safe_load(contract.read_text())

    def test_contract_is_openapi_31_with_unique_operation_ids(self):
        self.assertEqual(self.document["openapi"], "3.1.0")
        operation_ids = [
            operation["operationId"]
            for path in self.document["paths"].values()
            for method, operation in path.items()
            if method in {"get", "post", "patch", "put", "delete"}
        ]
        self.assertEqual(len(operation_ids), len(set(operation_ids)))

    def test_implemented_routes_match_contract_paths(self):
        contract_paths = set(self.document["paths"])
        resolver = get_resolver()
        api_patterns = resolver.url_patterns[0].url_patterns
        implemented = {"/" + str(pattern.pattern).replace("<uuid:analysis_id>", "{analysis_id}") for pattern in api_patterns}
        self.assertTrue(contract_paths <= implemented)

    def test_unsafe_operations_document_csrf_and_standard_errors(self):
        for path, path_item in self.document["paths"].items():
            for method in {"post", "patch", "put", "delete"} & set(path_item):
                operation = path_item[method]
                parameters = operation.get("parameters", [])
                self.assertIn({"$ref": "#/components/parameters/CsrfToken"}, parameters, f"{method} {path}")
                self.assertIn("403", operation["responses"], f"{method} {path}")
