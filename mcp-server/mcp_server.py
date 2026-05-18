"""MCP server exposing CRUD tools via HTTP API calls.

Transport: SSE (Server-Sent Events) for remote MCP clients.
"""
import json
import os
from typing import Any, Dict, List, Optional

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, TextContent

# Disable DNS rebinding protection so the server works behind an ALB
# (the ALB's Host header won't match localhost)
mcp = FastMCP(
    "serverless-crud",
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

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


def _call_api(
    method: str,
    path: str,
    body: Optional[Dict[str, Any]] = None,
    query_params: Optional[Dict[str, str]] = None,
) -> CallToolResult:
    """Make an HTTP request to the API and return an MCP tool result."""
    try:
        # If using API Gateway, send standard HTTP request
        if API_ID:
            url = f"{API_ENDPOINT}{path}"
            if query_params:
                qs = "&".join(f"{k}={v}" for k, v in query_params.items())
                url = f"{url}?{qs}"
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
            # Extract resource name from path (e.g., "/dictionary/{word}" -> "dictionary")
            path_parts = path.strip("/").split("/")
            resource = path_parts[0]
            
            # Extract path parameters
            path_params = {}
            if len(path_parts) > 1:
                # Map common path parameter names
                if resource == "dictionary":
                    path_params["word"] = path_parts[1]
                elif resource == "product":
                    path_params["product_id"] = path_parts[1]
                elif resource == "shopping-cart":
                    path_params["cart_id"] = path_parts[1]
            
            # Build Lambda URL
            url = f"{API_ENDPOINT}/{resource}-local/invocations"
            
            # Build event with operation, payload, and path parameters
            operation_map = {"POST": "create", "GET": "read", "PUT": "update", "DELETE": "delete"}
            event_payload = {**(body or {}), **path_params}
            # Operation priority: body > query_params > HTTP method mapping
            op = (body or {}).get("operation")
            if op is None and query_params and "operation" in query_params:
                op = query_params["operation"]
            if op is None:
                op = operation_map.get(method, "read")
            event = {
                "operation": op,
                "payload": event_payload,
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


@mcp.tool()
def dictionary_list() -> CallToolResult:
    """List all dictionary entries."""
    return _call_api("GET", "/dictionary", query_params={"operation": "list"})


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


@mcp.tool()
def product_list() -> CallToolResult:
    """List all products."""
    return _call_api("GET", "/product", {"operation": "list"}, query_params={"operation": "list"})


@mcp.tool()
def product_search(term: str) -> CallToolResult:
    """Search products by name (case-insensitive substring match)."""
    return _call_api(
        "GET", "/product",
        {"operation": "search", "term": term},
        query_params={"operation": "search", "term": term},
    )


# Shopping Cart tools
@mcp.tool()
def shopping_cart_create(cart_id: str, products: List[Dict[str, Any]]) -> CallToolResult:
    """Create a shopping cart with product objects (each with uuid, name, price)."""
    return _call_api("POST", "/shopping-cart", {"UUID": cart_id, "products": products})


@mcp.tool()
def shopping_cart_read(cart_id: str) -> CallToolResult:
    """Read a shopping cart by id."""
    return _call_api("GET", f"/shopping-cart/{cart_id}")


@mcp.tool()
def shopping_cart_update(cart_id: str, products: List[Dict[str, Any]]) -> CallToolResult:
    """Update a shopping cart's product objects."""
    return _call_api("PUT", f"/shopping-cart/{cart_id}", {"products": products})


@mcp.tool()
def shopping_cart_delete(cart_id: str) -> CallToolResult:
    """Delete a shopping cart by id."""
    return _call_api("DELETE", f"/shopping-cart/{cart_id}")


@mcp.tool()
def shopping_cart_add_product(
    cart_id: str,
    product_uuid: str,
    name: Optional[str] = None,
    price: Optional[float] = None,
) -> CallToolResult:
    """Add a product to a shopping cart. If name and price are provided, they are
    stored as a snapshot. If only product_uuid is provided, the server fetches
    the product details automatically."""
    product = {"uuid": product_uuid}
    if name is not None:
        product["name"] = name
    if price is not None:
        product["price"] = price
    return _call_api(
        "POST", "/shopping-cart",
        {
            "operation": "add_product",
            "cart_id": cart_id,
            "product": product,
        },
    )


@mcp.tool()
def shopping_cart_remove_product(
    cart_id: str,
    product_uuid: str,
) -> CallToolResult:
    """Remove a product from a shopping cart by product UUID."""
    return _call_api(
        "POST", "/shopping-cart",
        {
            "operation": "remove_product",
            "cart_id": cart_id,
            "product_uuid": product_uuid,
        },
    )


@mcp.tool()
def shopping_cart_get_total(
    cart_id: str,
    tax_rate: Optional[float] = 0.07,
) -> CallToolResult:
    """Get the shopping cart total (subtotal, tax, total) for a given cart."""
    return _call_api(
        "POST", "/shopping-cart",
        {
            "operation": "get_total",
            "cart_id": cart_id,
            "tax_rate": tax_rate,
        },
    )


# Word Trick tool
@mcp.tool()
def word_trick(sentence: str) -> CallToolResult:
    """Apply the word trick: returns the i-th character of the i-th word for each word in the sentence."""
    return _call_api("POST", "/word-trick", {"sentence": sentence})


if __name__ == "__main__":
    import uvicorn
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Route

    # Health check endpoint for ALB
    async def health(request):
        return JSONResponse({"status": "ok"})

    sse_app = mcp.sse_app()

    app = Starlette(
        routes=[
            Route("/health", health),
            *sse_app.routes,
        ]
    )
    uvicorn.run(app, host="0.0.0.0", port=8000)