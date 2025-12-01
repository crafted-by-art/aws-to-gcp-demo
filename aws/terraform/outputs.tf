# API Gateway output
output "api_gateway_url" {
  value = "${aws_api_gateway_deployment.pet_clinic_deployment.invoke_url}${aws_api_gateway_stage.pet_clinic_stage.stage_name}"
  description = "URL of the API Gateway"
}

# Lambda function outputs
output "authentication_service_arn" {
  value       = aws_lambda_function.authentication_service.arn
  description = "The ARN of the Authentication Service Lambda function"
}

output "profile_service_arn" {
  value       = aws_lambda_function.profile_service.arn
  description = "The ARN of the Profile Service Lambda function"
}

output "article_service_arn" {
  value       = aws_lambda_function.article_service.arn
  description = "The ARN of the Article Service Lambda function"
}

output "comment_service_arn" {
  value       = aws_lambda_function.comment_service.arn
  description = "The ARN of the Comment Service Lambda function"
}

output "tag_service_arn" {
  value       = aws_lambda_function.tag_service.arn
  description = "The ARN of the Tag Service Lambda function"
}

output "article_favorite_service_arn" {
  value       = aws_lambda_function.article_favorite_service.arn
  description = "The ARN of the Article Favorite Service Lambda function"
}

output "article_feed_service_arn" {
  value       = aws_lambda_function.article_feed_service.arn
  description = "The ARN of the Article Feed Service Lambda function"
}

# S3 bucket output
output "lambda_bucket_name" {
  value       = aws_s3_bucket.lambda_bucket.id
  description = "The name of the S3 bucket for Lambda deployment packages"
}

# DynamoDB table outputs
output "dynamodb_tables" {
  value = {
    users            = aws_dynamodb_table.users_table.name
    profiles         = aws_dynamodb_table.profiles_table.name
    articles         = aws_dynamodb_table.articles_table.name
    comments         = aws_dynamodb_table.comments_table.name
    tags             = aws_dynamodb_table.tags_table.name
    follows          = aws_dynamodb_table.follows_table.name
    article_favorites = aws_dynamodb_table.article_favorites_table.name
  }
  description = "The names of all DynamoDB tables"
}