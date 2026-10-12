variable "aws_region" {
  description = "The AWS region to deploy resources in."
  type        = string
  default     = "eu-west-1"

  validation {
    condition = contains(
      [
        "eu-west-1", "eu-west-3", "eu-central-1", "eu-north-1",
        "us-east-1", "us-east-2", "us-west-2",
        "ap-south-1", "ap-southeast-1", "ap-northeast-1",
      ],
      var.aws_region
    )
    error_message = "aws_region must be one of the regions in ADR 0001's table."
  }
}

variable "owner" {
  description = "The owner of the resources."
  type        = string
}

variable "aws_account_id" {
  description = "The AWS account ID to allow access to."
  type        = string
}

variable "terraform_state_bucket_name" {
  description = "Name of the S3 bucket that stores Terraform state, issued by scripts/naming.py (service s3)."
  type        = string

  validation {
    condition     = can(regex("^[a-z]{2}(ne|se|[nsewc])-[0-9]+-[0-9]+-(dev|lab|prod|shared)-s3-[0-9a-z]{7}$", var.terraform_state_bucket_name))
    error_message = "terraform_state_bucket_name must follow ADR 0001 with service s3: <region>-<account>-<env>-s3-<id>."
  }
}
