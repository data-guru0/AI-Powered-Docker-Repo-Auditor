variable "project_name" { type = string }
variable "environment" { type = string }
variable "aws_region" { type = string }
variable "ecs_cluster_name" { type = string }
variable "alarm_email" {
  type    = string
  default = ""
}
variable "tags" {
  type    = map(string)
  default = {}
}
