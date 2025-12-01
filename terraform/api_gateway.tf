# API Gateway REST API
resource "aws_api_gateway_rest_api" "pet_clinic_api" {
  name        = var.api_gateway_name
  description = "API Gateway for Django REST Pet Clinic"

  endpoint_configuration {
    types = ["REGIONAL"]
  }
}

# API Gateway Stage
resource "aws_api_gateway_stage" "pet_clinic_stage" {
  deployment_id = aws_api_gateway_deployment.pet_clinic_deployment.id
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  stage_name    = var.api_gateway_stage_name
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "pet_clinic_deployment" {
  rest_api_id = aws_api_gateway_rest_api.pet_clinic_api.id
  
  # Ensure deployment happens after all resources are created
  depends_on = [
    aws_api_gateway_integration.auth_service_registration_integration,
    aws_api_gateway_integration.auth_service_login_integration,
    aws_api_gateway_integration.auth_service_get_user_integration,
    aws_api_gateway_integration.auth_service_update_user_integration,
    aws_api_gateway_integration.profile_service_get_integration,
    aws_api_gateway_integration.profile_service_username_get_integration,
    aws_api_gateway_integration.profile_service_follow_post_integration,
    aws_api_gateway_integration.profile_service_follow_delete_integration,
    aws_api_gateway_integration.article_service_get_articles_integration,
    aws_api_gateway_integration.article_service_create_article_integration,
    aws_api_gateway_integration.article_service_get_article_integration,
    aws_api_gateway_integration.article_service_update_article_integration,
    aws_api_gateway_integration.article_service_delete_article_integration,
    aws_api_gateway_integration.article_feed_service_integration,
    aws_api_gateway_integration.article_favorite_post_integration,
    aws_api_gateway_integration.article_favorite_delete_integration,
    aws_api_gateway_integration.comment_service_comments_get_integration,
    aws_api_gateway_integration.comment_service_comments_post_integration,
    aws_api_gateway_integration.comment_service_comment_delete_integration,
    aws_api_gateway_integration.tag_service_tags_integration
  ]

  # Force re-deployment when routes change
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.api_resource.id,
      aws_api_gateway_resource.users_resource.id,
      aws_api_gateway_resource.login_resource.id,
      aws_api_gateway_resource.user_resource.id,
      aws_api_gateway_resource.profiles_resource.id,
      aws_api_gateway_resource.profile_username_resource.id,
      aws_api_gateway_resource.profile_follow_resource.id,
      aws_api_gateway_resource.articles_resource.id,
      aws_api_gateway_resource.article_slug_resource.id,
      aws_api_gateway_resource.article_feed_resource.id,
      aws_api_gateway_resource.article_favorite_resource.id,
      aws_api_gateway_resource.article_comments_resource.id,
      aws_api_gateway_resource.article_comment_id_resource.id,
      aws_api_gateway_resource.tags_resource.id,
      aws_api_gateway_method.auth_service_registration_method.id,
      aws_api_gateway_method.auth_service_login_method.id,
      aws_api_gateway_method.auth_service_get_user_method.id,
      aws_api_gateway_method.auth_service_update_user_method.id,
      aws_api_gateway_method.profile_service_get_method.id,
      aws_api_gateway_method.profile_service_username_get_method.id,
      aws_api_gateway_method.profile_service_follow_post_method.id,
      aws_api_gateway_method.profile_service_follow_delete_method.id,
      aws_api_gateway_method.article_service_get_articles_method.id,
      aws_api_gateway_method.article_service_create_article_method.id,
      aws_api_gateway_method.article_service_get_article_method.id,
      aws_api_gateway_method.article_service_update_article_method.id,
      aws_api_gateway_method.article_service_delete_article_method.id,
      aws_api_gateway_method.article_feed_service_method.id,
      aws_api_gateway_method.article_favorite_post_method.id,
      aws_api_gateway_method.article_favorite_delete_method.id,
      aws_api_gateway_method.comment_service_comments_get_method.id,
      aws_api_gateway_method.comment_service_comments_post_method.id,
      aws_api_gateway_method.comment_service_comment_delete_method.id,
      aws_api_gateway_method.tag_service_tags_method.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

# /api resource
resource "aws_api_gateway_resource" "api_resource" {
  rest_api_id = aws_api_gateway_rest_api.pet_clinic_api.id
  parent_id   = aws_api_gateway_rest_api.pet_clinic_api.root_resource_id
  path_part   = "api"
}

# /api/users resource
resource "aws_api_gateway_resource" "users_resource" {
  rest_api_id = aws_api_gateway_rest_api.pet_clinic_api.id
  parent_id   = aws_api_gateway_resource.api_resource.id
  path_part   = "users"
}

# /api/users/login resource
resource "aws_api_gateway_resource" "login_resource" {
  rest_api_id = aws_api_gateway_rest_api.pet_clinic_api.id
  parent_id   = aws_api_gateway_resource.users_resource.id
  path_part   = "login"
}

# /api/user resource
resource "aws_api_gateway_resource" "user_resource" {
  rest_api_id = aws_api_gateway_rest_api.pet_clinic_api.id
  parent_id   = aws_api_gateway_resource.api_resource.id
  path_part   = "user"
}

# POST method for /api/users (registration)
resource "aws_api_gateway_method" "auth_service_registration_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.users_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "auth_service_registration_integration" {
  rest_api_id             = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id             = aws_api_gateway_resource.users_resource.id
  http_method             = aws_api_gateway_method.auth_service_registration_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.authentication_service.invoke_arn
}

# POST method for /api/users/login
resource "aws_api_gateway_method" "auth_service_login_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.login_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "auth_service_login_integration" {
  rest_api_id             = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id             = aws_api_gateway_resource.login_resource.id
  http_method             = aws_api_gateway_method.auth_service_login_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.authentication_service.invoke_arn
}

