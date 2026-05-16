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
  value       = var.stage == "prod" ? aws_iam_role.lambda_role[0].arn : null
}

output "lambda_arns" {
  description = "Lambda function ARNs."
  value = var.stage == "prod" ? {
    dictionary    = aws_lambda_function.dictionary[0].arn
    product       = aws_lambda_function.product[0].arn
    shopping_cart = aws_lambda_function.shopping_cart[0].arn
  } : null
}

output "aws_endpoint_url" {
  description = "Endpoint override in use (if any)."
  value       = var.aws_endpoint_url
}
