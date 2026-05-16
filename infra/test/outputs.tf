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
