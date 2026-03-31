# Financial Helper App

A personalized AI-powered financial advisor that remembers your information and provides tailored advice.

## LinkedIn Post

[See it in action](https://www.linkedin.com/posts/will-ledbetter-114318167_aws-amazonkiro-awskiro-activity-7403131213701488641-21KW?utm_source=share&utm_medium=member_desktop&rcm=ACoAACe8W6ABz_yW6tZUwf4zTku75hhXakj6lxU)

## Architecture

```
Frontend (Amplify Hosting)
    ↓
Cognito (User Authentication)
    ↓
API Gateway
    ↓
Lambda Functions
    ↓
DynamoDB (User Profiles) + Bedrock (AI Advice)
```

## Features

- **User Authentication**: Secure login with AWS Cognito
- **Profile Management**: Store and update financial information
- **AI-Powered Advice**: Personalized recommendations based on your profile
- **Session Memory**: App remembers your information across sessions
- **Responsive Design**: Works on desktop and mobile

## Tech Stack

- **Frontend**: HTML, CSS, JavaScript
- **Hosting**: AWS Amplify
- **Authentication**: AWS Cognito
- **Backend**: AWS Lambda (Python)
- **Database**: DynamoDB
- **AI**: Amazon Bedrock (Claude 3)
- **API**: API Gateway

## User Profile Data Stored

- Income information
- Monthly expenses
- Savings goals
- Debt information
- Investment preferences
- Risk tolerance
- Financial goals

## Setup Instructions

See `DEPLOYMENT.md` for detailed setup instructions.

## File Structure

```
Financial Helper App/
├── frontend/
│   ├── index.html          # Main app interface
│   ├── login.html          # Login/signup page
│   ├── styles.css          # Styling
│   └── app.js              # Frontend logic
├── lambda/
│   ├── auth_handler.py     # Authentication logic
│   ├── profile_handler.py  # Profile CRUD operations
│   └── advisor_handler.py  # AI advice generation
├── amplify.yml             # Amplify build config
└── README.md
```

## Cost Estimate

- Cognito: Free tier (50,000 MAUs)
- DynamoDB: ~$0.25/month (free tier)
- Lambda: ~$0.20/month (free tier)
- Bedrock: ~$0.02 per advice request
- Amplify: Free tier (1000 build minutes)

**Total**: ~$5-10/month for moderate usage
