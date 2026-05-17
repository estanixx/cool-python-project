# Serverless CRUD + MCP Server

A serverless Python backend with Lambda functions, DynamoDB storage, and an MCP (Model Context Protocol) server that exposes CRUD operations as AI-accessible tools.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        AI Client                             │
│              (Claude, Cursor, OpenCode, etc.)                │
└────────────────────────┬────────────────────────────────────┘
                         │ SSE Transport
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     MCP Server                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │Dictionary│  │ Product  │  │   Cart   │  │Word Trick│    │
│  │  Tools   │  │  Tools   │  │  Tools   │  │  Tool    │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP / Direct Lambda
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway / Lambda                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │Dictionary│  │ Product  │  │   Cart   │  │Word Trick│    │
│  │ Handler  │  │ Handler  │  │ Handler  │  │ Handler  │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└────────────────────────┬────────────────────────────────────┘
                         │ boto3
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      DynamoDB                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │Dictionary│  │ Product  │  │   Cart   │                  │
│  │  Table   │  │  Table   │  │  Table   │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- **Docker** + **Docker Compose**
- **Python 3.11+**
- **Terraform** (for infrastructure)

### 1. Start Local Infrastructure
```bash
docker-compose up -d
```

### 2. Deploy Infrastructure (Local)
```bash
terraform -chdir=infra/test init
terraform -chdir=infra/test apply
```

### 3. Run Tests
```bash
pip install pytest
python -m pytest api/tests/ -v
```

### 4. Start MCP Server
```bash
cd mcp-server
pip install -r requirements.txt
python mcp_server.py
```

The MCP server will be available at `http://localhost:8000/sse`.

## Project Structure

```
├── api/                          # Backend application
│   ├── dal/                      # Data Access Layer (DAOs)
│   ├── handlers/                 # Lambda entry points
│   ├── utils/                    # Domain classes & utilities
│   └── tests/                    # Unit & integration tests
├── mcp-server/                   # MCP server for AI integration
│   ├── mcp_server.py             # FastMCP server implementation
│   ├── Dockerfile                # Container definition
│   └── requirements.txt          # Python dependencies
├── infra/                        # Infrastructure as Code (Terraform)
│   ├── modules/crud/             # Reusable infrastructure module
│   ├── test/                     # Local environment (Floci)
│   └── prod/                     # Production environment (AWS)
├── docker-compose.yml            # Local services orchestration
└── README.md                     # This file
```

## Key Components

### API (`api/`)
Serverless Lambda functions handling CRUD operations for:
- **Dictionary** — Word definitions
- **Product** — E-commerce products with UUIDs
- **Shopping Cart** — Carts storing full product snapshots
- **Word Trick** — String manipulation utility

See [API README](api/README.md) for detailed documentation.

### MCP Server (`mcp-server/`)
Exposes all API operations as MCP tools accessible by AI clients:
- 20 tools across 4 domains
- SSE transport for broad client compatibility
- Dual-mode product addition (snapshot or auto-fetch)

See [MCP Server README](mcp-server/README.md) for tool reference.

### Infrastructure (`infra/`)
Terraform-managed infrastructure with environment separation:
- **test/** — Local deployment via Floci (Docker-based AWS emulator)
- **prod/** — Real AWS deployment (DynamoDB, Lambda, API Gateway, ECS)

See [Infrastructure README](infra/README.md) for deployment guide.

## Adding New Features

### 1. Define the Domain Model
Create or update classes in `api/utils/`:
```python
# api/utils/my_feature.py
class MyFeature:
    def __init__(self, ...): ...
    def to_dict(self) -> dict: ...
    @staticmethod
    def from_dict(data: dict) -> "MyFeature": ...
```

### 2. Create the DAO
Add a new DAO in `api/dal/`:
```python
# api/dal/my_feature_dao.py
class MyFeatureDAO:
    def create(self, ...) -> dict: ...
    def read(self, ...) -> dict: ...
    def update(self, ...) -> dict: ...
    def delete(self, ...) -> dict: ...
    def list_all(self) -> list: ...
```

### 3. Create the Lambda Handler
Add a handler in `api/handlers/`:
```python
# api/handlers/my_feature_handler.py
def handler(event, context):
    operation, payload = parse_event(event or {})
    dao = MyFeatureDAO(get_dynamodb_resource())
    # Route operations...
```

### 4. Update Infrastructure
- Add DynamoDB table in `infra/modules/crud/main.tf`
- Add Lambda function and API Gateway routes
- Update `infra/test/main.tf` and `infra/prod/main.tf` with zip artifacts

### 5. Add MCP Tools
Add tools in `mcp-server/mcp_server.py`:
```python
@mcp.tool()
def my_feature_create(...) -> CallToolResult:
    return _call_api("POST", "/my-feature", {...})
```

### 6. Write Tests
- Unit tests in `api/tests/test_my_feature.py`
- Integration tests in `api/tests/test_my_feature_integration.py`

### 7. Deploy & Verify
```bash
terraform -chdir=infra/test apply
python -m pytest api/tests/ -v
docker-compose down mcp-server && docker-compose build mcp-server && docker-compose up -d mcp-server
```

## Testing Strategy

| Test Type | Location | Purpose |
|-----------|----------|---------|
| Unit tests | `api/tests/test_*_unit.py` | Test DAOs, handlers, utils in isolation |
| Integration tests | `api/tests/test_*_integration.py` | Test against real DynamoDB (Floci) |
| Handler unit tests | `api/tests/test_handlers_unit.py` | Test operation routing with mocked DAOs |

Run all tests:
```bash
python -m pytest api/tests/ -v
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STAGE` | `local` | Deployment stage (`local` or `prod`) |
| `AWS_ENDPOINT_URL` | `http://localhost:4566` | DynamoDB endpoint override |
| `API_BASE_URL` | `http://localhost:4566` | MCP server API base URL |
| `API_ID` | `""` | API Gateway ID (empty = direct Lambda) |
| `CART_TAX_RATE` | `0.07` | Default tax rate for cart totals |

## License

MIT
