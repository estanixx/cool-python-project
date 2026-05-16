locals {
  tags = {
    Service = "serverless-crud-dynamodb-mcp"
    Stage   = var.stage
  }
}

resource "aws_dynamodb_table" "dictionary" {
  name         = var.table_names.dictionary
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "word"

  attribute {
    name = "word"
    type = "S"
  }

  tags = local.tags
}

resource "aws_dynamodb_table" "product" {
  name         = var.table_names.product
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "product_id"

  attribute {
    name = "product_id"
    type = "S"
  }

  tags = local.tags
}

resource "aws_dynamodb_table" "shopping_cart" {
  name         = var.table_names.shopping_cart
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "cart_id"

  attribute {
    name = "cart_id"
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
