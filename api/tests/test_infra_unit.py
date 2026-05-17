import pathlib
import re
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]


def read_infra(relative_path: str) -> str:
    return (ROOT / "infra" / relative_path).read_text(encoding="utf-8")


class TestInfraProviders(unittest.TestCase):
    def test_local_provider_uses_endpoint_override(self):
        content = read_infra("test/providers.tf")
        self.assertIn("aws_endpoint_url", content)
        self.assertIn('dynamic "endpoints"', content)

    def test_prod_provider_has_no_hardcoded_localhost(self):
        content = read_infra("prod/providers.tf")
        self.assertNotIn("localhost:4566", content)
        self.assertNotIn("access_key", content)
        self.assertNotIn("secret_key", content)
        self.assertNotIn("skip_credentials_validation", content)


class TestInfraDynamoKeys(unittest.TestCase):
    def test_dictionary_hash_key_is_word_capitalized(self):
        content = read_infra("modules/crud/main.tf")
        self.assertRegex(content, r'hash_key\s*=\s*"Word"')

    def test_product_and_cart_hash_keys_match_spec(self):
        content = read_infra("modules/crud/main.tf")
        self.assertRegex(content, r'hash_key\s*=\s*"uuid"')
        self.assertRegex(content, r'hash_key\s*=\s*"UUID"')


class TestInfraLambdaResources(unittest.TestCase):
    def test_lambda_resources_declared(self):
        content = read_infra("modules/crud/main.tf")
        self.assertRegex(content, r'resource\s+"aws_lambda_function"\s+"dictionary"')
        self.assertRegex(content, r'resource\s+"aws_lambda_function"\s+"product"')
        self.assertRegex(content, r'resource\s+"aws_lambda_function"\s+"shopping_cart"')

    def test_lambda_resources_reference_zip_sources(self):
        content = read_infra("modules/crud/main.tf")
        self.assertRegex(content, r'filename\s*=\s*var\.lambda_artifacts\.dictionary')
        self.assertRegex(content, r'filename\s*=\s*var\.lambda_artifacts\.product')
        self.assertRegex(content, r'filename\s*=\s*var\.lambda_artifacts\.shopping_cart')
        self.assertIn("source_code_hash", content)


class TestInfraLambdaIam(unittest.TestCase):
    def test_lambda_basic_execution_role_attached(self):
        content = read_infra("modules/crud/main.tf")
        self.assertIn("AWSLambdaBasicExecutionRole", content)

    def test_lambda_role_attachment_uses_lambda_role(self):
        content = read_infra("modules/crud/main.tf")
        self.assertRegex(content, r'role\s*=\s*aws_iam_role\.lambda_role\.name')
