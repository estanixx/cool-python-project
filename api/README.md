# API — Serverless Backend

Lambda-based Python backend providing CRUD operations for Dictionary, Product, Shopping Cart, and Word Trick domains.

## Architecture

```
api/
├── dal/              # Data Access Layer — DynamoDB DAOs
├── handlers/         # Lambda entry points — route operations
├── utils/            # Domain classes & utilities
└── tests/            # Unit & integration tests
```

### Layer Responsibilities

| Layer | Purpose | Files |
|-------|---------|-------|
| **DAL** | Database operations, validation, error handling | `dal/*_dao.py` |
| **Handlers** | Event parsing, operation routing, response formatting | `handlers/*_handler.py` |
| **Utils** | Domain models, serialization, business logic | `utils/*.py` |

## Domain Models

### Dictionary
- **Partition Key**: `Word` (String, capitalized)
- **Attributes**: `definition` (String)
- **Operations**: create, read, update, delete, list

### Product
- **Partition Key**: `uuid` (String, UUID format)
- **Attributes**: `name` (String), `price` (Number/Decimal)
- **Operations**: create, read, update, delete, list, search

### Shopping Cart
- **Partition Key**: `UUID` (String, uppercase)
- **Attributes**: `products` (List of Maps: `{uuid, name, price}`)
- **Operations**: create, read, update, delete, add_product, remove_product, get_total

### Word Trick
- **No persistence** — stateless string manipulation
- **Operation**: apply word trick algorithm

## Data Access Layer (DAL)

### Base Pattern
Each DAO follows this pattern:
```python
class ExampleDAO:
    def __init__(self, dynamodb_resource):
        self.table = dynamodb_resource.Table(self._table_name())
    
    def create(self, ...) -> dict: ...
    def read(self, ...) -> dict: ...
    def update(self, ...) -> dict: ...
    def delete(self, ...) -> dict: ...
```

### Key Files

| File | Purpose |
|------|---------|
| `dal/db_client.py` | DynamoDB resource creation with stage-aware endpoint |
| `dal/errors.py` | Custom exceptions: `NotFoundError`, `ValidationError`, `DynamoError` |
| `dal/dictionary_dao.py` | Dictionary CRUD + `list_all()` |
| `dal/product_dao.py` | Product CRUD + `list()` + `search(term)` |
| `dal/shopping_cart_dao.py` | Cart CRUD + `add_product()` + `remove_product()` + `get_total()` |

### Important Patterns

**Decimal Handling**: DynamoDB returns numbers as `Decimal`. Always convert:
```python
from decimal import Decimal
price = Decimal(str(price))  # On write
float(price)                 # On read/serialization
```

**Reserved Keywords**: DynamoDB reserved words (`Word`, `uuid`, `UUID`, `name`, `price`) require `ExpressionAttributeNames`:
```python
ExpressionAttributeNames={"#pk": "Word", "#nm": "name"}
```

**Normalization**: Keys are normalized consistently:
- Dictionary words → `capitalize()`
- Cart IDs → `strip().upper()`
- Product UUIDs → `uuid.UUID()` validation

## Handlers

### Event Parsing
`handlers/utils.py` provides `parse_event()` which handles:
- **API Gateway v2 format** — HTTP method → operation mapping, query/path params
- **Legacy format** — Direct `{"operation": "...", "payload": {...}}`

### Operation Routing
Each handler routes operations:
```python
def handler(event, context):
    operation, payload = parse_event(event or {})
    dao = ExampleDAO(get_dynamodb_resource())
    
    if operation == "create": ...
    if operation == "read": ...
    if operation == "list": ...
    # etc.
```

### Response Format
All handlers return API Gateway v2 format:
```python
{"statusCode": 200, "body": json.dumps(data, cls=_DecimalEncoder)}
```

## Utils Classes

### Product (`utils/shopping.py`)
```python
class Product:
    def __init__(self, name, price): ...
    def to_dict(self) -> dict: ...      # {uuid, name, price}
    @staticmethod
    def from_dict(data: dict) -> "Product": ...
```

### ShoppingCart (`utils/shopping.py`)
```python
class ShoppingCart:
    def add_product(self, product: Product): ...
    def remove_product(self, product_id): ...
    def total(self): ...                 # Handles dicts and Product objects
    def to_dict(self) -> dict: ...
    @staticmethod
    def from_dict(data: dict) -> "ShoppingCart": ...
```

### Dictionary (`utils/dictionary.py`)
```python
class Dictionary:
    def newentry(self, key, value): ...
    def look(self, key): ...
```

### Word Trick (`utils/word_trick.py`)
```python
def word_trick(sentence: str) -> str:
    """Returns i-th character of i-th word for each word."""
```

## Testing

### Test Structure
```
tests/
├── conftest.py                    # Test configuration, Floci helpers
├── test_dal_unit.py               # DAO unit tests (mocked table)
├── test_handlers_unit.py          # Handler routing tests (mocked DAOs)
├── test_*_integration.py          # Integration tests (real DynamoDB)
└── test_*.py                      # Domain-specific unit tests
```

### Running Tests
```bash
# All tests
python -m pytest api/tests/ -v

# Specific test file
python -m pytest api/tests/test_product_integration.py -v

# Unit tests only
python -m pytest api/tests/test_dal_unit.py api/tests/test_handlers_unit.py -v
```

### Test Configuration
- Tables are provisioned by Terraform (`infra/test/`)
- `conftest.py` clears data between tests
- Integration tests skip if Floci is unavailable

## Adding a New Domain

### 1. Create DAO
```python
# api/dal/my_domain_dao.py
class MyDomainDAO:
    def __init__(self, dynamodb_resource):
        self.table = dynamodb_resource.Table(self._table_name())
    
    def create(self, ...) -> dict: ...
    def read(self, ...) -> dict: ...
    # ... other operations
    
    def _table_name(self) -> str:
        return os.getenv("DYNAMODB_TABLE_MY_DOMAIN", "MyDomain")
```

### 2. Create Handler
```python
# api/handlers/my_domain_handler.py
def handler(event, context):
    operation, payload = parse_event(event or {})
    dao = MyDomainDAO(get_dynamodb_resource())
    # Route operations...
```

### 3. Update DAL Exports
```python
# api/dal/__init__.py
from .my_domain_dao import MyDomainDAO
```

### 4. Add Terraform Resources
- DynamoDB table in `infra/modules/crud/main.tf`
- Lambda function and API Gateway routes
- Zip artifact in `infra/test/main.tf` and `infra/prod/main.tf`

### 5. Write Tests
- Unit tests for DAO methods
- Integration tests against Floci
- Handler unit tests for operation routing

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `STAGE` | `local` | Deployment stage |
| `AWS_ENDPOINT_URL` | `http://localhost:4566` | DynamoDB endpoint |
| `DYNAMODB_TABLE_DICTIONARY` | `Dictionary` | Dictionary table name |
| `DYNAMODB_TABLE_PRODUCT` | `Product` | Product table name |
| `DYNAMODB_TABLE_SHOPPING_CART` | `ShoppingCart` | Cart table name |
| `CART_TAX_RATE` | `0.07` | Default cart tax rate |
