import json
import os
import datetime
import jwt
import bcrypt
import boto3
from boto3.dynamodb.conditions import Key

# Initialize AWS services
dynamodb = boto3.resource('dynamodb')
users_table = dynamodb.Table(os.environ.get('USERS_TABLE', 'Users'))
profiles_table = dynamodb.Table(os.environ.get('PROFILES_TABLE', 'Profiles'))

# Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key')
JWT_ALGORITHM = 'HS256'
JWT_EXP_DAYS = 60

class ValidationError(Exception):
    """Exception raised for validation errors in input data."""
    pass

def generate_jwt_token(user_id):
    """Generate a JWT token for a user."""
    payload = {
        'id': user_id,
        'exp': int((datetime.datetime.now() + datetime.timedelta(days=JWT_EXP_DAYS)).timestamp())
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def hash_password(password):
    """Hash a password for storing."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user."""
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

def get_user_by_email(email):
    """Retrieve a user by email."""
    response = users_table.query(
        IndexName='EmailIndex',
        KeyConditionExpression=Key('email').eq(email)
    )
    
    items = response.get('Items', [])
    if items:
        return items[0]
    return None

def get_user_by_id(user_id):
    """Retrieve a user by ID."""
    response = users_table.get_item(Key={'id': user_id})
    return response.get('Item')

def get_profile(username):
    """Retrieve a profile by username."""
    response = profiles_table.get_item(Key={'username': username})
    return response.get('Item')

def authenticate(email, password):
    """Authenticate a user by email and password."""
    user = get_user_by_email(email)
    
    if user is None:
        return None
        
    if not verify_password(user['password'], password):
        return None
        
    if not user.get('is_active', True):
        return None
        
    return user

def create_user(username, email, password):
    """Create a new user and associated profile."""
    # Check if user with email already exists
    existing_user = get_user_by_email(email)
    if existing_user:
        raise ValidationError('User with this email already exists')
    
    # Create user
    user_id = str(hash(email + datetime.datetime.now().isoformat()))  # Simple ID generation
    
    user_item = {
        'id': user_id,
        'username': username,
        'email': email,
        'password': hash_password(password),
        'is_active': True,
        'is_staff': False,
        'created_at': datetime.datetime.now().isoformat(),
        'updated_at': datetime.datetime.now().isoformat()
    }
    
    users_table.put_item(Item=user_item)
    
    # Create profile
    profile_item = {
        'id': user_id,
        'username': username,
        'user_id': user_id,
        'bio': '',
        'image': 'https://static.productionready.io/images/smiley-cyrus.jpg',
        'created_at': datetime.datetime.now().isoformat(),
        'updated_at': datetime.datetime.now().isoformat()
    }
    
    profiles_table.put_item(Item=profile_item)
    
    # Return user without password
    user_response = {k: v for k, v in user_item.items() if k != 'password'}
    user_response['token'] = generate_jwt_token(user_id)
    
    return user_response

def update_user(user_id, data):
    """Update user and profile information."""
    user = get_user_by_id(user_id)
    if not user:
        raise ValidationError('User not found')
        
    update_expression_parts = []
    expression_attribute_values = {}
    expression_attribute_names = {}
    
    # Update user attributes
    for key, value in data.items():
        if key in ['username', 'email']:
            update_expression_parts.append(f"#{key} = :{key}")
            expression_attribute_names[f"#{key}"] = key
            expression_attribute_values[f":{key}"] = value
    
    if 'password' in data:
        update_expression_parts.append("#password = :password")
        expression_attribute_names["#password"] = "password"
        expression_attribute_values[":password"] = hash_password(data['password'])
    
    # Always update the updated_at timestamp
    update_expression_parts.append("#updated_at = :updated_at")
    expression_attribute_names["#updated_at"] = "updated_at"
    expression_attribute_values[":updated_at"] = datetime.datetime.now().isoformat()
    
    if update_expression_parts:
        users_table.update_item(
            Key={'id': user_id},
            UpdateExpression="SET " + ", ".join(update_expression_parts),
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values
        )
    
    # Update profile if profile data is provided
    if 'profile' in data and isinstance(data['profile'], dict):
        profile = get_profile(user['username'])
        
        profile_update_parts = []
        profile_values = {}
        profile_names = {}
        
        for key, value in data['profile'].items():
            if key in ['bio', 'image']:
                profile_update_parts.append(f"#{key} = :{key}")
                profile_names[f"#{key}"] = key
                profile_values[f":{key}"] = value
        
        profile_update_parts.append("#updated_at = :updated_at")
        profile_names["#updated_at"] = "updated_at"
        profile_values[":updated_at"] = datetime.datetime.now().isoformat()
        
        if profile_update_parts:
            profiles_table.update_item(
                Key={'username': user['username']},
                UpdateExpression="SET " + ", ".join(profile_update_parts),
                ExpressionAttributeNames=profile_names,
                ExpressionAttributeValues=profile_values
            )
    
    # Get updated user and profile
    updated_user = get_user_by_id(user_id)
    updated_profile = get_profile(updated_user['username'])
    
    # Prepare response
    user_response = {k: v for k, v in updated_user.items() if k != 'password'}
    user_response['token'] = generate_jwt_token(user_id)
    user_response['bio'] = updated_profile.get('bio', '')
    user_response['image'] = updated_profile.get('image', '')
    
    return user_response

def extract_token(headers):
    """Extract token from Authorization header."""
    auth_header = headers.get('Authorization', '')
    if auth_header.startswith('Token '):
        return auth_header.replace('Token ', '')
    elif auth_header.startswith('Bearer '):
        return auth_header.replace('Bearer ', '')
    return None

def verify_token(token):
    """Verify a JWT token and return the user ID."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload['id']
    except jwt.PyJWTError:
        return None

def format_response(data, status_code=200):
    """Format the API response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': True
        },
        'body': json.dumps({'user': data}) if data else json.dumps({'errors': {'body': ['Invalid request']}})
    }

