terraform {
  backend "s3" {
    bucket              = "anthony-proppilot-tfstate-388691194728"
    key                 = "proppilot/registry/terraform.tfstate"
    region              = "us-east-1"
    encrypt             = true
    use_lockfile        = true
    allowed_account_ids = ["388691194728"]
  }
}
