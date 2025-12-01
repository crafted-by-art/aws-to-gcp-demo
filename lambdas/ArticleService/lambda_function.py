import json
import os
import time
import uuid
import boto3
import re
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
import jwt
from datetime import datetime, timedelta

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
article_table = dynamodb.Table(os.environ.get('ARTICLE_TABLE', 'Articles'))
tag_table = dynamodb.Table(os.environ.get('TAG_TABLE', 'Tags'))
profile_table = dynamodb.Table(os.environ.get('PROFILE_TABLE', 'Profiles'))
comment_table = dynamodb.Table(os.environ.get('COMMENT_TABLE', 'Comments'))

# JWT Secret and Algorithm
JWT_SECRET = os.environ.get('JWT_SECRET', 'secret')
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_SECONDS = 86400  # 24 hours

# Pagination defaults
DEFAULT_LIMIT = 20
DEFAULT_OFFSET = 0


def generate_slug(title):
    """Generate a URL-friendly slug from a title."""
    # Convert to lowercase, replace spaces with hyphens, remove special chars
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    # Add a unique suffix to ensure uniqueness
    unique_suffix = str(int(time.time()))
    return f"{slug}-{unique_suffix}"


def extract_token(headers):
    """Extract the JWT token from request headers."""
    auth_header = headers.get('Authorization', '')
    if auth_header.startswith('Token '):
        return auth_header.split(' ')[1]
    return None


def decode_token(token):
    """Decode the JWT token and return the user information."""
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_user_from_token(headers):
    """Get user profile from the JWT token in headers."""
    token = extract_token(headers)
    if not token:
        return None
    
    payload = decode_token(token)
    if not payload:
        return None
    
    user_id = payload.get('id')
    if not user_id:
        return None
    
    # Get user profile from DynamoDB
    try:
        response = profile_table.get_item(Key={'user_id': user_id})
        return response.get('Item')
    except Exception:
        return None


def get_profile_by_username(username):
    """Get profile by username from DynamoDB."""
    try:
        # Query using a secondary index on username
        response = profile_table.query(
            IndexName='username-index',
            KeyConditionExpression=Key('username').eq(username)
        )
        items = response.get('Items', [])
        return items[0] if items else None
    except Exception as e:
        print(f"Error getting profile by username: {str(e)}")
        return None


def format_article_response(article, user_profile=None):
    """Format article for API response."""
    # Get author profile
    try:
        author = profile_table.get_item(Key={'user_id': article['author_id']}).get('Item', {})
    except Exception:
        author = {}
    
    # Format the author information
    author_data = {
        'username': author.get('username', ''),
        'bio': author.get('bio', ''),
        'image': author.get('image', ''),
        'following': False
    }
    
    # Check if the current user is following the author
    if user_profile and 'following' in user_profile:
        author_data['following'] = article['author_id'] in user_profile.get('following', [])
    
    # Get tags
    tags = []
    if 'tag_list' in article:
        tags = article['tag_list']
    
    # Calculate favorited status and count
    favorited = False
    favorites_count = article.get('favorites_count', 0)
    
    if user_profile and 'favorites' in user_profile:
        favorited = article['slug'] in user_profile.get('favorites', [])
    
    # Format datetime fields
    created_at = article.get('created_at', datetime.utcnow().isoformat())
    updated_at = article.get('updated_at', created_at)
    
    # Build the response
    return {
        'slug': article['slug'],
        'title': article['title'],
        'description': article.get('description', ''),
        'body': article.get('body', ''),
        'tagList': tags,
        'createdAt': created_at,
        'updatedAt': updated_at,
        'favorited': favorited,
        'favoritesCount': favorites_count,
        'author': author_data
    }


