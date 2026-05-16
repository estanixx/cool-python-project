# Auto-generate Lambda zip artifacts from source code.
# These are created automatically during `terraform plan` / `terraform apply`.
#
# Each Lambda includes ALL DAOs because api/handlers/__init__.py imports
# all three handlers, and each handler imports its own DAO.

locals {
  backend_root = "${path.module}/../../backend"

  # Shared sources included in every Lambda zip
  lambda_shared = [
    { content = file("${local.backend_root}/__init__.py"), filename = "api/__init__.py" },
    { content = file("${local.backend_root}/dal/__init__.py"), filename = "api/dal/__init__.py" },
    { content = file("${local.backend_root}/dal/db_client.py"), filename = "api/dal/db_client.py" },
    { content = file("${local.backend_root}/dal/errors.py"), filename = "api/dal/errors.py" },
    { content = file("${local.backend_root}/dal/dictionary_dao.py"), filename = "api/dal/dictionary_dao.py" },
    { content = file("${local.backend_root}/dal/product_dao.py"), filename = "api/dal/product_dao.py" },
    { content = file("${local.backend_root}/dal/shopping_cart_dao.py"), filename = "api/dal/shopping_cart_dao.py" },
    { content = file("${local.backend_root}/handlers/__init__.py"), filename = "api/handlers/__init__.py" },
  ]
}

data "archive_file" "dictionary" {
  type        = "zip"
  output_path = "${path.module}/.terraform/artifacts/dictionary.zip"

  dynamic "source" {
    for_each = local.lambda_shared
    content {
      content  = source.value.content
      filename = source.value.filename
    }
  }

  source {
    content  = file("${local.backend_root}/handlers/dictionary_handler.py")
    filename = "api/handlers/dictionary_handler.py"
  }
}

data "archive_file" "product" {
  type        = "zip"
  output_path = "${path.module}/.terraform/artifacts/product.zip"

  dynamic "source" {
    for_each = local.lambda_shared
    content {
      content  = source.value.content
      filename = source.value.filename
    }
  }

  source {
    content  = file("${local.backend_root}/handlers/product_handler.py")
    filename = "api/handlers/product_handler.py"
  }
}

data "archive_file" "shopping_cart" {
  type        = "zip"
  output_path = "${path.module}/.terraform/artifacts/shopping_cart.zip"

  dynamic "source" {
    for_each = local.lambda_shared
    content {
      content  = source.value.content
      filename = source.value.filename
    }
  }

  source {
    content  = file("${local.backend_root}/handlers/shopping_cart_handler.py")
    filename = "api/handlers/shopping_cart_handler.py"
  }
}

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
    dictionary    = "api.handlers.dictionary_handler.handler"
    product       = "api.handlers.product_handler.handler"
    shopping_cart = "api.handlers.shopping_cart_handler.handler"
  }

  lambda_artifacts = {
    dictionary    = data.archive_file.dictionary.output_path
    product       = data.archive_file.product.output_path
    shopping_cart = data.archive_file.shopping_cart.output_path
  }

  # Lambda containers reach Floci via Docker network hostname
  lambda_env_endpoint_url = "http://floci:4566"
}
