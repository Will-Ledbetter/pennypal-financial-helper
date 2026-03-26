# PennyPal Advisor - Architecture & Data Flow

## Complete Question Flow

Here's exactly what happens when a user asks a financial question:

### Step 1: User Authentication
```
User → Browser → Cognito
```
1. User logs in via `login.html`
2. Cognito validates credentials
3. Cognito returns JWT token (idToken)
4. Token stored in browser memory
5. User redirected to `index.html`

### Step 2: Profile Loading
```
Browser → API Gateway → Profile Lambda → DynamoDB
```
1. `app.js` calls `loadUserProfile()`
2. GET request to `/profile` endpoint
3. Includes JWT token in Authorization header
4. API Gateway validates token with Cognito Authorizer
5. Routes to `profile_handler.py` Lambda
6. Lambda extracts userId from token
7. Lambda queries DynamoDB for user profile
8. Returns profile data to browser
9. Profile displayed on page

### Step 3: User Asks Question
```
User types question → Browser validates → Prepares request
```
1. User types question in textarea
2. Clicks "Get Advice" button
3. `askAdvisor()` function triggered
4. Validates question is not empty
5. Validates profile exists
6. Shows loading indicator
7. Disables button to prevent double-clicks

### Step 4: API Request
```
Browser → API Gateway → Cognito → Advisor Lambda
```
1. Browser sends POST to `/advice` endpoint
2. Request includes:
   - Authorization header (JWT token)
   - Body: `{question: "...", profile: {...}}`
3. API Gateway receives request
4. Cognito Authorizer validates JWT token
5. If valid, extracts user claims (userId, email)
6. Routes to `advisor_handler.py` Lambda

### Step 5: Lambda Processing
```
Advisor Lambda → Bedrock AI → Response
```
1. Lambda receives event with:
   - httpMethod: "POST"
   - body: JSON string
   - requestContext: Contains user info from Cognito
2. Lambda extracts userId from token
3. Lambda parses request body
4. Lambda validates:
   - Question exists
   - Profile exists
   - Profile has annualIncome (minimum requirement)
5. Lambda builds context from profile:
   - Income & expenses
   - Savings & investments
   - Debts & obligations
   - Housing situation
   - Goals & risk tolerance
   - Calculates net worth
   - Calculates savings potential
6. Lambda creates prompt for AI:
   - User's financial profile
   - User's specific question
   - Instructions for AI advisor
7. Lambda calls Amazon Bedrock:
   - Model: Claude 3 Haiku
   - Max tokens: 2048
   - Temperature: 0.7
8. Bedrock processes request (10-30 seconds)
9. Bedrock returns AI-generated advice
10. Lambda adds disclaimer
11. Lambda logs success
12. Lambda returns response

### Step 6: Response Handling
```
Advisor Lambda → API Gateway → Browser → Display
```
1. Lambda returns:
   ```json
   {
     "statusCode": 200,
     "headers": {CORS headers},
     "body": "{\"success\": true, \"advice\": \"...\"}"
   }
   ```
2. API Gateway forwards response to browser
3. Browser receives response
4. `app.js` parses JSON
5. Validates advice is not empty
6. Calls `displayAdvice(question, advice)`
7. Formats advice (converts line breaks to HTML)
8. Displays in advice-response div
9. Scrolls to advice
10. Clears question input
11. Adds to conversation history
12. Hides loading indicator
13. Re-enables button

### Step 7: History Display
```
Browser → Local Display (No Server)
```
1. `addToHistory()` creates conversation item
2. Adds question, answer, timestamp
3. Truncates answer to 200 chars for preview
4. Inserts at top of history
5. Keeps only last 5 conversations
6. History stored in browser only (not saved to DB)

---

