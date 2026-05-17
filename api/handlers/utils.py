"""Shared utilities for Lambda handlers."""
import json
from typing import Any, Dict, Tuple

# Mapping of HTTP methods to internal CRUD operations
METHOD_TO_OPERATION = {
    "POST": "create",
    "GET": "read",
    "PUT": "update",
    "DELETE": "delete",
}


def parse_event(event: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Parse Lambda event from either API Gateway v2 or legacy custom format.
    
    Returns:
        Tuple of (operation, payload)
    """
    # API Gateway v2 format
    if "requestContext" in event:
        method = event.get("requestContext", {}).get("http", {}).get("method", "").upper()
        operation = METHOD_TO_OPERATION.get(method)

        # Allow query parameter to override operation (e.g., GET /product?operation=list)
        query_params = event.get("queryStringParameters") or {}
        if "operation" in query_params:
            operation = query_params["operation"]

        body = event.get("body", "{}")
        if isinstance(body, str):
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                payload = {}
        else:
            payload = body or {}

        # Inject path parameters (e.g., {word} from /dictionary/{word})
        path_params = event.get("pathParameters") or {}
        payload.update(path_params)

        # Inject query parameters (e.g., ?term=mouse for search)
        payload.update(query_params)

        return operation, payload
    
    # Legacy custom format (for direct invocation/testing)
    return event.get("operation"), event.get("payload") or {}
