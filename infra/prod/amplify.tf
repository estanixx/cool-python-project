# AWS Amplify hosting for the Next.js SSR website.
#
# The repository is linked via a GitHub Personal Access Token stored in
# GitHub Secrets (GH_PAT) and passed as var.github_token during terraform apply.
# Auto-build is DISABLED — builds are triggered manually via GitHub Actions
# when website/ files change (see .github/workflows/deploy-amplify.yml).

resource "aws_amplify_app" "website" {
  name       = "cool-python-project-website"
  repository = "https://github.com/estanixx/cool-python-project"
  access_token = var.github_token

  platform                   = "WEB_COMPUTE"
  enable_auto_branch_creation = false

  build_spec = <<-EOT
    version: 1
    frontend:
      phases:
        preBuild:
          commands:
            - cd website && npm ci
        build:
          commands:
            - cd website && npm run build
      artifacts:
        baseDirectory: website/.next
        files:
          - '**/*'
      cache:
        paths:
          - website/node_modules/**/*
  EOT

  environment_variables = {
    NEXT_PUBLIC_API_URL = module.crud.api_endpoint
    NODE_ENV            = "production"
  }

  tags = {
    Project   = "cool-python-project"
    ManagedBy = "terraform"
  }
}

resource "aws_amplify_branch" "main" {
  app_id      = aws_amplify_app.website.id
  branch_name = "main"

  # CRITICAL: Do NOT auto-build on git push. We control this via GitHub Actions.
  enable_auto_build = false

  tags = {
    Project   = "cool-python-project"
    ManagedBy = "terraform"
  }
}
