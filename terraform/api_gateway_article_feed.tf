# ArticleFeedService API Gateway Integration

# GET method for /api/articles/feed
resource "aws_api_gateway_method" "article_feed_service_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_feed_resource.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "article_feed_service_integration" {
  rest_api_id             = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id             = aws_api_gateway_resource.article_feed_resource.id
  http_method             = aws_api_gateway_method.article_feed_service_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.article_feed_service.invoke_arn
}

# OPTIONS method for CORS on /api/articles/feed
resource "aws_api_gateway_method" "article_feed_service_options_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_feed_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "article_feed_service_options_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_feed_resource.id
  http_method   = aws_api_gateway_method.article_feed_service_options_method.http_method
  status_code   = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration" "article_feed_service_options_integration" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_feed_resource.id
  http_method   = aws_api_gateway_method.article_feed_service_options_method.http_method
  type          = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration_response" "article_feed_service_options_integration_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_feed_resource.id
  http_method   = aws_api_gateway_method.article_feed_service_options_method.http_method
  status_code   = aws_api_gateway_method_response.article_feed_service_options_response.status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'",
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'",
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}