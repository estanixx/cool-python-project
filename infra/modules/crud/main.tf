locals {
  tags = {
    Service = "serverless-crud-dynamodb-mcp"
    Stage   = var.stage
  }
}

resource "aws_dynamodb_table" "dictionary" {
  name         = var.table_names.dictionary
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "Word"

  attribute {
    name = "Word"
    type = "S"
  }

  tags = local.tags
}

resource "aws_dynamodb_table" "product" {
  name         = var.table_names.product
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "uuid"

  attribute {
    name = "uuid"
    type = "S"
  }

  tags = local.tags
}

resource "aws_dynamodb_table" "shopping_cart" {
  name         = var.table_names.shopping_cart
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "UUID"

  attribute {
    name = "UUID"
    type = "S"
  }

  tags = local.tags
}

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_role" {
  name               = var.lambda_role_name
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json

  tags = local.tags
}

data "aws_iam_policy_document" "crud_policy" {
  statement {
    sid = "DynamoCrud"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:Query",
      "dynamodb:Scan"
    ]
    resources = [
      aws_dynamodb_table.dictionary.arn,
      aws_dynamodb_table.product.arn,
      aws_dynamodb_table.shopping_cart.arn
    ]
  }
}

resource "aws_iam_policy" "crud_policy" {
  name   = "${var.lambda_role_name}-crud"
  policy = data.aws_iam_policy_document.crud_policy.json

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "crud_attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.crud_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_basic_attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "dictionary" {
  function_name    = var.lambda_function_names.dictionary
  role             = aws_iam_role.lambda_role.arn
  handler          = var.lambda_handler_names.dictionary
  runtime          = var.lambda_runtime
  timeout          = var.lambda_timeout
  filename         = var.lambda_artifacts.dictionary
  source_code_hash = filebase64sha256(var.lambda_artifacts.dictionary)

  environment {
    variables = {
      STAGE            = var.stage
      AWS_ENDPOINT_URL = var.lambda_env_endpoint_url != "" ? var.lambda_env_endpoint_url : var.aws_endpoint_url
    }
  }

  tags = local.tags
}

resource "aws_lambda_function" "product" {
  function_name    = var.lambda_function_names.product
  role             = aws_iam_role.lambda_role.arn
  handler          = var.lambda_handler_names.product
  runtime          = var.lambda_runtime
  timeout          = var.lambda_timeout
  filename         = var.lambda_artifacts.product
  source_code_hash = filebase64sha256(var.lambda_artifacts.product)

  environment {
    variables = {
      STAGE            = var.stage
      AWS_ENDPOINT_URL = var.lambda_env_endpoint_url != "" ? var.lambda_env_endpoint_url : var.aws_endpoint_url
    }
  }

  tags = local.tags
}

resource "aws_lambda_function" "shopping_cart" {
  function_name    = var.lambda_function_names.shopping_cart
  role             = aws_iam_role.lambda_role.arn
  handler          = var.lambda_handler_names.shopping_cart
  runtime          = var.lambda_runtime
  timeout          = var.lambda_timeout
  filename         = var.lambda_artifacts.shopping_cart
  source_code_hash = filebase64sha256(var.lambda_artifacts.shopping_cart)

  environment {
    variables = {
      STAGE            = var.stage
      AWS_ENDPOINT_URL = var.lambda_env_endpoint_url != "" ? var.lambda_env_endpoint_url : var.aws_endpoint_url
    }
  }

  tags = local.tags
}

# HTTP API (v2) for Lambda integration
resource "aws_apigatewayv2_api" "crud_api" {
  name          = "serverless-crud-${var.stage}"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
  }

  tags = local.tags
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.crud_api.id
  name        = "$default"
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "dictionary" {
  api_id             = aws_apigatewayv2_api.crud_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.dictionary.invoke_arn
  integration_method = "POST"
}

resource "aws_apigatewayv2_integration" "product" {
  api_id             = aws_apigatewayv2_api.crud_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.product.invoke_arn
  integration_method = "POST"
}

