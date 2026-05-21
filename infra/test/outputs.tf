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
  description = "API Gateway HTTP endpoint."
  value       = module.crud.api_endpoint
}

output "api_id" {
  description = "API Gateway ID."
  value       = module.crud.api_id
}
