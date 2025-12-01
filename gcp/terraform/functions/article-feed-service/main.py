"""
Article Feed Service - GCP Cloud Function
Provides personalized article feed for authenticated users based on who they follow
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from flask import Request
import functions_framework
from google.cloud import firestore
import jwt

# Initialize Firestore client
db = firestore.Client()

# Collection names
ARTICLES_COLLECTION = 'articles'
PROFILES_COLLECTION = 'profiles'
USERS_COLLECTION = 'users'

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'default-secret-key')

# Pagination defaults
DEFAULT_LIMIT = 20
DEFAULT_OFFSET = 0


def extract_token(headers: Dict[str, str]) -> Optional[str]:
    """Extract JWT token from Authorization header"""
    auth_header = headers.get('Authorization', '')
    if not auth_header:
        return None
    
    # Remove 'Token ' prefix if present
    if auth_header.startswith('Token '):
        return auth_header[6:]
    
    return auth_header


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        print("Token has expired")
        return None
    except jwt.InvalidTokenError:
        print("Invalid token")
        return None
    except Exception as e:
        print(f"Token decode error: {str(e)}")
        return None


def get_user_from_token(headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
    """Authenticate user from JWT token and return user profile"""
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
        # Get user profile from Firestore
        profile_ref = db.collection(PROFILES_COLLECTION).document(user_id)
        profile_doc = profile_ref.get()
        
        if not profile_doc.exists:
            return None
        
        profile = profile_doc.to_dict()
        profile['user_id'] = user_id
        return profile
        
    except Exception as e:
        print(f"Error getting user profile: {str(e)}")
        return None


def get_profile_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get profile by username"""
    try:
        profiles_ref = db.collection(PROFILES_COLLECTION)
        query = profiles_ref.where('username', '==', username).limit(1)
        docs = list(query.stream())
        
        if not docs:
            return None
        
        profile = docs[0].to_dict()
        profile['user_id'] = docs[0].id
        return profile
        
    except Exception as e:
        print(f"Error getting profile by username: {str(e)}")
        return None


def get_articles_by_authors(author_ids: List[str], limit: int = 20, offset: int = 0) -> Dict[str, Any]:
    """Get articles written by the list of authors"""
    articles = []
    
    try:
        articles_ref = db.collection(ARTICLES_COLLECTION)
        
        # Firestore 'in' operator supports max 10 values
        # If more authors, batch the queries
        for i in range(0, len(author_ids), 10):
            batch = author_ids[i:i+10]
            query = articles_ref.where('author_id', 'in', batch)
            
            for doc in query.stream():
                article = doc.to_dict()
                article['slug'] = doc.id
                articles.append(article)
        
        # Sort articles by created_at (most recent first)
        articles.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Get total count before pagination
        total_count = len(articles)
        
        # Apply pagination
        paginated_articles = articles[offset:offset+limit]
        
        return {
            'articles': paginated_articles,
            'articlesCount': total_count
        }
    except Exception as e:
        print(f"Error getting articles: {str(e)}")
        return {'articles': [], 'articlesCount': 0}


def format_article_response(articles: List[Dict[str, Any]], user_profile: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Format articles for API response"""
    formatted_articles = []
    
    for article in articles:
        # Get author profile
        author_profile = {}
        author_id = article.get('author_id')
        
        if author_id:
            try:
                author_ref = db.collection(PROFILES_COLLECTION).document(author_id)
                author_doc = author_ref.get()
                if author_doc.exists:
                    author_profile = author_doc.to_dict()
            except Exception as e:
                print(f"Error getting author profile: {str(e)}")
        
        # Check if user has favorited this article
        favorited = False
        if user_profile and 'favorites' in user_profile:
            favorited = article.get('slug') in user_profile['favorites']
        
        # Check if user follows the author
        following = False
        if user_profile and author_id and 'following' in user_profile:
            following = author_id in user_profile['following']
        
        # Format the article
        formatted_article = {
            'slug': article.get('slug', ''),
            'title': article.get('title', ''),
            'description': article.get('description', ''),
            'body': article.get('body', ''),
            'tagList': article.get('tag_list', []),
            'createdAt': article.get('created_at', ''),
            'updatedAt': article.get('updated_at', ''),
            'favorited': favorited,
            'favoritesCount': article.get('favorites_count', 0),
            'author': {
                'username': author_profile.get('username', ''),
                'bio': author_profile.get('bio', ''),
                'image': author_profile.get('image', ''),
                'following': following
            }
        }
        
        formatted_articles.append(formatted_article)
    
    return formatted_articles


@functions_framework.http
def article_feed_service(request: Request):
    """
    Cloud Function entry point for article feed service
    Provides personalized article feed based on followed users
    """
    # Set CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Content-Type': 'application/json'
    }
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return ('', 204, headers)
    
    try:
        # Only handle GET requests
        if request.method != 'GET':
            return (
                json.dumps({'errors': {'message': 'Method not allowed'}}),
                405,
                headers
            )
        
        # Get Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header:
            return (
                json.dumps({'errors': {'message': 'Authorization required'}}),
                401,
                headers
            )
        
        # Authenticate user
        user_profile = get_user_from_token(request.headers)
        if not user_profile:
            return (
                json.dumps({'errors': {'message': 'Invalid token'}}),
                401,
                headers
            )
        
        # Get pagination parameters
        limit = int(request.args.get('limit', DEFAULT_LIMIT))
        offset = int(request.args.get('offset', DEFAULT_OFFSET))
        
        # Get profiles the user follows
        followed_profiles = user_profile.get('following', [])
        
        # Get articles by followed authors
        if not followed_profiles:
            result = {'articles': [], 'articlesCount': 0}
        else:
            result = get_articles_by_authors(followed_profiles, limit, offset)
        
        # Format response
        formatted_articles = format_article_response(result['articles'], user_profile)
        
        # Return response
        response = {
            'articles': formatted_articles,
            'articlesCount': result['articlesCount']
        }
        
        return (json.dumps(response), 200, headers)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return (
            json.dumps({'errors': {'message': 'Internal server error'}}),
            500,
            headers
        )