def handle_get_articles(event, user_profile=None):
    """Handle listing articles with filtering options."""
    params = event.get('queryStringParameters', {}) or {}
    
    # Parse pagination parameters
    try:
        limit = int(params.get('limit', DEFAULT_LIMIT))
        offset = int(params.get('offset', DEFAULT_OFFSET))
    except ValueError:
        limit = DEFAULT_LIMIT
        offset = DEFAULT_OFFSET
    
    # Prepare the scan filter
    filter_expression = None
    
    # Filter by author
    author_username = params.get('author')
    if author_username:
        author_profile = get_profile_by_username(author_username)
        if author_profile:
            author_id = author_profile.get('user_id')
            author_filter = Attr('author_id').eq(author_id)
            filter_expression = author_filter if not filter_expression else filter_expression & author_filter
    
    # Filter by tag
    tag = params.get('tag')
    if tag:
        tag_filter = Attr('tag_list').contains(tag)
        filter_expression = tag_filter if not filter_expression else filter_expression & tag_filter
    
    # Filter by favorited
    favorited_by = params.get('favorited')
    if favorited_by and user_profile:
        favorited_profile = get_profile_by_username(favorited_by)
        if favorited_profile and 'favorites' in favorited_profile:
            favs = favorited_profile.get('favorites', [])
            # We need to check each article's slug to see if it's in the favorites list
            # This is inefficient in DynamoDB but maintaining the original functionality
            # A better approach would be to use a GSI or separate table for favorites
            # This is a simplification for the migration
            if favs:
                favorited_filter = Attr('slug').is_in(favs)
                filter_expression = favorited_filter if not filter_expression else filter_expression & favorited_filter
    
    # Query the database
    try:
        if filter_expression:
            response = article_table.scan(
                FilterExpression=filter_expression,
                Limit=limit
            )
        else:
            response = article_table.scan(Limit=limit)
        
        articles = response.get('Items', [])
        
        # Apply offset manually (DynamoDB doesn't have native offset)
        articles = articles[offset:offset+limit] if offset < len(articles) else []
        
        # Format the articles
        formatted_articles = [format_article_response(article, user_profile) for article in articles]
        
        # Get total count (for pagination)
        # Note: this is inefficient for large tables
        count = len(articles)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'articles': formatted_articles,
                'articlesCount': count
            })
        }
    except Exception as e:
        print(f"Error getting articles: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'errors': {'body': ['An error occurred while retrieving articles.']}})
        }


def handle_get_article(event, user_profile=None):
    """Handle retrieving a single article by slug."""
    path_params = event.get('pathParameters', {}) or {}
    slug = path_params.get('slug')
    
    if not slug:
        return {
            'statusCode': 400,
            'body': json.dumps({'errors': {'body': ['Article slug is required']}})
        }
    
    try:
        response = article_table.get_item(Key={'slug': slug})
        article = response.get('Item')
        
        if not article:
            return {
                'statusCode': 404,
                'body': json.dumps({'errors': {'body': ['Article not found']}})
            }
        
        formatted_article = format_article_response(article, user_profile)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'article': formatted_article})
        }
    except Exception as e:
        print(f"Error getting article: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'errors': {'body': ['An error occurred while retrieving the article.']}})
        }


def handle_create_article(event, user_profile):
    """Handle creating a new article."""
    if not user_profile:
        return {
            'statusCode': 401,
            'body': json.dumps({'errors': {'body': ['Authorization required']}})
        }
    
    try:
        # Parse the request body
        body = json.loads(event.get('body', '{}'))
        article_data = body.get('article', {})
        
        title = article_data.get('title')
        description = article_data.get('description', '')
        body_content = article_data.get('body', '')
        tag_list = article_data.get('tagList', [])
        
        if not title:
            return {
                'statusCode': 400,
                'body': json.dumps({'errors': {'title': ['Title is required']}})
            }
        
        # Generate slug from title
        slug = generate_slug(title)
        
        # Create timestamp
        timestamp = datetime.utcnow().isoformat()
        
        # Create the article
        article = {
            'slug': slug,
            'title': title,
            'description': description,
            'body': body_content,
            'author_id': user_profile.get('user_id'),
            'tag_list': tag_list,
            'created_at': timestamp,
            'updated_at': timestamp,
            'favorites_count': 0
        }
        
        # Save the article to DynamoDB
        article_table.put_item(Item=article)
        
        # Save tags
        for tag in tag_list:
            tag_item = {
                'tag': tag,
                'created_at': timestamp,
                'updated_at': timestamp
            }
            tag_table.put_item(Item=tag_item)
        
        # Format the response
        formatted_article = format_article_response(article, user_profile)
        
        return {
            'statusCode': 201,
            'body': json.dumps({'article': formatted_article})
        }
    except Exception as e:
        print(f"Error creating article: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'errors': {'body': ['An error occurred while creating the article.']}})
        }