# GET method for /api/user
resource "aws_api_gateway_method" "auth_service_get_user_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.user_resource.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "auth_service_get_user_integration" {
  rest_api_id             = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id             = aws_api_gateway_resource.user_resource.id
  http_method             = aws_api_gateway_method.auth_service_get_user_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.authentication_service.invoke_arn
}

# PUT method for /api/user
resource "aws_api_gateway_method" "auth_service_update_user_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.user_resource.id
  http_method   = "PUT"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "auth_service_update_user_integration" {
  rest_api_id             = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id             = aws_api_gateway_resource.user_resource.id
  http_method             = aws_api_gateway_method.auth_service_update_user_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.authentication_service.invoke_arn
}

# OPTIONS method for CORS on /api/users
resource "aws_api_gateway_method" "users_options_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.users_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "users_options_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.users_resource.id
  http_method   = aws_api_gateway_method.users_options_method.http_method
  status_code   = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration" "users_options_integration" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.users_resource.id
  http_method   = aws_api_gateway_method.users_options_method.http_method
  type          = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration_response" "users_options_integration_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.users_resource.id
  http_method   = aws_api_gateway_method.users_options_method.http_method
  status_code   = aws_api_gateway_method_response.users_options_response.status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'",
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'",
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# OPTIONS method for CORS on /api/users/login
resource "aws_api_gateway_method" "login_options_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.login_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "login_options_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.login_resource.id
  http_method   = aws_api_gateway_method.login_options_method.http_method
  status_code   = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration" "login_options_integration" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.login_resource.id
  http_method   = aws_api_gateway_method.login_options_method.http_method
  type          = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration_response" "login_options_integration_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.login_resource.id
  http_method   = aws_api_gateway_method.login_options_method.http_method
  status_code   = aws_api_gateway_method_response.login_options_response.status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'",
    "method.response.header.Access-Control-Allow-Methods" = "'POST,OPTIONS'",
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# /api/profiles resource
resource "aws_api_gateway_resource" "profiles_resource" {
  rest_api_id = aws_api_gateway_rest_api.pet_clinic_api.id
  parent_id   = aws_api_gateway_resource.api_resource.id
  path_part   = "profiles"
}

# /api/profiles/{username} resource
resource "aws_api_gateway_resource" "profile_username_resource" {
  rest_api_id = aws_api_gateway_rest_api.pet_clinic_api.id
  parent_id   = aws_api_gateway_resource.profiles_resource.id
  path_part   = "{username}"
}

# /api/profiles/{username}/follow resource
resource "aws_api_gateway_resource" "profile_follow_resource" {
  rest_api_id = aws_api_gateway_rest_api.pet_clinic_api.id
  parent_id   = aws_api_gateway_resource.profile_username_resource.id
  path_part   = "follow"
}

# GET method for /api/profiles
resource "aws_api_gateway_method" "profile_service_get_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.profiles_resource.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "profile_service_get_integration" {
  rest_api_id             = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id             = aws_api_gateway_resource.profiles_resource.id
  http_method             = aws_api_gateway_method.profile_service_get_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.profile_service.invoke_arn
}

