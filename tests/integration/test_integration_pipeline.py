"""
Integration tests for the complete pipeline:
User inputs → validation → financial engine → projection output → UI data preparation
"""

import unittest
import sys
import os

# Add project directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'financial_engine', 'core'))

from financial_engine.core.calculations import validate_inputs, calculate_projection


class TestIntegrationPipeline(unittest.TestCase):
    """Test the complete integration pipeline"""

    def setUp(self):
        """Set up test inputs for a known scenario"""
        self.test_inputs = {
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

    def test_complete_pipeline_with_known_inputs(self):
        """Test the complete pipeline with known inputs and expected outputs"""

        # Step 1: Validate inputs
        validated_inputs = validate_inputs(self.test_inputs)

        # Verify validation preserved all inputs correctly
        for key, value in self.test_inputs.items():
            self.assertEqual(validated_inputs[key], value, f"Validation failed for {key}")

        # Step 2: Calculate projection
        projection = calculate_projection(validated_inputs)

        # Step 3: Verify projection output characteristics

        # Assertion: correct number of projection years
        expected_years = self.test_inputs['target_age'] - self.test_inputs['current_age']
        self.assertEqual(len(projection), expected_years,
                        f"Expected {expected_years} years, got {len(projection)}")

        # Assertion: correct first and last ages
        self.assertEqual(projection[0]['age'], self.test_inputs['current_age'] + 1,
                        f"First year age should be {self.test_inputs['current_age'] + 1}")
        self.assertEqual(projection[-1]['age'], self.test_inputs['target_age'],
                        f"Last year age should be {self.test_inputs['target_age']}")

        # Assertion: invested + cash = total nominal wealth (for all years)
        for year in projection:
            total_wealth = year['ending_invested_wealth'] + year['ending_cash_wealth']
            self.assertAlmostEqual(total_wealth, year['ending_nominal_wealth'], places=2,
                                 msg=f"Wealth accounting failed in year {year['age']}")

        # Assertion: annual savings = investment contribution + uninvested cash savings
        for year in projection:
            expected_savings = year['annual_investment_contribution'] + year['uninvested_cash_savings']
            self.assertAlmostEqual(year['annual_savings'], expected_savings, places=2,
                                 msg=f"Savings accounting failed in year {year['age']}")

        # Assertion: cumulative contributions and returns
        total_contributions = sum(year['annual_investment_contribution'] for year in projection)
        total_returns = sum(year['investment_returns'] for year in projection)

        self.assertAlmostEqual(projection[-1]['cumulative_contributions'], total_contributions, places=2)
        self.assertAlmostEqual(projection[-1]['cumulative_investment_returns'], total_returns, places=2)

        # Assertion: nominal vs inflation-adjusted wealth relationship
        for year in projection:
            # With positive inflation, real wealth should be <= nominal wealth
            self.assertLessEqual(year['inflation_adjusted_wealth'], year['ending_nominal_wealth'] + 0.01,
                               msg=f"Real wealth > nominal wealth in year {year['age']}")

        # Assertion: UI-facing projection data has required fields
        required_fields = [
            'age', 'starting_invested_wealth', 'starting_cash_wealth',
            'annual_income', 'annual_expenses', 'annual_savings',
            'annual_investment_contribution', 'uninvested_cash_savings',
            'investment_returns', 'ending_invested_wealth', 'ending_cash_wealth',
            'ending_nominal_wealth', 'inflation_adjusted_wealth',
            'cumulative_contributions', 'cumulative_investment_returns'
        ]

        for year in projection:
            for field in required_fields:
                self.assertIn(field, year, f"Missing field '{field}' in projection data for year {year['age']}")
                self.assertIsInstance(year[field], (int, float),
                                    f"Field '{field}' is not numeric in year {year['age']}")

    def test_pipeline_with_zero_growth_scenario(self):
        """Test pipeline with zero growth rates (known manual calculation scenario)"""

        # Modify inputs for zero growth scenario
        zero_growth_inputs = self.test_inputs.copy()
        zero_growth_inputs['annual_income_growth_pct'] = 0.0
        zero_growth_inputs['annual_expense_growth_pct'] = 0.0
        zero_growth_inputs['expected_annual_return_pct'] = 0.0
        zero_growth_inputs['annual_inflation_pct'] = 0.0

        # Step 1: Validate inputs
        validated_inputs = validate_inputs(zero_growth_inputs)

        # Step 2: Calculate projection
        projection = calculate_projection(validated_inputs)

        # With zero growth and zero returns:
        # - Annual income, expenses, savings constant each year
        # - Investment returns = 0 each year
        # - Wealth increases linearly by annual savings each year

        expected_annual_savings = (5000 - 3000) * 12  # 24000

        for i, year in enumerate(projection):
            # Check annual values are constant
            self.assertAlmostEqual(year['annual_income'], 5000 * 12, places=2)
            self.assertAlmostEqual(year['annual_expenses'], 3000 * 12, places=2)
            self.assertAlmostEqual(year['annual_savings'], expected_annual_savings, places=2)

            # Check investment returns are zero
            self.assertAlmostEqual(year['investment_returns'], 0.0, places=2)

            # Check wealth increases linearly
            expected_wealth = 10000 + (i + 1) * expected_annual_savings
            self.assertAlmostEqual(year['ending_nominal_wealth'], expected_wealth, places=2)

            # With zero inflation, nominal = real
            self.assertAlmostEqual(year['inflation_adjusted_wealth'], year['ending_nominal_wealth'], places=2)

            # Check accounting identities
            total_wealth = year['ending_invested_wealth'] + year['ending_cash_wealth']
            self.assertAlmostEqual(total_wealth, year['ending_nominal_wealth'], places=2)

            expected_savings = year['annual_investment_contribution'] + year['uninvested_cash_savings']
            self.assertAlmostEqual(year['annual_savings'], expected_savings, places=2)

    def test_pipeline_maximum_valid_contribution(self):
        """Test pipeline with maximum valid investment contribution"""

        # Set investment contribution to maximum valid value (income - expenses)
        max_contrib_inputs = self.test_inputs.copy()
        max_contrib_inputs['monthly_investment_contribution'] = 2000.0  # 5000 - 3000 = 2000

        # Step 1: Validate inputs (should not raise exception)
        validated_inputs = validate_inputs(max_contrib_inputs)
        self.assertEqual(validated_inputs['monthly_investment_contribution'], 2000.0)

        # Step 2: Calculate projection
        projection = calculate_projection(validated_inputs)

        # With maximum contribution, uninvested cash savings should be zero
        for year in projection:
            self.assertAlmostEqual(year['uninvested_cash_savings'], 0.0, places=2,
                                 msg=f"Uninvested cash savings should be zero with max contribution in year {year['age']}")
            # All savings should go to investments
            self.assertAlmostEqual(year['annual_savings'], year['annual_investment_contribution'], places=2,
                                 msg=f"All savings should go to investments in year {year['age']}")

    def test_pipeline_zero_contribution(self):
        """Test pipeline with zero investment contribution"""

        # Set investment contribution to zero
        zero_contrib_inputs = self.test_inputs.copy()
        zero_contrib_inputs['monthly_investment_contribution'] = 0.0

        # Step 1: Validate inputs (should not raise exception)
        validated_inputs = validate_inputs(zero_contrib_inputs)
        self.assertEqual(validated_inputs['monthly_investment_contribution'], 0.0)

        # Step 2: Calculate projection
        projection = calculate_projection(validated_inputs)

        # With zero contribution, all savings should go to cash
        for year in projection:
            self.assertAlmostEqual(year['annual_investment_contribution'], 0.0, places=2,
                                 msg=f"Investment contribution should be zero in year {year['age']}")
            # All savings should go to cash (since investment contribution is zero)
            self.assertAlmostEqual(year['uninvested_cash_savings'], year['annual_savings'], places=2,
                                 msg=f"All savings should go to cash in year {year['age']}")
            # Investment returns should only be on starting wealth (no new contributions)
            expected_return = year['starting_invested_wealth'] * 0.05  # 5% return
            self.assertAlmostEqual(year['investment_returns'], expected_return, places=2,
                                 msg=f"Investment returns should be on starting wealth only in year {year['age']}")

    def test_ui_data_preparation_compatibility(self):
        """Test that projection output is compatible with UI data preparation"""

        # Get projection from financial engine
        validated_inputs = validate_inputs(self.test_inputs)
        projection = calculate_projection(validated_inputs)

        # Simulate UI data preparation (from ui/app.py)
        # Format the dataframe for display
        import pandas as pd
        display_df = pd.DataFrame(projection)

        # Format currency columns (as done in UI)
        currency_columns = [
            'starting_invested_wealth', 'starting_cash_wealth',
            'annual_income', 'annual_expenses', 'annual_savings',
            'annual_investment_contribution', 'uninvested_cash_savings',
            'investment_returns', 'ending_invested_wealth', 'ending_cash_wealth',
            'ending_nominal_wealth', 'inflation_adjusted_wealth',
            'cumulative_contributions', 'cumulative_investment_returns'
        ]

        # Verify all currency columns exist and are numeric
        for col in currency_columns:
            self.assertIn(col, display_df.columns, f"Missing currency column '{col}'")
            # Verify all values are numeric (can be formatted)
            for value in display_df[col]:
                self.assertIsInstance(value, (int, float),
                                    f"Non-numeric value in column '{col}': {value}")

        # Verify we can create the display strings (as done in UI)
        for col in currency_columns:
            formatted_col = display_df[col].apply(lambda x: f"${x:,.2f}")
            # Verify all formatted values are strings starting with $
            for formatted_value in formatted_col:
                self.assertIsInstance(formatted_value, str)
                self.assertTrue(formatted_value.startswith('$'),
                              f"Formatted value doesn't start with $: {formatted_value}")


if __name__ == '__main__':
    unittest.main()