def handle_update_article(event, user_profile):
    """Handle updating an existing article."""
    if not user_profile:
        return {
            'statusCode': 401,
            'body': json.dumps({'errors': {'body': ['Authorization required']}})
        }
    
    path_params = event.get('pathParameters', {}) or {}
    slug = path_params.get('slug')
    
    if not slug:
        return {
            'statusCode': 400,
            'body': json.dumps({'errors': {'body': ['Article slug is required']}})
        }
    
    try:
        # Get the existing article
        response = article_table.get_item(Key={'slug': slug})
        article = response.get('Item')
        
        if not article:
            return {
                'statusCode': 404,
                'body': json.dumps({'errors': {'body': ['Article not found']}})
            }
        
        # Check if the user is the author
        if article.get('author_id') != user_profile.get('user_id'):
            return {
                'statusCode': 403,
                'body': json.dumps({'errors': {'body': ['You are not authorized to update this article']}})
            }
        
        # Parse the request body
        body = json.loads(event.get('body', '{}'))
        article_data = body.get('article', {})
        
        # Update fields
        if 'title' in article_data:
            article['title'] = article_data['title']
            # If title changes, generate new slug
            article['slug'] = generate_slug(article_data['title'])
            
        if 'description' in article_data:
            article['description'] = article_data['description']
            
        if 'body' in article_data:
            article['body'] = article_data['body']
        
        if 'tagList' in article_data:
            article['tag_list'] = article_data['tagList']
            
            # Save any new tags
            timestamp = datetime.utcnow().isoformat()
            for tag in article_data['tagList']:
                tag_item = {
                    'tag': tag,
                    'created_at': timestamp,
                    'updated_at': timestamp
                }
                tag_table.put_item(Item=tag_item)
        
        # Update timestamp
        article['updated_at'] = datetime.utcnow().isoformat()
        
        # Save the updated article
        article_table.put_item(Item=article)
        
        # Format the response
        formatted_article = format_article_response(article, user_profile)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'article': formatted_article})
        }
    except Exception as e:
        print(f"Error updating article: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'errors': {'body': ['An error occurred while updating the article.']}})
        }


def handle_delete_article(event, user_profile):
    """Handle deleting an article."""
    if not user_profile:
        return {
            'statusCode': 401,
            'body': json.dumps({'errors': {'body': ['Authorization required']}})
        }
    
    path_params = event.get('pathParameters', {}) or {}
    slug = path_params.get('slug')
    
    if not slug:
        return {
            'statusCode': 400,
            'body': json.dumps({'errors': {'body': ['Article slug is required']}})
        }
    
    try:
        # Get the existing article
        response = article_table.get_item(Key={'slug': slug})
        article = response.get('Item')
        
        if not article:
            return {
                'statusCode': 404,
                'body': json.dumps({'errors': {'body': ['Article not found']}})
            }
        
        # Check if the user is the author
        if article.get('author_id') != user_profile.get('user_id'):
            return {
                'statusCode': 403,
                'body': json.dumps({'errors': {'body': ['You are not authorized to delete this article']}})
            }
        
        # Delete the article
        article_table.delete_item(Key={'slug': slug})
        
        # Delete associated comments (in a real implementation, you might want to batch this)
        try:
            comment_response = comment_table.scan(
                FilterExpression=Attr('article_slug').eq(slug)
            )
            for comment in comment_response.get('Items', []):
                comment_table.delete_item(Key={'id': comment['id']})
        except Exception as e:
            print(f"Error deleting comments: {str(e)}")
        
        return {
            'statusCode': 204,
            'body': ''
        }
    except Exception as e:
        print(f"Error deleting article: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'errors': {'body': ['An error occurred while deleting the article.']}})
        }


