import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
import os
import logging

# Configure logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get environment variables
TABLE_NAME = os.environ.get('TAGS_TABLE', 'Tags')

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    AWS Lambda function to retrieve all tags from DynamoDB
    
    :param event: API Gateway Lambda Proxy Input Format
    :param context: Lambda Context runtime methods and attributes
    :return: API Gateway Lambda Proxy Output Format
    """
    logger.info(f"Event received: {json.dumps(event)}")
    
    try:
        # Get all tags from DynamoDB
        response = table.scan(
            ProjectionExpression="tag"
        )
        
        # Extract tag values
        tags = [item['tag'] for item in response.get('Items', [])]
        
        # If there are more items (pagination), continue scanning
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ProjectionExpression="tag",
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            tags.extend([item['tag'] for item in response.get('Items', [])])
        
        # Return the response with proper headers for CORS
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,OPTIONS'
            },
            'body': json.dumps({'tags': tags})
        }
    
    except Exception as e:
        logger.error(f"Error retrieving tags: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type,Authorization',
                'Access-Control-Allow-Methods': 'GET,OPTIONS'
            },
            'body': json.dumps({'error': 'Error retrieving tags'})
        }