data "aws_iam_policy_document" "ecs_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "task_execution" {
  name               = "${var.project_name}-${var.environment}-task-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "task_execution_basic" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "task_execution_secrets" {
  name = "${var.project_name}-${var.environment}-task-execution-secrets"
  role = aws_iam_role.task_execution.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue", "kms:Decrypt"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken", "ecr:BatchCheckLayerAvailability", "ecr:GetDownloadUrlForLayer", "ecr:BatchGetImage"]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role" "task" {
  name               = "${var.project_name}-${var.environment}-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "task_dynamodb" {
  role       = aws_iam_role.task.name
  policy_arn = var.dynamodb_policy_arn
}

resource "aws_iam_role_policy_attachment" "task_s3" {
  role       = aws_iam_role.task.name
  policy_arn = var.s3_policy_arn
}

resource "aws_iam_role_policy_attachment" "task_secrets_read" {
  role       = aws_iam_role.task.name
  policy_arn = var.secrets_read_policy_arn
}

resource "aws_iam_role_policy_attachment" "task_secrets_write" {
  role       = aws_iam_role.task.name
  policy_arn = var.secrets_write_policy_arn
}

resource "aws_iam_role_policy_attachment" "task_sqs_producer" {
  role       = aws_iam_role.task.name
  policy_arn = var.sqs_producer_policy_arn
}

resource "aws_iam_role_policy_attachment" "task_sqs_consumer" {
  role       = aws_iam_role.task.name
  policy_arn = var.sqs_consumer_policy_arn
}

resource "aws_iam_role_policy_attachment" "task_invoke_trivy" {
  role       = aws_iam_role.task.name
  policy_arn = var.invoke_trivy_policy_arn
}

resource "aws_iam_role_policy_attachment" "task_apigw_post" {
  role       = aws_iam_role.task.name
  policy_arn = var.apigw_post_policy_arn
}

resource "aws_iam_role_policy" "task_ses_xray" {
  name = "${var.project_name}-${var.environment}-task-ses-xray"
  role = aws_iam_role.task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ses:SendEmail", "ses:SendRawEmail"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["cloudwatch:PutMetricData", "logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["inspector2:ListFindings"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["ecr:DescribeImages", "ecr:ListImages", "ecr:GetAuthorizationToken"]
        Resource = "*"
      }
    ]
  })
}

resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}" })
}

resource "aws_ecs_cluster_capacity_providers" "main" {
  cluster_name       = aws_ecs_cluster.main.name
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  default_capacity_provider_strategy {
    base              = 1
    weight            = 100
    capacity_provider = "FARGATE"
  }
}

resource "aws_security_group" "alb_frontend" {
  name        = "${var.project_name}-${var.environment}-alb-frontend"
  description = "Frontend ALB security group"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}-alb-frontend-sg" })
}

resource "aws_security_group" "alb_backend" {
  name        = "${var.project_name}-${var.environment}-alb-backend"
  description = "Backend ALB security group"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}-alb-backend-sg" })
}

resource "aws_security_group" "frontend" {
  name        = "${var.project_name}-${var.environment}-frontend"
  description = "Frontend ECS task security group"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_frontend.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}-frontend-sg" })
}

resource "aws_security_group" "backend" {
  name        = "${var.project_name}-${var.environment}-backend"
  description = "Backend ECS task security group"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_backend.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}-backend-sg" })
}

resource "aws_security_group" "worker" {
  name        = "${var.project_name}-${var.environment}-worker"
  description = "Worker ECS task security group"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}-worker-sg" })
}

resource "aws_lb" "frontend" {
  name               = "${var.project_name}-${var.environment}-frontend"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_frontend.id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = var.environment == "prod"
  enable_http2               = true

  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}-frontend-alb" })
}

resource "aws_lb" "backend" {
  name               = "${var.project_name}-${var.environment}-backend"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_backend.id]
  subnets            = var.public_subnet_ids

  enable_deletion_protection = var.environment == "prod"
  enable_http2               = true

  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}-backend-alb" })
}

