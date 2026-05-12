aws_region     = "us-east-1"
aws_account_id = "123456789012"
project_name   = "docker-auditor"
environment    = "staging"
ses_from_email = "noreply@docker-auditor.example.com"
vpc_cidr       = "10.1.0.0/16"

frontend_image = "123456789012.dkr.ecr.us-east-1.amazonaws.com/docker-auditor-staging-frontend:latest"
backend_image  = "123456789012.dkr.ecr.us-east-1.amazonaws.com/docker-auditor-staging-backend:latest"
worker_image   = "123456789012.dkr.ecr.us-east-1.amazonaws.com/docker-auditor-staging-worker:latest"

frontend_min_tasks = 1
backend_min_tasks  = 1
backend_max_tasks  = 3
worker_min_tasks   = 1
worker_max_tasks   = 3
redis_node_type    = "cache.t3.small"
alarm_email        = "devops@example.com"
