## Financial Helper App - Deployment Guide

Complete step-by-step guide to deploy your financial helper app on AWS Amplify.

## Prerequisites

- AWS Account
- AWS CLI installed and configured
- Basic knowledge of AWS services

## Step 1: Create DynamoDB Table

1. Go to AWS Console → DynamoDB
2. Click "Create table"
3. Settings:
   - Table name: `financial-helper-profiles`
   - Partition key: `userId` (String)
   - Use default settings for everything else
4. Click "Create table"

## Step 2: Create Cognito User Pool

1. Go to AWS Console → Cognito
2. Click "Create user pool"
3. Configure sign-in:
   - Provider types: Cognito user pool
   - Cognito user pool sign-in options: Email
4. Security requirements:
   - Password policy: Cognito defaults (or customize)
   - Multi-factor authentication: Optional (recommended: OFF for development)
5. Sign-up experience:
   - Self-service sign-up: Enabled
   - Required attributes: name, email
6. Message delivery:
   - Email provider: Send email with Cognito
7. Integrate your app:
   - User pool name: `financial-helper-users`
   - App client name: `financial-helper-client`
   - Don't generate a client secret
8. Review and create

**Save these values:**
- User Pool ID (e.g., `us-east-1_XXXXXXXXX`)
- App Client ID (e.g., `1234567890abcdefghijklmnop`)

## Step 3: Create Lambda Functions

### A. Create IAM Role for Lambda

1. Go to IAM → Roles → Create role
2. Trusted entity: Lambda
3. Permissions:
   - `AmazonDynamoDBFullAccess`
   - `AmazonBedrockFullAccess`
   - `CloudWatchLogsFullAccess`
4. Role name: `financial-helper-lambda-role`

### B. Create Profile Handler Lambda

1. Go to Lambda → Create function
2. Function name: `financial-helper-profile`
3. Runtime: Python 3.14 (or latest available)
4. Execution role: Use existing role → `financial-helper-lambda-role`
5. Create function
6. Copy code from `lambda/profile_handler.py`
7. Configuration:
   - Environment variables:
     - `PROFILES_TABLE` = `financial-helper-profiles`
   - Timeout: 30 seconds
8. Deploy

### C. Create Advisor Handler Lambda

1. Go to Lambda → Create function
2. Function name: `financial-helper-advisor`
3. Runtime: Python 3.14 (or latest available)
4. Execution role: Use existing role → `financial-helper-lambda-role`
5. Create function
6. Copy code from `lambda/advisor_handler.py`
7. Configuration:
   - Timeout: 60 seconds (Bedrock can take time)
   - Memory: 512 MB
8. Deploy

## Step 4: Create API Gateway

1. Go to API Gateway → Create API
2. Choose "REST API" (not private)
3. API name: `financial-helper-api`
4. Create API

### A. Create Cognito Authorizer

1. In your API, go to "Authorizers"
2. Create New Authorizer:
   - Name: `cognito-authorizer`
   - Type: Cognito
   - Cognito User Pool: Select your user pool
   - Token Source: `Authorization`
3. Create

### B. Create Resources and Methods

#### Profile Resource:

1. Actions → Create Resource
   - Resource Name: `profile`
   - Resource Path: `/profile`
   - Enable CORS: Yes
2. Create Resource
3. Select `/profile` → Actions → Create Method → GET
   - Integration type: Lambda Function
   - Lambda Function: `financial-helper-profile`
   - Save
   - Method Request → Authorization: `cognito-authorizer`
4. Select `/profile` → Actions → Create Method → POST
   - Integration type: Lambda Function
   - Lambda Function: `financial-helper-profile`
   - Save
   - Method Request → Authorization: `cognito-authorizer`
5. Select `/profile` → Actions → Create Method → OPTIONS
   - Integration type: Mock
   - Save

#### Advice Resource:

1. Actions → Create Resource
   - Resource Name: `advice`
   - Resource Path: `/advice`
   - Enable CORS: Yes
2. Create Resource
3. Select `/advice` → Actions → Create Method → POST
   - Integration type: Lambda Function
   - Lambda Function: `financial-helper-advisor`
   - Save
   - Method Request → Authorization: `cognito-authorizer`
4. Select `/advice` → Actions → Create Method → OPTIONS
   - Integration type: Mock
   - Save

### C. Configure Resource Policy (Important!)

1. In your API, go to "Resource Policy"
2. Add this policy:
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
3. Save

**Note**: This allows public access but Cognito authorizer still protects your endpoints.

### D. Add Lambda Permissions

For each Lambda function, add API Gateway permission:

**Profile Lambda:**
```bash
aws lambda add-permission \
  --function-name financial-helper-profile \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:REGION:ACCOUNT_ID:API_ID/*"
```

