variable "project_name" { type = string }
variable "environment" { type = string }
variable "aws_region" { type = string }
variable "cognito_user_pool_id" { type = string }
variable "cognito_client_id" { type = string }
variable "tags" {
  type    = map(string)
  default = {}
}
