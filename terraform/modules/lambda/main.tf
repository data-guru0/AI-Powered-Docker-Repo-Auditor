data "aws_iam_policy_document" "lambda_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "trivy_scanner" {
  name               = "${var.project_name}-${var.environment}-trivy-scanner"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = merge(var.tags, { Name = "${var.project_name}-${var.environment}-trivy-scanner-role" })
}

resource "aws_iam_role_policy_attachment" "trivy_vpc" {
  role       = aws_iam_role.trivy_scanner.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

resource "aws_iam_role_policy" "trivy_ecr" {
  name = "${var.project_name}-${var.environment}-trivy-ecr"
  role = aws_iam_role.trivy_scanner.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:DescribeImages",
          "ecr:ListImages"
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["inspector2:ListFindings", "inspector2:GetFindingsReportStatus"]
        Resource = "*"
      }
    ]
  })
}

resource "aws_security_group" "trivy_lambda" {
  name        = "${var.project_name}-${var.environment}-trivy-lambda"
  description = "Trivy scanner Lambda security group"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}-trivy-lambda-sg" })
}

data "archive_file" "trivy_placeholder" {
  type        = "zip"
  output_path = "${path.module}/trivy_placeholder.zip"
  source {
    filename = "index.py"
    content  = "def handler(event, context): return {'statusCode': 200, 'findings': []}"
  }
}

resource "aws_lambda_function" "trivy_scanner" {
  function_name    = "${var.project_name}-${var.environment}-trivy-scanner"
  role             = aws_iam_role.trivy_scanner.arn
  package_type     = "Zip"
  filename         = data.archive_file.trivy_placeholder.output_path
  source_code_hash = data.archive_file.trivy_placeholder.output_base64sha256
  runtime          = "python3.12"
  handler          = "index.handler"
  timeout          = 300
  memory_size      = 1024

  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [aws_security_group.trivy_lambda.id]
  }

  environment {
    variables = {
      ENVIRONMENT  = var.environment
      PROJECT_NAME = var.project_name
    }
  }

  tracing_config { mode = "Active" }

  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}-trivy-scanner" })

  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }
}

resource "aws_cloudwatch_log_group" "trivy_scanner" {
  name              = "/aws/lambda/${aws_lambda_function.trivy_scanner.function_name}"
  retention_in_days = 30
  tags              = var.tags
}

resource "aws_iam_policy" "invoke_trivy" {
  name        = "${var.project_name}-${var.environment}-invoke-trivy"
  description = "Allow invoking Trivy scanner Lambda"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["lambda:InvokeFunction"]
        Resource = aws_lambda_function.trivy_scanner.arn
      }
    ]
  })
}
