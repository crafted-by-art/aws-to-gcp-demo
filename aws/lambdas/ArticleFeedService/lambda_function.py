import json
import boto3
import os
from decimal import Decimal
from boto3.dynamodb.conditions import Key
import jwt
from datetime import datetime

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table(os.environ.get('USERS_TABLE', 'Users'))
profiles_table = dynamodb.Table(os.environ.get('PROFILES_TABLE', 'Profiles'))
articles_table = dynamodb.Table(os.environ.get('ARTICLES_TABLE', 'Articles'))
follows_table = dynamodb.Table(os.environ.get('FOLLOWS_TABLE', 'Follows'))

# JWT Secret Key - should be stored in AWS Secrets Manager in production
JWT_SECRET = os.environ.get('JWT_SECRET', 'default-secret-key')

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(DecimalEncoder, self).default(obj)

def authenticate_token(token):
    """Validate JWT token and return the user"""
    try:
        # Remove 'Token ' prefix if present
        if token.startswith('Token '):
            token = token[6:]
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user_id = payload['id']
        
        # Get user from DynamoDB
        response = users_table.get_item(Key={'id': user_id})
        
        if 'Item' not in response:
            return None
            
        return response['Item']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return None

def get_user_profile(user_id):
    """Get user profile from DynamoDB"""
    try:
        response = profiles_table.get_item(Key={'user_id': user_id})
        if 'Item' in response:
            return response['Item']
        return None
    except Exception as e:
        print(f"Error getting profile: {str(e)}")
        return None

def get_follows(profile_id):
    """Get the list of profiles that a user follows"""
    try:
        response = follows_table.query(
            KeyConditionExpression=Key('follower_id').eq(profile_id)
        )
        return [item['followed_id'] for item in response.get('Items', [])]
    except Exception as e:
        print(f"Error getting follows: {str(e)}")
        return []

def get_articles_by_authors(author_ids, limit=20, offset=0):
    """Get articles written by the list of authors"""
    articles = []
    
    try:
        # DynamoDB doesn't support direct IN queries, so we need to query for each author
        # In a production system, we might use a GSI or a different data model
        for author_id in author_ids:
            response = articles_table.query(
                IndexName='author_id-index',
                KeyConditionExpression=Key('author_id').eq(author_id)
            )
            
            if 'Items' in response:
                articles.extend(response['Items'])
        
        # Sort articles by created_at (most recent first)
        articles.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Apply pagination
        paginated_articles = articles[offset:offset+limit]
        
        return {
            'articles': paginated_articles,
            'articlesCount': len(articles)
        }
    except Exception as e:
        print(f"Error getting articles: {str(e)}")
        return {'articles': [], 'articlesCount': 0}

def has_favorited(profile_id, article):
    """Check if a profile has favorited an article"""
    try:
        # In a production system, we'd have a separate favorites table or a different approach
        # This is a simplified example
        if 'favorited_by' in article:
            return profile_id in article['favorited_by']
        return False
    except Exception as e:
        print(f"Error checking favorites: {str(e)}")
        return False

def format_article_response(articles, user_profile=None):
    """Format articles for API response"""
    formatted_articles = []
    
    for article in articles:
        # Get author profile
        author_profile = {}
        if 'author_id' in article:
            author_response = profiles_table.get_item(Key={'id': article['author_id']})
            if 'Item' in author_response:
                author_profile = author_response['Item']
        
        # Format the article
        formatted_article = {
            'slug': article.get('slug', ''),
            'title': article.get('title', ''),
            'description': article.get('description', ''),
            'body': article.get('body', ''),
            'tagList': article.get('tags', []),
            'createdAt': article.get('created_at', ''),
            'updatedAt': article.get('updated_at', ''),
            'favorited': False,
            'favoritesCount': len(article.get('favorited_by', [])),
            'author': {
                'username': author_profile.get('username', ''),
                'bio': author_profile.get('bio', ''),
                'image': author_profile.get('image', ''),
                'following': False
            }
        }
        
        # Add favorited and following flags if user is authenticated
        if user_profile:
            formatted_article['favorited'] = has_favorited(user_profile['id'], article)
            formatted_article['author']['following'] = user_profile.get('follows', []).includes(author_profile['id']) if author_profile else False
            
        formatted_articles.append(formatted_article)
    
    return formatted_articles

def lambda_handler(event, context):
    """Lambda function to provide a personalized article feed for authenticated users"""
    try:
        # Parse request
        method = event.get('httpMethod', '')
        
        # Only handle GET requests
        if method != 'GET':
            return {
                'statusCode': 405,
                'body': json.dumps({'errors': {'message': 'Method not allowed'}}),
                'headers': {'Content-Type': 'application/json'}
            }
        
        # Get Authorization header
        headers = event.get('headers', {})
        auth_header = headers.get('Authorization', '')
        
        if not auth_header:
            return {
                'statusCode': 401,
                'body': json.dumps({'errors': {'message': 'Authorization required'}}),
                'headers': {'Content-Type': 'application/json'}
            }
        
        # Authenticate user
        user = authenticate_token(auth_header)
        if not user:
            return {
                'statusCode': 401,
                'body': json.dumps({'errors': {'message': 'Invalid token'}}),
                'headers': {'Content-Type': 'application/json'}
            }
        
        # Get user profile
        profile = get_user_profile(user['id'])
        if not profile:
            return {
                'statusCode': 404,
                'body': json.dumps({'errors': {'message': 'Profile not found'}}),
                'headers': {'Content-Type': 'application/json'}
            }
        
        # Get pagination parameters
        query_params = event.get('queryStringParameters', {}) or {}
        limit = int(query_params.get('limit', 20))
        offset = int(query_params.get('offset', 0))
        
        # Get profiles the user follows
        followed_profiles = get_follows(profile['id'])
        
        # Get articles by followed authors
        if not followed_profiles:
            result = {'articles': [], 'articlesCount': 0}
        else:
            result = get_articles_by_authors(followed_profiles, limit, offset)
        
        # Format response
        formatted_articles = format_article_response(result['articles'], profile)
        
        # Return response
        response = {
            'articles': formatted_articles,
            'articlesCount': result['articlesCount']
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps(response, cls=DecimalEncoder),
            'headers': {'Content-Type': 'application/json'}
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'errors': {'message': 'Internal server error'}}),
            'headers': {'Content-Type': 'application/json'}
        }