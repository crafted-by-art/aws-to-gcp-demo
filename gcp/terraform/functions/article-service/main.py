import json
import os
import time
import uuid
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import jwt
from google.cloud import firestore
import functions_framework
from flask import Request

# Initialize Firestore client
db = firestore.Client()

# Collections
ARTICLES_COLLECTION = 'articles'
TAGS_COLLECTION = 'tags'
PROFILES_COLLECTION = 'profiles'
COMMENTS_COLLECTION = 'comments'

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'secret')
JWT_ALGORITHM = 'HS256'
JWT_EXP_DELTA_SECONDS = 86400  # 24 hours

# Pagination defaults
DEFAULT_LIMIT = 20
DEFAULT_OFFSET = 0


def generate_slug(title: str) -> str:
    """Generate a URL-friendly slug from a title."""
    slug = re.sub(r'[^\w\s-]', '', title.lower())
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    unique_suffix = str(int(time.time()))
    return f"{slug}-{unique_suffix}"


def extract_token(headers: Dict[str, str]) -> Optional[str]:
    """Extract the JWT token from request headers."""
    auth_header = headers.get('Authorization', headers.get('authorization', ''))
    if auth_header.startswith('Token '):
        return auth_header.split(' ')[1]
    return None


def decode_token(token: str) -> Optional[Dict[str, Any]]:
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


