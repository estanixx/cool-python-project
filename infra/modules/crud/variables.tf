variable "stage" {
  description = "Deployment stage (local or prod)."
  type        = string

  validation {
    condition     = length(trim(var.stage)) > 0
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

variable "table_names" {
  description = "DynamoDB table names for Dictionary, Product, ShoppingCart."
  type = object({
    dictionary     = string
    product        = string
    shopping_cart  = string
  })

  validation {
    condition = (
      length(trim(var.table_names.dictionary)) > 0 &&
      length(trim(var.table_names.product)) > 0 &&
      length(trim(var.table_names.shopping_cart)) > 0
    )
    error_message = "All table_names fields must be provided and non-empty."
  }
}

variable "lambda_role_name" {
  description = "IAM role name for CRUD Lambdas."
  type        = string
}
