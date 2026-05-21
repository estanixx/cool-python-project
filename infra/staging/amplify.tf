# AWS Amplify hosting for the Next.js SSR website (staging).
#
# Mirrors infra/prod/amplify.tf with staging suffix and staging branch.
# Auto-build is DISABLED — builds are triggered from the CD workflow
# when website/ files change.

resource "aws_amplify_app" "website" {
  name = "cool-python-project-website-staging"

  # Only link the repository when github_token is provided (non-empty).
  repository   = var.github_token != "" ? "https://github.com/estanixx/cool-python-project" : null
  access_token = var.github_token != "" ? var.github_token : null

  platform                    = "WEB_COMPUTE"
  enable_auto_branch_creation = false

  build_spec = <<-EOT
    version: 1
    applications:
      - appRoot: website
        frontend:
          phases:
            preBuild:
              commands:
                # Install devDependencies so TypeScript/@types/node are available in Amplify.
                - npm ci --include=dev
            build:
              commands:
                - npm run build
          artifacts:
            baseDirectory: .next
            files:
              - '**/*'
          cache:
            paths:
              - node_modules/**/*
  EOT

  environment_variables = {
    AMPLIFY_MONOREPO_APP_ROOT = "website"
    # Strip trailing slash to avoid // in frontend requests.
    # API_URL — available in SSR runtime (server components).
    API_URL = trimsuffix(module.crud.api_endpoint, "/")
    # NEXT_PUBLIC_API_URL — inlined at build time for client-side.
    NEXT_PUBLIC_API_URL = trimsuffix(module.crud.api_endpoint, "/")
    NODE_ENV            = "staging"
    AMPLIFY_YARN_ENABLE_IMMUTABLE_INSTALLS = "false"
  }

  tags = {
    Project   = "cool-python-project"
    Stage     = "staging"
    ManagedBy = "terraform"
  }
}

resource "aws_amplify_branch" "staging" {
  app_id      = aws_amplify_app.website.id
  branch_name = "staging"

  # CRITICAL: Do NOT auto-build on git push. We control this via GitHub Actions.
  enable_auto_build = false

  tags = {
    Project   = "cool-python-project"
    Stage     = "staging"
    ManagedBy = "terraform"
  }
}
