output "openai_api_key_secret_arn" { value = aws_secretsmanager_secret.openai_api_key.arn }
output "openai_api_key_secret_name" { value = aws_secretsmanager_secret.openai_api_key.name }
output "langsmith_api_key_secret_arn" { value = aws_secretsmanager_secret.langsmith_api_key.arn }
output "langsmith_api_key_secret_name" { value = aws_secretsmanager_secret.langsmith_api_key.name }
output "secrets_read_policy_arn" { value = aws_iam_policy.secrets_read.arn }
output "secrets_write_policy_arn" { value = aws_iam_policy.secrets_write.arn }
output "credential_prefix" { value = "${var.project_name}/${var.environment}" }
