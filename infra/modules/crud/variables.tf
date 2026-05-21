variable "stage" {
  description = "Deployment stage (local or prod)."
  type        = string

  validation {
    condition     = length(var.stage) > 0
    error_message = "stage is required and cannot be empty."
  }
}

variable "aws_region" {
  description = "AWS region for resources."
  type        = string
  default     = "us-east-1"
}

variable "aws_endpoint_url" {
  description = "Optional AWS endpoint override (e.g. local Floci)."
  type        = string
  default     = ""
}

variable "lambda_env_endpoint_url" {
  description = "DynamoDB endpoint URL for Lambda runtime (may differ from provider endpoint)."
  type        = string
  default     = ""
}

variable "table_names" {
  description = "DynamoDB table names for Dictionary, Product, ShoppingCart."
  type = object({
    dictionary    = string
    product       = string
    shopping_cart = string
  })

  validation {
    condition = (
      length(var.table_names.dictionary) > 0 &&
      length(var.table_names.product) > 0 &&
      length(var.table_names.shopping_cart) > 0
    )
    error_message = "All table_names fields must be provided and non-empty."
  }
}

variable "lambda_role_name" {
  description = "IAM role name for CRUD Lambdas."
  type        = string
}

variable "lambda_runtime" {
  description = "Lambda runtime for CRUD handlers."
  type        = string
  default     = "python3.11"
}

variable "lambda_timeout" {
  description = "Lambda timeout in seconds."
  type        = number
  default     = 30
}

variable "lambda_artifacts" {
  description = "Zip artifacts for Lambda functions. Required only when stage=prod."
  type = object({
    dictionary    = string
    product       = string
    shopping_cart = string
    word_trick    = optional(string, "")
  })
}

variable "lambda_function_names" {
  description = "Lambda function names for CRUD handlers."
  type = object({
    dictionary    = string
    product       = string
    shopping_cart = string
    word_trick    = optional(string, "")
  })

  validation {
    condition = (
      length(var.lambda_function_names.dictionary) > 0 &&
      length(var.lambda_function_names.product) > 0 &&
      length(var.lambda_function_names.shopping_cart) > 0
    )
    error_message = "All lambda_function_names fields must be provided and non-empty."
  }
}

variable "lambda_handler_names" {
  description = "Handler entrypoints for CRUD Lambdas."
  type = object({
    dictionary    = string
    product       = string
    shopping_cart = string
    word_trick    = optional(string, "")
  })

  validation {
    condition = (
      length(var.lambda_handler_names.dictionary) > 0 &&
      length(var.lambda_handler_names.product) > 0 &&
      length(var.lambda_handler_names.shopping_cart) > 0
    )
    error_message = "All lambda_handler_names fields must be provided and non-empty."
  }
}

# --- VPC Networking (prod) ---

variable "enable_alb" {
  description = "Enable ALB, autoscaling, and VPC networking for ECS Fargate."
  type        = bool
  default     = false
}

variable "availability_zones" {
  description = "Availability zones for subnet placement (required when enable_alb=true)."
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets (ALB). Required when enable_alb=true."
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets (ECS Fargate). Required when enable_alb=true."
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC (used when creating a new VPC)."
  type        = string
  default     = "10.0.0.0/16"
}

variable "mcp_image_tag" {
  description = "Docker image tag for the MCP server ECS task. In CI/CD, pass the commit SHA."
  type        = string
  default     = "latest"
}

variable "api_gateway_cors_origins" {
  description = "Allowed origins for API Gateway CORS. Restrict to the Amplify domain in production."
  type        = list(string)
  default     = ["*"]
}

# --- ECS Auto-Scaling ---

variable "ecs_min_capacity" {
  description = "Minimum ECS service capacity for autoscaling."
  type        = number
  default     = 1
}

variable "ecs_desired_count" {
  description = "Desired ECS service task count."
  type        = number
  default     = 1
}

variable "ecs_max_capacity" {
  description = "Maximum ECS service capacity for autoscaling."
  type        = number
  default     = 2
}

# --- Observability ---

variable "alarm_email" {
  description = "Email address for CloudWatch alarm notifications via SNS."
  type        = string
  default     = "juaneste687@gmail.com"
}
