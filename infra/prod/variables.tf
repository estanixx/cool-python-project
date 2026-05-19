variable "stage" {
  description = "Deployment stage (local or prod)."
  type        = string
  default     = "prod"
}

variable "aws_region" {
  description = "AWS region for resources."
  type        = string
  default     = "us-east-1"
}

variable "aws_endpoint_url" {
  description = "Optional AWS endpoint override (leave empty for AWS)."
  type        = string
  default     = ""
}

variable "mcp_image_tag" {
  description = "Docker image tag for the MCP server ECS task. Passed from CI/CD."
  type        = string
  default     = "latest"
}
