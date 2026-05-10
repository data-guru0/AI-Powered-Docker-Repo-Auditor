resource "aws_apigatewayv2_api" "websocket" {
  name                       = "${var.project_name}-${var.environment}-ws"
  protocol_type              = "WEBSOCKET"
  route_selection_expression = "$request.body.action"
  tags                       = merge(var.tags, { Name = "${var.project_name}-${var.environment}-ws" })
}

resource "aws_apigatewayv2_stage" "websocket" {
  api_id      = aws_apigatewayv2_api.websocket.id
  name        = var.environment
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 1000
    throttling_rate_limit  = 500
  }


  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}-ws-stage" })
}

resource "aws_cloudwatch_log_group" "websocket" {
  name              = "/aws/apigateway/${var.project_name}-${var.environment}-ws"
  retention_in_days = 30
  tags              = var.tags
}

data "aws_iam_policy_document" "lambda_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ws_authorizer" {
  name               = "${var.project_name}-${var.environment}-ws-authorizer"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "ws_authorizer_basic" {
  role       = aws_iam_role.ws_authorizer.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "ws_authorizer" {
  function_name    = "${var.project_name}-${var.environment}-ws-authorizer"
  role             = aws_iam_role.ws_authorizer.arn
  runtime          = "python3.12"
  handler          = "index.handler"
  timeout          = 10
  memory_size      = 128
  filename         = data.archive_file.ws_authorizer.output_path
  source_code_hash = data.archive_file.ws_authorizer.output_base64sha256

  environment {
    variables = {
      COGNITO_USER_POOL_ID = var.cognito_user_pool_id
      COGNITO_CLIENT_ID    = var.cognito_client_id
      AWS_ACCOUNT_REGION   = var.aws_region
    }
  }

  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}-ws-authorizer" })
}

data "archive_file" "ws_authorizer" {
  type        = "zip"
  output_path = "${path.module}/ws_authorizer.zip"
  source {
    filename = "index.py"
    content  = <<-EOF
import base64, json

def handler(event, context):
    token = (event.get("queryStringParameters") or {}).get("token", "")
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid token")
        padding = 4 - len(parts[1]) % 4
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * padding))
        user_id = payload.get("sub", "")
        if not user_id:
            raise ValueError("No sub claim")
        return {
            "principalId": user_id,
            "policyDocument": {"Version": "2012-10-17", "Statement": [{"Action": "execute-api:Invoke", "Effect": "Allow", "Resource": event["methodArn"]}]},
            "context": {"userId": user_id}
        }
    except Exception:
        raise Exception("Unauthorized")
EOF
  }
}

resource "aws_cloudwatch_log_group" "ws_authorizer" {
  name              = "/aws/lambda/${aws_lambda_function.ws_authorizer.function_name}"
  retention_in_days = 30
  tags              = var.tags
}

resource "aws_apigatewayv2_authorizer" "cognito" {
  api_id           = aws_apigatewayv2_api.websocket.id
  authorizer_type  = "REQUEST"
  name             = "cognito-authorizer"
  identity_sources = ["route.request.querystring.token"]
  authorizer_uri   = "arn:aws:apigateway:${var.aws_region}:lambda:path/2015-03-31/functions/${aws_lambda_function.ws_authorizer.arn}/invocations"
}

resource "aws_lambda_permission" "api_gateway_authorizer" {
  statement_id  = "AllowAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ws_authorizer.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket.execution_arn}/*/*"
}

resource "aws_iam_role" "ws_events" {
  name               = "${var.project_name}-${var.environment}-ws-events"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "ws_events_basic" {
  role       = aws_iam_role.ws_events.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "ws_events_dynamodb" {
  name = "${var.project_name}-${var.environment}-ws-events-dynamodb"
  role = aws_iam_role.ws_events.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["dynamodb:PutItem", "dynamodb:DeleteItem", "dynamodb:Scan"]
      Resource = "arn:aws:dynamodb:${var.aws_region}:*:table/${var.project_name}-${var.environment}-ws-connections"
    }]
  })
}

