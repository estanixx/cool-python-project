output "table_names" {
  description = "DynamoDB table names."
  value = {
    dictionary    = aws_dynamodb_table.dictionary.name
    product       = aws_dynamodb_table.product.name
    shopping_cart = aws_dynamodb_table.shopping_cart.name
  }
}

output "table_arns" {
  description = "DynamoDB table ARNs."
  value = {
    dictionary    = aws_dynamodb_table.dictionary.arn
    product       = aws_dynamodb_table.product.arn
    shopping_cart = aws_dynamodb_table.shopping_cart.arn
  }
}

output "lambda_role_arn" {
  description = "IAM role ARN for CRUD Lambdas."
  value       = aws_iam_role.lambda_role.arn
}

output "lambda_arns" {
  description = "Lambda function ARNs."
  value = {
    dictionary    = aws_lambda_function.dictionary.arn
    product       = aws_lambda_function.product.arn
    shopping_cart = aws_lambda_function.shopping_cart.arn
  }
}

output "api_endpoint" {
  description = "API Gateway HTTP endpoint."
  value       = aws_apigatewayv2_stage.default.invoke_url
}

output "mcp_ecr_repository_url" {
  description = "ECR repository URL for MCP server image."
  value       = var.stage == "prod" ? aws_ecr_repository.mcp_server[0].repository_url : null
}

output "mcp_service_endpoint" {
  description = "MCP server service endpoint (if deployed)."
  value       = var.stage == "prod" ? "http://${aws_ecs_service.mcp_server[0].id}" : null
}

output "aws_endpoint_url" {
  description = "Endpoint override in use (if any)."
  value       = var.aws_endpoint_url
}
