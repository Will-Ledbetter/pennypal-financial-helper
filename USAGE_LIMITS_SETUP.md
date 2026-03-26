# Usage Limits Setup Guide

## Overview

PennyPal now has usage limits to control costs:
- **Free Tier**: 10 questions per user (permanently cut off after limit)
- **Pro Tier**: Unlimited questions (manually granted by you only)

Users who reach their limit will see: "Pro version not yet released" - they cannot upgrade themselves.

## How It Works

1. **New users** automatically get Free tier (10 questions)
2. **Each question** increments their counter
3. **After 10 questions**, free users are permanently blocked
4. **Message shown**: "Pro version not yet released"
5. **Only you** can manually upgrade specific users to Pro tier (unlimited access)

## Deployment Steps

### 1. Update Lambda Functions

Deploy the updated Lambda functions:

```bash
cd "Financial Helper App"

# Package and deploy advisor handler
cd lambda
zip advisor_handler.zip advisor_handler.py
aws lambda update-function-code \
  --function-name financial-helper-advisor \
  --zip-file fileb://advisor_handler.zip

# Package and deploy profile handler
zip profile_handler.zip profile_handler.py
aws lambda update-function-code \
  --function-name financial-helper-profile \
  --zip-file fileb://profile_handler.zip

cd ..
```

### 2. Update DynamoDB Permissions

Ensure the advisor Lambda has DynamoDB permissions:

```bash
# The advisor Lambda needs to read/write to the profiles table
# This should already be configured, but verify in IAM
```

### 3. Configure Admin Script

Edit `admin/manage_users.py` and update:

```python
COGNITO_USER_POOL_ID = 'your-actual-user-pool-id'
```

Find your User Pool ID:
```bash
aws cognito-idp list-user-pools --max-results 10
```

### 4. Test the System

Test with a free tier user:
1. Create a new account
2. Ask 10 questions
3. On the 11th question, you should see: "You have reached your limit of 10 questions"

## Managing Users

### View User Status

```bash
python admin/manage_users.py view user@example.com
```

Output:
```
📊 User Details
   Email: user@example.com
   User ID: abc123...
   
💳 Subscription
   Tier: FREE
   Questions Asked: 8
   Questions Remaining: 2
```

### Upgrade User to Pro

```bash
python admin/manage_users.py upgrade user@example.com
```

Output:
```
✅ Upgraded user@example.com to Pro tier!
   User ID: abc123...
   Unlimited questions enabled
```

### List All Users

```bash
python admin/manage_users.py list
```

Output:
```
📋 All Users (5 total)

Email                          Tier     Used   Limit    Remaining
----------------------------------------------------------------------
user1@example.com              free     8      10       2
user2@example.com              pro      45     999999   999954
user3@example.com              free     10     10       0
```

### Reset Usage Counter

If you want to give a user more free questions:

```bash
python admin/manage_users.py reset user@example.com
```

### Downgrade User

```bash
python admin/manage_users.py downgrade user@example.com
```

## Manual DynamoDB Updates

You can also manage users directly in the AWS Console:

1. Go to **DynamoDB Console**
2. Open table: `financial-helper-profiles`
3. Find user by `userId` (their Cognito sub)
4. Edit item:
   - `subscriptionTier`: "free" or "pro"
   - `questionsLimit`: 10 or 999999
   - `questionsAsked`: current count (reset to 0 if needed)

## Changing the Free Tier Limit

To change from 10 to a different number:

1. Edit `lambda/advisor_handler.py`:
   ```python
   FREE_TIER_LIMIT = 20  # Change to your desired limit
   ```

2. Edit `lambda/profile_handler.py`:
   ```python
   profile_data['questionsLimit'] = 20  # Change to match
   ```

3. Redeploy both Lambdas

4. Update existing users (optional):
   ```bash
   aws dynamodb update-item \
     --table-name financial-helper-profiles \
     --key '{"userId": {"S": "USER_ID"}}' \
     --update-expression "SET questionsLimit = :limit" \
     --expression-attribute-values '{":limit": {"N": "20"}}'
   ```

## Frontend Integration

The frontend will automatically show usage information after each question:
- Questions remaining
- Upgrade message when limit is reached

The API response now includes:
```json
{
  "success": true,
  "advice": "...",
  "usage": {
    "questionsAsked": 8,
    "questionsLimit": 10,
    "questionsRemaining": 2
  }
}
```

## Monitoring Usage

### CloudWatch Query

Monitor question usage:

```
fields @timestamp, userId, questionsAsked, questionsLimit
| filter @message like /Generating advice/
| stats count() by userId
```

### Find Users Near Limit

```bash
aws dynamodb scan \
  --table-name financial-helper-profiles \
  --filter-expression "subscriptionTier = :free AND questionsAsked >= :threshold" \
  --expression-attribute-values '{":free": {"S": "free"}, ":threshold": {"N": "8"}}'
```

## Cost Savings

With 10 questions per free user:
- **Before**: Unlimited questions = unpredictable costs
- **After**: Max 10 questions per user = predictable costs
- **Bedrock cost**: ~$0.03 per question × 10 = $0.30 per user max

## Future Enhancements

Consider adding:
1. **Email notifications** when users reach 8/10 questions
2. **Payment integration** (Stripe, PayPal) for automatic upgrades
3. **Monthly reset** for free tier (10 questions per month instead of lifetime)
4. **Usage dashboard** in the frontend
5. **Different tiers** (Basic: 10, Plus: 50, Pro: Unlimited)

## Troubleshooting

### User says they're blocked but shouldn't be

Check their status:
```bash
python admin/manage_users.py view user@example.com
```

Reset if needed:
```bash
python admin/manage_users.py reset user@example.com
```

### Admin script can't find user

Make sure:
1. User Pool ID is correct in the script
2. User has actually signed up (exists in Cognito)
3. AWS credentials are configured (`aws configure`)

### Usage counter not incrementing

Check CloudWatch logs for the advisor Lambda:
```bash
aws logs tail /aws/lambda/financial-helper-advisor --follow
```

Look for errors in the `increment_usage` function.
