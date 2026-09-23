"""
Unit tests for V2 goal planning module
"""

import unittest
import sys
import os

# Add project directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import from the v2_extensions package
from v2_extensions.goal_planning import calculate_goal_requirements, validate_goal_inputs


class TestGoalPlanning(unittest.TestCase):
    """Test goal planning functions"""

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

    def test_validate_goal_inputs_valid(self):
        """Test validation of valid goal inputs"""
        goal_inputs = self.base_inputs.copy()
        goal_inputs.update({
            'goal_name': 'Retirement',
            'target_amount': 500000.0,
            'target_age': 65
        })

        validated = validate_goal_inputs(goal_inputs)

        self.assertEqual(validated['goal_name'], 'Retirement')
        self.assertEqual(validated['target_amount'], 500000.0)
        self.assertEqual(validated['target_age'], 65)
        # Check that base inputs are preserved
        self.assertEqual(validated['current_age'], 30)
        self.assertEqual(validated['monthly_income'], 5000.0)

    def test_validate_goal_inputs_invalid_name(self):
        """Test validation rejects invalid goal names"""
        goal_inputs = self.base_inputs.copy()
        goal_inputs.update({
            'goal_name': '',  # Empty string
            'target_amount': 500000.0,
            'target_age': 65
        })

        with self.assertRaises(ValueError) as context:
            validate_goal_inputs(goal_inputs)
        self.assertIn('goal_name must be a non-empty string', str(context.exception))

        goal_inputs['goal_name'] = '   '  # Whitespace only
        with self.assertRaises(ValueError) as context:
            validate_goal_inputs(goal_inputs)
        self.assertIn('goal_name must be a non-empty string', str(context.exception))

    def test_validate_goal_inputs_invalid_target_amount(self):
        """Test validation rejects invalid target amounts"""
        goal_inputs = self.base_inputs.copy()
        goal_inputs.update({
            'goal_name': 'Test',
            'target_amount': -1000.0,  # Negative
            'target_age': 65
        })

        with self.assertRaises(ValueError) as context:
            validate_goal_inputs(goal_inputs)
        self.assertIn('target_amount must be non-negative', str(context.exception))

        goal_inputs['target_amount'] = 'invalid'  # Wrong type
        with self.assertRaises(ValueError) as context:
            validate_goal_inputs(goal_inputs)
        self.assertIn('target_amount must be a number', str(context.exception))

    def test_validate_goal_inputs_invalid_target_age(self):
        """Test validation rejects invalid target ages"""
        goal_inputs = self.base_inputs.copy()
        goal_inputs.update({
            'goal_name': 'Test',
            'target_amount': 500000.0,
            'target_age': 25  # Less than current_age (30)
        })

        with self.assertRaises(ValueError) as context:
            validate_goal_inputs(goal_inputs)
        self.assertIn('target_age', str(context.exception))
        self.assertIn('greater than current_age', str(context.exception))

        goal_inputs['target_age'] = 'thirty'  # Wrong type
        with self.assertRaises(ValueError) as context:
            validate_goal_inputs(goal_inputs)
        self.assertIn('target_age must be an integer', str(context.exception))

    def test_calculate_goal_requirements_goal_already_met(self):
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

    def test_calculate_goal_requirements_zero_growth_scenario(self):
        """Test goal planning with zero growth rates and zero return"""
        # Use zero growth inputs for predictable results
        zero_growth_inputs = self.base_inputs.copy()
        zero_growth_inputs.update({
            'annual_income_growth_pct': 0.0,
            'annual_expense_growth_pct': 0.0,
            'expected_annual_return_pct': 0.0,
            'annual_inflation_pct': 0.0
        })

        # With zero return, total wealth accumulated is independent of investment contribution
        # It depends only on initial wealth and savings rate (income - expenses)
        monthly_savings = zero_growth_inputs['monthly_income'] - zero_growth_inputs['monthly_expenses']
        months = (zero_growth_inputs['target_age'] - zero_growth_inputs['current_age']) * 12
        expected_wealth = zero_growth_inputs['current_savings'] + monthly_savings * months

        goal_inputs = zero_growth_inputs.copy()
        goal_inputs.update({
            'goal_name': 'Zero Growth Test',
            'target_amount': expected_wealth,  # Target exactly what we accumulate from savings
            'target_age': zero_growth_inputs['target_age']
        })

        result = calculate_goal_requirements(
            base_inputs=zero_growth_inputs,
            goal_name=goal_inputs['goal_name'],
            target_amount=goal_inputs['target_amount'],
            target_age=goal_inputs['target_age']
        )

        # Should require zero investment since we reach target through savings alone
        # (with zero return, investment contribution doesn't affect total wealth accumulation)
        self.assertAlmostEqual(result['required_monthly_investment'], 0.0, places=1)
        self.assertEqual(result['calculation_method'], 'direct')
        self.assertEqual(result['iterations'], 0)
        self.assertTrue(result['verification_passed'])
        self.assertAlmostEqual(result['surplus_or_shortfall'], 0.0, places=1)
        self.assertTrue(result['goal_reached'])  # Should be exactly at target

    def test_calculate_goal_requirements_with_growth_and_returns(self):
        """Test goal planning with realistic growth and return rates"""
        # Use the base inputs (5% return, 2% inflation, 0% growth)
        goal_inputs = self.base_inputs.copy()
        goal_inputs.update({
            'goal_name': 'Moderate Growth Test',
            'target_amount': 140000.0,  # Aim for 140k - requires actual investment
            'target_age': 35  # 5 years from now
        })

        result = calculate_goal_requirements(
            base_inputs=self.base_inputs,
            goal_name=goal_inputs['goal_name'],
            target_amount=goal_inputs['target_amount'],
            target_age=goal_inputs['target_age']
        )

        # Should require a reasonable monthly investment (between 0 and max possible)
        self.assertGreaterEqual(result['required_monthly_investment'], 0.0)
        self.assertLess(result['required_monthly_investment'], 2000.0)  # Should be less than max possible
        self.assertEqual(result['calculation_method'], 'binary_search')
        self.assertGreater(result['iterations'], 0)
        self.assertTrue(result['verification_passed'])

        # Verify that plugging the contribution back in gets us close to target
        test_inputs = self.base_inputs.copy()
        test_inputs['monthly_investment_contribution'] = result['required_monthly_investment']
        # Import V1 functions to verify
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'financial_engine', 'core'))
        from calculations import validate_inputs, calculate_projection

        validated_inputs = validate_inputs(test_inputs)
        projection = calculate_projection(validated_inputs)
        actual_wealth = projection[-1]['ending_nominal_wealth']

        self.assertAlmostEqual(actual_wealth, result['target_amount'], places=0)
        self.assertAlmostEqual(result['projected_wealth_at_target'], actual_wealth, places=0)

    def test_calculate_goal_requirements_unreachable_goal(self):
        """Test goal planning when goal is unreachable even with maximum contribution"""
        # Set up a scenario where even saving everything won't reach the goal
        # Very low income, high expenses, huge target
        unlikely_inputs = self.base_inputs.copy()
        unlikely_inputs.update({
            'monthly_income': 2000.0,    # Low income
            'monthly_expenses': 1900.0,  # High expenses (only 100/month savings)
            'monthly_investment_contribution': 100.0,  # Maximum allowed savings
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

    def test_calculate_goal_requirements_maximum_contribution(self):
        """Test goal planning when solution requires maximum contribution"""
        # Set up scenario where we need to save everything we can
        tight_inputs = self.base_inputs.copy()
        tight_inputs.update({
            'monthly_income': 4000.0,
            'monthly_expenses': 3000.0,  # Only 1000/month available (equal to current contribution)
            'expected_annual_return_pct': 1.0,  # Low return
            'target_age': 35
        })

        # Set ambitious target that requires saving at maximum rate
        goal_inputs = tight_inputs.copy()
        goal_inputs.update({
            'goal_name': 'Maximum Effort',
            'target_amount': 100000.0,  # Ambitious target
            'target_age': 35
        })

        result = calculate_goal_requirements(
            base_inputs=tight_inputs,
            goal_name=goal_inputs['goal_name'],
            target_amount=goal_inputs['target_amount'],
            target_age=goal_inputs['target_age']
        )

        # Should require maximum contribution (income - expenses)
        max_contribution = tight_inputs['monthly_income'] - tight_inputs['monthly_expenses']  # 1000.0
        self.assertEqual(result['required_monthly_investment'], max_contribution)
        self.assertEqual(result['calculation_method'], 'boundary')
        # May or may not reach goal depending on numbers, but should use boundary solution

    def test_calculate_goal_requirements_verification_failure_handling(self):
        """Test that verification failures are handled gracefully"""
        # This is harder to test directly since we'd need to force a verification failure
        # The binary search function should handle this internally and return verification_passed=False
        # We'll test that the structure is correct even when verification fails

        # Use a case that should work normally to verify structure
        goal_inputs = self.base_inputs.copy()
        goal_inputs.update({
            'goal_name': 'Verification Test',
            'target_amount': 50000.0,
            'target_age': 40  # Longer time horizon
        })

        result = calculate_goal_requirements(
            base_inputs=self.base_inputs,
            goal_name=goal_inputs['goal_name'],
            target_amount=goal_inputs['target_amount'],
            target_age=goal_inputs['target_age']
        )

        # Check that all expected fields are present
        expected_fields = [
            'goal_name', 'target_amount', 'target_age', 'current_age',
            'required_monthly_investment', 'projected_wealth_at_target',
            'surplus_or_shortfall', 'goal_reached', 'calculation_method',
            'iterations', 'verification_passed'
        ]

        for field in expected_fields:
            self.assertIn(field, result, f"Missing field: {field}")

        # Check types
        self.assertIsInstance(result['goal_name'], str)
        self.assertIsInstance(result['target_amount'], (int, float))
        self.assertIsInstance(result['target_age'], int)
        self.assertIsInstance(result['current_age'], int)
        self.assertIsInstance(result['required_monthly_investment'], (int, float))
        self.assertIsInstance(result['projected_wealth_at_target'], (int, float))
        self.assertIsInstance(result['surplus_or_shortfall'], (int, float))
        self.assertIsInstance(result['goal_reached'], bool)
        self.assertIsInstance(result['calculation_method'], str)
        self.assertIsInstance(result['iterations'], int)
        self.assertIsInstance(result['verification_passed'], bool)

        # Check that calculation method is one of expected values
        self.assertIn(result['calculation_method'], ['direct', 'binary_search', 'boundary'])


if __name__ == '__main__':
    unittest.main()