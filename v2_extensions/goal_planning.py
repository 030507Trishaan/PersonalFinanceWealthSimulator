"""
Goal planning module for V2 extensions of Personal Finance & Wealth Simulator
Calculates required savings to reach specific financial goals.
"""

def calculate_goal_requirements(base_inputs, goal_name, target_amount, target_age):
    """
    Calculate the monthly investment needed to reach a financial goal.

    Parameters:
    -----------
    base_inputs : dict
        V1 validated inputs (current_age, target_age, etc. from base scenario)
    goal_name : str
        Descriptive name for the goal (non-empty)
    target_amount : float
        Desired future wealth amount (nominal currency, non-negative)
    target_age : int
        Age by which to achieve the goal (must be > current_age)

    Returns:
    --------
    dict
        {
            'goal_name': str,
            'target_amount': float,
            'target_age': int,
            'current_age': int,
            'required_monthly_investment': float,  # Monthly contribution needed
            'projected_wealth_at_target': float,   # Wealth with current assumptions
            'surplus_or_shortfall': float,         # projected - target (positive = surplus)
            'goal_reached': bool,                  # True if surplus_or_shortfall >= 0
            'calculation_method': str,             # 'direct', 'binary_search', or 'boundary'
            'iterations': int                      # Number of iterations if applicable
            'verification_passed': bool            # Whether solution verified within tolerance
        }

    Raises:
    -------
    ValueError
        If inputs are invalid or goal is mathematically impossible
    """
    # Import shared utilities and V1 functions
    from .shared_utils import validate_goal_inputs, binary_search_contribution
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'financial_engine', 'core'))
    from calculations import validate_inputs, calculate_projection

    # Validate goal inputs
    goal_inputs = base_inputs.copy()
    goal_inputs.update({
        'goal_name': goal_name,
        'target_amount': target_amount,
        'target_age': target_age
    })

    validated_goal_inputs = validate_goal_inputs(goal_inputs)

    # Extract validated parameters
    current_age = validated_goal_inputs['current_age']
    validated_target_amount = validated_goal_inputs['target_amount']
    validated_target_age = validated_goal_inputs['target_age']

    # Calculate projected wealth with current assumptions (no goal planning)
    baseline_projection = calculate_projection(validated_goal_inputs)
    projected_wealth_at_target = baseline_projection[-1]['ending_nominal_wealth'] if baseline_projection else validated_goal_inputs['current_savings']

    # Calculate surplus/shortfall with current assumptions
    # surplus_or_shortfall = projected_wealth - target_amount (positive = surplus, negative = shortfall)
    surplus_or_shortfall = projected_wealth_at_target - validated_target_amount
    goal_reached = surplus_or_shortfall >= -0.01  # Allow small tolerance for floating point

    # If goal already reached or target age equals current age, no planning needed
    if validated_target_age <= current_age:
        # This should have been caught by validation, but handle gracefully
        return {
            'goal_name': goal_name,
            'target_amount': validated_target_amount,
            'target_age': validated_target_age,
            'current_age': current_age,
            'required_monthly_investment': 0.0,
            'projected_wealth_at_target': projected_wealth_at_target,
            'surplus_or_shortfall': surplus_or_shortfall,
            'goal_reached': goal_reached,
            'calculation_method': 'direct',
            'iterations': 0,
            'verification_passed': True
        }

    # Use binary search to find required contribution
    result = binary_search_contribution(
        base_inputs=validated_goal_inputs,
        target_amount=validated_target_amount,
        target_age=validated_target_age
    )

    # Format the result to match expected return format
    return {
        'goal_name': goal_name,
        'target_amount': validated_target_amount,
        'target_age': validated_target_age,
        'current_age': current_age,
        'required_monthly_investment': result['required_monthly_investment'],
        'projected_wealth_at_target': result['projected_wealth_at_target'],
        'surplus_or_shortfall': result['surplus_or_shortfall'],  # Already correctly defined as projected - target
        'goal_reached': result['surplus_or_shortfall'] >= -0.01,  # Recalculate based on our definition
        'calculation_method': result['calculation_method'],
        'iterations': result['iterations'],
        'verification_passed': result['verification_passed']
    }


def validate_goal_inputs(goal_inputs):
    """
    Validate goal planning inputs.

    Parameters:
    -----------
    goal_inputs : dict
        Dictionary containing goal parameters

    Returns:
    --------
    dict
        Validated goal inputs

    Raises:
    -------
    ValueError
        For invalid goal inputs
    """
    # Import and use the shared validation function
    from .shared_utils import validate_goal_inputs as shared_validate_goal_inputs
    return shared_validate_goal_inputs(goal_inputs)