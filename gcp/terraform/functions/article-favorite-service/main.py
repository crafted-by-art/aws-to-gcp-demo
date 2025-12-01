import json
import os
import uuid
import time
import jwt
from decimal import Decimal

# Initialize DynamoDB client
db = firestore.Client()
users_table = dynamodb.Table(os.environ.get('USERS_TABLE', 'Users'))
articles_table = dynamodb.Table(os.environ.get('ARTICLES_TABLE', 'Articles'))
favorites_table = dynamodb.Table(os.environ.get('FAVORITES_TABLE', 'ArticleFavorites'))

# JWT configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'default-secret-key')
JWT_ALGORITHM = 'HS256'

class AuthError(Exception):
    def __init__(self, message="Authentication failed"):
        self.message = message
        super().__init__(self.message)

class NotFoundError(Exception):
    def __init__(self, message="Resource not found"):
        self.message = message
        super().__init__(self.message)

def verify_token(token):
    """Verify the JWT token and return the user information"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token expired")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token")

def get_token_from_header(event):
    """Extract the token from the Authorization header"""
    headers = event.get('headers', {})
    auth_header = headers.get('Authorization') or headers.get('authorization')
    
    if not auth_header:
        raise AuthError("No authorization header provided")
        
    if not auth_header.startswith('Token '):
        raise AuthError("Invalid authorization format")
        
    token = auth_header.split(' ')[1]
    return token

def get_user_profile(username):
    """Get user profile from the database"""
    response = users_table.query(
        KeyConditionExpression=Key('username').eq(username)
    )
    items = response.get('Items', [])
    if not items:
        raise NotFoundError(f"User profile not found for {username}")
    return items[0]

def get_article(slug):
    """Get article from the database"""
    response = articles_table.query(
        KeyConditionExpression=Key('slug').eq(slug)
    )
    items = response.get('Items', [])
    if not items:
        raise NotFoundError(f"Article with slug '{slug}' not found")
    return items[0]

def has_favorited(username, article_slug):
    """Check if the user has favorited the article"""
    response = favorites_table.query(
        KeyConditionExpression=Key('username').eq(username) & Key('article_slug').eq(article_slug)
    )
    return len(response.get('Items', [])) > 0

def get_favorites_count(article_slug):
    """Get the number of favorites for an article"""
    response = favorites_table.query(
        IndexName='article_slug-index',
        KeyConditionExpression=Key('article_slug').eq(article_slug)
    )
    return len(response.get('Items', []))

def favorite_article(username, article_slug):
    """Add an article to user's favorites"""
    if has_favorited(username, article_slug):
        # Already favorited, nothing to do
        return
    
    # Add to favorites
    favorites_table.put_item(
        Item={
            'username': username,
            'article_slug': article_slug,
            'created_at': int(time.time())
        }
    )

def unfavorite_article(username, article_slug):
    """Remove an article from user's favorites"""
    if not has_favorited(username, article_slug):
        # Not favorited, nothing to do
        return
    
    # Remove from favorites
    favorites_table.delete_item(
        Key={
            'username': username,
            'article_slug': article_slug
        }
    )

def format_article_response(article, username):
    """Format the article response according to the API requirements"""
    # Get the author profile
    author_username = article.get('author_username')
    author = get_user_profile(author_username)
    
    # Format the response
    is_favorited = has_favorited(username, article['slug'])
    favorites_count = get_favorites_count(article['slug'])
    
    created_at = article.get('created_at', '')
    updated_at = article.get('updated_at', '')
    
    # Format the tags (if any)
    tag_list = article.get('tags', [])
    
    return {
        'article': {
            'slug': article['slug'],
            'title': article['title'],
            'description': article['description'],
            'body': article['body'],
            'tagList': tag_list,
            'createdAt': created_at,
            'updatedAt': updated_at,
            'favorited': is_favorited,
            'favoritesCount': favorites_count,
            'author': {
                'username': author_username,
                'bio': author.get('bio', ''),
                'image': author.get('image', ''),
                'following': False  # We would need to implement this separately
            }
        }
    }

@functions_framework.http
def article_favorite_service(request: Request):
    # Log the event for debugging purposes
    print(f"Event: {json.dumps(event)}")
    
    try:
        # Extract HTTP method and path parameters
        http_method = event['httpMethod']
        path_parameters = event.get('pathParameters', {})
        slug = path_parameters.get('slug')
        
        if not slug:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'errors': {'slug': ['Slug parameter is required']}})
            }
        
        # Verify the token and get user info
        token = get_token_from_header(event)
        payload = verify_token(token)
        username = payload.get('username')
        
        # Get the article
        try:
            article = get_article(slug)
        except NotFoundError as e:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'errors': {'article': [str(e)]}})
            }
        
        # Handle the favorite/unfavorite action based on HTTP method
        if http_method == 'POST':
            # Favorite an article
            favorite_article(username, slug)
            response_data = format_article_response(article, username)
            status_code = 201
        elif http_method == 'DELETE':
            # Unfavorite an article
            unfavorite_article(username, slug)
            response_data = format_article_response(article, username)
            status_code = 200
        else:
            return {
                'statusCode': 405,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'errors': {'method': ['Method not allowed']}})
            }
        
        return {
            'statusCode': status_code,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps(response_data, default=str)
        }
    
    except AuthError as e:
        return {
            'statusCode': 401,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'errors': {'authentication': [str(e)]}})
        }
    except NotFoundError as e:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'errors': {'resource': [str(e)]}})
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'errors': {'server': ['An internal server error occurred']}})
        }