resource "aws_lb_target_group" "frontend" {
  name        = "${var.project_name}-${var.environment}-frontend"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/api/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 10
    interval            = 30
    matcher             = "200"
  }

  deregistration_delay = 30
  tags                 = var.tags
}

resource "aws_lb_target_group" "backend" {
  name        = "${var.project_name}-${var.environment}-backend"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/health"
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 10
    interval            = 30
    matcher             = "200"
  }

  deregistration_delay = 30
  tags                 = var.tags
}

resource "aws_lb_listener" "frontend_http" {
  load_balancer_arn = aws_lb.frontend.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

resource "aws_lb_listener" "backend_http" {
  load_balancer_arn = aws_lb.backend.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}

resource "aws_ecs_task_definition" "frontend" {
  family                   = "${var.project_name}-${var.environment}-frontend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name      = "frontend"
      image     = var.frontend_image
      essential = true

      portMappings = [
        { containerPort = 3000, protocol = "tcp" }
      ]

      environment = [
        { name = "NODE_ENV", value = "production" },
        { name = "NEXT_PUBLIC_API_URL", value = "http://${aws_lb.backend.dns_name}" },
        { name = "NEXT_PUBLIC_WS_URL", value = var.websocket_url },
        { name = "NEXT_PUBLIC_AWS_REGION", value = var.aws_region },
        { name = "NEXT_PUBLIC_COGNITO_USER_POOL_ID", value = var.cognito_user_pool_id },
        { name = "NEXT_PUBLIC_COGNITO_CLIENT_ID", value = var.cognito_client_id },
        { name = "NEXT_PUBLIC_COGNITO_IDENTITY_POOL_ID", value = var.cognito_identity_pool_id }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = var.frontend_log_group
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "frontend"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:3000/api/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = var.tags
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "${var.project_name}-${var.environment}-backend"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 1024
  memory                   = 2048
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = var.backend_image
      essential = true

      portMappings = [
        { containerPort = 8000, protocol = "tcp" }
      ]

      environment = [
        { name = "ENVIRONMENT", value = var.environment },
        { name = "PROJECT_NAME", value = var.project_name },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "FRONTEND_URL", value = "http://${aws_lb.frontend.dns_name}" },
        { name = "COGNITO_USER_POOL_ID", value = var.cognito_user_pool_id },
        { name = "COGNITO_CLIENT_ID", value = var.cognito_client_id },
        { name = "DYNAMODB_SCAN_JOBS_TABLE", value = var.scan_jobs_table },
        { name = "DYNAMODB_SCAN_RESULTS_TABLE", value = var.scan_results_table },
        { name = "DYNAMODB_CONNECTIONS_TABLE", value = var.connections_table },
        { name = "DYNAMODB_WS_CONNECTIONS_TABLE", value = var.ws_connections_table },
        { name = "SQS_SCAN_JOBS_URL", value = var.scan_jobs_queue_url },
        { name = "S3_SCAN_REPORTS_BUCKET", value = var.scan_reports_bucket },
        { name = "REDIS_URL", value = var.redis_url },
        { name = "SES_FROM_EMAIL", value = var.ses_from_email },
        { name = "SECRET_PREFIX", value = var.secret_prefix },
        { name = "WEBSOCKET_API_ENDPOINT", value = var.websocket_execution_arn },
        { name = "LANGCHAIN_TRACING_V2", value = "true" },
        { name = "LANGCHAIN_PROJECT", value = "${var.project_name}-${var.environment}" }
      ]

      secrets = [
        { name = "OPENAI_API_KEY_SECRET_NAME", valueFrom = var.openai_secret_arn },
        { name = "LANGSMITH_API_KEY_SECRET_NAME", valueFrom = var.langsmith_secret_arn }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = var.backend_log_group
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "backend"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = var.tags
}

resource "aws_ecs_task_definition" "worker" {
  family                   = "${var.project_name}-${var.environment}-worker"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 2048
  memory                   = 4096
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.task.arn

  container_definitions = jsonencode([
    {
      name      = "worker"
      image     = var.worker_image
      essential = true

      environment = [
        { name = "ENVIRONMENT", value = var.environment },
        { name = "PROJECT_NAME", value = var.project_name },
        { name = "AWS_REGION", value = var.aws_region },
        { name = "DYNAMODB_SCAN_JOBS_TABLE", value = var.scan_jobs_table },
        { name = "DYNAMODB_SCAN_RESULTS_TABLE", value = var.scan_results_table },
        { name = "DYNAMODB_WS_CONNECTIONS_TABLE", value = var.ws_connections_table },
        { name = "SQS_SCAN_JOBS_URL", value = var.scan_jobs_queue_url },
        { name = "S3_SCAN_REPORTS_BUCKET", value = var.scan_reports_bucket },
        { name = "REDIS_URL", value = var.redis_url },
        { name = "TRIVY_LAMBDA_FUNCTION_NAME", value = var.trivy_lambda_name },
        { name = "WEBSOCKET_API_ENDPOINT", value = var.websocket_execution_arn },
        { name = "SES_FROM_EMAIL", value = var.ses_from_email },
        { name = "SECRET_PREFIX", value = var.secret_prefix },
        { name = "OPENAI_API_KEY_SECRET_NAME", value = var.openai_secret_name },
        { name = "LANGSMITH_API_KEY_SECRET_NAME", value = var.langsmith_secret_name },
        { name = "LANGCHAIN_TRACING_V2", value = "true" },
        { name = "LANGCHAIN_PROJECT", value = "${var.project_name}-${var.environment}" }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = var.worker_log_group
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "worker"
        }
      }
    }
  ])

  tags = var.tags
}

resource "aws_ecs_service" "frontend" {
  name                              = "${var.project_name}-${var.environment}-frontend"
  cluster                           = aws_ecs_cluster.main.id
  task_definition                   = aws_ecs_task_definition.frontend.arn
  desired_count                     = var.frontend_min_tasks
  launch_type                       = "FARGATE"
  platform_version                  = "LATEST"
  health_check_grace_period_seconds = 120
  propagate_tags                    = "SERVICE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.frontend.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 3000
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  deployment_controller {
    type = "ECS"
  }

  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }

  tags = var.tags
}

