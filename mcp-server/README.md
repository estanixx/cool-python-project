# MCP Server — AI-Accessible Tools

Model Context Protocol (MCP) server that exposes all API operations as tools accessible by AI clients (Claude, Cursor, OpenCode, etc.).

## Quick Start

### Run Locally
```bash
cd mcp-server
pip install -r requirements.txt
python mcp_server.py
```

### Run with Docker
```bash
docker-compose up -d mcp-server
```

Server will be available at `http://localhost:8000/sse`.

## Architecture

```
┌──────────────┐     SSE      ┌─────────────────┐     HTTP/Lambda     ┌──────────────┐
│  AI Client   │ ───────────► │   MCP Server    │ ─────────────────► │  API / Lambda │
│ (Claude, etc)│              │  (FastMCP +     │                    │  (DynamoDB)   │
└──────────────┘              │   Uvicorn)      │                    └──────────────┘
                              └─────────────────┘
```

### Transport
- **SSE (Server-Sent Events)** — Default, widely supported
- Binds to `0.0.0.0:8000` for Docker compatibility

### Connection Modes
| Mode | `API_ID` | Behavior |
|------|----------|----------|
| **Direct Lambda** | Empty | Calls Lambda functions directly via Floci API |
| **API Gateway** | Set | Routes through API Gateway HTTP API |

## Tool Reference

### Dictionary Tools (5 tools)

| Tool | Parameters | Description |
|------|------------|-------------|
| `dictionary_create` | `word: str`, `definition: str` | Create a dictionary entry |
| `dictionary_read` | `word: str` | Read a dictionary entry by word |
| `dictionary_update` | `word: str`, `definition: str` | Update a dictionary entry's definition |
| `dictionary_delete` | `word: str` | Delete a dictionary entry by word |
| `dictionary_list` | *(none)* | List all dictionary entries |

**Example**:
```
dictionary_create(word="Python", definition="A programming language")
dictionary_read(word="Python")
dictionary_list()
```

### Product Tools (7 tools)

| Tool | Parameters | Description |
|------|------------|-------------|
| `product_create` | `name: str`, `price: float`, `product_id?: str` | Create a product (auto-generates UUID if not provided) |
| `product_read` | `product_id: str` | Read a product by UUID |
| `product_update` | `product_id: str`, `name?: str`, `price?: float` | Update product fields |
| `product_delete` | `product_id: str` | Delete a product by UUID |
| `product_list` | *(none)* | List all products |
| `product_search` | `term: str` | Search products by name (case-insensitive substring) |

**Example**:
```
product_create(name="Laptop", price=999.99)
product_search(term="lap")
product_list()
```

### Shopping Cart Tools (8 tools)

| Tool | Parameters | Description |
|------|------------|-------------|
| `shopping_cart_create` | `cart_id: str`, `products: List[{uuid, name, price}]` | Create a cart with product snapshots |
| `shopping_cart_read` | `cart_id: str` | Read a shopping cart by ID |
| `shopping_cart_update` | `cart_id: str`, `products: List[{uuid, name, price}]` | Replace cart's product list |
| `shopping_cart_delete` | `cart_id: str` | Delete a shopping cart |
| `shopping_cart_add_product` | `cart_id: str`, `product_uuid: str`, `name?: str`, `price?: float` | Add product to cart (dual-mode) |
| `shopping_cart_remove_product` | `cart_id: str`, `product_uuid: str` | Remove product from cart |
| `shopping_cart_get_total` | `cart_id: str`, `tax_rate?: float` | Calculate cart total with tax |

#### Dual-Mode Add Product
`shopping_cart_add_product` supports two modes:

**Mode 1 — Full Snapshot** (provide all details):
```
shopping_cart_add_product(cart_id="cart-1", product_uuid="p1", name="Laptop", price=999.99)
```
→ Stores `{"uuid": "p1", "name": "Laptop", "price": 999.99}` directly

**Mode 2 — UUID Only** (auto-fetch):
```
shopping_cart_add_product(cart_id="cart-1", product_uuid="p1")
```
→ Server fetches product details from ProductDAO and creates snapshot
→ Returns 404 if product doesn't exist

### Word Trick Tool (1 tool)

| Tool | Parameters | Description |
|------|------------|-------------|
| `word_trick` | `sentence: str` | Returns i-th character of i-th word for each word |

**Example**:
```
word_trick(sentence="The quick brown fox")
# Returns: "Tqbf" (T from "The", q from "quick", b from "brown", f from "fox")
```

## Production Endpoint (ALB)

When deployed to production with `enable_alb=true`, the MCP server runs behind an Application Load Balancer:

```bash
# Get the ALB DNS name after terraform apply
terraform -chdir=infra/prod output mcp_alb_dns_name

# Or use the service endpoint (includes http:// prefix)
terraform -chdir=infra/prod output mcp_service_endpoint
```

The ALB endpoint is also printed in the CD workflow deploy job logs after a successful `terraform apply`.

### Connecting AI Clients to Production

Configure your MCP client to connect to the ALB endpoint:
```
http://<alb-dns-name>/sse
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE_URL` | `http://localhost:4566` | Base URL for API calls |
| `API_ID` | `""` | API Gateway ID (empty = direct Lambda) |

### Docker Compose
```yaml
mcp-server:
  build: ./mcp-server
  ports:
    - "8000:8000"
  environment:
    - API_BASE_URL=http://floci:4566
    - API_ID=${API_ID:-}
  depends_on:
    - floci
```

## Connecting AI Clients

### OpenCode / Claude Desktop / Cursor
Configure your MCP client to connect to:
```
http://localhost:8000/sse
```

### Manual Testing
```bash
# List available tools
curl -N http://localhost:8000/sse &
sleep 1
curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

## Adding New Tools

### 1. Define the Tool
```python
@mcp.tool()
def my_new_tool(param1: str, param2: Optional[int] = None) -> CallToolResult:
    """Description of what this tool does."""
    return _call_api(
        "POST", "/my-endpoint",
        {"param1": param1, "param2": param2},
        query_params={"action": "my_action"},
    )
```

### 2. Follow Naming Conventions
- Use `snake_case` for tool names
- Prefix with domain: `dictionary_*`, `product_*`, `shopping_cart_*`
- Use descriptive parameter names

### 3. Error Handling
The `_call_api()` function automatically:
- Returns `isError=True` for HTTP 4xx/5xx
- Wraps network errors in `CallToolResult`
- Includes `_meta` with status code

### 4. Test the Tool
```bash
# Rebuild and restart
docker-compose down mcp-server
docker-compose build mcp-server
docker-compose up -d mcp-server

# Verify tool appears in list
curl http://localhost:8000/sse -N &
curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

## Response Format

All tools return `CallToolResult`:
```json
{
  "content": [{"type": "text", "text": "..."}],
  "structuredContent": {...},
  "_meta": {"status_code": 200},
  "isError": false
}
```

## Troubleshooting

### "Connection reset by peer"
- Server must bind to `0.0.0.0`, not `127.0.0.1`
- Rebuild Docker image: `docker-compose build --no-cache mcp-server`

### "Invalid request parameters"
- Check parameter names match tool schema exactly
- Cart IDs are case-sensitive (stored as uppercase)

### "Terminating session: None"
- SSE transport session management issue
- Restart MCP server: `docker-compose restart mcp-server`
- Reconnect AI client

### Tool not found
- Verify tool is decorated with `@mcp.tool()`
- Check server logs: `docker-compose logs mcp-server`
- Ensure server is running: `docker-compose ps`
