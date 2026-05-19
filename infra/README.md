# Infrastructure as Code — Terraform

## Directory Structure

```
infra/
├── modules/
│   └── crud/                 ← Reusable module (WHAT to deploy)
│       ├── main.tf           ←   DynamoDB, IAM, Lambda, API Gateway, Amplify
│       ├── variables.tf      ←   Input parameters
│       └── outputs.tf        ←   Output values (ARNs, endpoints)
├── test/                     ← Local environment (WHERE — Floci)
│   ├── main.tf               ←   Invokes "crud" module with stage=local + auto-zip
│   ├── providers.tf          ←   AWS provider → Floci (localhost:4566)
│   ├── variables.tf          ←   Variables with local defaults
│   └── terraform.tfvars      ←   Concrete values for local
├── prod/                     ← Production environment (WHERE — AWS real)
│   ├── main.tf               ←   Invokes "crud" module with stage=prod + auto-zip
│   ├── amplify.tf            ←   AWS Amplify app + branch for frontend
│   ├── providers.tf          ←   AWS provider → AWS real (no overrides)
│   └── variables.tf          ←   Variables with production defaults
├── Dockerfile.terraform      ←   Init container for local infra deploy
└── docker-entrypoint-terraform.sh
```

## What Each Directory Does

### `modules/crud/` — The WHAT (reusable module)

Defines **what resources** to create, without specifying **where**. It is a template reused across environments.

**Contains:**
- 3 DynamoDB tables (Dictionary, Product, ShoppingCart)
- IAM role + policy for Lambda
- 3 Lambda functions with environment variables
- API Gateway v2 (HTTP API) with routes and Lambda integrations
- Lambda permissions for API Gateway invocation

It does **not** know whether it deploys to Floci or AWS real. It only receives variables.

### `test/` — Local environment (Floci)

Deploys **everything** (DynamoDB + IAM + Lambda + API Gateway) to Floci (`localhost:4566`).

**Auto-generates Lambda zips** during `terraform plan` — no manual zip creation needed.

Used for:
- Local development
- Integration tests against local DynamoDB
- Validating code works before pushing to AWS

### `prod/` — Production environment (AWS real)

Deploys **everything** (DynamoDB + IAM + Lambda + API Gateway) to real AWS.

**Auto-generates Lambda zips** during `terraform plan` — same mechanism as `test/`.

## Why Use Modules?

Without modules, you would duplicate tables, IAM, Lambdas, and API Gateway in both `test/` and `prod/`. With a module:

| Without modules | With modules |
|-----------------|--------------|
| Define tables in `test/` | Define tables **once** in `modules/crud/` |
| Define tables in `prod/` | Invoke module from `test/` and `prod/` |
| Change something → edit 2 places | Change something → edit **1 place** |

The module is the **single source of truth** for what resources exist. Environments (`test/`, `prod/`) only specify **with what parameters** to invoke it.

## Workflow

### Local (development and tests)

```bash
# 1. Make sure Floci is running
docker-compose up -d

# 2. Deploy local infrastructure (DynamoDB + Lambda + API Gateway)
terraform -chdir=infra/test init     # only first time
terraform -chdir=infra/test apply

# 3. Run tests (use tables created by Terraform)
python3 -m unittest discover -s api/tests -v

# 4. Destroy infrastructure when done
terraform -chdir=infra/test destroy
```

### Production (AWS real)

```bash
# 1. Configure AWS credentials
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_DEFAULT_REGION="us-east-1"

# 2. Deploy infrastructure to AWS (DynamoDB + IAM + Lambda + API Gateway)
terraform -chdir=infra/prod init     # only first time
terraform -chdir=infra/prod plan     # review changes before applying
terraform -chdir=infra/prod apply

# 3. Lambda zips are auto-generated during plan/apply
#    No manual zip creation needed.
```

## Auto-Generated Lambda Zips

Both `test/` and `prod/` use `data "archive_file"` blocks that read Python source files and generate zips **during** `terraform plan`:

```hcl
data "archive_file" "dictionary" {
  type        = "zip"
  output_path = "${path.module}/.terraform/artifacts/dictionary.zip"

  source {
    content  = file("${local.backend_root}/handlers/dictionary_handler.py")
    filename = "api/handlers/dictionary_handler.py"
  }
  # ... more files (DAL, __init__.py, etc.)
}
```

Each Lambda package includes:
- Its specific handler
- Shared DAL (`db_client.py`, `errors.py`, `*_dao.py`)
- Required `__init__.py` files for Python imports

Zips are stored in `.terraform/artifacts/` (gitignored).

## API Gateway Endpoints

The module creates an HTTP API (v2) with these routes:

| Route | Lambda | Methods |
|-------|--------|---------|
| `ANY /dictionary` | `dictionary-local` / `dictionary-prod` | GET, POST, PUT, DELETE |
| `ANY /product` | `product-local` / `product-prod` | GET, POST, PUT, DELETE |
| `ANY /shopping-cart` | `shopping-cart-local` / `shopping-cart-prod` | GET, POST, PUT, DELETE |

### Testing locally via Floci

Floci exposes API Gateway on `localhost:4566`. The invoke URL format is:

