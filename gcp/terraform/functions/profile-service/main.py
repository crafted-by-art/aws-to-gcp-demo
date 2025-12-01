import json
import os
import jwt
from datetime import datetime
from botocore.exceptions import ClientError

# Initialize DynamoDB client
db = firestore.Client()
user_table = dynamodb.Table(os.environ.get('USER_TABLE', 'Users'))
profile_table = dynamodb.Table(os.environ.get('PROFILE_TABLE', 'Profiles'))
follow_table = dynamodb.Table(os.environ.get('FOLLOW_TABLE', 'Follows'))

# JWT Secret key
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'default-secret-key')

# Default profile image
DEFAULT_PROFILE_IMAGE = 'https://static.productionready.io/images/smiley-cyrus.jpg'

class ProfileNotFound(Exception):
    pass

class AuthenticationError(Exception):
    pass

def get_current_user_from_token(token):
    """Extract user information from JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        user_id = payload['id']
        
        # Get user from DynamoDB
        response = user_table.get_item(Key={'id': user_id})
        if 'Item' not in response:
            raise AuthenticationError("User not found")
        
        return response['Item']
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")
    except Exception as e:
        raise AuthenticationError(str(e))

def get_profile(username):
    """Retrieve profile by username"""
    try:
        # First get user ID by username
        response = user_table.scan(
            FilterExpression="username = :username",
            ExpressionAttributeValues={":username": username}
        )
        
        if not response['Items']:
            raise ProfileNotFound("Profile not found")
            
        user = response['Items'][0]
        
        # Then get the profile
        profile_response = profile_table.get_item(Key={'user_id': user['id']})
        
        if 'Item' not in profile_response:
            # Create default profile if not exists
            profile = {
                'user_id': user['id'],
                'username': user['username'],
                'bio': '',
                'image': DEFAULT_PROFILE_IMAGE,
            }
        else:
            profile = profile_response['Item']
            if not profile.get('image'):
                profile['image'] = DEFAULT_PROFILE_IMAGE
        
        return profile
    except ProfileNotFound:
        raise
    except Exception as e:
        raise Exception(f"Error retrieving profile: {str(e)}")

def is_following(follower_id, followee_id):
    """Check if user is following another user"""
    try:
        response = follow_table.get_item(
            Key={
                'follower_id': follower_id,
                'followee_id': followee_id
            }
        )
        return 'Item' in response
    except Exception:
        return False

def follow_profile(follower_id, followee_id):
    """Follow a profile"""
    if follower_id == followee_id:
        raise Exception("You cannot follow yourself")
        
    try:
        follow_table.put_item(
            Item={
                'follower_id': follower_id,
                'followee_id': followee_id,
                'created_at': datetime.now().isoformat()
            }
        )
        return True
    except Exception as e:
        raise Exception(f"Error following profile: {str(e)}")

def unfollow_profile(follower_id, followee_id):
    """Unfollow a profile"""
    try:
        follow_table.delete_item(
            Key={
                'follower_id': follower_id,
                'followee_id': followee_id
            }
        )
        return True
    except Exception as e:
        raise Exception(f"Error unfollowing profile: {str(e)}")

def format_response(status_code, body):
    """Format API Gateway response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization'
        },
        'body': json.dumps(body)
    }

def get_profile_response(profile, current_user_id=None):
    """Format profile response"""
    following = False
    if current_user_id:
        following = is_following(current_user_id, profile['user_id'])
    
    return {
        "profile": {
            "username": profile["username"],
            "bio": profile.get("bio", ""),
            "image": profile.get("image", DEFAULT_PROFILE_IMAGE),
            "following": following
        }
    }

@functions_framework.http
def profile_service(request: Request):
    """
    Main Lambda handler function for profile service
    - GET /api/profiles/{username}: Get user profile
    - POST /api/profiles/{username}/follow: Follow user
    - DELETE /api/profiles/{username}/follow: Unfollow user
    """
    try:
        # Handle OPTIONS request for CORS
        if event['httpMethod'] == 'OPTIONS':
            return format_response(200, {})
        
        # Extract path parameters
        path = event['path']
        http_method = event['httpMethod']
        path_params = event.get('pathParameters', {}) or {}
        username = path_params.get('username')
        
        # Check if this is a follow/unfollow request
        is_follow_request = '/follow' in path
        
        # Handle GET request - Get Profile
        if http_method == 'GET' and not is_follow_request:
            if not username:
                return format_response(400, {"errors": {"body": ["Username is required"]}})
            
            # Check if authenticated
            current_user = None
            if 'Authorization' in event.get('headers', {}):
                try:
                    token = event['headers']['Authorization'].split(' ')[1]
                    current_user = get_current_user_from_token(token)
                except (AuthenticationError, IndexError):
                    # Continue without authenticated user
                    pass
            
            profile = get_profile(username)
            response = get_profile_response(
                profile, 
                current_user['id'] if current_user else None
            )
            
            return format_response(200, response)
        
        # Handle follow/unfollow operations
        elif is_follow_request:
            # These operations require authentication
            if 'Authorization' not in event.get('headers', {}):
                return format_response(401, {"errors": {"body": ["Authentication required"]}})
            
            try:
                token = event['headers']['Authorization'].split(' ')[1]
                current_user = get_current_user_from_token(token)
            except (AuthenticationError, IndexError) as e:
                return format_response(401, {"errors": {"body": [str(e)]}})
            
            if not username:
                return format_response(400, {"errors": {"body": ["Username is required"]}})
            
            # Get the profile to follow/unfollow
            try:
                profile = get_profile(username)
            except ProfileNotFound:
                return format_response(404, {"errors": {"body": ["Profile not found"]}})
            
            # Follow profile
            if http_method == 'POST':
                try:
                    follow_profile(current_user['id'], profile['user_id'])
                    response = get_profile_response(profile, current_user['id'])
                    return format_response(201, response)
                except Exception as e:
                    return format_response(400, {"errors": {"body": [str(e)]}})
            
            # Unfollow profile
            elif http_method == 'DELETE':
                try:
                    unfollow_profile(current_user['id'], profile['user_id'])
                    response = get_profile_response(profile, current_user['id'])
                    return format_response(200, response)
                except Exception as e:
                    return format_response(400, {"errors": {"body": [str(e)]}})
        
        # Handle unsupported operations
        return format_response(404, {"errors": {"body": ["Endpoint not found"]}})
        
    except ProfileNotFound:
        return format_response(404, {"errors": {"body": ["Profile not found"]}})
    except AuthenticationError as e:
        return format_response(401, {"errors": {"body": [str(e)]}})
    except Exception as e:
        return format_response(500, {"errors": {"body": [f"Server error: {str(e)}"]}})