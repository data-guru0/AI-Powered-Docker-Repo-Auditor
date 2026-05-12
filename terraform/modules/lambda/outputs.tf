output "trivy_scanner_name" { value = aws_lambda_function.trivy_scanner.function_name }
output "invoke_trivy_policy_arn" { value = aws_iam_policy.invoke_trivy.arn }
