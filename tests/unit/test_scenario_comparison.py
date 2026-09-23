"""
Unit tests for V2 scenario comparison module
"""

import unittest
import sys
import os

# Add project directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import from the v2_extensions package
from v2_extensions.scenario_comparison import create_scenario_inputs, run_scenario_comparison


class TestScenarioComparison(unittest.TestCase):
    """Test scenario comparison functions"""

    def setUp(self):
        """Set up test inputs for a known scenario"""
        self.base_inputs = {
            'current_age': 30,
            'target_age': 35,
            'current_savings': 10000.0,
            'monthly_income': 5000.0,
            'monthly_expenses': 3000.0,
            'monthly_investment_contribution': 1000.0,
            'annual_income_growth_pct': 3.0,
            'annual_expense_growth_pct': 2.0,
            'expected_annual_return_pct': 5.0,
            'annual_inflation_pct': 2.0
        }

    def test_create_scenario_inputs_base(self):
        """Test base scenario creation"""
        scenario_inputs, warnings = create_scenario_inputs(self.base_inputs, 'base')

        # Should be identical to base inputs
        self.assertEqual(scenario_inputs, self.base_inputs)
        self.assertEqual(len(warnings), 0)

    def test_create_scenario_inputs_conservative(self):
        """Test conservative scenario creation"""
        scenario_inputs, warnings = create_scenario_inputs(self.base_inputs, 'conservative')

        # Check that modifications were applied correctly
        # Conservative: return -2%, income growth -1%, expense growth +1%, inflation +1%
        self.assertEqual(scenario_inputs['expected_annual_return_pct'], 3.0)   # 5.0 - 2.0
        self.assertEqual(scenario_inputs['annual_income_growth_pct'], 2.0)     # 3.0 - 1.0
        self.assertEqual(scenario_inputs['annual_expense_growth_pct'], 3.0)    # 2.0 + 1.0
        self.assertEqual(scenario_inputs['annual_inflation_pct'], 3.0)         # 2.0 + 1.0

        # Other parameters should be unchanged
        self.assertEqual(scenario_inputs['current_age'], self.base_inputs['current_age'])
        self.assertEqual(scenario_inputs['monthly_income'], self.base_inputs['monthly_income'])

        # Should have warnings about clamping if any values went out of bounds
        # In this case, all values should be within [0, 20] so no clamping warnings

    def test_create_scenario_inputs_optimistic(self):
        """Test optimistic scenario creation"""
        scenario_inputs, warnings = create_scenario_inputs(self.base_inputs, 'optimistic')

        # Check that modifications were applied correctly
        # Optimistic: return +2%, income growth +1%, expense growth -1%, inflation -1%
        self.assertEqual(scenario_inputs['expected_annual_return_pct'], 7.0)   # 5.0 + 2.0
        self.assertEqual(scenario_inputs['annual_income_growth_pct'], 4.0)     # 3.0 + 1.0
        self.assertEqual(scenario_inputs['annual_expense_growth_pct'], 1.0)    # 2.0 - 1.0
        self.assertEqual(scenario_inputs['annual_inflation_pct'], 1.0)         # 2.0 - 1.0

        # Other parameters should be unchanged
        self.assertEqual(scenario_inputs['current_age'], self.base_inputs['current_age'])
        self.assertEqual(scenario_inputs['monthly_income'], self.base_inputs['monthly_income'])

    def test_create_scenario_inputs_custom(self):
        """Test custom scenario creation"""
        modifications = {
            'expected_annual_return_pct_delta': +1.5,
            'annual_income_growth_pct_delta': -0.5,
            'annual_expense_growth_pct_delta': +2.0,
            'annual_inflation_pct_delta': -1.0
        }

        scenario_inputs, warnings = create_scenario_inputs(
            self.base_inputs, 'custom', custom_modifications=modifications
        )

        # Check that modifications were applied correctly
        self.assertEqual(scenario_inputs['expected_annual_return_pct'], 6.5)   # 5.0 + 1.5
        self.assertEqual(scenario_inputs['annual_income_growth_pct'], 2.5)     # 3.0 - 0.5
        self.assertEqual(scenario_inputs['annual_expense_growth_pct'], 4.0)    # 2.0 + 2.0
        self.assertEqual(scenario_inputs['annual_inflation_pct'], 1.0)         # 2.0 - 1.0

        # Other parameters should be unchanged
        self.assertEqual(scenario_inputs['current_age'], self.base_inputs['current_age'])
        self.assertEqual(scenario_inputs['monthly_income'], self.base_inputs['monthly_income'])

    def test_create_scenario_inputs_custom_out_of_bounds_deltas(self):
        """Test custom scenario with deltas outside allowed range [-20,20] raises ValueError"""
        modifications = {
            'expected_annual_return_pct_delta': -10.0,  # This is within [-20,20], ok
            'annual_income_growth_pct_delta': +25.0,    # Outside +20
            'annual_expense_growth_pct_delta': -5.0,    # Within
            'annual_inflation_pct_delta': +30.0         # Outside +20
        }

        with self.assertRaises(ValueError) as context:
            create_scenario_inputs(
                self.base_inputs, 'custom', custom_modifications=modifications
            )
        # Check that error message mentions the invalid delta
        self.assertIn('must be between -20.0 and 20.0 percentage points', str(context.exception))

    def test_create_scenario_inputs_invalid_type(self):
        """Test that invalid scenario type raises ValueError"""
        with self.assertRaises(ValueError) as context:
            create_scenario_inputs(self.base_inputs, 'invalid_type')
        self.assertIn("scenario_type must be one of", str(context.exception))

    def test_create_scenario_inputs_custom_invalid_keys(self):
        """Test that custom scenario with invalid keys raises ValueError"""
        modifications = {
            'invalid_param': 1.0,
            'another_invalid': 2.0
        }

        with self.assertRaises(ValueError) as context:
            create_scenario_inputs(self.base_inputs, 'custom', custom_modifications=modifications)
        self.assertIn("custom_modifications contains invalid keys", str(context.exception))

    def test_create_scenario_inputs_custom_non_numeric_delta(self):
        """Test that custom scenario with non-numeric delta raises ValueError"""
        modifications = {
            'expected_annual_return_pct_delta': 'not_a_number'
        }

        with self.assertRaises(ValueError) as context:
            create_scenario_inputs(self.base_inputs, 'custom', custom_modifications=modifications)
        self.assertIn("must be a number", str(context.exception))

    def test_run_scenario_comparison_basic(self):
        """Test running full scenario comparison"""
        results = run_scenario_comparison(self.base_inputs)

        # Check structure
        self.assertIn('scenarios', results)
        self.assertIn('summary', results)
        self.assertIn('wealth_comparison', results['summary'])
        self.assertIn('assumption_comparison', results['summary'])

        # Check that all four scenarios are present
        scenarios = results['scenarios']
        self.assertIn('base', scenarios)
        self.assertIn('conservative', scenarios)
        self.assertIn('optimistic', scenarios)
        self.assertIn('custom', scenarios)

        # Check that each scenario has the expected structure
        for scenario_name in ['base', 'conservative', 'optimistic', 'custom']:
            self.assertIn(scenario_name, scenarios)
            scenario = scenarios[scenario_name]
            # Should not have error key if successful
            if 'error' not in scenario:
                self.assertIn('inputs', scenario)
                self.assertIn('projection', scenario)
                self.assertIn('warnings', scenario)
                # Projection should be a list
                self.assertIsInstance(scenario['projection'], list)
                # If we have projection data, it should have the expected keys
                if len(scenario['projection']) > 0:
                    first_year = scenario['projection'][0]
                    expected_keys = ['age', 'starting_invested_wealth', 'starting_cash_wealth',
                                   'annual_income', 'annual_expenses', 'annual_savings',
                                   'annual_investment_contribution', 'uninvested_cash_savings',
                                   'investment_returns', 'ending_invested_wealth', 'ending_cash_wealth',
                                   'ending_nominal_wealth', 'inflation_adjusted_wealth',
                                   'cumulative_contributions', 'cumulative_investment_returns']
                    for key in expected_keys:
                        self.assertIn(key, first_year)

    def test_run_scenario_comparison_wealth_comparison(self):
        """Test that wealth comparison is correctly calculated"""
        results = run_scenario_comparison(self.base_inputs)

        wealth_comparison = results['summary']['wealth_comparison']

        # Should have wealth values for all scenarios
        for scenario_name in ['base', 'conservative', 'optimistic', 'custom']:
            self.assertIn(scenario_name, wealth_comparison)
            wealth = wealth_comparison[scenario_name]
            # Should be a number or None (if error occurred)
            if wealth is not None:
                self.assertIsInstance(wealth, (int, float))
                self.assertGreaterEqual(wealth, 0.0)

    def test_run_scenario_comparison_assumption_comparison(self):
        """Test that assumption comparison is correctly calculated"""
        results = run_scenario_comparison(self.base_inputs)

        assumption_comparison = results['summary']['assumption_comparison']

        # Should have the four varied parameters
        expected_params = ['expected_annual_return_pct', 'annual_income_growth_pct',
                          'annual_expense_growth_pct', 'annual_inflation_pct']
        for param in expected_params:
            self.assertIn(param, assumption_comparison)
            param_values = assumption_comparison[param]
            # Should have values for all scenarios
            for scenario_name in ['base', 'conservative', 'optimistic', 'custom']:
                self.assertIn(scenario_name, param_values)
                # Should be a number or None (if error occurred)
                value = param_values[scenario_name]
                if value is not None:
                    self.assertIsInstance(value, (int, float))

    def test_run_scenario_comparison_conservative_vs_base_relationships(self):
        """Test that conservative scenario has appropriate relationships to base"""
        results = run_scenario_comparison(self.base_inputs)

        # Get the scenarios
        base_scenario = results['scenarios']['base']
        conservative_scenario = results['scenarios']['conservative']

        # Skip if either had errors
        if 'error' in base_scenario or 'error' in conservative_scenario:
            self.skipTest("One or more scenarios had errors")

        base_projection = base_scenario['projection']
        conservative_projection = conservative_scenario['projection']

        # Skip if no projection data
        if len(base_projection) == 0 or len(conservative_projection) == 0:
            self.skipTest("No projection data available")

        # Conservative should have lower or equal return and income growth
        # and higher or equal expense growth and inflation
        base_inputs = base_scenario['inputs']
        conservative_inputs = conservative_scenario['inputs']

        # Return: conservative <= base
        self.assertLessEqual(
            conservative_inputs['expected_annual_return_pct'],
            base_inputs['expected_annual_return_pct']
        )

        # Income growth: conservative <= base
        self.assertLessEqual(
            conservative_inputs['annual_income_growth_pct'],
            base_inputs['annual_income_growth_pct']
        )

        # Expense growth: conservative >= base
        self.assertGreaterEqual(
            conservative_inputs['annual_expense_growth_pct'],
            base_inputs['annual_expense_growth_pct']
        )

        # Inflation: conservative >= base
        self.assertGreaterEqual(
            conservative_inputs['annual_inflation_pct'],
            base_inputs['annual_inflation_pct']
        )

    def test_run_scenario_comparison_optimistic_vs_base_relationships(self):
        """Test that optimistic scenario has appropriate relationships to base"""
        results = run_scenario_comparison(self.base_inputs)

        # Get the scenarios
        base_scenario = results['scenarios']['base']
        optimistic_scenario = results['scenarios']['optimistic']

        # Skip if either had errors
        if 'error' in base_scenario or 'error' in optimistic_scenario:
            self.skipTest("One or more scenarios had errors")

        base_projection = base_scenario['projection']
        optimistic_projection = optimistic_scenario['projection']

        # Skip if no projection data
        if len(base_projection) == 0 or len(optimistic_projection) == 0:
            self.skipTest("No projection data available")

        # Optimistic should have higher or equal return and income growth
        # and lower or equal expense growth and inflation
        base_inputs = base_scenario['inputs']
        optimistic_inputs = optimistic_scenario['inputs']

        # Return: optimistic >= base
        self.assertGreaterEqual(
            optimistic_inputs['expected_annual_return_pct'],
            base_inputs['expected_annual_return_pct']
        )

        # Income growth: optimistic >= base
        self.assertGreaterEqual(
            optimistic_inputs['annual_income_growth_pct'],
            base_inputs['annual_income_growth_pct']
        )

        # Expense growth: optimistic <= base
        self.assertLessEqual(
            optimistic_inputs['annual_expense_growth_pct'],
            base_inputs['annual_expense_growth_pct']
        )

        # Inflation: optimistic <= base
        self.assertLessEqual(
            optimistic_inputs['annual_inflation_pct'],
            base_inputs['annual_inflation_pct']
        )


if __name__ == '__main__':
    unittest.main()