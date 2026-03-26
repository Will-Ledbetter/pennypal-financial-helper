# Payment Integration Setup Guide

## Overview

This guide covers setting up Stripe payments for PennyPal Advisor Pro subscriptions.

## Option 1: Stripe Integration (Recommended)

### Step 1: Create Stripe Account

1. Go to https://stripe.com
2. Sign up for an account
3. Complete business verification
4. Go to Dashboard

### Step 2: Get Stripe Keys

1. In Stripe Dashboard, click "Developers" → "API keys"
2. Copy these keys:
   - **Publishable key** (starts with `pk_test_` or `pk_live_`)
   - **Secret key** (starts with `sk_test_` or `sk_live_`)

### Step 3: Create Product and Price

1. In Stripe Dashboard, go to "Products"
2. Click "Add product"
3. Fill in:
   - Name: "PennyPal Pro"
   - Description: "Unlimited AI financial advice"
   - Pricing: $9.99 USD
   - Billing period: Monthly
   - Recurring
4. Click "Save product"
5. Copy the **Price ID** (starts with `price_`)

### Step 4: Configure Frontend

Edit `upgrade.html` line 119:
```javascript
const STRIPE_PUBLISHABLE_KEY = 'pk_test_YOUR_KEY_HERE';
```
Replace with your actual publishable key.

### Step 5: Deploy Subscription Lambda

1. Install Stripe library:
```bash
cd "Financial Helper App/lambda"
pip install stripe -t .
```

2. Create deployment package:
```bash
zip -r subscription_handler.zip subscription_handler.py stripe/
```

3. Create Lambda in AWS Console:
   - Name: `financial-helper-subscription`
   - Runtime: Python 3.11
   - Upload `subscription_handler.zip`

4. Add environment variables:
   - `STRIPE_SECRET_KEY`: Your Stripe secret key
   - `STRIPE_PRICE_ID`: Your Stripe price ID
   - `PROFILES_TABLE`: `financial-helper-profiles`

5. Set timeout to 30 seconds

6. Add IAM permissions:
   - DynamoDB: `GetItem`, `UpdateItem`, `Scan`
   - CloudWatch Logs

### Step 6: Add API Gateway Endpoints

1. Go to API Gateway Console
2. Select your API
3. Create `/subscribe` resource
4. Add POST method:
   - Integration: Lambda
   - Lambda: `financial-helper-subscription`
   - Authorizer: Your Cognito authorizer
5. Enable CORS
6. Deploy API

### Step 7: Setup Stripe Webhooks

1. In Stripe Dashboard, go to "Developers" → "Webhooks"
2. Click "Add endpoint"
3. Endpoint URL: `https://YOUR_API_GATEWAY_URL/prod/webhook`
4. Select events:
   - `customer.subscription.deleted`
   - `customer.subscription.updated`
   - `invoice.payment_failed`
5. Copy the **Webhook signing secret**
6. Add to Lambda environment variable:
   - `STRIPE_WEBHOOK_SECRET`: Your webhook secret

### Step 8: Test Payment Flow

1. Use Stripe test card: `4242 4242 4242 4242`
2. Any future expiry date
3. Any 3-digit CVC
4. Any ZIP code

## Option 2: Manual Payment Management

If you want to handle payments manually (PayPal, Venmo, bank transfer):

### Step 1: Collect Payment Offline

1. User contacts you via email
2. They send payment via PayPal/Venmo/etc.
3. You verify payment received

### Step 2: Upgrade User Manually

Use AWS CLI:
```bash
# Get user's Cognito sub from their email
aws cognito-idp list-users \
  --user-pool-id YOUR_USER_POOL_ID \
  --filter "email = \"user@example.com\""

# Upgrade to Pro
aws dynamodb update-item \
  --table-name financial-helper-profiles \
  --key '{"userId": {"S": "USER_SUB_HERE"}}' \
  --update-expression "SET subscriptionTier = :tier, questionsLimit = :limit" \
  --expression-attribute-values '{":tier": {"S": "pro"}, ":limit": {"N": "999999"}}'
```

### Step 3: Track Subscriptions

Create a spreadsheet:
- User Email
- Payment Date
- Payment Method
- Amount
- Subscription Status
- Renewal Date

