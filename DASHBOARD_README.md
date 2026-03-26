# Financial Helper App - CloudWatch Dashboard

This dashboard provides real-time monitoring of your Financial Helper application's key metrics.

## 📊 Metrics Tracked

### 1. **Total Registered Accounts**
- Shows the total number of user profiles stored in DynamoDB
- Updates every 5 minutes
- Source: DynamoDB `ItemCount` metric

### 2. **Total Advice Uses**
- Shows the total number of advice requests in the last 30 days
- Tracks how many times users have asked for financial advice
- Source: Lambda invocation count for `financial-helper-advisor`

### 3. **Advice Requests Trend (24 Hours)**
- Time-series graph showing advice request patterns
- Helps identify peak usage times
- Hourly granularity

### 4. **Performance Metrics**
- Average and maximum response times for advice generation
- Helps monitor Bedrock AI performance
- Typical range: 10-30 seconds

### 5. **Error Tracking**
- Monitors errors in both advisor and profile Lambda functions
- Helps identify issues quickly
- Should remain at or near zero

### 6. **Profile Activity**
- Shows read/write operations on the profiles table
- Tracks user profile updates and retrievals

### 7. **Success Rate**
- Log-based metric showing successful advice generations
- 5-minute intervals

### 8. **New Registrations**
- Tracks new user profile creations
- Hourly intervals

## 🚀 Quick Setup

### Prerequisites
- AWS CLI installed and configured
- Appropriate IAM permissions for CloudWatch
- Financial Helper app deployed (Lambda functions and DynamoDB table)

### Deploy the Dashboard

```bash
cd "Financial Helper App"
./setup_dashboard.sh
```

The script will:
1. Verify your AWS credentials
2. Check that Lambda functions and DynamoDB table exist
3. Create the CloudWatch dashboard
4. Provide a direct link to view it

### Manual Setup

If you prefer to create the dashboard manually:

1. Go to AWS CloudWatch Console
2. Navigate to Dashboards
3. Click "Create dashboard"
4. Name it "FinancialHelperApp-Metrics"
5. Import the configuration from `cloudwatch_dashboard.json`

## 🔧 Configuration

The dashboard is configured for:
- **Region**: `us-east-1`
- **Advisor Lambda**: `financial-helper-advisor`
- **Profile Lambda**: `financial-helper-profile`
- **DynamoDB Table**: `financial-helper-profiles`

If your resources have different names, edit the variables in `setup_dashboard.sh`:

```bash
ADVISOR_LAMBDA_NAME="your-advisor-lambda-name"
PROFILE_LAMBDA_NAME="your-profile-lambda-name"
DYNAMODB_TABLE_NAME="your-table-name"
REGION="your-region"
```

## 📈 Understanding the Metrics

### Total Registered Accounts
This metric comes from DynamoDB's `ItemCount`. Each item represents one user profile.

**Note**: DynamoDB updates this metric approximately every 6 hours, so new registrations may not appear immediately.

For real-time counts, you can query DynamoDB directly:
```bash
aws dynamodb scan --table-name financial-helper-profiles --select COUNT
```

### Total Advice Uses
This is the sum of all Lambda invocations for the advisor function. Each invocation = one advice request.

**Calculation**: 
- Period: Last 30 days
- Metric: Lambda Invocations (Sum)
- Excludes errors and timeouts

### Performance Benchmarks
- **Good**: < 20 seconds average
- **Acceptable**: 20-30 seconds average
- **Needs attention**: > 30 seconds average

High response times may indicate:
- Bedrock throttling
- Cold Lambda starts
- Network issues

## 🔍 Troubleshooting

### Dashboard shows no data
1. **Check if resources exist**:
   ```bash
   aws lambda list-functions | grep financial-helper
   aws dynamodb list-tables | grep financial-helper
   ```

2. **Verify metrics are being generated**:
   - Use the app to create a profile and ask a question
   - Wait 5-10 minutes for metrics to populate
   - Refresh the dashboard

3. **Check CloudWatch Logs**:
   ```bash
   aws logs tail /aws/lambda/financial-helper-advisor --follow
   ```

### ItemCount shows zero but users exist
DynamoDB's `ItemCount` metric updates slowly. Use this query for real-time counts:
```bash
aws dynamodb scan \
  --table-name financial-helper-profiles \
  --select COUNT \
  --region us-east-1
```

### Metrics show unexpected values
1. Check the time range on the dashboard (top right)
2. Verify you're looking at the correct region
3. Check for Lambda errors in CloudWatch Logs

## 🎯 Setting Up Alarms

You can create CloudWatch alarms based on these metrics:

### High Error Rate Alert
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name financial-helper-high-errors \
  --alarm-description "Alert when error rate exceeds 5%" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=financial-helper-advisor \
  --evaluation-periods 2
```

### Slow Response Time Alert
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name financial-helper-slow-response \
  --alarm-description "Alert when response time exceeds 45 seconds" \
  --metric-name Duration \
  --namespace AWS/Lambda \
  --statistic Average \
  --period 300 \
  --threshold 45000 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=financial-helper-advisor \
  --evaluation-periods 2
```

## 💰 Cost Considerations

CloudWatch dashboard costs:
- **First 3 dashboards**: Free
- **Additional dashboards**: $3/month each
- **Custom metrics**: $0.30 per metric per month
- **Log queries**: $0.005 per GB scanned

This dashboard uses standard AWS metrics (free) and log insights queries (minimal cost).

**Estimated monthly cost**: < $1

## 🔗 Useful Links

- [View Dashboard](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=FinancialHelperApp-Metrics)
- [CloudWatch Logs - Advisor](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/$252Faws$252Flambda$252Ffinancial-helper-advisor)
- [CloudWatch Logs - Profile](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/$252Faws$252Flambda$252Ffinancial-helper-profile)
- [DynamoDB Table](https://console.aws.amazon.com/dynamodbv2/home?region=us-east-1#table?name=financial-helper-profiles)

## 📝 Customization

### Add More Widgets

Edit `cloudwatch_dashboard.json` to add custom widgets. Common additions:

**API Gateway Metrics**:
```json
{
  "type": "metric",
  "properties": {
    "metrics": [
      ["AWS/ApiGateway", "Count", {"stat": "Sum"}]
    ],
    "title": "API Requests"
  }
}
```

**Cognito User Pool**:
```json
{
  "type": "metric",
  "properties": {
    "metrics": [
      ["AWS/Cognito", "UserAuthentication", {"stat": "Sum"}]
    ],
    "title": "User Logins"
  }
}
```

### Change Time Ranges

Modify the `period` value in the dashboard JSON:
- `300` = 5 minutes
- `3600` = 1 hour
- `86400` = 1 day
- `2592000` = 30 days

## 🆘 Support

If you encounter issues:
1. Check CloudWatch Logs for errors
2. Verify IAM permissions
3. Ensure all resources are in the same region
4. Review the [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) guide
