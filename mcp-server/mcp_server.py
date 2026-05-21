"""MCP server exposing CRUD tools.

In LOCAL mode (Floci/LocalStack), we bypass API Gateway v2 (which Floci doesn't
support) and invoke Lambda functions directly via the Lambda API.
In PRODUCTION mode, we call the real API Gateway v2 HTTP endpoint.
"""
import inspect
import json
import logging
import os
import time
import uuid
from typing import Any, Dict, List, Optional

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, TextContent

logger = logging.getLogger("mcp_server")

# Disable DNS rebinding protection so the server works behind an ALB
# (the ALB's Host header won't match localhost)
mcp = FastMCP(
    "serverless-crud",
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

# Configuration
STAGE = os.getenv("STAGE", "local")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:4566")
API_ID = os.getenv("API_ID", "")

IS_PROD = STAGE != "local"

# For local mode: Lambda direct invoke URL
LAMBDA_INVOKE_URL = f"{API_BASE_URL}/2015-03-31/functions"

# Map the first path segment to the Lambda function name (local mode only)
PATH_TO_FUNCTION: Dict[str, str] = {
    "dictionary": f"dictionary-{STAGE}",
    "product": f"product-{STAGE}",
    "shopping-cart": f"shopping-cart-{STAGE}",
    "word-trick": f"word-trick-{STAGE}",
}


def _get_caller_name() -> str:
    """Extract the MCP tool function name from the call stack."""
    try:
        frame = inspect.currentframe()
        # Walk up: _get_caller_name → _call_api → tool function
        if frame and frame.f_back and frame.f_back.f_back:
            return frame.f_back.f_back.f_code.co_name
    except Exception:
        pass
    return "unknown"


def _log_tool_call(tool: str, method: str, path: str, status: int, duration_ms: int) -> None:
    """Best-effort structured JSON log. Never breaks the call."""
    try:
        print(json.dumps({
            "level": "info",
            "tool": tool,
            "method": method,
            "path": path,
            "status": status,
            "duration_ms": duration_ms,
        }), flush=True)
    except Exception:
        pass


def _build_success_result(payload: dict, status_code: int) -> CallToolResult:
    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(payload))],
        structuredContent=payload,
        _meta={"status_code": status_code},
    )


def _build_error_result(payload: dict, status_code: int) -> CallToolResult:
    message = payload.get("error", "api error") if isinstance(payload, dict) else "api error"
    return CallToolResult(
        content=[TextContent(type="text", text=message)],
        isError=True,
        structuredContent=payload,
        _meta={"status_code": status_code},
    )


def _call_api_prod(
    method: str,
    path: str,
    body: Optional[Dict[str, Any]] = None,
    query_params: Optional[Dict[str, str]] = None,
) -> CallToolResult:
    """Call the real API Gateway v2 endpoint directly (production)."""
    invoke_url = f"{API_BASE_URL}{path}"
    if query_params:
        qs = "&".join(f"{k}={v}" for k, v in query_params.items())
        invoke_url += f"?{qs}"

    start = time.monotonic()
    response = httpx.request(
        method=method.upper(),
        url=invoke_url,
        headers={"Content-Type": "application/json"},
        json=body,
        timeout=10.0,
    )
    duration_ms = round((time.monotonic() - start) * 1000)
    status_code = response.status_code

    try:
        payload = response.json()
    except json.JSONDecodeError:
        payload = {"raw": response.text}

    # Determine final status
    final_status = status_code

    if status_code >= 400:
        result = _build_error_result(payload, final_status)
    else:
        result = _build_success_result(payload, final_status)

    # Structured log AFTER determining final status (fixes G7)
    caller = _get_caller_name()
    _log_tool_call(caller, method, path, final_status, duration_ms)

    return result


