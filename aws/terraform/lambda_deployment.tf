# Configuration for Lambda deployments

###########################################################
# Authentication Service Lambda
###########################################################
resource "aws_s3_object" "auth_service_lambda" {
  bucket = aws_s3_bucket.lambda_bucket.id
  key    = "AuthenticationService.zip"
  source = "../lambdas/archives/AuthenticationService.zip"
  etag   = filemd5("../lambdas/archives/AuthenticationService.zip")
}

resource "aws_lambda_function" "authentication_service" {
  function_name = "${var.project_name}-authentication-service-${var.environment}"
  description   = "Authentication service handling user registration, login, and profile updates"
  
  s3_bucket     = aws_s3_bucket.lambda_bucket.id
  s3_key        = aws_s3_object.auth_service_lambda.key
  source_code_hash = filebase64sha256("../lambdas/archives/AuthenticationService.zip")
  
  handler     = "lambda_function.lambda_handler"
  runtime     = var.lambda_runtime
  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout
  role        = aws_iam_role.lambda_execution_role.arn

  environment {
    variables = {
      USERS_TABLE    = aws_dynamodb_table.users_table.name
      PROFILES_TABLE = aws_dynamodb_table.profiles_table.name
      JWT_SECRET     = "secure-jwt-secret-to-be-replaced" # Should be replaced with a secure value from SSM/Secrets Manager
    }
  }
}

###########################################################
# Profile Service Lambda
###########################################################
resource "aws_s3_object" "profile_service_lambda" {
  bucket = aws_s3_bucket.lambda_bucket.id
  key    = "ProfileService.zip"
  source = "../lambdas/archives/ProfileService.zip"
  etag   = filemd5("../lambdas/archives/ProfileService.zip")
}

resource "aws_lambda_function" "profile_service" {
  function_name = "${var.project_name}-profile-service-${var.environment}"
  description   = "Handles profile retrieval and follow/unfollow operations for users"
  
  s3_bucket     = aws_s3_bucket.lambda_bucket.id
  s3_key        = aws_s3_object.profile_service_lambda.key
  source_code_hash = filebase64sha256("../lambdas/archives/ProfileService.zip")
  
  handler     = "lambda_function.lambda_handler"
  runtime     = var.lambda_runtime
  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout
  role        = aws_iam_role.lambda_execution_role.arn

  environment {
    variables = {
      USER_TABLE    = aws_dynamodb_table.users_table.name
      PROFILES_TABLE = aws_dynamodb_table.profiles_table.name
      FOLLOWS_TABLE  = aws_dynamodb_table.follows_table.name
      JWT_SECRET_KEY = "secure-jwt-secret-to-be-replaced" # Should be replaced with a secure value from SSM/Secrets Manager
    }
  }
}

###########################################################
# Article Service Lambda
###########################################################
resource "aws_s3_object" "article_service_lambda" {
  bucket = aws_s3_bucket.lambda_bucket.id
  key    = "ArticleService.zip"
  source = "../lambdas/archives/ArticleService.zip"
  etag   = filemd5("../lambdas/archives/ArticleService.zip")
}

resource "aws_lambda_function" "article_service" {
  function_name = "${var.project_name}-article-service-${var.environment}"
  description   = "Handles article creation, retrieval, updating and listing"
  
  s3_bucket     = aws_s3_bucket.lambda_bucket.id
  s3_key        = aws_s3_object.article_service_lambda.key
  source_code_hash = filebase64sha256("../lambdas/archives/ArticleService.zip")
  
  handler     = "lambda_function.lambda_handler"
  runtime     = var.lambda_runtime
  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout
  role        = aws_iam_role.lambda_execution_role.arn

  environment {
    variables = {
      USERS_TABLE    = aws_dynamodb_table.users_table.name
      PROFILES_TABLE = aws_dynamodb_table.profiles_table.name
      ARTICLES_TABLE = aws_dynamodb_table.articles_table.name
      TAGS_TABLE     = aws_dynamodb_table.tags_table.name
      COMMENTS_TABLE = aws_dynamodb_table.comments_table.name
      JWT_SECRET     = "secure-jwt-secret-to-be-replaced" # Should be replaced with a secure value from SSM/Secrets Manager
    }
  }
}

###########################################################
# Comment Service Lambda
###########################################################
resource "aws_s3_object" "comment_service_lambda" {
  bucket = aws_s3_bucket.lambda_bucket.id
  key    = "CommentService.zip"
  source = "../lambdas/archives/CommentService.zip"
  etag   = filemd5("../lambdas/archives/CommentService.zip")
}

resource "aws_lambda_function" "comment_service" {
  function_name = "${var.project_name}-comment-service-${var.environment}"
  description   = "Manages article comments including creation, listing and deletion"
  
  s3_bucket     = aws_s3_bucket.lambda_bucket.id
  s3_key        = aws_s3_object.comment_service_lambda.key
  source_code_hash = filebase64sha256("../lambdas/archives/CommentService.zip")
  
  handler     = "lambda_function.lambda_handler"
  runtime     = var.lambda_runtime
  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout
  role        = aws_iam_role.lambda_execution_role.arn

  environment {
    variables = {
      COMMENTS_TABLE = aws_dynamodb_table.comments_table.name
      ARTICLES_TABLE = aws_dynamodb_table.articles_table.name
      PROFILES_TABLE = aws_dynamodb_table.profiles_table.name
      JWT_SECRET     = "secure-jwt-secret-to-be-replaced" # Should be replaced with a secure value from SSM/Secrets Manager
    }
  }
}

