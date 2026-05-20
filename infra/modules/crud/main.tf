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

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = true
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

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = true
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

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = true
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

resource "aws_lambda_function" "word_trick" {
  count            = var.stage == "prod" ? 1 : 0
  function_name    = var.lambda_function_names.word_trick
  role             = aws_iam_role.lambda_role.arn
  handler          = var.lambda_handler_names.word_trick
  runtime          = var.lambda_runtime
  timeout          = var.lambda_timeout
  filename         = var.lambda_artifacts.word_trick
  source_code_hash = filebase64sha256(var.lambda_artifacts.word_trick)

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
    allow_origins = var.api_gateway_cors_origins
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
  }

  tags = local.tags
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.crud_api.id
  name        = "$default"
  auto_deploy = true

  dynamic "access_log_settings" {
    for_each = var.stage == "prod" ? [1] : []
    content {
      destination_arn = aws_cloudwatch_log_group.api_gw_access_logs[0].arn
      format = jsonencode({
        requestId        = "$context.requestId"
        method           = "$context.httpMethod"
        path             = "$context.path"
        status           = "$context.status"
        latency          = "$context.integrationLatency"
        integrationError = "$context.integration.error"
      })
    }
  }
}

resource "aws_apigatewayv2_integration" "dictionary" {
  api_id                 = aws_apigatewayv2_api.crud_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.dictionary.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "product" {
  api_id                 = aws_apigatewayv2_api.crud_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.product.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "shopping_cart" {
  api_id                 = aws_apigatewayv2_api.crud_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.shopping_cart.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
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

resource "aws_apigatewayv2_integration" "word_trick" {
  count                  = var.stage == "prod" ? 1 : 0
  api_id                 = aws_apigatewayv2_api.crud_api.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.word_trick[0].invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "word_trick" {
  count     = var.stage == "prod" ? 1 : 0
  api_id    = aws_apigatewayv2_api.crud_api.id
  route_key = "ANY /word-trick"
  target    = "integrations/${aws_apigatewayv2_integration.word_trick[0].id}"
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

resource "aws_lambda_permission" "word_trick" {
  count         = var.stage == "prod" ? 1 : 0
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.word_trick[0].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.crud_api.execution_arn}/*/*"
}

# --- VPC Networking (prod, when enable_alb=true) ---

resource "aws_vpc" "main" {
  count                = var.enable_alb ? 1 : 0
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.tags, { Name = "mcp-vpc-${var.stage}" })
}

resource "aws_internet_gateway" "main" {
  count  = var.enable_alb ? 1 : 0
  vpc_id = aws_vpc.main[0].id

  tags = merge(local.tags, { Name = "mcp-igw-${var.stage}" })
}

resource "aws_subnet" "public" {
  count                   = var.enable_alb ? length(var.public_subnet_cidrs) : 0
  vpc_id                  = aws_vpc.main[0].id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true

  tags = merge(local.tags, { Name = "mcp-public-${var.stage}-${count.index + 1}" })
}

resource "aws_subnet" "private" {
  count             = var.enable_alb ? length(var.private_subnet_cidrs) : 0
  vpc_id            = aws_vpc.main[0].id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = var.availability_zones[count.index]

  tags = merge(local.tags, { Name = "mcp-private-${var.stage}-${count.index + 1}" })
}

resource "aws_route_table" "public" {
  count  = var.enable_alb ? 1 : 0
  vpc_id = aws_vpc.main[0].id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main[0].id
  }

  tags = merge(local.tags, { Name = "mcp-public-rt-${var.stage}" })
}

resource "aws_route_table_association" "public" {
  count          = var.enable_alb ? length(var.public_subnet_cidrs) : 0
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public[0].id
}

resource "aws_eip" "nat" {
  count  = var.enable_alb ? 1 : 0
  domain = "vpc"

  tags = merge(local.tags, { Name = "mcp-nat-eip-${var.stage}" })
}

resource "aws_nat_gateway" "main" {
  count         = var.enable_alb ? 1 : 0
  allocation_id = aws_eip.nat[0].id
  subnet_id     = aws_subnet.public[0].id

  tags = merge(local.tags, { Name = "mcp-nat-gw-${var.stage}" })

  depends_on = [aws_internet_gateway.main]
}

resource "aws_route_table" "private" {
  count  = var.enable_alb ? 1 : 0
  vpc_id = aws_vpc.main[0].id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[0].id
  }

  tags = merge(local.tags, { Name = "mcp-private-rt-${var.stage}" })
}

resource "aws_route_table_association" "private" {
  count          = var.enable_alb ? length(var.private_subnet_cidrs) : 0
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[0].id
}

# --- VPC Flow Logs (when enable_alb=true) ---

resource "aws_iam_role" "flow_log_role" {
  count = var.enable_alb ? 1 : 0
  name  = "vpc-flow-log-role-${var.stage}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "vpc-flow-logs.amazonaws.com"
      }
    }]
  })

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "flow_log_policy" {
  count      = var.enable_alb ? 1 : 0
  role       = aws_iam_role.flow_log_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  count             = var.enable_alb ? 1 : 0
  name              = "/aws/vpc/flow-logs/${var.stage}"
  retention_in_days = 30

  tags = local.tags
}

resource "aws_flow_log" "main" {
  count                = var.enable_alb ? 1 : 0
  iam_role_arn         = aws_iam_role.flow_log_role[0].arn
  log_destination      = aws_cloudwatch_log_group.vpc_flow_logs[0].arn
  log_destination_type = "cloud-watch-logs"
  traffic_type         = "ALL"
  vpc_id               = aws_vpc.main[0].id

  tags = local.tags
}

# --- ECS Fargate for MCP Server (Production only) ---

resource "aws_ecr_repository" "mcp_server" {
  count        = var.stage == "prod" ? 1 : 0
  name         = "mcp-server-${var.stage}"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }

  image_tag_mutability = "IMMUTABLE"

  tags = local.tags
}

resource "aws_ecs_cluster" "mcp" {
  count = var.stage == "prod" ? 1 : 0
  name  = "mcp-cluster-${var.stage}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

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

# ALB Security Group (created when enable_alb=true)
resource "aws_security_group" "alb" {
  count       = var.enable_alb && var.stage == "prod" ? 1 : 0
  name        = "alb-sg-${var.stage}"
  description = "Security group for ALB"
  vpc_id      = aws_vpc.main[0].id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP from internet"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = local.tags
}

# ECS Security Group — restricted to ALB when enable_alb=true
resource "aws_security_group" "mcp_server" {
  count       = var.stage == "prod" ? 1 : 0
  name        = "mcp-server-sg-${var.stage}"
  description = "Security group for MCP server"
  vpc_id      = var.enable_alb ? aws_vpc.main[0].id : data.aws_vpc.default[0].id

  dynamic "ingress" {
    for_each = var.enable_alb ? [] : [1]
    content {
      from_port   = 8000
      to_port     = 8000
      protocol    = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
    }
  }

  dynamic "ingress" {
    for_each = var.enable_alb ? [1] : []
    content {
      from_port       = 8000
      to_port         = 8000
      protocol        = "tcp"
      security_groups = [aws_security_group.alb[0].id]
      description     = "MCP server from ALB only"
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = local.tags
}

data "aws_vpc" "default" {
  count   = var.stage == "prod" && !var.enable_alb ? 1 : 0
  default = true
}

resource "aws_ecs_task_definition" "mcp_server" {
  count                    = var.stage == "prod" ? 1 : 0
  family                   = "mcp-server-${var.stage}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_task_execution_role[0].arn
  task_role_arn            = aws_iam_role.ecs_task_role[0].arn

  container_definitions = jsonencode([
    {
      name      = "mcp-server"
      image     = "${aws_ecr_repository.mcp_server[0].repository_url}:${var.mcp_image_tag}"
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
          name  = "STAGE"
          value = var.stage
        },
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

# --- API Gateway Access Logs (prod only) ---

resource "aws_cloudwatch_log_group" "api_gw_access_logs" {
  count             = var.stage == "prod" ? 1 : 0
  name              = "/api-gw/access-logs-${var.stage}"
  retention_in_days = 30
  tags              = local.tags
}

resource "aws_iam_role" "api_gw_cloudwatch" {
  count = var.stage == "prod" ? 1 : 0
  name  = "api-gw-cloudwatch-role-${var.stage}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "apigateway.amazonaws.com"
      }
    }]
  })

  tags = local.tags
}

resource "aws_iam_role_policy" "api_gw_cloudwatch" {
  count = var.stage == "prod" ? 1 : 0
  name  = "api-gw-cloudwatch-policy-${var.stage}"
  role  = aws_iam_role.api_gw_cloudwatch[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
      Effect   = "Allow"
      Resource = "arn:aws:logs:*:*:*"
    }]
  })
}

# ALB and Target Group (when enable_alb=true)
resource "aws_lb" "mcp" {
  count                      = var.enable_alb && var.stage == "prod" ? 1 : 0
  name                       = "mcp-alb-${var.stage}"
  internal                   = false
  load_balancer_type         = "application"
  security_groups            = [aws_security_group.alb[0].id]
  subnets                    = aws_subnet.public[*].id
  drop_invalid_header_fields = true

  tags = local.tags
}

resource "aws_lb_target_group" "mcp" {
  count       = var.enable_alb && var.stage == "prod" ? 1 : 0
  name        = "mcp-tg-${var.stage}"
  port        = 8000
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.main[0].id

  health_check {
    path                = "/health"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }

  tags = local.tags
}

resource "aws_lb_listener" "mcp_http" {
  count             = var.enable_alb && var.stage == "prod" ? 1 : 0
  load_balancer_arn = aws_lb.mcp[0].arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.mcp[0].arn
  }
}

resource "aws_ecs_service" "mcp_server" {
  count           = var.stage == "prod" ? 1 : 0
  name            = "mcp-server-service-${var.stage}"
  cluster         = aws_ecs_cluster.mcp[0].id
  task_definition = aws_ecs_task_definition.mcp_server[0].arn
  desired_count   = var.enable_alb ? 1 : 1
  launch_type     = "FARGATE"

  dynamic "load_balancer" {
    for_each = var.enable_alb ? [1] : []
    content {
      target_group_arn = aws_lb_target_group.mcp[0].arn
      container_name   = "mcp-server"
      container_port   = 8000
    }
  }

  network_configuration {
    subnets          = var.enable_alb ? aws_subnet.private[*].id : data.aws_subnets.default[0].ids
    security_groups  = [aws_security_group.mcp_server[0].id]
    assign_public_ip = var.enable_alb ? false : true
  }

  tags = local.tags
}

data "aws_subnets" "default" {
  count = var.stage == "prod" && !var.enable_alb ? 1 : 0
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default[0].id]
  }
}

# --- Autoscaling (when enable_alb=true) ---

resource "aws_appautoscaling_target" "mcp" {
  count              = var.enable_alb && var.stage == "prod" ? 1 : 0
  max_capacity       = 4
  min_capacity       = 1
  resource_id        = "service/${aws_ecs_cluster.mcp[0].name}/${aws_ecs_service.mcp_server[0].name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "mcp_cpu" {
  count              = var.enable_alb && var.stage == "prod" ? 1 : 0
  name               = "mcp-cpu-scaling-${var.stage}"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.mcp[0].resource_id
  scalable_dimension = aws_appautoscaling_target.mcp[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.mcp[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value = 50.0
  }
}

resource "aws_appautoscaling_policy" "mcp_memory" {
  count              = var.enable_alb && var.stage == "prod" ? 1 : 0
  name               = "mcp-memory-scaling-${var.stage}"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.mcp[0].resource_id
  scalable_dimension = aws_appautoscaling_target.mcp[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.mcp[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageMemoryUtilization"
    }
    target_value = 70.0
  }
}

# --- Observability: MCP Log Metric Filters (prod only) ---

resource "aws_cloudwatch_log_metric_filter" "mcp_tool_calls" {
  count          = var.stage == "prod" ? 1 : 0
  name           = "MCPToolCalls"
  log_group_name = aws_cloudwatch_log_group.mcp_server[0].name
  pattern        = "{ $.status < 400 && $.tool = * }"

  metric_transformation {
    name      = "ToolCalls"
    namespace = "MCP/Server"
    value     = "1"
    dimensions = {
      ToolName = "$.tool"
    }
  }
}

resource "aws_cloudwatch_log_metric_filter" "mcp_tool_errors" {
  count          = var.stage == "prod" ? 1 : 0
  name           = "MCPToolErrors"
  log_group_name = aws_cloudwatch_log_group.mcp_server[0].name
  pattern        = "{ $.status >= 400 && $.tool = * }"

  metric_transformation {
    name      = "ToolErrors"
    namespace = "MCP/Server"
    value     = "1"
    dimensions = {
      ToolName = "$.tool"
    }
  }
}

# --- Observability: CloudWatch Dashboard (prod only) ---

locals {
  dashboard_body = jsonencode({
    widgets = [
      # Row 1: MCP Custom Metrics
      { type = "metric", x = 0, y = 0, width = 12, height = 6,
        properties = {
          title   = "MCP Tool Calls",
          metrics = [["MCP/Server", "ToolCalls", { stat = "Sum", period = 300 }]],
          region  = var.aws_region
          view    = "timeSeries"
        }
      },
      { type = "metric", x = 12, y = 0, width = 12, height = 6,
        properties = {
          title   = "MCP Tool Errors",
          metrics = [["MCP/Server", "ToolErrors", { stat = "Sum", period = 300 }]],
          region  = var.aws_region
          view    = "timeSeries"
        }
      },
      # Row 2: API Gateway
      { type = "metric", x = 0, y = 6, width = 8, height = 6,
        properties = {
          title   = "API Gateway — Count",
          metrics = [["AWS/ApiGateway", "Count", "ApiName", "serverless-crud-${var.stage}", { stat = "Sum" }]],
          region  = var.aws_region
          view    = "timeSeries"
        }
      },
      { type = "metric", x = 8, y = 6, width = 8, height = 6,
        properties = {
          title   = "API Gateway — Latency",
          metrics = [["AWS/ApiGateway", "Latency", "ApiName", "serverless-crud-${var.stage}", { stat = "Average" }]],
          region  = var.aws_region
          view    = "timeSeries"
        }
      },
      { type = "metric", x = 16, y = 6, width = 8, height = 6,
        properties = {
          title = "API Gateway — 4xx/5xx",
          metrics = [
            ["AWS/ApiGateway", "4xx", "ApiName", "serverless-crud-${var.stage}", { stat = "Sum" }],
            [".", "5xx", ".", ".", { stat = "Sum" }]
          ],
          region = var.aws_region
          view   = "timeSeries"
        }
      },
      # Row 3: ECS
      { type = "metric", x = 0, y = 12, width = 8, height = 6,
        properties = {
          title   = "ECS — CPU Utilization",
          metrics = [["AWS/ECS", "CPUUtilization", "ClusterName", "mcp-cluster-${var.stage}", "ServiceName", "mcp-server-service-${var.stage}", { stat = "Average" }]],
          region  = var.aws_region
          view    = "timeSeries"
        }
      },
      { type = "metric", x = 8, y = 12, width = 8, height = 6,
        properties = {
          title   = "ECS — Memory Utilization",
          metrics = [["AWS/ECS", "MemoryUtilization", "ClusterName", "mcp-cluster-${var.stage}", "ServiceName", "mcp-server-service-${var.stage}", { stat = "Average" }]],
          region  = var.aws_region
          view    = "timeSeries"
        }
      },
      { type = "metric", x = 16, y = 12, width = 8, height = 6,
        properties = {
          title   = "ECS — Running Task Count",
          metrics = [["AWS/ECS", "RunningTaskCount", "ClusterName", "mcp-cluster-${var.stage}", "ServiceName", "mcp-server-service-${var.stage}", { stat = "Average" }]],
          region  = var.aws_region
          view    = "timeSeries"
        }
      },
      # Row 4: ALB
      { type = "metric", x = 0, y = 18, width = 8, height = 6,
        properties = {
          title   = "ALB — Request Count",
          metrics = [["AWS/ApplicationELB", "RequestCount", "LoadBalancer", "app/mcp-alb-${var.stage}", { stat = "Sum" }]],
          region  = var.aws_region
          view    = "timeSeries"
        }
      },
      { type = "metric", x = 8, y = 18, width = 8, height = 6,
        properties = {
          title   = "ALB — Target Response Time",
          metrics = [["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", "app/mcp-alb-${var.stage}", { stat = "Average" }]],
          region  = var.aws_region
          view    = "timeSeries"
        }
      },
      { type = "metric", x = 16, y = 18, width = 8, height = 6,
        properties = {
          title   = "ALB — Healthy Host Count",
          metrics = [["AWS/ApplicationELB", "HealthyHostCount", "LoadBalancer", "app/mcp-alb-${var.stage}", { stat = "Average" }]],
          region  = var.aws_region
          view    = "timeSeries"
        }
      },
      # Row 5: DynamoDB
      { type = "metric", x = 0, y = 24, width = 12, height = 6,
        properties = {
          title = "DynamoDB — Read/Write Capacity",
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", var.table_names.dictionary, { stat = "Sum" }],
            [".", "ConsumedWriteCapacityUnits", ".", ".", { stat = "Sum" }]
          ],
          region = var.aws_region
          view   = "timeSeries"
        }
      },
      { type = "metric", x = 12, y = 24, width = 12, height = 6,
        properties = {
          title   = "DynamoDB — System Errors",
          metrics = [["AWS/DynamoDB", "SystemErrors", "TableName", var.table_names.dictionary, { stat = "Sum" }]],
          region  = var.aws_region
          view    = "timeSeries"
        }
      },
      # Row 6: Lambda
      { type = "metric", x = 0, y = 30, width = 8, height = 6,
        properties = {
          title   = "Lambda — Invocations",
          metrics = [["AWS/Lambda", "Invocations", "FunctionName", var.lambda_function_names.dictionary, { stat = "Sum" }]],
          region  = var.aws_region
          view    = "timeSeries"
        }
      },
      { type = "metric", x = 8, y = 30, width = 8, height = 6,
        properties = {
          title   = "Lambda — Duration",
          metrics = [["AWS/Lambda", "Duration", "FunctionName", var.lambda_function_names.dictionary, { stat = "Average" }]],
          region  = var.aws_region
          view    = "timeSeries"
        }
      },
      { type = "metric", x = 16, y = 30, width = 8, height = 6,
        properties = {
          title   = "Lambda — Errors",
          metrics = [["AWS/Lambda", "Errors", "FunctionName", var.lambda_function_names.dictionary, { stat = "Sum" }]],
          region  = var.aws_region
          view    = "timeSeries"
        }
      },
    ]
  })
}

resource "aws_cloudwatch_dashboard" "main" {
  count          = var.stage == "prod" ? 1 : 0
  dashboard_name = "mcp-server-${var.stage}"
  dashboard_body = local.dashboard_body
}