def _call_api_local(
    method: str,
    path: str,
    body: Optional[Dict[str, Any]] = None,
    query_params: Optional[Dict[str, str]] = None,
) -> CallToolResult:
    """Invoke Lambda directly via Floci's Lambda API (local dev).

    Constructs an API Gateway v2 event envelope so the Lambda handler
    receives exactly the same format as it would from real API Gateway.
    """
    seg = path.strip("/").split("/")[0]
    function_name = PATH_TO_FUNCTION.get(seg, f"{seg}-{STAGE}")

    # Build the query string
    query_string = ""
    if query_params:
        query_string = "&".join(f"{k}={v}" for k, v in query_params.items())

    # Extract path segments for pathParameters
    segments = path.strip("/").split("/")
    path_params: Optional[Dict[str, str]] = None
    if len(segments) > 1:
        param_name = {
            "dictionary": "word",
            "product": "product_id",
            "shopping-cart": "cart_id",
        }.get(segments[0])
        if param_name:
            path_params = {param_name: segments[1]}

    query_params_parsed: Optional[Dict[str, str]] = None
    if query_params and len(query_params) > 0:
        query_params_parsed = dict(query_params)

    # Build API Gateway v2 event envelope
    event = {
        "version": "2.0",
        "routeKey": f"{method.upper()} {path}",
        "rawPath": path,
        "rawQueryString": query_string,
        "headers": {
            "Content-Type": "application/json",
        },
        "requestContext": {
            "accountId": "000000000000",
            "apiId": API_ID,
            "stage": "$default",
            "domainName": f"{API_ID}.execute-api.{os.getenv('AWS_DEFAULT_REGION', 'us-east-1')}.amazonaws.com",
            "domainPrefix": API_ID,
            "requestId": str(uuid.uuid4()),
            "http": {
                "method": method.upper(),
                "path": path,
                "protocol": "HTTP/1.1",
                "sourceIp": "127.0.0.1",
                "userAgent": "mcp-server",
            },
        },
        "pathParameters": path_params,
        "queryStringParameters": query_params_parsed,
        "body": json.dumps(body) if body is not None else None,
        "isBase64Encoded": False,
    }

    invoke_url = f"{LAMBDA_INVOKE_URL}/{function_name}/invocations"
    start = time.monotonic()
    response = httpx.request(
        method="POST",
        url=invoke_url,
        json=event,
        headers={"Content-Type": "application/json"},
        timeout=10.0,
    )
    duration_ms = round((time.monotonic() - start) * 1000)

    try:
        payload = response.json()
    except json.JSONDecodeError:
        payload = {"raw": response.text}

    # Unwrap the Lambda return envelope
    lambda_status = payload.get("statusCode", 200) if isinstance(payload, dict) else 200

    if lambda_status >= 400:
        inner_body = payload.get("body", "{}")
        try:
            err_payload = json.loads(inner_body) if isinstance(inner_body, str) else inner_body
        except json.JSONDecodeError:
            err_payload = {"raw": inner_body}
        result = _build_error_result(err_payload, lambda_status)
    else:
        inner_body = payload.get("body", "{}")
        try:
            inner_payload = json.loads(inner_body) if isinstance(inner_body, str) else inner_body
        except json.JSONDecodeError:
            inner_payload = {"raw": inner_body}
        result = _build_success_result(inner_payload, lambda_status)

    # Structured log AFTER determining final status (fixes G7)
    caller = _get_caller_name()
    _log_tool_call(caller, method, path, lambda_status, duration_ms)

    return result


def _call_api(
    method: str,
    path: str,
    body: Optional[Dict[str, Any]] = None,
    query_params: Optional[Dict[str, str]] = None,
) -> CallToolResult:
    """Route to production or local API caller based on STAGE."""
    try:
        if IS_PROD:
            return _call_api_prod(method, path, body, query_params)
        return _call_api_local(method, path, body, query_params)
    except httpx.RequestError as exc:
        caller = _get_caller_name()
        _log_tool_call(caller, method, path, 502, 0)
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


@mcp.tool()
def stress_test(
    iterations: int = 10,
    concurrency: int = 1,
    delay_ms: int = 100,
) -> CallToolResult:
    """Run stress test against production API.

    Loops through: product_list, dictionary_list, shopping_cart_list.
    Each iteration calls all 3 endpoints and logs results.
    """
    import time as _time

    endpoints = [
        ("GET", "/product", {"operation": "list"}),
        ("GET", "/dictionary", {"operation": "list"}),
        ("GET", "/shopping-cart", {"operation": "list"}),
    ]

    total_calls = 0
    success_count = 0
    error_count = 0
    results: List[Dict[str, Any]] = []

    for i in range(iterations):
        for method, path, body in endpoints:
            total_calls += 1
            try:
                if IS_PROD:
                    result = _call_api_prod(method, path, body)
                else:
                    result = _call_api_local(method, path, body)

                status = result._meta.get("status_code", 0) if result._meta else 0
                if status < 400:
                    success_count += 1
                else:
                    error_count += 1

                results.append({
                    "iteration": i + 1,
                    "endpoint": f"{method} {path}",
                    "status": status,
                })
            except Exception as exc:
                error_count += 1
                results.append({
                    "iteration": i + 1,
                    "endpoint": f"{method} {path}",
                    "status": 0,
                    "error": str(exc),
                })

            if delay_ms > 0:
                _time.sleep(delay_ms / 1000.0)

    summary = {
        "total_calls": total_calls,
        "success": success_count,
        "errors": error_count,
        "iterations": iterations,
        "concurrency": concurrency,
        "delay_ms": delay_ms,
        "results": results,
    }

    print(json.dumps({
        "level": "info",
        "tool": "stress_test",
        "total_calls": total_calls,
        "success": success_count,
        "errors": error_count,
    }), flush=True)

    return CallToolResult(
        content=[TextContent(type="text", text=json.dumps(summary))],
        structuredContent=summary,
        _meta={"status_code": 200},
    )


if __name__ == "__main__":
    import uvicorn
    from starlette.applications import Starlette
    from starlette.responses import JSONResponse
    from starlette.routing import Mount, Route

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
