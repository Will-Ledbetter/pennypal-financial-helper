"""
Profile Handler Lambda
Manages user financial profile CRUD operations in DynamoDB
"""

import json
import os
import logging
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('PROFILES_TABLE', 'financial-helper-profiles')
table = dynamodb.Table(table_name)

# CORS headers
CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
}

def lambda_handler(event, context):
    """
    Handle profile operations
    
    GET /profile - Get user profile
    POST /profile - Create/Update user profile
    """
    
    # Handle OPTIONS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return create_response(200, {})
    
    try:
        # Get user ID from Cognito token
        user_id = get_user_id_from_token(event)
        if not user_id:
            return create_response(401, {'error': 'Unauthorized'})
        
        http_method = event.get('httpMethod')
        
        if http_method == 'GET':
            return get_profile(user_id)
        elif http_method == 'POST':
            return save_profile(user_id, event)
        else:
            return create_response(405, {'error': 'Method not allowed'})
            
    except Exception as e:
        logger.error(f"Error: {e}")
        return create_response(500, {'error': 'Internal server error'})

def get_user_id_from_token(event):
    """Extract user ID from Cognito JWT token"""
    try:
        # In API Gateway with Cognito authorizer, user info is in requestContext
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        claims = authorizer.get('claims', {})
        
        # Get user ID (sub claim)
        user_id = claims.get('sub') or claims.get('cognito:username')
        
        return user_id
    except Exception as e:
        logger.error(f"Error extracting user ID: {e}")
        return None

def get_profile(user_id):
    """Get user profile from DynamoDB"""
    try:
        response = table.get_item(Key={'userId': user_id})
        
        if 'Item' in response:
            profile = response['Item']
            
            # Ensure subscription fields exist - update DB if missing
            needs_update = False
            if 'subscriptionTier' not in profile:
                profile['subscriptionTier'] = 'free'
                profile['questionsAsked'] = 0
                profile['questionsLimit'] = 10
                needs_update = True
            
            # Update the database if subscription fields were missing
            if needs_update:
                try:
                    table.update_item(
                        Key={'userId': user_id},
                        UpdateExpression='SET subscriptionTier = :tier, questionsAsked = :asked, questionsLimit = :limit',
                        ExpressionAttributeValues={
                            ':tier': profile['subscriptionTier'],
                            ':asked': profile['questionsAsked'],
                            ':limit': profile['questionsLimit']
                        }
                    )
                    logger.info(f"Added subscription fields to existing profile for user: {user_id}")
                except ClientError as e:
                    logger.error(f"Error updating subscription fields: {e}")
            
            # Remove internal fields from response
            response_profile = profile.copy()
            response_profile.pop('userId', None)
            response_profile.pop('createdAt', None)
            response_profile.pop('updatedAt', None)
            
            return create_response(200, {'profile': response_profile})
        else:
            # No profile yet
            return create_response(200, {'profile': {}})
            
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return create_response(500, {'error': 'Failed to retrieve profile'})

