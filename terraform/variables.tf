variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "aws_account_id" {
  type = string
}

variable "project_name" {
  type    = string
  default = "docker-auditor"
}

variable "environment" {
  type = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod"
  }
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "ses_from_email" {
  type    = string
  default = ""
}

variable "frontend_image" {
  type = string
}

variable "backend_image" {
  type = string
}

variable "worker_image" {
  type = string
}


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

variable "redis_node_type" {
  type    = string
  default = "cache.t3.micro"
}

variable "alarm_email" {
  type    = string
  default = ""
}

variable "github_org" {
  type        = string
  description = "GitHub username or organization"
}

variable "github_repo" {
  type        = string
  default     = "docker-image-auditor"
  description = "GitHub repository name"
}

variable "sentry_dsn" {
  type        = string
  default     = ""
  description = "Sentry DSN for error monitoring (backend and worker)"
}

variable "sentry_dsn_frontend" {
  type        = string
  default     = ""
  description = "Sentry DSN for frontend error monitoring (baked into Next.js build)"
}

variable "otel_exporter_otlp_endpoint" {
  type        = string
  default     = ""
  description = "Grafana Cloud OTLP endpoint for traces and metrics"
}

variable "otel_exporter_otlp_headers" {
  type        = string
  default     = ""
  description = "Grafana Cloud OTLP auth header (Authorization=Basic <base64(instanceId:apiKey)>)"
  sensitive   = true
}

variable "tags" {
  type    = map(string)
  default = {}
}
