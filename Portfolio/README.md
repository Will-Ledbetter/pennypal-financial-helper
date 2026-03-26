# Lambda Functions - Portfolio Examples

These are sanitized, generic versions of AWS Lambda functions for portfolio demonstration purposes.

## Files

### lambda_profile_handler.py
Generic CRUD Lambda for managing user profiles in DynamoDB.

**Features:**
- GET endpoint to retrieve user profile
- POST endpoint to create/update profile
- JWT token authentication
- DynamoDB integration
- CORS support
- Error handling

**Use Cases:**
- User profile management
- Settings storage
- Preferences management
- Any CRUD operations

### lambda_ai_advisor.py
Generic AI advisor Lambda using Amazon Bedrock.

**Features:**
- Generates personalized advice using AI
- Integrates with Amazon Bedrock (Claude)
- Context-aware responses
- JWT token authentication
- Error handling and logging
- Customizable prompts

**Use Cases:**
- AI chatbots
- Recommendation systems
- Personalized advice engines
- Content generation

## Architecture

```
User → API Gateway → Lambda → DynamoDB/Bedrock
         (Auth)      (Logic)   (Data/AI)
```

## Setup Requirements

### AWS Services Needed
1. **AWS Lambda** - Serverless compute
2. **API Gateway** - REST API endpoints
3. **DynamoDB** - NoSQL database
4. **Cognito** - User authentication
5. **Bedrock** - AI model access
6. **CloudWatch** - Logging

### IAM Permissions

**Profile Handler Lambda:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/your-table"
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

**AI Advisor Lambda:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "bedrock:InvokeModel",
      "Resource": "arn:aws:bedrock:*::foundation-model/*"
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

## Deployment

### 1. Package Lambda
```bash
# For profile handler
zip lambda_profile_handler.zip lambda_profile_handler.py

# For AI advisor
zip lambda_ai_advisor.zip lambda_ai_advisor.py
```

### 2. Create Lambda Functions
```bash
# Profile handler
aws lambda create-function \
  --function-name profile-handler \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT:role/lambda-role \
  --handler lambda_profile_handler.lambda_handler \
  --zip-file fileb://lambda_profile_handler.zip

# AI advisor
aws lambda create-function \
  --function-name ai-advisor \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT:role/lambda-role \
  --handler lambda_ai_advisor.lambda_handler \
  --zip-file fileb://lambda_ai_advisor.zip \
  --timeout 60 \
  --memory-size 512
```

### 3. Set Environment Variables
```bash
# Profile handler
aws lambda update-function-configuration \
  --function-name profile-handler \
  --environment Variables={PROFILES_TABLE=your-table-name}

# AI advisor
aws lambda update-function-configuration \
  --function-name ai-advisor \
  --environment Variables={MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0}
```

### 4. Create API Gateway
- Create REST API
- Add resources: `/profile`, `/advice`
- Add methods: GET, POST
- Configure Cognito authorizer
- Enable CORS
- Deploy to stage

## Customization

### Profile Handler
Edit the `profile_data` dictionary in `save_profile()` to match your data structure:

```python
profile_data = {
    'userId': user_id,
    'yourField1': body.get('yourField1', ''),
    'yourField2': body.get('yourField2', ''),
    # Add your fields here
    'updatedAt': datetime.utcnow().isoformat()
}
```

### AI Advisor
Edit the `build_context()` function to format your user data:

```python
def build_context(user_context):
    context = f"""
    - Your Field 1: {user_context.get('field1')}
    - Your Field 2: {user_context.get('field2')}
    """
    return context
```

Edit the prompt in `generate_advice()` to match your use case.

## Testing

### Test Profile Handler
```bash
aws lambda invoke \
  --function-name profile-handler \
  --payload '{"httpMethod":"GET","requestContext":{"authorizer":{"claims":{"sub":"test-user"}}}}' \
  response.json
```

### Test AI Advisor
```bash
aws lambda invoke \
  --function-name ai-advisor \
  --payload '{"httpMethod":"POST","body":"{\"question\":\"Test?\",\"context\":{}}","requestContext":{"authorizer":{"claims":{"sub":"test-user"}}}}' \
  response.json
```

## Monitoring

### CloudWatch Logs
```bash
# View logs
aws logs tail /aws/lambda/profile-handler --follow
aws logs tail /aws/lambda/ai-advisor --follow
```

### Metrics to Monitor
- Invocations
- Errors
- Duration
- Throttles
- Concurrent executions

## Cost Optimization

### Profile Handler
- Use DynamoDB on-demand pricing
- Set appropriate Lambda memory (128-256 MB)
- Use Lambda reserved concurrency if needed

### AI Advisor
- Use Claude Haiku (cheaper than Sonnet)
- Set max_tokens appropriately
- Cache responses if possible
- Monitor Bedrock costs (main expense)

## Security Best Practices

1. **Never hardcode credentials** - Use environment variables
2. **Use least privilege IAM** - Only grant necessary permissions
3. **Validate all inputs** - Check for malicious data
4. **Enable CloudWatch logs** - Monitor for suspicious activity
5. **Use VPC** - If accessing private resources
6. **Encrypt data** - Use DynamoDB encryption at rest
7. **Rate limiting** - Implement in API Gateway

## Troubleshooting

### Common Issues

**"Unauthorized" error:**
- Check Cognito authorizer configuration
- Verify JWT token is valid
- Check token expiration

**"Internal server error":**
- Check CloudWatch logs
- Verify IAM permissions
- Check environment variables

**"Timeout" error:**
- Increase Lambda timeout (especially for AI advisor)
- Check Bedrock response time
- Optimize code

**DynamoDB errors:**
- Verify table exists
- Check IAM permissions
- Verify table name in environment variable

## License

These examples are provided for educational and portfolio purposes.
Customize and use as needed for your projects.

## Notes

- These are simplified examples for demonstration
- Production code should include more error handling
- Add input validation based on your needs
- Consider adding rate limiting
- Implement proper logging and monitoring
- Add unit tests before production use
