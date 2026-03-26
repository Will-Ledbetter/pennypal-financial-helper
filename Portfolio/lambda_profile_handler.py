"""
Profile Handler Lambda - Generic Example
Manages user profile CRUD operations in DynamoDB

This is a sanitized example for portfolio purposes.
Replace configuration values with your own before deployment.
"""

import json
import os
import logging
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('PROFILES_TABLE', 'your-profiles-table')
table = dynamodb.Table(table_name)

# CORS headers
CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
}

def lambda_handler(event, context):
    """
    Handle profile operations
    
    GET /profile - Get user profile
    POST /profile - Create/Update user profile
    """
    
    # Handle OPTIONS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return create_response(200, {})
    
    try:
        # Get user ID from authentication token
        user_id = get_user_id_from_token(event)
        if not user_id:
            return create_response(401, {'error': 'Unauthorized'})
        
        http_method = event.get('httpMethod')
        
        if http_method == 'GET':
            return get_profile(user_id)
        elif http_method == 'POST':
            return save_profile(user_id, event)
        else:
            return create_response(405, {'error': 'Method not allowed'})
            
    except Exception as e:
        logger.error(f"Error: {e}")
        return create_response(500, {'error': 'Internal server error'})

def get_user_id_from_token(event):
    """Extract user ID from JWT token (Cognito example)"""
    try:
        # In API Gateway with Cognito authorizer, user info is in requestContext
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        claims = authorizer.get('claims', {})
        
        # Get user ID from token claims
        user_id = claims.get('sub') or claims.get('cognito:username')
        
        return user_id
    except Exception as e:
        logger.error(f"Error extracting user ID: {e}")
        return None

def get_profile(user_id):
    """Get user profile from DynamoDB"""
    try:
        response = table.get_item(Key={'userId': user_id})
        
        if 'Item' in response:
            profile = response['Item']
            # Remove internal fields from response
            profile.pop('userId', None)
            profile.pop('createdAt', None)
            profile.pop('updatedAt', None)
            
            return create_response(200, {'profile': profile})
        else:
            # No profile yet
            return create_response(200, {'profile': {}})
            
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return create_response(500, {'error': 'Failed to retrieve profile'})

def save_profile(user_id, event):
    """Save or update user profile in DynamoDB"""
    try:
        body = json.loads(event.get('body', '{}'))
        
        # Build profile data structure
        # Customize these fields based on your application needs
        profile_data = {
            'userId': user_id,
            'field1': body.get('field1', ''),
            'field2': body.get('field2', ''),
            'field3': body.get('field3', ''),
            # Add more fields as needed
            'updatedAt': datetime.utcnow().isoformat()
        }
        
        # Add createdAt if new profile
        existing = table.get_item(Key={'userId': user_id})
        if 'Item' not in existing:
            profile_data['createdAt'] = datetime.utcnow().isoformat()
        
        # Save to DynamoDB
        table.put_item(Item=profile_data)
        
        # Return saved profile (without internal fields)
        response_profile = profile_data.copy()
        response_profile.pop('userId', None)
        response_profile.pop('createdAt', None)
        response_profile.pop('updatedAt', None)
        
        logger.info(f"Profile saved for user: {user_id}")
        
        return create_response(200, {
            'success': True,
            'profile': response_profile
        })
        
    except json.JSONDecodeError:
        return create_response(400, {'error': 'Invalid JSON'})
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return create_response(500, {'error': 'Failed to save profile'})

def create_response(status_code, body):
    """Create API Gateway response with CORS headers"""
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps(body)
    }

# Example DynamoDB Table Schema:
# {
#     "userId": "string (partition key)",
#     "field1": "string",
#     "field2": "string",
#     "field3": "string",
#     "createdAt": "string (ISO timestamp)",
#     "updatedAt": "string (ISO timestamp)"
# }