**Advisor Lambda:**
```bash
aws lambda add-permission \
  --function-name financial-helper-advisor \
  --statement-id apigateway-invoke \
  --action lambda:InvokeFunction \
  --principal apigateway.amazonaws.com \
  --source-arn "arn:aws:execute-api:REGION:ACCOUNT_ID:API_ID/*"
```

Replace:
- `REGION` with your region (e.g., `us-east-1`)
- `ACCOUNT_ID` with your AWS account ID
- `API_ID` with your API Gateway ID

**Or do it in Console:**
1. Lambda → Configuration → Permissions
2. Resource-based policy statements → Add permissions
3. Service: API Gateway
4. Source ARN: Your API Gateway ARN
5. Save

### E. Configure Security Policy

1. In your API, go to "Settings" (left sidebar)
2. Find "Minimum TLS Version" or "Security Policy"
3. Select: **TLS 1.2** (recommended)
4. Save Changes

**What this does:** Encrypts all data in transit between clients and your API

### F. Deploy API

1. Actions → Deploy API
2. Deployment stage: New Stage
3. Stage name: `prod`
4. Deploy

**Save the Invoke URL** (e.g., `https://abc123.execute-api.us-east-1.amazonaws.com/prod`)

## Step 5: Update Frontend Configuration

Update these files with your AWS values:

### frontend/login.html (line 18-21):
```javascript
const AWS_CONFIG = {
    region: 'us-east-1',
    userPoolId: 'YOUR_USER_POOL_ID',  // From Step 2
    clientId: 'YOUR_CLIENT_ID'         // From Step 2
};
```

### frontend/app.js (line 2-6):
```javascript
const AWS_CONFIG = {
    region: 'us-east-1',
    userPoolId: 'YOUR_USER_POOL_ID',      // From Step 2
    clientId: 'YOUR_CLIENT_ID',            // From Step 2
    apiEndpoint: 'YOUR_API_GATEWAY_URL'    // From Step 4 (without /prod)
};
```

Example:
```javascript
apiEndpoint: 'https://abc123.execute-api.us-east-1.amazonaws.com/prod'
```

## Step 6: Deploy to Amplify

### A. Create GitHub Repository (Optional but Recommended)

1. Create a new GitHub repository
2. Push your code:
```bash
cd "Financial Helper App"
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/financial-helper.git
git push -u origin main
```

### B. Deploy to Amplify

1. Go to AWS Amplify → Get Started
2. Choose "Host web app"
3. Connect repository:
   - GitHub (or upload files directly)
   - Authorize AWS Amplify
   - Select your repository
   - Select branch: `main`
4. Build settings:
   - App name: `financial-helper`
   - Environment: `prod`
   - Build settings: Auto-detected (or use custom)
5. Review and Save and Deploy

### C. Custom Build Settings (if needed)

Create `amplify.yml` in root:
```yaml
version: 1
frontend:
  phases:
    build:
      commands:
        - echo "No build needed for static site"
  artifacts:
    baseDirectory: /frontend
    files:
      - '**/*'
  cache:
    paths: []
```

## Step 7: Test Your App

1. Go to your Amplify URL (e.g., `https://main.d1234567890.amplifyapp.com`)
2. Create an account
3. Verify your email
4. Login
5. Set up your financial profile
6. Ask a question!

## Troubleshooting

### CORS Errors
- Make sure you enabled CORS on all API Gateway methods
- Redeploy your API after making changes

### Authentication Errors
- Verify User Pool ID and Client ID are correct
- Check that Cognito authorizer is attached to API methods

### Lambda Errors
- Check CloudWatch Logs for each Lambda function
- Verify IAM role has correct permissions
- Check environment variables are set

### Bedrock Access
- Ensure your AWS account has Bedrock access enabled
- Request access to Claude 3 Sonnet model if needed
- Check IAM role has `AmazonBedrockFullAccess`

## Cost Optimization

- Use AWS Free Tier where available
- Set up billing alerts
- Monitor CloudWatch metrics
- Consider using DynamoDB on-demand pricing

## Security Best Practices

1. Enable MFA on Cognito (production)
2. Use HTTPS only (Amplify does this automatically)
3. Implement rate limiting on API Gateway
4. Regularly rotate IAM credentials
5. Enable CloudWatch logging
6. Set up AWS WAF for API protection

## Next Steps

- Add email notifications
- Implement conversation history storage
- Add data export functionality
- Create admin dashboard
- Add more financial calculators
- Implement budget tracking

## Support

For issues or questions:
1. Check CloudWatch Logs
2. Review API Gateway execution logs
3. Test Lambda functions individually
4. Verify all AWS resources are in the same region
