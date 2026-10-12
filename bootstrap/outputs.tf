output "state_bucket_name" {
  description = "Name of the S3 bucket that stores Terraform state. Use it in backend.hcl."
  value       = aws_s3_bucket.state.id
}

output "state_bucket_arn" {
  description = "ARN of the Terraform state bucket."
  value       = aws_s3_bucket.state.arn
}

output "state_bucket_region" {
  description = "Region of the Terraform state bucket. Use it in backend.hcl."
  value       = aws_s3_bucket.state.region
}
