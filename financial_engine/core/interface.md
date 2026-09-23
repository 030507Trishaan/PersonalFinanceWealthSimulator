# Financial Calculation Engine Interface

This module defines the interface for the financial calculation engine.
The engine should be completely independent of the UI layer.

## Core Functions

### validate_inputs(inputs)
Validates all user inputs and returns validated inputs or raises appropriate exceptions.

**Parameters:**
- inputs (dict): Dictionary containing all user input parameters

**Returns:**
- dict: Validated and normalized inputs

**Raises:**
- ValueError: For invalid input values
- TypeError: For incorrect input types

### calculate_projection(inputs)
Calculates year-by-year wealth projection based on validated inputs.

**Parameters:**
- inputs (dict): Validated user inputs

**Returns:**
- list of dicts: Each dict represents one year's projection with keys:
  - age
  - starting_invested_wealth
  - starting_cash_wealth
  - annual_income
  - annual_expenses
  - annual_savings
  - annual_investment_contribution
  - uninvested_cash_savings
  - investment_returns
  - ending_invested_wealth
  - ending_cash_wealth
  - ending_nominal_wealth
  - inflation_adjusted_wealth
  - cumulative_contributions
  - cumulative_investment_returns

## Input Parameters Dictionary Structure
{
    'current_age': int,
    'target_age': int,
    'current_savings': float,
    'monthly_income': float,
    'monthly_expenses': float,
    'monthly_investment_contribution': float,
    'annual_income_growth_pct': float,
    'annual_expense_growth_pct': float,
    'expected_annual_return_pct': float,
    'annual_inflation_pct': float
}

## Assumptions
1. Calculations are performed at year-end
2. Investment contributions are made at the beginning of each year
3. Income and expenses grow compounded annually
4. Investment returns are simple annual percentage on (starting invested wealth + annual contribution)
5. Nominal wealth = invested wealth + cash wealth
6. Inflation-adjusted wealth = nominal wealth / (1 + inflation rate)^years_elapsed
7. All monetary values use the same currency unit
8. Percentages are expressed as values (e.g., 5% = 5.0)
9. All current_savings are treated as invested wealth at t=0 (start of simulation)
10. Starting cash wealth is zero
11. Uninvested cash savings = max(0, annual savings - annual investment contribution) [ensured by validation]
12. Simulation runs for years where age progresses from current_age to target_age-1
    (produces target_age - current_age years of accumulation)