import re
from pathlib import Path

import yaml
from django.test import SimpleTestCase
from django.urls import get_resolver


class CopilotOpenApiContractTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        path = Path(__file__).resolve().parents[3] / "specs/002-personalized-shopping-copilot/contracts/openapi.yaml"
        cls.document = yaml.safe_load(path.read_text(encoding="utf-8"))

    def resolve(self, schema):
        while "$ref" in schema:
            value = self.document
            for part in schema["$ref"].removeprefix("#/").split("/"):
                value = value[part]
            schema = value
        return schema

    def assert_example(self, schema, value, location):
        schema = self.resolve(schema)
        for part in schema.get("allOf", []):
            self.assert_example(part, value, location)
        expected = schema.get("type")
        if isinstance(expected, list):
            if value is None and "null" in expected:
                return
            expected = next(item for item in expected if item != "null")
        if expected == "object":
            self.assertIsInstance(value, dict, location)
            self.assertTrue(set(schema.get("required", [])) <= set(value), location)
            if schema.get("additionalProperties") is False:
                self.assertFalse(set(value) - set(schema.get("properties", {})), location)
            for key, item in value.items():
                if key in schema.get("properties", {}):
                    self.assert_example(schema["properties"][key], item, f"{location}.{key}")
        elif expected == "array":
            self.assertIsInstance(value, list, location)
            for item in value:
                self.assert_example(schema["items"], item, location)
        elif expected == "string":
            self.assertIsInstance(value, str, location)
        elif expected == "integer":
            self.assertIs(type(value), int, location)
        elif expected == "boolean":
            self.assertIs(type(value), bool, location)

    def test_contract_is_v31_versioned_and_operation_ids_are_unique(self):
        self.assertEqual(self.document["openapi"], "3.1.0")
        self.assertEqual(self.document["servers"], [{"url": "/api/v1"}])
        operations = [
            operation for item in self.document["paths"].values()
            for method, operation in item.items() if method in {"get", "post", "patch", "delete"}
        ]
        operation_ids = [operation["operationId"] for operation in operations]
        self.assertEqual(len(operation_ids), len(set(operation_ids)))

    def test_every_active_contract_path_has_an_implemented_route(self):
        patterns = get_resolver().url_patterns[0].url_patterns
        implemented = {
            re.sub(r"<uuid:[^>]+>", "{}", "/" + str(pattern.pattern).rstrip("/")) for pattern in patterns
        }
        for path in self.document["paths"]:
            normalized = re.sub(r"\{[^}]+\}", "{}", path)
            self.assertIn(normalized, implemented, path)

    def test_documented_examples_conform_to_their_schemas(self):
        checked = 0
        for path, item in self.document["paths"].items():
            for method, operation in item.items():
                if method not in {"get", "post", "patch", "delete"}:
                    continue
                for status, response in operation["responses"].items():
                    response = self.resolve(response)
                    for media, content in response.get("content", {}).items():
                        if "example" in content:
                            self.assert_example(content["schema"], content["example"], f"{method} {path} {status} {media}")
                            checked += 1
                        for named in content.get("examples", {}).values():
                            self.assert_example(content["schema"], named["value"], f"{method} {path} {status}")
                            checked += 1
        self.assertGreaterEqual(checked, 7)
