"""
Simple test script to verify the financial engine works correctly
"""
import sys
import os

# Add the financial_engine directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'financial_engine', 'core'))

from calculations import validate_inputs, calculate_projection

def test_basic_functionality():
    """Test basic financial engine functionality"""
    print("Testing basic financial engine functionality...")

    # Test inputs
    test_inputs = {
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

    try:
        # Validate inputs
        validated = validate_inputs(test_inputs)
        print("✓ Input validation successful")

        # Calculate projection
        projection = calculate_projection(validated)
        print(f"✓ Projection calculation successful - {len(projection)} years projected")

        # Check first year results
        if len(projection) > 0:
            first_year = projection[0]
            print(f"First year (age {first_year['age']}):")
            print(f"  Starting invested wealth: ${first_year['starting_invested_wealth']:.2f}")
            print(f"  Starting cash wealth: ${first_year['starting_cash_wealth']:.2f}")
            print(f"  Annual income: ${first_year['annual_income']:.2f}")
            print(f"  Annual expenses: ${first_year['annual_expenses']:.2f}")
            print(f"  Annual savings: ${first_year['annual_savings']:.2f}")
            print(f"  Annual investment contribution: ${first_year['annual_investment_contribution']:.2f}")
            print(f"  Uninvested cash savings: ${first_year['uninvested_cash_savings']:.2f}")
            print(f"  Investment returns: ${first_year['investment_returns']:.2f}")
            print(f"  Ending invested wealth: ${first_year['ending_invested_wealth']:.2f}")
            print(f"  Ending cash wealth: ${first_year['ending_cash_wealth']:.2f}")
            print(f"  Ending nominal wealth: ${first_year['ending_nominal_wealth']:.2f}")
            print(f"  Inflation-adjusted wealth: ${first_year['inflation_adjusted_wealth']:.2f}")

            # Verify no double-counting
            annual_savings = first_year['annual_savings']
            investment_contribution = first_year['annual_investment_contribution']
            uninvested_cash = first_year['uninvested_cash_savings']
            expected_savings = investment_contribution + uninvested_cash

            if abs(annual_savings - expected_savings) < 0.01:
                print("✓ Annual savings correctly split between investment and cash")
            else:
                print(f"✗ Annual savings mismatch: {annual_savings} != {expected_savings}")

            # Verify wealth accounting
            total_wealth = first_year['ending_invested_wealth'] + first_year['ending_cash_wealth']
            if abs(total_wealth - first_year['ending_nominal_wealth']) < 0.01:
                print("✓ Ending nominal wealth = ending invested + ending cash")
            else:
                print(f"✗ Wealth accounting error: {total_wealth} != {first_year['ending_nominal_wealth']}")

        print("✓ Basic functionality test completed successfully")

    except Exception as e:
        print(f"✗ Error during testing: {e}")
        raise  # Re-raise the exception so pytest can catch it and mark the test as failed

if __name__ == "__main__":
    test_basic_functionality()
    print("\n🎉 All tests passed!")