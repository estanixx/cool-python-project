# CI/CD Pipelines

## CI (`ci.yml`)

Triggered on PRs to any branch and pushes to `main`.

| Job | What it does | Tools |
|-----|-------------|-------|
| **Python Tests** | Runs unit tests for API and MCP server | `unittest` |
| **Website TypeScript** | TypeScript compilation check for Next.js app | `tsc --noEmit` |
| **Terraform Validate** | Format check + `terraform validate` for test/prod | `terraform` |
| **Trivy Scan** | IaC security scan for `infra/` directory | `trivy-action` |
| **SonarQube Analysis** | Static analysis for Python, TypeScript, and IaC | `sonarcloud` |
| **OpenAPI Spec** | Lint API specification | `spectral` |

### SonarQube

Scans `api/`, `mcp-server/`, and `website/` source directories. Runs conditionally when `SONAR_TOKEN` is configured.

## CD (`cd.yml`)

Triggered on push to `main`. Deploys production infrastructure.

### Jobs

1. **Tests** — Runs Python unit tests (same as CI)
2. **Detect Changes** — `dorny/paths-filter` checks if `mcp-server/`, `api/`, `website/`, `infra/`, or `.github/workflows/` changed
3. **Build & Push** — Builds MCP server Docker image and pushes to ECR (skipped if no code changes)
4. **Deploy** — Runs `terraform apply` in `infra/prod` with the resolved image tag

### Change Detection

The deploy job only runs when relevant code changes:

```yaml
code_changed:
  - 'mcp-server/**'
  - 'api/**'
  - 'website/**'
  - 'infra/**'
  - '.github/workflows/*.yml'
```

## CodeQL (`codeql.yml`)

Triggered on PRs and weekly schedule. Analyzes Python and GitHub Actions for security vulnerabilities.

## Dependabot

Weekly dependency updates via `.github/dependabot.yml`:

| Ecosystem | Location | Groups |
|-----------|----------|--------|
| pip | `/api` | All deps in one PR |
| pip | `/mcp-server` | All deps in one PR |
| npm | `/website` | All deps in one PR |
| github-actions | `/` | All actions in one PR |
