terraform {
  required_version = ">= 1.10.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 6.0" }
  }
  backend "s3" {
    bucket              = "anthony-proppilot-tfstate-388691194728"
    key                 = "proppilot/ci/terraform.tfstate"
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
resource "aws_iam_role" "deploy" {
  name                 = "anthony-proppilot-github-deploy"
  max_session_duration = 3600
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow", Action = "sts:AssumeRoleWithWebIdentity"
      Principal = { Federated = "arn:aws:iam::388691194728:oidc-provider/token.actions.githubusercontent.com" }
      Condition = { StringEquals = {
        "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        "token.actions.githubusercontent.com:sub" = "repo:anthonycarlock1@237302030/proppilot-ai@1435163725:ref:refs/heads/main"
      } }
    }]
  })
}
resource "aws_iam_role_policy" "deploy" {
  role = aws_iam_role.deploy.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["eks:DescribeCluster"], Resource = "arn:aws:eks:us-east-1:388691194728:cluster/anthony-assessment4-eks" },
      { Effect = "Allow", Action = ["ecr:GetAuthorizationToken"], Resource = "*" },
      { Effect = "Allow", Action = ["ecr:BatchCheckLayerAvailability", "ecr:InitiateLayerUpload", "ecr:UploadLayerPart", "ecr:CompleteLayerUpload", "ecr:PutImage", "ecr:DescribeImages", "ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"], Resource = [for s in ["category", "urgency", "agent", "tickets", "frontend"] : "arn:aws:ecr:us-east-1:388691194728:repository/anthony-proppilot-${s}"] }
    ]
  })
}
output "deploy_role_arn" { value = aws_iam_role.deploy.arn }
