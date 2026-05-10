resource "aws_secretsmanager_secret" "openai_api_key" {
  name                    = "${var.project_name}/${var.environment}/openai-api-key"
  description             = "OpenAI API key for LLM agents"
  recovery_window_in_days = 7
  tags                    = merge(var.tags, { Name = "${var.project_name}-${var.environment}-openai-key" })
}

resource "aws_secretsmanager_secret" "langsmith_api_key" {
  name                    = "${var.project_name}/${var.environment}/langsmith-api-key"
  description             = "LangSmith API key for tracing"
  recovery_window_in_days = 7
  tags                    = merge(var.tags, { Name = "${var.project_name}-${var.environment}-langsmith-key" })
}

resource "aws_secretsmanager_secret" "registry_credentials_prefix" {
  name                    = "${var.project_name}/${var.environment}/registry-credentials-prefix"
  description             = "Prefix path for per-user registry credentials"
  recovery_window_in_days = 7
  tags                    = merge(var.tags, { Name = "${var.project_name}-${var.environment}-registry-prefix" })
}

resource "aws_secretsmanager_secret_version" "registry_credentials_prefix" {
  secret_id     = aws_secretsmanager_secret.registry_credentials_prefix.id
  secret_string = jsonencode({ prefix = "${var.project_name}/${var.environment}" })
}

resource "aws_iam_policy" "secrets_read" {
  name        = "${var.project_name}-${var.environment}-secrets-read"
  description = "Allow reading application secrets"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          aws_secretsmanager_secret.openai_api_key.arn,
          aws_secretsmanager_secret.langsmith_api_key.arn,
          "arn:aws:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:${var.project_name}/${var.environment}/users/*"
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "secrets_write" {
  name        = "${var.project_name}-${var.environment}-secrets-write"
  description = "Allow creating/updating user registry credentials"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:CreateSecret",
          "secretsmanager:PutSecretValue",
          "secretsmanager:DeleteSecret",
          "secretsmanager:TagResource"
        ]
        Resource = "arn:aws:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:${var.project_name}/${var.environment}/users/*"
      }
    ]
  })
}
