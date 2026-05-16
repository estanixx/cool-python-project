import importlib.util
import unittest

from backend.tests import conftest


HAVE_MCP = importlib.util.find_spec("mcp") is not None

if HAVE_MCP:
    from backend.mcp import mcp_server
else:
    mcp_server = None


@unittest.skipUnless(HAVE_MCP, "mcp package not installed")
class TestMCPE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        conftest.configure_test_env()
        if not conftest.floci_available():
            raise unittest.SkipTest("Floci DynamoDB not available")
        conftest.ensure_tables()

    def setUp(self):
        conftest.clear_table("Dictionary", "Word")

    def test_dictionary_tool_happy_path(self):
        created = mcp_server.dictionary_create("apple", "A fruit")
        self.assertFalse(created.isError)
        self.assertEqual(created.structuredContent["Word"], "Apple")

        fetched = mcp_server.dictionary_read("apple")
        self.assertFalse(fetched.isError)
        self.assertEqual(fetched.structuredContent["definition"], "A fruit")

    def test_dictionary_tool_propagates_not_found(self):
        result = mcp_server.dictionary_read("missing")
        self.assertTrue(result.isError)
        self.assertIn("not found", result.structuredContent["error"])
        self.assertEqual(result.meta.get("status_code"), 404)
