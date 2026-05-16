You are an expert Cloud Software Architect and Senior Python Engineer. Your task is to implement a clean, decoupled serverless backend application adhering strictly to Software Design Document (SDD) and Test-Driven Development (TDD) best practices. 

### 1. Project Context & Current Layout
We have an existing codebase with core utilities located in `backend/utils/`. The root directories are structured under `infra/` (for Terraform) and `backend/` (for Python application logic).
The existing utilities include:
1. A Dictionary class that stores and retrieves words and definitions.
2. A Product class and a ShoppingCart class (a cart holds multiple products).
3. A Word Trick utility function.
Respective unit tests for these utilities already exist.

### 2. Objective
Build Python AWS Lambda functions that provide CRUD endpoints interacting with these entities. The data must be backed by Amazon DynamoDB. The entire local stack must deploy and test against **Floci** (running locally on `http://localhost:4566`), with seamless configurations to deploy to live **AWS** in production. Finally, expose these operations as a Model Context Protocol (MCP) server.

---

### 3. Technical Specifications

#### A. Architecture & Directory Rules
Do not write monolithic handlers. Split the backend using a clean, layered architecture:
*   `backend/utils/`: (Existing) Core business logic.
*   `backend/dal/`: Data Access Layer / Data Access Objects (DAOs) to isolate all DynamoDB `boto3` interactions. Write a unified database client that checks for an `AWS_ENDPOINT_URL` or `STAGE=local` env variable to route traffic to Floci (port 4566) or native AWS.
*   `backend/handlers/`: Clean Lambda functions that handle API Gateway JSON payloads, delegate database queries to the DAOs, and return formatted responses.
*   `infra/`: Infrastructure as Code directory.

#### B. DynamoDB Schema Map
*   **Dictionary Table:** Partition Key = `Word` (String) | Attribute = `Definition` (String)
*   **Product Table:** Partition Key = `uuid` (String) | Attributes = `name` (String), `price` (Number), `img` (String)
*   **ShoppingCart Table:** Partition Key = `UUID` (String) | Attribute = `product_ids` (List of Strings). *Crucial requirement:* Store ONLY product IDs in the shopping cart table, not full product objects.

---

### 4. Step-by-Step Implementation Required

#### Step 1: Software Design Document (SDD)
Generate a clean technical blueprint defining the module interactions, structural flow, and error-handling strategies. 

#### Step 2: Infrastructure as Code (`infra/` folder)
Write modular Terraform configurations using a `stage` variable (defaulting to `local`).
*   Configure the AWS provider block to dynamically route endpoint overrides to `http://localhost:4566` if `var.stage == "local"` to support Floci.
*   Define the 3 DynamoDB tables matching the schema map.
*   Define the Lambda resources and their respective code zip sources.
*   Write explicit IAM Execution Roles and Policies granting minimum-viable CRUD permissions to these specific DynamoDB tables.

#### Step 3: Layered Backend Implementation (`backend/` folder)
*   Implement the `db_client.py` engine mapping to Floci or live AWS.
*   Write individual DAOs for Dictionary, Product, and ShoppingCart operations.
*   Write the Lambda handler entry points ensuring clean JSON serialization and structured status responses.

#### Step 4: TDD Integration Testing Suite (`backend/tests/`)
*   Create a global `conftest.py` setting up the local test environment variables mapping to Floci.
*   Write comprehensive integration tests that execute CRUD actions against the live local Floci DynamoDB tables, asserting data parity and performing routine test state teardown.

#### Step 5: Convert to an MCP Server
*   Implement a separate Python entry point (`mcp_server.py`) using the official `mcp` SDK.
*   Wrap your developed DynamoDB DAOs as **MCP Tools** with descriptive metadata schemas so LLM agents know exactly when and how to invoke CRUD operations for the dictionary, products, and shopping carts.
*   Configure an SSE (Server-Sent Events) or HTTP-compatible transport layer wrapper matching standard MCP specs.

Provide the complete file implementations, fully commented, and structurally optimized for maximum maintainability.