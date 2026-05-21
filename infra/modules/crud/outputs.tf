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

output "api_id" {
  description = "API Gateway ID."
  value       = aws_apigatewayv2_api.crud_api.id
}

output "mcp_ecr_repository_url" {
  description = "ECR repository URL for MCP server image."
  value       = var.enable_ecs ? aws_ecr_repository.mcp_server[0].repository_url : null
}

output "mcp_service_endpoint" {
  description = "MCP server service endpoint (ALB DNS when enabled, fallback otherwise)."
  value = var.enable_alb && var.enable_ecs ? "http://${aws_lb.mcp[0].dns_name}" : (
    var.enable_ecs ? "http://${aws_ecs_service.mcp_server[0].id}" : null
  )
}

output "alb_dns_name" {
  description = "ALB DNS name (only when enable_alb=true)."
  value       = var.enable_alb ? aws_lb.mcp[0].dns_name : null
}

output "alb_arn" {
  description = "ALB ARN (only when enable_alb=true)."
  value       = var.enable_alb ? aws_lb.mcp[0].arn : null
}

output "alb_security_group_id" {
  description = "ALB security group ID (only when enable_alb=true)."
  value       = var.enable_alb ? aws_security_group.alb[0].id : null
}

output "public_subnet_ids" {
  description = "Public subnet IDs for ALB (only when enable_alb=true)."
  value       = var.enable_alb ? aws_subnet.public[*].id : null
}

output "private_subnet_ids" {
  description = "Private subnet IDs for ECS Fargate (only when enable_alb=true)."
  value       = var.enable_alb ? aws_subnet.private[*].id : null
}

output "vpc_id" {
  description = "VPC ID (only when enable_alb=true)."
  value       = var.enable_alb ? aws_vpc.main[0].id : null
}

output "aws_endpoint_url" {
  description = "Endpoint override in use (if any)."
  value       = var.aws_endpoint_url
}

output "dashboard_name" {
  description = "CloudWatch dashboard name."
  value       = var.enable_observability ? aws_cloudwatch_dashboard.main[0].dashboard_name : null
}

output "dashboard_arn" {
  description = "CloudWatch dashboard ARN."
  value       = var.enable_observability ? aws_cloudwatch_dashboard.main[0].dashboard_arn : null
}

output "sns_topic_arn" {
  description = "SNS topic ARN for alarm notifications."
  value       = var.enable_observability ? aws_sns_topic.alarm_notifications[0].arn : null
}

output "alarm_arns" {
  description = "CloudWatch alarm ARNs."
  value = var.enable_observability ? {
    mcp_tool_errors   = aws_cloudwatch_metric_alarm.mcp_tool_errors[0].arn
    apigw_5xx         = aws_cloudwatch_metric_alarm.apigw_5xx[0].arn
    ecs_cpu           = aws_cloudwatch_metric_alarm.ecs_cpu[0].arn
    ecs_memory        = aws_cloudwatch_metric_alarm.ecs_memory[0].arn
    alb_healthy_hosts = var.enable_alb ? aws_cloudwatch_metric_alarm.alb_healthy_hosts[0].arn : null
  } : null
}

output "word_trick_lambda_arn" {
  description = "Word Trick Lambda function ARN (null if enable_word_trick=false)."
  value       = var.enable_word_trick ? aws_lambda_function.word_trick[0].arn : null
}

output "ecs_cluster_name" {
  description = "ECS cluster name (null if enable_ecs=false)."
  value       = var.enable_ecs ? aws_ecs_cluster.mcp[0].name : null
}
