// Personal Finance & Wealth Simulator - Static Demo JavaScript
// Implements all financial calculations in pure JavaScript

// Utility function to format numbers as Indian Rupees
function formatINR(value) {
    if (value === null || value === undefined || isNaN(value)) {
        return "N/A";
    }

    try {
        const number = Math.round(parseFloat(value));
        const sign = number < 0 ? "-" : "";
        const digits = String(Math.abs(number));

        if (digits.length <= 3) {
            return `â‚¹${sign}${digits}`;
        }

        const lastThree = digits.slice(-3);
        let remaining = digits.slice(0, -3);
        const groups = [];

        while (remaining.length > 0) {
            if (remaining.length >= 2) {
                groups.unshift(remaining.slice(-2));
                remaining = remaining.slice(0, -2);
            } else {
                groups.unshift(remaining);
                remaining = "";
            }
        }

        const formatted = groups.join(",") + "," + lastThree;
        return `â‚¹${sign}${formatted}`;
    } catch (e) {
        return "N/A";
    }
}
function validateAndClamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
}

// Core wealth projection calculation (matches financial_engine/core/calculations.py)
function calculateProjection(inputs) {
    // Extract inputs
    const currentAge = inputs.current_age;
    const targetAge = inputs.target_age;
    let currentSavings = inputs.current_savings;
    const monthlyIncome = inputs.monthly_income;
    const monthlyExpenses = inputs.monthly_expenses;
    const monthlyInvestmentContribution = inputs.monthly_investment_contribution;
    const annualIncomeGrowthPct = inputs.annual_income_growth_pct;
    const annualExpenseGrowthPct = inputs.annual_expense_growth_pct;
    const expectedAnnualReturnPct = inputs.expected_annual_return_pct;
    const annualInflationPct = inputs.annual_inflation_pct;

    // Convert percentages to decimals
    const incomeGrowthRate = annualIncomeGrowthPct / 100.0;
    const expenseGrowthRate = annualExpenseGrowthPct / 100.0;
    const returnRate = expectedAnnualReturnPct / 100.0;
    const inflationRate = annualInflationPct / 100.0;

    // Initialize results
    const projectionResults = [];

    // Initialize wealth tracking
    let startingInvestedWealth = currentSavings; // All current savings treated as invested
    let startingCashWealth = 0.0;

    // Initialize cumulative trackers
    let cumulativeContributions = 0.0;
    let cumulativeInvestmentReturns = 0.0;

    // Calculate projection for each year
    for (let yearOffset = 0; yearOffset < targetAge - currentAge; yearOffset++) {
        const currentYearAge = currentAge + yearOffset + 1;

        // Calculate growth factors
        const yearsElapsed = yearOffset;
        const incomeGrowthFactor = Math.pow(1.0 + incomeGrowthRate, yearsElapsed);
        const expenseGrowthFactor = Math.pow(1.0 + expenseGrowthRate, yearsElapsed);
        const inflationFactor = Math.pow(1.0 + inflationRate, yearsElapsed);

        // Calculate annual values
        const annualIncome = monthlyIncome * 12.0 * incomeGrowthFactor;
        const annualExpenses = monthlyExpenses * 12.0 * expenseGrowthFactor;
        const annualSavings = annualIncome - annualExpenses;
        const annualInvestmentContribution = monthlyInvestmentContribution * 12.0; // Fixed nominal

        // Calculate uninvested cash savings
        const uninvestedCashSavings = Math.max(0, annualSavings - annualInvestmentContribution);

        // Calculate investment return (beginning of year timing)
        const investmentReturn = (startingInvestedWealth + annualInvestmentContribution) * returnRate;

        // Calculate ending wealth values
        const endingInvestedWealth = startingInvestedWealth + annualInvestmentContribution + investmentReturn;
        const endingCashWealth = startingCashWealth + uninvestedCashSavings;
        const endingNominalWealth = endingInvestedWealth + endingCashWealth;

        // Calculate inflation-adjusted/real wealth
        const inflationAdjustedWealth = inflationFactor > 0 ? endingNominalWealth / inflationFactor : endingNominalWealth;

        // Update cumulative trackers
        cumulativeContributions += annualInvestmentContribution;
        cumulativeInvestmentReturns += investmentReturn;

        // Create result record
        const yearResult = {
            age: currentYearAge,
            starting_invested_wealth: startingInvestedWealth,
            starting_cash_wealth: startingCashWealth,
            annual_income: annualIncome,
            annual_expenses: annualExpenses,
            annual_savings: annualSavings,
            annual_investment_contribution: annualInvestmentContribution,
            uninvested_cash_savings: uninvestedCashSavings,
            investment_returns: investmentReturn,
            ending_invested_wealth: endingInvestedWealth,
            ending_cash_wealth: endingCashWealth,
            ending_nominal_wealth: endingNominalWealth,
            inflation_adjusted_wealth: inflationAdjustedWealth,
            cumulative_contributions: cumulativeContributions,
            cumulative_investment_returns: cumulativeInvestmentReturns
        };

        projectionResults.push(yearResult);

        // Set starting values for next year
        startingInvestedWealth = endingInvestedWealth;
        startingCashWealth = endingCashWealth;
    }

    return projectionResults;
}

