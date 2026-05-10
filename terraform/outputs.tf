output "github_deploy_role_arn" {
  value       = module.iam.github_deploy_role_arn
  description = "ARN for AWS_DEPLOY_ROLE_ARN GitHub secret"
}

output "github_terraform_role_arn" {
  value       = module.iam.github_terraform_role_arn
  description = "ARN for AWS_TERRAFORM_ROLE_ARN GitHub secret"
}

output "frontend_url" {
  value       = "http://${module.ecs.frontend_alb_dns}"
  description = "Frontend application URL"
}

output "backend_url" {
  value       = "http://${module.ecs.backend_alb_dns}"
  description = "Backend API URL"
}

output "frontend_alb_dns" {
  value       = module.ecs.frontend_alb_dns
  description = "Frontend ALB DNS name"
}

output "backend_alb_dns" {
  value       = module.ecs.backend_alb_dns
  description = "Backend ALB DNS name"
}

output "websocket_url" {
  value       = module.api.websocket_stage_url
  description = "API Gateway WebSocket URL"
}

output "frontend_ecr_url" {
  value       = module.ecr.frontend_repository_url
  description = "Frontend ECR repository URL"
}

output "backend_ecr_url" {
  value       = module.ecr.backend_repository_url
  description = "Backend ECR repository URL"
}

output "worker_ecr_url" {
  value       = module.ecr.worker_repository_url
  description = "Worker ECR repository URL"
}

output "cognito_user_pool_id" {
  value       = module.auth.user_pool_id
  description = "Cognito User Pool ID"
}

output "cognito_client_id" {
  value       = module.auth.client_id
  description = "Cognito App Client ID"
}

output "ecs_cluster_name" {
  value       = module.ecs.cluster_name
  description = "ECS cluster name"
}

output "openai_secret_name" {
  value       = module.secrets.openai_api_key_secret_name
  description = "Secrets Manager name for OpenAI API key"
}

output "langsmith_secret_name" {
  value       = module.secrets.langsmith_api_key_secret_name
  description = "Secrets Manager name for LangSmith API key"
}
