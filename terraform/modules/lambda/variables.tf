variable "project_name" { type = string }
variable "environment" { type = string }
variable "vpc_id" { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "trivy_image_uri" {
  type    = string
  default = ""
}
variable "tags" {
  type    = map(string)
  default = {}
}