// Scenario comparison calculations (matches v2_extensions/scenario_comparison.py)
function createScenarioInputs(baseInputs, scenarioType, customModifications = {}) {
    const validScenarios = ['base', 'conservative', 'optimistic', 'custom'];
    if (!validScenarios.includes(scenarioType)) {
        throw new Error(`scenarioType must be one of ${validScenarios.join(', ')}, got '${scenarioType}'`);
    }

    // Base scenario: no modifications
    if (scenarioType === 'base') {
        return { inputs: { ...baseInputs }, warnings: [] };
    }

    // Define scenario deltas: [return_delta, income_growth_delta, expense_growth_delta, inflation_delta]
    const scenarioDeltas = {
        'conservative': [-2.0, -1.0, +1.0, +1.0],
        'optimistic': [+2.0, +1.0, -1.0, -1.0]
    };

    let modifications = {};

    if (scenarioType in scenarioDeltas) {
        const deltas = scenarioDeltas[scenarioType];
        modifications = {
            expected_annual_return_pct_delta: deltas[0],
            annual_income_growth_pct_delta: deltas[1],
            annual_expense_growth_pct_delta: deltas[2],
            annual_inflation_pct_delta: deltas[3]
        };
    } else if (scenarioType === 'custom') {
        modifications = customModifications;
    }

    // Apply modifications and clamp to valid ranges
    const inputs = { ...baseInputs };
    const warnings = [];

    // Process each modification
    if (modifications.expected_annual_return_pct_delta !== undefined) {
        const delta = parseFloat(modifications.expected_annual_return_pct_delta) || 0;
        const newValue = inputs.expected_annual_return_pct + delta;
        inputs.expected_annual_return_pct = validateAndClamp(newValue, 0, 20);
        if (newValue < 0 || newValue > 20) {
            warnings.push(`Expected annual return clamped to ${inputs.expected_annual_return_pct}%`);
        }
    }

    if (modifications.annual_income_growth_pct_delta !== undefined) {
        const delta = parseFloat(modifications.annual_income_growth_pct_delta) || 0;
        const newValue = inputs.annual_income_growth_pct + delta;
        inputs.annual_income_growth_pct = validateAndClamp(newValue, 0, 20);
        if (newValue < 0 || newValue > 20) {
            warnings.push(`Annual income growth clamped to ${inputs.annual_income_growth_pct}%`);
        }
    }

    if (modifications.annual_expense_growth_pct_delta !== undefined) {
        const delta = parseFloat(modifications.annual_expense_growth_pct_delta) || 0;
        const newValue = inputs.annual_expense_growth_pct + delta;
        inputs.annual_expense_growth_pct = validateAndClamp(newValue, 0, 20);
        if (newValue < 0 || newValue > 20) {
            warnings.push(`Annual expense growth clamped to ${inputs.annual_expense_growth_pct}%`);
        }
    }

    if (modifications.annual_inflation_pct_delta !== undefined) {
        const delta = parseFloat(modifications.annual_inflation_pct_delta) || 0;
        const newValue = inputs.annual_inflation_pct + delta;
        inputs.annual_inflation_pct = validateAndClamp(newValue, 0, 10);
        if (newValue < 0 || newValue > 10) {
            warnings.push(`Annual inflation clamped to ${inputs.annual_inflation_pct}%`);
        }
    }

    return { inputs, warnings };
}

function runScenarioComparison(baseInputs) {
    const scenarioTypes = ['base', 'conservative', 'optimistic', 'custom'];
    const scenarios = {};

    // Validate base inputs first (simplified validation)
    const validatedBaseInputs = { ...baseInputs };

    // Run each scenario
    for (const scenarioType of scenarioTypes) {
        try {
            // For custom scenario, use empty modifications (simplified)
            const customMods = scenarioType === 'custom' ? {} : null;
            const { inputs, warnings } = createScenarioInputs(
                validatedBaseInputs,
                scenarioType,
                customMods
            );

            // Run projection
            const projection = calculateProjection(inputs);

            scenarios[scenarioType] = {
                inputs: inputs,
                projection: projection,
                warnings: warnings
            };
        } catch (error) {
            scenarios[scenarioType] = {
                error: error.message,
                inputs: null,
                projection: [],
                warnings: []
            };
        }
    }

    // Create summary
    const wealthComparison = {};
    const assumptionComparison = {};

    // Extract ending wealth values
    for (const scenarioType of scenarioTypes) {
        if (scenarios[scenarioType] && scenarios[scenarioType].projection && scenarios[scenarioType].projection.length > 0) {
            const projection = scenarios[scenarioType].projection;
            wealthComparison[scenarioType] = projection[projection.length - 1].ending_nominal_wealth;
        } else {
            wealthComparison[scenarioType] = null;
        }
    }

    // Extract key assumptions for comparison
    const keyParams = ['expected_annual_return_pct', 'annual_income_growth_pct', 'annual_expense_growth_pct', 'annual_inflation_pct'];
    for (const param of keyParams) {
        assumptionComparison[param] = {};
        for (const scenarioType of scenarioTypes) {
            if (scenarios[scenarioType] && scenarios[scenarioType].inputs) {
                assumptionComparison[param][scenarioType] = scenarios[scenarioType].inputs[param];
            } else {
                assumptionComparison[param][scenarioType] = null;
            }
        }
    }

    return {
        scenarios: scenarios,
        summary: {
            wealth_comparison: wealthComparison,
            assumption_comparison: assumptionComparison
        }
    };
}