def format_error(message, status_code=400):
    """Format an error response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': True
        },
        'body': json.dumps({'errors': {'body': [message]}})
    }

def handle_registration(event):
    """Handle user registration."""
    try:
        data = json.loads(event.get('body', '{}'))
        user_data = data.get('user', {})
        
        # Validate required fields
        if not user_data.get('username'):
            return format_error('Username is required')
            
        if not user_data.get('email'):
            return format_error('Email is required')
            
        if not user_data.get('password'):
            return format_error('Password is required')
            
        if len(user_data.get('password', '')) < 8:
            return format_error('Password must be at least 8 characters')
        
        # Create new user
        user = create_user(
            username=user_data['username'],
            email=user_data['email'],
            password=user_data['password']
        )
        
        return format_response(user, 201)
    except ValidationError as e:
        return format_error(str(e))
    except Exception as e:
        return format_error(f'An error occurred: {str(e)}', 500)

def handle_login(event):
    """Handle user login."""
    try:
        data = json.loads(event.get('body', '{}'))
        user_data = data.get('user', {})
        
        if not user_data.get('email'):
            return format_error('Email is required')
            
        if not user_data.get('password'):
            return format_error('Password is required')
        
        user = authenticate(user_data['email'], user_data['password'])
        
        if not user:
            return format_error('A user with this email and password was not found', 401)
        
        # Get user's profile
        profile = get_profile(user['username'])
        
        # Format user response
        user_response = {k: v for k, v in user.items() if k != 'password'}
        user_response['token'] = generate_jwt_token(user['id'])
        user_response['bio'] = profile.get('bio', '')
        user_response['image'] = profile.get('image', '')
        
        return format_response(user_response)
    except Exception as e:
        return format_error(f'An error occurred: {str(e)}', 500)

def handle_user_get(event):
    """Handle retrieving current user."""
    try:
        token = extract_token(event.get('headers', {}))
        if not token:
            return format_error('Authentication required', 401)
        
        user_id = verify_token(token)
        if not user_id:
            return format_error('Invalid token', 401)
        
        user = get_user_by_id(user_id)
        if not user:
            return format_error('User not found', 404)
        
        # Get user's profile
        profile = get_profile(user['username'])
        
        # Format user response
        user_response = {k: v for k, v in user.items() if k != 'password'}
        user_response['token'] = token
        user_response['bio'] = profile.get('bio', '')
        user_response['image'] = profile.get('image', '')
        
        return format_response(user_response)
    except Exception as e:
        return format_error(f'An error occurred: {str(e)}', 500)

def handle_user_update(event):
    """Handle updating current user."""
    try:
        token = extract_token(event.get('headers', {}))
        if not token:
            return format_error('Authentication required', 401)
        
        user_id = verify_token(token)
        if not user_id:
            return format_error('Invalid token', 401)
        
        data = json.loads(event.get('body', '{}'))
        user_data = data.get('user', {})
        
        if not user_data:
            return format_error('No update data provided')
        
        # Update user
        updated_user = update_user(user_id, user_data)
        
        return format_response(updated_user)
    except ValidationError as e:
        return format_error(str(e))
    except Exception as e:
        return format_error(f'An error occurred: {str(e)}', 500)

def lambda_handler(event, context):
    """Main Lambda handler function."""
    try:
        # For API Gateway OPTIONS request (CORS preflight)
        if event.get('httpMethod') == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                    'Access-Control-Allow-Credentials': True
                },
                'body': ''
            }
        
        path = event.get('path', '')
        http_method = event.get('httpMethod', '')
        
        # Handle registration endpoint
        if path == '/api/users' and http_method == 'POST':
            return handle_registration(event)
        
        # Handle login endpoint
        if path == '/api/users/login' and http_method == 'POST':
            return handle_login(event)
        
        # Handle current user endpoint - GET
        if path == '/api/user' and http_method == 'GET':
            return handle_user_get(event)
        
        # Handle current user endpoint - PUT
        if path == '/api/user' and http_method == 'PUT':
            return handle_user_update(event)
        
        # If we get here, no route matched
        return format_error('Not found', 404)
        
    except Exception as e:
        return format_error(f'An unexpected error occurred: {str(e)}', 500)