# Troubleshooting Guide

## "Failed to get advice" Error

If you're getting a "Failed to get advice" error, follow these steps:

### 1. Check Browser Console
Open your browser's Developer Tools (F12) and check the Console tab for detailed error messages.

Look for:
- Response status code
- Error messages from the API
- Network errors

### 2. Verify Lambda Deployment

Make sure you've deployed the updated Lambda functions:

```bash
cd "Financial Helper App/lambda"

# Update advisor Lambda
zip advisor_handler.zip advisor_handler.py
# Upload to AWS Lambda Console: financial-helper-advisor

# Update profile Lambda (if needed)
zip profile_handler.zip profile_handler.py
# Upload to AWS Lambda Console: financial-helper-profile
```

### 3. Check CloudWatch Logs

1. Go to AWS CloudWatch Console
2. Navigate to Log Groups
3. Find `/aws/lambda/financial-helper-advisor`
4. Check the latest log stream for errors

Common errors:
- **Bedrock permissions**: Lambda needs `bedrock:InvokeModel` permission
- **Timeout**: Lambda may need more time (increase timeout to 60 seconds)
- **Memory**: Lambda may need more memory (increase to 512 MB)

### 4. Verify Lambda Configuration

**Timeout**: Should be at least 30-60 seconds (Bedrock can be slow)
**Memory**: Should be at least 256 MB (512 MB recommended)
**Environment Variables**: Check if any are required

### 5. Test Lambda Directly

Test the Lambda function directly in AWS Console with this payload:

```json
{
  "httpMethod": "POST",
  "body": "{\"question\":\"Should I save or invest?\",\"profile\":{\"annualIncome\":\"75000\",\"monthlyExpenses\":\"3000\",\"currentSavings\":\"10000\",\"totalDebt\":\"5000\",\"riskTolerance\":\"moderate\"}}",
  "requestContext": {
    "authorizer": {
      "claims": {
        "sub": "test-user-123"
      }
    }
  }
}
```

### 6. Check IAM Permissions

The Lambda execution role needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

### 7. Common Issues

**Issue**: "Unauthorized" error
**Solution**: Check that Cognito authorizer is properly configured on API Gateway

**Issue**: "CORS error"
**Solution**: Verify CORS is enabled on API Gateway and OPTIONS method exists

**Issue**: "Timeout"
**Solution**: Increase Lambda timeout to 60 seconds

**Issue**: "Empty response"
**Solution**: Check CloudWatch logs for Bedrock errors, verify model ID is correct

**Issue**: "Model not found"
**Solution**: Verify you have access to Claude 3 Sonnet in your AWS region. You may need to request model access in Bedrock console.

### 8. Enable Bedrock Model Access

1. Go to AWS Bedrock Console
2. Click "Model access" in the left sidebar
3. Click "Manage model access"
4. Enable "Claude 3 Sonnet"
5. Wait for approval (usually instant)

### 9. Check API Gateway

1. Go to API Gateway Console
2. Find your API
3. Check the `/advice` POST method exists
4. Verify the Cognito authorizer is attached
5. Check Lambda integration is correct
6. Deploy the API to the stage

### 10. Frontend Configuration

Verify `app.js` has the correct values:

```javascript
const AWS_CONFIG = {
    region: 'us-east-1',
    userPoolId: 'YOUR_USER_POOL_ID',
    clientId: 'YOUR_CLIENT_ID',
    apiEndpoint: 'YOUR_API_GATEWAY_URL'
};
```

## Still Having Issues?

1. Clear browser cache and reload
2. Try a different browser
3. Check if you can save your profile (tests profile Lambda)
4. Look at Network tab in browser DevTools to see the actual API response
