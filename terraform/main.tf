provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

locals {
  common_tags = merge(var.tags, {
    Project     = var.project_name
    Environment = var.environment
  })
}

module "iam" {
  source = "./modules/iam"

  project_name   = var.project_name
  environment    = var.environment
  aws_account_id = var.aws_account_id
  github_org     = var.github_org
  github_repo    = var.github_repo
  tags           = local.common_tags
}

module "networking" {
  source = "./modules/networking"

  project_name = var.project_name
  environment  = var.environment
  aws_region   = var.aws_region
  vpc_cidr     = var.vpc_cidr
  tags         = local.common_tags
}

module "ecr" {
  source = "./modules/ecr"

  project_name = var.project_name
  environment  = var.environment
  tags         = local.common_tags
}

module "auth" {
  source = "./modules/auth"

  project_name   = var.project_name
  environment    = var.environment
  aws_account_id = var.aws_account_id
  tags           = local.common_tags
}

module "secrets" {
  source = "./modules/secrets"

  project_name   = var.project_name
  environment    = var.environment
  aws_region     = var.aws_region
  aws_account_id = var.aws_account_id
  tags           = local.common_tags
}

module "database" {
  source = "./modules/database"

  project_name = var.project_name
  environment  = var.environment
  tags         = local.common_tags
}

module "storage" {
  source = "./modules/storage"

  project_name   = var.project_name
  environment    = var.environment
  aws_account_id = var.aws_account_id
  tags           = local.common_tags
}

module "queue" {
  source = "./modules/queue"

  project_name = var.project_name
  environment  = var.environment
  tags         = local.common_tags
}

module "cache" {
  source = "./modules/cache"

  project_name               = var.project_name
  environment                = var.environment
  vpc_id                     = module.networking.vpc_id
  private_subnet_ids         = module.networking.private_subnet_ids
  allowed_security_group_ids = [module.networking.lambda_security_group_id]
  redis_node_type            = var.redis_node_type
  tags                       = local.common_tags
}

module "lambda" {
  source = "./modules/lambda"

  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  trivy_image_uri    = ""
  tags               = local.common_tags
}

module "api" {
  source = "./modules/api"

  project_name         = var.project_name
  environment          = var.environment
  aws_region           = var.aws_region
  cognito_user_pool_id = module.auth.user_pool_id
  cognito_client_id    = module.auth.client_id
  tags                 = local.common_tags
}

module "monitoring" {
  source = "./modules/monitoring"

  project_name     = var.project_name
  environment      = var.environment
  aws_region       = var.aws_region
  ecs_cluster_name = module.ecs.cluster_name
  alarm_email      = var.alarm_email
  tags             = local.common_tags
}

module "ecs" {
  source = "./modules/ecs"

  project_name             = var.project_name
  environment              = var.environment
  aws_region               = var.aws_region
  vpc_id                   = module.networking.vpc_id
  vpc_cidr                 = module.networking.vpc_cidr
  public_subnet_ids        = module.networking.public_subnet_ids
  private_subnet_ids       = module.networking.private_subnet_ids
  frontend_image           = var.frontend_image
  backend_image            = var.backend_image
  worker_image             = var.worker_image
  cognito_user_pool_id     = module.auth.user_pool_id
  cognito_client_id        = module.auth.client_id
  cognito_identity_pool_id = module.auth.identity_pool_id
  scan_jobs_table          = module.database.scan_jobs_table_name
  scan_results_table       = module.database.scan_results_table_name
  connections_table        = module.database.connections_table_name
  ws_connections_table     = module.database.ws_connections_table_name
  chat_history_table       = module.database.chat_history_table_name
  scan_jobs_queue_url      = module.queue.scan_jobs_queue_url
  scan_reports_bucket      = module.storage.scan_reports_bucket_name
  redis_url                = module.cache.redis_url
  ses_from_email           = var.ses_from_email
  secret_prefix            = module.secrets.credential_prefix
  openai_secret_arn        = module.secrets.openai_api_key_secret_arn
  openai_secret_name       = module.secrets.openai_api_key_secret_name
  langsmith_secret_arn     = module.secrets.langsmith_api_key_secret_arn
  langsmith_secret_name    = module.secrets.langsmith_api_key_secret_name
  trivy_lambda_name        = module.lambda.trivy_scanner_name
  websocket_execution_arn  = module.api.websocket_management_url
  websocket_url            = module.api.websocket_stage_url
  frontend_log_group       = module.monitoring.frontend_log_group
  backend_log_group        = module.monitoring.backend_log_group
  worker_log_group         = module.monitoring.worker_log_group
  dynamodb_policy_arn      = module.database.dynamodb_full_policy_arn
  s3_policy_arn            = module.storage.s3_full_policy_arn
  secrets_read_policy_arn  = module.secrets.secrets_read_policy_arn
  secrets_write_policy_arn = module.secrets.secrets_write_policy_arn
  sqs_producer_policy_arn  = module.queue.sqs_producer_policy_arn
  sqs_consumer_policy_arn  = module.queue.sqs_consumer_policy_arn
  invoke_trivy_policy_arn  = module.lambda.invoke_trivy_policy_arn
  apigw_post_policy_arn    = module.api.apigw_post_policy_arn
  frontend_min_tasks       = var.frontend_min_tasks
  backend_min_tasks        = var.backend_min_tasks
  backend_max_tasks        = var.backend_max_tasks
  worker_min_tasks         = var.worker_min_tasks
  worker_max_tasks         = var.worker_max_tasks
  tags                     = local.common_tags
}

# Lambda integration for $connect — receives connectionId natively via event.requestContext
resource "aws_apigatewayv2_integration" "backend" {
  api_id           = module.api.websocket_api_id
  integration_type = "AWS_PROXY"
  integration_uri  = module.api.ws_connect_invoke_arn

  lifecycle {
    create_before_destroy = true
  }
}

# Lambda integration for $disconnect
resource "aws_apigatewayv2_integration" "ws_disconnect" {
  api_id           = module.api.websocket_api_id
  integration_type = "AWS_PROXY"
  integration_uri  = module.api.ws_disconnect_invoke_arn

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_apigatewayv2_integration" "ws_message" {
  api_id             = module.api.websocket_api_id
  integration_type   = "HTTP_PROXY"
  integration_uri    = "http://${module.ecs.backend_alb_dns}/api/v1/ws/message"
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "connect" {
  api_id             = module.api.websocket_api_id
  route_key          = "$connect"
  authorization_type = "CUSTOM"
  authorizer_id      = module.api.websocket_authorizer_id
  target             = "integrations/${aws_apigatewayv2_integration.backend.id}"
}

resource "aws_apigatewayv2_route" "disconnect" {
  api_id    = module.api.websocket_api_id
  route_key = "$disconnect"
  target    = "integrations/${aws_apigatewayv2_integration.ws_disconnect.id}"
}

resource "aws_apigatewayv2_route" "subscribe" {
  api_id    = module.api.websocket_api_id
  route_key = "subscribe"
  target    = "integrations/${aws_apigatewayv2_integration.ws_message.id}"
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = module.api.websocket_api_id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.ws_message.id}"
}
