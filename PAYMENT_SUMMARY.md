# Payment & Subscription System - Quick Start

## What You Have Now

✅ **Usage Limits**: Free users get 10 questions, Pro users get unlimited
✅ **Upgrade Page**: Professional upgrade page with pricing
✅ **Stripe Integration**: Ready to accept payments (needs configuration)
✅ **Admin Tools**: Python script to manually manage subscriptions
✅ **Automatic Tracking**: Usage automatically tracked in DynamoDB

## Three Ways to Manage Payments

### Option 1: Stripe (Automated) - RECOMMENDED

**Best for**: Scaling, automation, professional setup

**Setup Time**: 2-3 hours

**Steps**:
1. Create Stripe account
2. Get API keys
3. Deploy subscription Lambda
4. Configure webhook
5. Test with test cards
6. Go live

**Pros**:
- Fully automated
- Handles recurring billing
- Professional checkout
- Automatic upgrades/downgrades
- Built-in fraud protection

**Cons**:
- Stripe fees (2.9% + $0.30)
- Requires technical setup

**See**: `PAYMENT_SETUP.md` for full instructions

---

### Option 2: Manual Management - EASIEST TO START

**Best for**: Starting out, low volume, testing

**Setup Time**: 5 minutes

**Steps**:
1. User emails you requesting Pro
2. They send payment via PayPal/Venmo/Zelle
3. You run admin script to upgrade them
4. Done!

**How to upgrade a user**:
```bash
cd "Financial Helper App/admin"
python manage_subscriptions.py upgrade user@example.com
```

**Pros**:
- No technical setup
- Start immediately
- Flexible payment methods
- No platform fees

**Cons**:
- Manual work for each user
- No automatic renewals
- You track renewals manually

**See**: `admin/manage_subscriptions.py`

---

### Option 3: PayPal (Semi-Automated)

**Best for**: International users, PayPal preference

**Setup Time**: 1-2 hours

**Steps**:
1. Create PayPal Business account
2. Create subscription plan
3. Add PayPal button to upgrade page
4. Create webhook handler
5. Test and go live

**Pros**:
- Trusted brand
- Good for international
- Recurring billing
- Lower fees than Stripe in some regions

**Cons**:
- More complex API
- Less developer-friendly than Stripe

**See**: `PAYMENT_SETUP.md` Option 3

---

## Quick Start: Manual Management

**Right now, you can start accepting payments manually:**

### Step 1: Set Your Price
- Decide on pricing (suggested: $9.99/month)
- Create PayPal.me link or Venmo username

### Step 2: Add Payment Info to Upgrade Page
Edit `upgrade.html` and add your payment details:
```html
<p>Send $9.99/month to:</p>
<p>PayPal: your@email.com</p>
<p>Venmo: @yourvenmo</p>
<p>Then email us to activate Pro</p>
```

### Step 3: When User Pays
```bash
# Install boto3 if needed
pip install boto3

# Configure AWS credentials
aws configure

# Upgrade user
cd "Financial Helper App/admin"
python manage_subscriptions.py upgrade user@example.com
```

### Step 4: Track Renewals
Create a spreadsheet:
- User Email
- Payment Date
- Next Renewal Date
- Payment Method
- Status

Set calendar reminders for renewals.

---

## Admin Commands

View user details:
```bash
python manage_subscriptions.py view user@example.com
```

List all Pro users:
```bash
python manage_subscriptions.py list-pro
```

Reset usage (give more free questions):
```bash
python manage_subscriptions.py reset user@example.com
```

Downgrade to free:
```bash
python manage_subscriptions.py downgrade user@example.com
```

---

## Pricing Recommendations

### Conservative (Testing)
- Free: 5 questions/month
- Pro: $4.99/month

### Recommended (Balanced)
- Free: 10 questions/month
- Pro: $9.99/month

### Premium (High Value)
- Free: 10 questions/month
- Pro: $14.99/month
- Premium: $29.99/month (with 1-on-1 consultation)

---

## Current Limits

Edit these in the Lambda functions:

**Free Tier**: 10 questions
- Change in `advisor_handler.py`: `FREE_TIER_LIMIT = 10`

**Pro Tier**: Unlimited (999,999)
- Change in `advisor_handler.py`: `PRO_TIER_LIMIT = 999999`

---

## Next Steps

### Immediate (Manual)
1. ✅ Deploy updated Lambda functions
2. ✅ Test usage limits
3. ✅ Set up admin script
4. ✅ Add payment info to upgrade page
5. ✅ Start accepting payments manually

### Short Term (Stripe)
1. Create Stripe account
2. Get API keys
3. Deploy subscription Lambda
4. Test with test cards
5. Go live

### Long Term (Scale)
1. Add annual pricing (discount)
2. Add premium tier
3. Implement referral program
4. Add usage analytics
5. Email notifications for limits

---

## Support

### User Asks: "How do I upgrade?"
1. Direct them to upgrade.html
2. They see pricing
3. They pay via your method
4. You upgrade them manually
5. They get confirmation email

### User Asks: "Can I get a refund?"
1. Check when they paid
2. If within 30 days, refund
3. Downgrade their account
4. Send confirmation

### User Asks: "How do I cancel?"
1. Stop charging them
2. Downgrade to free tier
3. They keep their data
4. Can resubscribe anytime

---

## Files Created

- `frontend/upgrade.html` - Upgrade page with pricing
- `lambda/subscription_handler.py` - Stripe integration Lambda
- `admin/manage_subscriptions.py` - Admin management tool
- `PAYMENT_SETUP.md` - Detailed Stripe setup guide
- `SUBSCRIPTION_MANAGEMENT.md` - DynamoDB management guide
- `PAYMENT_SUMMARY.md` - This file

---

## Questions?

**Q: Can I change the free tier limit?**
A: Yes, edit `FREE_TIER_LIMIT` in `advisor_handler.py`

**Q: How do I test without deploying?**
A: Use the admin script to manually set tiers

**Q: Can I offer annual pricing?**
A: Yes, create a second Stripe price or handle manually

**Q: What if I want to give someone free Pro?**
A: Use admin script: `python manage_subscriptions.py upgrade email@example.com`

**Q: How do I track revenue?**
A: Stripe Dashboard shows all revenue, or use your spreadsheet for manual

**Q: Can I change pricing later?**
A: Yes, but existing subscribers keep their price (grandfather them in)
