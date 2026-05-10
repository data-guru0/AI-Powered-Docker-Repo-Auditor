resource "aws_sqs_queue" "scan_dlq" {
  name                        = "${var.project_name}-${var.environment}-scan-dlq.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  message_retention_seconds   = 1209600
  tags                        = merge(var.tags, { Name = "${var.project_name}-${var.environment}-scan-dlq" })
}

resource "aws_sqs_queue" "scan_jobs" {
  name                        = "${var.project_name}-${var.environment}-scan-jobs.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  visibility_timeout_seconds  = 900
  message_retention_seconds   = 86400
  receive_wait_time_seconds   = 20

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.scan_dlq.arn
    maxReceiveCount     = 3
  })

  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}-scan-jobs" })
}

resource "aws_iam_policy" "sqs_producer" {
  name        = "${var.project_name}-${var.environment}-sqs-producer"
  description = "Allow sending scan job messages to SQS"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["sqs:SendMessage", "sqs:GetQueueUrl", "sqs:GetQueueAttributes"]
        Resource = aws_sqs_queue.scan_jobs.arn
      }
    ]
  })
}

resource "aws_iam_policy" "sqs_consumer" {
  name        = "${var.project_name}-${var.environment}-sqs-consumer"
  description = "Allow consuming scan job messages from SQS"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes", "sqs:ChangeMessageVisibility"]
        Resource = aws_sqs_queue.scan_jobs.arn
      }
    ]
  })
}
