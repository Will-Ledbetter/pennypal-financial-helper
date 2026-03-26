// Configuration - UPDATE THESE WITH YOUR AWS VALUES
const AWS_CONFIG = {
    region: 'us-east-1',
    userPoolId: 'us-east-1_Nmvta5ZLQ',      // Update this
    clientId: 'uc6cmidga31h3olddhib899nv',            // Update this
    apiEndpoint: 'https://emhxnvn3j7.execute-api.us-east-1.amazonaws.com/prod'    // Update this
};

// Initialize Cognito
const poolData = {
    UserPoolId: AWS_CONFIG.userPoolId,
    ClientId: AWS_CONFIG.clientId
};
const userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);

// Global variables
let currentUser = null;
let idToken = null;
let userProfile = null;

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    checkAuthentication();
    setupEventListeners();
});

// Check if user is authenticated
function checkAuthentication() {
    const cognitoUser = userPool.getCurrentUser();
    
    if (!cognitoUser) {
        window.location.href = 'login.html';
        return;
    }
    
    cognitoUser.getSession((err, session) => {
        if (err || !session.isValid()) {
            window.location.href = 'login.html';
            return;
        }
        
        currentUser = cognitoUser;
        idToken = session.getIdToken().getJwtToken();
        
        // Get user attributes
        cognitoUser.getUserAttributes((err, attributes) => {
            if (err) {
                console.error('Error getting user attributes:', err);
                return;
            }
            
            const name = attributes.find(attr => attr.Name === 'name')?.Value || 'User';
            document.getElementById('user-name').textContent = name;
        });
        
        // Load user profile
        loadUserProfile();
    });
}

// Setup event listeners
function setupEventListeners() {
    // Logout
    document.getElementById('logout-btn').addEventListener('click', logout);
    
    // Edit profile
    document.getElementById('edit-profile-btn').addEventListener('click', openProfileModal);
    
    // Profile modal
    const modal = document.getElementById('profile-modal');
    const closeBtn = modal.querySelector('.close');
    closeBtn.addEventListener('click', closeProfileModal);
    
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeProfileModal();
        }
    });
    
    // Profile form submit
    document.getElementById('profile-form').addEventListener('submit', saveProfile);
    
    // Ask advisor
    document.getElementById('ask-btn').addEventListener('click', askAdvisor);
    
    // Enter key in question input
    document.getElementById('question-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey) {
            askAdvisor();
        }
    });
}

// Logout
function logout() {
    if (currentUser) {
        currentUser.signOut();
    }
    window.location.href = 'login.html';
}

