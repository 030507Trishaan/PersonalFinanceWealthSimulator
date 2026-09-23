"""
Shared utilities for V2 extensions of Personal Finance & Wealth Simulator
Contains validation, clamping, and helper functions used by both scenario comparison and goal planning modules.
"""

def validate_and_clamp_scenario_inputs(base_inputs, modifications):
    """
    Apply modifications to base inputs, clamp to valid ranges, and validate.

    Parameters:
    -----------
    base_inputs : dict
        V1 validated inputs from user
    modifications : dict
        Modifications to apply to the four scenario parameters:
        - 'expected_annual_return_pct_delta': float
        - 'annual_income_growth_pct_delta': float
        - 'annual_expense_growth_pct_delta': float
        - 'annual_inflation_pct_delta': float

    Returns:
    --------
    tuple (dict, list):
        - Validated inputs ready for V1 financial engine
        - List of warnings generated during clamping/validation

    Raises:
    -------
    ValueError
        If modifications create inputs that fail V1 validation after clamping
    """
    # Import V1 validation function (we'll import it locally to avoid circular imports)
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'financial_engine', 'core'))
    from calculations import validate_inputs

    # Start with a copy of base inputs
    modified_inputs = base_inputs.copy()
    warnings = []

    # Define parameter mappings and their valid ranges
    param_ranges = {
        'expected_annual_return_pct': (0.0, 20.0),
        'annual_income_growth_pct': (0.0, 20.0),
        'annual_expense_growth_pct': (0.0, 20.0),
        'annual_inflation_pct': (0.0, 20.0)
    }

    # Define modification keys
    mod_keys = {
        'expected_annual_return_pct': 'expected_annual_return_pct_delta',
        'annual_income_growth_pct': 'annual_income_growth_pct_delta',
        'annual_expense_growth_pct': 'annual_expense_growth_pct_delta',
        'annual_inflation_pct': 'annual_inflation_pct_delta'
    }

    # Apply modifications and clamp
    for param_name, mod_key in mod_keys.items():
        if mod_key in modifications:
            base_value = base_inputs[param_name]
            delta = modifications[mod_key]
            # Validate user-provided delta is within allowed range
            if not (-20.0 <= delta <= 20.0):
                raise ValueError(f"{mod_key} delta {delta} must be between -20.0 and 20.0 percentage points")
            # Apply delta
            raw_value = base_value + delta

            # Clamp to valid range
            min_val, max_val = param_ranges[param_name]
            clamped_value = max(min_val, min(raw_value, max_val))

            # Check if clamping occurred
            if clamped_value != raw_value:
                warnings.append(f"{param_name}: value {raw_value} clamped to {clamped_value} (range [{min_val}, {max_val}])")

            # Update the parameter
            modified_inputs[param_name] = clamped_value

    # Validate the modified inputs using V1 validation
    try:
        validated_inputs = validate_inputs(modified_inputs)
        return validated_inputs, warnings
    except ValueError as e:
        raise ValueError(f"Scenario modifications resulted in invalid inputs: {str(e)}")


