resource "aws_s3_bucket" "scan_reports" {
  bucket        = "${var.project_name}-${var.environment}-scan-reports-${var.aws_account_id}"
  force_destroy = var.environment != "prod"
  tags          = merge(var.tags, { Name = "${var.project_name}-${var.environment}-scan-reports" })
}

resource "aws_s3_bucket_versioning" "scan_reports" {
  bucket = aws_s3_bucket.scan_reports.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "scan_reports" {
  bucket = aws_s3_bucket.scan_reports.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "scan_reports" {
  bucket                  = aws_s3_bucket.scan_reports.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "scan_reports" {
  bucket = aws_s3_bucket.scan_reports.id

  rule {
    id     = "archive-old-reports"
    status = "Enabled"
    filter {}

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }

  rule {
    id     = "delete-incomplete-multipart"
    status = "Enabled"
    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

resource "aws_iam_policy" "s3_full" {
  name        = "${var.project_name}-${var.environment}-s3-full"
  description = "Full access to application S3 buckets"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [
          aws_s3_bucket.scan_reports.arn,
          "${aws_s3_bucket.scan_reports.arn}/*"
        ]
      }
    ]
  })
}
