variable "project_name" { type = string }
variable "environment" { type = string }
variable "domain_name" { type = string }
variable "frontend_alb_dns" { type = string }
variable "frontend_alb_zone_id" { type = string }
variable "backend_alb_dns" { type = string }
variable "backend_alb_zone_id" { type = string }
variable "tags" {
  type    = map(string)
  default = {}
}
