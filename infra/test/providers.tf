provider "aws" {
  access_key                  = "mock-local-access-key"
  secret_key                  = "mock-local-secret-key"
  region                      = var.aws_region
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  dynamic "endpoints" {
    for_each = var.aws_endpoint_url != "" ? [var.aws_endpoint_url] : []
    content {
      dynamodb     = endpoints.value
      lambda       = endpoints.value
      iam          = endpoints.value
      apigateway   = endpoints.value
      apigatewayv2 = endpoints.value
    }
  }
}
