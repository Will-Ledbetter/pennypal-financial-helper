"""
Advisor Handler Lambda
Generates personalized financial advice using Amazon Bedrock
"""

import json
import os
import logging
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Bedrock and DynamoDB
bedrock_runtime = boto3.client('bedrock-runtime')
dynamodb = boto3.resource('dynamodb')
profiles_table = dynamodb.Table(os.environ.get('PROFILES_TABLE', 'financial-helper-profiles'))

# Model configuration
# Use Claude 3 Haiku (faster, cheaper, no use case form required)
MODEL_ID = 'anthropic.claude-3-haiku-20240307-v1:0'
MAX_TOKENS = 1500  # Reduced for faster responses

# Usage limits
FREE_TIER_LIMIT = 10
PRO_TIER_LIMIT = 999999

# CORS headers
CORS_HEADERS = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
}

def lambda_handler(event, context):
    """
    Generate personalized financial advice
    
    POST /advice
    Body: {
        "question": "user's question",
        "profile": {user profile data}
    }
    """
    
    # Handle OPTIONS preflight
    if event.get('httpMethod') == 'OPTIONS':
        return create_response(200, {})
    
    try:
        # Get user ID from token (for logging/tracking)
        user_id = get_user_id_from_token(event)
        if not user_id:
            return create_response(401, {'error': 'Unauthorized'})
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        question = body.get('question', '').strip()
        profile = body.get('profile', {})
        
        if not question:
            return create_response(400, {'error': 'Question is required'})
        
        if not profile or not profile.get('annualIncome'):
            return create_response(400, {'error': 'User profile is required'})
        
        # Check usage limits
        usage_check = check_usage_limit(user_id)
        if not usage_check['allowed']:
            logger.warning(f"User {user_id} exceeded usage limit")
            return create_response(403, {
                'error': 'Usage limit reached',
                'message': usage_check['message'],
                'questionsAsked': usage_check['questionsAsked'],
                'questionsLimit': usage_check['questionsLimit']
            })
        
        logger.info(f"Generating advice for user: {user_id}, question length: {len(question)}, questions used: {usage_check['questionsAsked']}/{usage_check['questionsLimit']}")
        
        # Generate advice using Bedrock
        advice = generate_advice(question, profile)
        
        # Increment usage counter
        increment_usage(user_id)
        
        if not advice:
            logger.error("Generated advice is empty")
            return create_response(500, {'error': 'Failed to generate advice - empty response'})
        
        logger.info(f"Successfully generated advice, length: {len(advice)}")
        
        # Get updated usage stats
        updated_usage = get_usage_stats(user_id)
        
        return create_response(200, {
            'success': True,
            'advice': advice,
            'usage': {
                'questionsAsked': updated_usage['questionsAsked'],
                'questionsLimit': updated_usage['questionsLimit'],
                'questionsRemaining': updated_usage['questionsLimit'] - updated_usage['questionsAsked']
            }
        })
        
    except json.JSONDecodeError:
        return create_response(400, {'error': 'Invalid JSON'})
    except Exception as e:
        logger.error(f"Error: {e}")
        return create_response(500, {'error': 'Failed to generate advice'})

def get_user_id_from_token(event):
    """Extract user ID from Cognito JWT token"""
    try:
        request_context = event.get('requestContext', {})
        authorizer = request_context.get('authorizer', {})
        claims = authorizer.get('claims', {})
        user_id = claims.get('sub') or claims.get('cognito:username')
        return user_id
    except Exception as e:
        logger.error(f"Error extracting user ID: {e}")
        return None