# GET method for /api/profiles/{username}
resource "aws_api_gateway_method" "profile_service_username_get_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.profile_username_resource.id
  http_method   = "GET"
  authorization = "NONE"
  request_parameters = {
    "method.request.path.username" = true
  }
}

resource "aws_api_gateway_integration" "profile_service_username_get_integration" {
  rest_api_id             = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id             = aws_api_gateway_resource.profile_username_resource.id
  http_method             = aws_api_gateway_method.profile_service_username_get_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.profile_service.invoke_arn
}

# POST method for /api/profiles/{username}/follow
resource "aws_api_gateway_method" "profile_service_follow_post_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.profile_follow_resource.id
  http_method   = "POST"
  authorization = "NONE"
  request_parameters = {
    "method.request.path.username" = true
  }
}

resource "aws_api_gateway_integration" "profile_service_follow_post_integration" {
  rest_api_id             = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id             = aws_api_gateway_resource.profile_follow_resource.id
  http_method             = aws_api_gateway_method.profile_service_follow_post_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.profile_service.invoke_arn
}

# DELETE method for /api/profiles/{username}/follow
resource "aws_api_gateway_method" "profile_service_follow_delete_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.profile_follow_resource.id
  http_method   = "DELETE"
  authorization = "NONE"
  request_parameters = {
    "method.request.path.username" = true
  }
}

resource "aws_api_gateway_integration" "profile_service_follow_delete_integration" {
  rest_api_id             = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id             = aws_api_gateway_resource.profile_follow_resource.id
  http_method             = aws_api_gateway_method.profile_service_follow_delete_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.profile_service.invoke_arn
}

# OPTIONS method for CORS on /api/profiles
resource "aws_api_gateway_method" "profiles_options_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.profiles_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "profiles_options_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.profiles_resource.id
  http_method   = aws_api_gateway_method.profiles_options_method.http_method
  status_code   = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration" "profiles_options_integration" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.profiles_resource.id
  http_method   = aws_api_gateway_method.profiles_options_method.http_method
  type          = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration_response" "profiles_options_integration_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.profiles_resource.id
  http_method   = aws_api_gateway_method.profiles_options_method.http_method
  status_code   = aws_api_gateway_method_response.profiles_options_response.status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'",
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'",
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# OPTIONS method for CORS on /api/profiles/{username}
resource "aws_api_gateway_method" "profile_username_options_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.profile_username_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "profile_username_options_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.profile_username_resource.id
  http_method   = aws_api_gateway_method.profile_username_options_method.http_method
  status_code   = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration" "profile_username_options_integration" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.profile_username_resource.id
  http_method   = aws_api_gateway_method.profile_username_options_method.http_method
  type          = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration_response" "profile_username_options_integration_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.profile_username_resource.id
  http_method   = aws_api_gateway_method.profile_username_options_method.http_method
  status_code   = aws_api_gateway_method_response.profile_username_options_response.status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'",
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'",
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# OPTIONS method for CORS on /api/profiles/{username}/follow
resource "aws_api_gateway_method" "profile_follow_options_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.profile_follow_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "profile_follow_options_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.profile_follow_resource.id
  http_method   = aws_api_gateway_method.profile_follow_options_method.http_method
  status_code   = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration" "profile_follow_options_integration" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.profile_follow_resource.id
  http_method   = aws_api_gateway_method.profile_follow_options_method.http_method
  type          = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration_response" "profile_follow_options_integration_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.profile_follow_resource.id
  http_method   = aws_api_gateway_method.profile_follow_options_method.http_method
  status_code   = aws_api_gateway_method_response.profile_follow_options_response.status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'",
    "method.response.header.Access-Control-Allow-Methods" = "'POST,DELETE,OPTIONS'",
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# OPTIONS method for CORS on /api/user
resource "aws_api_gateway_method" "user_options_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.user_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "user_options_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.user_resource.id
  http_method   = aws_api_gateway_method.user_options_method.http_method
  status_code   = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration" "user_options_integration" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.user_resource.id
  http_method   = aws_api_gateway_method.user_options_method.http_method
  type          = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration_response" "user_options_integration_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.user_resource.id
  http_method   = aws_api_gateway_method.user_options_method.http_method
  status_code   = aws_api_gateway_method_response.user_options_response.status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'",
    "method.response.header.Access-Control-Allow-Methods" = "'GET,PUT,OPTIONS'",
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}