

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Owner       = var.owner
      Environment = "shared"
      Project     = "aws-startup-kit"
      ManagedBy   = "terraform"
      Lab         = "1"
      CostCenter  = "free-tier"
      Module      = "bootstrap"
    }
  }

  allowed_account_ids = [
    var.aws_account_id
  ]
}
