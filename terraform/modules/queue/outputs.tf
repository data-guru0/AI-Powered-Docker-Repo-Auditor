output "scan_jobs_queue_url" { value = aws_sqs_queue.scan_jobs.id }
output "scan_jobs_queue_arn" { value = aws_sqs_queue.scan_jobs.arn }
output "scan_dlq_arn" { value = aws_sqs_queue.scan_dlq.arn }
output "sqs_producer_policy_arn" { value = aws_iam_policy.sqs_producer.arn }
output "sqs_consumer_policy_arn" { value = aws_iam_policy.sqs_consumer.arn }
