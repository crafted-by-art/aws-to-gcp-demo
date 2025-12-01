# ArticleService API Gateway Resources

# /api/articles resource
resource "aws_api_gateway_resource" "articles_resource" {
  rest_api_id = aws_api_gateway_rest_api.pet_clinic_api.id
  parent_id   = aws_api_gateway_resource.api_resource.id
  path_part   = "articles"
}

# /api/articles/{slug} resource
resource "aws_api_gateway_resource" "article_slug_resource" {
  rest_api_id = aws_api_gateway_rest_api.pet_clinic_api.id
  parent_id   = aws_api_gateway_resource.articles_resource.id
  path_part   = "{slug}"
}

# /api/articles/feed resource
resource "aws_api_gateway_resource" "article_feed_resource" {
  rest_api_id = aws_api_gateway_rest_api.pet_clinic_api.id
  parent_id   = aws_api_gateway_resource.articles_resource.id
  path_part   = "feed"
}

# /api/articles/{slug}/favorite resource
resource "aws_api_gateway_resource" "article_favorite_resource" {
  rest_api_id = aws_api_gateway_rest_api.pet_clinic_api.id
  parent_id   = aws_api_gateway_resource.article_slug_resource.id
  path_part   = "favorite"
}

# /api/articles/{slug}/comments resource
resource "aws_api_gateway_resource" "article_comments_resource" {
  rest_api_id = aws_api_gateway_rest_api.pet_clinic_api.id
  parent_id   = aws_api_gateway_resource.article_slug_resource.id
  path_part   = "comments"
}

# /api/articles/{slug}/comments/{id} resource
resource "aws_api_gateway_resource" "article_comment_id_resource" {
  rest_api_id = aws_api_gateway_rest_api.pet_clinic_api.id
  parent_id   = aws_api_gateway_resource.article_comments_resource.id
  path_part   = "{id}"
}

# /api/tags resource
resource "aws_api_gateway_resource" "tags_resource" {
  rest_api_id = aws_api_gateway_rest_api.pet_clinic_api.id
  parent_id   = aws_api_gateway_resource.api_resource.id
  path_part   = "tags"
}

# Methods for /api/articles

# GET method for /api/articles
resource "aws_api_gateway_method" "article_service_get_articles_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.articles_resource.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "article_service_get_articles_integration" {
  rest_api_id             = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id             = aws_api_gateway_resource.articles_resource.id
  http_method             = aws_api_gateway_method.article_service_get_articles_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.article_service.invoke_arn
}

# POST method for /api/articles
resource "aws_api_gateway_method" "article_service_create_article_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.articles_resource.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "article_service_create_article_integration" {
  rest_api_id             = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id             = aws_api_gateway_resource.articles_resource.id
  http_method             = aws_api_gateway_method.article_service_create_article_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.article_service.invoke_arn
}

# OPTIONS method for CORS on /api/articles
resource "aws_api_gateway_method" "articles_options_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.articles_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "articles_options_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.articles_resource.id
  http_method   = aws_api_gateway_method.articles_options_method.http_method
  status_code   = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration" "articles_options_integration" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.articles_resource.id
  http_method   = aws_api_gateway_method.articles_options_method.http_method
  type          = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration_response" "articles_options_integration_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.articles_resource.id
  http_method   = aws_api_gateway_method.articles_options_method.http_method
  status_code   = aws_api_gateway_method_response.articles_options_response.status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'",
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,OPTIONS'",
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# Methods for /api/articles/{slug}

# GET method for /api/articles/{slug}
resource "aws_api_gateway_method" "article_service_get_article_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_slug_resource.id
  http_method   = "GET"
  authorization = "NONE"
  request_parameters = {
    "method.request.path.slug" = true
  }
}

resource "aws_api_gateway_integration" "article_service_get_article_integration" {
  rest_api_id             = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id             = aws_api_gateway_resource.article_slug_resource.id
  http_method             = aws_api_gateway_method.article_service_get_article_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.article_service.invoke_arn
}

# PUT method for /api/articles/{slug}
resource "aws_api_gateway_method" "article_service_update_article_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_slug_resource.id
  http_method   = "PUT"
  authorization = "NONE"
  request_parameters = {
    "method.request.path.slug" = true
  }
}

resource "aws_api_gateway_integration" "article_service_update_article_integration" {
  rest_api_id             = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id             = aws_api_gateway_resource.article_slug_resource.id
  http_method             = aws_api_gateway_method.article_service_update_article_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.article_service.invoke_arn
}

# DELETE method for /api/articles/{slug}
resource "aws_api_gateway_method" "article_service_delete_article_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_slug_resource.id
  http_method   = "DELETE"
  authorization = "NONE"
  request_parameters = {
    "method.request.path.slug" = true
  }
}

resource "aws_api_gateway_integration" "article_service_delete_article_integration" {
  rest_api_id             = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id             = aws_api_gateway_resource.article_slug_resource.id
  http_method             = aws_api_gateway_method.article_service_delete_article_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.article_service.invoke_arn
}

# OPTIONS method for CORS on /api/articles/{slug}
resource "aws_api_gateway_method" "article_slug_options_method" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_slug_resource.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method_response" "article_slug_options_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_slug_resource.id
  http_method   = aws_api_gateway_method.article_slug_options_method.http_method
  status_code   = "200"
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true,
    "method.response.header.Access-Control-Allow-Methods" = true,
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration" "article_slug_options_integration" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_slug_resource.id
  http_method   = aws_api_gateway_method.article_slug_options_method.http_method
  type          = "MOCK"
  
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration_response" "article_slug_options_integration_response" {
  rest_api_id   = aws_api_gateway_rest_api.pet_clinic_api.id
  resource_id   = aws_api_gateway_resource.article_slug_resource.id
  http_method   = aws_api_gateway_method.article_slug_options_method.http_method
  status_code   = aws_api_gateway_method_response.article_slug_options_response.status_code
  
  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token'",
    "method.response.header.Access-Control-Allow-Methods" = "'GET,PUT,DELETE,OPTIONS'",
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# Methods for /api/articles/feed - moved to api_gateway_article_feed.tf and integrated with the ArticleFeedService Lambda

# Methods for /api/articles/{slug}/favorite

# Moved to api_gateway_article_favorite.tf and integrated with the ArticleFavoriteService Lambda

# Methods for /api/articles/{slug}/comments

# Comment methods are moved to api_gateway_comment.tf and integrated with the CommentService Lambda

# Methods for /api/articles/{slug}/comments/{id}

# Comment delete method is moved to api_gateway_comment.tf and integrated with the CommentService Lambda

# Methods for /api/tags

# Tags resource and methods are moved to api_gateway_tag.tf and integrated with the TagService Lambda

# OPTIONS method for /api/tags is moved to api_gateway_tag.tf and integrated with the TagService Lambda