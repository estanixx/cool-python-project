import unittest
from pathlib import Path


class TestAmplifyAliasConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = Path(__file__).resolve().parents[2]

    def test_amplify_yml_app_root_and_commands(self):
        amplify_yml = self.repo_root / "amplify.yml"
        content = amplify_yml.read_text(encoding="utf-8")

        self.assertIn("appRoot: website", content)
        self.assertIn("npm ci", content)
        self.assertIn("npm run build", content)
        self.assertIn("appRoot must remain website", content)

    def test_app_root_override_guardrails(self):
        amplify_yml = self.repo_root / "amplify.yml"
        amplify_tf = self.repo_root / "infra" / "prod" / "amplify.tf"

        amplify_yml_content = amplify_yml.read_text(encoding="utf-8")
        amplify_tf_content = amplify_tf.read_text(encoding="utf-8")

        self.assertIn("appRoot override", amplify_yml_content)
        self.assertIn("appRoot override", amplify_tf_content)
        self.assertIn("AMPLIFY_MONOREPO_APP_ROOT = \"website\"", amplify_tf_content)

    def test_terraform_build_spec_app_root_and_env(self):
        amplify_tf = self.repo_root / "infra" / "prod" / "amplify.tf"
        content = amplify_tf.read_text(encoding="utf-8")

        self.assertIn("appRoot: website", content)
        self.assertIn("AMPLIFY_MONOREPO_APP_ROOT = \"website\"", content)
        self.assertIn("appRoot aligned with amplify.yml", content)

    def test_build_installs_dev_dependencies_for_typescript(self):
        amplify_yml = self.repo_root / "amplify.yml"
        amplify_tf = self.repo_root / "infra" / "prod" / "amplify.tf"

        amplify_yml_content = amplify_yml.read_text(encoding="utf-8")
        amplify_tf_content = amplify_tf.read_text(encoding="utf-8")

        self.assertIn("npm ci --include=dev", amplify_yml_content)
        self.assertIn("npm ci --include=dev", amplify_tf_content)

    def test_next_config_alias_fallback(self):
        next_config = self.repo_root / "website" / "next.config.js"
        content = next_config.read_text(encoding="utf-8")

        self.assertIn("webpack:", content)
        self.assertIn("alias", content)
        self.assertIn("\"@\"", content)
        self.assertIn("path.resolve(__dirname)", content)

    def test_alias_resolution_when_root_misaligned(self):
        next_config = self.repo_root / "website" / "next.config.js"
        content = next_config.read_text(encoding="utf-8")

        self.assertIn("root misaligned", content)
        self.assertIn("path.resolve(__dirname)", content)


if __name__ == "__main__":
    unittest.main()
