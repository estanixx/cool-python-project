"""MCP server exposing CRUD tools via Lambda handlers.

Transport: Streamable HTTP (simple request/response, no SSE).
"""

import json
import os
from typing import Any, Callable, Dict, Optional, List

from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent

from backend.handlers import dictionary_handler, product_handler, shopping_cart_handler


def _build_event(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"operation": operation, "payload": payload}


def _parse_handler_response(response: Dict[str, Any]) -> Dict[str, Any]:
    body = response.get("body")
    if body is None:
        return {}
    if isinstance(body, str):
        return json.loads(body)
    return body


def _tool_result(handler: Callable[[Dict[str, Any], Any], Dict[str, Any]], event: Dict[str, Any]) -> CallToolResult:
    response = handler(event, None)
    status_code = response.get("statusCode", 500)
    payload = _parse_handler_response(response)

    if status_code >= 400:
        message = payload.get("error", "handler error")
        return CallToolResult(
            content=[TextContent(type="text", text=message)],
            isError=True,
            structuredContent=payload,
            _meta={"status_code": status_code},
        )

    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(payload))],
        structuredContent=payload,
        _meta={"status_code": status_code},
    )


mcp = FastMCP("serverless-crud", stateless_http=True, json_response=True)


@mcp.tool()
def dictionary_create(word: str, definition: str) -> CallToolResult:
    """Create a dictionary entry."""
    event = _build_event("create", {"Word": word, "definition": definition})
    return _tool_result(dictionary_handler.handler, event)


@mcp.tool()
def dictionary_read(word: str) -> CallToolResult:
    """Read a dictionary entry by word."""
    event = _build_event("read", {"Word": word})
    return _tool_result(dictionary_handler.handler, event)


@mcp.tool()
def dictionary_update(word: str, definition: str) -> CallToolResult:
    """Update a dictionary entry."""
    event = _build_event("update", {"Word": word, "definition": definition})
    return _tool_result(dictionary_handler.handler, event)


@mcp.tool()
def dictionary_delete(word: str) -> CallToolResult:
    """Delete a dictionary entry by word."""
    event = _build_event("delete", {"Word": word})
    return _tool_result(dictionary_handler.handler, event)


@mcp.tool()
def product_create(name: str, price: float, product_id: Optional[str] = None) -> CallToolResult:
    """Create a product (optionally provide a product_id)."""
    payload: Dict[str, Any] = {"name": name, "price": price}
    if product_id:
        payload["uuid"] = product_id
    event = _build_event("create", payload)
    return _tool_result(product_handler.handler, event)


@mcp.tool()
def product_read(product_id: str) -> CallToolResult:
    """Read a product by id."""
    event = _build_event("read", {"uuid": product_id})
    return _tool_result(product_handler.handler, event)


@mcp.tool()
def product_update(product_id: str, name: Optional[str] = None, price: Optional[float] = None) -> CallToolResult:
    """Update product fields by id."""
    payload: Dict[str, Any] = {"uuid": product_id}
    if name is not None:
        payload["name"] = name
    if price is not None:
        payload["price"] = price
    event = _build_event("update", payload)
    return _tool_result(product_handler.handler, event)


@mcp.tool()
def product_delete(product_id: str) -> CallToolResult:
    """Delete a product by id."""
    event = _build_event("delete", {"uuid": product_id})
    return _tool_result(product_handler.handler, event)


@mcp.tool()
def shopping_cart_create(cart_id: str, product_ids: List[str]) -> CallToolResult:
    """Create a shopping cart with product IDs."""
    event = _build_event("create", {"UUID": cart_id, "productIds": product_ids})
    return _tool_result(shopping_cart_handler.handler, event)


@mcp.tool()
def shopping_cart_read(cart_id: str) -> CallToolResult:
    """Read a shopping cart by id."""
    event = _build_event("read", {"UUID": cart_id})
    return _tool_result(shopping_cart_handler.handler, event)


@mcp.tool()
def shopping_cart_update(cart_id: str, product_ids: List[str]) -> CallToolResult:
    """Update a shopping cart's product IDs."""
    event = _build_event("update", {"UUID": cart_id, "productIds": product_ids})
    return _tool_result(shopping_cart_handler.handler, event)


@mcp.tool()
def shopping_cart_delete(cart_id: str) -> CallToolResult:
    """Delete a shopping cart by id."""
    event = _build_event("delete", {"UUID": cart_id})
    return _tool_result(shopping_cart_handler.handler, event)


def _configure_default_env() -> None:
    os.environ.setdefault("STAGE", "local")
    os.environ.setdefault("AWS_ENDPOINT_URL", "http://localhost:4566")


if __name__ == "__main__":
    _configure_default_env()
    mcp.run(
        transport="streamable-http",
        host="127.0.0.1",
        port=8000,
        streamable_http_path="/mcp",
        json_response=True,
        stateless_http=True,
    )