def handle_favorite_article(event, user_profile, is_favorite=True):
    """Handle favoriting or unfavoriting an article."""
    if not user_profile:
        return {
            'statusCode': 401,
            'body': json.dumps({'errors': {'body': ['Authorization required']}})
        }
    
    path_params = event.get('pathParameters', {}) or {}
    slug = path_params.get('slug')
    
    if not slug:
        return {
            'statusCode': 400,
            'body': json.dumps({'errors': {'body': ['Article slug is required']}})
        }
    
    try:
        # Get the existing article
        response = article_table.get_item(Key={'slug': slug})
        article = response.get('Item')
        
        if not article:
            return {
                'statusCode': 404,
                'body': json.dumps({'errors': {'body': ['Article not found']}})
            }
        
        # Update the user's favorites list
        if 'favorites' not in user_profile:
            user_profile['favorites'] = []
        
        # Add to favorites
        if is_favorite and slug not in user_profile['favorites']:
            user_profile['favorites'].append(slug)
            article['favorites_count'] = article.get('favorites_count', 0) + 1
        # Remove from favorites
        elif not is_favorite and slug in user_profile['favorites']:
            user_profile['favorites'].remove(slug)
            article['favorites_count'] = max(0, article.get('favorites_count', 0) - 1)
        
        # Update the user profile
        profile_table.update_item(
            Key={'user_id': user_profile['user_id']},
            UpdateExpression="set favorites=:f",
            ExpressionAttributeValues={':f': user_profile['favorites']}
        )
        
        # Update the article
        article_table.update_item(
            Key={'slug': slug},
            UpdateExpression="set favorites_count=:c",
            ExpressionAttributeValues={':c': article['favorites_count']}
        )
        
        # Format the response
        formatted_article = format_article_response(article, user_profile)
        
        return {
            'statusCode': 200,
            'body': json.dumps({'article': formatted_article})
        }
    except Exception as e:
        print(f"Error favoriting article: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'errors': {'body': ['An error occurred while favoriting the article.']}})
        }


def handle_feed_articles(event, user_profile):
    """Handle retrieving articles from followed users."""
    if not user_profile:
        return {
            'statusCode': 401,
            'body': json.dumps({'errors': {'body': ['Authorization required']}})
        }
    
    params = event.get('queryStringParameters', {}) or {}
    
    # Parse pagination parameters
    try:
        limit = int(params.get('limit', DEFAULT_LIMIT))
        offset = int(params.get('offset', DEFAULT_OFFSET))
    except ValueError:
        limit = DEFAULT_LIMIT
        offset = DEFAULT_OFFSET
    
    # Get user's follows
    following = user_profile.get('following', [])
    
    if not following:
        return {
            'statusCode': 200,
            'body': json.dumps({
                'articles': [],
                'articlesCount': 0
            })
        }
    
    try:
        # Scan for articles from followed users
        # Note: In a production environment with large datasets, this should be done
        # with a GSI on author_id or another more efficient approach
        articles = []
        for author_id in following:
            response = article_table.scan(
                FilterExpression=Attr('author_id').eq(author_id)
            )
            articles.extend(response.get('Items', []))
        
        # Sort by creation date (newest first)
        articles.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Apply pagination
        paginated_articles = articles[offset:offset+limit] if offset < len(articles) else []
        
        # Format the articles
        formatted_articles = [format_article_response(article, user_profile) for article in paginated_articles]
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'articles': formatted_articles,
                'articlesCount': len(articles)
            })
        }
    except Exception as e:
        print(f"Error getting feed: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'errors': {'body': ['An error occurred while retrieving the feed.']}})
        }