// Goal planner calculations (matches goal_planner/goal_calculations.py)
function validateGoalPlannerInputs(currentAge, goalAge, targetCorpus, currentSavings, expectedAnnualReturnPct) {
    // Validate currentAge
    if (!Number.isInteger(currentAge)) {
        throw new TypeError("current_age must be an integer");
    }
    if (currentAge < 0) {
        throw new ValueError("current_age must be >= 0");
    }

    // Validate goalAge
    if (!Number.isInteger(goalAge)) {
        throw new TypeError("goal_age must be an integer");
    }
    if (goalAge <= currentAge) {
        throw new Error("goal_age must be greater than current_age");
    }

    // Validate targetCorpus
    if (typeof targetCorpus !== 'number') {
        throw new TypeError("target_corpus must be a number");
    }
    if (targetCorpus < 0) {
        throw new Error("target_corpus must be >= 0");
    }

    // Validate currentSavings
    if (typeof currentSavings !== 'number') {
        throw new TypeError("current_savings must be a number");
    }
    if (currentSavings < 0) {
        throw new Error("current_savings must be >= 0");
    }

    // Validate expectedAnnualReturnPct
    if (typeof expectedAnnualReturnPct !== 'number') {
        throw new TypeError("expected_annual_return_pct must be a number");
    }
    if (expectedAnnualReturnPct < 0) {
        throw new Error("expected_annual_return_pct must be >= 0");
    }

    return {
        currentAge: parseFloat(currentAge),
        goalAge: parseFloat(goalAge),
        targetCorpus: parseFloat(targetCorpus),
        currentSavings: parseFloat(currentSavings),
        expectedAnnualReturnPct: parseFloat(expectedAnnualReturnPct)
    };
}

function calculateGoalPlanner(currentAge, goalAge, targetCorpus, currentSavings, expectedAnnualReturnPct) {
    // Validate inputs
    const validated = validateGoalPlannerInputs(currentAge, goalAge, targetCorpus, currentSavings, expectedAnnualReturnPct);

    // Extract validated values
    const P = validated.currentSavings; // Current corpus
    const rAnnual = validated.expectedAnnualReturnPct / 100.0; // Annual return as decimal
    const nYears = validated.goalAge - validated.currentAge; // Years available
    const T = validated.targetCorpus; // Target corpus

    // Calculate years available
    const yearsAvailable = nYears;

    // Handle zero return case separately
    let requiredMonthly;
    if (rAnnual === 0) {
        // PMT = max(0, (T - P) / (12 * n))
        requiredMonthly = yearsAvailable > 0 ? Math.max(0, (T - P) / (12 * yearsAvailable)) : 0;
    } else {
        // Monthly return rate
        const rMonthly = rAnnual / 12.0;
        // Number of monthly periods
        const nMonths = yearsAvailable * 12;

        // Future value of current corpus
        const fvCurrent = P * Math.pow(1 + rMonthly, nMonths);

        // If current corpus already grows to >= target
        if (fvCurrent >= T) {
            requiredMonthly = 0;
        } else {
            // Calculate denominator: [((1 + r/12)^(12n) - 1) / (r/12)]
            const denominator = (Math.pow(1 + rMonthly, nMonths) - 1) / rMonthly;

            // Solve for PMT: PMT = (T - P * (1 + r/12)^(12n)) / denominator
            requiredMonthly = (T - fvCurrent) / denominator;

            // Ensure non-negative
            requiredMonthly = Math.max(0, requiredMonthly);
        }
    }

    // Calculate required annual investment
    const requiredAnnual = requiredMonthly * 12;

    // Calculate total future contributions
    const totalFutureContributions = requiredMonthly * 12 * yearsAvailable;

    // Calculate projected corpus
    let projectedCorpus;
    if (rAnnual === 0) {
        projectedCorpus = P + (requiredMonthly * 12 * yearsAvailable);
    } else {
        const rMonthly = rAnnual / 12.0;
        const nMonths = yearsAvailable * 12;
        const fvCurrent = P * Math.pow(1 + rMonthly, nMonths);
        const fvContributions = requiredMonthly * (Math.pow(1 + rMonthly, nMonths) - 1) / rMonthly;
        projectedCorpus = fvCurrent + fvContributions;
    }

    // Calculate estimated investment returns
    const estimatedInvestmentReturns = projectedCorpus - P - totalFutureContributions;

    // Calculate surplus/shortfall versus target
    const surplusOrShortfall = projectedCorpus - T;
    const goalReached = surplusOrShortfall >= -0.01; // Small tolerance for floating point

    // Generate year-by-year projection
    const yearByYear = generateYearByYearProjectionFixed(
        currentAge, goalAge, P, T, expectedAnnualReturnPct, requiredMonthly
    );

    return {
        required_monthly_investment: requiredMonthly,
        required_annual_investment: requiredAnnual,
        years_available: yearsAvailable,
        total_future_contributions: totalFutureContributions,
        estimated_investment_returns: estimatedInvestmentReturns,
        projected_corpus: projectedCorpus,
        surplus_or_shortfall: surplusOrShortfall,
        goal_reached: goalReached,
        year_by_year_projection: yearByYear,
        target_corpus: T
    };
}

