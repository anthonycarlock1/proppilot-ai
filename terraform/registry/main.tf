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
resource "aws_ecr_repository" "hosting" {
  name                 = "anthony-proppilot-category-hosting"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = false
  image_scanning_configuration { scan_on_push = true }
}
output "repository_url" { value = aws_ecr_repository.hosting.repository_url }
resource "aws_ecr_repository" "urgency_hosting" {
  name                 = "anthony-proppilot-urgency-hosting"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = false
  image_scanning_configuration { scan_on_push = true }
}
output "urgency_repository_url" { value = aws_ecr_repository.urgency_hosting.repository_url }
