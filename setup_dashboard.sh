#!/bin/bash

# Financial Helper App - CloudWatch Dashboard Setup
# This script creates a CloudWatch dashboard to monitor:
# - Total registered accounts
# - Total advice uses
# - Performance metrics
# - Error rates

set -e

# Configuration
DASHBOARD_NAME="FinancialHelperApp-Metrics"
REGION="us-east-1"
ADVISOR_LAMBDA_NAME="financial-helper-advisor"
PROFILE_LAMBDA_NAME="financial-helper-profile"
DYNAMODB_TABLE_NAME="financial-helper-profiles"

echo "=========================================="
echo "Financial Helper Dashboard Setup"
echo "=========================================="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ Error: AWS CLI is not installed"
    echo "Please install it from: https://aws.amazon.com/cli/"
    exit 1
fi

echo "✓ AWS CLI found"

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ Error: AWS credentials not configured"
    echo "Please run: aws configure"
    exit 1
fi

echo "✓ AWS credentials configured"
echo ""

# Get Lambda function ARNs
echo "Checking Lambda functions..."
ADVISOR_ARN=$(aws lambda get-function --function-name "$ADVISOR_LAMBDA_NAME" --region "$REGION" --query 'Configuration.FunctionArn' --output text 2>/dev/null || echo "")
PROFILE_ARN=$(aws lambda get-function --function-name "$PROFILE_LAMBDA_NAME" --region "$REGION" --query 'Configuration.FunctionArn' --output text 2>/dev/null || echo "")

if [ -z "$ADVISOR_ARN" ]; then
    echo "⚠️  Warning: Advisor Lambda function '$ADVISOR_LAMBDA_NAME' not found"
    echo "   Dashboard will be created but metrics may not appear until Lambda is deployed"
else
    echo "✓ Found advisor Lambda: $ADVISOR_LAMBDA_NAME"
fi

if [ -z "$PROFILE_ARN" ]; then
    echo "⚠️  Warning: Profile Lambda function '$PROFILE_LAMBDA_NAME' not found"
    echo "   Dashboard will be created but metrics may not appear until Lambda is deployed"
else
    echo "✓ Found profile Lambda: $PROFILE_LAMBDA_NAME"
fi

# Check DynamoDB table
echo ""
echo "Checking DynamoDB table..."
TABLE_STATUS=$(aws dynamodb describe-table --table-name "$DYNAMODB_TABLE_NAME" --region "$REGION" --query 'Table.TableStatus' --output text 2>/dev/null || echo "")

if [ -z "$TABLE_STATUS" ]; then
    echo "⚠️  Warning: DynamoDB table '$DYNAMODB_TABLE_NAME' not found"
    echo "   Dashboard will be created but account metrics may not appear until table is created"
else
    echo "✓ Found DynamoDB table: $DYNAMODB_TABLE_NAME (Status: $TABLE_STATUS)"
fi

echo ""
echo "Creating dashboard configuration..."

