output "scan_reports_bucket_name" { value = aws_s3_bucket.scan_reports.id }
output "scan_reports_bucket_arn" { value = aws_s3_bucket.scan_reports.arn }
output "s3_full_policy_arn" { value = aws_iam_policy.s3_full.arn }
