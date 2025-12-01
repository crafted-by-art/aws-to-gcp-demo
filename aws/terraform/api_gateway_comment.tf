# CommentService API Gateway Integration

# Update API Gateway deployment to include comment service integrations
# The resources are already defined in api_gateway_article.tf:
# - /api/articles/{slug}/comments
# - /api/articles/{slug}/comments/{id}

# GET method for /api/articles/{slug}/comments
resource "aws_api_gateway_method" "comment_service_comments_get_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_comments_resource.id
  http_method   = "GET"
  authorization = "NONE"
  request_parameters = {
    "method.request.path.slug" = true
  }
}

resource "aws_api_gateway_integration" "comment_service_comments_get_integration" {
  rest_api_id             = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id             = aws_api_gateway_resource.article_comments_resource.id
  http_method             = aws_api_gateway_method.comment_service_comments_get_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.comment_service.invoke_arn
}

# POST method for /api/articles/{slug}/comments
resource "aws_api_gateway_method" "comment_service_comments_post_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_comments_resource.id
  http_method   = "POST"
  authorization = "NONE"
  request_parameters = {
    "method.request.path.slug" = true
  }
}

resource "aws_api_gateway_integration" "comment_service_comments_post_integration" {
  rest_api_id             = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id             = aws_api_gateway_resource.article_comments_resource.id
  http_method             = aws_api_gateway_method.comment_service_comments_post_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.comment_service.invoke_arn
}

# DELETE method for /api/articles/{slug}/comments/{id}
resource "aws_api_gateway_method" "comment_service_comment_delete_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_comment_id_resource.id
  http_method   = "DELETE"
  authorization = "NONE"
  request_parameters = {
    "method.request.path.slug" = true,
    "method.request.path.id"   = true
  }
}

resource "aws_api_gateway_integration" "comment_service_comment_delete_integration" {
  rest_api_id             = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id             = aws_api_gateway_resource.article_comment_id_resource.id
  http_method             = aws_api_gateway_method.comment_service_comment_delete_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.comment_service.invoke_arn
}

# OPTIONS method for CORS on /api/articles/{slug}/comments
resource "aws_api_gateway_method" "comment_service_comments_options_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_comments_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "comment_service_comments_options_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_comments_resource.id
  http_method   = aws_api_gateway_method.comment_service_comments_options_method.http_method
  status_code   = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration" "comment_service_comments_options_integration" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_comments_resource.id
  http_method   = aws_api_gateway_method.comment_service_comments_options_method.http_method
  type          = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration_response" "comment_service_comments_options_integration_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_comments_resource.id
  http_method   = aws_api_gateway_method.comment_service_comments_options_method.http_method
  status_code   = aws_api_gateway_method_response.comment_service_comments_options_response.status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'",
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,OPTIONS'",
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# OPTIONS method for CORS on /api/articles/{slug}/comments/{id}
resource "aws_api_gateway_method" "comment_service_comment_id_options_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_comment_id_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "comment_service_comment_id_options_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_comment_id_resource.id
  http_method   = aws_api_gateway_method.comment_service_comment_id_options_method.http_method
  status_code   = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration" "comment_service_comment_id_options_integration" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_comment_id_resource.id
  http_method   = aws_api_gateway_method.comment_service_comment_id_options_method.http_method
  type          = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration_response" "comment_service_comment_id_options_integration_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_comment_id_resource.id
  http_method   = aws_api_gateway_method.comment_service_comment_id_options_method.http_method
  status_code   = aws_api_gateway_method_response.comment_service_comment_id_options_response.status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'",
    "method.response.header.Access-Control-Allow-Methods" = "'DELETE,OPTIONS'",
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}