provider "aws" {
  access_key                  = "test"
  secret_key                  = "test"
  region                      = var.aws_region
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  dynamic "endpoints" {
    for_each = var.aws_endpoint_url != "" ? [var.aws_endpoint_url] : []
    content {
      dynamodb = endpoints.value
      lambda   = endpoints.value
    }
  }
}
