output "frontend_repository_url" { value = aws_ecr_repository.frontend.repository_url }
output "backend_repository_url" { value = aws_ecr_repository.backend.repository_url }
output "worker_repository_url" { value = aws_ecr_repository.worker.repository_url }
