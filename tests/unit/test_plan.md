# Test Cases for Financial Engine

## Unit Test Categories

### 1. Input Validation Tests
- Negative age values
- Target age less than or equal to current age
- Negative monetary values
- Negative percentage values
- Monthly investment contribution exceeding available savings (income - expenses)
- Extreme values that might cause overflow
- Non-numeric inputs where numbers expected

### 2. Boundary Condition Tests
- Current age equals target age - 1 (single year projection)
- Zero values for all growth rates and returns
- Zero inflation rate
- Zero investment returns
- Zero income and expenses
- Very small decimal values
- Very large numbers (within reason)

### 3. Calculation Accuracy Tests
- Known manual calculations for simple scenarios
- Zero growth scenario verification
- Constant growth scenario verification
- Relationship between nominal and real wealth
- Cumulative sums verification
- Invested wealth + cash wealth = total nominal wealth

### 4. Consistency Tests
- Starting invested wealth correctly set to current_savings (all treated as invested)
- Starting cash wealth correctly set to zero
- Each year's starting invested wealth equals previous year's ending invested wealth
- Each year's starting cash wealth equals previous year's ending cash wealth
- Inflation-adjusted wealth <= nominal wealth when inflation > 0
- Cumulative contributions = sum of annual investment contributions
- Cumulative investment returns = sum of annual investment returns
- Annual savings = annual investment contribution + uninvested cash savings
- Investment returns = (starting invested wealth + annual investment contribution) * return rate

## Example Test Case: Zero Growth Scenario
Inputs:
- current_age: 30
- target_age: 35
- current_savings: 10000
- monthly_income: 5000
- monthly_expenses: 3000
- monthly_investment_contribution: 1000
- annual_income_growth_pct: 0
- annual_expense_growth_pct: 0
- expected_annual_return_pct: 0
- annual_inflation_pct: 0

Expected Results (year by year, showing age at END of year):
- Age: 31, 32, 33, 34, 35
- Annual Income: 60000 (5000 * 12) each year
- Annual Expenses: 36000 (3000 * 12) each year
- Annual Savings: 24000 each year
- Annual Investment Contribution: 12000 (1000 * 12) each year
- Uninvested Cash Savings: 12000 each year
- Investment Returns: 0 each year
- Ending Invested Wealth: Starts at 10000, increases by 12000 each year
- Ending Cash Wealth: Starts at 0, increases by 12000 each year
- Ending Nominal Wealth: Equal to Ending Invested Wealth + Ending Cash Wealth
- Inflation Adjusted Wealth: Equal to Nominal Wealth (0% inflation)
- Cumulative Contributions: Year * 12000
- Cumulative Investment Returns: 0

## Integration Test Scenarios
1. Full projection from inputs to outputs
2. Edge case handling in complete pipeline
3. Data formatting for UI consumption
4. Chart data generation accuracy