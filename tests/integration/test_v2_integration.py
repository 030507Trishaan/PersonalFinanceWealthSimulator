"""
Integration tests for V2 extensions
"""

import unittest
import sys
import os

# Add project directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import from the v2_extensions package
from v2_extensions.scenario_comparison import run_scenario_comparison
from v2_extensions.goal_planning import calculate_goal_requirements


class TestV2Integration(unittest.TestCase):
    """Integration tests for V2 extensions"""

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

    def test_goal_planning_integration_with_v1_engine(self):
        """Test that goal planning properly integrates with V1 engine"""
        # Test a case where we know the answer or can verify it
        goal_inputs = self.base_inputs.copy()
        goal_inputs.update({
            'goal_name': 'Integration Test',
            'target_amount': 50000.0,
            'target_age': 35
        })

        result = calculate_goal_requirements(
            base_inputs=self.base_inputs,
            goal_name=goal_inputs['goal_name'],
            target_amount=goal_inputs['target_amount'],
            target_age=goal_inputs['target_age']
        )

        # Should return a valid result structure
        self.assertIn('required_monthly_investment', result)
        self.assertIn('projected_wealth_at_target', result)
        self.assertIn('surplus_or_shortfall', result)
        self.assertIn('goal_reached', result)
        self.assertIn('calculation_method', result)
        self.assertIn('verification_passed', result)

        # Types should be correct
        self.assertIsInstance(result['required_monthly_investment'], (int, float))
        self.assertIsInstance(result['projected_wealth_at_target'], (int, float))
        self.assertIsInstance(result['surplus_or_shortfall'], (int, float))
        self.assertIsInstance(result['goal_reached'], bool)
        self.assertIsInstance(result['calculation_method'], str)
        self.assertIsInstance(result['verification_passed'], bool)

        # If verification passed and we used binary search, we can do a stronger test
        # (direct method may have large surplus/deficit from early exit)
        if result['verification_passed'] and result['calculation_method'] == 'binary_search':
            # Plug the solved contribution back into V1 engine and verify we get close to target
            test_inputs = self.base_inputs.copy()
            test_inputs['monthly_investment_contribution'] = result['required_monthly_investment']

            # Import V1 functions
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'financial_engine', 'core'))
            from calculations import validate_inputs, calculate_projection

            validated_inputs = validate_inputs(test_inputs)
            projection = calculate_projection(validated_inputs)
            actual_wealth = projection[-1]['ending_nominal_wealth'] if projection else self.base_inputs['current_savings']

            # Should be close to target amount (within tolerance)
            self.assertAlmostEqual(actual_wealth, result['target_amount'], places=0)
            self.assertAlmostEqual(result['projected_wealth_at_target'], actual_wealth, places=0)

    def test_scenario_and_goal_planning_workflow(self):
        """Test a workflow where scenario results inform goal planning"""
        # Run scenario comparison first
        scenario_results = run_scenario_comparison(self.base_inputs)

        # Use the optimistic scenario as a basis for goal planning
        optimistic_scenario = scenario_results['scenarios']['optimistic']
        self.assertNotIn('error', optimistic_scenario, "Optimistic scenario failed")

        optimistic_inputs = optimistic_scenario['inputs']
        optimistic_projection = optimistic_scenario['projection']

        # Get the projected wealth at target age from optimistic scenario
        if len(optimistic_projection) > 0:
            optimistic_wealth_at_target = optimistic_projection[-1]['ending_nominal_wealth']

            # Now set a goal to exceed that wealth by some amount
            goal_target = optimistic_wealth_at_target + 10000.0  # Want to beat optimistic scenario by 10k

            goal_result = calculate_goal_requirements(
                base_inputs=optimistic_inputs,  # Use optimistic scenario as base
                goal_name='Beat Optimistic Scenario',
                target_amount=goal_target,
                target_age=optimistic_inputs['target_age']
            )

            # Should return a valid goal planning result
            self.assertIn('required_monthly_investment', goal_result)
            self.assertIn('verification_passed', goal_result)

            # The required investment should be non-negative
            self.assertGreaterEqual(goal_result['required_monthly_investment'], 0.0)

            # If verification passed, we can verify the math
            if goal_result['verification_passed']:
                # Plug back into V1 engine with optimistic inputs + solved contribution
                test_inputs = optimistic_inputs.copy()
                test_inputs['monthly_investment_contribution'] = goal_result['required_monthly_investment']

                # Import V1 functions
                import sys
                import os
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'financial_engine', 'core'))
                from calculations import validate_inputs, calculate_projection

                validated_inputs = validate_inputs(test_inputs)
                projection = calculate_projection(validated_inputs)
                actual_wealth = projection[-1]['ending_nominal_wealth'] if projection else optimistic_inputs['current_savings']

                # Should be close to our goal target
                self.assertAlmostEqual(actual_wealth, goal_target, places=0)

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

    def test_edge_case_zero_time_horizon_approaching(self):
        """Test edge case where target age approaches current age"""
        # Target age very close to current age
        near_future_inputs = self.base_inputs.copy()
        near_future_inputs['target_age'] = 31  # Just 1 year ahead

        # Scenario comparison should work
        scenario_results = run_scenario_comparison(near_future_inputs)
        self.assertIn('scenarios', scenario_results)

        # Goal planning with near future goal
        goal_inputs = near_future_inputs.copy()
        goal_inputs.update({
            'goal_name': 'Near Future Goal',
            'target_amount': 15000.0,
            'target_age': 31
        })

        goal_result = calculate_goal_requirements(
            base_inputs=near_future_inputs,
            goal_name=goal_inputs['goal_name'],
            target_amount=goal_inputs['target_amount'],
            target_age=goal_inputs['target_age']
        )

        # Should return valid result
        self.assertIn('required_monthly_investment', goal_result)
        self.assertIn('calculation_method', goal_result)
        # For very short time horizons, might use different calculation method
        self.assertIn(goal_result['calculation_method'], ['direct', 'binary_search', 'boundary'])

    def test_edge_case_goal_already_exceeded(self):
        """Test goal planning when current savings already exceed target"""
        # Target less than current savings
        inputs = self.base_inputs.copy()
        inputs.update({
            'goal_name': 'Already Achieved',
            'target_amount': 5000.0,  # Less than current_savings (10000)
            'target_age': 35
        })

        goal_result = calculate_goal_requirements(
            base_inputs=inputs,
            goal_name=inputs['goal_name'],
            target_amount=inputs['target_amount'],
            target_age=inputs['target_age']
        )

        # Should require zero contribution
        self.assertEqual(goal_result['required_monthly_investment'], 0.0)
        self.assertEqual(goal_result['calculation_method'], 'direct')
        self.assertEqual(goal_result['iterations'], 0)
        self.assertTrue(goal_result['verification_passed'])
        # Should indicate goal is reached (we have more than needed)
        self.assertTrue(goal_result['goal_reached'])


if __name__ == '__main__':
    unittest.main()