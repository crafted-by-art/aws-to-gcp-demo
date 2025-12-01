# TagService API Gateway Integration

# Note: The /api/tags resource is already defined in api_gateway_article.tf

# GET method for /api/tags
resource "aws_api_gateway_method" "tag_service_tags_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.tags_resource.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "tag_service_tags_integration" {
  rest_api_id             = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id             = aws_api_gateway_resource.tags_resource.id
  http_method             = aws_api_gateway_method.tag_service_tags_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.tag_service.invoke_arn
}

# OPTIONS method for CORS on /api/tags
resource "aws_api_gateway_method" "tag_service_tags_options_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.tags_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "tag_service_tags_options_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.tags_resource.id
  http_method   = aws_api_gateway_method.tag_service_tags_options_method.http_method
  status_code   = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration" "tag_service_tags_options_integration" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.tags_resource.id
  http_method   = aws_api_gateway_method.tag_service_tags_options_method.http_method
  type          = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration_response" "tag_service_tags_options_integration_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.tags_resource.id
  http_method   = aws_api_gateway_method.tag_service_tags_options_method.http_method
  status_code   = aws_api_gateway_method_response.tag_service_tags_options_response.status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'",
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'",
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}