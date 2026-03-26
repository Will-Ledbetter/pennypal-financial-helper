"""
AI Advisor Lambda - Generic Example
Generates personalized advice using Amazon Bedrock

This is a sanitized example for portfolio purposes.
Replace configuration values with your own before deployment.
"""

import json
import os
import logging
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Bedrock
bedrock_runtime = boto3.client('bedrock-runtime')

# Model configuration
MODEL_ID = 'anthropic.claude-3-haiku-20240307-v1:0'  # Or your preferred model
MAX_TOKENS = 2048

# CORS headers
CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
}

def lambda_handler(event, context):
    """
    Generate personalized advice using AI
    
    POST /advice
    Body: {
        "question": "user's question",
        "context": {user context data}
    }
    """
    
    # Handle OPTIONS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return create_response(200, {})
    
    try:
        # Get user ID from token (for logging/tracking)
        user_id = get_user_id_from_token(event)
        if not user_id:
            return create_response(401, {'error': 'Unauthorized'})
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        question = body.get('question', '').strip()
        user_context = body.get('context', {})
        
        if not question:
            return create_response(400, {'error': 'Question is required'})
        
        if not user_context:
            return create_response(400, {'error': 'User context is required'})
        
        logger.info(f"Generating advice for user: {user_id}, question length: {len(question)}")
        
        # Generate advice using Bedrock
        advice = generate_advice(question, user_context)
        
        if not advice:
            logger.error("Generated advice is empty")
            return create_response(500, {'error': 'Failed to generate advice - empty response'})
        
        logger.info(f"Successfully generated advice, length: {len(advice)}")
        
        return create_response(200, {
            'success': True,
            'advice': advice
        })
        
    except json.JSONDecodeError:
        return create_response(400, {'error': 'Invalid JSON'})
    except Exception as e:
        logger.error(f"Error: {e}")
        return create_response(500, {'error': 'Failed to generate advice'})

def get_user_id_from_token(event):
    """Extract user ID from JWT token"""
    try:
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        claims = authorizer.get('claims', {})
        user_id = claims.get('sub') or claims.get('cognito:username')
        return user_id
    except Exception as e:
        logger.error(f"Error extracting user ID: {e}")
        return None

def generate_advice(question, user_context):
    """Generate personalized advice using Bedrock"""
    
    # Build context from user data
    context_text = build_context(user_context)
    
    # Build prompt for AI
    prompt = f"""You are a professional advisor. A client has asked you for advice based on their situation.

CLIENT'S CONTEXT:
{context_text}

CLIENT'S QUESTION:
{question}

Please provide personalized, actionable advice based on their specific situation. Be specific, practical, and encouraging.

Your advice should:
1. Address their specific question directly
2. Consider their complete context
3. Provide concrete, actionable steps
4. Be realistic and achievable
5. Explain the reasoning behind your recommendations

Keep your response concise but comprehensive (300-500 words).
"""
    
    try:
        logger.info(f"Calling Bedrock with model: {MODEL_ID}")
        
        # Call Bedrock
        response = bedrock_runtime.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": MAX_TOKENS,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7
            })
        )
        
        logger.info("Bedrock response received, parsing...")
        
        # Parse response
        response_body = json.loads(response['body'].read())
        
        if 'content' not in response_body or not response_body['content']:
            logger.error(f"Invalid response structure: {response_body}")
            raise Exception("Invalid response from Bedrock")
        
        advice = response_body['content'][0]['text']
        
        if not advice or len(advice.strip()) == 0:
            logger.error("Bedrock returned empty advice")
            raise Exception("Empty advice from Bedrock")
        
        logger.info(f"Advice generated successfully, length: {len(advice)}")
        
        # Add disclaimer
        disclaimer = "\n\n---\n\nDisclaimer: This advice is generated by AI and should not be considered professional advice. Please consult with a licensed professional for personalized guidance."
        
        return advice + disclaimer
        
    except ClientError as e:
        logger.error(f"Bedrock ClientError: {e}")
        raise Exception(f"Bedrock API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error generating advice: {e}")
        raise Exception(f"Failed to generate advice: {str(e)}")

def build_context(user_context):
    """Build a readable context string from user data"""
    
    def format_value(value):
        if not value:
            return "Not provided"
        return str(value)
    
    # Customize these fields based on your application
    context = f"""
- Field 1: {format_value(user_context.get('field1'))}
- Field 2: {format_value(user_context.get('field2'))}
- Field 3: {format_value(user_context.get('field3'))}
"""
    
    return context.strip()

def create_response(status_code, body):
    """Create API Gateway response"""
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps(body)
    }

# Example Request:
# {
#     "question": "What should I do about X?",
#     "context": {
#         "field1": "value1",
#         "field2": "value2",
#         "field3": "value3"
#     }
# }

# Example Response:
# {
#     "success": true,
#     "advice": "Based on your situation..."
# }
