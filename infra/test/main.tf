# Lambda zip artifacts are only needed for prod (Floci doesn't support Lambda).
# For local stage, only DynamoDB tables are provisioned.

module "crud" {
  source = "../modules/crud"

  stage            = var.stage
  aws_region       = var.aws_region
  aws_endpoint_url = var.aws_endpoint_url

  table_names = {
    dictionary    = "Dictionary"
    product       = "Product"
    shopping_cart = "ShoppingCart"
  }

  lambda_role_name = "serverless-crud-${var.stage}-lambda"

  lambda_function_names = {
    dictionary    = "dictionary-${var.stage}"
    product       = "product-${var.stage}"
    shopping_cart = "shopping-cart-${var.stage}"
  }

  lambda_handler_names = {
    dictionary    = "backend.handlers.dictionary_handler.handler"
    product       = "backend.handlers.product_handler.handler"
    shopping_cart = "backend.handlers.shopping_cart_handler.handler"
  }

  # Not used for local — Floci doesn't support Lambda.
  lambda_artifacts = {
    dictionary    = ""
    product       = ""
    shopping_cart = ""
  }
}