function generateYearByYearProjectionFixed(currentAge, goalAge, currentCorpus, targetCorpus, annualReturnPct, monthlyContribution) {
    const projection = [];

    // Convert to decimals
    const rAnnual = annualReturnPct / 100.0;
    const rMonthly = rAnnual !== 0 ? rAnnual / 12.0 : 0;

    // Starting values
    let corpusAtStartOfYear = currentCorpus;

    // Loop for each year from currentAge to goalAge-1
    for (let yearNum = 1; yearNum <= goalAge - currentAge; yearNum++) {
        const yearStartAge = currentAge + (yearNum - 1);
        const yearEndAge = currentAge + yearNum;

        const startingCorpus = corpusAtStartOfYear;
        const annualContribution = monthlyContribution * 12;

        let investmentReturns;
        let endingCorpus;

        if (rAnnual === 0) {
            investmentReturns = 0;
            endingCorpus = startingCorpus + annualContribution;
        } else {
            // Value at start of year
            const startValue = corpusAtStartOfYear;
            // Value at end of year
            const endValue = corpusAtStartOfYear * Math.pow(1 + rMonthly, 12) +
                           monthlyContribution * (Math.pow(1 + rMonthly, 12) - 1) / rMonthly;

            endingCorpus = endValue;
            investmentReturns = endingCorpus - startingCorpus - annualContribution;
        }

        const yearRecord = {
            Age: yearStartAge,
            Year: yearNum,
            'Starting Corpus': startingCorpus,
            'Annual Contributions': annualContribution,
            'Investment Returns': investmentReturns,
            'Ending Corpus': endingCorpus,
            'Target Corpus': targetCorpus
        };

        projection.push(yearRecord);

        // Update for next year
        corpusAtStartOfYear = endingCorpus;
    }

    return projection;
}

// Chart instances
let wealthChart = null;
let compositionChart = null;
let savingsChart = null;
let scenarioChart = null;
let goalChart = null;

// DOM Content Loaded
if (typeof document !== 'undefined') {
document.addEventListener('DOMContentLoaded', function() {
    // Tab switching functionality
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabPanels = document.querySelectorAll('.tab-panel');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all buttons and panels
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanels.forEach(panel => panel.classList.remove('active'));

            // Add active class to clicked button
            button.classList.add('active');

            // Show corresponding panel
            const tabId = button.getAttribute('data-tab');
            const targetPanel = document.getElementById(tabId);
            if (targetPanel) {
                targetPanel.classList.add('active');
            }
        });
    });

    // Wealth Simulator Form Handling
    const wealthForm = document.getElementById('wealth-form');
    const wealthResults = document.getElementById('wealth-results');

    if (wealthForm) {
        wealthForm.addEventListener('submit', function(e) {
            e.preventDefault();
            calculateWealthProjection();
        });
    }

    // Scenario Comparison Form Handling
    const scenarioForm = document.getElementById('scenario-form');
    const scenarioResults = document.getElementById('scenario-results');

    if (scenarioForm) {
        scenarioForm.addEventListener('submit', function(e) {
            e.preventDefault();
            calculateScenarioComparison();
        });
    }

    // Goal Planner Form Handling
    const goalForm = document.getElementById('goal-form');
    const goalResults = document.getElementById('goal-results');

    if (goalForm) {
        goalForm.addEventListener('submit', function(e) {
            e.preventDefault();
            calculateGoalPlannerResult();
        });
    }
});
}

// Wealth Projection Calculation
function calculateWealthProjection() {
    // Show loading state
    const wealthResults = document.getElementById('wealth-results');
    wealthResults.innerHTML = '<div class="loading"><div>Calculating projection...</div></div>';

    try {
        // Get form values
        const inputs = {
            current_age: parseInt(document.getElementById('current-age').value),
            target_age: parseInt(document.getElementById('target-age').value),
            current_savings: parseFloat(document.getElementById('current-savings').value),
            monthly_income: parseFloat(document.getElementById('monthly-income').value),
            monthly_expenses: parseFloat(document.getElementById('monthly-expenses').value),
            monthly_investment_contribution: parseFloat(document.getElementById('monthly-investment').value),
            annual_income_growth_pct: parseFloat(document.getElementById('annual-income-growth').value),
            annual_expense_growth_pct: parseFloat(document.getElementById('annual-expense-growth').value),
            expected_annual_return_pct: parseFloat(document.getElementById('expected-return').value),
            annual_inflation_pct: parseFloat(document.getElementById('annual-inflation').value)
        };

        // Validate investment contribution doesn't exceed available savings
        const availableSavings = inputs.monthly_income - inputs.monthly_expenses;
        if (inputs.monthly_investment_contribution > availableSavings) {
            throw new Error(`Monthly investment contribution (â‚¹${formatINR(inputs.monthly_investment_contribution)}) cannot exceed available savings (â‚¹${formatINR(availableSavings)})`);
        }

        // Calculate projection
        const projection = calculateProjection(inputs);

        // Display results
        displayWealthResults(projection, inputs);
    } catch (error) {
        wealthResults.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    }
}

