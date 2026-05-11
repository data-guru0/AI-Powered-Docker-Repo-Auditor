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

# Observability
sentry_dsn          = "https://e5940f7c2fc5c2804b7d618c28e177ce@o4511369794158592.ingest.us.sentry.io/4511369862774785"
sentry_dsn_frontend = "https://ab2fc5f13383b74e531e8094feb53229@o4511369794158592.ingest.us.sentry.io/4511369866051584"

otel_exporter_otlp_endpoint = "https://otlp-gateway-prod-ap-south-1.grafana.net/otlp"
otel_exporter_otlp_headers  = "Authorization=Basic%20MTYzMTgxMjpnbGNfZXlKdklqb2lNVGMyTWpNd05TSXNJbTRpT2lKbmNtRm1ZVzVoTFRrM05qQWlMQ0pySWpvaVFqQmxkWEUyVXpJMmNFeEtNbU5HT1VjM04yODNNRkZPSWl3aWJTSTZleUp5SWpvaWNISnZaQzFoY0MxemIzVjBhQzB4SW4xOQ=="
