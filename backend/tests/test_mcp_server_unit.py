import importlib.util
import json
import unittest
from unittest.mock import patch

from backend.handlers import dictionary_handler

HAVE_MCP = importlib.util.find_spec("mcp") is not None

if HAVE_MCP:
    from mcp.types import CallToolResult
    from backend.mcp import mcp_server
else:
    CallToolResult = object
    mcp_server = None


@unittest.skipUnless(HAVE_MCP, "mcp package not installed")
class TestMCPServerToolResult(unittest.TestCase):
    def test_tool_result_surfaces_handler_errors(self):
        def failing_handler(_event, _context):
            return {"statusCode": 404, "body": json.dumps({"error": "missing"})}

        result = mcp_server._tool_result(failing_handler, {"operation": "read"})

        self.assertIsInstance(result, CallToolResult)
        self.assertTrue(result.isError)
        self.assertEqual(result.structuredContent, {"error": "missing"})
        self.assertEqual(result._meta.get("status_code"), 404)

    def test_tool_result_returns_payload(self):
        def ok_handler(_event, _context):
            return {"statusCode": 200, "body": json.dumps({"word": "Apple"})}

        result = mcp_server._tool_result(ok_handler, {"operation": "read"})

        self.assertIsInstance(result, CallToolResult)
        self.assertFalse(result.isError)
        self.assertEqual(result.structuredContent, {"word": "Apple"})
        self.assertEqual(result._meta.get("status_code"), 200)


@unittest.skipUnless(HAVE_MCP, "mcp package not installed")
class TestMCPServerTools(unittest.TestCase):
    def test_dictionary_read_tool_invokes_handler(self):
        with patch.object(dictionary_handler, "handler") as handler:
            handler.return_value = {"statusCode": 200, "body": json.dumps({"word": "Apple"})}

            result = mcp_server.dictionary_read("apple")

        self.assertFalse(result.isError)
        self.assertEqual(result.structuredContent, {"word": "Apple"})
        handler.assert_called_once_with({"operation": "read", "payload": {"word": "apple"}}, None)