## Complete Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER BROWSER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  login.html  │  │  index.html  │  │   app.js     │          │
│  │  (Auth UI)   │  │  (Main App)  │  │  (Logic)     │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
└─────────┼──────────────────┼──────────────────┼──────────────────┘
          │                  │                  │
          │ 1. Login         │ 2. Load Profile  │ 3. Ask Question
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AWS COGNITO                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  User Pool: financial-helper-users                         │ │
│  │  - Stores user credentials                                 │ │
│  │  - Issues JWT tokens                                       │ │
│  │  - Validates tokens                                        │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │ Token Validation
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AWS API GATEWAY                               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  API: financial-helper-api                                 │ │
│  │  Stage: prod                                               │ │
│  │                                                            │ │
│  │  Endpoints:                                                │ │
│  │  - GET  /profile  → profile_handler Lambda                │ │
│  │  - POST /profile  → profile_handler Lambda                │ │
│  │  - POST /advice   → advisor_handler Lambda                │ │
│  │                                                            │ │
│  │  Authorizer: Cognito User Pool                            │ │
│  │  CORS: Enabled                                            │ │
│  └────────────────────────────────────────────────────────────┘ │
└───────────────┬─────────────────────────┬───────────────────────┘
                │                         │
    ┌───────────▼──────────┐  ┌──────────▼──────────┐
    │  AWS LAMBDA          │  │  AWS LAMBDA         │
    │  profile_handler.py  │  │  advisor_handler.py │
    │                      │  │                     │
    │  - Get profile       │  │  - Validate request │
    │  - Save profile      │  │  - Build context    │
    │  - CRUD operations   │  │  - Call Bedrock     │
    └──────────┬───────────┘  │  - Return advice    │
               │              └──────────┬──────────┘
               │                         │
               ▼                         ▼
    ┌─────────────────────┐   ┌─────────────────────┐
    │   AWS DYNAMODB      │   │  AWS BEDROCK        │
    │                     │   │                     │
    │  Table:             │   │  Model:             │
    │  financial-helper-  │   │  Claude 3 Haiku     │
    │  profiles           │   │                     │
    │                     │   │  - Processes prompt │
    │  Stores:            │   │  - Generates advice │
    │  - User profiles    │   │  - Returns text     │
    │  - Financial data   │   │                     │
    └─────────────────────┘   └─────────────────────┘
