terraform {
  required_version = ">= 1.10.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
  backend "s3" {
    bucket              = "anthony-proppilot-tfstate-388691194728"
    key                 = "proppilot/runtime/terraform.tfstate"
    region              = "us-east-1"
    encrypt             = true
    use_lockfile        = true
    allowed_account_ids = ["388691194728"]
  }
}
provider "aws" {
  region              = "us-east-1"
  allowed_account_ids = ["388691194728"]
  default_tags {
    tags = { Project = "anthony-proppilot", Owner = "anthony", ManagedBy = "terraform" }
  }
}
locals {
  account  = "388691194728"
  cluster  = "anthony-assessment4-eks"
  services = toset(["category", "urgency", "agent", "tickets", "frontend"])
  policies = {
    category = [{ Effect = "Allow", Action = ["sagemaker:InvokeEndpoint"], Resource = "arn:aws:sagemaker:us-east-1:${local.account}:endpoint/anthony-proppilot-category-v010" }]
    urgency  = [{ Effect = "Allow", Action = ["sagemaker:InvokeEndpoint"], Resource = "arn:aws:sagemaker:us-east-1:${local.account}:endpoint/anthony-proppilot-urgency-v010" }]
    agent    = [{ Effect = "Allow", Action = ["bedrock:InvokeModel"], Resource = "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-lite-v1:0" }]
    tickets  = [{ Effect = "Allow", Action = ["dynamodb:DescribeTable", "dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:Query", "dynamodb:ConditionCheckItem"], Resource = "arn:aws:dynamodb:us-east-1:${local.account}:table/anthony-proppilot-tickets" }]
  }
}
resource "aws_ecr_repository" "application" {
  for_each             = local.services
  name                 = "anthony-proppilot-${each.key}"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = false
  image_scanning_configuration { scan_on_push = true }
}
resource "aws_iam_role" "workload" {
  for_each = local.policies
  name     = "anthony-proppilot-${each.key}-runtime"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow", Principal = { Service = "pods.eks.amazonaws.com" }, Action = ["sts:AssumeRole", "sts:TagSession"]
      Condition = { StringEquals = {
        "aws:RequestTag/kubernetes-namespace"       = "proppilot"
        "aws:RequestTag/kubernetes-service-account" = each.key
        "aws:RequestTag/eks-cluster-name"           = local.cluster
      } }
    }]
  })
}
resource "aws_iam_role_policy" "workload" {
  for_each = local.policies
  role     = aws_iam_role.workload[each.key].id
  policy   = jsonencode({ Version = "2012-10-17", Statement = each.value })
}
resource "aws_eks_pod_identity_association" "workload" {
  for_each        = local.policies
  cluster_name    = local.cluster
  namespace       = "proppilot"
  service_account = each.key
  role_arn        = aws_iam_role.workload[each.key].arn
  depends_on      = [aws_iam_role_policy.workload]
}
output "repositories" { value = { for name, repository in aws_ecr_repository.application : name => repository.repository_url } }
output "workload_roles" { value = { for name, role in aws_iam_role.workload : name => role.arn } }