###########################################################
# Tag Service Lambda
###########################################################
resource "aws_s3_object" "tag_service_lambda" {
  bucket = aws_s3_bucket.lambda_bucket.id
  key    = "TagService.zip"
  source = "../lambdas/archives/TagService.zip"
  etag   = filemd5("../lambdas/archives/TagService.zip")
}

resource "aws_lambda_function" "tag_service" {
  function_name = "${var.project_name}-tag-service-${var.environment}"
  description   = "Provides a list of all article tags in the system"
  
  s3_bucket     = aws_s3_bucket.lambda_bucket.id
  s3_key        = aws_s3_object.tag_service_lambda.key
  source_code_hash = filebase64sha256("../lambdas/archives/TagService.zip")
  
  handler     = "lambda_function.lambda_handler"
  runtime     = var.lambda_runtime
  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout
  role        = aws_iam_role.lambda_execution_role.arn

  environment {
    variables = {
      TAGS_TABLE = aws_dynamodb_table.tags_table.name
    }
  }
}

###########################################################
# Article Favorite Service Lambda
###########################################################
resource "aws_s3_object" "article_favorite_service_lambda" {
  bucket = aws_s3_bucket.lambda_bucket.id
  key    = "ArticleFavoriteService.zip"
  source = "../lambdas/archives/ArticleFavoriteService.zip"
  etag   = filemd5("../lambdas/archives/ArticleFavoriteService.zip")
}

resource "aws_lambda_function" "article_favorite_service" {
  function_name = "${var.project_name}-article-favorite-service-${var.environment}"
  description   = "Manages favoriting and unfavoriting articles by users"
  
  s3_bucket     = aws_s3_bucket.lambda_bucket.id
  s3_key        = aws_s3_object.article_favorite_service_lambda.key
  source_code_hash = filebase64sha256("../lambdas/archives/ArticleFavoriteService.zip")
  
  handler     = "lambda_function.lambda_handler"
  runtime     = var.lambda_runtime
  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout
  role        = aws_iam_role.lambda_execution_role.arn

  environment {
    variables = {
      USERS_TABLE          = aws_dynamodb_table.users_table.name
      ARTICLES_TABLE       = aws_dynamodb_table.articles_table.name
      FAVORITES_TABLE      = aws_dynamodb_table.article_favorites_table.name
      JWT_SECRET           = "secure-jwt-secret-to-be-replaced" # Should be replaced with a secure value from SSM/Secrets Manager
    }
  }
}

###########################################################
# Article Feed Service Lambda
###########################################################
resource "aws_s3_object" "article_feed_service_lambda" {
  bucket = aws_s3_bucket.lambda_bucket.id
  key    = "ArticleFeedService.zip"
  source = "../lambdas/archives/ArticleFeedService.zip"
  etag   = filemd5("../lambdas/archives/ArticleFeedService.zip")
}

resource "aws_lambda_function" "article_feed_service" {
  function_name = "${var.project_name}-article-feed-service-${var.environment}"
  description   = "Provides personalized article feed for authenticated users based on their following list"
  
  s3_bucket     = aws_s3_bucket.lambda_bucket.id
  s3_key        = aws_s3_object.article_feed_service_lambda.key
  source_code_hash = filebase64sha256("../lambdas/archives/ArticleFeedService.zip")
  
  handler     = "lambda_function.lambda_handler"
  runtime     = var.lambda_runtime
  memory_size = var.lambda_memory_size
  timeout     = var.lambda_timeout
  role        = aws_iam_role.lambda_execution_role.arn

  environment {
    variables = {
      USERS_TABLE    = aws_dynamodb_table.users_table.name
      PROFILES_TABLE = aws_dynamodb_table.profiles_table.name
      FOLLOWS_TABLE  = aws_dynamodb_table.follows_table.name
      ARTICLES_TABLE = aws_dynamodb_table.articles_table.name
      JWT_SECRET     = "secure-jwt-secret-to-be-replaced" # Should be replaced with a secure value from SSM/Secrets Manager
    }
  }
}

###########################################################
# Lambda Permissions for API Gateway
###########################################################
resource "aws_lambda_permission" "api_gateway_auth_service" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.authentication_service.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn = "${aws_api_gateway_rest_api.pet_clinic_api.execution_arn}/*/*/*"
}

resource "aws_lambda_permission" "api_gateway_profile_service" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.profile_service.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn = "${aws_api_gateway_rest_api.pet_clinic_api.execution_arn}/*/*/*"
}

resource "aws_lambda_permission" "api_gateway_article_service" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.article_service.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn = "${aws_api_gateway_rest_api.pet_clinic_api.execution_arn}/*/*/*"
}

resource "aws_lambda_permission" "api_gateway_comment_service" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.comment_service.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn = "${aws_api_gateway_rest_api.pet_clinic_api.execution_arn}/*/*/*"
}

resource "aws_lambda_permission" "api_gateway_tag_service" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.tag_service.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn = "${aws_api_gateway_rest_api.pet_clinic_api.execution_arn}/*/*/*"
}

resource "aws_lambda_permission" "api_gateway_article_favorite_service" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.article_favorite_service.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn = "${aws_api_gateway_rest_api.pet_clinic_api.execution_arn}/*/*/*"
}

resource "aws_lambda_permission" "api_gateway_article_feed_service" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.article_feed_service.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn = "${aws_api_gateway_rest_api.pet_clinic_api.execution_arn}/*/*/*"
}