variable "project_name" { type = string }
variable "environment" { type = string }
variable "frontend_alb_arn" { type = string }
variable "backend_alb_arn" { type = string }
variable "tags" {
  type    = map(string)
  default = {}
}