Set calendar reminders for renewals.

## Option 3: PayPal Integration

### Step 1: Create PayPal Business Account

1. Go to https://paypal.com/business
2. Sign up for business account
3. Get API credentials

### Step 2: Add PayPal Button

In `upgrade.html`, add:
```html
<div id="paypal-button-container"></div>

<script src="https://www.paypal.com/sdk/js?client-id=YOUR_CLIENT_ID&vault=true&intent=subscription"></script>
<script>
  paypal.Buttons({
    createSubscription: function(data, actions) {
      return actions.subscription.create({
        'plan_id': 'YOUR_PLAN_ID'
      });
    },
    onApprove: function(data, actions) {
      // Call your backend to upgrade user
      fetch(`${AWS_CONFIG.apiEndpoint}/paypal-subscribe`, {
        method: 'POST',
        headers: {
          'Authorization': idToken,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          subscriptionID: data.subscriptionID
        })
      });
    }
  }).render('#paypal-button-container');
</script>
```

## Pricing Recommendations

### Suggested Pricing Tiers

**Free Tier:**
- 10 questions/month
- Basic features
- $0

**Pro Tier:**
- Unlimited questions
- All features
- $9.99/month or $99/year (save 17%)

**Premium Tier (Future):**
- Everything in Pro
- 1-on-1 consultation
- Custom reports
- $29.99/month

## Managing Subscriptions

### View All Pro Users

```bash
aws dynamodb scan \
  --table-name financial-helper-profiles \
  --filter-expression "subscriptionTier = :pro" \
  --expression-attribute-values '{":pro": {"S": "pro"}}'
```

### Cancel Subscription

In Stripe Dashboard:
1. Go to "Customers"
2. Find customer
3. Click on subscription
4. Click "Cancel subscription"
5. Webhook will automatically downgrade user

### Refund

In Stripe Dashboard:
1. Go to "Payments"
2. Find payment
3. Click "Refund"
4. Manually downgrade user if needed

## Testing

### Test Cards (Stripe)

Success:
- `4242 4242 4242 4242` - Visa
- `5555 5555 5555 4444` - Mastercard

Decline:
- `4000 0000 0000 0002` - Card declined

### Test Webhooks

Use Stripe CLI:
```bash
stripe listen --forward-to localhost:3000/webhook
stripe trigger customer.subscription.deleted
```

## Security Best Practices

1. **Never expose secret keys** in frontend code
2. **Always verify webhooks** using signature
3. **Use HTTPS** for all payment pages
4. **Store minimal data** - let Stripe handle cards
5. **Log all transactions** for audit trail
6. **Implement rate limiting** on payment endpoints
7. **Monitor for fraud** using Stripe Radar

## Compliance

### Required Disclosures

Add to your site:
- Privacy Policy
- Terms of Service
- Refund Policy
- Subscription Terms

### PCI Compliance

Using Stripe Elements (as implemented) makes you PCI compliant because:
- Card data never touches your servers
- Stripe handles all card processing
- You only receive tokens

## Support & Troubleshooting

### Common Issues

**Payment fails:**
- Check Stripe Dashboard for error
- Verify API keys are correct
- Check webhook is receiving events

**User not upgraded:**
- Check CloudWatch logs
- Verify DynamoDB permissions
- Check subscription_handler Lambda

**Webhook not working:**
- Verify webhook URL is correct
- Check webhook secret matches
- Test with Stripe CLI

### Customer Support Flow

1. User reports payment issue
2. Check Stripe Dashboard for their email
3. View payment/subscription status
4. Check DynamoDB for their tier
5. Resolve discrepancy
6. Update user if needed

## Monitoring

### CloudWatch Metrics

Create alarms for:
- Failed payments
- Subscription cancellations
- Lambda errors

### Stripe Dashboard

Monitor:
- Monthly Recurring Revenue (MRR)
- Churn rate
- Failed payments
- New subscriptions

## Next Steps

1. Set up Stripe account
2. Deploy subscription Lambda
3. Test with test cards
4. Go live with real keys
5. Monitor first transactions
6. Set up customer support email
7. Create refund policy
8. Add analytics tracking
