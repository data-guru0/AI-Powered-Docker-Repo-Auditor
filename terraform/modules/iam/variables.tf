variable "project_name" { type = string }
variable "environment" { type = string }
variable "aws_account_id" { type = string }
variable "github_org" { type = string }
variable "github_repo" { type = string }
variable "tags" {
  type    = map(string)
  default = {}
}