def check_usage_limit(user_id):
    """Check if user has exceeded their usage limit"""
    try:
        response = profiles_table.get_item(Key={'userId': user_id})
        
        if 'Item' not in response:
            # New user, initialize with free tier
            return {
                'allowed': True,
                'questionsAsked': 0,
                'questionsLimit': FREE_TIER_LIMIT
            }
        
        profile = response['Item']
        subscription_tier = profile.get('subscriptionTier', 'free')
        questions_asked = int(profile.get('questionsAsked', 0))
        questions_limit = int(profile.get('questionsLimit', FREE_TIER_LIMIT))
        
        if questions_asked >= questions_limit:
            return {
                'allowed': False,
                'questionsAsked': questions_asked,
                'questionsLimit': questions_limit,
                'message': f'You have reached your limit of {questions_limit} questions. Pro version not yet released.'
            }
        
        return {
            'allowed': True,
            'questionsAsked': questions_asked,
            'questionsLimit': questions_limit
        }
        
    except Exception as e:
        logger.error(f"Error checking usage limit: {e}")
        # Allow on error to not block users
        return {
            'allowed': True,
            'questionsAsked': 0,
            'questionsLimit': FREE_TIER_LIMIT
        }

def increment_usage(user_id):
    """Increment the user's question counter"""
    try:
        profiles_table.update_item(
            Key={'userId': user_id},
            UpdateExpression='SET questionsAsked = if_not_exists(questionsAsked, :zero) + :inc',
            ExpressionAttributeValues={
                ':zero': 0,
                ':inc': 1
            }
        )
        logger.info(f"Incremented usage for user: {user_id}")
    except Exception as e:
        logger.error(f"Error incrementing usage: {e}")

def get_usage_stats(user_id):
    """Get current usage statistics for a user"""
    try:
        response = profiles_table.get_item(Key={'userId': user_id})
        if 'Item' in response:
            profile = response['Item']
            return {
                'questionsAsked': int(profile.get('questionsAsked', 0)),
                'questionsLimit': int(profile.get('questionsLimit', FREE_TIER_LIMIT))
            }
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
    
    return {
        'questionsAsked': 0,
        'questionsLimit': FREE_TIER_LIMIT
    }

def generate_advice(question, profile):
    """Generate personalized financial advice using Bedrock"""
    
    # Build context from user profile
    profile_context = build_profile_context(profile)
    
    # Build prompt
    prompt = f"""You are a professional financial advisor providing direct, conversational advice. 

IMPORTANT STYLE GUIDELINES:
- Do NOT use formal greetings like "Dear Client" or any salutations
- Do NOT include sign-offs, signatures, or closings at the end
- Jump straight into the advice
- Write in a friendly, conversational tone
- Be direct and actionable

CRITICAL RULES:
1. ONLY use information explicitly provided in the client's profile
2. DO NOT assume the client has debts, expenses, or financial obligations not listed
3. DO NOT make up scenarios or suggest solutions for problems they don't have
4. If a field shows "Not provided" or is empty, DO NOT mention or assume anything about it
5. Base your advice ONLY on what they've actually shared

DEBT CLASSIFICATION FRAMEWORK (only apply if client HAS these debts):
When evaluating financial decisions, use this debt classification:

GOOD DEBT (Low Priority to Pay Off):
- Mortgage debt - This is considered good debt. Do NOT recommend postponing financial goals solely because the mortgage isn't paid off
- Car loans - If the vehicle provides good ROI (enables income, reasonable rate)
- Student loans - If at low interest rates

BAD DEBT (High Priority to Pay Off):
- High-interest credit cards (typically 15%+ APR)
- Personal loans with high rates
- Payday loans
- Any debt with interest rates significantly higher than investment returns

DEBT EVALUATION APPROACH (only if applicable):
1. Include mortgage payment in monthly expenses (not as "debt to eliminate")
2. Assess affordability based on cash flow, savings goals, and investment strategy
3. Prioritize paying off bad debt (high-interest) first
4. Good debt can coexist with investing and other financial goals
5. Compare debt interest rates vs. expected investment returns when advising

CLIENT'S FINANCIAL PROFILE:
{profile_context}

CLIENT'S QUESTION:
{question}

Provide personalized, actionable financial advice based on their specific situation. Consider their income, expenses, savings, debt, goals, and risk tolerance. Be specific, practical, and encouraging.

Your advice should:
1. Start immediately with addressing their question (no greeting)
2. ONLY reference information explicitly provided in their profile
3. Apply the debt classification framework ONLY if they have those debts
4. Never assume they have credit card debt, student loans, or other obligations unless stated
5. Consider their complete financial picture based on what they've shared
6. Provide concrete, actionable steps
7. Be realistic and achievable
8. Explain the reasoning behind your recommendations
9. End naturally without formal closings or sign-offs

Keep your response concise and actionable (200-400 words).
"""
    
    try:
        logger.info(f"Calling Bedrock with model: {MODEL_ID}")
        
        # Call Bedrock
        response = bedrock_runtime.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": MAX_TOKENS,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7
            })
        )
        
        logger.info("Bedrock response received, parsing...")
        
        # Parse response
        response_body = json.loads(response['body'].read())
        
        if 'content' not in response_body or not response_body['content']:
            logger.error(f"Invalid response structure: {response_body}")
            raise Exception("Invalid response from Bedrock")
        
        advice = response_body['content'][0]['text']
        
        if not advice or len(advice.strip()) == 0:
            logger.error("Bedrock returned empty advice")
            raise Exception("Empty advice from Bedrock")
        
        logger.info(f"Advice generated successfully, length: {len(advice)}")
        
        # Add disclaimer
        disclaimer = "\n\n---\n\nDisclaimer: This advice is generated by AI and should not be considered professional financial advice. Please consult with a licensed financial advisor for personalized guidance."
        
        return advice + disclaimer
        
    except ClientError as e:
        logger.error(f"Bedrock ClientError: {e}")
        raise Exception(f"Bedrock API error: {str(e)}")
    except Exception as e:
        logger.error(f"Error generating advice: {e}")
        raise Exception(f"Failed to generate advice: {str(e)}")

