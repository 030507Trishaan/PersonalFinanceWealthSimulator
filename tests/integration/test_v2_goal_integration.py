"""
Integration tests for V2 goal planning
"""
import unittest
import sys
import os

# Add project directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import from the v2_extensions package
from v2_extensions.goal_planning import calculate_goal_requirements

class TestV2GoalIntegration(unittest.TestCase):
    """Integration tests for V2 goal planning"""

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

    def test_goal_planning_zero_growth_scenario(self):
        """Test goal planning with zero growth rates and zero return"""
        # Use zero growth inputs for predictable results
        zero_growth_inputs = self.base_inputs.copy()
        zero_growth_inputs.update({
            'annual_income_growth_pct': 0.0,
            'annual_expense_growth_pct': 0.0,
            'expected_annual_return_pct': 0.0,
            'annual_inflation_pct': 0.0
        })

        # Calculate annual savings from income - expenses
        annual_savings = (zero_growth_inputs['monthly_income'] - zero_growth_inputs['monthly_expenses']) * 12.0
        years = zero_growth_inputs['target_age'] - zero_growth_inputs['current_age']
        # Target wealth achievable by saving all savings in cash (zero investment)
        target_wealth = zero_growth_inputs['current_savings'] + annual_savings * years

        goal_inputs = zero_growth_inputs.copy()
        goal_inputs.update({
            'goal_name': 'Zero Growth Test',
            'target_amount': target_wealth,
            'target_age': zero_growth_inputs['target_age']
        })

        result = calculate_goal_requirements(
            base_inputs=zero_growth_inputs,
            goal_name=goal_inputs['goal_name'],
            target_amount=goal_inputs['target_amount'],
            target_age=goal_inputs['target_age']
        )

        # Should require approximately zero monthly investment (since savings alone suffice)
        self.assertAlmostEqual(result['required_monthly_investment'], 0.0, places=1)
        self.assertIn(result['calculation_method'], ['direct', 'binary_search'])
        self.assertGreaterEqual(result['iterations'], 0)
        self.assertTrue(result['verification_passed'])
        self.assertAlmostEqual(result['surplus_or_shortfall'], 0.0, places=1)
        self.assertTrue(result['goal_reached'])  # Target met exactly

    def test_goal_planning_unreachable_goal(self):
        """Test goal planning when goal is unreachable even with maximum contribution"""
        # Set up a scenario where even saving everything won't reach the goal
        # Very low income, high expenses, huge target
        unlikely_inputs = self.base_inputs.copy()
        unlikely_inputs.update({
            'monthly_income': 2000.0,    # Low income
            'monthly_expenses': 1900.0,  # High expenses (only 100/month savings)
            'monthly_investment_contribution': 100.0,  # Maximum allowed
            'expected_annual_return_pct': 1.0,  # Low return
            'target_age': 35             # Only 5 years
        })

        goal_inputs = unlikely_inputs.copy()
        goal_inputs.update({
            'goal_name': 'Unreachable Goal',
            'target_amount': 1000000.0,  # One million - almost impossible
            'target_age': 35
        })

        result = calculate_goal_requirements(
            base_inputs=unlikely_inputs,
            goal_name=goal_inputs['goal_name'],
            target_amount=goal_inputs['target_amount'],
            target_age=goal_inputs['target_age']
        )

        # Should require maximum possible contribution
        max_possible = unlikely_inputs['monthly_income'] - unlikely_inputs['monthly_expenses']  # 100.0
        self.assertEqual(result['required_monthly_investment'], max_possible)
        self.assertEqual(result['calculation_method'], 'boundary')
        self.assertEqual(result['iterations'], 0)
        self.assertFalse(result['goal_reached'])  # Definitely not reached
        self.assertLess(result['surplus_or_shortfall'], 0)  # Negative (shortfall)
        self.assertFalse(result['verification_passed'])  # Could not verify reaching target

    def test_goal_planning_goal_already_met(self):
        """Test goal planning when goal is already met"""
        # Set target amount less than current savings
        goal_inputs = self.base_inputs.copy()
        goal_inputs.update({
            'goal_name': 'Emergency Fund',
            'target_amount': 5000.0,  # Less than current_savings (10000)
            'target_age': 35
        })

        result = calculate_goal_requirements(
            base_inputs=self.base_inputs,
            goal_name=goal_inputs['goal_name'],
            target_amount=goal_inputs['target_amount'],
            target_age=goal_inputs['target_age']
        )

        self.assertEqual(result['goal_name'], 'Emergency Fund')
        self.assertEqual(result['target_amount'], 5000.0)
        self.assertEqual(result['target_age'], 35)
        self.assertEqual(result['current_age'], 30)
        self.assertEqual(result['required_monthly_investment'], 0.0)
        self.assertEqual(result['calculation_method'], 'direct')
        self.assertEqual(result['iterations'], 0)
        self.assertTrue(result['verification_passed'])
        self.assertTrue(result['goal_reached'])  # Should be True since we have more than needed
        self.assertGreaterEqual(result['projected_wealth_at_target'], 5000.0)

    def test_v2_modules_preserve_v1_behavior(self):
        """Test that V2 modules don't change V1 engine behavior"""
        # Run goal planning to get recommendation
        goal_inputs = self.base_inputs.copy()
        goal_inputs.update({
            'goal_name': 'Preservation Test',
            'target_amount': 50000.0,
            'target_age': 35
        })

        result = calculate_goal_requirements(
            base_inputs=self.base_inputs,
            goal_name=goal_inputs['goal_name'],
            target_amount=goal_inputs['target_amount'],
            target_age=goal_inputs['target_age']
        )

        # Run V1 engine with the recommended contribution
        test_inputs = self.base_inputs.copy()
        test_inputs['monthly_investment_contribution'] = result['required_monthly_investment']
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'financial_engine', 'core'))
        from calculations import validate_inputs, calculate_projection

        validated_inputs = validate_inputs(test_inputs)
        v2_projection = calculate_projection(validated_inputs)

        # The V2 projection should match what goal planning predicted
        # Check final wealth matches prediction
        if v2_projection:
            actual_wealth = v2_projection[-1]['ending_nominal_wealth']
            predicted_wealth = result['projected_wealth_at_target']
            self.assertAlmostEqual(actual_wealth, predicted_wealth, places=10)
            # Also verify we can reach the goal (or understand why not)
            self.assertEqual(result['goal_reached'], actual_wealth >= result['target_amount'] - 0.01)

if __name__ == '__main__':
    unittest.main()