"""
Integration tests for combined V2 scenario comparison and goal planning
"""
import unittest
import sys
import os

# Add project directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import from the v2_extensions package
from v2_extensions.scenario_comparison import run_scenario_comparison
from v2_extensions.goal_planning import calculate_goal_requirements

class TestV2CombinedIntegration(unittest.TestCase):
    """Integration tests for combined V2 scenario comparison and goal planning"""

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
                sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'financial_engine', 'core').replace('\\', '/'))
                from calculations import validate_inputs, calculate_projection

                validated_inputs = validate_inputs(test_inputs)
                projection = calculate_projection(validated_inputs)
                actual_wealth = projection[-1]['ending_nominal_wealth'] if projection else optimistic_inputs['current_savings']

                # Should be close to our goal target
                self.assertAlmostEqual(actual_wealth, goal_target, places=0)

    def test_goal_informing_scenario_adjustment(self):
        """Test a workflow where goal results inform scenario adjustments (conceptual)"""
        # First, run goal planning to see what contribution is needed for a goal
        goal_inputs = self.base_inputs.copy()
        goal_inputs.update({
            'goal_name': 'Growth Goal',
            'target_amount': 100000.0,
            'target_age': 35
        })

        goal_result = calculate_goal_requirements(
            base_inputs=self.base_inputs,
            goal_name=goal_inputs['goal_name'],
            target_amount=goal_inputs['target_amount'],
            target_age=goal_inputs['target_age']
        )

        # Should return a valid result
        self.assertIn('required_monthly_investment', goal_result)
        self.assertIn('verification_passed', goal_result)

        # If we have a solution, we could adjust scenario assumptions to see impact
        # For simplicity, we just verify that the goal result is sane
        if goal_result['verification_passed']:
            # The required contribution should be reasonable
            self.assertGreaterEqual(goal_result['required_monthly_investment'], 0.0)
            self.assertLess(goal_result['required_monthly_investment'],
                           self.base_inputs['monthly_income'] - self.base_inputs['monthly_expenses'] + 1.0)

    def test_v2_modules_preserve_v1_behavior_combined(self):
        """Test that combined V2 workflow doesn't change V1 engine behavior"""
        # Run V1 engine directly on base inputs
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'financial_engine', 'core').replace('\\', '/'))
        from calculations import validate_inputs, calculate_projection

        validated_inputs = validate_inputs(self.base_inputs)
        v1_projection = calculate_projection(validated_inputs)

        # Run scenario comparison
        v2_scenario_results = run_scenario_comparison(self.base_inputs)
        v2_base_scenario = v2_scenario_results['scenarios']['base']
        self.assertNotIn('error', v2_base_scenario)
        v2_base_projection = v2_base_scenario['projection']

        # Run goal planning
        goal_inputs = self.base_inputs.copy()
        goal_inputs.update({
            'goal_name': 'Combined Test',
            'target_amount': 50000.0,
            'target_age': 35
        })
        goal_result = calculate_goal_requirements(
            base_inputs=self.base_inputs,
            goal_name=goal_inputs['goal_name'],
            target_amount=goal_inputs['target_amount'],
            target_age=goal_inputs['target_age']
        )

        # Verify goal planning result has expected fields
        self.assertIn('required_monthly_investment', goal_result)
        self.assertIn('projected_wealth_at_target', goal_result)
        self.assertIn('surplus_or_shortfall', goal_result)
        self.assertIn('goal_reached', goal_result)
        self.assertIn('calculation_method', goal_result)

        # Base scenario from V2 should match V1 (using identical inputs)
        self.assertEqual(len(v1_projection), len(v2_base_projection))
        for i in range(len(v1_projection)):
            v1_year = v1_projection[i]
            v2b_year = v2_base_projection[i]

            self.assertAlmostEqual(v1_year['ending_nominal_wealth'], v2b_year['ending_nominal_wealth'], places=10)
            self.assertAlmostEqual(v1_year['ending_invested_wealth'], v2b_year['ending_invested_wealth'], places=10)
            self.assertAlmostEqual(v1_year['ending_cash_wealth'], v2b_year['ending_cash_wealth'], places=10)
            self.assertAlmostEqual(v1_year['annual_savings'], v2b_year['annual_savings'], places=10)

        # If goal planning determined that target is already achievable (zero contribution needed)
        if goal_result['required_monthly_investment'] == 0.0:
            # Create inputs with zero contribution to verify the goal claim
            test_inputs = self.base_inputs.copy()
            test_inputs['monthly_investment_contribution'] = 0.0
            validated_inputs = validate_inputs(test_inputs)
            v2_goal_projection = calculate_projection(validated_inputs)

            # Should have same length as V1 projection
            self.assertEqual(len(v1_projection), len(v2_goal_projection))

            # Get the target year projection (last year in the projection)
            target_year_idx = len(v2_goal_projection) - 1  # Year corresponding to target_age
            v2g_target_year = v2_goal_projection[target_year_idx]

            # Verify that with zero contribution, we meet or exceed the target amount at target age
            self.assertGreaterEqual(v2g_target_year['ending_nominal_wealth'], goal_result['target_amount'])
            self.assertAlmostEqual(goal_result['projected_wealth_at_target'], v2g_target_year['ending_nominal_wealth'], places=0)

            # Verify goal_reached is True when target is met or exceeded
            self.assertTrue(goal_result['goal_reached'])

            # Verify surplus_or_shortfall calculation is correct: projected - target
            expected_surplus = v2g_target_year['ending_nominal_wealth'] - goal_result['target_amount']
            self.assertAlmostEqual(goal_result['surplus_or_shortfall'], expected_surplus, places=0)

if __name__ == '__main__':
    unittest.main()