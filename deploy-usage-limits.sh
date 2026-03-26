#!/bin/bash

# Deploy Usage Limits Update
# This script deploys the updated Lambda functions with usage limit functionality

set -e

echo "🚀 Deploying PennyPal Usage Limits..."
echo ""

# Configuration
ADVISOR_LAMBDA="financial-helper-advisor"
PROFILE_LAMBDA="financial-helper-profile"
LAMBDA_DIR="lambda"

# Check if we're in the right directory
if [ ! -d "$LAMBDA_DIR" ]; then
    echo "❌ Error: lambda directory not found"
    echo "Please run this script from the 'Financial Helper App' directory"
    exit 1
fi

# Navigate to lambda directory
cd "$LAMBDA_DIR"

echo "📦 Packaging advisor Lambda..."
zip -q advisor_handler.zip advisor_handler.py
echo "✅ advisor_handler.zip created"

echo "📦 Packaging profile Lambda..."
zip -q profile_handler.zip profile_handler.py
echo "✅ profile_handler.zip created"

echo ""
echo "🔄 Deploying advisor Lambda..."
aws lambda update-function-code \
    --function-name "$ADVISOR_LAMBDA" \
    --zip-file fileb://advisor_handler.zip \
    --no-cli-pager

echo "✅ Advisor Lambda deployed"

echo ""
echo "🔄 Deploying profile Lambda..."
aws lambda update-function-code \
    --function-name "$PROFILE_LAMBDA" \
    --zip-file fileb://profile_handler.zip \
    --no-cli-pager

echo "✅ Profile Lambda deployed"

echo ""
echo "🧹 Cleaning up..."
rm advisor_handler.zip profile_handler.zip

cd ..

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Test with a free tier user (should be limited to 10 questions)"
echo "2. Configure admin script: edit admin/manage_users.py with your User Pool ID"
echo "3. Upgrade specific users: python admin/manage_users.py upgrade user@example.com"
echo ""
echo "📖 See USAGE_LIMITS_SETUP.md for full documentation"