def handle_get_tags(event):
    """Handle retrieving all tags."""
    try:
        response = tag_table.scan()
        tags = [item['tag'] for item in response.get('Items', [])]
        
        return {
            'statusCode': 200,
            'body': json.dumps({'tags': tags})
        }
    except Exception as e:
        print(f"Error getting tags: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'errors': {'body': ['An error occurred while retrieving tags.']}})
        }


def handle_create_comment(event, user_profile):
    """Handle creating a comment for an article."""
    if not user_profile:
        return {
            'statusCode': 401,
            'body': json.dumps({'errors': {'body': ['Authorization required']}})
        }
    
    path_params = event.get('pathParameters', {}) or {}
    article_slug = path_params.get('slug')
    
    if not article_slug:
        return {
            'statusCode': 400,
            'body': json.dumps({'errors': {'body': ['Article slug is required']}})
        }
    
    try:
        # Get the article
        response = article_table.get_item(Key={'slug': article_slug})
        article = response.get('Item')
        
        if not article:
            return {
                'statusCode': 404,
                'body': json.dumps({'errors': {'body': ['Article not found']}})
            }
        
        # Parse the request body
        body = json.loads(event.get('body', '{}'))
        comment_data = body.get('comment', {})
        
        comment_body = comment_data.get('body')
        
        if not comment_body:
            return {
                'statusCode': 400,
                'body': json.dumps({'errors': {'body': ['Comment body is required']}})
            }
        
        # Create timestamp
        timestamp = datetime.utcnow().isoformat()
        
        # Create the comment
        comment_id = str(uuid.uuid4())
        comment = {
            'id': comment_id,
            'body': comment_body,
            'article_slug': article_slug,
            'author_id': user_profile.get('user_id'),
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        # Save the comment to DynamoDB
        comment_table.put_item(Item=comment)
        
        # Format the response
        author_data = {
            'username': user_profile.get('username', ''),
            'bio': user_profile.get('bio', ''),
            'image': user_profile.get('image', ''),
            'following': False  # User can't follow themselves
        }
        
        formatted_comment = {
            'id': comment_id,
            'body': comment_body,
            'createdAt': timestamp,
            'updatedAt': timestamp,
            'author': author_data
        }
        
        return {
            'statusCode': 201,
            'body': json.dumps({'comment': formatted_comment})
        }
    except Exception as e:
        print(f"Error creating comment: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'errors': {'body': ['An error occurred while creating the comment.']}})
        }


def handle_get_comments(event, user_profile=None):
    """Handle retrieving comments for an article."""
    path_params = event.get('pathParameters', {}) or {}
    article_slug = path_params.get('slug')
    
    if not article_slug:
        return {
            'statusCode': 400,
            'body': json.dumps({'errors': {'body': ['Article slug is required']}})
        }
    
    try:
        # Get the article
        article_response = article_table.get_item(Key={'slug': article_slug})
        article = article_response.get('Item')
        
        if not article:
            return {
                'statusCode': 404,
                'body': json.dumps({'errors': {'body': ['Article not found']}})
            }
        
        # Get comments for the article
        comment_response = comment_table.scan(
            FilterExpression=Attr('article_slug').eq(article_slug)
        )
        comments = comment_response.get('Items', [])
        
        # Format the comments
        formatted_comments = []
        for comment in comments:
            # Get author profile
            author_id = comment.get('author_id')
            author_response = profile_table.get_item(Key={'user_id': author_id})
            author = author_response.get('Item', {})
            
            following = False
            if user_profile and 'following' in user_profile:
                following = author_id in user_profile.get('following', [])
            
            author_data = {
                'username': author.get('username', ''),
                'bio': author.get('bio', ''),
                'image': author.get('image', ''),
                'following': following
            }
            
            formatted_comment = {
                'id': comment.get('id'),
                'body': comment.get('body', ''),
                'createdAt': comment.get('created_at', ''),
                'updatedAt': comment.get('updated_at', ''),
                'author': author_data
            }
            
            formatted_comments.append(formatted_comment)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'comments': formatted_comments
            })
        }
    except Exception as e:
        print(f"Error getting comments: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'errors': {'body': ['An error occurred while retrieving comments.']}})
        }