def build_profile_context(profile):
    """Build a readable context string from user profile"""
    
    def format_currency(value):
        if not value:
            return "Not provided"
        try:
            return f"${int(value):,}"
        except:
            return value
    
    def format_percent(value):
        if not value:
            return "Not provided"
        try:
            return f"{float(value)}%"
        except:
            return value
    
    # Income & Expenses
    annual_income = format_currency(profile.get('annualIncome'))
    monthly_expenses = format_currency(profile.get('monthlyExpenses'))
    bonus_income = format_currency(profile.get('bonusIncome'))
    side_income = format_currency(profile.get('sideIncome'))
    
    # Savings & Investments
    current_savings = format_currency(profile.get('currentSavings'))
    emergency_fund = format_currency(profile.get('emergencyFund'))
    emergency_fund_goal = format_currency(profile.get('emergencyFundGoal'))
    total_investments = format_currency(profile.get('totalInvestments'))
    monthly_investment = format_currency(profile.get('monthlyInvestment'))
    retirement_accounts = format_currency(profile.get('retirementAccounts'))
    investment_types = profile.get('investmentTypes', 'Not specified')
    employer_match = format_percent(profile.get('employerMatch'))
    asset_allocation = profile.get('assetAllocation', 'Not specified')
    taxable_investments = format_currency(profile.get('taxableInvestments'))
    tax_advantaged_investments = format_currency(profile.get('taxAdvantagedInvestments'))
    expected_return = format_percent(profile.get('expectedReturn'))
    
    # Debt
    total_debt = format_currency(profile.get('totalDebt'))
    car_payment = format_currency(profile.get('carPayment'))
    car_loan_balance = format_currency(profile.get('carLoanBalance'))
    student_loan_balance = format_currency(profile.get('studentLoanBalance'))
    student_loan_rate = format_percent(profile.get('studentLoanRate'))
    credit_card_limit = format_currency(profile.get('creditCardLimit'))
    credit_utilization = format_percent(profile.get('creditUtilization'))
    credit_card_rate = format_percent(profile.get('creditCardRate'))
    other_debt_payment = format_currency(profile.get('otherDebtPayment'))
    other_debt_balance = format_currency(profile.get('otherDebtBalance'))
    other_debt_description = profile.get('otherDebtDescription', 'Not specified')
    
    # Housing
    housing_status = profile.get('housingStatus', 'Not specified')
    housing_payment = format_currency(profile.get('housingPayment'))
    mortgage_balance = format_currency(profile.get('mortgageBalance'))
    mortgage_rate = format_percent(profile.get('mortgageRate'))
    
    # Insurance
    life_insurance_value = format_currency(profile.get('lifeInsuranceValue'))
    health_insurance_deductible = format_currency(profile.get('healthInsuranceDeductible'))
    health_insurance_premium = format_currency(profile.get('healthInsurancePremium'))
    homeowners_insurance = format_currency(profile.get('homeownersInsurance'))
    auto_insurance = format_currency(profile.get('autoInsurance'))
    
    # Tax & Benefits
    hsa_balance = format_currency(profile.get('hsaBalance'))
    hsa_contribution = format_currency(profile.get('hsaContribution'))
    fsa_contribution = format_currency(profile.get('fsaContribution'))
    childcare_benefits = format_currency(profile.get('childcareBenefits'))
    
    # Goals & Planning
    savings_goal = format_currency(profile.get('savingsGoal'))
    retirement_goal = format_currency(profile.get('retirementGoal'))
    retirement_age = profile.get('retirementAge', 'Not specified')
    current_age = profile.get('currentAge', 'Not specified')
    dependents = profile.get('dependents', 'Not specified')
    tax_filing_status = profile.get('taxFilingStatus', 'Not specified')
    risk_tolerance = profile.get('riskTolerance', 'Not specified')
    financial_goals = profile.get('financialGoals', 'Not specified')
    planned_expenses = profile.get('plannedExpenses', 'Not specified')
    education_savings_goal = format_currency(profile.get('educationSavingsGoal'))
    education_529_balance = format_currency(profile.get('education529Balance'))
    charitable_giving = format_currency(profile.get('charitableGiving'))
    
    # Retirement Planning
    social_security_estimate = format_currency(profile.get('socialSecurityEstimate'))
    pension_benefit = format_currency(profile.get('pensionBenefit'))
    retirement_spending = format_currency(profile.get('retirementSpending'))
    
    # Calculate derived metrics
    monthly_income = 0
    monthly_savings_potential = 0
    total_monthly_debt_payments = 0
    net_worth = 0
    
    try:
        if profile.get('annualIncome'):
            monthly_income = int(profile['annualIncome']) / 12
        
        # Calculate total monthly debt payments
        if profile.get('housingPayment'):
            total_monthly_debt_payments += int(profile['housingPayment'])
        if profile.get('carPayment'):
            total_monthly_debt_payments += int(profile['carPayment'])
        if profile.get('otherDebtPayment'):
            total_monthly_debt_payments += int(profile['otherDebtPayment'])
        
        # Calculate net worth (assets - liabilities)
        assets = 0
        liabilities = 0
        
        if profile.get('currentSavings'):
            assets += int(profile['currentSavings'])
        if profile.get('totalInvestments'):
            assets += int(profile['totalInvestments'])
        if profile.get('retirementAccounts'):
            assets += int(profile['retirementAccounts'])
        
        if profile.get('totalDebt'):
            liabilities += int(profile['totalDebt'])
        if profile.get('mortgageBalance'):
            liabilities += int(profile['mortgageBalance'])
        if profile.get('carLoanBalance'):
            liabilities += int(profile['carLoanBalance'])
        if profile.get('otherDebtBalance'):
            liabilities += int(profile['otherDebtBalance'])
        
        net_worth = assets - liabilities
        
        if profile.get('monthlyExpenses') and monthly_income > 0:
            monthly_savings_potential = monthly_income - int(profile['monthlyExpenses']) - total_monthly_debt_payments
    except Exception as e:
        logger.warning(f"Error calculating metrics: {e}")
    
    context = f"""
INCOME & CASH FLOW:
- Annual Income: {annual_income}
- Monthly Income: ${monthly_income:,.0f}
- Expected Annual Bonus/Commission: {bonus_income}
- Monthly Side/Passive Income: {side_income}
- Monthly Expenses: {monthly_expenses}
- Tax Filing Status: {tax_filing_status}

SAVINGS & EMERGENCY FUND:
- Current Savings: {current_savings}
- Emergency Fund: {emergency_fund}
- Emergency Fund Goal: {emergency_fund_goal}

INVESTMENTS:
- Total Investments: {total_investments}
- Taxable Investments: {taxable_investments}
- Tax-Advantaged Investments: {tax_advantaged_investments}
- Retirement Accounts (401k/IRA): {retirement_accounts}
- Monthly Investment Contribution: {monthly_investment}
- Investment Types: {investment_types}
- Asset Allocation: {asset_allocation}
- Expected Annual Return: {expected_return}
- Employer 401k Match: {employer_match}

DEBT OBLIGATIONS:
- Total Debt: {total_debt}
- Monthly Debt Payments: ${total_monthly_debt_payments:,.0f}
- Student Loan Balance: {student_loan_balance} (Rate: {student_loan_rate})
- Credit Card Limit: {credit_card_limit} (Utilization: {credit_utilization}, Rate: {credit_card_rate})
- Car Payment: {car_payment} (Balance: {car_loan_balance})
- Other Debt Payment: {other_debt_payment} (Balance: {other_debt_balance})
- Other Debt Type: {other_debt_description}

HOUSING:
- Housing Status: {housing_status}
- Monthly Housing Payment: {housing_payment}
- Mortgage Balance: {mortgage_balance}
- Mortgage Rate: {mortgage_rate}

INSURANCE COVERAGE:
- Life Insurance: {life_insurance_value}
- Health Insurance Deductible: {health_insurance_deductible}
- Health Insurance Premium: {health_insurance_premium}
- Homeowners/Renters Insurance: {homeowners_insurance}
- Auto Insurance: {auto_insurance}

TAX & BENEFITS:
- HSA Balance: {hsa_balance}
- Annual HSA Contribution: {hsa_contribution}
- Annual FSA Contribution: {fsa_contribution}
- Childcare/Dependent Care Benefits: {childcare_benefits}

GOALS & PLANNING:
- Savings Goal: {savings_goal}
- Retirement Goal: {retirement_goal}
- Current Age: {current_age}
- Target Retirement Age: {retirement_age}
- Years Until Retirement: {int(retirement_age) - int(current_age) if retirement_age != 'Not specified' and current_age != 'Not specified' else 'Not calculated'}
- Desired Annual Retirement Spending: {retirement_spending}
- Social Security Estimate: {social_security_estimate}
- Pension Benefit: {pension_benefit}
- Number of Dependents: {dependents}
- Risk Tolerance: {risk_tolerance}
- Financial Goals: {financial_goals}
- Planned Large Expenses: {planned_expenses}
- Education Savings Goal: {education_savings_goal}
- 529 Plan Balance: {education_529_balance}
- Annual Charitable Giving: {charitable_giving}

CALCULATED METRICS:
- Estimated Net Worth: ${net_worth:,.0f}
- Monthly Savings Potential: ${monthly_savings_potential:,.0f}
"""
    
    return context.strip()

def create_response(status_code, body):
    """Create API Gateway response"""
    return {
        'statusCode': status_code,
        'headers': CORS_HEADERS,
        'body': json.dumps(body)
    }

# Example Request:
# {
#     "question": "Should I pay off my debt or invest more?",
#     "profile": {
#         "annualIncome": "75000",
#         "monthlyExpenses": "3000",
#         "currentSavings": "10000",
#         "totalDebt": "25000",
#         "savingsGoal": "50000",
#         "riskTolerance": "moderate",
#         "financialGoals": "Buy a house in 5 years"
#     }
# }

# Example Response:
# {
#     "success": true,
#     "advice": "Based on your financial situation..."
# }