data "archive_file" "ws_connect" {
  type        = "zip"
  output_path = "${path.module}/ws_connect.zip"
  source {
    filename = "index.py"
    content  = <<-EOF
import boto3, os
dynamodb = boto3.resource("dynamodb")

def handler(event, context):
    connection_id = event["requestContext"]["connectionId"]
    job_id = (event.get("queryStringParameters") or {}).get("jobId", "")
    if job_id:
        table = dynamodb.Table(os.environ["WS_CONNECTIONS_TABLE"])
        table.put_item(Item={"job_id": job_id, "connection_id": connection_id})
    return {"statusCode": 200, "body": "Connected"}
EOF
  }
}

resource "aws_lambda_function" "ws_connect" {
  function_name    = "${var.project_name}-${var.environment}-ws-connect"
  role             = aws_iam_role.ws_events.arn
  runtime          = "python3.12"
  handler          = "index.handler"
  timeout          = 10
  memory_size      = 128
  filename         = data.archive_file.ws_connect.output_path
  source_code_hash = data.archive_file.ws_connect.output_base64sha256

  environment {
    variables = {
      WS_CONNECTIONS_TABLE = "${var.project_name}-${var.environment}-ws-connections"
    }
  }

  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}-ws-connect" })
}

resource "aws_cloudwatch_log_group" "ws_connect" {
  name              = "/aws/lambda/${aws_lambda_function.ws_connect.function_name}"
  retention_in_days = 30
  tags              = var.tags
}

resource "aws_lambda_permission" "api_gateway_ws_connect" {
  statement_id  = "AllowAPIGatewayConnect"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ws_connect.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket.execution_arn}/*/*"
}

data "archive_file" "ws_disconnect" {
  type        = "zip"
  output_path = "${path.module}/ws_disconnect.zip"
  source {
    filename = "index.py"
    content  = <<-EOF
import boto3, os
dynamodb = boto3.resource("dynamodb")
attr = boto3.dynamodb.conditions.Attr

def handler(event, context):
    connection_id = event["requestContext"]["connectionId"]
    table = dynamodb.Table(os.environ["WS_CONNECTIONS_TABLE"])
    resp = table.scan(FilterExpression=attr("connection_id").eq(connection_id))
    for item in resp.get("Items", []):
        table.delete_item(Key={"job_id": item["job_id"], "connection_id": connection_id})
    return {"statusCode": 200, "body": "Disconnected"}
EOF
  }
}

resource "aws_lambda_function" "ws_disconnect" {
  function_name    = "${var.project_name}-${var.environment}-ws-disconnect"
  role             = aws_iam_role.ws_events.arn
  runtime          = "python3.12"
  handler          = "index.handler"
  timeout          = 10
  memory_size      = 128
  filename         = data.archive_file.ws_disconnect.output_path
  source_code_hash = data.archive_file.ws_disconnect.output_base64sha256

  environment {
    variables = {
      WS_CONNECTIONS_TABLE = "${var.project_name}-${var.environment}-ws-connections"
    }
  }

  tags = merge(var.tags, { Name = "${var.project_name}-${var.environment}-ws-disconnect" })
}

resource "aws_cloudwatch_log_group" "ws_disconnect" {
  name              = "/aws/lambda/${aws_lambda_function.ws_disconnect.function_name}"
  retention_in_days = 30
  tags              = var.tags
}

resource "aws_lambda_permission" "api_gateway_ws_disconnect" {
  statement_id  = "AllowAPIGatewayDisconnect"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ws_disconnect.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.websocket.execution_arn}/*/*"
}

resource "aws_iam_policy" "apigw_post_to_connection" {
  name        = "${var.project_name}-${var.environment}-apigw-post"
  description = "Allow posting to WebSocket connections"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["execute-api:ManageConnections"]
        Resource = "${aws_apigatewayv2_api.websocket.execution_arn}/${var.environment}/POST/@connections/*"
      }
    ]
  })
}
