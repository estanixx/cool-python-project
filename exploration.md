## Exploration: GitHub Actions CI/CD Pipeline

### Current State

**Infrastructure (Terraform):**
- `infra/modules/crud/main.tf` — Single reusable module containing: 3 DynamoDB tables, IAM roles/policies, 3 Lambda functions, API Gateway v2 (HTTP), Lambda permissions, and **ECS Fargate for MCP server** (prod-only via `count = var.stage == "prod"`)
- `infra/prod/` — Production environment: real AWS, auto-generates Lambda zips via `data.archive_file`, hardcoded test credentials in `providers.tf`
- `infra/test/` — Local environment: Floci (localhost:4566), includes additional `word_trick` Lambda not in prod
- ECS Fargate exists but has **NO ALB, NO autoscaling** — plain service with `assign_public_ip = true` and security group allowing `0.0.0.0/0` on port 8000
- ECR repository created for MCP server image (`mcp-server-prod`)
- Uses default VPC and default subnets (not production-grade networking)

**Application:**
- `api/` — Python Lambda handlers with DAL layer (boto3 DynamoDB), tests use `unittest` (NOT pytest despite user mention)
- `mcp-server/` — Python MCP server using FastMCP + uvicorn on port 8000, Dockerfile exists
- `docker-compose.yml` — Local dev with Floci + MCP server

**CI/CD:**
- **No `.github/` directory exists** — completely greenfield
- Only `main` branch exists — `prod` branch needs to be created
- No existing workflows, actions, or CI configuration

**Tests:**
- Unit tests: `test_handlers_unit.py`, `test_dal_unit.py`, `test_infra_unit.py`, `test_word_trick.py` — use mocks, no external deps
- Integration tests: `test_dictionary_integration.py`, `test_product_integration.py`, `test_shopping_cart_integration.py` — need Floci running

### Affected Areas

- `infra/modules/crud/main.tf` — Needs ALB, target group, autoscaling resources added to ECS section
- `infra/modules/crud/variables.tf` — Needs new variables for ALB config, autoscaling params
- `infra/modules/crud/outputs.tf` — Needs ALB DNS output, service endpoint changes
- `infra/prod/providers.tf` — Needs real AWS auth (OIDC or credentials) — currently has hardcoded test creds
- `.github/workflows/` — New directory with CI/CD workflow files
- `.gitignore` — May need updates for GitHub Actions artifacts
- `mcp-server/Dockerfile` — May need multi-stage build or health check endpoint for ALB

### Approaches

#### 1. Single Monolithic Workflow
One `.github/workflows/ci-cd.yml` file with all jobs (test, build, deploy) controlled by `if` conditions and path filters.

- **Pros:** Simple to understand, single file, easy to trace execution
- **Cons:** Large file, harder to maintain, all jobs in one place
- **Effort:** Low
- **Best for:** Small teams, simple pipelines

#### 2. Multi-Workflow with Reusable Workflows
Separate workflows: `test.yml` (runs on all PRs), `deploy.yml` (runs on prod pushes), with reusable workflow components.

- **Pros:** Clean separation, reusable components, better parallelism
- **Cons:** More files, slightly more complex orchestration
- **Effort:** Medium
- **Best for:** Growing projects, multiple deployment targets

#### 3. Terraform-Managed OIDC + Multi-Workflow (Recommended)
Use Terraform to provision the GitHub OIDC provider and IAM roles (infrastructure-as-code for auth), combined with separate workflows for test and deploy.

- **Pros:** No long-lived AWS secrets, auditable auth setup, clean separation of concerns
- **Cons:** Requires one-time manual OIDC provider setup or bootstrapping
- **Effort:** Medium-High
- **Best for:** Production-grade security, teams following IaC best practices

### Detailed Recommendations

#### AWS Authentication: OIDC (Strongly Recommended)

**Why OIDC over secrets:**
- No long-lived access keys to rotate or leak
- Credentials scoped to specific repo/branch/workflow
- Automatic expiration after workflow completes
- Industry best practice for GitHub + AWS integration

**Setup requires:**
1. Create OIDC identity provider in AWS (thumbprint: `6938fd4d98bab03faadb97b34396831e31db1dd8`)
2. Create IAM role with trust policy allowing `sts:AssumeRoleWithWebIdentity`
3. Condition: `StringLike: token.actions.githubusercontent.com:sub = "repo:OWNER/REPO:ref:refs/heads/prod"`
4. Attach policies: `AmazonECRFullAccess`, `AmazonECS_FullAccess`, `AmazonAPIGatewayAdministrator`, `AWSLambdaFullAccess`, `AmazonDynamoDBFullAccess`, `IAM` (for role creation)

**Alternative (simpler but less secure):** Store `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` as GitHub repository secrets. Use `aws-actions/configure-aws-credentials@v4` action.

