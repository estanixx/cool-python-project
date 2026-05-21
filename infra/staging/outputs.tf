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

output "mcp_alb_dns_name" {
  description = "ALB DNS name for MCP server (null if enable_alb=false)."
  value       = module.crud.alb_dns_name
}

output "mcp_service_endpoint" {
  description = "MCP server service endpoint URL."
  value       = module.crud.mcp_service_endpoint
}

output "word_trick_lambda_arn" {
  description = "Word Trick Lambda function ARN."
  value       = module.crud.lambda_arns.word_trick
}

output "ecs_cluster_name" {
  description = "ECS cluster name."
  value       = module.crud.mcp_ecr_repository_url != null ? "mcp-cluster-${var.stage}" : null
}

output "sns_topic_arn" {
  description = "SNS topic ARN for alarm notifications."
  value       = module.crud.sns_topic_arn
}

output "alarm_arns" {
  description = "CloudWatch alarm ARNs."
  value       = module.crud.alarm_arns
}

output "dashboard_name" {
  description = "CloudWatch dashboard name."
  value       = module.crud.dashboard_name
}

output "amplify_app_id" {
  description = "AWS Amplify application ID."
  value       = aws_amplify_app.website.id
}

output "amplify_branch_url" {
  description = "AWS Amplify app URL for staging branch."
  value       = "https://staging.${aws_amplify_app.website.id}.amplifyapp.com"
}

output "amplify_default_domain" {
  description = "Amplify default domain for the website."
  value       = aws_amplify_app.website.default_domain
}
