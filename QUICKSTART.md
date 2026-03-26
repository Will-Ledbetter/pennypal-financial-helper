# Financial Helper App - Quick Start

Get your financial advisor app running in 30 minutes!

## What You'll Build

A personalized AI financial advisor that:
- ✅ Remembers user information across sessions
- ✅ Provides personalized advice based on user's financial profile
- ✅ Secure authentication with AWS Cognito
- ✅ Stores data in DynamoDB
- ✅ Uses AI (Claude 3) for intelligent advice
- ✅ Hosted on AWS Amplify

## Architecture Overview

```
User → Amplify (Frontend) → API Gateway → Lambda → DynamoDB + Bedrock
                                ↓
                            Cognito (Auth)
```

## 5-Step Setup

### 1. Create DynamoDB Table (2 min)
```
AWS Console → DynamoDB → Create table
- Name: financial-helper-profiles
- Partition key: userId (String)
→ Create
```

### 2. Create Cognito User Pool (3 min)
```
AWS Console → Cognito → Create user pool
- Sign-in: Email
- Required attributes: name, email
- App client: financial-helper-client (no secret)
→ Create

📝 Save: User Pool ID & Client ID
```

### 3. Create Lambda Functions (10 min)

**A. Create IAM Role:**
```
IAM → Roles → Create role
- Service: Lambda
- Permissions: DynamoDB, Bedrock, CloudWatch
- Name: financial-helper-lambda-role
```

**B. Profile Lambda:**
```
Lambda → Create function
- Name: financial-helper-profile
- Runtime: Python 3.14 (or latest available)
- Role: financial-helper-lambda-role
→ Copy code from lambda/profile_handler.py
→ Add env var: PROFILES_TABLE = financial-helper-profiles
→ Deploy
```

**C. Advisor Lambda:**
```
Lambda → Create function
- Name: financial-helper-advisor
- Runtime: Python 3.14 (or latest available)
- Role: financial-helper-lambda-role
- Timeout: 60 seconds
- Memory: 512 MB
→ Copy code from lambda/advisor_handler.py
→ Deploy
```

### 4. Create API Gateway (10 min)

```
API Gateway → Create REST API
- Name: financial-helper-api

Create Authorizer:
- Type: Cognito
- User Pool: [your pool]
- Token Source: Authorization

Create Resources:
1. /profile (GET, POST with Cognito auth)
2. /advice (POST with Cognito auth)

Deploy API → Stage: prod

📝 Save: Invoke URL
```

### 5. Deploy to Amplify (5 min)

**Update Config Files:**

`frontend/login.html` & `frontend/app.js`:
```javascript
const AWS_CONFIG = {
    region: 'us-east-1',
    userPoolId: 'YOUR_USER_POOL_ID',
    clientId: 'YOUR_CLIENT_ID',
    apiEndpoint: 'YOUR_API_GATEWAY_URL'
};
```

**Deploy:**
```
AWS Amplify → New app → Deploy without Git
→ Upload frontend folder
→ Deploy
```

## Test It Out!

1. Open your Amplify URL
2. Sign up with your email
3. Verify email (check spam folder)
4. Login
5. Fill out your financial profile
6. Ask: "Should I pay off debt or invest?"
7. Get personalized AI advice! 🎉

## Common Issues

**"Unauthorized" error:**
- Check Cognito IDs in config files
- Verify API Gateway has Cognito authorizer

**"CORS" error:**
- Enable CORS on all API methods
- Redeploy API

**"Bedrock access denied":**
- Request Bedrock access in AWS Console
- Enable Claude 3 Sonnet model

## What's Next?

- Customize the UI colors/branding
- Add more financial metrics
- Implement budget tracking
- Add conversation history storage
- Create mobile app version

## Cost Estimate

**Free Tier Usage:**
- Cognito: 50,000 users/month
- DynamoDB: 25 GB storage
- Lambda: 1M requests/month
- Amplify: 1000 build minutes

**Paid Usage:**
- Bedrock: ~$0.02 per advice request
- **Total: $5-10/month** for moderate use

## Need Help?

Check `DEPLOYMENT.md` for detailed instructions!
