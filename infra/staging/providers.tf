terraform {
  backend "s3" {
    bucket       = "central-tfstate-estanix-871696174477"
    key          = "cool-python-project-staging"
    region       = "us-east-1"
    use_lockfile = true
  }
}

provider "aws" {
  region = var.aws_region
}