#### Change Detection Strategy

**Option A: Native `paths` filter (simpler)**
```yaml
on:
  push:
    branches: [prod]
    paths:
      - 'mcp-server/**'
      - 'api/**'
      - 'infra/**'
      - '.github/workflows/**'
```
- Pros: Built-in, no external action needed
- Cons: Less granular — can't distinguish api changes from mcp-server changes

**Option B: `dorny/paths-filter@v3` (recommended)**
```yaml
- uses: dorny/paths-filter@v3
  id: filter
  with:
    filters: |
      api:
        - 'api/**'
      mcp-server:
        - 'mcp-server/**'
      infra:
        - 'infra/**'
      workflow:
        - '.github/workflows/**'
```
- Pros: Granular control, can skip ECR build if only API changed
- Cons: External dependency, requires checkout first

**Recommendation:** Use `dorny/paths-filter@v3` for granular control. Skip ECR build when only `api/**` or `infra/**` changed (no MCP server code changes). Always run Terraform when `infra/**` or `.github/workflows/**` changed.

#### ECR Login and Docker Build/Push

```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
    aws-region: us-east-1

- name: Login to Amazon ECR
  id: login-ecr
  uses: aws-actions/amazon-ecr-login@v2

- name: Build and push Docker image
  env:
    ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
    ECR_REPOSITORY: mcp-server-prod
    IMAGE_TAG: ${{ github.sha }}
  run: |
    docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG -t $ECR_REGISTRY/$ECR_REPOSITORY:latest ./mcp-server
    docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
    docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest
```

**Key patterns:**
- Tag with commit SHA for traceability (NOT just `latest`)
- Push both SHA tag and `latest` tag
- Use `aws-actions/amazon-ecr-login@v2` (official AWS action)

#### ECS Deployment After Image Push

After pushing new image to ECR, update the ECS service:

```yaml
- name: Update ECS task definition
  id: task-def
  uses: aws-actions/amazon-ecs-render-task-definition@v1
  with:
    task-definition: infra/prod/.terraform/artifacts/mcp-task-def.json
    container-name: mcp-server
    image: ${{ steps.login-ecr.outputs.registry }}/mcp-server-prod:${{ github.sha }}

- name: Deploy to ECS
  uses: aws-actions/amazon-ecs-deploy-task-definition@v2
  with:
    task-definition: ${{ steps.task-def.outputs.task-definition }}
    service: mcp-server-service-prod
    cluster: mcp-cluster-prod
    wait-for-service-stability: true
```

**Important:** The current Terraform module embeds the image directly in `container_definitions`. For CI/CD, you have two options:
1. **Terraform-first:** Run `terraform apply` after image push (Terraform detects image URL change)
2. **ECS action-first:** Use `amazon-ecs-render-task-definition` to create a new revision, then deploy

**Recommendation:** Use Terraform for infrastructure (ALB, autoscaling) and ECS actions for image updates. This avoids Terraform state lock issues during deployments and allows faster rollbacks.

#### ALB + Target Group Configuration

The current ECS service needs these additions in `infra/modules/crud/main.tf`:

```hcl
# ALB
resource "aws_lb" "mcp" {
  count              = var.stage == "prod" ? 1 : 0
  name               = "mcp-alb-${var.stage}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb[0].id]
  subnets            = data.aws_subnets.default[0].ids
}

# Target Group
resource "aws_lb_target_group" "mcp" {
  count       = var.stage == "prod" ? 1 : 0
  name        = "mcp-tg-${var.stage}"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default[0].id
  target_type = "ip"  # Fargate uses awsvpc network mode

  health_check {
    path                = "/health"  # MCP server needs health endpoint
    protocol            = "HTTP"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 3
    unhealthy_threshold = 3
  }
}

# Listener
resource "aws_lb_listener" "mcp" {
  count             = var.stage == "prod" ? 1 : 0
  load_balancer_arn = aws_lb.mcp[0].arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.mcp[0].arn
  }
}
```

**Security group changes:**
- ALB SG: Allow inbound HTTP (80) from `0.0.0.0/0`
- ECS SG: Allow inbound 8000 ONLY from ALB SG (not `0.0.0.0/0`)

**MCP server health endpoint:** The current `mcp_server.py` has no `/health` endpoint. Need to add one:
```python
@mcp.tool()  # or as a raw HTTP route
# Better: add a simple Flask/FastAPI health route alongside MCP
```
Actually, the MCP server uses uvicorn + SSE. The SSE endpoint at `/sse` can serve as a health check (returns 200 when server is running). Use `path: /sse` for health check.

#### ECS Autoscaling Configuration

