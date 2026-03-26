#!/bin/bash

# Deploy Lambda Functions Script
# This script packages and prepares Lambda functions for upload to AWS

echo "🚀 Packaging Lambda Functions..."
echo ""

cd lambda

# Package Profile Handler
echo "📦 Packaging profile_handler..."
zip -q profile_handler.zip profile_handler.py
echo "✅ profile_handler.zip created"

# Package Advisor Handler
echo "📦 Packaging advisor_handler..."
zip -q advisor_handler.zip advisor_handler.py
echo "✅ advisor_handler.zip created"

echo ""
echo "✨ Lambda functions packaged successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Go to AWS Lambda Console"
echo "2. Upload profile_handler.zip to 'financial-helper-profile' function"
echo "3. Upload advisor_handler.zip to 'financial-helper-advisor' function"
echo ""
echo "⚠️  IMPORTANT: Check these settings for advisor Lambda:"
echo "   - Timeout: 60 seconds (Configuration → General)"
echo "   - Memory: 512 MB"
echo "   - IAM Role has bedrock:InvokeModel permission"
echo ""
