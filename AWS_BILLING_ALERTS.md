# AWS Billing Alerts Setup Guide

## Set Up $25 Cost Alert

### Method 1: AWS Budgets (Recommended)

**Step 1: Go to AWS Budgets**
1. Sign in to AWS Console
2. Search for "Budgets" in the top search bar
3. Click "AWS Budgets"
4. Or go directly to: https://console.aws.amazon.com/billing/home#/budgets

**Step 2: Create Budget**
1. Click "Create budget"
2. Select "Customize (advanced)"
3. Choose "Cost budget"
4. Click "Next"

**Step 3: Set Budget Details**
1. **Budget name**: `PennyPal-Monthly-Budget`
2. **Period**: Monthly
3. **Budget effective dates**: Recurring budget
4. **Start month**: Current month
5. **Budgeting method**: Fixed
6. **Enter your budgeted amount**: `$25.00`
7. Click "Next"

**Step 4: Configure Alerts**
1. Click "Add an alert threshold"

**Alert 1 - Actual Costs:**
- **Threshold**: 80% of budgeted amount ($20)
- **Trigger**: Actual
- **Email recipients**: your@email.com
- Click "Add alert threshold"

**Alert 2 - Forecasted Costs:**
- **Threshold**: 100% of budgeted amount ($25)
- **Trigger**: Forecasted
- **Email recipients**: your@email.com

2. Click "Next"
3. Review and click "Create budget"

**Step 5: Confirm Email**
1. Check your email
2. Click the confirmation link from AWS
3. You're all set!

---

### Method 2: CloudWatch Billing Alarms

**Prerequisites:**
- Must be in **us-east-1** region (N. Virginia)
- Billing metrics only available there

**Step 1: Enable Billing Alerts**
1. Go to AWS Console
2. Click your account name (top right)
3. Click "Billing and Cost Management"
4. Click "Billing preferences" (left sidebar)
5. Check "Receive Billing Alerts"
6. Click "Save preferences"

**Step 2: Create CloudWatch Alarm**
1. Switch to **us-east-1** region (top right)
2. Go to CloudWatch Console
3. Click "Alarms" → "All alarms"
4. Click "Create alarm"

**Step 3: Select Metric**
1. Click "Select metric"
2. Click "Billing"
3. Click "Total Estimated Charge"
4. Check the box for "USD"
5. Click "Select metric"

**Step 4: Configure Alarm**
1. **Statistic**: Maximum
2. **Period**: 6 hours
3. **Threshold type**: Static
4. **Whenever EstimatedCharges is...**: Greater
5. **than...**: `25`
6. Click "Next"

**Step 5: Configure Actions**
1. **Alarm state trigger**: In alarm
2. **Select an SNS topic**: Create new topic
3. **Topic name**: `billing-alerts`
4. **Email endpoint**: your@email.com
5. Click "Create topic"
6. Click "Next"

**Step 6: Name and Create**
1. **Alarm name**: `Billing-Alert-$25`
2. **Alarm description**: `Alert when monthly costs exceed $25`
3. Click "Next"
4. Review and click "Create alarm"

**Step 7: Confirm Email**
1. Check your email
2. Click "Confirm subscription"
3. Done!

---

## Additional Alerts to Set Up

### Alert at $20 (80% threshold)
Follow the same steps but set threshold to `20`

### Alert at $15 (60% threshold)
Follow the same steps but set threshold to `15`

### Alert at $10 (40% threshold)
Follow the same steps but set threshold to `10`

---

## Service-Specific Alerts

### Bedrock Cost Alert
Since Bedrock is your main cost driver:

**Step 1: Create Budget**
1. Go to AWS Budgets
2. Create budget
3. Choose "Cost budget"
4. **Budget name**: `Bedrock-Monthly-Budget`
5. **Amount**: `$20.00`

**Step 2: Add Filters**
1. Under "Budget scope"
2. Click "Add filter"
3. **Dimension**: Service
4. **Values**: Select "Amazon Bedrock"
5. Set alert at 80% ($16)

### Lambda Cost Alert
**Budget name**: `Lambda-Monthly-Budget`
**Amount**: `$2.00`
**Filter**: Service = AWS Lambda

### DynamoDB Cost Alert
**Budget name**: `DynamoDB-Monthly-Budget`
**Amount**: `$1.00`
**Filter**: Service = Amazon DynamoDB

---

## Cost Monitoring Dashboard

### View Current Costs

**Option 1: Cost Explorer**
1. Go to "Cost Management" → "Cost Explorer"
2. Enable Cost Explorer (if not enabled)
3. View costs by service
4. Filter by date range

**Option 2: Billing Dashboard**
1. Go to "Billing and Cost Management"
2. View "Month-to-date costs"
3. See breakdown by service

---

## Automated Cost Reports

### Daily Cost Email

**Step 1: Create Budget Report**
1. Go to AWS Budgets
2. Click "Budget reports" (left sidebar)
3. Click "Create report"
4. **Report name**: `Daily-Cost-Report`
5. **Frequency**: Daily
6. **Email recipients**: your@email.com
7. Select your budgets to include
8. Click "Create report"

### Weekly Summary
Same steps but set **Frequency**: Weekly

---

## Cost Optimization Tips

### 1. Monitor Bedrock Usage
```bash
# Check Bedrock costs
aws ce get-cost-and-usage \
  --time-period Start=2024-12-01,End=2024-12-31 \
  --granularity DAILY \
  --metrics "UnblendedCost" \
  --filter file://bedrock-filter.json
```

**bedrock-filter.json:**
```json
{
  "Dimensions": {
    "Key": "SERVICE",
    "Values": ["Amazon Bedrock"]
  }
}
```