def validate_goal_inputs(goal_inputs):
    """
    Validate goal planning inputs according to V2 rules.

    Parameters:
    -----------
    goal_inputs : dict
        Dictionary containing:
        - 'goal_name': str
        - 'target_amount': float
        - 'target_age': int
        - Plus all base V1 input parameters

    Returns:
    --------
    dict
        Validated goal inputs (includes all input fields)

    Raises:
    -------
    ValueError
        For invalid goal inputs with descriptive messages
    """
    # Make a copy to avoid modifying original
    inputs = goal_inputs.copy()

    # Extract and validate goal-specific fields
    goal_name = inputs.get('goal_name', '')
    if not isinstance(goal_name, str) or not goal_name.strip():
        raise ValueError("goal_name must be a non-empty string")
    validated_goal_name = goal_name.strip()

    target_amount = inputs.get('target_amount', 0)
    if not isinstance(target_amount, (int, float)):
        raise ValueError("target_amount must be a number")
    if target_amount < 0:
        raise ValueError("target_amount must be non-negative")
    validated_target_amount = float(target_amount)

    target_age = inputs.get('target_age', 0)
    if not isinstance(target_age, int):
        raise ValueError("target_age must be an integer")
    current_age = inputs.get('current_age', 0)
    if not isinstance(current_age, int):
        raise ValueError("current_age must be an integer")
    if target_age <= current_age:
        raise ValueError(f"target_age ({target_age}) must be greater than current_age ({current_age})")
    validated_target_age = target_age

    # Create base inputs dictionary for V1 validation (exclude goal-specific fields)
    base_input_fields = {
        'current_age', 'target_age', 'current_savings', 'monthly_income', 'monthly_expenses',
        'monthly_investment_contribution', 'annual_income_growth_pct', 'annual_expense_growth_pct',
        'expected_annual_return_pct', 'annual_inflation_pct'
    }
    base_inputs = {k: inputs[k] for k in base_input_fields if k in inputs}

    # Validate base inputs using V1 validation
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'financial_engine', 'core'))
    from calculations import validate_inputs

    try:
        validated_base_inputs = validate_inputs(base_inputs)
    except ValueError as e:
        raise ValueError(f"Invalid base inputs: {str(e)}")

    # Combine validated base inputs with validated goal-specific fields
    validated_inputs = validated_base_inputs.copy()
    validated_inputs['goal_name'] = validated_goal_name
    validated_inputs['target_amount'] = validated_target_amount
    validated_inputs['target_age'] = validated_target_age

    return validated_inputs


