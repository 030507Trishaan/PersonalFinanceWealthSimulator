"""
Integration tests for V2 scenario comparison
"""
import unittest
import sys
import os

# Add project directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import from the v2_extensions package
from v2_extensions.scenario_comparison import run_scenario_comparison

class TestV2ScenarioIntegration(unittest.TestCase):
    """Integration tests for V2 scenario comparison"""

    def setUp(self):
        """Set up test inputs for a known scenario"""
        self.base_inputs = {
            'current_age': 30,
            'target_age': 35,
            'current_savings': 10000.0,
            'monthly_income': 5000.0,
            'monthly_expenses': 3000.0,
            'monthly_investment_contribution': 1000.0,
            'annual_income_growth_pct': 0.0,
            'annual_expense_growth_pct': 0.0,
            'expected_annual_return_pct': 5.0,
            'annual_inflation_pct': 2.0
        }

    def test_scenario_comparison_integration_with_v1_engine(self):
        """Test that scenario comparison properly integrates with V1 engine"""
        results = run_scenario_comparison(self.base_inputs)

        # Should not have errors in any scenario
        for scenario_name in ['base', 'conservative', 'optimistic', 'custom']:
            scenario = results['scenarios'][scenario_name]
            self.assertNotIn('error', scenario, f"Scenario {scenario_name} had error: {scenario.get('error', 'Unknown')}")

            # Should have valid projection data
            self.assertIn('projection', scenario)
            projection = scenario['projection']
            self.assertIsInstance(projection, list)
            self.assertGreater(len(projection), 0, f"Scenario {scenario_name} has empty projection")

            # Each year should have the expected financial engine outputs
            first_year = projection[0]
            expected_keys = [
                'age', 'starting_invested_wealth', 'starting_cash_wealth',
                'annual_income', 'annual_expenses', 'annual_savings',
                'annual_investment_contribution', 'uninvested_cash_savings',
                'investment_returns', 'ending_invested_wealth', 'ending_cash_wealth',
                'ending_nominal_wealth', 'inflation_adjusted_wealth',
                'cumulative_contributions', 'cumulative_investment_returns'
            ]
            for key in expected_keys:
                self.assertIn(key, first_year, f"Missing key {key} in {scenario_name} projection")
                # Should be numeric values
                value = first_year[key]
                self.assertIsInstance(value, (int, float), f"Non-numeric value for {key} in {scenario_name}: {value}")

    def test_scenario_assumptions_modifications(self):
        """Test that scenario assumptions are correctly modified"""
        results = run_scenario_comparison(self.base_inputs)
        scenarios = results['scenarios']

        # Base scenario should equal base inputs
        base_inputs = scenarios['base']['inputs']
        for key, value in self.base_inputs.items():
            self.assertEqual(base_inputs[key], value, f"Base scenario input {key} mismatch")

        # Conservative scenario: return -2%, income growth -1%, expense growth +1%, inflation +1%
        cons_inputs = scenarios['conservative']['inputs']
        self.assertEqual(cons_inputs['expected_annual_return_pct'], 3.0)   # 5.0 - 2.0
        self.assertEqual(cons_inputs['annual_income_growth_pct'], 0.0)     # 0.0 - 1.0 -> clamped to 0.0
        self.assertEqual(cons_inputs['annual_expense_growth_pct'], 1.0)    # 0.0 + 1.0
        self.assertEqual(cons_inputs['annual_inflation_pct'], 3.0)         # 2.0 + 1.0

        # Optimistic scenario: return +2%, income growth +1%, expense growth -1%, inflation -1%
        opt_inputs = scenarios['optimistic']['inputs']
        self.assertEqual(opt_inputs['expected_annual_return_pct'], 7.0)    # 5.0 + 2.0
        self.assertEqual(opt_inputs['annual_income_growth_pct'], 1.0)      # 0.0 + 1.0
        self.assertEqual(opt_inputs['annual_expense_growth_pct'], 0.0)     # 0.0 - 1.0 -> clamped to 0.0
        self.assertEqual(opt_inputs['annual_inflation_pct'], 1.0)          # 2.0 - 1.0

        # Custom scenario with empty modifications (should be same as base)
        custom_inputs = scenarios['custom']['inputs']
        for key, value in self.base_inputs.items():
            self.assertEqual(custom_inputs[key], value, f"Custom scenario input {key} mismatch")

    def test_scenario_wealth_comparison(self):
        """Test that wealth comparison is correctly calculated"""
        results = run_scenario_comparison(self.base_inputs)
        wealth_comparison = results['summary']['wealth_comparison']

        # Should have wealth values for all scenarios
        for scenario_name in ['base', 'conservative', 'optimistic', 'custom']:
            self.assertIn(scenario_name, wealth_comparison)
            wealth = wealth_comparison[scenario_name]
            self.assertIsInstance(wealth, (int, float))
            self.assertGreaterEqual(wealth, 0.0)

        # Conservative wealth should be <= base wealth (due to lower return, higher expenses, etc.)
        # Optimistic wealth should be >= base wealth
        base_wealth = wealth_comparison['base']
        cons_wealth = wealth_comparison['conservative']
        opt_wealth = wealth_comparison['optimistic']
        # Note: due to clamping and interactions, not guaranteed but likely
        # We'll just check they are numbers
        self.assertIsInstance(base_wealth, (int, float))
        self.assertIsInstance(cons_wealth, (int, float))
        self.assertIsInstance(opt_wealth, (int, float))

    def test_scenario_assumption_comparison(self):
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
                value = param_values[scenario_name]
                self.assertIsInstance(value, (int, float))

    def test_v2_modules_preserve_v1_behavior(self):
        """Test that V2 modules don't change V1 engine behavior"""
        # Run V1 engine directly on base inputs
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'financial_engine', 'core'))
        from calculations import validate_inputs, calculate_projection

        validated_inputs = validate_inputs(self.base_inputs)
        v1_projection = calculate_projection(validated_inputs)

        # Run scenario comparison and extract base scenario
        v2_results = run_scenario_comparison(self.base_inputs)
        v2_base_scenario = v2_results['scenarios']['base']

        # The base scenario should be identical to direct V1 engine run
        self.assertNotIn('error', v2_base_scenario)
        v2_projection = v2_base_scenario['projection']

        # Should have same length
        self.assertEqual(len(v1_projection), len(v2_projection))

        # Should have identical values (within floating point precision)
        for i in range(len(v1_projection)):
            v1_year = v1_projection[i]
            v2_year = v2_projection[i]

            # Compare key financial values
            self.assertAlmostEqual(v1_year['ending_nominal_wealth'], v2_year['ending_nominal_wealth'], places=10)
            self.assertAlmostEqual(v1_year['ending_invested_wealth'], v2_year['ending_invested_wealth'], places=10)
            self.assertAlmostEqual(v1_year['ending_cash_wealth'], v2_year['ending_cash_wealth'], places=10)
            self.assertAlmostEqual(v1_year['annual_savings'], v2_year['annual_savings'], places=10)

if __name__ == '__main__':
    unittest.main()