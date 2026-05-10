variable "project_name" { type = string }
variable "environment" { type = string }
variable "aws_region" { type = string }
variable "vpc_id" { type = string }
variable "vpc_cidr" { type = string }
variable "public_subnet_ids" { type = list(string) }
variable "private_subnet_ids" { type = list(string) }
variable "frontend_image" { type = string }
variable "backend_image" { type = string }
variable "worker_image" { type = string }
variable "cognito_user_pool_id" { type = string }
variable "cognito_client_id" { type = string }
variable "cognito_identity_pool_id" { type = string }
variable "scan_jobs_table" { type = string }
variable "scan_results_table" { type = string }
variable "connections_table" { type = string }
variable "ws_connections_table" { type = string }
variable "scan_jobs_queue_url" { type = string }
variable "scan_reports_bucket" { type = string }
variable "redis_url" { type = string }
variable "ses_from_email" { type = string }
variable "secret_prefix" { type = string }
variable "openai_secret_arn" { type = string }
variable "openai_secret_name" { type = string }
variable "langsmith_secret_arn" { type = string }
variable "langsmith_secret_name" { type = string }
variable "trivy_lambda_name" { type = string }
variable "websocket_execution_arn" { type = string }
variable "websocket_url" { type = string }
variable "access_logs_bucket" {
  type    = string
  default = ""
}
variable "frontend_log_group" { type = string }
variable "backend_log_group" { type = string }
variable "worker_log_group" { type = string }
variable "dynamodb_policy_arn" { type = string }
variable "s3_policy_arn" { type = string }
variable "secrets_read_policy_arn" { type = string }
variable "secrets_write_policy_arn" { type = string }
variable "sqs_producer_policy_arn" { type = string }
variable "sqs_consumer_policy_arn" { type = string }
variable "invoke_trivy_policy_arn" { type = string }
variable "apigw_post_policy_arn" { type = string }
variable "frontend_min_tasks" {
  type    = number
  default = 1
}
variable "backend_min_tasks" {
  type    = number
  default = 1
}
variable "backend_max_tasks" {
  type    = number
  default = 4
}
variable "worker_min_tasks" {
  type    = number
  default = 1
}
variable "worker_max_tasks" {
  type    = number
  default = 4
}
variable "tags" {
  type    = map(string)
  default = {}
}
