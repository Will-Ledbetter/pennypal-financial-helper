# Subscription Management Guide

## Overview

PennyPal Advisor now has a two-tier subscription system:

- **Free Tier**: 10 questions per account
- **Pro Tier**: Unlimited questions

## How It Works

### Usage Tracking
- Each time a user asks a question, the `questionsAsked` counter increments
- Free tier users are blocked after reaching their limit
- Pro tier users have unlimited access

### User Profile Fields
Each user profile in DynamoDB includes:
- `subscriptionTier`: "free" or "pro"
- `questionsAsked`: Number of questions asked
- `questionsLimit`: Maximum questions allowed (10 for free, 999999 for pro)

## Managing User Subscriptions

### Option 1: AWS DynamoDB Console (Manual)

1. Go to AWS DynamoDB Console
2. Open the `financial-helper-profiles` table
3. Find the user by their `userId` (Cognito sub)
4. Click "Edit item"
5. Update these fields:
   - `subscriptionTier`: Change to "pro"
   - `questionsLimit`: Change to 999999
6. Save

### Option 2: AWS CLI (Scripted)

Upgrade a user to Pro:
```bash
aws dynamodb update-item \
  --table-name financial-helper-profiles \
  --key '{"userId": {"S": "USER_COGNITO_SUB_HERE"}}' \
  --update-expression "SET subscriptionTier = :tier, questionsLimit = :limit" \
  --expression-attribute-values '{":tier": {"S": "pro"}, ":limit": {"N": "999999"}}'
```

Reset a user's question count:
```bash
aws dynamodb update-item \
  --table-name financial-helper-profiles \
  --key '{"userId": {"S": "USER_COGNITO_SUB_HERE"}}' \
  --update-expression "SET questionsAsked = :zero" \
  --expression-attribute-values '{":zero": {"N": "0"}}'
```

### Option 3: Python Script

Create a file `upgrade_user.py`:

```python
import boto3
import sys

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('financial-helper-profiles')

def upgrade_to_pro(user_email):
    """Upgrade a user to Pro tier by email"""
    # First, find the user's Cognito sub by email
    cognito = boto3.client('cognito-idp')
    user_pool_id = 'YOUR_USER_POOL_ID'
    
    response = cognito.list_users(
        UserPoolId=user_pool_id,
        Filter=f'email = "{user_email}"'
    )
    
    if not response['Users']:
        print(f"User not found: {user_email}")
        return
    
    user_sub = None
    for attr in response['Users'][0]['Attributes']:
        if attr['Name'] == 'sub':
            user_sub = attr['Value']
            break
    
    if not user_sub:
        print("Could not find user sub")
        return
    
    # Update DynamoDB
    table.update_item(
        Key={'userId': user_sub},
        UpdateExpression='SET subscriptionTier = :tier, questionsLimit = :limit',
        ExpressionAttributeValues={
            ':tier': 'pro',
            ':limit': 999999
        }
    )
    
    print(f"✅ Upgraded {user_email} to Pro tier!")
    print(f"   User ID: {user_sub}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python upgrade_user.py user@email.com")
        sys.exit(1)
    
    upgrade_to_pro(sys.argv[1])
```

Run it:
```bash
python upgrade_user.py user@example.com
```

## Finding User IDs

### Method 1: From Cognito
1. Go to AWS Cognito Console
2. Select your User Pool
3. Click "Users"
4. Find the user by email
5. Click on the user
6. Copy the "sub" attribute (this is the userId)

### Method 2: From DynamoDB
1. Go to DynamoDB Console
2. Open `financial-helper-profiles` table
3. Click "Explore table items"
4. Search by any field to find the user

## Payment Integration (Future)

To add payment processing:

### Option 1: Stripe
1. Create Stripe account
2. Add Stripe Checkout to frontend
3. Create webhook Lambda to handle successful payments
4. Webhook updates DynamoDB subscription tier

### Option 2: AWS Marketplace
1. List app on AWS Marketplace
2. Use Marketplace Metering API
3. Automatically sync subscriptions

### Option 3: PayPal
1. Add PayPal buttons to frontend
2. Create IPN webhook handler
3. Update subscriptions on payment

## Monitoring Usage

### CloudWatch Query
Create a CloudWatch Insights query to monitor usage:

```
fields @timestamp, userId, questionsAsked, subscriptionTier
| filter @message like /Generating advice/
| stats count() by userId
```

### DynamoDB Scan
Get all users approaching their limit:

```bash
aws dynamodb scan \
  --table-name financial-helper-profiles \
  --filter-expression "subscriptionTier = :free AND questionsAsked >= :threshold" \
  --expression-attribute-values '{":free": {"S": "free"}, ":threshold": {"N": "8"}}'
```

## Changing Limits

To change the free tier limit:

1. Update `FREE_TIER_LIMIT` in `advisor_handler.py`
2. Update the default in `profile_handler.py`
3. Redeploy both Lambdas
4. Update existing users in DynamoDB (optional)

## Email Notifications

To notify users when they're approaching their limit, add to `advisor_handler.py`:

```python
import boto3
ses = boto3.client('ses')

def send_limit_warning(user_email, remaining):
    if remaining == 2:  # 2 questions left
        ses.send_email(
            Source='noreply@pennypal.com',
            Destination={'ToAddresses': [user_email]},
            Message={
                'Subject': {'Data': 'You have 2 questions remaining'},
                'Body': {
                    'Text': {'Data': 'Upgrade to Pro for unlimited questions!'}
                }
            }
        )
```

## Support & Refunds

When handling support requests:
1. Verify payment in Stripe/PayPal
2. Find user by email in Cognito
3. Update subscription in DynamoDB
4. Confirm with user

For refunds:
1. Process refund in payment system
2. Downgrade user to free tier
3. Reset question count if appropriate
