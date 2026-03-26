# API Gateway Security Setup

## Quick Answer

You need **TWO security layers**:

### 1. Resource Policy (API Gateway Level)
Allows traffic to reach your API

### 2. Cognito Authorizer (Endpoint Level)
Protects individual endpoints - only authenticated users can access

## Step-by-Step Setup

### Step 1: Add Resource Policy

**In AWS Console:**
1. Go to API Gateway → Your API
2. Click "Resource Policy" in left sidebar
3. Paste this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "execute-api:Invoke",
      "Resource": "arn:aws:execute-api:*:*:*"
    }
  ]
}
```

4. Click "Save"

**What this does:** Allows anyone to reach your API Gateway (but Cognito still protects the actual endpoints)

### Step 2: Give API Gateway Permission to Invoke Lambda

**Option A: Using AWS Console (Easier)**

For each Lambda function:
1. Go to Lambda → Your function (e.g., `financial-helper-profile`)
2. Configuration tab → Permissions
3. Scroll to "Resource-based policy statements"
4. Click "Add permissions"
5. Fill in:
   - **Service**: API Gateway
   - **Statement ID**: `apigateway-invoke`
   - **Principal**: `apigateway.amazonaws.com`
   - **Source ARN**: `arn:aws:execute-api:REGION:ACCOUNT_ID:API_ID/*`
     - Find this in API Gateway → Your API → ARN at top
     - Example: `arn:aws:execute-api:us-east-1:123456789012:abc123xyz/*`
6. Click "Save"

Repeat for both Lambda functions:
- `financial-helper-profile`
- `financial-helper-advisor`

**Option B: Using AWS CLI**

```bash
# For Profile Lambda
aws lambda add-permission \
  --function-name financial-helper-profile \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:YOUR_ACCOUNT_ID:YOUR_API_ID/*"

# For Advisor Lambda
aws lambda add-permission \
  --function-name financial-helper-advisor \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:us-east-1:YOUR_ACCOUNT_ID:YOUR_API_ID/*"
```

### Step 3: Verify Cognito Authorizer is Attached

1. Go to API Gateway → Your API → Resources
2. Click on each method (GET /profile, POST /profile, POST /advice)
3. Click "Method Request"
4. Verify "Authorization" shows your Cognito authorizer
5. If not, click the pencil icon and select your authorizer

### Step 4: Deploy API

After making any changes:
1. Actions → Deploy API
2. Select stage: `prod`
3. Deploy

## Security Summary

Your API has **3 layers of security**:

1. ✅ **Resource Policy**: Controls who can reach API Gateway
2. ✅ **Cognito Authorizer**: Validates JWT tokens on each request
3. ✅ **Lambda Permissions**: Allows API Gateway to invoke your functions

## Testing Security

### Test 1: Unauthenticated Request (Should Fail)
```bash
curl -X POST https://YOUR_API_URL/prod/advice \
  -H "Content-Type: application/json" \
  -d '{"question":"test"}'
```
**Expected**: `{"message":"Unauthorized"}` (401 error)

### Test 2: Authenticated Request (Should Work)
1. Login to your app
2. Open browser DevTools → Network tab
3. Ask a question
4. Check the request - should see `Authorization: Bearer eyJ...` header
5. Should get a successful response

## Common Issues

### "Missing Authentication Token"
- Resource policy not set
- API not deployed
- Wrong URL

### "Unauthorized" (401)
- Cognito authorizer not attached to method
- Invalid/expired JWT token
- Wrong User Pool ID in authorizer

### "Internal Server Error" (500)
- Lambda doesn't have permission to be invoked by API Gateway
- Check Lambda → Configuration → Permissions

### "Forbidden" (403)
- Resource policy is too restrictive
- Check API Gateway → Resource Policy

## Production Security Enhancements

For production, consider:

1. **Restrict Resource Policy by IP**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "execute-api:Invoke",
      "Resource": "arn:aws:execute-api:*:*:*",
      "Condition": {
        "IpAddress": {
          "aws:SourceIp": ["YOUR_IP_RANGE"]
        }
      }
    }
  ]
}
```

2. **Add Rate Limiting**:
   - API Gateway → Usage Plans
   - Set throttle limits (e.g., 100 requests/second)

3. **Enable AWS WAF**:
   - Protects against common web exploits
   - Costs extra but worth it for production

4. **Add API Keys** (optional extra layer):
   - API Gateway → API Keys
   - Require API key header on requests

## Need Help?

If you get errors:
1. Check CloudWatch Logs for Lambda functions
2. Check API Gateway → Stages → Logs
3. Verify all 3 security layers are configured
4. Make sure API is deployed after changes
