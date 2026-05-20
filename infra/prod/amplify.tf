# AWS Amplify hosting for the Next.js SSR website.
#
# The repository is linked via a GitHub Personal Access Token stored in
# GitHub Secrets (GH_PAT) and passed as var.github_token during terraform apply.
# Auto-build is DISABLED — builds are triggered from the CD workflow
# when website/ files change (see .github/workflows/cd.yml, job: deploy-amplify).

resource "aws_amplify_app" "website" {
  name = "cool-python-project-website"

  # Only link the repository when github_token is provided (non-empty).
  # When empty/token not set, the app is created without a repo link,
  # and you must connect via the Amplify Console manually.
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
                - npm ci
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
