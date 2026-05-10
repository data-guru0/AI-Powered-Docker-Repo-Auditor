aws_region     = "us-east-1"
aws_account_id = "789438508565"
project_name   = "docker-auditor"
environment    = "dev"
vpc_cidr       = "10.0.0.0/16"

frontend_image = "789438508565.dkr.ecr.us-east-1.amazonaws.com/docker-auditor-dev-frontend:latest"
backend_image  = "789438508565.dkr.ecr.us-east-1.amazonaws.com/docker-auditor-dev-backend:latest"
worker_image   = "789438508565.dkr.ecr.us-east-1.amazonaws.com/docker-auditor-dev-worker:latest"

frontend_min_tasks = 1
backend_min_tasks  = 1
backend_max_tasks  = 2
worker_min_tasks   = 1
worker_max_tasks   = 2
redis_node_type    = "cache.t3.micro"
ses_from_email     = "sudhanshugusain45@gmail.com"
alarm_email        = "sudhanshugusain45@gmail.com"
github_org         = "data-guru0"
github_repo        = "TESTING-MAJOR-22"