resource "aws_apigatewayv2_integration" "shopping_cart" {
  api_id             = aws_apigatewayv2_api.crud_api.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.shopping_cart.invoke_arn
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "dictionary" {
  api_id    = aws_apigatewayv2_api.crud_api.id
  route_key = "ANY /dictionary"
  target    = "integrations/${aws_apigatewayv2_integration.dictionary.id}"
}

resource "aws_apigatewayv2_route" "dictionary_item" {
  api_id    = aws_apigatewayv2_api.crud_api.id
  route_key = "ANY /dictionary/{word}"
  target    = "integrations/${aws_apigatewayv2_integration.dictionary.id}"
}

resource "aws_apigatewayv2_route" "product" {
  api_id    = aws_apigatewayv2_api.crud_api.id
  route_key = "ANY /product"
  target    = "integrations/${aws_apigatewayv2_integration.product.id}"
}

resource "aws_apigatewayv2_route" "product_item" {
  api_id    = aws_apigatewayv2_api.crud_api.id
  route_key = "ANY /product/{product_id}"
  target    = "integrations/${aws_apigatewayv2_integration.product.id}"
}

resource "aws_apigatewayv2_route" "shopping_cart" {
  api_id    = aws_apigatewayv2_api.crud_api.id
  route_key = "ANY /shopping-cart"
  target    = "integrations/${aws_apigatewayv2_integration.shopping_cart.id}"
}

resource "aws_apigatewayv2_route" "shopping_cart_item" {
  api_id    = aws_apigatewayv2_api.crud_api.id
  route_key = "ANY /shopping-cart/{cart_id}"
  target    = "integrations/${aws_apigatewayv2_integration.shopping_cart.id}"
}

# Lambda permissions for API Gateway
resource "aws_lambda_permission" "dictionary" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dictionary.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.crud_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "product" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.product.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.crud_api.execution_arn}/*/*"
}

resource "aws_lambda_permission" "shopping_cart" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.shopping_cart.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.crud_api.execution_arn}/*/*"
}

# --- ECS Fargate for MCP Server (Production only) ---

resource "aws_ecr_repository" "mcp_server" {
  count        = var.stage == "prod" ? 1 : 0
  name         = "mcp-server-${var.stage}"
  force_delete = true

  tags = local.tags
}

resource "aws_ecs_cluster" "mcp" {
  count = var.stage == "prod" ? 1 : 0
  name  = "mcp-cluster-${var.stage}"

  tags = local.tags
}

resource "aws_iam_role" "ecs_task_execution_role" {
  count = var.stage == "prod" ? 1 : 0
  name  = "ecs-task-execution-role-${var.stage}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  count      = var.stage == "prod" ? 1 : 0
  role       = aws_iam_role.ecs_task_execution_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "ecs_task_role" {
  count = var.stage == "prod" ? 1 : 0
  name  = "ecs-task-role-${var.stage}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })

  tags = local.tags
}

resource "aws_security_group" "mcp_server" {
  count       = var.stage == "prod" ? 1 : 0
  name        = "mcp-server-sg-${var.stage}"
  description = "Security group for MCP server"
  vpc_id      = data.aws_vpc.default[0].id

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = local.tags
}

data "aws_vpc" "default" {
  count = var.stage == "prod" ? 1 : 0
  default = true
}

resource "aws_ecs_task_definition" "mcp_server" {
  count                  = var.stage == "prod" ? 1 : 0
  family                 = "mcp-server-${var.stage}"
  network_mode           = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                    = "256"
  memory                 = "512"
  execution_role_arn     = aws_iam_role.ecs_task_execution_role[0].arn
  task_role_arn          = aws_iam_role.ecs_task_role[0].arn

  container_definitions = jsonencode([
    {
      name      = "mcp-server"
      image     = "${aws_ecr_repository.mcp_server[0].repository_url}:latest"
      essential = true
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]
      environment = [
        {
          name  = "API_BASE_URL"
          value = "https://${aws_apigatewayv2_api.crud_api.id}.execute-api.${var.aws_region}.amazonaws.com"
        },
        {
          name  = "API_ID"
          value = aws_apigatewayv2_api.crud_api.id
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/mcp-server-${var.stage}"
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "mcp-server"
        }
      }
    }
  ])

  tags = local.tags
}

resource "aws_cloudwatch_log_group" "mcp_server" {
  count             = var.stage == "prod" ? 1 : 0
  name              = "/ecs/mcp-server-${var.stage}"
  retention_in_days = 30

  tags = local.tags
}

resource "aws_ecs_service" "mcp_server" {
  count           = var.stage == "prod" ? 1 : 0
  name            = "mcp-server-service-${var.stage}"
  cluster         = aws_ecs_cluster.mcp[0].id
  task_definition = aws_ecs_task_definition.mcp_server[0].arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = data.aws_subnets.default[0].ids
    security_groups = [aws_security_group.mcp_server[0].id]
    assign_public_ip = true
  }

  tags = local.tags
}

data "aws_subnets" "default" {
  count = var.stage == "prod" ? 1 : 0
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default[0].id]
  }
}
