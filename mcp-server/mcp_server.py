"""MCP server exposing CRUD tools via HTTP API calls.

Transport: Streamable HTTP (simple request/response, no SSE).
"""
import json
import os
from typing import Any, Dict, List, Optional

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.types import CallToolResult, TextContent

# Configuration: API base URL and API ID (from Floci/AWS)
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:4566")
API_ID = os.getenv("API_ID", "")

# Resolve full API Gateway URL
if API_ID:
    # Floci API Gateway v2 format
    API_ENDPOINT = f"{API_BASE_URL}/restapis/{API_ID}/_user_request_"
else:
    # Fallback to direct Lambda invocation (for local dev without API Gateway)
    API_ENDPOINT = f"{API_BASE_URL}/2015-03-31/functions"

mcp = FastMCP("serverless-crud", stateless_http=True, json_response=True)


def _call_api(method: str, path: str, body: Optional[Dict[str, Any]] = None) -> CallToolResult:
    """Make an HTTP request to the API and return an MCP tool result."""
    url = f"{API_ENDPOINT}{path}" if API_ID else f"{API_ENDPOINT}/{path}-local/invocations"
    
    try:
        # If using API Gateway, send standard HTTP request
        if API_ID:
            response = httpx.request(
                method=method,
                url=url,
                json=body,
                headers={"Content-Type": "application/json"},
                timeout=10.0,
            )
            status_code = response.status_code
            try:
                payload = response.json()
            except json.JSONDecodeError:
                payload = {"raw": response.text}
        else:
            # Direct Lambda invocation (legacy format)
            operation_map = {"POST": "create", "GET": "read", "PUT": "update", "DELETE": "delete"}
            event = {
                "operation": operation_map.get(method, "read"),
                "payload": body or {},
            }
            response = httpx.post(
                url,
                json=event,
                headers={"Content-Type": "application/json"},
                timeout=10.0,
            )
            status_code = response.status_code
            payload = response.json()

        if status_code >= 400:
            message = payload.get("error", "api error")
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
    except httpx.RequestError as exc:
        return CallToolResult(
            content=[TextContent(type="text", text=f"API request failed: {exc}")],
            isError=True,
            structuredContent={"error": str(exc)},
            _meta={"status_code": 502},
        )


# Dictionary tools
@mcp.tool()
def dictionary_create(word: str, definition: str) -> CallToolResult:
    """Create a dictionary entry."""
    return _call_api("POST", "/dictionary", {"Word": word, "definition": definition})


@mcp.tool()
def dictionary_read(word: str) -> CallToolResult:
    """Read a dictionary entry by word."""
    return _call_api("GET", f"/dictionary/{word}")


@mcp.tool()
def dictionary_update(word: str, definition: str) -> CallToolResult:
    """Update a dictionary entry."""
    return _call_api("PUT", f"/dictionary/{word}", {"definition": definition})


@mcp.tool()
def dictionary_delete(word: str) -> CallToolResult:
    """Delete a dictionary entry by word."""
    return _call_api("DELETE", f"/dictionary/{word}")


# Product tools
@mcp.tool()
def product_create(name: str, price: float, product_id: Optional[str] = None) -> CallToolResult:
    """Create a product (optionally provide a product_id)."""
    body: Dict[str, Any] = {"name": name, "price": price}
    if product_id:
        body["uuid"] = product_id
    return _call_api("POST", "/product", body)


@mcp.tool()
def product_read(product_id: str) -> CallToolResult:
    """Read a product by id."""
    return _call_api("GET", f"/product/{product_id}")


@mcp.tool()
def product_update(product_id: str, name: Optional[str] = None, price: Optional[float] = None) -> CallToolResult:
    """Update product fields by id."""
    body: Dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if price is not None:
        body["price"] = price
    return _call_api("PUT", f"/product/{product_id}", body)


@mcp.tool()
def product_delete(product_id: str) -> CallToolResult:
    """Delete a product by id."""
    return _call_api("DELETE", f"/product/{product_id}")


# Shopping Cart tools
@mcp.tool()
def shopping_cart_create(cart_id: str, product_ids: List[str]) -> CallToolResult:
    """Create a shopping cart with product IDs."""
    return _call_api("POST", "/shopping-cart", {"UUID": cart_id, "productIds": product_ids})


@mcp.tool()
def shopping_cart_read(cart_id: str) -> CallToolResult:
    """Read a shopping cart by id."""
    return _call_api("GET", f"/shopping-cart/{cart_id}")


@mcp.tool()
def shopping_cart_update(cart_id: str, product_ids: List[str]) -> CallToolResult:
    """Update a shopping cart's product IDs."""
    return _call_api("PUT", f"/shopping-cart/{cart_id}", {"productIds": product_ids})


@mcp.tool()
def shopping_cart_delete(cart_id: str) -> CallToolResult:
    """Delete a shopping cart by id."""
    return _call_api("DELETE", f"/shopping-cart/{cart_id}")


if __name__ == "__main__":
    mcp.run()
