# Auto-generate Lambda zip artifacts from source code.
# These are created automatically during `terraform plan` / `terraform apply`.

locals {
  backend_root = "${path.module}/../../backend"
}

data "archive_file" "dictionary" {
  type        = "zip"
  output_path = "${path.module}/.terraform/artifacts/dictionary.zip"

  source {
    content  = file("${local.backend_root}/handlers/dictionary_handler.py")
    filename = "backend/handlers/dictionary_handler.py"
  }
  source {
    content  = file("${local.backend_root}/handlers/__init__.py")
    filename = "backend/handlers/__init__.py"
  }
  source {
    content  = file("${local.backend_root}/dal/__init__.py")
    filename = "backend/dal/__init__.py"
  }
  source {
    content  = file("${local.backend_root}/dal/db_client.py")
    filename = "backend/dal/db_client.py"
  }
  source {
    content  = file("${local.backend_root}/dal/dictionary_dao.py")
    filename = "backend/dal/dictionary_dao.py"
  }
  source {
    content  = file("${local.backend_root}/dal/errors.py")
    filename = "backend/dal/errors.py"
  }
  source {
    content  = file("${local.backend_root}/__init__.py")
    filename = "backend/__init__.py"
  }
}

data "archive_file" "product" {
  type        = "zip"
  output_path = "${path.module}/.terraform/artifacts/product.zip"

  source {
    content  = file("${local.backend_root}/handlers/product_handler.py")
    filename = "backend/handlers/product_handler.py"
  }
  source {
    content  = file("${local.backend_root}/handlers/__init__.py")
    filename = "backend/handlers/__init__.py"
  }
  source {
    content  = file("${local.backend_root}/dal/__init__.py")
    filename = "backend/dal/__init__.py"
  }
  source {
    content  = file("${local.backend_root}/dal/db_client.py")
    filename = "backend/dal/db_client.py"
  }
  source {
    content  = file("${local.backend_root}/dal/product_dao.py")
    filename = "backend/dal/product_dao.py"
  }
  source {
    content  = file("${local.backend_root}/dal/errors.py")
    filename = "backend/dal/errors.py"
  }
  source {
    content  = file("${local.backend_root}/__init__.py")
    filename = "backend/__init__.py"
  }
}

data "archive_file" "shopping_cart" {
  type        = "zip"
  output_path = "${path.module}/.terraform/artifacts/shopping_cart.zip"

  source {
    content  = file("${local.backend_root}/handlers/shopping_cart_handler.py")
    filename = "backend/handlers/shopping_cart_handler.py"
  }
  source {
    content  = file("${local.backend_root}/handlers/__init__.py")
    filename = "backend/handlers/__init__.py"
  }
  source {
    content  = file("${local.backend_root}/dal/__init__.py")
    filename = "backend/dal/__init__.py"
  }
  source {
    content  = file("${local.backend_root}/dal/db_client.py")
    filename = "backend/dal/db_client.py"
  }
  source {
    content  = file("${local.backend_root}/dal/shopping_cart_dao.py")
    filename = "backend/dal/shopping_cart_dao.py"
  }
  source {
    content  = file("${local.backend_root}/dal/errors.py")
    filename = "backend/dal/errors.py"
  }
  source {
    content  = file("${local.backend_root}/__init__.py")
    filename = "backend/__init__.py"
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
    dictionary    = "backend.handlers.dictionary_handler.handler"
    product       = "backend.handlers.product_handler.handler"
    shopping_cart = "backend.handlers.shopping_cart_handler.handler"
  }

  lambda_artifacts = {
    dictionary    = data.archive_file.dictionary.output_path
    product       = data.archive_file.product.output_path
    shopping_cart = data.archive_file.shopping_cart.output_path
  }
}
