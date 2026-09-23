"""
Financial Calculation Engine for Personal Finance & Wealth Simulator
Implements the core wealth projection logic as specified in SPECIFICATION.md
"""

from typing import Dict, List, Any


def validate_inputs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates all user inputs and returns validated inputs or raises appropriate exceptions.

    Parameters:
    -----------
    inputs : dict
        Dictionary containing all user input parameters

    Returns:
    --------
    dict
        Validated and normalized inputs

    Raises:
    -------
    ValueError
        For invalid input values
    TypeError
        For incorrect input types
    """
    validated = {}

    # Validate age inputs
    if not isinstance(inputs.get('current_age'), int):
        raise TypeError("current_age must be an integer")
    if not isinstance(inputs.get('target_age'), int):
        raise TypeError("target_age must be an integer")

    current_age = inputs['current_age']
    target_age = inputs['target_age']

    if current_age <= 0:
        raise ValueError("current_age must be a positive integer")
    if target_age <= 0:
        raise ValueError("target_age must be a positive integer")
    if target_age <= current_age:
        raise ValueError("target_age must be greater than current_age")

    validated['current_age'] = current_age
    validated['target_age'] = target_age

    # Validate monetary inputs (must be non-negative)
    monetary_fields = ['current_savings', 'monthly_income', 'monthly_expenses',
                      'monthly_investment_contribution']

    for field in monetary_fields:
        value = inputs.get(field, 0)
        if not isinstance(value, (int, float)):
            raise TypeError(f"{field} must be a number")
        if value < 0:
            raise ValueError(f"{field} must be non-negative")
        validated[field] = float(value)

    # Validate percentage inputs (must be non-negative)
    percentage_fields = ['annual_income_growth_pct', 'annual_expense_growth_pct',
                        'expected_annual_return_pct', 'annual_inflation_pct']

    for field in percentage_fields:
        value = inputs.get(field, 0.0)
        if not isinstance(value, (int, float)):
            raise TypeError(f"{field} must be a number")
        if value < 0:
            raise ValueError(f"{field} must be non-negative")
        validated[field] = float(value)

    # Validate investment contribution affordability
    monthly_income = validated['monthly_income']
    monthly_expenses = validated['monthly_expenses']
    monthly_investment = validated['monthly_investment_contribution']

    max_monthly_investment = monthly_income - monthly_expenses
    if monthly_investment > max_monthly_investment:
        raise ValueError(
            f"monthly_investment_contribution ({monthly_investment}) cannot exceed "
            f"available savings (monthly_income - monthly_expenses = {max_monthly_investment})"
        )

    return validated


def calculate_projection(inputs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Calculates year-by-year wealth projection based on validated inputs.

    Parameters:
    -----------
    inputs : dict
        Validated user inputs from validate_inputs()

    Returns:
    --------
    list of dicts
        Each dict represents one year's projection with keys:
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
    """
    # Extract validated inputs
    current_age = inputs['current_age']
    target_age = inputs['target_age']
    current_savings = inputs['current_savings']
    monthly_income = inputs['monthly_income']
    monthly_expenses = inputs['monthly_expenses']
    monthly_investment_contribution = inputs['monthly_investment_contribution']
    annual_income_growth_pct = inputs['annual_income_growth_pct']
    annual_expense_growth_pct = inputs['annual_expense_growth_pct']
    expected_annual_return_pct = inputs['expected_annual_return_pct']
    annual_inflation_pct = inputs['annual_inflation_pct']

    # Convert percentages to decimals
    income_growth_rate = annual_income_growth_pct / 100.0
    expense_growth_rate = annual_expense_growth_pct / 100.0
    return_rate = expected_annual_return_pct / 100.0
    inflation_rate = annual_inflation_pct / 100.0

    # Initialize results list
    projection_results = []

    # Initialize wealth tracking
    # All current_savings are treated as invested wealth at the beginning
    starting_invested_wealth = current_savings
    starting_cash_wealth = 0.0

    # Initialize cumulative trackers
    cumulative_contributions = 0.0
    cumulative_investment_returns = 0.0

    # Calculate projection for each year from current_age to target_age-1
    # This produces exactly (target_age - current_age) years of accumulation
    for year_offset in range(target_age - current_age):
        # Calculate the current year's age (at the END of the year)
        current_year_age = current_age + year_offset + 1

        # Calculate growth factors for this year
        # years_elapsed = number of full years completed so far
        years_elapsed = year_offset  # 0 for first year, 1 for second year, etc.
        income_growth_factor = (1.0 + income_growth_rate) ** years_elapsed
        expense_growth_factor = (1.0 + expense_growth_rate) ** years_elapsed
        inflation_factor = (1.0 + inflation_rate) ** years_elapsed

        # Calculate annual values
        annual_income = monthly_income * 12.0 * income_growth_factor
        annual_expenses = monthly_expenses * 12.0 * expense_growth_factor
        annual_savings = annual_income - annual_expenses
        annual_investment_contribution = monthly_investment_contribution * 12.0  # Fixed nominal amount

        # Calculate uninvested cash savings (ensured non-negative by validation)
        uninvested_cash_savings = annual_savings - annual_investment_contribution

        # Calculate investment return (beginning of year timing)
        # Return is calculated on starting invested wealth + this year's contribution
        investment_return = (starting_invested_wealth + annual_investment_contribution) * return_rate

        # Calculate ending wealth values
        ending_invested_wealth = starting_invested_wealth + annual_investment_contribution + investment_return
        ending_cash_wealth = starting_cash_wealth + uninvested_cash_savings
        ending_nominal_wealth = ending_invested_wealth + ending_cash_wealth

        # Calculate inflation-adjusted/real wealth
        if inflation_factor > 0:
            inflation_adjusted_wealth = ending_nominal_wealth / inflation_factor
        else:
            # Handle edge case where inflation_factor is 0 (should not happen with validation)
            inflation_adjusted_wealth = ending_nominal_wealth

        # Update cumulative trackers
        cumulative_contributions += annual_investment_contribution
        cumulative_investment_returns += investment_return

        # Create result record for this year
        year_result = {
            'age': current_year_age,
            'starting_invested_wealth': starting_invested_wealth,
            'starting_cash_wealth': starting_cash_wealth,
            'annual_income': annual_income,
            'annual_expenses': annual_expenses,
            'annual_savings': annual_savings,
            'annual_investment_contribution': annual_investment_contribution,
            'uninvested_cash_savings': uninvested_cash_savings,
            'investment_returns': investment_return,
            'ending_invested_wealth': ending_invested_wealth,
            'ending_cash_wealth': ending_cash_wealth,
            'ending_nominal_wealth': ending_nominal_wealth,
            'inflation_adjusted_wealth': inflation_adjusted_wealth,
            'cumulative_contributions': cumulative_contributions,
            'cumulative_investment_returns': cumulative_investment_returns
        }

        projection_results.append(year_result)

        # Set starting values for next year (end of current year becomes start of next year)
        starting_invested_wealth = ending_invested_wealth
        starting_cash_wealth = ending_cash_wealth

    return projection_results