// Load user profile
async function loadUserProfile() {
    try {
        const response = await fetch(`${AWS_CONFIG.apiEndpoint}/profile`, {
            method: 'GET',
            headers: {
                'Authorization': idToken,
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to load profile');
        }
        
        const data = await response.json();
        userProfile = data.profile;
        
        displayProfile(userProfile);
        displayUsageInfo(userProfile);
        
    } catch (error) {
        console.error('Error loading profile:', error);
        document.getElementById('profile-summary').innerHTML = 
            '<p class="error">Failed to load profile. Please try refreshing the page.</p>';
    }
}

// Display usage information
function displayUsageInfo(profile) {
    const tier = profile.subscriptionTier || 'free';
    const asked = profile.questionsAsked || 0;
    const limit = profile.questionsLimit || 10;
    const remaining = limit - asked;
    
    // Update the questions badge in header
    const questionsBadge = document.getElementById('questions-remaining');
    if (questionsBadge) {
        // Remove existing classes
        questionsBadge.className = 'questions-badge';
        
        if (tier === 'pro') {
            questionsBadge.textContent = '∞ Unlimited';
            questionsBadge.classList.add('pro');
        } else {
            // Only show count if we have valid data (questionsAsked exists in profile)
            if (profile.hasOwnProperty('questionsAsked')) {
                questionsBadge.textContent = `${remaining} Questions Left`;
                
                if (remaining === 0) {
                    questionsBadge.classList.add('danger');
                } else if (remaining <= 2) {
                    questionsBadge.classList.add('warning');
                }
            } else {
                // Show loading state if data not yet available
                questionsBadge.textContent = 'Loading...';
            }
        }
    }
}

// Display profile
function displayProfile(profile) {
    const summaryDiv = document.getElementById('profile-summary');
    
    if (!profile || Object.keys(profile).length === 0) {
        summaryDiv.innerHTML = '<p>No profile data yet. Click "Edit Profile" to get started!</p>';
        return;
    }
    
    const formatCurrency = (value) => {
        return value ? `$${parseInt(value).toLocaleString()}` : 'Not set';
    };
    
    const formatFilingStatus = (status) => {
        const statuses = {
            'single': 'Single',
            'married-jointly': 'Married Filing Jointly',
            'married-separately': 'Married Filing Separately',
            'head-of-household': 'Head of Household'
        };
        return statuses[status] || 'Not set';
    };
    
    summaryDiv.innerHTML = `
        <p><strong>Annual Income:</strong> ${formatCurrency(profile.annualIncome)}</p>
        <p><strong>Monthly Expenses:</strong> ${formatCurrency(profile.monthlyExpenses)}</p>
        <p><strong>Current Savings:</strong> ${formatCurrency(profile.currentSavings)}</p>
        <p><strong>Total Debt:</strong> ${formatCurrency(profile.totalDebt)}</p>
        <p><strong>Savings Goal:</strong> ${formatCurrency(profile.savingsGoal)}</p>
        <p><strong>Tax Filing Status:</strong> ${formatFilingStatus(profile.taxFilingStatus)}</p>
        <p><strong>Risk Tolerance:</strong> ${profile.riskTolerance || 'Not set'}</p>
        ${profile.financialGoals ? `<p><strong>Goals:</strong> ${profile.financialGoals}</p>` : ''}
    `;
}

// Open profile modal
function openProfileModal() {
    const modal = document.getElementById('profile-modal');
    
    // Populate form with existing data
    if (userProfile) {
        // Basic Info
        document.getElementById('annual-income').value = userProfile.annualIncome || '';
        document.getElementById('monthly-expenses').value = userProfile.monthlyExpenses || '';
        document.getElementById('current-savings').value = userProfile.currentSavings || '';
        document.getElementById('total-investments').value = userProfile.totalInvestments || '';
        document.getElementById('monthly-investment').value = userProfile.monthlyInvestment || '';
        document.getElementById('retirement-accounts').value = userProfile.retirementAccounts || '';
        document.getElementById('investment-types').value = userProfile.investmentTypes || '';
        document.getElementById('employer-match').value = userProfile.employerMatch || '';
        document.getElementById('total-debt').value = userProfile.totalDebt || '';
        document.getElementById('savings-goal').value = userProfile.savingsGoal || '';
        document.getElementById('retirement-goal').value = userProfile.retirementGoal || '';
        document.getElementById('retirement-age').value = userProfile.retirementAge || '';
        document.getElementById('current-age').value = userProfile.currentAge || '';
        document.getElementById('dependents').value = userProfile.dependents || '';
        document.getElementById('tax-filing-status').value = userProfile.taxFilingStatus || '';
        document.getElementById('housing-status').value = userProfile.housingStatus || '';
        document.getElementById('housing-payment').value = userProfile.housingPayment || '';
        document.getElementById('mortgage-balance').value = userProfile.mortgageBalance || '';
        document.getElementById('mortgage-rate').value = userProfile.mortgageRate || '';
        document.getElementById('car-payment').value = userProfile.carPayment || '';
        document.getElementById('car-loan-balance').value = userProfile.carLoanBalance || '';
        document.getElementById('other-debt-payment').value = userProfile.otherDebtPayment || '';
        document.getElementById('other-debt-balance').value = userProfile.otherDebtBalance || '';
        document.getElementById('other-debt-description').value = userProfile.otherDebtDescription || '';
        document.getElementById('risk-tolerance').value = userProfile.riskTolerance || 'moderate';
        document.getElementById('financial-goals').value = userProfile.financialGoals || '';
        
        // Insurance Coverage
        document.getElementById('life-insurance-value').value = userProfile.lifeInsuranceValue || '';
        document.getElementById('health-insurance-deductible').value = userProfile.healthInsuranceDeductible || '';
        document.getElementById('health-insurance-premium').value = userProfile.healthInsurancePremium || '';
        document.getElementById('homeowners-insurance').value = userProfile.homeownersInsurance || '';
        document.getElementById('auto-insurance').value = userProfile.autoInsurance || '';
        
        // Emergency Planning
        document.getElementById('emergency-fund').value = userProfile.emergencyFund || '';
        document.getElementById('emergency-fund-goal').value = userProfile.emergencyFundGoal || '';
        
        // Additional Income
        document.getElementById('bonus-income').value = userProfile.bonusIncome || '';
        document.getElementById('side-income').value = userProfile.sideIncome || '';
        
        // Investment Details
        document.getElementById('asset-allocation').value = userProfile.assetAllocation || '';
        document.getElementById('taxable-investments').value = userProfile.taxableInvestments || '';
        document.getElementById('tax-advantaged-investments').value = userProfile.taxAdvantagedInvestments || '';
        document.getElementById('expected-return').value = userProfile.expectedReturn || '';
        
        // Debt Details
        document.getElementById('credit-card-limit').value = userProfile.creditCardLimit || '';
        document.getElementById('credit-utilization').value = userProfile.creditUtilization || '';
        document.getElementById('student-loan-balance').value = userProfile.studentLoanBalance || '';
        document.getElementById('student-loan-rate').value = userProfile.studentLoanRate || '';
        document.getElementById('credit-card-rate').value = userProfile.creditCardRate || '';
        
        // Tax & Benefits
        document.getElementById('hsa-balance').value = userProfile.hsaBalance || '';
        document.getElementById('hsa-contribution').value = userProfile.hsaContribution || '';
        document.getElementById('fsa-contribution').value = userProfile.fsaContribution || '';
        document.getElementById('childcare-benefits').value = userProfile.childcareBenefits || '';
        
        // Lifestyle & Future Planning
        document.getElementById('planned-expenses').value = userProfile.plannedExpenses || '';
        document.getElementById('education-savings-goal').value = userProfile.educationSavingsGoal || '';
        document.getElementById('education-529-balance').value = userProfile.education529Balance || '';
        document.getElementById('charitable-giving').value = userProfile.charitableGiving || '';
        
        // Retirement Planning
        document.getElementById('social-security-estimate').value = userProfile.socialSecurityEstimate || '';
        document.getElementById('pension-benefit').value = userProfile.pensionBenefit || '';
        document.getElementById('retirement-spending').value = userProfile.retirementSpending || '';
    }
    
    modal.style.display = 'block';
}

// Close profile modal
function closeProfileModal() {
    document.getElementById('profile-modal').style.display = 'none';
}

// Save profile
async function saveProfile(e) {
    e.preventDefault();
    
    const profileData = {
        // Basic Info
        annualIncome: document.getElementById('annual-income').value,
        monthlyExpenses: document.getElementById('monthly-expenses').value,
        currentSavings: document.getElementById('current-savings').value,
        totalInvestments: document.getElementById('total-investments').value,
        monthlyInvestment: document.getElementById('monthly-investment').value,
        retirementAccounts: document.getElementById('retirement-accounts').value,
        investmentTypes: document.getElementById('investment-types').value,
        employerMatch: document.getElementById('employer-match').value,
        totalDebt: document.getElementById('total-debt').value,
        savingsGoal: document.getElementById('savings-goal').value,
        retirementGoal: document.getElementById('retirement-goal').value,
        retirementAge: document.getElementById('retirement-age').value,
        currentAge: document.getElementById('current-age').value,
        dependents: document.getElementById('dependents').value,
        taxFilingStatus: document.getElementById('tax-filing-status').value,
        housingStatus: document.getElementById('housing-status').value,
        housingPayment: document.getElementById('housing-payment').value,
        mortgageBalance: document.getElementById('mortgage-balance').value,
        mortgageRate: document.getElementById('mortgage-rate').value,
        carPayment: document.getElementById('car-payment').value,
        carLoanBalance: document.getElementById('car-loan-balance').value,
        otherDebtPayment: document.getElementById('other-debt-payment').value,
        otherDebtBalance: document.getElementById('other-debt-balance').value,
        otherDebtDescription: document.getElementById('other-debt-description').value,
        riskTolerance: document.getElementById('risk-tolerance').value,
        financialGoals: document.getElementById('financial-goals').value,
        
        // Insurance Coverage
        lifeInsuranceValue: document.getElementById('life-insurance-value').value,
        healthInsuranceDeductible: document.getElementById('health-insurance-deductible').value,
        healthInsurancePremium: document.getElementById('health-insurance-premium').value,
        homeownersInsurance: document.getElementById('homeowners-insurance').value,
        autoInsurance: document.getElementById('auto-insurance').value,
        
        // Emergency Planning
        emergencyFund: document.getElementById('emergency-fund').value,
        emergencyFundGoal: document.getElementById('emergency-fund-goal').value,
        
        // Additional Income
        bonusIncome: document.getElementById('bonus-income').value,
        sideIncome: document.getElementById('side-income').value,
        
        // Investment Details
        assetAllocation: document.getElementById('asset-allocation').value,
        taxableInvestments: document.getElementById('taxable-investments').value,
        taxAdvantagedInvestments: document.getElementById('tax-advantaged-investments').value,
        expectedReturn: document.getElementById('expected-return').value,
        
        // Debt Details
        creditCardLimit: document.getElementById('credit-card-limit').value,
        creditUtilization: document.getElementById('credit-utilization').value,
        studentLoanBalance: document.getElementById('student-loan-balance').value,
        studentLoanRate: document.getElementById('student-loan-rate').value,
        creditCardRate: document.getElementById('credit-card-rate').value,
        
        // Tax & Benefits
        hsaBalance: document.getElementById('hsa-balance').value,
        hsaContribution: document.getElementById('hsa-contribution').value,
        fsaContribution: document.getElementById('fsa-contribution').value,
        childcareBenefits: document.getElementById('childcare-benefits').value,
        
        // Lifestyle & Future Planning
        plannedExpenses: document.getElementById('planned-expenses').value,
        educationSavingsGoal: document.getElementById('education-savings-goal').value,
        education529Balance: document.getElementById('education-529-balance').value,
        charitableGiving: document.getElementById('charitable-giving').value,
        
        // Retirement Planning
        socialSecurityEstimate: document.getElementById('social-security-estimate').value,
        pensionBenefit: document.getElementById('pension-benefit').value,
        retirementSpending: document.getElementById('retirement-spending').value
    };
    
    try {
        const response = await fetch(`${AWS_CONFIG.apiEndpoint}/profile`, {
            method: 'POST',
            headers: {
                'Authorization': idToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(profileData)
        });
        
        if (!response.ok) {
            throw new Error('Failed to save profile');
        }
        
        const data = await response.json();
        userProfile = data.profile;
        
        displayProfile(userProfile);
        closeProfileModal();
        
        alert('Profile saved successfully!');
        
    } catch (error) {
        console.error('Error saving profile:', error);
        alert('Failed to save profile. Please try again.');
    }
}

// Ask advisor
async function askAdvisor() {
    const questionInput = document.getElementById('question-input');
    const question = questionInput.value.trim();
    
    if (!question) {
        alert('Please enter a question');
        return;
    }
    
    if (!userProfile || Object.keys(userProfile).length === 0) {
        alert('Please set up your financial profile first!');
        openProfileModal();
        return;
    }
    
    // Show loading
    document.getElementById('loading-indicator').style.display = 'block';
    document.getElementById('advice-response').style.display = 'none';
    document.getElementById('ask-btn').disabled = true;
    
    try {
        console.log('Sending request to advisor API...');
        console.log('Profile data:', userProfile);
        
        const response = await fetch(`${AWS_CONFIG.apiEndpoint}/advice`, {
            method: 'POST',
            headers: {
                'Authorization': idToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                profile: userProfile
            })
        });
        
        console.log('Response status:', response.status);
        
        const data = await response.json();
        console.log('Response data:', data);
        
        if (!response.ok) {
            const errorMsg = data.error || 'Failed to get advice';
            throw new Error(errorMsg);
        }
        
        if (!data.advice || data.advice.trim() === '') {
            throw new Error('Received empty advice from server');
        }
        
        // Update usage info if provided
        if (data.usage) {
            userProfile.questionsAsked = data.usage.questionsAsked;
            userProfile.questionsLimit = data.usage.questionsLimit;
            displayUsageInfo(userProfile);
        }
        
        // Display advice
        displayAdvice(question, data.advice, data.usage);
        
        // Clear input
        questionInput.value = '';
        
        // Add to history
        addToHistory(question, data.advice);
        
    } catch (error) {
        console.error('Error getting advice:', error);
        console.error('Error details:', error.message);
        
        // Check if it's a usage limit error
        if (error.message.includes('Usage limit reached') || error.message.includes('limit')) {
            alert(`❌ ${error.message}\n\nPro version not yet released.`);
        } else {
            alert(`Failed to get advice: ${error.message}\n\nPlease check the browser console for more details.`);
        }
    } finally {
        document.getElementById('loading-indicator').style.display = 'none';
        document.getElementById('ask-btn').disabled = false;
    }
}

// Display advice
function displayAdvice(question, advice, usage) {
    const adviceContent = document.getElementById('advice-content');
    const adviceResponse = document.getElementById('advice-response');
    
    // Format the advice (convert line breaks to paragraphs)
    const formattedAdvice = advice
        .split('\n\n')
        .map(para => `<p>${para.replace(/\n/g, '<br>')}</p>`)
        .join('');
    
    // Add usage info if available
    let usageInfo = '';
    if (usage) {
        const remaining = usage.questionsRemaining;
        if (remaining <= 3 && remaining > 0) {
            usageInfo = `
                <div style="background: #fff3cd; padding: 12px; border-radius: 6px; margin-bottom: 15px; border-left: 4px solid #ffc107;">
                    ⚠️ <strong>Note:</strong> You have ${remaining} question${remaining === 1 ? '' : 's'} remaining in your free tier.
                </div>
            `;
        }
    }
    
    adviceContent.innerHTML = `
        <div style="background: #e7f3ff; padding: 15px; border-radius: 6px; margin-bottom: 15px;">
            <strong>Your Question:</strong> ${question}
        </div>
        ${usageInfo}
        ${formattedAdvice}
    `;
    
    adviceResponse.style.display = 'block';
    adviceResponse.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Add to conversation history
function addToHistory(question, answer) {
    const historyDiv = document.getElementById('conversation-history');
    
    // Remove empty state if present
    const emptyState = historyDiv.querySelector('.empty-state');
    if (emptyState) {
        emptyState.remove();
    }
    
    // Create conversation item
    const item = document.createElement('div');
    item.className = 'conversation-item';
    
    const timestamp = new Date().toLocaleString();
    
    // Truncate answer for history display
    const shortAnswer = answer.length > 200 ? answer.substring(0, 200) + '...' : answer;
    
    item.innerHTML = `
        <div class="question">Q: ${question}</div>
        <div class="answer">A: ${shortAnswer}</div>
        <div class="timestamp">${timestamp}</div>
    `;
    
    // Add to top of history
    historyDiv.insertBefore(item, historyDiv.firstChild);
    
    // Keep only last 5 conversations
    const items = historyDiv.querySelectorAll('.conversation-item');
    if (items.length > 5) {
        items[items.length - 1].remove();
    }
}

// Helper function to format currency
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}
