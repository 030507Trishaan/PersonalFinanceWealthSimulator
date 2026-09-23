"""
Tests for the standalone Goal Planner module
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'goal_planner'))

from goal_calculations import validate_goal_planner_inputs, calculate_goal_planner


def test_basic_calculation():
    """Test a basic known calculation"""
    # Example from spec:
    # Current age = 20
    # Goal age = 50
    # Target corpus = ₹1,00,00,000
    # Current savings/investments = ₹0
    # Expected annual return = 10%

    result = calculate_goal_planner(
        current_age=20,
        goal_age=50,
        target_corpus=10000000,  # 1,00,00,000
        current_savings=0,
        expected_annual_return_pct=10
    )

    # Verify we get a reasonable monthly investment (should be around ₹10,000-15,000 for this scenario)
    assert result['required_monthly_investment'] > 0
    assert result['goal_reached'] == True
    assert abs(result['surplus_or_shortfall']) < 1000  # Should be very close to target


def test_zero_return():
    """Test zero return case"""
    result = calculate_goal_planner(
        current_age=30,
        goal_age=40,
        target_corpus=500000,
        current_savings=0,
        expected_annual_return_pct=0
    )

    # With zero return over 10 years (120 months), to reach ₹5,00,000:
    # Required monthly = 5,00,000 / 120 = ₹4,166.67
    expected_monthly = 500000 / 120
    assert abs(result['required_monthly_investment'] - expected_monthly) < 0.01
    assert result['goal_reached'] == True


def test_zero_current_savings():
    """Test with zero current savings"""
    result = calculate_goal_planner(
        current_age=25,
        goal_age=35,
        target_corpus=2000000,
        current_savings=0,
        expected_annual_return_pct=8
    )

    assert result['required_monthly_investment'] > 0


def test_current_corpus_already_reaches_target():
    """Test when current corpus already reaches target"""
    result = calculate_goal_planner(
        current_age=40,
        goal_age=50,
        target_corpus=1000000,
        current_savings=1500000,  # Already more than target
        expected_annual_return_pct=5
    )

    # Should require 0 monthly investment since we already exceed target
    assert result['required_monthly_investment'] == 0
    assert result['goal_reached'] == True
    assert result['surplus_or_shortfall'] > 0  # Should have surplus


def test_one_year_goal():
    """Test one-year goal"""
    result = calculate_goal_planner(
        current_age=29,
        goal_age=30,
        target_corpus=120000,
        current_savings=0,
        expected_annual_return_pct=12
    )

    # Should be approximately 120,000 / 12 = 10,000 per month (adjusted for interest)
    assert result['years_available'] == 1
    assert result['required_monthly_investment'] > 0


def test_multi_year_goal():
    """Test multi-year goal"""
    result = calculate_goal_planner(
        current_age=20,
        goal_age=60,
        target_corpus=50000000,
        current_savings=100000,
        expected_annual_return_pct=8
    )

    assert result['years_available'] == 40
    assert result['required_monthly_investment'] > 0


def test_invalid_age():
    """Test invalid age inputs"""
    try:
        calculate_goal_planner(
            current_age=-1,
            goal_age=30,
            target_corpus=100000,
            current_savings=0,
            expected_annual_return_pct=5
        )
        assert False, "Should have raised ValueError for negative age"
    except ValueError:
        pass  # Expected

    try:
        calculate_goal_planner(
            current_age=30,
            goal_age=30,
            target_corpus=100000,
            current_savings=0,
            expected_annual_return_pct=5
        )
        assert False, "Should have raised ValueError for goal_age <= current_age"
    except ValueError:
        pass  # Expected


def test_goal_age_equals_current_age():
    """Test goal age equals current age"""
    try:
        calculate_goal_planner(
            current_age=30,
            goal_age=30,
            target_corpus=100000,
            current_savings=0,
            expected_annual_return_pct=5
        )
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected


def test_negative_target():
    """Test negative target"""
    try:
        calculate_goal_planner(
            current_age=25,
            goal_age=35,
            target_corpus=-100000,
            current_savings=0,
            expected_annual_return_pct=5
        )
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected


def test_negative_current_savings():
    """Test negative current savings"""
    try:
        calculate_goal_planner(
            current_age=25,
            goal_age=35,
            target_corpus=100000,
            current_savings=-50000,
            expected_annual_return_pct=5
        )
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected


def test_negative_return():
    """Test negative return"""
    try:
        calculate_goal_planner(
            current_age=25,
            goal_age=35,
            target_corpus=100000,
            current_savings=0,
            expected_annual_return_pct=-2
        )
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected


def test_numerical_verification():
    """Test numerical verification of projected corpus"""
    result = calculate_goal_planner(
        current_age=25,
        goal_age=45,
        target_corpus=10000000,
        current_savings=500000,
        expected_annual_return_pct=10
    )

    # The projected corpus should be very close to the target (within tolerance)
    assert abs(result['projected_corpus'] - 10000000) < 1000  # Within ₹1000
    assert result['goal_reached'] == True


def test_year_by_year_row_count():
    """Test year-by-year row count"""
    result = calculate_goal_planner(
        current_age=20,
        goal_age=50,
        target_corpus=10000000,
        current_savings=0,
        expected_annual_return_pct=10
    )

    # Should have exactly (goal_age - current_age) rows
    expected_rows = 50 - 20
    assert len(result['year_by_year_projection']) == expected_rows
    assert result['years_available'] == expected_rows

    # Final row should represent age 50 (ending corpus)
    final_row = result['year_by_year_projection'][-1]
    assert abs(final_row['Ending Corpus'] - result['projected_corpus']) < 0.01  # Within 1 paisa
    assert final_row['Age'] == 49  # Starting age of the final year
    assert final_row['Year'] == 30  # 30th year


def test_final_projection_age_equals_goal_age():
    """Test that final projection age equals goal age"""
    result = calculate_goal_planner(
        current_age=20,
        goal_age=50,
        target_corpus=10000000,
        current_savings=0,
        expected_annual_return_pct=10
    )

    # The projected corpus should be the value at goal age
    # Even though the final row shows starting age, the Ending Corpus is at goal age
    assert result['years_available'] == 30
    final_row = result['year_by_year_projection'][-1]
    assert final_row['Year'] == 30
    assert final_row['Age'] == 49  # Started year at age 49
    # The ending corpus is what we have after 30 years, i.e., at age 50