```hcl
# Application Auto Scaling
resource "aws_appautoscaling_target" "mcp" {
  count              = var.stage == "prod" ? 1 : 0
  max_capacity       = 4
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.mcp[0].name}/${aws_ecs_service.mcp_server[0].name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# Scale on CPU
resource "aws_appautoscaling_policy" "mcp_cpu" {
  count              = var.stage == "prod" ? 1 : 0
  name               = "mcp-cpu-scaling-${var.stage}"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.mcp[0].resource_id
  scalable_dimension = aws_appautoscaling_target.mcp[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.mcp[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 50.0
    scale_in_cooldown  = 60
    scale_out_cooldown = 60
  }
}

# Scale on Memory
resource "aws_appautoscaling_policy" "mcp_memory" {
  count              = var.stage == "prod" ? 1 : 0
  name               = "mcp-memory-scaling-${var.stage}"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.mcp[0].resource_id
  scalable_dimension = aws_appautoscaling_target.mcp[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.mcp[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value       = 70.0
    scale_in_cooldown  = 60
    scale_out_cooldown = 60
  }
}
```

**ECS service update:** Add `load_balancer` block:
```hcl
resource "aws_ecs_service" "mcp_server" {
  # ... existing config ...
  load_balancer {
    target_group_arn = aws_lb_target_group.mcp[0].arn
    container_name   = "mcp-server"
    container_port   = 8000
  }
}
```

#### Recommended Workflow Structure

```
.github/workflows/
├── ci.yml              # Runs on PRs to any branch: lint + unit tests
└── cd.yml              # Runs on push to prod: test + build + deploy
```

**`ci.yml`** — Runs on every PR:
- Checkout code
- Run unit tests (no Floci needed): `python -m unittest discover -s api/tests -p 'test_*_unit.py'`
- (Optional) Run Docker build validation (no push)

**`cd.yml`** — Runs on push to `prod`:
1. **Change Detection** — `dorny/paths-filter` to detect what changed
2. **Unit Tests** — Always run
3. **Integration Tests** — Spin up Floci via Docker Compose, run integration tests
4. **Build & Push MCP Image** — Only if `mcp-server/**` changed
5. **Terraform Plan/Apply** — Only if `infra/**` changed
6. **Deploy ECS** — Only if MCP image was built (force new deployment)

#### Terraform State Management

**Current issue:** No remote state backend. State files are local (`.terraform/` is gitignored).

**Options:**
1. **S3 + DynamoDB backend** (recommended for production):
   ```hcl
   terraform {
     backend "s3" {
       bucket         = "my-terraform-state"
       key            = "prod/terraform.tfstate"
       region         = "us-east-1"
       dynamodb_table = "terraform-locks"
       encrypt        = true
     }
   }
   ```
2. **GitHub Actions cache** (simpler, but not recommended for prod): Use `hashicorp/setup-terraform@v3` with local state
3. **Keep local** (current): Works for single-developer, but risky for CI/CD

**Recommendation:** Add S3 backend as part of this change. Create the S3 bucket and DynamoDB table via a separate bootstrap step or manually first.

### Risks

1. **Health endpoint missing** — MCP server has no `/health` endpoint. ALB health checks will fail. Must add health endpoint or use `/sse` as health path.
2. **Default VPC usage** — Current ECS uses default VPC with public subnets. Production should use dedicated VPC with public/private subnets. Out of scope for this change but should be noted.
3. **Terraform state locking** — Without remote state, concurrent runs could corrupt state. S3 backend needed.
4. **`prod` branch doesn't exist** — Must be created before workflow can trigger on it.
5. **Hardcoded test credentials** — `infra/prod/providers.tf` has `access_key = "test"`. Must be removed/updated for real AWS auth.
6. **ECR repository already exists** — If Terraform already created it, the workflow should use the existing repo, not try to create a new one.
7. **Lambda zip generation in CI** — `data.archive_file` runs during `terraform plan`. CI runner needs Python source files accessible from the Terraform working directory.
8. **Tests are unittest, not pytest** — User mentioned pytest but codebase uses `unittest`. Pipeline should run `python -m unittest discover`.

### Ready for Proposal

**Yes.** Enough information has been gathered to create a comprehensive change proposal. The proposal should cover:

1. **ALB + Target Group + Listener** — New Terraform resources in `modules/crud/`
2. **ECS Autoscaling** — Application Auto Scaling with target tracking policies
3. **Security Group hardening** — Restrict ECS SG to ALB-only ingress
4. **GitHub Actions workflows** — `ci.yml` (tests) + `cd.yml` (deploy on prod)
5. **AWS OIDC authentication** — IAM role for GitHub Actions
6. **Change detection** — `dorny/paths-filter` for granular job control
7. **ECR build/push** — Conditional on MCP server changes
8. **Terraform remote state** — S3 + DynamoDB backend (or document as prerequisite)
9. **Health endpoint** — Add `/health` or configure ALB to use `/sse`
