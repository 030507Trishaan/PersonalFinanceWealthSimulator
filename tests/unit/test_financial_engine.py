"""
Unit tests for the financial calculation engine
Tests all aspects of the financial engine as specified in the test plan
"""

import unittest
import sys
import os

# Add the financial_engine directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from financial_engine.core.calculations import validate_inputs, calculate_projection


class TestFinancialEngine(unittest.TestCase):

    def setUp(self):
        """Set up test inputs"""
        self.valid_inputs = {
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

    # === 1. Input Validation Tests ===

    def test_negative_age_values(self):
        """Test negative age values are rejected"""
        inputs = self.valid_inputs.copy()
        inputs['current_age'] = -5
        with self.assertRaises(ValueError):
            validate_inputs(inputs)

        inputs['current_age'] = 30
        inputs['target_age'] = -10
        with self.assertRaises(ValueError):
            validate_inputs(inputs)

    def test_target_age_less_than_or_equal_current_age(self):
        """Test target age <= current age is rejected"""
        inputs = self.valid_inputs.copy()
        inputs['target_age'] = 30  # Equal to current age
        with self.assertRaises(ValueError):
            validate_inputs(inputs)

        inputs['target_age'] = 25  # Less than current age
        with self.assertRaises(ValueError):
            validate_inputs(inputs)

    def test_negative_monetary_values(self):
        """Test negative monetary values are rejected"""
        monetary_fields = ['current_savings', 'monthly_income', 'monthly_expenses',
                          'monthly_investment_contribution']

        for field in monetary_fields:
            inputs = self.valid_inputs.copy()
            inputs[field] = -100.0
            with self.assertRaises(ValueError):
                validate_inputs(inputs)

    def test_negative_percentage_values(self):
        """Test negative percentage values are rejected"""
        percentage_fields = ['annual_income_growth_pct', 'annual_expense_growth_pct',
                           'expected_annual_return_pct', 'annual_inflation_pct']

        for field in percentage_fields:
            inputs = self.valid_inputs.copy()
            inputs[field] = -5.0
            with self.assertRaises(ValueError):
                validate_inputs(inputs)

    def test_monthly_investment_exceeding_available_savings(self):
        """Test monthly investment contribution exceeding available savings is rejected"""
        inputs = self.valid_inputs.copy()
        # Available savings = monthly_income - monthly_expenses = 5000 - 3000 = 2000
        # Monthly investment contribution = 3000 (exceeds available savings)
        inputs['monthly_investment_contribution'] = 3000.0
        with self.assertRaises(ValueError):
            validate_inputs(inputs)

    def test_non_integer_ages(self):
        """Test non-integer ages are rejected"""
        inputs = self.valid_inputs.copy()
        inputs['current_age'] = 30.5
        with self.assertRaises(TypeError):
            validate_inputs(inputs)

        inputs['current_age'] = 30
        inputs['target_age'] = 35.5
        with self.assertRaises(TypeError):
            validate_inputs(inputs)

    def test_non_numeric_inputs(self):
        """Test non-numeric inputs where numbers expected are rejected"""
        # Test monetary fields
        monetary_fields = ['current_savings', 'monthly_income', 'monthly_expenses',
                          'monthly_investment_contribution']

        for field in monetary_fields:
            inputs = self.valid_inputs.copy()
            inputs[field] = "not_a_number"
            with self.assertRaises(TypeError):
                validate_inputs(inputs)

        # Test percentage fields
        percentage_fields = ['annual_income_growth_pct', 'annual_expense_growth_pct',
                           'expected_annual_return_pct', 'annual_inflation_pct']

        for field in percentage_fields:
            inputs = self.valid_inputs.copy()
            inputs[field] = "not_a_number"
            with self.assertRaises(TypeError):
                validate_inputs(inputs)

    # === 2. Boundary Condition Tests ===

    def test_current_age_equals_target_age_minus_one_single_year(self):
        """Test current age equals target age - 1 (single year projection)"""
        inputs = self.valid_inputs.copy()
        inputs['target_age'] = 31  # current_age=30, target_age=31 -> 1 year
        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)
        self.assertEqual(len(projection), 1)  # Should produce exactly 1 year
        self.assertEqual(projection[0]['age'], 31)  # Age at end of year

    def test_zero_values_for_all_growth_rates_and_returns(self):
        """Test zero values for all growth rates and returns"""
        inputs = self.valid_inputs.copy()
        inputs['annual_income_growth_pct'] = 0.0
        inputs['annual_expense_growth_pct'] = 0.0
        inputs['expected_annual_return_pct'] = 0.0
        inputs['annual_inflation_pct'] = 0.0

        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        # With zero growth, values should be constant each year
        first_year = projection[0]
        last_year = projection[-1]

        # Annual income, expenses, savings should be constant
        self.assertAlmostEqual(first_year['annual_income'], last_year['annual_income'], places=2)
        self.assertAlmostEqual(first_year['annual_expenses'], last_year['annual_expenses'], places=2)
        self.assertAlmostEqual(first_year['annual_savings'], last_year['annual_savings'], places=2)

        # Investment returns should be zero each year
        for year in projection:
            self.assertAlmostEqual(year['investment_returns'], 0.0, places=2)

    def test_zero_inflation_rate(self):
        """Test zero inflation rate"""
        inputs = self.valid_inputs.copy()
        inputs['annual_inflation_pct'] = 0.0
        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        # With zero inflation, nominal and real wealth should be equal
        for year in projection:
            self.assertAlmostEqual(year['ending_nominal_wealth'], year['inflation_adjusted_wealth'], places=2)

    def test_zero_investment_returns(self):
        """Test zero investment returns"""
        inputs = self.valid_inputs.copy()
        inputs['expected_annual_return_pct'] = 0.0
        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        # Investment returns should be zero
        for year in projection:
            self.assertAlmostEqual(year['investment_returns'], 0.0, places=2)

    def test_zero_income_and_expenses(self):
        """Test zero income and expenses"""
        inputs = self.valid_inputs.copy()
        inputs['monthly_income'] = 0.0
        inputs['monthly_expenses'] = 0.0
        # With zero income and expenses, available savings is 0, so investment contribution must be 0
        inputs['monthly_investment_contribution'] = 0.0
        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        for year in projection:
            self.assertAlmostEqual(year['annual_income'], 0.0, places=2)
            self.assertAlmostEqual(year['annual_expenses'], 0.0, places=2)
            self.assertAlmostEqual(year['annual_savings'], 0.0, places=2)

    def test_very_small_decimal_values(self):
        """Test very small decimal values"""
        inputs = self.valid_inputs.copy()
        inputs['current_savings'] = 0.01
        inputs['monthly_income'] = 0.01
        inputs['monthly_expenses'] = 0.005
        inputs['monthly_investment_contribution'] = 0.004
        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        # Should not crash and should produce reasonable results
        self.assertGreater(len(projection), 0)
        self.assertGreaterEqual(projection[0]['ending_nominal_wealth'], 0)

    def test_very_large_numbers_within_reason(self):
        """Test very large numbers (within reason)"""
        inputs = self.valid_inputs.copy()
        inputs['current_savings'] = 1000000.0  # 1 million
        inputs['monthly_income'] = 50000.0     # 50k/month
        inputs['monthly_expenses'] = 20000.0   # 20k/month
        inputs['monthly_investment_contribution'] = 15000.0  # 15k/month
        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        # Should not crash and should produce reasonable results
        self.assertGreater(len(projection), 0)
        self.assertGreater(projection[-1]['ending_nominal_wealth'], projection[0]['ending_nominal_wealth'])

    # === 3. Calculation Accuracy Tests ===

    def test_known_manual_calculations_for_simple_scenarios(self):
        """Test known manual calculations for simple scenarios"""
        # Simple scenario: 1 year, no growth, 5% return, 2% inflation
        inputs = {
            'current_age': 30,
            'target_age': 31,  # 1 year projection
            'current_savings': 10000.0,
            'monthly_income': 5000.0,
            'monthly_expenses': 3000.0,
            'monthly_investment_contribution': 1000.0,
            'annual_income_growth_pct': 0.0,
            'annual_expense_growth_pct': 0.0,
            'expected_annual_return_pct': 5.0,
            'annual_inflation_pct': 2.0
        }

        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        self.assertEqual(len(projection), 1)
        year = projection[0]

        # Manual calculations:
        # Annual income = 5000 * 12 = 60000
        # Annual expenses = 3000 * 12 = 36000
        # Annual savings = 60000 - 36000 = 24000
        # Annual investment contribution = 1000 * 12 = 12000
        # Uninvested cash savings = 24000 - 12000 = 12000
        # Investment return = (10000 + 12000) * 0.05 = 1100
        # Ending invested wealth = 10000 + 12000 + 1100 = 23100
        # Ending cash wealth = 0 + 12000 = 12000
        # Ending nominal wealth = 23100 + 12000 = 35100
        # Inflation factor = (1 + 0.02)^0 = 1.0 (year 0)
        # Inflation-adjusted wealth = 35100 / 1.0 = 35100

        self.assertAlmostEqual(year['annual_income'], 60000.0, places=2)
        self.assertAlmostEqual(year['annual_expenses'], 36000.0, places=2)
        self.assertAlmostEqual(year['annual_savings'], 24000.0, places=2)
        self.assertAlmostEqual(year['annual_investment_contribution'], 12000.0, places=2)
        self.assertAlmostEqual(year['uninvested_cash_savings'], 12000.0, places=2)
        self.assertAlmostEqual(year['investment_returns'], 1100.0, places=2)
        self.assertAlmostEqual(year['ending_invested_wealth'], 23100.0, places=2)
        self.assertAlmostEqual(year['ending_cash_wealth'], 12000.0, places=2)
        self.assertAlmostEqual(year['ending_nominal_wealth'], 35100.0, places=2)
        self.assertAlmostEqual(year['inflation_adjusted_wealth'], 35100.0, places=2)

    def test_zero_growth_scenario_verification(self):
        """Test zero growth scenario verification"""
        inputs = self.valid_inputs.copy()
        inputs['annual_income_growth_pct'] = 0.0
        inputs['annual_expense_growth_pct'] = 0.0
        inputs['expected_annual_return_pct'] = 0.0
        inputs['annual_inflation_pct'] = 0.0

        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        # With zero growth and zero returns, wealth should increase linearly by annual savings each year
        annual_savings = (5000 - 3000) * 12  # 24000

        for i, year in enumerate(projection):
            expected_wealth = 10000 + (i + 1) * annual_savings  # Starting savings + years * annual savings
            self.assertAlmostEqual(year['ending_nominal_wealth'], expected_wealth, places=2)
            self.assertAlmostEqual(year['inflation_adjusted_wealth'], expected_wealth, places=2)  # 0% inflation

    def test_constant_growth_scenario_verification(self):
        """Test constant growth scenario verification"""
        # Test with constant income growth
        inputs = self.valid_inputs.copy()
        inputs['annual_income_growth_pct'] = 10.0  # 10% income growth
        inputs['annual_expense_growth_pct'] = 0.0   # No expense growth
        inputs['expected_annual_return_pct'] = 0.0  # No returns to isolate income effect
        inputs['annual_inflation_pct'] = 0.0        # No inflation

        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        # Income should grow by 10% each year
        base_income = 5000 * 12  # 60000

        for i, year in enumerate(projection):
            expected_income = base_income * (1.10 ** i)  # Compound growth
            self.assertAlmostEqual(year['annual_income'], expected_income, places=2)

    def test_relationship_between_nominal_and_real_wealth(self):
        """Test relationship between nominal and real wealth"""
        inputs = self.valid_inputs.copy()
        # Use positive inflation to test the relationship
        inputs['annual_inflation_pct'] = 3.0

        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        # Real wealth should be less than or equal to nominal wealth when inflation > 0
        for year in projection:
            self.assertLessEqual(year['inflation_adjusted_wealth'], year['ending_nominal_wealth'] + 0.01)  # Allow small floating point difference

    def test_cumulative_sums_verification(self):
        """Test cumulative sums verification"""
        inputs = self.valid_inputs.copy()
        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        # Calculate expected cumulative values
        expected_contributions = 0.0
        expected_returns = 0.0

        for year in projection:
            expected_contributions += year['annual_investment_contribution']
            expected_returns += year['investment_returns']

            # Check that cumulative values match
            self.assertAlmostEqual(year['cumulative_contributions'], expected_contributions, places=2)
            self.assertAlmostEqual(year['cumulative_investment_returns'], expected_returns, places=2)

    # === 4. Consistency Tests ===

    def test_starting_wealth_correctly_set_to_current_savings(self):
        """Test starting wealth correctly set to current_savings (all treated as invested)"""
        inputs = self.valid_inputs.copy()
        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        # First year starting invested wealth should equal current_savings
        self.assertAlmostEqual(projection[0]['starting_invested_wealth'], 10000.0, places=2)
        # First year starting cash wealth should be 0
        self.assertAlmostEqual(projection[0]['starting_cash_wealth'], 0.0, places=2)

    def test_each_year_starting_wealth_equals_previous_year_ending_wealth(self):
        """Test each year's starting wealth equals previous year's ending wealth"""
        inputs = self.valid_inputs.copy()
        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        for i in range(1, len(projection)):
            prev_year = projection[i-1]
            curr_year = projection[i]

            # Starting invested wealth should equal previous year's ending invested wealth
            self.assertAlmostEqual(curr_year['starting_invested_wealth'], prev_year['ending_invested_wealth'], places=2)
            # Starting cash wealth should equal previous year's ending cash wealth
            self.assertAlmostEqual(curr_year['starting_cash_wealth'], prev_year['ending_cash_wealth'], places=2)

    def test_inflation_adjusted_wealth_less_than_nominal_when_inflation_gt_0(self):
        """Test inflation-adjusted wealth <= nominal wealth when inflation > 0"""
        inputs = self.valid_inputs.copy()
        inputs['annual_inflation_pct'] = 3.0  # Positive inflation

        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        for year in projection:
            # Real wealth should be less than nominal wealth when inflation > 0
            self.assertLessEqual(year['inflation_adjusted_wealth'], year['ending_nominal_wealth'] + 0.01)

    def test_cumulative_contributions_equal_sum_of_annual_investment_contributions(self):
        """Test cumulative contributions = sum of annual investment contributions"""
        inputs = self.valid_inputs.copy()
        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        total_contributions = sum(year['annual_investment_contribution'] for year in projection)
        final_cumulative = projection[-1]['cumulative_contributions']

        self.assertAlmostEqual(total_contributions, final_cumulative, places=2)

    def test_cumulative_investment_returns_equal_sum_of_annual_investment_returns(self):
        """Test cumulative investment returns = sum of annual investment returns"""
        inputs = self.valid_inputs.copy()
        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        total_returns = sum(year['investment_returns'] for year in projection)
        final_cumulative = projection[-1]['cumulative_investment_returns']

        self.assertAlmostEqual(total_returns, final_cumulative, places=2)

    def test_annual_savings_equals_investment_contribution_plus_uninvested_cash_savings(self):
        """Test annual savings = annual investment contribution + uninvested cash savings"""
        inputs = self.valid_inputs.copy()
        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        for year in projection:
            expected_savings = year['annual_investment_contribution'] + year['uninvested_cash_savings']
            self.assertAlmostEqual(year['annual_savings'], expected_savings, places=2)

    def test_investment_returns_equals_starting_invested_wealth_plus_contribution_times_return_rate(self):
        """Test investment returns = (starting invested wealth + annual investment contribution) * return rate"""
        inputs = self.valid_inputs.copy()
        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        return_rate = 0.05  # 5% from test inputs

        for year in projection:
            expected_return = (year['starting_invested_wealth'] + year['annual_investment_contribution']) * return_rate
            self.assertAlmostEqual(year['investment_returns'], expected_return, places=2)

    # === Additional Edge Case Tests ===

    def test_single_year_projection_age_30_to_31(self):
        """Test specific case: current_age=30, target_age=31 (1 year)"""
        inputs = self.valid_inputs.copy()
        inputs['target_age'] = 31
        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        self.assertEqual(len(projection), 1)
        self.assertEqual(projection[0]['age'], 31)  # End of year age
        self.assertEqual(projection[0]['starting_invested_wealth'], 10000.0)
        self.assertEqual(projection[0]['starting_cash_wealth'], 0.0)

    def test_maximum_valid_contribution(self):
        """Test maximum valid contribution (when investment contribution = income - expenses)"""
        inputs = self.valid_inputs.copy()
        # Maximum valid contribution = monthly_income - monthly_expenses = 5000 - 3000 = 2000
        inputs['monthly_investment_contribution'] = 2000.0
        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        # With maximum contribution, uninvested cash savings should be zero
        for year in projection:
            self.assertAlmostEqual(year['uninvested_cash_savings'], 0.0, places=2)
            # All savings go to investments
            self.assertAlmostEqual(year['annual_savings'], year['annual_investment_contribution'], places=2)

    def test_zero_contribution(self):
        """Test zero investment contribution"""
        inputs = self.valid_inputs.copy()
        inputs['monthly_investment_contribution'] = 0.0
        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        # With zero contribution, all savings should go to cash
        for year in projection:
            self.assertAlmostEqual(year['annual_investment_contribution'], 0.0, places=2)
            self.assertAlmostEqual(year['uninvested_cash_savings'], year['annual_savings'], places=2)
            # Investment returns should only be on starting wealth (no new contributions)
            expected_return = year['starting_invested_wealth'] * 0.05  # 5% return
            self.assertAlmostEqual(year['investment_returns'], expected_return, places=2)

    def test_high_inflation_scenario(self):
        """Test high inflation scenario"""
        inputs = self.valid_inputs.copy()
        inputs['annual_inflation_pct'] = 10.0  # 10% inflation
        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        # Real wealth should be less than or equal to nominal wealth when inflation > 0
        # (equal only in first year when years_elapsed=0)
        for i, year in enumerate(projection):
            if i == 0:  # First year: years_elapsed = 0, so inflation factor = 1.0
                self.assertAlmostEqual(year['inflation_adjusted_wealth'], year['ending_nominal_wealth'], places=2)
            else:  # Subsequent years: real wealth should be less than nominal wealth
                self.assertLess(year['inflation_adjusted_wealth'], year['ending_nominal_wealth'])

    def test_high_return_scenario(self):
        """Test high investment return scenario"""
        inputs = self.valid_inputs.copy()
        inputs['expected_annual_return_pct'] = 15.0  # 15% return
        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        # Returns should be substantial
        for year in projection:
            self.assertGreater(year['investment_returns'], 0)
            # Returns should grow over time as invested wealth grows

    def test_extreme_but_valid_values(self):
        """Test extreme but valid values"""
        inputs = self.valid_inputs.copy()
        inputs['current_savings'] = 1000000.0  # 1M savings
        inputs['monthly_income'] = 100000.0    # 100k/month income
        inputs['monthly_expenses'] = 50000.0   # 50k/month expenses
        inputs['monthly_investment_contribution'] = 40000.0  # 40k/month investment (max valid)
        inputs['annual_income_growth_pct'] = 5.0   # 5% income growth
        inputs['annual_expense_growth_pct'] = 3.0   # 3% expense growth
        inputs['expected_annual_return_pct'] = 10.0  # 10% return
        inputs['annual_inflation_pct'] = 4.0         # 4% inflation

        validated = validate_inputs(inputs)
        projection = calculate_projection(validated)

        # Should not crash and should produce reasonable results
        self.assertGreater(len(projection), 0)
        self.assertGreater(projection[-1]['ending_nominal_wealth'], projection[0]['ending_nominal_wealth'])

        # Verify no double-counting still holds
        for year in projection:
            self.assertAlmostEqual(
                year['annual_savings'],
                year['annual_investment_contribution'] + year['uninvested_cash_savings'],
                places=2
            )
            self.assertAlmostEqual(
                year['ending_nominal_wealth'],
                year['ending_invested_wealth'] + year['ending_cash_wealth'],
                places=2
            )


if __name__ == '__main__':
    unittest.main()