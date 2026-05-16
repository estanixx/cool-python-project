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
    dictionary     = string
    product        = string
    shopping_cart  = string
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
  })
}

variable "lambda_function_names" {
  description = "Lambda function names for CRUD handlers."
  type = object({
    dictionary    = string
    product       = string
    shopping_cart = string
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
