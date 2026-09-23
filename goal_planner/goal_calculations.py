"""
Standalone Goal Planner Calculations
Implements the future-value model for goal planning as specified in the requirements.
"""

from typing import Dict, List, Tuple


def validate_goal_planner_inputs(
    current_age: int,
    goal_age: int,
    target_corpus: float,
    current_savings: float,
    expected_annual_return_pct: float
) -> Dict[str, float]:
    """
    Validate inputs for the goal planner.

    Parameters:
    -----------
    current_age : int
        Current age (must be >= 0)
    goal_age : int
        Goal/retirement age (must be > current_age)
    target_corpus : float
        Target corpus amount (must be >= 0)
    current_savings : float
        Current savings/investments (must be >= 0)
    expected_annual_return_pct : float
        Expected annual investment return percentage (must be >= 0)

    Returns:
    --------
    dict
        Validated inputs

    Raises:
    -------
    ValueError
        If any input is invalid
    """
    # Validate current_age
    if not isinstance(current_age, int):
        raise TypeError("current_age must be an integer")
    if current_age < 0:
        raise ValueError("current_age must be >= 0")

    # Validate goal_age
    if not isinstance(goal_age, int):
        raise TypeError("goal_age must be an integer")
    if goal_age <= current_age:
        raise ValueError("goal_age must be greater than current_age")

    # Validate target_corpus
    if not isinstance(target_corpus, (int, float)):
        raise TypeError("target_corpus must be a number")
    if target_corpus < 0:
        raise ValueError("target_corpus must be >= 0")

    # Validate current_savings
    if not isinstance(current_savings, (int, float)):
        raise TypeError("current_savings must be a number")
    if current_savings < 0:
        raise ValueError("current_savings must be >= 0")

    # Validate expected_annual_return_pct
    if not isinstance(expected_annual_return_pct, (int, float)):
        raise TypeError("expected_annual_return_pct must be a number")
    if expected_annual_return_pct < 0:
        raise ValueError("expected_annual_return_pct must be >= 0")

    return {
        'current_age': float(current_age),
        'goal_age': float(goal_age),
        'target_corpus': float(target_corpus),
        'current_savings': float(current_savings),
        'expected_annual_return_pct': float(expected_annual_return_pct)
    }


def calculate_goal_planner(
    current_age: int,
    goal_age: int,
    target_corpus: float,
    current_savings: float,
    expected_annual_return_pct: float
) -> Dict[str, any]:
    """
    Calculate the required monthly investment to reach a financial goal.

    Uses the future-value model:
    FV = P * (1 + r/12)^(12n) + PMT * [((1 + r/12)^(12n) - 1) / (r/12)]

    Where:
    - P = current corpus (current_savings)
    - r = annual return rate (as decimal)
    - n = number of years
    - PMT = monthly payment (what we're solving for)
    - FV = target corpus

    Parameters:
    -----------
    current_age : int
        Current age (must be >= 0)
    goal_age : int
        Goal/retirement age (must be > current_age)
    target_corpus : float
        Target corpus amount (must be >= 0)
    current_savings : float
        Current savings/investments (must be >= 0)
    expected_annual_return_pct : float
        Expected annual investment return percentage (must be >= 0)

    Returns:
    --------
    dict
        Contains all calculation results including:
        - required_monthly_investment
        - required_annual_investment
        - years_available
        - total_future_contributions
        - estimated_investment_returns
        - projected_corpus
        - surplus_or_shortfall
        - goal_reached
        - year_by_year_projection (list of dicts)
    """
    # Validate inputs
    validated = validate_goal_planner_inputs(
        current_age, goal_age, target_corpus, current_savings, expected_annual_return_pct
    )

    # Extract validated values
    P = validated['current_savings']  # Current corpus
    r_annual = validated['expected_annual_return_pct'] / 100.0  # Annual return as decimal
    n_years = validated['goal_age'] - validated['current_age']  # Years available
    T = validated['target_corpus']  # Target corpus

    # Calculate years available
    years_available = n_years

    # Handle zero return case separately
    if r_annual == 0:
        # PPT = max(0, (T - P) / (12 * n))
        if years_available > 0:
            required_monthly = max(0, (T - P) / (12 * years_available))
        else:
            required_monthly = 0
    else:
        # Monthly return rate
        r_monthly = r_annual / 12.0
        # Number of monthly periods
        n_months = years_available * 12

        # Future value of current corpus
        fv_current = P * ((1 + r_monthly) ** n_months)

        # If current corpus already grows to >= target
        if fv_current >= T:
            required_monthly = 0
        else:
            # Calculate denominator: [((1 + r/12)^(12n) - 1) / (r/12)]
            denominator = (((1 + r_monthly) ** n_months) - 1) / r_monthly

            # Solve for PMT: PMT = (T - P * (1 + r/12)^(12n)) / denominator
            required_monthly = (T - fv_current) / denominator

            # Ensure non-negative
            required_monthly = max(0, required_monthly)

    # Calculate required annual investment
    required_annal = required_monthly * 12

    # Calculate total future contributions
    total_future_contributions = required_monthly * 12 * years_available

    # Calculate projected corpus using the same formula for verification
    if r_annual == 0:
        projected_corpus = P + (required_monthly * 12 * years_available)
    else:
        r_monthly = r_annual / 12.0
        n_months = years_available * 12
        fv_current = P * ((1 + r_monthly) ** n_months)
        fv_contributions = required_monthly * (((1 + r_monthly) ** n_months) - 1) / r_monthly
        projected_corpus = fv_current + fv_contributions

    # Calculate estimated investment returns
    estimated_investment_returns = projected_corpus - P - total_future_contributions

    # Calculate surplus/shortfall versus target
    surplus_or_shortfall = projected_corpus - T
    goal_reached = surplus_or_shortfall >= -0.01  # Small tolerance for floating point

    # Generate year-by-year projection
    year_by_year = generate_year_by_year_projection_fixed(
        current_age, goal_age, P, T, r_annual * 100, required_monthly
    )

    return {
        'required_monthly_investment': required_monthly,
        'required_annual_investment': required_annal,
        'years_available': years_available,
        'total_future_contributions': total_future_contributions,
        'estimated_investment_returns': estimated_investment_returns,
        'projected_corpus': projected_corpus,
        'surplus_or_shortfall': surplus_or_shortfall,
        'goal_reached': goal_reached,
        'year_by_year_projection': year_by_year,
        'target_corpus': T
    }


