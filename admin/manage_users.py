#!/usr/bin/env python3
"""
PennyPal User Management Script
Manage user subscriptions and usage limits
"""

import boto3
import sys
from botocore.exceptions import ClientError

# AWS Configuration
DYNAMODB_TABLE = 'financial-helper-profiles'
COGNITO_USER_POOL_ID = 'YOUR_USER_POOL_ID'  # Update this with your actual User Pool ID

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
cognito = boto3.client('cognito-idp')
table = dynamodb.Table(DYNAMODB_TABLE)

def find_user_by_email(email):
    """Find a user's Cognito sub by email"""
    try:
        response = cognito.list_users(
            UserPoolId=COGNITO_USER_POOL_ID,
            Filter=f'email = "{email}"'
        )
        
        if not response['Users']:
            print(f"❌ User not found: {email}")
            return None
        
        user = response['Users'][0]
        user_sub = None
        user_email = None
        
        for attr in user['Attributes']:
            if attr['Name'] == 'sub':
                user_sub = attr['Value']
            if attr['Name'] == 'email':
                user_email = attr['Value']
        
        return {
            'userId': user_sub,
            'email': user_email,
            'username': user['Username']
        }
        
    except ClientError as e:
        print(f"❌ Error finding user: {e}")
        return None

def get_user_profile(user_id):
    """Get user profile from DynamoDB"""
    try:
        response = table.get_item(Key={'userId': user_id})
        if 'Item' in response:
            return response['Item']
        return None
    except ClientError as e:
        print(f"❌ Error getting profile: {e}")
        return None

def upgrade_to_pro(email):
    """Upgrade a user to Pro tier"""
    user = find_user_by_email(email)
    if not user:
        return False
    
    user_id = user['userId']
    
    try:
        table.update_item(
            Key={'userId': user_id},
            UpdateExpression='SET subscriptionTier = :tier, questionsLimit = :limit',
            ExpressionAttributeValues={
                ':tier': 'pro',
                ':limit': 999999
            }
        )
        
        print(f"✅ Upgraded {email} to Pro tier!")
        print(f"   User ID: {user_id}")
        print(f"   Unlimited questions enabled")
        return True
        
    except ClientError as e:
        print(f"❌ Error upgrading user: {e}")
        return False

def downgrade_to_free(email):
    """Downgrade a user to Free tier"""
    user = find_user_by_email(email)
    if not user:
        return False
    
    user_id = user['userId']
    
    try:
        table.update_item(
            Key={'userId': user_id},
            UpdateExpression='SET subscriptionTier = :tier, questionsLimit = :limit',
            ExpressionAttributeValues={
                ':tier': 'free',
                ':limit': 10
            }
        )
        
        print(f"✅ Downgraded {email} to Free tier")
        print(f"   User ID: {user_id}")
        print(f"   Limit: 10 questions")
        return True
        
    except ClientError as e:
        print(f"❌ Error downgrading user: {e}")
        return False

def reset_usage(email):
    """Reset a user's question counter"""
    user = find_user_by_email(email)
    if not user:
        return False
    
    user_id = user['userId']
    
    try:
        table.update_item(
            Key={'userId': user_id},
            UpdateExpression='SET questionsAsked = :zero',
            ExpressionAttributeValues={
                ':zero': 0
            }
        )
        
        print(f"✅ Reset usage counter for {email}")
        print(f"   User ID: {user_id}")
        return True
        
    except ClientError as e:
        print(f"❌ Error resetting usage: {e}")
        return False

def view_user(email):
    """View user details"""
    user = find_user_by_email(email)
    if not user:
        return
    
    user_id = user['userId']
    profile = get_user_profile(user_id)
    
    print(f"\n📊 User Details")
    print(f"   Email: {user['email']}")
    print(f"   User ID: {user_id}")
    print(f"   Username: {user['username']}")
    
    if profile:
        tier = profile.get('subscriptionTier', 'free')
        asked = profile.get('questionsAsked', 0)
        limit = profile.get('questionsLimit', 10)
        remaining = limit - asked
        
        print(f"\n💳 Subscription")
        print(f"   Tier: {tier.upper()}")
        print(f"   Questions Asked: {asked}")
        print(f"   Questions Limit: {limit}")
        print(f"   Questions Remaining: {remaining}")
        
        if profile.get('annualIncome'):
            print(f"\n💰 Profile")
            print(f"   Annual Income: ${profile.get('annualIncome', 'N/A')}")
            print(f"   Created: {profile.get('createdAt', 'N/A')}")
            print(f"   Updated: {profile.get('updatedAt', 'N/A')}")
    else:
        print(f"\n⚠️  No profile data found")

def list_all_users():
    """List all users with their subscription status"""
    try:
        response = table.scan()
        users = response['Items']
        
        print(f"\n📋 All Users ({len(users)} total)\n")
        print(f"{'Email':<30} {'Tier':<8} {'Used':<6} {'Limit':<8} {'Remaining':<10}")
        print("-" * 70)
        
        for profile in users:
            user_id = profile.get('userId')
            tier = profile.get('subscriptionTier', 'free')
            asked = profile.get('questionsAsked', 0)
            limit = profile.get('questionsLimit', 10)
            remaining = limit - asked
            
            # Try to get email from Cognito
            try:
                cognito_user = cognito.admin_get_user(
                    UserPoolId=COGNITO_USER_POOL_ID,
                    Username=user_id
                )
                email = next((attr['Value'] for attr in cognito_user['UserAttributes'] if attr['Name'] == 'email'), 'N/A')
            except:
                email = 'N/A'
            
            print(f"{email:<30} {tier:<8} {asked:<6} {limit:<8} {remaining:<10}")
        
    except ClientError as e:
        print(f"❌ Error listing users: {e}")

def main():
    if len(sys.argv) < 2:
        print("""
PennyPal User Management

Usage:
  python manage_users.py upgrade <email>      - Upgrade user to Pro tier
  python manage_users.py downgrade <email>    - Downgrade user to Free tier
  python manage_users.py reset <email>        - Reset usage counter
  python manage_users.py view <email>         - View user details
  python manage_users.py list                 - List all users

Examples:
  python manage_users.py upgrade user@example.com
  python manage_users.py view user@example.com
  python manage_users.py list
        """)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        list_all_users()
    elif command in ['upgrade', 'downgrade', 'reset', 'view']:
        if len(sys.argv) < 3:
            print("❌ Email required")
            sys.exit(1)
        
        email = sys.argv[2]
        
        if command == 'upgrade':
            upgrade_to_pro(email)
        elif command == 'downgrade':
            downgrade_to_free(email)
        elif command == 'reset':
            reset_usage(email)
        elif command == 'view':
            view_user(email)
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)

if __name__ == '__main__':
    main()
