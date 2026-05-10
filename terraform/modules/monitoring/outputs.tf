output "frontend_log_group" { value = aws_cloudwatch_log_group.frontend.name }
output "backend_log_group" { value = aws_cloudwatch_log_group.backend.name }
output "worker_log_group" { value = aws_cloudwatch_log_group.worker.name }
output "alarm_sns_topic_arn" { value = aws_sns_topic.alarms.arn }