def handle_delete_comment(event, user_profile):
    """Handle deleting a comment."""
    if not user_profile:
        return {
            'statusCode': 401,
            'body': json.dumps({'errors': {'body': ['Authorization required']}})
        }
    
    path_params = event.get('pathParameters', {}) or {}
    article_slug = path_params.get('slug')
    comment_id = path_params.get('id')
    
    if not article_slug or not comment_id:
        return {
            'statusCode': 400,
            'body': json.dumps({'errors': {'body': ['Article slug and comment ID are required']}})
        }
    
    try:
        # Get the comment
        comment_response = comment_table.get_item(Key={'id': comment_id})
        comment = comment_response.get('Item')
        
        if not comment:
            return {
                'statusCode': 404,
                'body': json.dumps({'errors': {'body': ['Comment not found']}})
            }
        
        # Check if the user is authorized (author of the comment)
        if comment.get('author_id') != user_profile.get('user_id'):
            return {
                'statusCode': 403,
                'body': json.dumps({'errors': {'body': ['You are not authorized to delete this comment']}})
            }
        
        # Delete the comment
        comment_table.delete_item(Key={'id': comment_id})
        
        return {
            'statusCode': 204,
            'body': ''
        }
    except Exception as e:
        print(f"Error deleting comment: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'errors': {'body': ['An error occurred while deleting the comment.']}})
        }


def lambda_handler(event, context):
    """Main handler function for AWS Lambda."""
    # Extract HTTP method and path
    method = event.get('httpMethod', '')
    path = event.get('path', '')
    resource = event.get('resource', '')
    
    # Get user profile from token
    user_profile = get_user_from_token(event.get('headers', {}))
    
    # Routing logic
    # Articles endpoints
    if resource == '/api/articles' and method == 'GET':
        return handle_get_articles(event, user_profile)
    elif resource == '/api/articles' and method == 'POST':
        return handle_create_article(event, user_profile)
    elif resource == '/api/articles/{slug}' and method == 'GET':
        return handle_get_article(event, user_profile)
    elif resource == '/api/articles/{slug}' and method == 'PUT':
        return handle_update_article(event, user_profile)
    elif resource == '/api/articles/{slug}' and method == 'DELETE':
        return handle_delete_article(event, user_profile)
    
    # Article feed
    elif resource == '/api/articles/feed' and method == 'GET':
        return handle_feed_articles(event, user_profile)
    
    # Article favorites
    elif resource == '/api/articles/{slug}/favorite' and method == 'POST':
        return handle_favorite_article(event, user_profile, True)
    elif resource == '/api/articles/{slug}/favorite' and method == 'DELETE':
        return handle_favorite_article(event, user_profile, False)
    
    # Comments
    elif resource == '/api/articles/{slug}/comments' and method == 'GET':
        return handle_get_comments(event, user_profile)
    elif resource == '/api/articles/{slug}/comments' and method == 'POST':
        return handle_create_comment(event, user_profile)
    elif resource == '/api/articles/{slug}/comments/{id}' and method == 'DELETE':
        return handle_delete_comment(event, user_profile)
    
    # Tags
    elif resource == '/api/tags' and method == 'GET':
        return handle_get_tags(event)
    
    # Default: Not found
    else:
        return {
            'statusCode': 404,
            'body': json.dumps({'errors': {'body': ['Endpoint not found']}})
        }