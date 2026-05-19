# AWS Amplify hosting for the Next.js SSR website.
#
# IMPORTANT: The repository is NOT linked via Terraform because it requires
# a GitHub OAuth token. After `terraform apply`, connect the repository
# manually via the Amplify Console:
#   1. Open the Amplify app
#   2. "Connect repository" → GitHub → authorize
#   3. Select estanixx/cool-python-project, branch feat/website-and-deployment
#   4. The build spec (amplify.yml) is auto-detected

resource "aws_amplify_app" "website" {
  name     = "cool-python-project-website"
  platform = "WEB_COMPUTE"

  # Build spec is defined in amplify.yml at the repo root.
  # Amplify auto-detects it; no need to inline it here.

  environment_variables = {
    NEXT_PUBLIC_API_URL = module.crud.api_endpoint
    NODE_ENV            = "production"
  }

  tags = {
    Project   = "cool-python-project"
    ManagedBy = "terraform"
  }
}