def binary_search_contribution(base_inputs, target_amount, target_age):
    """
    Solve for monthly investment contribution using binary search.

    Parameters:
    -----------
    base_inputs : dict
        V1 validated inputs (excluding contribution which is solved for)
    target_amount : float
        Desired future wealth amount (nominal currency)
    target_age : int
        Age by which to achieve the goal

    Returns:
    --------
    dict
        {
            'required_monthly_investment': float,
            'projected_wealth_at_target': float,
            'surplus_or_shortfall': float,
            'calculation_method': str,
            'iterations': int,
            'convergence_tolerance': float,
            'verification_passed': bool
        }
    """
    # Import V1 functions
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'financial_engine', 'core'))
    from calculations import validate_inputs, calculate_projection

    current_age = base_inputs['current_age']

    # Handle special case: goal already met with current savings
    current_savings = base_inputs['current_savings']
    if target_amount <= current_savings:
        # No contribution needed - we already have enough or more
        test_inputs = base_inputs.copy()
        test_inputs['monthly_investment_contribution'] = 0.0
        validated_inputs = validate_inputs(test_inputs)
        projection = calculate_projection(validated_inputs)
        projected_wealth = projection[-1]['ending_nominal_wealth'] if projection else current_savings

        # Surplus is what we have extra (positive means we have more than target)
        surplus = projected_wealth - target_amount

        return {
            'required_monthly_investment': 0.0,
            'projected_wealth_at_target': projected_wealth,
            'surplus_or_shortfall': surplus,
            'calculation_method': 'direct',
            'iterations': 0,
            'convergence_tolerance': abs(surplus),
            'verification_passed': True
        }

    # Set up binary search
    monthly_income = base_inputs['monthly_income']
    monthly_expenses = base_inputs['monthly_expenses']
    max_contribution = monthly_income - monthly_expenses

    # Ensure max_contribution is non-negative (should be validated already, but double-check)
    if max_contribution < 0:
        max_contribution = 0.0

    # Check if we already exceed target with zero contribution
    test_inputs_zero = base_inputs.copy()
    test_inputs_zero['monthly_investment_contribution'] = 0.0
    validated_inputs_zero = validate_inputs(test_inputs_zero)
    projection_zero = calculate_projection(validated_inputs_zero)
    wealth_at_zero = projection_zero[-1]['ending_nominal_wealth'] if projection_zero else current_savings

    if wealth_at_zero >= target_amount - 0.01:  # Using tolerance of 0.01
        # We already meet or exceed target with zero contribution
        surplus = wealth_at_zero - target_amount  # Positive means surplus
        return {
            'required_monthly_investment': 0.0,
            'projected_wealth_at_target': wealth_at_zero,
            'surplus_or_shortfall': surplus,
            'calculation_method': 'direct',
            'iterations': 0,
            'convergence_tolerance': abs(surplus),
            'verification_passed': True
        }

    # If even maximum contribution can't reach goal, return boundary solution
    test_inputs_max = base_inputs.copy()
    test_inputs_max['monthly_investment_contribution'] = max_contribution
    validated_inputs_max = validate_inputs(test_inputs_max)
    projection_max = calculate_projection(validated_inputs_max)
    wealth_at_max = projection_max[-1]['ending_nominal_wealth'] if projection_max else current_savings

    if wealth_at_max < target_amount - 0.01:  # Using tolerance of 0.01
        # Even maximum contribution isn't enough
        surplus = wealth_at_max - target_amount  # Negative means shortfall
        return {
            'required_monthly_investment': max_contribution,
            'projected_wealth_at_target': wealth_at_max,
            'surplus_or_shortfall': surplus,
            'calculation_method': 'boundary',
            'iterations': 0,
            'convergence_tolerance': abs(surplus),
            'verification_passed': False  # Could not reach target
        }

    # Binary search setup
    low = 0.0
    high = max_contribution
    tolerance = 0.01  # Currency units
    max_iterations = 100
    iteration = 0
    best_contribution = 0.0
    best_wealth = current_savings
    best_error = float('inf')

    # Binary search loop
    while low <= high and iteration < max_iterations:
        iteration += 1
        mid = (low + high) / 2.0

        # Test this contribution level
        test_inputs = base_inputs.copy()
        test_inputs['monthly_investment_contribution'] = mid
        validated_inputs = validate_inputs(test_inputs)
        projection = calculate_projection(validated_inputs)
        wealth_at_mid = projection[-1]['ending_nominal_wealth'] if projection else current_savings

        error = abs(wealth_at_mid - target_amount)

        # Track best solution
        if error < best_error:
            best_error = error
            best_contribution = mid
            best_wealth = wealth_at_mid

        # Check if we've reached desired tolerance
        if error <= tolerance:
            # Found good solution, verify it
            surplus = wealth_at_mid - target_amount  # Positive = surplus, Negative = shortfall
            return {
                'required_monthly_investment': mid,
                'projected_wealth_at_target': wealth_at_mid,
                'surplus_or_shortfall': surplus,
                'calculation_method': 'binary_search',
                'iterations': iteration,
                'convergence_tolerance': error,
                'verification_passed': True
            }

        # Adjust search range
        if wealth_at_mid < target_amount:
            # Need more contribution
            low = mid
        else:
            # Need less contribution
            high = mid

    # If we exit loop, use best solution found
    # Verify the best solution
    test_inputs_best = base_inputs.copy()
    test_inputs_best['monthly_investment_contribution'] = best_contribution
    validated_inputs_best = validate_inputs(test_inputs_best)
    projection_best = calculate_projection(validated_inputs_best)
    wealth_at_best = projection_best[-1]['ending_nominal_wealth'] if projection_best else current_savings

    surplus = wealth_at_best - target_amount  # Positive = surplus, Negative = shortfall
    return {
        'required_monthly_investment': best_contribution,
        'projected_wealth_at_target': wealth_at_best,
        'surplus_or_shortfall': surplus,
        'calculation_method': 'binary_search',
        'iterations': iteration,
        'convergence_tolerance': best_error,
        'verification_passed': best_error <= tolerance
    }