### 2. Set Lambda Concurrency Limits
Prevent runaway costs:
```bash
aws lambda put-function-concurrency \
  --function-name financial-helper-advisor \
  --reserved-concurrent-executions 10
```

### 3. Enable DynamoDB Auto Scaling
Automatically adjust capacity:
1. Go to DynamoDB Console
2. Select your table
3. Click "Additional settings"
4. Enable "Auto scaling"
5. Set min/max capacity

### 4. Use CloudWatch Logs Retention
Reduce storage costs:
```bash
aws logs put-retention-policy \
  --log-group-name /aws/lambda/financial-helper-advisor \
  --retention-in-days 7
```

---

## Emergency Cost Controls

### If Costs Spike Unexpectedly

**Immediate Actions:**

1. **Disable API Gateway**
   - Go to API Gateway Console
   - Select your API
   - Delete the deployment stage
   - This stops all traffic immediately

2. **Disable Lambda Functions**
   ```bash
   # Remove Lambda permissions
   aws lambda remove-permission \
     --function-name financial-helper-advisor \
     --statement-id apigateway-prod-advice
   ```

3. **Check for Unauthorized Usage**
   - Go to CloudWatch Logs
   - Look for unusual patterns
   - Check for API abuse

4. **Contact AWS Support**
   - If costs are due to AWS error
   - They may provide credits

---

## Cost Breakdown Estimates

### Expected Monthly Costs (100 active users)

| Service | Usage | Cost |
|---------|-------|------|
| **Bedrock** | 1000 questions × 2000 tokens | $6.00 |
| **Lambda** | 1000 invocations | $0.20 |
| **API Gateway** | 5000 requests | $0.02 |
| **DynamoDB** | 5000 reads/writes | $0.25 |
| **Cognito** | 100 MAU | Free |
| **CloudWatch** | Logs & metrics | $0.50 |
| **Total** | | **~$7.00** |

### Cost Per User
- Light user (5 questions/month): $0.03
- Average user (10 questions/month): $0.06
- Heavy user (50 questions/month): $0.30

### Break-Even Analysis
At $25/month budget:
- Can support ~400 questions/month
- Or ~40 active users (10 questions each)

---

## Monitoring Commands

### Check Current Month Costs
```bash
aws ce get-cost-and-usage \
  --time-period Start=$(date -u +%Y-%m-01),End=$(date -u +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics "UnblendedCost"
```

### Check Today's Costs
```bash
aws ce get-cost-and-usage \
  --time-period Start=$(date -u +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
  --granularity DAILY \
  --metrics "UnblendedCost"
```

### Check Costs by Service
```bash
aws ce get-cost-and-usage \
  --time-period Start=$(date -u +%Y-%m-01),End=$(date -u +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE
```

---

## Alert Notification Options

### Email
- Default option
- Free
- Immediate delivery

### SMS
1. Create SNS topic
2. Add SMS subscription
3. Costs $0.00645 per SMS (US)

### Slack
1. Create SNS topic
2. Use AWS Chatbot
3. Connect to Slack channel
4. Free

### Lambda Function
1. Create SNS topic
2. Subscribe Lambda function
3. Custom logic (e.g., auto-shutdown)

---

## Testing Your Alerts

### Test Budget Alert
1. Go to AWS Budgets
2. Select your budget
3. Click "Actions" → "Edit"
4. Temporarily lower threshold to $0.01
5. Wait 24 hours for alert
6. Reset threshold

### Test CloudWatch Alarm
1. Go to CloudWatch Alarms
2. Select your alarm
3. Click "Actions" → "Set alarm state"
4. Choose "In alarm"
5. Check if you receive email
6. Reset to "OK"

---

## Troubleshooting

### Not Receiving Alerts

**Check 1: Email Confirmed?**
- Go to SNS Console
- Check subscription status
- Resend confirmation if needed

**Check 2: Spam Folder?**
- Check spam/junk folder
- Add aws-notifications@amazon.com to contacts

**Check 3: Alarm Configured?**
- Go to CloudWatch Alarms
- Check alarm state
- Verify threshold settings

**Check 4: Billing Alerts Enabled?**
- Go to Billing Preferences
- Ensure "Receive Billing Alerts" is checked

### Alarm Not Triggering

**Issue**: Costs exceeded but no alarm
**Solution**: 
- Billing data updates every 6-8 hours
- Wait for next update cycle
- Check alarm history in CloudWatch

---

## Best Practices

1. **Set Multiple Thresholds**
   - 40%, 60%, 80%, 100%
   - Early warning system

2. **Monitor Daily**
   - Check costs in morning
   - Catch issues early

3. **Review Monthly**
   - Analyze cost trends
   - Optimize services

4. **Tag Resources**
   - Tag all resources with project name
   - Track costs by project

5. **Use Cost Allocation Tags**
   - Enable in Billing preferences
   - Better cost tracking

6. **Set Up Anomaly Detection**
   - AWS Cost Anomaly Detection
   - Automatic unusual spend alerts

---

## Quick Setup Checklist

- [ ] Enable billing alerts in preferences
- [ ] Create $25 monthly budget
- [ ] Set alert at 80% ($20)
- [ ] Set alert at 100% ($25)
- [ ] Confirm email subscription
- [ ] Create Bedrock-specific budget ($20)
- [ ] Set up daily cost report
- [ ] Add billing dashboard to favorites
- [ ] Document emergency shutdown procedure
- [ ] Test alert notifications

---

## Support

If you exceed your budget unexpectedly:
1. Check CloudWatch Logs for unusual activity
2. Review API Gateway access logs
3. Check for unauthorized API calls
4. Contact AWS Support if needed
5. Request cost review/credits if appropriate

**AWS Support**: https://console.aws.amazon.com/support/