// Display Wealth Results
function displayWealthResults(projection, inputs) {
    const wealthResults = document.getElementById('wealth-results');
    if (!projection || projection.length === 0) {
        wealthResults.innerHTML = '<div class="no-results">No projection data available.</div>';
        return;
    }

    const df = projection;
    const finalYear = df[df.length - 1];

    // Summary metrics
    let metricsHTML = `
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">Final Nominal Wealth</div>
                <div class="metric-value">${formatINR(finalYear.ending_nominal_wealth)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Final Real Wealth</div>
                <div class="metric-value">${formatINR(finalYear.inflation_adjusted_wealth)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Contributions</div>
                <div class="metric-value">${formatINR(finalYear.cumulative_contributions)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Total Investment Returns</div>
                <div class="metric-value">${formatINR(finalYear.cumulative_investment_returns)}</div>
            </div>
        </div>
    `;

    // Charts section
    let chartsHTML = `
        <div class="chart-wrapper">
            <h3 class="chart-title">Wealth Projection Over Time</h3>
            <div class="chart-container">
                <canvas id="wealth-chart"></canvas>
            </div>
        </div>

        <div class="chart-wrapper">
            <h3 class="chart-title">Wealth Composition: Invested vs Cash</h3>
            <div class="chart-container">
                <canvas id="composition-chart"></canvas>
            </div>
        </div>

        <div class="chart-wrapper">
            <h3 class="chart-title">Annual Savings Breakdown</h3>
            <div class="chart-container">
                <canvas id="savings-chart"></canvas>
            </div>
        </div>
    `;

    // Annual details table
    let tableHTML = `
        <div class="table-container">
            <div class="table-title">Annual Projection Details</div>
            <div class="table-scroll">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Age</th>
                            <th>Starting Invested (â‚¹)</th>
                            <th>Starting Cash (â‚¹)</th>
                            <th>Annual Income (â‚¹)</th>
                            <th>Annual Expenses (â‚¹)</th>
                            <th>Annual Savings (â‚¹)</th>
                            <th>Investment Contribution (â‚¹)</th>
                            <th>Cash Savings (â‚¹)</th>
                            <th>Investment Returns (â‚¹)</th>
                            <th>Ending Invested (â‚¹)</th>
                            <th>Ending Cash (â‚¹)</th>
                            <th>Ending Nominal (â‚¹)</th>
                            <th>Inflation Adjusted (â‚¹)</th>
                            <th>Cumulative Contributions (â‚¹)</th>
                            <th>Cumulative Returns (â‚¹)</th>
                        </tr>
                    </thead>
                    <tbody>
    `;

    df.forEach(row => {
        tableHTML += `
            <tr>
                <td>${row.age}</td>
                <td>${formatINR(row.starting_invested_wealth)}</td>
                <td>${formatINR(row.starting_cash_wealth)}</td>
                <td>${formatINR(row.annual_income)}</td>
                <td>${formatINR(row.annual_expenses)}</td>
                <td>${formatINR(row.annual_savings)}</td>
                <td>${formatINR(row.annual_investment_contribution)}</td>
                <td>${formatINR(row.uninvested_cash_savings)}</td>
                <td>${formatINR(row.investment_returns)}</td>
                <td>${formatINR(row.ending_invested_wealth)}</td>
                <td>${formatINR(row.ending_cash_wealth)}</td>
                <td>${formatINR(row.ending_nominal_wealth)}</td>
                <td>${formatINR(row.inflation_adjusted_wealth)}</td>
                <td>${formatINR(row.cumulative_contributions)}</td>
                <td>${formatINR(row.cumulative_investment_returns)}</td>
            </tr>
        `;
    });

    tableHTML += `
                    </tbody>
                </table>
            </div>
        </div>
    `;

    // Key insights
    const totalYears = df.length;
    const totalContributions = finalYear.cumulative_contributions;
    const totalReturns = finalYear.cumulative_investment_returns;
    const finalNominal = finalYear.ending_nominal_wealth;
    const finalReal = finalYear.inflation_adjusted_wealth;

    const wealthGrowth = inputs.current_savings > 0 ? ((finalNominal - inputs.current_savings) / inputs.current_savings * 100) : 0;
    const realGrowth = inputs.current_savings > 0 ? ((finalReal - inputs.current_savings) / inputs.current_savings * 100) : 0;
    const inflationImpact = finalNominal > 0 ? ((finalNominal - finalReal) / finalNominal * 100) : 0;

    let insightsHTML = `
        <div class="table-container">
            <div class="table-title">Key Insights</div>
            <div class="table-scroll">
                <div style="padding: 1.5rem;">
                    <div class="metrics-grid" style="gap: 1rem;">
                        <div class="metric-card" style="text-align: left;">
                            <div class="metric-label">Investment Performance</div>
                            <div style="font-size: 0.9rem; line-height: 1.4;">
                                <p><strong>Total contributions over ${totalYears} years:</strong> ${formatINR(totalContributions)}</p>
                                <p><strong>Total investment returns:</strong> ${formatINR(totalReturns)}</p>
                                <p><strong>Return on contributions:</strong> ${totalContributions > 0 ? ((totalReturns/totalContributions*100).toFixed(1) + '%') : '0%'}</p>
                            </div>
                        </div>
                        <div class="metric-card" style="text-align: left;">
                            <div class="metric-label">Wealth Growth</div>
                            <div style="font-size: 0.9rem; line-height: 1.4;">
                                <p><strong>Nominal wealth growth:</strong> ${wealthGrowth.toFixed(1)}%</p>
                                <p><strong>Real wealth growth:</strong> ${realGrowth.toFixed(1)}%</p>
                                <p><strong>Inflation impact on wealth:</strong> ${inflationImpact.toFixed(1)}%</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    wealthResults.innerHTML = metricsHTML + chartsHTML + tableHTML + insightsHTML;

    // Initialize or update charts
    updateWealthCharts(df);
}

// Update wealth simulator charts
function updateWealthCharts(df) {
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        drawChartError('wealth-chart', 'Chart.js failed to load');
        drawChartError('composition-chart', 'Chart.js failed to load');
        drawChartError('savings-chart', 'Chart.js failed to load');
        return;
    }

    const ages = df.map(row => row.age);
    const nominalWealth = df.map(row => row.ending_nominal_wealth);
    const realWealth = df.map(row => row.inflation_adjusted_wealth);
    const investedWealth = df.map(row => row.ending_invested_wealth);
    const cashWealth = df.map(row => row.ending_cash_wealth);
    const investmentContribution = df.map(row => row.annual_investment_contribution);
    const cashSavings = df.map(row => row.uninvested_cash_savings);

    // Wealth Projection Over Time chart
    const wealthCtx = document.getElementById('wealth-chart').getContext('2d');
    if (wealthChart) {
        wealthChart.destroy();
    }
    wealthChart = new Chart(wealthCtx, {
        type: 'line',
        data: {
            labels: ages,
            datasets: [
                {
                    label: 'Nominal Wealth (â‚¹)',
                    data: nominalWealth,
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 111, 253, 0.1)',
                    tension: 0.3,
                    fill: false
                },
                {
                    label: 'Real Wealth (â‚¹)',
                    data: realWealth,
                    borderColor: '#198754',
                    backgroundColor: 'rgba(25, 135, 84, 0.1)',
                    tension: 0.3,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        // Include a rupee symbol in the tick labels
                        callback: function(value) {
                            return 'â‚¹' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });

    // Wealth Composition: Invested vs Cash chart
    const compositionCtx = document.getElementById('composition-chart').getContext('2d');
    if (compositionChart) {
        compositionChart.destroy();
    }
    compositionChart = new Chart(compositionCtx, {
        type: 'line',
        data: {
            labels: ages,
            datasets: [
                {
                    label: 'Invested Wealth (â‚¹)',
                    data: investedWealth,
                    borderColor: '#ffc107',
                    backgroundColor: 'rgba(255, 193, 7, 0.1)',
                    tension: 0.3,
                    fill: false
                },
                {
                    label: 'Cash Wealth (â‚¹)',
                    data: cashWealth,
                    borderColor: '#20c997',
                    backgroundColor: 'rgba(32, 201, 151, 0.1)',
                    tension: 0.3,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return 'â‚¹' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });

    // Annual Savings Breakdown chart
    const savingsCtx = document.getElementById('savings-chart').getContext('2d');
    if (savingsChart) {
        savingsChart.destroy();
    }
    savingsChart = new Chart(savingsCtx, {
        type: 'line',
        data: {
            labels: ages,
            datasets: [
                {
                    label: 'Investment Contribution (â‚¹)',
                    data: investmentContribution,
                    borderColor: '#fd7e14',
                    backgroundColor: 'rgba(253, 126, 20, 0.1)',
                    tension: 0.3,
                    fill: false
                },
                {
                    label: 'Cash Savings (â‚¹)',
                    data: cashSavings,
                    borderColor: '#6f42c1',
                    backgroundColor: 'rgba(111, 66, 193, 0.1)',
                    tension: 0.3,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return 'â‚¹' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

// Helper function to draw error message on canvas
function drawChartError(canvasId, message) {
    const canvas = document.getElementById(canvasId);
    if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#dc3545';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(message, canvas.width / 2, canvas.height / 2);
    }
}

// Scenario Comparison Calculation
function calculateScenarioComparison() {
    // Show loading state
    const scenarioResults = document.getElementById('scenario-results');
    scenarioResults.innerHTML = '<div class="loading"><div>Running scenario comparison...</div></div>';

    try {
        // Get form values
        const baseInputs = {
            current_age: parseInt(document.getElementById('scenario-current-age').value),
            target_age: parseInt(document.getElementById('scenario-target-age').value),
            current_savings: parseFloat(document.getElementById('scenario-current-savings').value),
            monthly_income: parseFloat(document.getElementById('scenario-monthly-income').value),
            monthly_expenses: parseFloat(document.getElementById('scenario-monthly-expenses').value),
            monthly_investment_contribution: parseFloat(document.getElementById('scenario-monthly-investment').value),
            annual_income_growth_pct: parseFloat(document.getElementById('scenario-base-income-growth').value),
            annual_expense_growth_pct: parseFloat(document.getElementById('scenario-base-expense-growth').value),
            expected_annual_return_pct: parseFloat(document.getElementById('scenario-base-return').value),
            annual_inflation_pct: parseFloat(document.getElementById('scenario-base-inflation').value)
        };

        // Run scenario comparison
        const results = runScenarioComparison(baseInputs);

        // Display results
        displayScenarioResults(results);
    } catch (error) {
        scenarioResults.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    }
}

// Display Scenario Results
function displayScenarioResults(results) {
    const scenarioResults = document.getElementById('scenario-results');
    if (!results || !results.summary) {
        scenarioResults.innerHTML = '<div class="no-results">No scenario comparison data available.</div>';
        return;
    }

    const wealthComparison = results.summary.wealth_comparison;
    const assumptionComparison = results.summary.assumption_comparison;

    // Wealth comparison table
    let wealthTableHTML = `
        <div class="table-container">
            <div class="table-title">Projected Wealth Comparison</div>
            <div class="table-scroll">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Scenario</th>
                            <th>Ending Wealth (â‚¹)</th>
                        </tr>
                    </thead>
                    <tbody>
    `;

    const scenarioNames = {
        'base': 'Base',
        'conservative': 'Conservative',
        'optimistic': 'Optimistic',
        'custom': 'Custom'
    };

    for (const [scenario, wealth] of Object.entries(wealthComparison)) {
        wealthTableHTML += `
            <tr>
                <td>${scenarioNames[scenario] || scenario}</td>
                <td>${wealth !== null ? formatINR(wealth) : "N/A"}</td>
            </tr>
        `;
    }

    wealthTableHTML += `
                    </tbody>
                </table>
            </div>
        </div>
    `;

    // Assumptions comparison table
    let assumptionsTableHTML = `
        <div class="table-container">
            <div class="table-title">Scenario Assumptions Comparison</div>
            <div class="table-scroll">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Parameter</th>
                            <th>Base (%)</th>
                            <th>Conservative (%)</th>
                            <th>Optimistic (%)</th>
                            <th>Custom (%)</th>
                        </tr>
                    </thead>
                    <tbody>
    `;

    const paramNames = {
        'expected_annual_return_pct': 'Expected Annual Return',
        'annual_income_growth_pct': 'Annual Income Growth',
        'annual_expense_growth_pct': 'Annual Expense Growth',
        'annual_inflation_pct': 'Annual Inflation Rate'
    };

    for (const [param, values] of Object.entries(assumptionComparison)) {
        assumptionsTableHTML += `
            <tr>
                <td>${paramNames[param] || param}</td>
                <td>${values.base !== null ? values.base.toFixed(1) : "N/A"}</td>
                <td>${values.conservative !== null ? values.conservative.toFixed(1) : "N/A"}</td>
                <td>${values.optimistic !== null ? values.optimistic.toFixed(1) : "N/A"}</td>
                <td>${values.custom !== null ? values.custom.toFixed(1) : "N/A"}</td>
            </tr>
        `;
    }

    assumptionsTableHTML += `
                    </tbody>
                </table>
            </div>
        </div>
    `;

    // Chart for wealth over time by scenario
    let chartHTML = `
        <div class="chart-wrapper">
            <h3 class="chart-title">Wealth Over Time by Scenario</h3>
            <div class="chart-container">
                <canvas id="scenario-chart"></canvas>
            </div>
        </div>
    `;

    scenarioResults.innerHTML = wealthTableHTML + assumptionsTableHTML + chartHTML;

    // Initialize or update scenario chart
    updateScenarioChart(results);
}

// Update scenario comparison chart
function updateScenarioChart(results) {
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        drawChartError('scenario-chart', 'Chart.js failed to load');
        return;
    }

    const scenarioTypes = ['base', 'conservative', 'optimistic', 'custom'];
    const scenarioNames = {
        'base': 'Base',
        'conservative': 'Conservative',
        'optimistic': 'Optimistic',
        'custom': 'Custom'
    };

    // Collect data for each scenario
    const chartData = {
        labels: [],
        datasets: []
    };

    // We assume all scenarios have the same age range (they should, as inputs are same except for parameters)
    // We'll take the age labels from the base scenario (or first available)
    let ages = [];
    for (const scenarioType of scenarioTypes) {
        if (results.scenarios[scenarioType] && results.scenarios[scenarioType].projection && results.scenarios[scenarioType].projection.length > 0) {
            ages = results.scenarios[scenarioType].projection.map(row => row.age);
            break;
        }
    }

    chartData.labels = ages;

    // Define colors for each scenario
    const colors = {
        'base': '#0d6efd',
        'conservative': '#fd7e14',
        'optimistic': '#198754',
        'custom': '#6f42c1'
    };

    for (const scenarioType of scenarioTypes) {
        if (results.scenarios[scenarioType] && results.scenarios[scenarioType].projection && results.scenarios[scenarioType].projection.length > 0) {
            const wealthData = results.scenarios[scenarioType].projection.map(row => row.ending_nominal_wealth);
            chartData.datasets.push({
                label: scenarioNames[scenarioType],
                data: wealthData,
                borderColor: colors[scenarioType],
                backgroundColor: hexToRgba(colors[scenarioType], 0.1),
                tension: 0.3,
                fill: false
            });
        }
    }

    const scenarioCtx = document.getElementById('scenario-chart').getContext('2d');
    if (scenarioChart) {
        scenarioChart.destroy();
    }
    scenarioChart = new Chart(scenarioCtx, {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return 'â‚¹' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

// Helper function to convert hex color to rgba
function hexToRgba(hex, alpha) {
    // Remove the '#' if present
    const cleanHex = hex.replace('#', '');
    // Parse the hex values
    const bigint = parseInt(cleanHex, 16);
    const r = (bigint >> 16) & 255;
    const g = (bigint >> 8) & 255;
    const b = bigint & 255;
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

// Goal Planner Calculation
function calculateGoalPlannerResult() {
    // Show loading state
    const goalResults = document.getElementById('goal-results');
    goalResults.innerHTML = '<div class="loading"><div>Calculating goal requirements...</div></div>';

    try {
        // Get form values
        const currentAge = parseInt(document.getElementById('goal-current-age').value);
        const goalAge = parseInt(document.getElementById('goal-age').value);
        const targetCorpus = parseFloat(document.getElementById('goal-target').value);
        const currentSavings = parseFloat(document.getElementById('goal-current-savings').value);
        const expectedAnnualReturnPct = parseFloat(document.getElementById('goal-return').value);

        // Validate that goal age is greater than current age
        if (goalAge <= currentAge) {
            throw new Error("Goal/retirement age must be greater than current age");
        }

        // Calculate goal requirements
        const result = calculateGoalPlanner(currentAge, goalAge, targetCorpus, currentSavings, expectedAnnualReturnPct);

        // Display results
        displayGoalResults(result);
    } catch (error) {
        goalResults.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    }
}

// Display Goal Results
function displayGoalResults(result) {
    const goalResults = document.getElementById('goal-results');
    if (!result) {
        goalResults.innerHTML = '<div class="no-results">No goal calculation data available.</div>';
        return;
    }

    // Prominent results
    let prominentHTML = `
        <div class="metrics-grid" style="margin-bottom: 2rem;">
            <div class="metric-card">
                <div class="metric-label">Required Monthly Investment</div>
                <div class="metric-value">${formatINR(result.required_monthly_investment)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Required Annual Investment</div>
                <div class="metric-value">${formatINR(result.required_annual_investment)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Target Corpus</div>
                <div class="metric-value">${formatINR(result.target_corpus)}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Projected Corpus</div>
                <div class="metric-value ${result.goal_reached ? 'positive' : 'negative'}">
                    ${formatINR(result.projected_corpus)}
                </div>
            </div>
        </div>
    `;

    // Status indicator
    let statusHTML = `
        <div style="text-align: center; margin-bottom: 2rem;">
            ${result.goal_reached ?
                '<div style="background-color: #D4EDDA; color: #155724; padding: 1rem; border-radius: 6px; border: 1px solid #C3E6CB;">âœ… Goal Reached</div>' :
                '<div style="background-color: #F8D7DA; color: #721C24; padding: 1rem; border-radius: 6px; border: 1px solid #F5C2C7;">âš ï¸ Goal Not Reached</div>'
            }
        </div>
    `;

    // Goal details
    let detailsHTML = `
        <div class="table-container">
            <div class="table-title">Goal Details</div>
            <div class="table-scroll">
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Years Available</div>
                        <div class="metric-value">${result.years_available} years</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Total Future Contributions</div>
                        <div class="metric-value">${formatINR(result.total_future_contributions)}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Estimated Investment Returns</div>
                        <div class="metric-value">${formatINR(result.estimated_investment_returns)}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Surplus/Shortfall</div>
                        <div class="metric-value ${result.surplus_or_shortfall >= 0 ? 'positive' : 'negative'}">
                            ${formatINR(Math.abs(result.surplus_or_shortfall))} ${result.surplus_or_shortfall >= 0 ? '(Surplus)' : '(Shortfall)'}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // Year-by-year projection table
    let tableHTML = `
        <div class="table-container">
            <div class="table-title">Year-by-Year Projection</div>
            <div class="table-scroll">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Age</th>
                            <th>Year</th>
                            <th>Starting Corpus (â‚¹)</th>
                            <th>Annual Contributions (â‚¹)</th>
                            <th>Investment Returns (â‚¹)</th>
                            <th>Ending Corpus (â‚¹)</th>
                            <th>Target Corpus (â‚¹)</th>
                        </tr>
                    </thead>
                    <tbody>
    `;

    result.year_by_year_projection.forEach(row => {
        tableHTML += `
            <tr>
                <td>${row.Age}</td>
                <td>${row.Year}</td>
                <td>${formatINR(row['Starting Corpus'])}</td>
                <td>${formatINR(row['Annual Contributions'])}</td>
                <td>${formatINR(row['Investment Returns'])}</td>
                <td>${formatINR(row['Ending Corpus'])}</td>
                <td>${formatINR(row['Target Corpus'])}</td>
            </tr>
        `;
    });

    tableHTML += `
                    </tbody>
                </table>
            </div>
        </div>
    `;

    // Chart for corpus growth projection
    let chartHTML = `
        <div class="chart-wrapper">
            <h3 class="chart-title">Corpus Growth Projection</h3>
            <div class="chart-container">
                <canvas id="goal-chart"></canvas>
            </div>
        </div>
    `;

    goalResults.innerHTML = prominentHTML + statusHTML + detailsHTML + tableHTML + chartHTML;

    // Initialize or update goal chart
    updateGoalChart(result);
}

// Update goal planner chart
function updateGoalChart(result) {
    // Check if Chart.js is loaded
    if (typeof Chart === 'undefined') {
        drawChartError('goal-chart', 'Chart.js failed to load');
        return;
    }

    const projection = result.year_by_year_projection;
    const ages = projection.map(row => row.Age);
    const endingCorpus = projection.map(row => row['Ending Corpus']);
    const targetCorpus = projection.map(row => row['Target Corpus']); // This is constant but we'll map it

    const goalCtx = document.getElementById('goal-chart').getContext('2d');
    if (goalChart) {
        goalChart.destroy();
    }
    goalChart = new Chart(goalCtx, {
        type: 'line',
        data: {
            labels: ages,
            datasets: [
                {
                    label: 'Projected Corpus (â‚¹)',
                    data: endingCorpus,
                    borderColor: '#0d6efd',
                    backgroundColor: 'rgba(13, 111, 253, 0.1)',
                    tension: 0.3,
                    fill: false
                },
                {
                    label: 'Target Corpus (â‚¹)',
                    data: targetCorpus,
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    tension: 0.3,
                    fill: false,
                    borderDash: [5, 5]
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return 'â‚¹' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    );
}

// Initialize chart placeholders (kept for compatibility, does nothing)
function initializeChartPlaceholders() {
    // This function is kept to avoid breaking existing calls, but does nothing now.
    // Charts are now created directly in the display functions.
}

// Export for potential use in other environments
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        calculateProjection,
        runScenarioComparison,
        calculateGoalPlanner,
        formatINR
    };
}
