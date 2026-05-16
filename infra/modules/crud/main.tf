locals {
  tags = {
    Service = "serverless-crud-dynamodb-mcp"
    Stage   = var.stage
  }
}

resource "aws_dynamodb_table" "dictionary" {
  name         = var.table_names.dictionary
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "Word"

  attribute {
    name = "Word"
    type = "S"
  }

  tags = local.tags
}

resource "aws_dynamodb_table" "product" {
  name         = var.table_names.product
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "uuid"

  attribute {
    name = "uuid"
    type = "S"
  }

  tags = local.tags
}

resource "aws_dynamodb_table" "shopping_cart" {
  name         = var.table_names.shopping_cart
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "UUID"

  attribute {
    name = "UUID"
    type = "S"
  }

  tags = local.tags
}

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_role" {
  name               = var.lambda_role_name
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json

  tags = local.tags
}

data "aws_iam_policy_document" "crud_policy" {
  statement {
    sid = "DynamoCrud"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:Query",
      "dynamodb:Scan"
    ]
    resources = [
      aws_dynamodb_table.dictionary.arn,
      aws_dynamodb_table.product.arn,
      aws_dynamodb_table.shopping_cart.arn
    ]
  }
}

resource "aws_iam_policy" "crud_policy" {
  name   = "${var.lambda_role_name}-crud"
  policy = data.aws_iam_policy_document.crud_policy.json

  tags = local.tags
}

resource "aws_iam_role_policy_attachment" "crud_attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.crud_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_basic_attach" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "dictionary" {
  function_name = var.lambda_function_names.dictionary
  role          = aws_iam_role.lambda_role.arn
  handler       = var.lambda_handler_names.dictionary
  runtime       = var.lambda_runtime
  filename      = var.lambda_artifacts.dictionary
  source_code_hash = filebase64sha256(var.lambda_artifacts.dictionary)

  tags = local.tags
}

resource "aws_lambda_function" "product" {
  function_name = var.lambda_function_names.product
  role          = aws_iam_role.lambda_role.arn
  handler       = var.lambda_handler_names.product
  runtime       = var.lambda_runtime
  filename      = var.lambda_artifacts.product
  source_code_hash = filebase64sha256(var.lambda_artifacts.product)

  tags = local.tags
}

resource "aws_lambda_function" "shopping_cart" {
  function_name = var.lambda_function_names.shopping_cart
  role          = aws_iam_role.lambda_role.arn
  handler       = var.lambda_handler_names.shopping_cart
  runtime       = var.lambda_runtime
  filename      = var.lambda_artifacts.shopping_cart
  source_code_hash = filebase64sha256(var.lambda_artifacts.shopping_cart)

  tags = local.tags
}
