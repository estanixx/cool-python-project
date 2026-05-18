output "table_names" {
  description = "DynamoDB table names."
  value       = module.crud.table_names
}

output "lambda_arns" {
  description = "Lambda ARNs."
  value       = module.crud.lambda_arns
}

output "lambda_role_arn" {
  description = "IAM role ARN for CRUD Lambdas."
  value       = module.crud.lambda_role_arn
}

output "api_endpoint" {
  description = "API Gateway HTTP endpoint URL."
  value       = module.crud.api_endpoint
}

output "amplify_app_id" {
  description = "AWS Amplify application ID."
  value       = aws_amplify_app.website.id
}

output "amplify_branch_url" {
  description = "AWS Amplify branch URL for the deployed website."
  value       = "https://${aws_amplify_branch.website_main.branch_name}.${aws_amplify_app.website.id}.amplifyapp.com"
}
