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

output "aws_endpoint_url" {
  description = "Endpoint override in use (if any)."
  value       = var.aws_endpoint_url
}
