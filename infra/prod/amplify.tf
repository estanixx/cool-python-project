# AWS Amplify hosting for the Next.js SSR website.

# IAM role that Amplify assumes to access the repository and deploy.
resource "aws_iam_role" "amplify_app_role" {
  name = "cool-python-project-amplify-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "amplify.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Project   = "cool-python-project"
    ManagedBy = "terraform"
  }
}

# Inline policy granting Amplify access to the GitHub repository.
resource "aws_iam_role_policy" "amplify_app_policy" {
  name = "cool-python-project-amplify-policy"
  role = aws_iam_role.amplify_app_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "amplify:*",
          "codecommit:GetBranch",
          "codecommit:GetRepository",
          "codecommit:GetCommit",
          "codecommit:GitPull",
          "codecommit:UploadArchive",
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}

# Amplify application linked to the GitHub repository.
resource "aws_amplify_app" "website" {
  name                 = "cool-python-project-website"
  repository           = "https://github.com/estanixx/cool-python-project"
  platform             = "WEB_COMPUTE"
  iam_service_role_arn = aws_iam_role.amplify_app_role.arn

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

# Amplify branch for the feature branch (change this to "main" after merge).
resource "aws_amplify_branch" "website_main" {
  app_id      = aws_amplify_app.website.id
  branch_name = "feat/website-and-deployment"

  # Enable auto-build on push.
  enable_auto_build = true

  tags = {
    Project   = "cool-python-project"
    ManagedBy = "terraform"
  }
}
