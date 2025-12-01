import json
import os
import boto3
import logging
from datetime import datetime
import uuid

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
comment_table = dynamodb.Table(os.environ.get('COMMENT_TABLE_NAME', 'Comments'))
article_table = dynamodb.Table(os.environ.get('ARTICLE_TABLE_NAME', 'Articles'))
profile_table = dynamodb.Table(os.environ.get('PROFILE_TABLE_NAME', 'Profiles'))

def lambda_handler(event, context):
    """
    Lambda function to handle comment operations for articles.
    
    This function handles:
    - Listing comments for an article
    - Creating a comment on an article
    - Deleting a comment
    
    The operation is determined by the HTTP method:
    - GET: List comments for an article
    - POST: Create a comment on an article
    - DELETE: Delete a comment
    """
    logger.info(f"Event: {json.dumps(event)}")
    
    # Get HTTP method and path parameters
    http_method = event.get('httpMethod', '')
    path_parameters = event.get('pathParameters', {}) or {}
    article_slug = path_parameters.get('slug', '')
    comment_id = path_parameters.get('comment_id', '')
    
    # Get request context for authentication
    request_context = event.get('requestContext', {})
    authorizer = request_context.get('authorizer', {})
    user_id = authorizer.get('principalId', None)
    
    # Parse query string parameters
    query_string_parameters = event.get('queryStringParameters', {}) or {}
    
    # Parse request body if present
    body = {}
    if event.get('body'):
        try:
            body = json.loads(event.get('body', '{}'))
        except json.JSONDecodeError:
            return response(400, {'errors': {'body': ['Invalid request body']}})
    
    # Route request based on HTTP method
    try:
        if http_method == 'GET':
            # List comments for an article
            return list_comments(article_slug)
        elif http_method == 'POST':
            # Create a comment on an article
            if not user_id:
                return response(401, {'errors': {'authentication': ['Authentication required']}})
            return create_comment(article_slug, user_id, body.get('comment', {}))
        elif http_method == 'DELETE':
            # Delete a comment
            if not user_id:
                return response(401, {'errors': {'authentication': ['Authentication required']}})
            return delete_comment(article_slug, comment_id, user_id)
        else:
            return response(405, {'errors': {'method': ['Method not allowed']}})
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return response(500, {'errors': {'server': ['Internal server error']}})

def list_comments(article_slug):
    """
    List all comments for a specific article.
    """
    # Verify the article exists
    try:
        article_response = article_table.get_item(
            Key={'slug': article_slug}
        )
        if 'Item' not in article_response:
            return response(404, {'errors': {'article': ['An article with this slug does not exist']}})
    except Exception as e:
        logger.error(f"Error checking article existence: {str(e)}")
        return response(500, {'errors': {'database': ['Failed to verify article']}})
    
    # Get comments for the article
    try:
        comment_response = comment_table.query(
            IndexName='article_index',
            KeyConditionExpression='article_slug = :slug',
            ExpressionAttributeValues={
                ':slug': article_slug
            }
        )
        
        comments = comment_response.get('Items', [])
        
        # Get author profiles for each comment
        formatted_comments = []
        for comment in comments:
            # Get author profile
            profile_response = profile_table.get_item(
                Key={'user_id': comment.get('author_id')}
            )
            profile = profile_response.get('Item', {})
            
            formatted_comment = {
                'id': comment.get('comment_id'),
                'createdAt': comment.get('created_at'),
                'updatedAt': comment.get('updated_at'),
                'body': comment.get('body'),
                'author': {
                    'username': profile.get('username', ''),
                    'bio': profile.get('bio', ''),
                    'image': profile.get('image', ''),
                    'following': False  # Default value, would need additional logic to set correctly
                }
            }
            formatted_comments.append(formatted_comment)
        
        return response(200, {'comments': formatted_comments})
    except Exception as e:
        logger.error(f"Error retrieving comments: {str(e)}")
        return response(500, {'errors': {'database': ['Failed to retrieve comments']}})

def create_comment(article_slug, user_id, comment_data):
    """
    Create a comment on an article.
    """
    # Extract and validate the comment data
    body = comment_data.get('body', '').strip()
    if not body:
        return response(400, {'errors': {'body': ['Comment body cannot be empty']}})
    
    # Verify the article exists
    try:
        article_response = article_table.get_item(
            Key={'slug': article_slug}
        )
        if 'Item' not in article_response:
            return response(404, {'errors': {'article': ['An article with this slug does not exist']}})
    except Exception as e:
        logger.error(f"Error checking article existence: {str(e)}")
        return response(500, {'errors': {'database': ['Failed to verify article']}})
    
    # Get the profile for the current user
    try:
        profile_response = profile_table.get_item(
            Key={'user_id': user_id}
        )
        if 'Item' not in profile_response:
            return response(404, {'errors': {'profile': ['User profile not found']}})
        
        profile = profile_response['Item']
    except Exception as e:
        logger.error(f"Error retrieving user profile: {str(e)}")
        return response(500, {'errors': {'database': ['Failed to retrieve user profile']}})
    
    # Create the comment
    try:
        current_time = datetime.utcnow().isoformat()
        comment_id = str(uuid.uuid4())
        
        new_comment = {
            'comment_id': comment_id,
            'article_slug': article_slug,
            'author_id': user_id,
            'body': body,
            'created_at': current_time,
            'updated_at': current_time
        }
        
        # Save the comment to DynamoDB
        comment_table.put_item(Item=new_comment)
        
        # Format the response
        formatted_comment = {
            'id': comment_id,
            'createdAt': current_time,
            'updatedAt': current_time,
            'body': body,
            'author': {
                'username': profile.get('username', ''),
                'bio': profile.get('bio', ''),
                'image': profile.get('image', ''),
                'following': False  # Default value, would need additional logic to set correctly
            }
        }
        
        return response(201, {'comment': formatted_comment})
    except Exception as e:
        logger.error(f"Error creating comment: {str(e)}")
        return response(500, {'errors': {'database': ['Failed to create comment']}})

def delete_comment(article_slug, comment_id, user_id):
    """
    Delete a comment from an article.
    """
    if not comment_id:
        return response(400, {'errors': {'comment': ['Comment ID is required']}})
    
    # Verify the comment exists and the user is authorized to delete it
    try:
        comment_response = comment_table.get_item(
            Key={'comment_id': comment_id}
        )
        
        if 'Item' not in comment_response:
            return response(404, {'errors': {'comment': ['Comment not found']}})
        
        comment = comment_response['Item']
        
        # Verify the comment belongs to the article
        if comment.get('article_slug') != article_slug:
            return response(400, {'errors': {'comment': ['Comment does not belong to the specified article']}})
        
        # Verify the user is the author of the comment or the article
        if comment.get('author_id') != user_id:
            # Check if the user is the article author
            article_response = article_table.get_item(
                Key={'slug': article_slug}
            )
            article = article_response.get('Item', {})
            
            if article.get('author_id') != user_id:
                return response(403, {'errors': {'authorization': ['You are not authorized to delete this comment']}})
        
        # Delete the comment
        comment_table.delete_item(
            Key={'comment_id': comment_id}
        )
        
        return response(204, None)
    except Exception as e:
        logger.error(f"Error deleting comment: {str(e)}")
        return response(500, {'errors': {'database': ['Failed to delete comment']}})

def response(status_code, body=None):
    """
    Create a response object for the API Gateway.
    """
    result = {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,Authorization'
        }
    }
    
    if body is not None:
        result['body'] = json.dumps(body)
    
    return result