def get_user_from_token(headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
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
    
    try:
        profile_ref = db.collection(PROFILES_COLLECTION).document(user_id)
        profile_doc = profile_ref.get()
        
        if profile_doc.exists:
            profile_data = profile_doc.to_dict()
            profile_data['user_id'] = profile_doc.id
            return profile_data
        return None
    except Exception as e:
        print(f"Error getting user profile: {str(e)}")
        return None


def get_profile_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get profile by username from Firestore."""
    try:
        profiles_ref = db.collection(PROFILES_COLLECTION)
        query = profiles_ref.where('username', '==', username).limit(1)
        docs = query.stream()
        
        for doc in docs:
            profile_data = doc.to_dict()
            profile_data['user_id'] = doc.id
            return profile_data
        return None
    except Exception as e:
        print(f"Error getting profile by username: {str(e)}")
        return None


def format_article_response(article: Dict[str, Any], user_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Format article for API response."""
    try:
        author_ref = db.collection(PROFILES_COLLECTION).document(article['author_id'])
        author_doc = author_ref.get()
        author = author_doc.to_dict() if author_doc.exists else {}
    except Exception as e:
        print(f"Error getting author profile: {str(e)}")
        author = {}
    
    author_data = {
        'username': author.get('username', ''),
        'bio': author.get('bio', ''),
        'image': author.get('image', ''),
        'following': False
    }
    
    if user_profile and 'following' in user_profile:
        author_data['following'] = article['author_id'] in user_profile.get('following', [])
    
    tags = article.get('tag_list', [])
    favorited = False
    favorites_count = article.get('favorites_count', 0)
    
    if user_profile and 'favorites' in user_profile:
        favorited = article['slug'] in user_profile.get('favorites', [])
    
    created_at = article.get('created_at', datetime.utcnow().isoformat())
    updated_at = article.get('updated_at', created_at)
    
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


def handle_get_articles(request: Request, user_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Handle listing articles with filtering options."""
    params = request.args
    try:
        limit = int(params.get('limit', DEFAULT_LIMIT))
        offset = int(params.get('offset', DEFAULT_OFFSET))
    except ValueError:
        limit = DEFAULT_LIMIT
        offset = DEFAULT_OFFSET
    articles_ref = db.collection(ARTICLES_COLLECTION)
    query = articles_ref
    author_username = params.get('author')
    if author_username:
        author_profile = get_profile_by_username(author_username)
        if author_profile:
            author_id = author_profile.get('user_id')
            query = query.where('author_id', '==', author_id)
    tag = params.get('tag')
    if tag:
        query = query.where('tag_list', 'array_contains', tag)
    favorited_by = params.get('favorited')
    favorited_slugs = []
    if favorited_by:
        favorited_profile = get_profile_by_username(favorited_by)
        if favorited_profile and 'favorites' in favorited_profile:
            favorited_slugs = favorited_profile.get('favorites', [])
    try:
        docs = query.stream()
        articles = []
        for doc in docs:
            article_data = doc.to_dict()
            article_data['slug'] = doc.id
            if favorited_slugs and article_data['slug'] not in favorited_slugs:
                continue
            articles.append(article_data)
        articles.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        total_count = len(articles)
        articles = articles[offset:offset+limit] if offset < len(articles) else []
        formatted_articles = [format_article_response(article, user_profile) for article in articles]
        return {'statusCode': 200, 'body': json.dumps({'articles': formatted_articles, 'articlesCount': total_count})}
    except Exception as e:
        print(f"Error getting articles: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'errors': {'body': ['An error occurred while retrieving articles.']}})}


def handle_get_article(slug: str, user_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Handle retrieving a single article by slug."""
    if not slug:
        return {'statusCode': 400, 'body': json.dumps({'errors': {'body': ['Article slug is required']}})}
    try:
        article_ref = db.collection(ARTICLES_COLLECTION).document(slug)
        article_doc = article_ref.get()
        if not article_doc.exists:
            return {'statusCode': 404, 'body': json.dumps({'errors': {'body': ['Article not found']}})}
        article = article_doc.to_dict()
        article['slug'] = slug
        formatted_article = format_article_response(article, user_profile)
        return {'statusCode': 200, 'body': json.dumps({'article': formatted_article})}
    except Exception as e:
        print(f"Error getting article: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'errors': {'body': ['An error occurred while retrieving the article.']}})}


def handle_create_article(request: Request, user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Handle creating a new article."""
    if not user_profile:
        return {'statusCode': 401, 'body': json.dumps({'errors': {'body': ['Authorization required']}})}
    try:
        body = request.get_json()
        article_data = body.get('article', {})
        title = article_data.get('title')
        description = article_data.get('description', '')
        body_content = article_data.get('body', '')
        tag_list = article_data.get('tagList', [])
        if not title:
            return {'statusCode': 400, 'body': json.dumps({'errors': {'title': ['Title is required']}})}
        slug = generate_slug(title)
        timestamp = datetime.utcnow().isoformat()
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
        db.collection(ARTICLES_COLLECTION).document(slug).set(article)
        for tag in tag_list:
            tag_item = {'tag': tag, 'created_at': timestamp, 'updated_at': timestamp}
            db.collection(TAGS_COLLECTION).document(tag).set(tag_item)
        formatted_article = format_article_response(article, user_profile)
        return {'statusCode': 201, 'body': json.dumps({'article': formatted_article})}
    except Exception as e:
        print(f"Error creating article: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'errors': {'body': ['An error occurred while creating the article.']}})}


def handle_update_article(slug: str, request: Request, user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Handle updating an existing article."""
    if not user_profile:
        return {'statusCode': 401, 'body': json.dumps({'errors': {'body': ['Authorization required']}})}
    if not slug:
        return {'statusCode': 400, 'body': json.dumps({'errors': {'body': ['Article slug is required']}})}
    try:
        article_ref = db.collection(ARTICLES_COLLECTION).document(slug)
        article_doc = article_ref.get()
        if not article_doc.exists:
            return {'statusCode': 404, 'body': json.dumps({'errors': {'body': ['Article not found']}})}
        article = article_doc.to_dict()
        article['slug'] = slug
        if article.get('author_id') != user_profile.get('user_id'):
            return {'statusCode': 403, 'body': json.dumps({'errors': {'body': ['You are not authorized to update this article']}})}
        body = request.get_json()
        article_data = body.get('article', {})
        new_slug = slug
        if 'title' in article_data:
            article['title'] = article_data['title']
            new_slug = generate_slug(article_data['title'])
            article['slug'] = new_slug
        if 'description' in article_data:
            article['description'] = article_data['description']
        if 'body' in article_data:
            article['body'] = article_data['body']
        if 'tagList' in article_data:
            article['tag_list'] = article_data['tagList']
            timestamp = datetime.utcnow().isoformat()
            for tag in article_data['tagList']:
                tag_item = {'tag': tag, 'created_at': timestamp, 'updated_at': timestamp}
                db.collection(TAGS_COLLECTION).document(tag).set(tag_item)
        article['updated_at'] = datetime.utcnow().isoformat()
        if new_slug != slug:
            article_ref.delete()
            db.collection(ARTICLES_COLLECTION).document(new_slug).set(article)
        else:
            article_ref.set(article)
        formatted_article = format_article_response(article, user_profile)
        return {'statusCode': 200, 'body': json.dumps({'article': formatted_article})}
    except Exception as e:
        print(f"Error updating article: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'errors': {'body': ['An error occurred while updating the article.']}})}


def handle_delete_article(slug: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Handle deleting an article."""
    if not user_profile:
        return {'statusCode': 401, 'body': json.dumps({'errors': {'body': ['Authorization required']}})}
    if not slug:
        return {'statusCode': 400, 'body': json.dumps({'errors': {'body': ['Article slug is required']}})}
    try:
        article_ref = db.collection(ARTICLES_COLLECTION).document(slug)
        article_doc = article_ref.get()
        if not article_doc.exists:
            return {'statusCode': 404, 'body': json.dumps({'errors': {'body': ['Article not found']}})}
        article = article_doc.to_dict()
        if article.get('author_id') != user_profile.get('user_id'):
            return {'statusCode': 403, 'body': json.dumps({'errors': {'body': ['You are not authorized to delete this article']}})}
        article_ref.delete()
        try:
            comments_ref = db.collection(COMMENTS_COLLECTION)
            comment_query = comments_ref.where('article_slug', '==', slug)
            comments = comment_query.stream()
            for comment_doc in comments:
                comment_doc.reference.delete()
        except Exception as e:
            print(f"Error deleting comments: {str(e)}")
        return {'statusCode': 204, 'body': ''}
    except Exception as e:
        print(f"Error deleting article: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'errors': {'body': ['An error occurred while deleting the article.']}})}


def handle_favorite_article(slug: str, user_profile: Dict[str, Any], is_favorite: bool = True) -> Dict[str, Any]:
    """Handle favoriting or unfavoriting an article."""
    if not user_profile:
        return {'statusCode': 401, 'body': json.dumps({'errors': {'body': ['Authorization required']}})}
    if not slug:
        return {'statusCode': 400, 'body': json.dumps({'errors': {'body': ['Article slug is required']}})}
    try:
        article_ref = db.collection(ARTICLES_COLLECTION).document(slug)
        article_doc = article_ref.get()
        if not article_doc.exists:
            return {'statusCode': 404, 'body': json.dumps({'errors': {'body': ['Article not found']}})}
        article = article_doc.to_dict()
        article['slug'] = slug
        if 'favorites' not in user_profile:
            user_profile['favorites'] = []
        if is_favorite and slug not in user_profile['favorites']:
            user_profile['favorites'].append(slug)
            article['favorites_count'] = article.get('favorites_count', 0) + 1
        elif not is_favorite and slug in user_profile['favorites']:
            user_profile['favorites'].remove(slug)
            article['favorites_count'] = max(0, article.get('favorites_count', 0) - 1)
        profile_ref = db.collection(PROFILES_COLLECTION).document(user_profile['user_id'])
        profile_ref.update({'favorites': user_profile['favorites']})
        article_ref.update({'favorites_count': article['favorites_count']})
        formatted_article = format_article_response(article, user_profile)
        return {'statusCode': 200, 'body': json.dumps({'article': formatted_article})}
    except Exception as e:
        print(f"Error favoriting article: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'errors': {'body': ['An error occurred while favoriting the article.']}})}


def handle_feed_articles(request: Request, user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Handle retrieving articles from followed users."""
    if not user_profile:
        return {'statusCode': 401, 'body': json.dumps({'errors': {'body': ['Authorization required']}})}
    params = request.args
    try:
        limit = int(params.get('limit', DEFAULT_LIMIT))
        offset = int(params.get('offset', DEFAULT_OFFSET))
    except ValueError:
        limit = DEFAULT_LIMIT
        offset = DEFAULT_OFFSET
    following = user_profile.get('following', [])
    if not following:
        return {'statusCode': 200, 'body': json.dumps({'articles': [], 'articlesCount': 0})}
    try:
        articles = []
        for author_id in following:
            query = db.collection(ARTICLES_COLLECTION).where('author_id', '==', author_id)
            docs = query.stream()
            for doc in docs:
                article_data = doc.to_dict()
                article_data['slug'] = doc.id
                articles.append(article_data)
        articles.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        total_count = len(articles)
        paginated_articles = articles[offset:offset+limit] if offset < len(articles) else []
        formatted_articles = [format_article_response(article, user_profile) for article in paginated_articles]
        return {'statusCode': 200, 'body': json.dumps({'articles': formatted_articles, 'articlesCount': total_count})}
    except Exception as e:
        print(f"Error getting feed: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'errors': {'body': ['An error occurred while retrieving the feed.']}})}


def handle_get_tags() -> Dict[str, Any]:
    """Handle retrieving all tags."""
    try:
        tags_ref = db.collection(TAGS_COLLECTION)
        docs = tags_ref.stream()
        tags = [doc.to_dict()['tag'] for doc in docs if 'tag' in doc.to_dict()]
        return {'statusCode': 200, 'body': json.dumps({'tags': tags})}
    except Exception as e:
        print(f"Error getting tags: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'errors': {'body': ['An error occurred while retrieving tags.']}})}


def handle_create_comment(article_slug: str, request: Request, user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Handle creating a comment for an article."""
    if not user_profile:
        return {'statusCode': 401, 'body': json.dumps({'errors': {'body': ['Authorization required']}})}
    if not article_slug:
        return {'statusCode': 400, 'body': json.dumps({'errors': {'body': ['Article slug is required']}})}
    try:
        article_ref = db.collection(ARTICLES_COLLECTION).document(article_slug)
        article_doc = article_ref.get()
        if not article_doc.exists:
            return {'statusCode': 404, 'body': json.dumps({'errors': {'body': ['Article not found']}})}
        body = request.get_json()
        comment_data = body.get('comment', {})
        comment_body = comment_data.get('body')
        if not comment_body:
            return {'statusCode': 400, 'body': json.dumps({'errors': {'body': ['Comment body is required']}})}
        timestamp = datetime.utcnow().isoformat()
        comment_id = str(uuid.uuid4())
        comment = {
            'id': comment_id,
            'body': comment_body,
            'article_slug': article_slug,
            'author_id': user_profile.get('user_id'),
            'created_at': timestamp,
            'updated_at': timestamp
        }
        db.collection(COMMENTS_COLLECTION).document(comment_id).set(comment)
        author_data = {
            'username': user_profile.get('username', ''),
            'bio': user_profile.get('bio', ''),
            'image': user_profile.get('image', ''),
            'following': False
        }
        formatted_comment = {
            'id': comment_id,
            'body': comment_body,
            'createdAt': timestamp,
            'updatedAt': timestamp,
            'author': author_data
        }
        return {'statusCode': 201, 'body': json.dumps({'comment': formatted_comment})}
    except Exception as e:
        print(f"Error creating comment: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'errors': {'body': ['An error occurred while creating the comment.']}})}


def handle_get_comments(article_slug: str, user_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Handle retrieving comments for an article."""
    if not article_slug:
        return {'statusCode': 400, 'body': json.dumps({'errors': {'body': ['Article slug is required']}})}
    try:
        article_ref = db.collection(ARTICLES_COLLECTION).document(article_slug)
        article_doc = article_ref.get()
        if not article_doc.exists:
            return {'statusCode': 404, 'body': json.dumps({'errors': {'body': ['Article not found']}})}
        comments_ref = db.collection(COMMENTS_COLLECTION)
        comment_query = comments_ref.where('article_slug', '==', article_slug)
        comments = comment_query.stream()
        formatted_comments = []
        for comment_doc in comments:
            comment = comment_doc.to_dict()
            author_id = comment.get('author_id')
            author_ref = db.collection(PROFILES_COLLECTION).document(author_id)
            author_doc = author_ref.get()
            author = author_doc.to_dict() if author_doc.exists else {}
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
        return {'statusCode': 200, 'body': json.dumps({'comments': formatted_comments})}
    except Exception as e:
        print(f"Error getting comments: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'errors': {'body': ['An error occurred while retrieving comments.']}})}


def handle_delete_comment(article_slug: str, comment_id: str, user_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Handle deleting a comment."""
    if not user_profile:
        return {'statusCode': 401, 'body': json.dumps({'errors': {'body': ['Authorization required']}})}
    if not article_slug or not comment_id:
        return {'statusCode': 400, 'body': json.dumps({'errors': {'body': ['Article slug and comment ID are required']}})}
    try:
        comment_ref = db.collection(COMMENTS_COLLECTION).document(comment_id)
        comment_doc = comment_ref.get()
        if not comment_doc.exists:
            return {'statusCode': 404, 'body': json.dumps({'errors': {'body': ['Comment not found']}})}
        comment = comment_doc.to_dict()
        if comment.get('author_id') != user_profile.get('user_id'):
            return {'statusCode': 403, 'body': json.dumps({'errors': {'body': ['You are not authorized to delete this comment']}})}
        comment_ref.delete()
        return {'statusCode': 204, 'body': ''}
    except Exception as e:
        print(f"Error deleting comment: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps({'errors': {'body': ['An error occurred while deleting the comment.']}})}


@functions_framework.http
def article_service(request: Request):
    """Main entry point for the article service Cloud Function."""
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
    }
    method = request.method
    path = request.path
    user_profile = get_user_from_token(request.headers)
    path_parts = [p for p in path.split("/") if p]
    try:
        if path.endswith("/articles/feed") and method == "GET":
            result = handle_feed_articles(request, user_profile)
        elif path.endswith("/articles") and method == "GET":
            result = handle_get_articles(request, user_profile)
        elif path.endswith("/articles") and method == "POST":
            result = handle_create_article(request, user_profile)
        elif "/articles/" in path and path.endswith("/favorite") and method == "POST":
            slug = path_parts[path_parts.index("articles") + 1]
            result = handle_favorite_article(slug, user_profile, True)
        elif "/articles/" in path and path.endswith("/favorite") and method == "DELETE":
            slug = path_parts[path_parts.index("articles") + 1]
            result = handle_favorite_article(slug, user_profile, False)
        elif "/articles/" in path and path.endswith("/comments") and method == "GET":
            slug = path_parts[path_parts.index("articles") + 1]
            result = handle_get_comments(slug, user_profile)
        elif "/articles/" in path and path.endswith("/comments") and method == "POST":
            slug = path_parts[path_parts.index("articles") + 1]
            result = handle_create_comment(slug, request, user_profile)
        elif "/articles/" in path and "/comments/" in path and method == "DELETE":
            slug = path_parts[path_parts.index("articles") + 1]
            comment_id = path_parts[path_parts.index("comments") + 1]
            result = handle_delete_comment(slug, comment_id, user_profile)
        elif "/articles/" in path and method == "GET":
            slug = path_parts[path_parts.index("articles") + 1]
            result = handle_get_article(slug, user_profile)
        elif "/articles/" in path and method == "PUT":
            slug = path_parts[path_parts.index("articles") + 1]
            result = handle_update_article(slug, request, user_profile)
        elif "/articles/" in path and method == "DELETE":
            slug = path_parts[path_parts.index("articles") + 1]
            result = handle_delete_article(slug, user_profile)
        elif path.endswith("/tags") and method == "GET":
            result = handle_get_tags()
        else:
            result = {"statusCode": 404, "body": json.dumps({"errors": {"body": ["Endpoint not found"]}})}
        status = result.get("statusCode", 200)
        body = result.get("body", "{}")
        return (body, status, headers)
    except Exception as e:
        print(f"Error in article_service: {str(e)}")
        return (json.dumps({"errors": {"body": [str(e)]}}), 500, headers)
