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
  description = "AWS Amplify app URL. Actual URL depends on the branch connected via Amplify Console."
  value       = "https://main.${aws_amplify_app.website.id}.amplifyapp.com"
}

output "mcp_alb_dns_name" {
  description = "ALB DNS name for MCP server (null if enable_alb=false)."
  value       = module.crud.alb_dns_name
}

output "mcp_service_endpoint" {
  description = "MCP server service endpoint URL."
  value       = module.crud.mcp_service_endpoint
}

output "amplify_default_domain" {
  description = "Amplify default domain for the website."
  value       = aws_amplify_app.website.default_domain
}
