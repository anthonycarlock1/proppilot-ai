terraform {
  required_version = ">= 1.10.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
}
provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = { Project = "anthony-proppilot", Owner = "anthony", ManagedBy = "terraform" }
  }
}
variable "image_uri" {
  type        = string
  description = "ECR hosting image pinned by sha256 digest"
  validation {
    condition     = can(regex("^[0-9]{12}\\.dkr\\.ecr\\.us-east-1\\.amazonaws\\.com/anthony-proppilot-urgency-hosting@sha256:[a-f0-9]{64}$", var.image_uri))
    error_message = "Use the dedicated us-east-1 ECR repository and immutable image digest."
  }
}
data "aws_caller_identity" "current" {}
data "aws_ecr_repository" "hosting" { name = "anthony-proppilot-urgency-hosting" }
locals {
  name = "anthony-proppilot-urgency-v010"
}
resource "aws_iam_role" "hosting" {
  name = "anthony-proppilot-urgency-hosting"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow", Principal = { Service = "sagemaker.amazonaws.com" }, Action = "sts:AssumeRole"
      Condition = {
        StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
        ArnLike      = { "aws:SourceArn" = "arn:aws:sagemaker:us-east-1:${data.aws_caller_identity.current.account_id}:*" }
      }
    }]
  })
}
resource "aws_iam_role_policy" "hosting" {
  role = aws_iam_role.hosting.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["ecr:GetAuthorizationToken"], Resource = "*" },
      { Effect = "Allow", Action = ["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer", "ecr:BatchCheckLayerAvailability"], Resource = data.aws_ecr_repository.hosting.arn },
      { Effect = "Allow", Action = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents", "logs:DescribeLogStreams"], Resource = "arn:aws:logs:us-east-1:${data.aws_caller_identity.current.account_id}:log-group:/aws/sagemaker/Endpoints/${local.name}:*" }
    ]
  })
}
resource "aws_sagemaker_model" "urgency" {
  name               = local.name
  execution_role_arn = aws_iam_role.hosting.arn
  primary_container { image = var.image_uri }
  depends_on = [aws_iam_role_policy.hosting]
}
resource "aws_sagemaker_endpoint_configuration" "urgency" {
  name = local.name
  production_variants {
    variant_name = "AllTraffic"
    model_name   = aws_sagemaker_model.urgency.name
    serverless_config {
      memory_size_in_mb = 2048
      max_concurrency   = 2
    }
  }
}
resource "aws_sagemaker_endpoint" "urgency" {
  name                 = local.name
  endpoint_config_name = aws_sagemaker_endpoint_configuration.urgency.name
}
output "endpoint_name" { value = aws_sagemaker_endpoint.urgency.name }
output "invoke_policy" {
  value = jsonencode({ Version = "2012-10-17", Statement = [{ Effect = "Allow", Action = "sagemaker:InvokeEndpoint", Resource = aws_sagemaker_endpoint.urgency.arn }] })
}