```bash
API_ID=$(terraform -chdir=infra/test output -raw api_endpoint | grep -oP '(?<=//)[^.]+')

# Create dictionary entry
curl -X POST "http://localhost:4566/restapis/$API_ID/_user_request_/dictionary" \
  -H "Content-Type: application/json" \
  -d '{"operation":"create","payload":{"Word":"Apple","definition":"A fruit"}}'
```

> **Note:** Floci Lambda execution requires Docker socket access. If you see `Lambda.InitError`, ensure Docker is properly configured for WSL2 integration.

### Testing production via AWS

```bash
API_URL=$(terraform -chdir=infra/prod output -raw api_endpoint)

curl -X POST "$API_URL/dictionary" \
  -H "Content-Type: application/json" \
  -d '{"operation":"create","payload":{"Word":"Apple","definition":"A fruit"}}'
```

## Stage-Aware Configuration

The module uses `var.stage` to set Lambda environment variables:

```hcl
environment {
  variables = {
    STAGE            = var.stage
    AWS_ENDPOINT_URL = var.aws_endpoint_url
  }
}
```

This allows the same Lambda code to route to Floci (local) or AWS (prod) based on environment variables.

## Module Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `stage` | `local` | Deployment environment |
| `aws_region` | `us-east-1` | AWS region |
| `aws_endpoint_url` | `""` | Override for Floci (local dev) |
| `enable_alb` | `false` | Provision ALB + ECS for MCP server |
| `mcp_image_tag` | `"latest"` | ECS container image tag |
| `api_gateway_cors_origins` | `["*"]` | Allowed CORS origins for API Gateway — restrict to Amplify domain in prod |

## DynamoDB Tables

| Table | Partition Key | Attributes |
|-------|---------------|------------|
| Dictionary | `Word` (S) | `definition` (S) |
| Product | `uuid` (S) | `name` (S), `price` (N) |
| ShoppingCart | `UUID` (S) | `product_ids` (List) |

## Lambda Functions

| Name | Handler | Source |
|------|---------|--------|
| `dictionary-{stage}` | `api.handlers.dictionary_handler.handler` | `api/handlers/` |
| `product-{stage}` | `api.handlers.product_handler.handler` | `api/handlers/` |
| `shopping-cart-{stage}` | `api.handlers.shopping_cart_handler.handler` | `api/handlers/` |
| `word-trick-{stage}` | `api.handlers.word_trick_handler.handler` | `api/handlers/` |

Each Lambda zip includes its handler + all shared DAL modules + `__init__.py` files.

## AWS Amplify

The `prod/` environment creates an Amplify app for the Next.js frontend:

- **Platform**: `WEB_COMPUTE` (SSR)
- **Repository**: GitHub (`estanixx/cool-python-project`)
- **Build spec**: `amplify.yml` (repo root, `appRoot: website`)
- **Branch**: `feat/website-and-deployment` (update to `main` after merge)
- **Auto-build**: Enabled on push
- **Env vars**: `NEXT_PUBLIC_API_URL` set to API Gateway invoke URL

## ECS Production Deployment (Fargate)

The `prod/` environment optionally deploys an ECS Fargate service behind an ALB (when `enable_alb = true`). This is used for the MCP server (`mcp-server/`).

### How it works

The ECS task definition references the MCP server image via a **variable tag**:

```hcl
image = "${aws_ecr_repository.mcp_server[0].repository_url}:${var.mcp_image_tag}"
```

This avoids the circular dependency problem — Terraform never needs to resolve a data source at plan time. The tag is resolved by the CD pipeline (`cd.yml`):

| Scenario | `build-and-push` result | Tag passed to Terraform | Effect |
|----------|------------------------|------------------------|--------|
| Code changed | `success` | `${{ github.sha }}` | New image pushed → new tag → Terraform creates new task definition → **ECS auto-deploy** ✅ |
| Infra-only change | `skipped` | Currently deployed tag (queried from ECS) | Terraform sees no image change → applies infra changes without touching ECS task ✅ |
| First deploy | `success` | `${{ github.sha }}` | Terraform doesn't need the image to exist at plan time — only ECS needs it at runtime ✅ |

### Image tags in ECR

The ECR repository uses `image_tag_mutability = "IMMUTABLE"`. Each deploy pushes a **single tag** (`${{ github.sha }}`), never `latest`. This means:

- Every tag is unique and never overwritten
- No risk of overwriting a deployed tag
- Git SHA doubles as the image tag — full traceability from commit to running container

### First-time deploy

There is **no manual bootstrap needed** — the CD pipeline handles everything automatically:

1. `build-and-push` pushes the image to ECR (the repo either exists or Terraform creates it)
2. `deploy` runs `terraform apply -var="mcp_image_tag=${{ github.sha }}"` which creates the repo (if needed), task definition, service, etc.
3. ECS pulls the image and starts the service

### Key details

- The ECS repository uses `IMMUTABLE` tags — you cannot overwrite a tag once pushed. This is why `latest` is **never used**. Every deploy uses the commit SHA as the image tag.
- `terraform plan` does **not** validate that the image tag exists in ECR. Validation happens at runtime when ECS tries to pull the image. This is why a non-existent tag won't fail `terraform apply`, but will fail the ECS service deployment.
- If `build-and-push` is skipped (no code changes), the deploy job queries the **currently deployed ECS task definition** for its image tag and passes it to Terraform. This prevents Terraform from creating a task definition with a non-existent image tag.
