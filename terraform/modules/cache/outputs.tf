output "redis_endpoint" { value = aws_elasticache_replication_group.main.primary_endpoint_address }
output "redis_port" { value = aws_elasticache_replication_group.main.port }
output "redis_url" { value = "rediss://${aws_elasticache_replication_group.main.primary_endpoint_address}:${aws_elasticache_replication_group.main.port}" }
output "redis_security_group_id" { value = aws_security_group.redis.id }
