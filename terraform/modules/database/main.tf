resource "aws_dynamodb_table" "scan_jobs" {
  name         = "${var.project_name}-${var.environment}-scan-jobs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "job_id"

  attribute {
    name = "job_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "repo_id"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  global_secondary_index {
    name            = "UserIdIndex"
    hash_key        = "user_id"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "RepoIdIndex"
    hash_key        = "repo_id"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  point_in_time_recovery { enabled = true }
  server_side_encryption { enabled = true }

  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}-scan-jobs" })
}

resource "aws_dynamodb_table" "scan_results" {
  name         = "${var.project_name}-${var.environment}-scan-results"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "job_id"

  attribute {
    name = "job_id"
    type = "S"
  }

  attribute {
    name = "repoId"
    type = "S"
  }

  attribute {
    name = "scanDate"
    type = "S"
  }

  global_secondary_index {
    name            = "RepoIdIndex"
    hash_key        = "repoId"
    range_key       = "scanDate"
    projection_type = "ALL"
  }

  point_in_time_recovery { enabled = true }
  server_side_encryption { enabled = true }

  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}-scan-results" })
}

resource "aws_dynamodb_table" "connections" {
  name         = "${var.project_name}-${var.environment}-connections"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"
  range_key    = "connection_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "connection_id"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  server_side_encryption { enabled = true }

  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}-connections" })
}

resource "aws_dynamodb_table" "ws_connections" {
  name         = "${var.project_name}-${var.environment}-ws-connections"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "job_id"
  range_key    = "connection_id"

  attribute {
    name = "job_id"
    type = "S"
  }

  attribute {
    name = "connection_id"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  server_side_encryption { enabled = true }

  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}-ws-connections" })
}

resource "aws_dynamodb_table" "eval_results" {
  name         = "${var.project_name}-${var.environment}-eval-results"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "job_id"
  range_key    = "eval_run_id"

  attribute {
    name = "job_id"
    type = "S"
  }

  attribute {
    name = "eval_run_id"
    type = "S"
  }

  point_in_time_recovery { enabled = true }
  server_side_encryption { enabled = true }

  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}-eval-results" })
}

resource "aws_dynamodb_table" "chat_history" {
  name         = "${var.project_name}-${var.environment}-chat-history"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"
  range_key    = "timestamp"

  attribute {
    name = "session_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  server_side_encryption { enabled = true }

  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}-chat-history" })
}

resource "aws_iam_policy" "dynamodb_full" {
  name        = "${var.project_name}-${var.environment}-dynamodb-full"
  description = "Full access to application DynamoDB tables"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem",
          "dynamodb:DescribeTable"
        ]
        Resource = [
          aws_dynamodb_table.scan_jobs.arn,
          "${aws_dynamodb_table.scan_jobs.arn}/index/*",
          aws_dynamodb_table.scan_results.arn,
          "${aws_dynamodb_table.scan_results.arn}/index/*",
          aws_dynamodb_table.connections.arn,
          "${aws_dynamodb_table.connections.arn}/index/*",
          aws_dynamodb_table.ws_connections.arn,
          "${aws_dynamodb_table.ws_connections.arn}/index/*",
          aws_dynamodb_table.eval_results.arn,
          aws_dynamodb_table.chat_history.arn
        ]
      }
    ]
  })
}
