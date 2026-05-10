output "websocket_api_id" { value = aws_apigatewayv2_api.websocket.id }
output "websocket_api_endpoint" { value = aws_apigatewayv2_api.websocket.api_endpoint }
output "websocket_stage_url" { value = "${aws_apigatewayv2_api.websocket.api_endpoint}/${var.environment}" }
output "websocket_management_url" { value = "https://${trimprefix(aws_apigatewayv2_api.websocket.api_endpoint, "wss://")}/${var.environment}" }
output "websocket_execution_arn" { value = aws_apigatewayv2_api.websocket.execution_arn }
output "websocket_authorizer_id" { value = aws_apigatewayv2_authorizer.cognito.id }
output "apigw_post_policy_arn" { value = aws_iam_policy.apigw_post_to_connection.arn }
