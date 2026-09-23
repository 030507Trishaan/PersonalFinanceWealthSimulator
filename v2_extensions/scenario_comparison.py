"""
Scenario comparison module for V2 extensions of Personal Finance & Wealth Simulator
Handles creation and execution of different financial assumption scenarios.
"""

def create_scenario_inputs(base_inputs, scenario_type, custom_modifications=None):
    """
    Create input dictionary for a specific scenario based on base inputs.

    Parameters:
    -----------
    base_inputs : dict
        V1 validated inputs from user
    scenario_type : str
        One of: 'base', 'conservative', 'optimistic', 'custom'
    custom_modifications : dict, optional
        For custom scenario: modifications to apply in the format:
        - 'expected_annual_return_pct_delta': float (percentage points)
        - 'annual_income_growth_pct_delta': float (percentage points)
        - 'annual_expense_growth_pct_delta': float (percentage points)
        - 'annual_inflation_pct_delta': float (percentage points)

    Returns:
    --------
    tuple (dict, list):
        - Modified inputs ready for V1 financial engine
        - List of warnings generated during processing

    Raises:
    -------
    ValueError
        If scenario_type is invalid or modifications create invalid inputs
    """
    # Import shared utilities
    from .shared_utils import validate_and_clamp_scenario_inputs

    # Validate scenario_type
    valid_scenarios = ['base', 'conservative', 'optimistic', 'custom']
    if scenario_type not in valid_scenarios:
        raise ValueError(f"scenario_type must be one of {valid_scenarios}, got '{scenario_type}'")

    # Base scenario: no modifications
    if scenario_type == 'base':
        return base_inputs.copy(), []

    # Define scenario deltas: [return_delta, income_growth_delta, expense_growth_delta, inflation_delta]
    scenario_deltas = {
        'conservative': [-2.0, -1.0, +1.0, +1.0],
        'optimistic': [+2.0, +1.0, -1.0, -1.0]
    }

    if scenario_type in scenario_deltas:
        # Create modifications dictionary from predefined deltas
        deltas = scenario_deltas[scenario_type]
        modifications = {
            'expected_annual_return_pct_delta': deltas[0],
            'annual_income_growth_pct_delta': deltas[1],
            'annual_expense_growth_pct_delta': deltas[2],
            'annual_inflation_pct_delta': deltas[3]
        }
        return validate_and_clamp_scenario_inputs(base_inputs, modifications)

    elif scenario_type == 'custom':
        if custom_modifications is None:
            custom_modifications = {}
        # Validate that custom_modifications only contains allowed keys
        allowed_keys = {
            'expected_annual_return_pct_delta',
            'annual_income_growth_pct_delta',
            'annual_expense_growth_pct_delta',
            'annual_inflation_pct_delta'
        }
        invalid_keys = set(custom_modifications.keys()) - allowed_keys
        if invalid_keys:
            raise ValueError(f"custom_modifications contains invalid keys: {invalid_keys}. Allowed keys: {allowed_keys}")

        # Validate delta values are reasonable (optional but good practice)
        for key, value in custom_modifications.items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"custom_modifications['{key}'] must be a number, got {type(value)}")
            # Optional: warn if delta is outside typical range
            if abs(value) > 20.0:
                # Not raising error, just letting clamping handle it
                pass

        return validate_and_clamp_scenario_inputs(base_inputs, custom_modifications)

    else:
        # This shouldn't happen due to validation above, but just in case
        raise ValueError(f"Unsupported scenario_type: {scenario_type}")


def run_scenario_comparison(base_inputs):
    """
    Run all four scenarios (base, conservative, optimistic, custom) and return results.

    Parameters:
    -----------
    base_inputs : dict
        V1 validated inputs from user

    Returns:
    --------
    dict
        {
            'scenarios': {
                'base': {
                    'inputs': dict,  # V1 inputs for base scenario
                    'projection': list  # Output from V1 calculate_projection(),
                    'warnings': list  # Any warnings from input processing
                },
                'conservative': {...},
                'optimistic': {...},
                'custom': {...}
            },
            'summary': {
                'wealth_comparison': dict,  # Ending wealth values for each scenario
                'assumption_comparison': dict  # Key assumption differences
            }
        }
    """
    # Import V1 functions
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'financial_engine', 'core'))
    from calculations import validate_inputs, calculate_projection

    # Validate base inputs first
    validated_base_inputs = validate_inputs(base_inputs)

    # Define scenarios to run
    scenario_types = ['base', 'conservative', 'optimistic', 'custom']
    scenarios = {}

    # Run each scenario
    for scenario_type in scenario_types:
        try:
            # For custom scenario, use empty modifications (user would provide these in real implementation)
            custom_mods = {} if scenario_type == 'custom' else None
            scenario_inputs, warnings = create_scenario_inputs(
                validated_base_inputs,
                scenario_type,
                custom_modifications=custom_mods
            )

            # Run the V1 financial engine
            projection = calculate_projection(scenario_inputs)

            scenarios[scenario_type] = {
                'inputs': scenario_inputs,
                'projection': projection,
                'warnings': warnings
            }

        except Exception as e:
            # If a scenario fails, we still want to return results for others
            scenarios[scenario_type] = {
                'error': str(e),
                'inputs': None,
                'projection': [],
                'warnings': []
            }

    # Create summary
    wealth_comparison = {}
    assumption_comparison = {}

    # Extract ending wealth values for summary
    for scenario_type in scenario_types:
        if scenario_type in scenarios and 'projection' in scenarios[scenario_type]:
            projection = scenarios[scenario_type]['projection']
            if projection:
                ending_wealth = projection[-1]['ending_nominal_wealth']
                wealth_comparison[scenario_type] = ending_wealth
            else:
                wealth_comparison[scenario_type] = None
        else:
            wealth_comparison[scenario_type] = None

    # Extract key assumptions for comparison (focus on the four varied parameters)
    key_params = ['expected_annual_return_pct', 'annual_income_growth_pct',
                  'annual_expense_growth_pct', 'annual_inflation_pct']
    for param in key_params:
        assumption_comparison[param] = {}
        for scenario_type in scenario_types:
            if scenario_type in scenarios and 'inputs' in scenarios[scenario_type]:
                assumption_comparison[param][scenario_type] = scenarios[scenario_type]['inputs'].get(param)
            else:
                assumption_comparison[param][scenario_type] = None

    return {
        'scenarios': scenarios,
        'summary': {
            'wealth_comparison': wealth_comparison,
            'assumption_comparison': assumption_comparison
        }
    }