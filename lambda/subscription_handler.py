"""
Subscription Handler Lambda
Manages Stripe subscriptions and upgrades users to Pro
"""

import json
import os
import logging
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize services
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('PROFILES_TABLE', 'financial-helper-profiles'))

# Stripe configuration (install: pip install stripe)
try:
    import stripe
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', '')
    STRIPE_PRICE_ID = os.environ.get('STRIPE_PRICE_ID', '')  # Your Stripe Price ID for $9.99/month
except ImportError:
    logger.warning("Stripe library not installed")

# CORS headers
CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
}

def lambda_handler(event, context):
    """
    Handle subscription operations
    
    POST /subscribe - Create Stripe subscription and upgrade user
    POST /webhook - Handle Stripe webhooks
    """
    
    # Handle OPTIONS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return create_response(200, {})
    
    try:
        path = event.get('path', '')
        
        if path.endswith('/subscribe'):
            return handle_subscribe(event)
        elif path.endswith('/webhook'):
            return handle_webhook(event)
        else:
            return create_response(404, {'error': 'Not found'})
            
    except Exception as e:
        logger.error(f"Error: {e}")
        return create_response(500, {'error': 'Internal server error'})

def handle_subscribe(event):
    """Create Stripe subscription and upgrade user"""
    
    # Get user ID from token
    user_id = get_user_id_from_token(event)
    if not user_id:
        return create_response(401, {'error': 'Unauthorized'})
    
    try:
        body = json.loads(event.get('body', '{}'))
        payment_method_id = body.get('paymentMethodId')
        
        if not payment_method_id:
            return create_response(400, {'error': 'Payment method required'})
        
        # Get user email from Cognito
        user_email = get_user_email(event)
        
        # Create or get Stripe customer
        customer = stripe.Customer.create(
            payment_method=payment_method_id,
            email=user_email,
            metadata={'userId': user_id},
            invoice_settings={
                'default_payment_method': payment_method_id
            }
        )
        
        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{'price': STRIPE_PRICE_ID}],
            expand=['latest_invoice.payment_intent']
        )
        
        # Upgrade user in DynamoDB
        upgrade_user_to_pro(user_id, customer.id, subscription.id)
        
        logger.info(f"User {user_id} upgraded to Pro")
        
        return create_response(200, {
            'success': True,
            'subscriptionId': subscription.id,
            'clientSecret': subscription.latest_invoice.payment_intent.client_secret
        })
        
    except stripe.error.CardError as e:
        logger.error(f"Card error: {e}")
        return create_response(400, {'error': 'Card declined'})
    except Exception as e:
        logger.error(f"Subscription error: {e}")
        return create_response(500, {'error': 'Failed to create subscription'})

def handle_webhook(event):
    """Handle Stripe webhooks for subscription events"""
    
    try:
        payload = event.get('body', '')
        sig_header = event.get('headers', {}).get('Stripe-Signature', '')
        webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
        
        # Verify webhook signature
        stripe_event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        
        event_type = stripe_event['type']
        data = stripe_event['data']['object']
        
        logger.info(f"Webhook received: {event_type}")
        
        # Handle different event types
        if event_type == 'customer.subscription.deleted':
            # Subscription cancelled - downgrade user
            customer_id = data['customer']
            downgrade_user(customer_id)
            
        elif event_type == 'invoice.payment_failed':
            # Payment failed - notify user
            customer_id = data['customer']
            logger.warning(f"Payment failed for customer: {customer_id}")
            # TODO: Send email notification
            
        elif event_type == 'customer.subscription.updated':
            # Subscription updated
            customer_id = data['customer']
            status = data['status']
            if status == 'active':
                ensure_user_is_pro(customer_id)
        
        return create_response(200, {'received': True})
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return create_response(400, {'error': 'Webhook failed'})

def upgrade_user_to_pro(user_id, stripe_customer_id, stripe_subscription_id):
    """Upgrade user to Pro tier in DynamoDB"""
    try:
        table.update_item(
            Key={'userId': user_id},
            UpdateExpression='SET subscriptionTier = :tier, questionsLimit = :limit, stripeCustomerId = :customer, stripeSubscriptionId = :subscription, upgradedAt = :time',
            ExpressionAttributeValues={
                ':tier': 'pro',
                ':limit': 999999,
                ':customer': stripe_customer_id,
                ':subscription': stripe_subscription_id,
                ':time': datetime.utcnow().isoformat()
            }
        )
        logger.info(f"Upgraded user {user_id} to Pro")
    except Exception as e:
        logger.error(f"Error upgrading user: {e}")
        raise

def downgrade_user(stripe_customer_id):
    """Downgrade user to free tier"""
    try:
        # Find user by Stripe customer ID
        response = table.scan(
            FilterExpression='stripeCustomerId = :customer',
            ExpressionAttributeValues={':customer': stripe_customer_id}
        )
        
        if response['Items']:
            user_id = response['Items'][0]['userId']
            table.update_item(
                Key={'userId': user_id},
                UpdateExpression='SET subscriptionTier = :tier, questionsLimit = :limit, downgradedAt = :time',
                ExpressionAttributeValues={
                    ':tier': 'free',
                    ':limit': 10,
                    ':time': datetime.utcnow().isoformat()
                }
            )
            logger.info(f"Downgraded user {user_id} to Free")
    except Exception as e:
        logger.error(f"Error downgrading user: {e}")

def ensure_user_is_pro(stripe_customer_id):
    """Ensure user has Pro tier (for subscription reactivation)"""
    try:
        response = table.scan(
            FilterExpression='stripeCustomerId = :customer',
            ExpressionAttributeValues={':customer': stripe_customer_id}
        )
        
        if response['Items']:
            user_id = response['Items'][0]['userId']
            if response['Items'][0].get('subscriptionTier') != 'pro':
                table.update_item(
                    Key={'userId': user_id},
                    UpdateExpression='SET subscriptionTier = :tier, questionsLimit = :limit',
                    ExpressionAttributeValues={
                        ':tier': 'pro',
                        ':limit': 999999
                    }
                )
                logger.info(f"Reactivated Pro for user {user_id}")
    except Exception as e:
        logger.error(f"Error ensuring Pro status: {e}")

def get_user_id_from_token(event):
    """Extract user ID from Cognito JWT token"""
    try:
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        claims = authorizer.get('claims', {})
        return claims.get('sub') or claims.get('cognito:username')
    except Exception as e:
        logger.error(f"Error extracting user ID: {e}")
        return None

def get_user_email(event):
    """Extract user email from Cognito JWT token"""
    try:
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        claims = authorizer.get('claims', {})
        return claims.get('email', '')
    except Exception as e:
        logger.error(f"Error extracting email: {e}")
        return ''

def create_response(status_code, body):
    """Create API Gateway response"""
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps(body)
    }
