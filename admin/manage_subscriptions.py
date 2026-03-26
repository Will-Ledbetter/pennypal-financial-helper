#!/usr/bin/env python3
"""
Admin Tool: Manage User Subscriptions
Usage: python manage_subscriptions.py [command] [email]
"""

import boto3
import sys
from datetime import datetime

# Configuration
USER_POOL_ID = 'us-east-1_Nmvta5ZLQ'  # Update with your User Pool ID
TABLE_NAME = 'financial-helper-profiles'
REGION = 'us-east-1'

# Initialize AWS clients
cognito = boto3.client('cognito-idp', region_name=REGION)
dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table(TABLE_NAME)

def get_user_by_email(email):
    """Find user in Cognito by email"""
    try:
        response = cognito.list_users(
            UserPoolId=USER_POOL_ID,
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
            'sub': user_sub,
            'email': user_email,
            'username': user['Username'],
            'status': user['UserStatus']
        }
    except Exception as e:
        print(f"❌ Error finding user: {e}")
        return None

def get_profile(user_sub):
    """Get user profile from DynamoDB"""
    try:
        response = table.get_item(Key={'userId': user_sub})
        return response.get('Item', {})
    except Exception as e:
        print(f"❌ Error getting profile: {e}")
        return {}

def upgrade_to_pro(email):
    """Upgrade user to Pro tier"""
    user = get_user_by_email(email)
    if not user:
        return
    
    try:
        table.update_item(
            Key={'userId': user['sub']},
            UpdateExpression='SET subscriptionTier = :tier, questionsLimit = :limit, upgradedAt = :time, manualUpgrade = :manual',
            ExpressionAttributeValues={
                ':tier': 'pro',
                ':limit': 999999,
                ':time': datetime.utcnow().isoformat(),
                ':manual': True
            }
        )
        print(f"✅ Upgraded {email} to Pro tier!")
        print(f"   User ID: {user['sub']}")
        print(f"   Status: {user['status']}")
    except Exception as e:
        print(f"❌ Error upgrading user: {e}")

def downgrade_to_free(email):
    """Downgrade user to Free tier"""
    user = get_user_by_email(email)
    if not user:
        return
    
    try:
        table.update_item(
            Key={'userId': user['sub']},
            UpdateExpression='SET subscriptionTier = :tier, questionsLimit = :limit, downgradedAt = :time',
            ExpressionAttributeValues={
                ':tier': 'free',
                ':limit': 10,
                ':time': datetime.utcnow().isoformat()
            }
        )
        print(f"✅ Downgraded {email} to Free tier")
        print(f"   User ID: {user['sub']}")
    except Exception as e:
        print(f"❌ Error downgrading user: {e}")

def reset_usage(email):
    """Reset user's question count"""
    user = get_user_by_email(email)
    if not user:
        return
    
    try:
        table.update_item(
            Key={'userId': user['sub']},
            UpdateExpression='SET questionsAsked = :zero',
            ExpressionAttributeValues={':zero': 0}
        )
        print(f"✅ Reset usage for {email}")
        print(f"   Questions asked: 0")
    except Exception as e:
        print(f"❌ Error resetting usage: {e}")

def view_user(email):
    """View user details"""
    user = get_user_by_email(email)
    if not user:
        return
    
    profile = get_profile(user['sub'])
    
    print(f"\n{'='*50}")
    print(f"USER DETAILS: {email}")
    print(f"{'='*50}")
    print(f"User ID: {user['sub']}")
    print(f"Username: {user['username']}")
    print(f"Status: {user['status']}")
    print(f"\nSUBSCRIPTION:")
    print(f"  Tier: {profile.get('subscriptionTier', 'free').upper()}")
    print(f"  Questions Asked: {profile.get('questionsAsked', 0)}")
    print(f"  Questions Limit: {profile.get('questionsLimit', 10)}")
    
    if profile.get('upgradedAt'):
        print(f"  Upgraded: {profile.get('upgradedAt')}")
    if profile.get('stripeCustomerId'):
        print(f"  Stripe Customer: {profile.get('stripeCustomerId')}")
    if profile.get('stripeSubscriptionId'):
        print(f"  Stripe Subscription: {profile.get('stripeSubscriptionId')}")
    
    print(f"\nFINANCIAL PROFILE:")
    print(f"  Annual Income: ${profile.get('annualIncome', 'Not set')}")
    print(f"  Monthly Expenses: ${profile.get('monthlyExpenses', 'Not set')}")
    print(f"  Current Savings: ${profile.get('currentSavings', 'Not set')}")
    print(f"  Total Debt: ${profile.get('totalDebt', 'Not set')}")
    print(f"{'='*50}\n")

def list_all_pro_users():
    """List all Pro tier users"""
    try:
        response = table.scan(
            FilterExpression='subscriptionTier = :pro',
            ExpressionAttributeValues={':pro': 'pro'}
        )
        
        users = response['Items']
        print(f"\n{'='*50}")
        print(f"PRO USERS ({len(users)} total)")
        print(f"{'='*50}")
        
        for user in users:
            user_id = user['userId']
            questions = user.get('questionsAsked', 0)
            upgraded = user.get('upgradedAt', 'Unknown')
            manual = user.get('manualUpgrade', False)
            
            # Get email from Cognito
            try:
                cog_user = cognito.admin_get_user(
                    UserPoolId=USER_POOL_ID,
                    Username=user_id
                )
                email = next((attr['Value'] for attr in cog_user['UserAttributes'] if attr['Name'] == 'email'), 'Unknown')
            except:
                email = 'Unknown'
            
            print(f"\n{email}")
            print(f"  Questions: {questions}")
            print(f"  Upgraded: {upgraded}")
            print(f"  Manual: {'Yes' if manual else 'No'}")
        
        print(f"\n{'='*50}\n")
    except Exception as e:
        print(f"❌ Error listing users: {e}")

def show_usage():
    """Show usage instructions"""
    print("""
PennyPal Advisor - Subscription Management Tool

USAGE:
    python manage_subscriptions.py [command] [email]

COMMANDS:
    upgrade <email>     - Upgrade user to Pro tier
    downgrade <email>   - Downgrade user to Free tier
    reset <email>       - Reset user's question count
    view <email>        - View user details
    list-pro           - List all Pro users

EXAMPLES:
    python manage_subscriptions.py upgrade user@example.com
    python manage_subscriptions.py view user@example.com
    python manage_subscriptions.py list-pro
    python manage_subscriptions.py reset user@example.com

NOTES:
    - Make sure AWS credentials are configured
    - Update USER_POOL_ID and TABLE_NAME in the script
    - Requires boto3: pip install boto3
    """)

def main():
    if len(sys.argv) < 2:
        show_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'list-pro':
        list_all_pro_users()
    elif len(sys.argv) < 3:
        print("❌ Email required for this command")
        show_usage()
    else:
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
            show_usage()

if __name__ == '__main__':
    main()