# Create the dashboard body with proper resource names
cat > /tmp/dashboard_body.json << EOF
{
  "widgets": [
    {
      "type": "log",
      "properties": {
        "query": "SOURCE '/aws/lambda/$PROFILE_LAMBDA_NAME'\\n| fields @timestamp, @message\\n| filter @message like /Profile saved for user/\\n| stats count() as TotalNewProfiles",
        "region": "$REGION",
        "title": "Total New Profiles (All Time)",
        "stacked": false
      },
      "width": 12,
      "height": 6,
      "x": 0,
      "y": 0
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "AWS/Lambda", "Invocations", { "stat": "Sum", "label": "Total Advice Requests", "dimensions": { "FunctionName": "$ADVISOR_LAMBDA_NAME" } } ]
        ],
        "view": "singleValue",
        "region": "$REGION",
        "title": "Total Advice Uses (Last 30 Days)",
        "period": 2592000,
        "yAxis": {
          "left": {
            "min": 0
          }
        }
      },
      "width": 8,
      "height": 6,
      "x": 12,
      "y": 0
    },
    {
      "type": "log",
      "properties": {
        "query": "SOURCE '/aws/lambda/$ADVISOR_LAMBDA_NAME'\\n| fields @timestamp, @message\\n| filter @message like /Generating advice for user/\\n| parse @message /user: (?<userId>[^,]+)/\\n| stats count() as Requests by userId\\n| sort Requests desc\\n| limit 20",
        "region": "$REGION",
        "title": "Total Requests by Profile (Top 20)",
        "stacked": false
      },
      "width": 12,
      "height": 6,
      "x": 0,
      "y": 6
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "AWS/Lambda", "Invocations", { "stat": "Sum", "label": "Advice Requests", "dimensions": { "FunctionName": "$ADVISOR_LAMBDA_NAME" } } ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "$REGION",
        "title": "Advice Requests - Last 24 Hours",
        "period": 3600,
        "yAxis": {
          "left": {
            "min": 0
          }
        }
      },
      "width": 12,
      "height": 6,
      "x": 12,
      "y": 6
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "AWS/Lambda", "Duration", { "stat": "Average", "label": "Avg Response Time", "dimensions": { "FunctionName": "$ADVISOR_LAMBDA_NAME" } } ],
          [ "...", { "stat": "Maximum", "label": "Max Response Time", "dimensions": { "FunctionName": "$ADVISOR_LAMBDA_NAME" } } ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "$REGION",
        "title": "Advice Generation Performance (ms)",
        "period": 300,
        "yAxis": {
          "left": {
            "label": "Milliseconds",
            "min": 0
          }
        }
      },
      "width": 12,
      "height": 6,
      "x": 12,
      "y": 6
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "AWS/Lambda", "Errors", { "stat": "Sum", "label": "Advisor Errors", "color": "#d62728", "dimensions": { "FunctionName": "$ADVISOR_LAMBDA_NAME" } } ],
          [ "...", { "stat": "Sum", "label": "Profile Errors", "color": "#ff7f0e", "dimensions": { "FunctionName": "$PROFILE_LAMBDA_NAME" } } ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "$REGION",
        "title": "Error Count",
        "period": 300,
        "yAxis": {
          "left": {
            "min": 0
          }
        }
      },
      "width": 12,
      "height": 6,
      "x": 0,
      "y": 12
    },
    {
      "type": "metric",
      "properties": {
        "metrics": [
          [ "AWS/DynamoDB", "ConsumedReadCapacityUnits", { "stat": "Sum", "label": "Profile Reads", "dimensions": { "TableName": "$DYNAMODB_TABLE_NAME" } } ],
          [ ".", "ConsumedWriteCapacityUnits", { "stat": "Sum", "label": "Profile Writes", "dimensions": { "TableName": "$DYNAMODB_TABLE_NAME" } } ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "$REGION",
        "title": "Profile Activity",
        "period": 300,
        "yAxis": {
          "left": {
            "min": 0
          }
        }
      },
      "width": 12,
      "height": 6,
      "x": 12,
      "y": 12
    },
    {
      "type": "log",
      "properties": {
        "query": "SOURCE '/aws/lambda/$ADVISOR_LAMBDA_NAME'\\n| fields @timestamp, @message\\n| filter @message like /Successfully generated advice/\\n| stats count() as SuccessfulAdvice by bin(5m)",
        "region": "$REGION",
        "title": "Successful Advice Generation Rate",
        "stacked": false
      },
      "width": 12,
      "height": 6,
      "x": 0,
      "y": 18
    },
    {
      "type": "log",
      "properties": {
        "query": "SOURCE '/aws/lambda/$PROFILE_LAMBDA_NAME'\\n| fields @timestamp, @message\\n| filter @message like /Profile saved for user/\\n| stats count() as NewProfiles by bin(1h)",
        "region": "$REGION",
        "title": "New Profile Registrations",
        "stacked": false
      },
      "width": 12,
      "height": 6,
      "x": 12,
      "y": 18
    }
  ]
}
EOF

echo "✓ Dashboard configuration created"
echo ""

# Create or update the dashboard
echo "Deploying dashboard to CloudWatch..."
aws cloudwatch put-dashboard \
    --dashboard-name "$DASHBOARD_NAME" \
    --dashboard-body file:///tmp/dashboard_body.json \
    --region "$REGION"

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Dashboard created successfully!"
    echo "=========================================="
    echo ""
    echo "Dashboard Name: $DASHBOARD_NAME"
    echo "Region: $REGION"
    echo ""
    echo "View your dashboard at:"
    echo "https://console.aws.amazon.com/cloudwatch/home?region=$REGION#dashboards:name=$DASHBOARD_NAME"
    echo ""
    echo "Metrics tracked:"
    echo "  • Total registered accounts (from DynamoDB)"
    echo "  • Total advice uses (Lambda invocations)"
    echo "  • Advice request trends (24 hours)"
    echo "  • Performance metrics (response times)"
    echo "  • Error rates"
    echo "  • Profile activity"
    echo ""
else
    echo ""
    echo "❌ Error: Failed to create dashboard"
    exit 1
fi

# Cleanup
rm -f /tmp/dashboard_body.json

echo "Setup complete!"
