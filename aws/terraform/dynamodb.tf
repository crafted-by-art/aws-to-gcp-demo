###########################################################
# DynamoDB Tables
###########################################################

# Users table
resource "aws_dynamodb_table" "users_table" {
  name           = "Users"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"
  
  attribute {
    name = "id"
    type = "S"
  }
  
  attribute {
    name = "username"
    type = "S"
  }
  
  attribute {
    name = "email"
    type = "S"
  }
  
  global_secondary_index {
    name               = "username-index"
    hash_key           = "username"
    projection_type    = "ALL"
  }
  
  global_secondary_index {
    name               = "EmailIndex"
    hash_key           = "email"
    projection_type    = "ALL"
  }
  
  tags = {
    Name        = "Users"
    Environment = var.environment
  }
}

# Profiles table
resource "aws_dynamodb_table" "profiles_table" {
  name           = "Profiles"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"
  
  attribute {
    name = "id"
    type = "S"
  }
  
  attribute {
    name = "username"
    type = "S"
  }
  
  attribute {
    name = "user_id"
    type = "S"
  }
  
  global_secondary_index {
    name               = "username-index"
    hash_key           = "username"
    projection_type    = "ALL"
  }
  
  global_secondary_index {
    name               = "user_id-index"
    hash_key           = "user_id"
    projection_type    = "ALL"
  }
  
  tags = {
    Name        = "Profiles"
    Environment = var.environment
  }
}

# Articles table
resource "aws_dynamodb_table" "articles_table" {
  name           = "Articles"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "slug"
  
  attribute {
    name = "slug"
    type = "S"
  }
  
  attribute {
    name = "author_id"
    type = "S"
  }
  
  global_secondary_index {
    name               = "author_id-index"
    hash_key           = "author_id"
    projection_type    = "ALL"
  }
  
  tags = {
    Name        = "Articles"
    Environment = var.environment
  }
}

# Comments table
resource "aws_dynamodb_table" "comments_table" {
  name           = "Comments"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "comment_id"
  
  attribute {
    name = "comment_id"
    type = "S"
  }
  
  attribute {
    name = "article_slug"
    type = "S"
  }
  
  global_secondary_index {
    name               = "article_index"
    hash_key           = "article_slug"
    projection_type    = "ALL"
  }
  
  tags = {
    Name        = "Comments"
    Environment = var.environment
  }
}

# Tags table
resource "aws_dynamodb_table" "tags_table" {
  name           = "Tags"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "tag"
  
  attribute {
    name = "tag"
    type = "S"
  }
  
  tags = {
    Name        = "Tags"
    Environment = var.environment
  }
}

# Follows table
resource "aws_dynamodb_table" "follows_table" {
  name           = "Follows"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "follower_id"
  range_key      = "followed_id"
  
  attribute {
    name = "follower_id"
    type = "S"
  }
  
  attribute {
    name = "followed_id"
    type = "S"
  }
  
  tags = {
    Name        = "Follows"
    Environment = var.environment
  }
}

# Article Favorites table
resource "aws_dynamodb_table" "article_favorites_table" {
  name           = "ArticleFavorites"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "username"
  range_key      = "article_slug"
  
  attribute {
    name = "username"
    type = "S"
  }
  
  attribute {
    name = "article_slug"
    type = "S"
  }
  
  global_secondary_index {
    name               = "article_slug-index"
    hash_key           = "article_slug"
    projection_type    = "ALL"
  }
  
  tags = {
    Name        = "ArticleFavorites"
    Environment = var.environment
  }
}