```

---

## Data Structures

### JWT Token (from Cognito)
```json
{
  "sub": "c4086478-6041-706d-698c-d9d7ee126e94",
  "email": "user@example.com",
  "name": "John Doe",
  "cognito:username": "user@example.com",
  "exp": 1701475200,
  "iat": 1701471600
}
```

### Profile Data (in DynamoDB)
```json
{
  "userId": "c4086478-6041-706d-698c-d9d7ee126e94",
  "annualIncome": "75000",
  "monthlyExpenses": "3000",
  "currentSavings": "10000",
  "totalInvestments": "50000",
  "monthlyInvestment": "500",
  "retirementAccounts": "100000",
  "investmentTypes": "Stocks, ETFs, 401k",
  "employerMatch": "5",
  "totalDebt": "25000",
  "savingsGoal": "50000",
  "retirementGoal": "1000000",
  "retirementAge": "65",
  "taxFilingStatus": "married-jointly",
  "housingStatus": "own",
  "housingPayment": "1500",
  "mortgageBalance": "250000",
  "mortgageRate": "3.5",
  "carPayment": "400",
  "carLoanBalance": "15000",
  "otherDebtPayment": "200",
  "otherDebtBalance": "5000",
  "otherDebtDescription": "Credit cards",
  "riskTolerance": "moderate",
  "financialGoals": "Buy a house, retire early",
  "createdAt": "2024-12-01T12:00:00.000Z",
  "updatedAt": "2024-12-01T15:30:00.000Z"
}
```

### API Request (Browser → API Gateway)
```javascript
POST /advice
Headers: {
  "Authorization": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "Content-Type": "application/json"
}
Body: {
  "question": "Should I pay off my car loan or invest more?",
  "profile": {
    "annualIncome": "75000",
    "monthlyExpenses": "3000",
    // ... all profile fields
  }
}
```

### Lambda Event (API Gateway → Lambda)
```json
{
  "httpMethod": "POST",
  "path": "/advice",
  "headers": {
    "Authorization": "Bearer token...",
    "Content-Type": "application/json"
  },
  "body": "{\"question\":\"...\",\"profile\":{...}}",
  "requestContext": {
    "authorizer": {
      "claims": {
        "sub": "c4086478-6041-706d-698c-d9d7ee126e94",
        "email": "user@example.com",
        "cognito:username": "user@example.com"
      }
    }
  }
}
```

### Bedrock Request (Lambda → Bedrock)
```json
{
  "anthropic_version": "bedrock-2023-05-31",
  "max_tokens": 2048,
  "messages": [
    {
      "role": "user",
      "content": "You are a professional financial advisor...\n\nCLIENT'S FINANCIAL PROFILE:\n- Annual Income: $75,000\n...\n\nCLIENT'S QUESTION:\nShould I pay off my car loan or invest more?\n\nPlease provide personalized advice..."
    }
  ],
  "temperature": 0.7
}
```

### Bedrock Response (Bedrock → Lambda)
```json
{
  "content": [
    {
      "type": "text",
      "text": "Based on your financial situation, here's my advice...\n\n1. Your car loan at X% interest...\n2. Investment returns typically...\n3. I recommend..."
    }
  ],
  "stop_reason": "end_turn"
}
```

### API Response (Lambda → Browser)
```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*"
  },
  "body": "{\"success\":true,\"advice\":\"Based on your financial situation...\"}"
}
```

---

## Error Handling Flow

### Authentication Errors
```
No token → Redirect to login.html
Invalid token → Redirect to login.html
Expired token → Redirect to login.html
```

### Validation Errors
```
Empty question → Alert: "Please enter a question"
No profile → Alert: "Please set up your profile first"
Missing annualIncome → 400 error: "User profile is required"
```

### API Errors
```
401 Unauthorized → Token invalid, redirect to login
400 Bad Request → Show error message to user
403 Forbidden → (Not used currently)
500 Internal Server Error → "Failed to get advice. Please try again."
```

### Lambda Errors
```
JSON parse error → 400: "Invalid JSON"
Bedrock error → 500: "Failed to generate advice"
DynamoDB error → 500: "Failed to retrieve/save profile"
```

### Network Errors
```
Timeout → "Request timed out. Please try again."
No internet → "Network error. Check your connection."
CORS error → Check API Gateway CORS configuration
```

---

## Security Flow

### Authentication
1. User credentials never stored in browser
2. Only JWT token stored (in memory, not localStorage)
3. Token expires after 1 hour
4. Token validated on every API request

### Authorization
1. Cognito Authorizer validates token
2. Extracts userId from token
3. User can only access their own data
4. Lambda enforces userId matching

### Data Protection
1. All API calls over HTTPS
2. Passwords hashed by Cognito
3. Financial data encrypted at rest in DynamoDB
4. No sensitive data in logs
5. CORS restricts API access

---

## Performance Characteristics

### Typical Response Times
- Login: 500ms - 1s
- Load profile: 200ms - 500ms
- Ask question: 10s - 30s (Bedrock processing)
- Save profile: 300ms - 700ms

### Bottlenecks
1. **Bedrock AI processing** (10-30s)
   - Most significant delay
   - User sees loading indicator
   - Cannot be optimized much

2. **Cold Lambda starts** (1-3s)
   - First request after idle
   - Subsequent requests faster
   - Mitigated by keeping Lambdas warm

3. **DynamoDB queries** (50-200ms)
   - Generally fast
   - Single-digit millisecond latency
   - Not a bottleneck

### Scalability
- **Cognito**: Handles millions of users
- **API Gateway**: Auto-scales
- **Lambda**: Auto-scales, concurrent executions
- **DynamoDB**: Auto-scales, on-demand pricing
- **Bedrock**: Rate limits apply (check quotas)

---

## Cost Breakdown (Estimated)

### Per User Per Month
- **Cognito**: $0.0055 per MAU (first 50k free)
- **API Gateway**: $0.000001 per request × ~50 requests = $0.00005
- **Lambda**: $0.0000002 per request × 50 = $0.00001
- **DynamoDB**: $0.25 per GB-month (minimal)
- **Bedrock**: ~$0.003 per 1000 tokens × 10 questions = $0.30

**Total per active user**: ~$0.30/month

### At Scale (1000 users)
- Monthly cost: ~$300
- Mostly Bedrock AI costs
- Other services negligible

---

## Monitoring & Logging

### CloudWatch Logs
- `/aws/lambda/financial-helper-profile`
- `/aws/lambda/financial-helper-advisor`

### Key Metrics to Monitor
- Lambda invocations
- Lambda errors
- Lambda duration
- API Gateway 4xx/5xx errors
- Bedrock throttling
- DynamoDB read/write capacity

### Alerts to Set Up
- Lambda error rate > 5%
- API Gateway 5xx rate > 1%
- Lambda duration > 30s
- Bedrock throttling events

---

## Deployment Checklist

### Initial Setup
- [ ] Create Cognito User Pool
- [ ] Create DynamoDB table
- [ ] Deploy Lambda functions
- [ ] Create API Gateway
- [ ] Configure Cognito Authorizer
- [ ] Enable CORS
- [ ] Deploy API to stage
- [ ] Enable Bedrock model access
- [ ] Update frontend config
- [ ] Test end-to-end

### Updates
- [ ] Update Lambda code
- [ ] Zip Lambda functions
- [ ] Upload to AWS Console
- [ ] Test in AWS Console
- [ ] Deploy API if routes changed
- [ ] Update frontend if needed
- [ ] Test in browser
- [ ] Check CloudWatch logs

---

## Troubleshooting Guide

### "Failed to get advice"
1. Check CloudWatch logs for Lambda errors
2. Verify Bedrock model access enabled
3. Check Lambda timeout (should be 60s)
4. Verify IAM permissions for Bedrock

### "Unauthorized" errors
1. Check token is being sent
2. Verify Cognito Authorizer configured
3. Check token hasn't expired
4. Verify User Pool ID matches

### Profile not saving
1. Check CloudWatch logs
2. Verify DynamoDB table exists
3. Check Lambda has DynamoDB permissions
4. Verify table name in environment variable

### CORS errors
1. Enable CORS on API Gateway
2. Add OPTIONS method
3. Deploy API after changes
4. Check CORS headers in Lambda response