def save_profile(user_id, event):
    """Save or update user profile in DynamoDB"""
    try:
        body = json.loads(event.get('body', '{}'))
        
        # Validate required fields
        profile_data = {
            'userId': user_id,
            # Basic Info
            'annualIncome': body.get('annualIncome', ''),
            'monthlyExpenses': body.get('monthlyExpenses', ''),
            'currentSavings': body.get('currentSavings', ''),
            'totalInvestments': body.get('totalInvestments', ''),
            'monthlyInvestment': body.get('monthlyInvestment', ''),
            'retirementAccounts': body.get('retirementAccounts', ''),
            'investmentTypes': body.get('investmentTypes', ''),
            'employerMatch': body.get('employerMatch', ''),
            'totalDebt': body.get('totalDebt', ''),
            'savingsGoal': body.get('savingsGoal', ''),
            'retirementGoal': body.get('retirementGoal', ''),
            'retirementAge': body.get('retirementAge', ''),
            'currentAge': body.get('currentAge', ''),
            'dependents': body.get('dependents', ''),
            'taxFilingStatus': body.get('taxFilingStatus', ''),
            'housingStatus': body.get('housingStatus', ''),
            'housingPayment': body.get('housingPayment', ''),
            'mortgageBalance': body.get('mortgageBalance', ''),
            'mortgageRate': body.get('mortgageRate', ''),
            'carPayment': body.get('carPayment', ''),
            'carLoanBalance': body.get('carLoanBalance', ''),
            'otherDebtPayment': body.get('otherDebtPayment', ''),
            'otherDebtBalance': body.get('otherDebtBalance', ''),
            'otherDebtDescription': body.get('otherDebtDescription', ''),
            'riskTolerance': body.get('riskTolerance', 'moderate'),
            'financialGoals': body.get('financialGoals', ''),
            
            # Insurance Coverage
            'lifeInsuranceValue': body.get('lifeInsuranceValue', ''),
            'healthInsuranceDeductible': body.get('healthInsuranceDeductible', ''),
            'healthInsurancePremium': body.get('healthInsurancePremium', ''),
            'homeownersInsurance': body.get('homeownersInsurance', ''),
            'autoInsurance': body.get('autoInsurance', ''),
            
            # Emergency Planning
            'emergencyFund': body.get('emergencyFund', ''),
            'emergencyFundGoal': body.get('emergencyFundGoal', ''),
            
            # Additional Income
            'bonusIncome': body.get('bonusIncome', ''),
            'sideIncome': body.get('sideIncome', ''),
            
            # Investment Details
            'assetAllocation': body.get('assetAllocation', ''),
            'taxableInvestments': body.get('taxableInvestments', ''),
            'taxAdvantagedInvestments': body.get('taxAdvantagedInvestments', ''),
            'expectedReturn': body.get('expectedReturn', ''),
            
            # Debt Details
            'creditCardLimit': body.get('creditCardLimit', ''),
            'creditUtilization': body.get('creditUtilization', ''),
            'studentLoanBalance': body.get('studentLoanBalance', ''),
            'studentLoanRate': body.get('studentLoanRate', ''),
            'creditCardRate': body.get('creditCardRate', ''),
            
            # Tax & Benefits
            'hsaBalance': body.get('hsaBalance', ''),
            'hsaContribution': body.get('hsaContribution', ''),
            'fsaContribution': body.get('fsaContribution', ''),
            'childcareBenefits': body.get('childcareBenefits', ''),
            
            # Lifestyle & Future Planning
            'plannedExpenses': body.get('plannedExpenses', ''),
            'educationSavingsGoal': body.get('educationSavingsGoal', ''),
            'education529Balance': body.get('education529Balance', ''),
            'charitableGiving': body.get('charitableGiving', ''),
            
            # Retirement Planning
            'socialSecurityEstimate': body.get('socialSecurityEstimate', ''),
            'pensionBenefit': body.get('pensionBenefit', ''),
            'retirementSpending': body.get('retirementSpending', ''),
            
            'updatedAt': datetime.utcnow().isoformat()
        }
        
        # Add createdAt and subscription fields if new profile
        existing = table.get_item(Key={'userId': user_id})
        if 'Item' not in existing:
            profile_data['createdAt'] = datetime.utcnow().isoformat()
            profile_data['subscriptionTier'] = 'free'
            profile_data['questionsAsked'] = 0
            profile_data['questionsLimit'] = 10
        else:
            # Preserve existing subscription data
            existing_item = existing['Item']
            profile_data['subscriptionTier'] = existing_item.get('subscriptionTier', 'free')
            profile_data['questionsAsked'] = existing_item.get('questionsAsked', 0)
            profile_data['questionsLimit'] = existing_item.get('questionsLimit', 10)
        
        # Save to DynamoDB
        table.put_item(Item=profile_data)
        
        # Return saved profile (without internal fields)
        response_profile = profile_data.copy()
        response_profile.pop('userId', None)
        response_profile.pop('createdAt', None)
        response_profile.pop('updatedAt', None)
        
        # Include subscription info in response
        response_profile['subscriptionTier'] = profile_data.get('subscriptionTier', 'free')
        response_profile['questionsAsked'] = profile_data.get('questionsAsked', 0)
        response_profile['questionsLimit'] = profile_data.get('questionsLimit', 10)
        
        logger.info(f"Profile saved for user: {user_id}")
        
        return create_response(200, {
            'success': True,
            'profile': response_profile
        })
        
    except json.JSONDecodeError:
        return create_response(400, {'error': 'Invalid JSON'})
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        return create_response(500, {'error': 'Failed to save profile'})

def create_response(status_code, body):
    """Create API Gateway response"""
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps(body)
    }

# Example DynamoDB Table Schema:
# {
#     "userId": "string (partition key)",
#     "annualIncome": "string",
#     "monthlyExpenses": "string",
#     "currentSavings": "string",
#     "totalDebt": "string",
#     "savingsGoal": "string",
#     "riskTolerance": "string",
#     "financialGoals": "string",
#     "createdAt": "string (ISO timestamp)",
#     "updatedAt": "string (ISO timestamp)"
# }
