aws_region     = "us-east-1"
aws_account_id = "123456789012"
project_name   = "docker-auditor"
environment    = "prod"
domain_name    = "docker-auditor.example.com"
ses_from_email = "noreply@docker-auditor.example.com"
vpc_cidr       = "10.2.0.0/16"

frontend_image = "123456789012.dkr.ecr.us-east-1.amazonaws.com/docker-auditor-prod-frontend:latest"
backend_image  = "123456789012.dkr.ecr.us-east-1.amazonaws.com/docker-auditor-prod-backend:latest"
worker_image   = "123456789012.dkr.ecr.us-east-1.amazonaws.com/docker-auditor-prod-worker:latest"
trivy_image    = "123456789012.dkr.ecr.us-east-1.amazonaws.com/docker-auditor-prod-worker:latest"

frontend_min_tasks = 2
backend_min_tasks  = 2
backend_max_tasks  = 8
worker_min_tasks   = 2
worker_max_tasks   = 8
redis_node_type    = "cache.r6g.large"
alarm_email        = "oncall@example.com"