def generate_year_by_year_projection(
    current_age: int,
    goal_age: int,
    current_corpus: float,
    annual_return_pct: float,
    monthly_contribution: float
) -> List[Dict[str, any]]:
    """
    Generate year-by-year projection table.

    Parameters:
    -----------
    current_age : int
        Starting age
    goal_age : int
        Target age (exclusive - we stop at this age)
    current_corpus : float
        Starting corpus amount
    annual_return_pct : float
        Annual return percentage
    monthly_contribution : float
        Monthly investment amount

    Returns:
    --------
    list of dicts
        Each dict contains:
        - Age
        - Year
        - Starting Corpus
        - Annual Contributions
        - Investment Returns
        - Ending Corpus
        - Target Corpus
    """
    # This function is deprecated - use generate_year_by_year_projection_fixed instead
    return []


def generate_year_by_year_projection_fixed(
    current_age: int,
    goal_age: int,
    current_corpus: float,
    target_corpus: float,
    annual_return_pct: float,
    monthly_contribution: float
) -> List[Dict[str, any]]:
    """
    Generate year-by-year projection table.

    Parameters:
    -----------
    current_age : int
        Starting age
    goal_age : int
        Target age (we show rows for ages current_age through goal_age-1,
        with the final row representing the values at goal_age)
    current_corpus : float
        Starting corpus amount
    target_corpus : float
        Target corpus amount to show in each row
    annual_return_pct : float
        Annual return percentage
    monthly_contribution : float
        Monthly investment amount

    Returns:
    --------
    list of dicts
        Each dict contains:
        - Age
        - Year
        - Starting Corpus
        - Annual Contributions
        - Investment Returns
        - Ending Corpus
        - Target Corpus
    """
    projection = []

    # Convert to decimals
    r_annual = annual_return_pct / 100.0
    r_monthly = r_annual / 12.0 if r_annual != 0 else 0

    # Starting values
    corpus_at_start_of_year = current_corpus

    # Loop for each year from current_age to goal_age-1
    # We need exactly (goal_age - current_age) rows
    # Each row represents one year: from age X to X+1
    for year_num in range(1, int(goal_age - current_age) + 1):
        year_start_age = current_age + (year_num - 1)
        year_end_age = current_age + year_num

        starting_corpus = corpus_at_start_of_year
        annual_contribution = monthly_contribution * 12

        if r_annual == 0:
            investment_returns = starting_corpus * r_annual  # 0
            ending_corpus = starting_corpus + annual_contribution + investment_returns
        else:
            # Value at start of year
            # Value at end of year
            start_value = corpus_at_start_of_year
            end_value = corpus_at_start_of_year * ((1 + r_monthly) ** 12) + \
                       monthly_contribution * (((1 + r_monthly) ** 12) - 1) / r_monthly

            ending_corpus = end_value
            investment_returns = ending_corpus - starting_corpus - annual_contribution

        year_record = {
            'Age': year_start_age,
            'Year': year_num,
            'Starting Corpus': starting_corpus,
            'Annual Contributions': annual_contribution,
            'Investment Returns': investment_returns,
            'Ending Corpus': ending_corpus,
            'Target Corpus': target_corpus
        }

        projection.append(year_record)

        # Update for next year
        corpus_at_start_of_year = ending_corpus

    return projection