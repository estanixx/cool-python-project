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

    def test_terraform_build_spec_app_root_and_env(self):
        amplify_tf = self.repo_root / "infra" / "prod" / "amplify.tf"
        content = amplify_tf.read_text(encoding="utf-8")

        self.assertIn("appRoot: website", content)
        self.assertIn("AMPLIFY_MONOREPO_APP_ROOT = \"website\"", content)
        self.assertIn("appRoot aligned with amplify.yml", content)

    def test_next_config_alias_fallback(self):
        next_config = self.repo_root / "website" / "next.config.js"
        content = next_config.read_text(encoding="utf-8")

        self.assertIn("webpack:", content)
        self.assertIn("alias", content)
        self.assertIn("\"@\"", content)
        self.assertIn("path.resolve(__dirname)", content)


if __name__ == "__main__":
    unittest.main()
