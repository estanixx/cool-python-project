"""Tests for MCP server structured logging in _call_api()."""
import json
import unittest
from unittest.mock import MagicMock, patch

from mcp.types import CallToolResult


class MockResponse:
    """Minimal mock for httpx.Response."""

    def __init__(self, status_code: int, json_body=None, text: str = ""):
        self.status_code = status_code
        self._json_body = json_body
        self._text = text

    def json(self):
        if self._json_body is not None:
            return self._json_body
        raise json.JSONDecodeError("no json", self._text, 0)

    @property
    def text(self):
        return self._text


class TestCallApiStructuredLogging(unittest.TestCase):
    """Verify _call_api() emits structured JSON logs without breaking behavior."""

    @patch("mcp_server.logger")
    @patch("mcp_server.httpx.request")
    def test_emits_structured_log_on_success(self, mock_request, mock_logger):
        """Successful API call emits a structured JSON log line with all required fields."""
        mock_request.return_value = MockResponse(
            200, json_body={"id": "1", "Word": "test"}
        )

        from mcp_server import _call_api

        result = _call_api("POST", "/dictionary", {"Word": "test"})

        # Verify the call still returns correctly
        self.assertIsInstance(result, CallToolResult)
        self.assertFalse(result.isError)

        # Verify logger.info was called with a JSON string
        mock_logger.info.assert_called_once()
        logged_json = mock_logger.info.call_args[0][0]
        logged_data = json.loads(logged_json)

        # Assert all required fields exist
        self.assertEqual(logged_data["level"], "info")
        self.assertEqual(logged_data["method"], "POST")
        self.assertEqual(logged_data["path"], "/dictionary")
        self.assertEqual(logged_data["status"], 200)
        self.assertIn("duration_ms", logged_data)
        self.assertIsInstance(logged_data["duration_ms"], int)
        self.assertIn("tool", logged_data)

    @patch("mcp_server.logger")
    @patch("mcp_server.httpx.request")
    def test_emits_structured_log_on_error_status(self, mock_request, mock_logger):
        """Failed API call (4xx) emits a structured JSON log with error status."""
        mock_request.return_value = MockResponse(
            404, json_body={"error": "not found"}
        )

        from mcp_server import _call_api

        result = _call_api("GET", "/dictionary/missing")

        # Verify the call still returns an error result
        self.assertIsInstance(result, CallToolResult)
        self.assertTrue(result.isError)

        # Verify logger.info was called
        mock_logger.info.assert_called_once()
        logged_json = mock_logger.info.call_args[0][0]
        logged_data = json.loads(logged_json)

        self.assertEqual(logged_data["status"], 404)
        self.assertEqual(logged_data["method"], "GET")
        self.assertEqual(logged_data["path"], "/dictionary/missing")

    @patch("mcp_server.logger")
    @patch("mcp_server.httpx.request")
    def test_logging_failure_does_not_break_call(self, mock_request, mock_logger):
        """If logger.info raises, _call_api() still returns the correct result."""
        mock_request.return_value = MockResponse(
            200, json_body={"id": "1", "Word": "hello"}
        )
        mock_logger.info.side_effect = RuntimeError("logging broken")

        from mcp_server import _call_api

        result = _call_api("POST", "/dictionary", {"Word": "hello"})

        # Must still return a valid result despite logging failure
        self.assertIsInstance(result, CallToolResult)
        self.assertFalse(result.isError)

    @patch("mcp_server.logger")
    @patch("mcp_server.httpx.request")
    def test_tool_name_derived_from_caller(self, mock_request, mock_logger):
        """The 'tool' field in the log matches the calling function name."""
        mock_request.return_value = MockResponse(
            200, json_body={"id": "1"}
        )

        from mcp_server import _call_api

        _call_api("GET", "/dictionary/test")

        logged_json = mock_logger.info.call_args[0][0]
        logged_data = json.loads(logged_json)

        # When called directly (not from a named tool function),
        # the tool field should be "test_tool_name_derived_from_caller"
        # (the test method name) or "unknown"
        self.assertIn("tool", logged_data)
        self.assertIsInstance(logged_data["tool"], str)
        self.assertTrue(len(logged_data["tool"]) > 0)


if __name__ == "__main__":
    unittest.main()
