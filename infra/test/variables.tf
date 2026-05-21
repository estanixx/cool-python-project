variable "stage" {
  description = "Deployment stage (local or prod)."
  type        = string
  default     = "local"
}

variable "aws_region" {
  description = "AWS region for resources."
  type        = string
  default     = "us-east-1"
}

variable "aws_endpoint_url" {
  description = "Optional AWS endpoint override (e.g. local Floci)."
  type        = string
  default     = "http://localhost:4566"
}