resource "aws_ecs_service" "backend" {
  name                              = "${var.project_name}-${var.environment}-backend"
  cluster                           = aws_ecs_cluster.main.id
  task_definition                   = aws_ecs_task_definition.backend.arn
  desired_count                     = var.backend_min_tasks
  launch_type                       = "FARGATE"
  platform_version                  = "LATEST"
  health_check_grace_period_seconds = 120
  propagate_tags                    = "SERVICE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.backend.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  deployment_controller {
    type = "ECS"
  }

  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }

  tags = var.tags
}

resource "aws_ecs_service" "worker" {
  name             = "${var.project_name}-${var.environment}-worker"
  cluster          = aws_ecs_cluster.main.id
  task_definition  = aws_ecs_task_definition.worker.arn
  desired_count    = var.worker_min_tasks
  launch_type      = "FARGATE"
  platform_version = "LATEST"
  propagate_tags   = "SERVICE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.worker.id]
    assign_public_ip = false
  }

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  deployment_controller {
    type = "ECS"
  }

  lifecycle {
    ignore_changes = [task_definition, desired_count]
  }

  tags = var.tags
}

resource "aws_appautoscaling_target" "backend" {
  max_capacity       = var.backend_max_tasks
  min_capacity       = var.backend_min_tasks
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.backend.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "backend_cpu" {
  name               = "${var.project_name}-${var.environment}-backend-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.backend.resource_id
  scalable_dimension = aws_appautoscaling_target.backend.scalable_dimension
  service_namespace  = aws_appautoscaling_target.backend.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

resource "aws_appautoscaling_target" "worker" {
  max_capacity       = var.worker_max_tasks
  min_capacity       = var.worker_min_tasks
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.worker.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "worker_cpu" {
  name               = "${var.project_name}-${var.environment}-worker-cpu"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.worker.resource_id
  scalable_dimension = aws_appautoscaling_target.worker.scalable_dimension
  service_namespace  = aws_appautoscaling_target.worker.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}
