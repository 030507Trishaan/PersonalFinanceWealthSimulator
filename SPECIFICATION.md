# Personal Finance & Wealth Simulator - V1 Specification

## Project Overview
Build a simple, professional financial planning simulator that models how a person's wealth changes over time based on income, expenses, savings/investment contributions, investment returns, and inflation.

## V1 Scope Only
Build a basic working wealth projection model with:
- User inputs for financial assumptions
- Year-by-year wealth projection calculations
- Clear distinction between nominal and inflation-adjusted wealth
- Summary numbers, wealth-over-time chart, and annual projection table

## Proposed Project Structure
```
PersonalFinanceWealthSimulator/
├── financial_engine/
│   └── core/                 # Financial calculation engine (separate from UI)
├── tests/
│   ├── unit/                 # Unit tests for financial engine
│   └── integration/          # Integration tests
├── ui/                       # Streamlit web interface
├── SPECIFICATION.md          # This file
├── README.md                 # Project overview and instructions
└── requirements.txt          # Python dependencies
```

## V1 Financial Methodology

### Core Principles
1. **Separation of Concerns**: Financial calculation engine is completely separate from UI
2. **Year-by-Year Projection**: Calculate values for each year from current age to target age (exclusive of target_age)
3. **Clear Distinction**: Maintain both nominal (not inflation-adjusted) and real (inflation-adjusted) wealth values
4. **Conservative Assumptions**: Use simple, understandable formulas appropriate for finance students

### Input Parameters
- `current_age`: User's current age (years)
- `target_age`: Target age for projection (years) - simulation runs for ages [current_age, target_age-1]
- `current_savings`: Starting wealth amount (currency)
- `monthly_income`: Monthly income (currency/month)
- `monthly_expenses`: Monthly expenses (currency/month)
- `monthly_investment_contribution`: Monthly amount dedicated to investments (currency/month)
- `annual_income_growth_pct`: Annual percentage increase in income (%/year)
- `annual_expense_growth_pct`: Annual percentage increase in expenses (%/year)
- `expected_annual_return_pct`: Expected annual investment return (%/year)
- `annual_inflation_pct`: Annual inflation rate (%/year)

### Annual Calculations (for each year from current_age to target_age-1)

Let:
- `years_elapsed = current_year - current_age`
- `income_growth_factor = (1 + annual_income_growth_pct/100)^years_elapsed`
- `expense_growth_factor = (1 + annual_expense_growth_pct/100)^years_elapsed`

Then for each year:
1. **Annual Income** = `monthly_income * 12 * income_growth_factor`
2. **Annual Expenses** = `monthly_expenses * 12 * expense_growth_factor`
3. **Annual Savings** = `Annual Income - Annual Expenses` (net annual cash flow)
4. **Annual Investment Contribution** = `monthly_investment_contribution * 12` (fixed nominal amount)
5. **Uninvested Cash Savings** = `Annual Savings - Annual Investment Contribution` (≥ 0 due to validation)
6. **Investment Return** = `(Starting Invested Wealth + Annual Investment Contribution) * (expected_annual_return_pct/100)`
7. **Ending Invested Wealth** = `Starting Invested Wealth + Annual Investment Contribution + Investment Return`
8. **Ending Cash Wealth** = `Starting Cash Wealth + Uninvested Cash Savings`
9. **Ending Total Nominal Wealth** = `Ending Invested Wealth + Ending Cash Wealth`
10. **Inflation Adjustment Factor** = `(1 + annual_inflation_pct/100)^years_elapsed`
11. **Inflation-Adjusted/Real Wealth** = `Ending Total Nominal Wealth / Inflation Adjustment Factor`
12. **Cumulative Contributions** = Sum of all Annual Investment Contributions from start to current year
13. **Cumulative Investment Returns** = Sum of all Investment Returns from start to current year

### Key Assumptions
1. **Timing**: All calculations assume end-of-year values
2. **Investment Timing**: Annual investment contribution is made at the beginning of each year
3. **Income/Expense Growth**: Compounds annually from the base values
4. **Inflation Adjustment**: Converts nominal future values to today's purchasing power
5. **Cash Savings**: Any savings not invested (Annual Savings - Annual Investment Contribution) are held as zero-interest cash
6. **Validation**: Monthly investment contribution must be ≤ (monthly income - monthly expenses) to prevent negative savings
7. **Initial Condition**: All `current_savings` are treated as invested wealth at the beginning of the simulation. Starting cash wealth is therefore zero.

### Model Outputs (for each year from current_age to target_age-1)
- Age (for reference, representing the age at the END of the year)
- Starting invested wealth (beginning of year)
- Starting cash wealth (beginning of year)
- Annual income
- Annual expenses
- Annual savings
- Annual investment contribution
- Uninvested cash savings
- Investment returns
- Ending invested wealth (end of year)
- Ending cash wealth (end of year)
- Ending total nominal wealth (end of year)
- Inflation-adjusted/real wealth
- Cumulative contributions
- Cumulative investment returns

### Boundary Conditions
- At `current_age` (start of simulation, before any annual calculations):
  - Starting invested wealth = `current_savings`
  - Starting cash wealth = 0
- At the end of each year (which becomes the start of the next year):
  - Starting invested wealth (next year) = Ending invested wealth (current year)
  - Starting cash wealth (next year) = Ending cash wealth (current year)
- Projection runs for years where age progresses from `current_age` to `target_age - 1`
- This produces exactly (`target_age` - `current_age`) years of accumulation
- Example: current_age=20, target_age=50 produces 30 years of accumulation (ages 20→21, 21→22, ..., 49→50)

## Explicitly OUT of Scope (Future Phases)
- Scenarios comparison
- Goal planning (e.g., "How much do I need to save to reach $X?")
- Monte Carlo simulations
- Portfolio optimization
- Stock/market APIs or real investment data
- Tax modeling
- Authentication, database, or user accounts
- AI features or financial product recommendations

## Dependencies
- Python 3.8+
- Streamlit (for UI)
- Pandas/Numpy (for data handling, if genuinely useful)
- Plotly (for charts)
- Pytest (for testing)

## Test Plan
Unit tests will cover:
1. Input validation (negative values, invalid ranges)
2. Boundary conditions (current_age = target_age-1 for single year)
3. Zero growth scenarios (0% income/expense/inflation/return)
4. Known calculation cases (manual verification)
5. Edge cases (extreme values, division by zero prevention)
6. Consistency checks (nominal vs real wealth relationship, invested+cash = total wealth)

Integration tests will verify:
1. Full pipeline from inputs to outputs
2. UI interaction with financial engine
3. Chart data generation from projection results

## Formulas Summary
- Annual Income Growth: Compounded annually from base monthly income
- Annual Expense Growth: Compounded annually from base monthly expenses
- Investment Returns: Simple annual return on (starting invested wealth + annual contribution)
- Invested Wealth Accumulation: Previous invested + contribution + investment returns
- Cash Wealth Accumulation: Previous cash + uninvested cash savings
- Total Nominal Wealth: Invested wealth + Cash wealth
- Inflation Adjustment: Division by cumulative inflation factor: `(1 + inflation_rate)^years_elapsed`
- Cumulative Sums: Running totals of contributions and returns

## Validation Rules
1. All age inputs must be positive integers, target_age > current_age
2. All monetary inputs must be non-negative
3. All percentage inputs must be non-negative
4. Monthly investment contribution ≤ (monthly income - monthly expenses)
5. Reasonable upper bounds on growth rates to prevent overflow