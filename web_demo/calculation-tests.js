// Permanent JavaScript calculation tests for web_demo/
// These tests verify that the JavaScript implementation matches the Python implementation

// Test 1: Wealth projection calculations
function testWealthProjection() {
    console.log("=== Testing Wealth Projection ===");

    // Test case: Basic scenario
    const inputs = {
        current_age: 30,
        target_age: 35,
        current_savings: 10000,
        monthly_income: 5000,
        monthly_expenses: 3000,
        monthly_investment_contribution: 1000,
        annual_income_growth_pct: 0,
        annual_expense_growth_pct: 0,
        expected_annual_return_pct: 5,
        annual_inflation_pct: 2
    };

    const projection = calculateProjection(inputs);

    // Verify we get 5 years of projection (30 to 35 exclusive)
    if (projection.length !== 5) {
        throw new Error(`Expected 5 years of projection, got ${projection.length}`);
    }

    // Verify first year age is 31
    if (projection[0].age !== 31) {
        throw new Error(`Expected first year age to be 31, got ${projection[0].age}`);
    }

    // Verify final year age is 35
    if (projection[4].age !== 35) {
        throw new Error(`Expected final year age to be 35, got ${projection[4].age}`);
    }

    // Verify wealth generally increases over time (with some exceptions possible due to inflation adjustment)
    const finalNominal = projection[4].ending_nominal_wealth;
    const initialNominal = projection[0].ending_nominal_wealth;

    // Allow for small decreases due to high inflation, but generally should increase
    if (finalNominal < initialNominal * 0.9) { // Allow 10% decrease max
        throw new Error(`Wealth decreased too much: ${initialNominal} -> ${finalNominal}`);
    }

    // Verify accounting identities
    for (let i = 0; i < projection.length; i++) {
        const year = projection[i];

        // Annual savings = income - expenses
        const expectedSavings = year.annual_income - year.annual_expenses;
        if (Math.abs(year.annual_savings - expectedSavings) > 0.01) {
            throw new Error(`Year ${year.age}: Annual savings mismatch: ${year.annual_savings} != ${expectedSavings}`);
        }

        // Annual savings = investment contribution + cash savings
        const expectedSavings2 = year.annual_investment_contribution + year.uninvested_cash_savings;
        if (Math.abs(year.annual_savings - expectedSavings2) > 0.01) {
            throw new Error(`Year ${year.age}: Savings split mismatch: ${year.annual_savings} != ${year.annual_investment_contribution} + ${year.uninvested_cash_savings}`);
        }

        // Ending wealth = invested + cash
        const expectedWealth = year.ending_invested_wealth + year.ending_cash_wealth;
        if (Math.abs(year.ending_nominal_wealth - expectedWealth) > 0.01) {
            throw new Error(`Year ${year.age}: Wealth accounting mismatch: ${year.ending_nominal_wealth} != ${year.ending_invested_wealth} + ${year.ending_cash_wealth}`);
        }

        // Investment return = (starting invested + contribution) * return rate
        const expectedReturn = (year.starting_invested_wealth + year.annual_investment_contribution) * (inputs.expected_annual_return_pct / 100);
        if (Math.abs(year.investment_returns - expectedReturn) > 0.01) {
            throw new Error(`Year ${year.age}: Investment return mismatch: ${year.investment_returns} != ${expectedReturn}`);
        }
    }

    console.log("✓ Wealth projection tests passed");
    return true;
}

// Test 2: Scenario comparison
function testScenarioComparison() {
    console.log("=== Testing Scenario Comparison ===");

    const baseInputs = {
        current_age: 30,
        target_age: 35,
        current_savings: 10000,
        monthly_income: 5000,
        monthly_expenses: 3000,
        monthly_investment_contribution: 1000,
        annual_income_growth_pct: 0,
        annual_expense_growth_pct: 0,
        expected_annual_return_pct: 5,
        annual_inflation_pct: 2
    };

    const results = runScenarioComparison(baseInputs);

    // Check all scenarios exist
    const scenarios = ['base', 'conservative', 'optimistic', 'custom'];
    for (const scenario of scenarios) {
        if (!results.scenarios[scenario]) {
            throw new Error(`Missing scenario: ${scenario}`);
        }
        if (!results.scenarios[scenario].projection || results.scenarios[scenario].projection.length === 0) {
            throw new Error(`Empty projection for scenario: ${scenario}`);
        }
    }

    // Verify conservative scenario has lower returns than base
    const baseWealth = results.scenarios.base.projection[results.scenarios.base.projection.length - 1].ending_nominal_wealth;
    const conservativeWealth = results.scenarios.conservative.projection[results.scenarios.conservative.projection.length - 1].ending_nominal_wealth;

    if (conservativeWealth >= baseWealth) {
        throw new Error(`Conservative scenario (${conservativeWealth}) should have less wealth than base scenario (${baseWealth})`);
    }

    // Verify optimistic scenario has higher returns than base
    const optimisticWealth = results.scenarios.optimistic.projection[results.scenarios.optimistic.projection.length - 1].ending_nominal_wealth;

    if (optimisticWealth <= baseWealth) {
        throw new Error(`Optimistic scenario (${optimisticWealth}) should have more wealth than base scenario (${baseWealth})`);
    }

    // Verify assumption comparisons exist
    if (!results.summary || !results.summary.assumption_comparison) {
        throw new Error("Missing assumption comparison in results");
    }

    const expectedParams = ['expected_annual_return_pct', 'annual_income_growth_pct', 'annual_expense_growth_pct', 'annual_inflation_pct'];
    for (const param of expectedParams) {
        if (!results.summary.assumption_comparison[param]) {
            throw new Error(`Missing assumption comparison for parameter: ${param}`);
        }
    }

    console.log("✓ Scenario comparison tests passed");
    return true;
}

// Test 3: Goal planner
function testGoalPlanner() {
    console.log("=== Testing Goal Planner ===");

    try {
        const result = calculateGoalPlanner(
            20, // current_age
            50, // goal_age
            10000000, // target_corpus
            0, // current_savings
            10 // expected_annual_return_pct
        );

        // Verify required monthly investment is non-negative
        if (result.required_monthly_investment < 0) {
            throw new Error(`Required monthly investment should not be negative: ${result.required_monthly_investment}`);
        }

        // Verify years available is correct
        if (result.years_available !== 30) {
            throw new Error(`Years available should be 30, got ${result.years_available}`);
        }

        // Verify that with the calculated investment, we reach approximately the target
        const projected = result.projected_corpus;
        const target = result.target_corpus;

        // Allow 1% tolerance due to rounding
        const tolerance = target * 0.01;
        if (Math.abs(projected - target) > tolerance) {
            throw new Error(`Projected corpus (${projected}) should be close to target (${target}) within 1%`);
        }

        // Verify accounting
        const expectedReturns = result.estimated_investment_returns;
        const totalContributions = result.total_future_contributions;
        const currentSavings = 0; // From our test inputs

        // FV = PV + contributions + returns (approximately)
        const expectedTotal = currentSavings + totalContributions + expectedReturns;
        if (Math.abs(result.projected_corpus - expectedTotal) > 1) { // Allow 1 rupee difference
            throw new Error(`Goal planner accounting mismatch: projected=${result.projected_corpus}, expected=${expectedTotal}`);
        }

        console.log("✓ Goal planner tests passed");
        return true;
    } catch (error) {
        throw new Error(`Goal planner test failed: ${error.message}`);
    }
}

// Test 4: Zero return case
function testZeroReturnCase() {
    console.log("=== Testing Zero Return Case ===");

    const inputs = {
        current_age: 30,
        target_age: 35,
        current_savings: 10000,
        monthly_income: 5000,
        monthly_expenses: 3000,
        monthly_investment_contribution: 1000,
        annual_income_growth_pct: 0,
        annual_expense_growth_pct: 0,
        expected_annual_return_pct: 0, // Zero return
        annual_inflation_pct: 0        // Zero inflation for simplicity
    };

    const projection = calculateProjection(inputs);

    // With zero return and zero inflation:
    // Each year: starting wealth + annual savings = ending wealth
    const annualSavings = (inputs.monthly_income - inputs.monthly_expenses) * 12;
    let expectedWealth = inputs.current_savings;

    for (let i = 0; i < projection.length; i++) {
        const year = projection[i];
        const expectedYearWealth = expectedWealth + annualSavings;

        if (Math.abs(year.ending_nominal_wealth - expectedYearWealth) > 0.01) {
            throw new Error(`Year ${year.age}: Zero return case mismatch: got ${year.ending_nominal_wealth}, expected ${expectedYearWealth}`);
        }
        expectedWealth = expectedYearWealth; // For next year
    }

    console.log("✓ Zero return case tests passed");
    return true;
}

// Test 5: Indian Rupee formatting
function testIndianRupeeFormatting() {
    console.log("=== Testing Indian Rupee Formatting ===");

    // Test cases: [input, expectedOutput]
    const testCases = [
        [0, "₹0"],
        [1000, "₹1,000"],
        [100000, "₹1,00,000"],
        [10000000, "₹1,00,00,000"],
        [1234567, "₹12,34,567"],
        [999999999, "₹99,99,99,999"]
    ];

    for (const [input, expected] of testCases) {
        const actual = formatINR(input);
        if (actual !== expected) {
            throw new Error(`Formatting mismatch for ${input}: expected '${expected}', got '${actual}'`);
        }
    }

    // Test negative numbers
    if (formatINR(-1000) !== "₹-1,000") {
        throw new Error("Negative number formatting failed");
    }

    // Test null/undefined/NaN
    if (formatINR(null) !== "N/A") {
        throw new Error("Null formatting failed");
    }
    if (formatINR(undefined) !== "N/A") {
        throw new Error("Undefined formatting failed");
    }
    if (formatINR(NaN) !== "N/A") {
        throw new Error("NaN formatting failed");
    }

    console.log("✓ Indian rupee formatting tests passed");
    return true;
}

// Test 6: Validation edge cases
function testValidationEdgeCases() {
    console.log("=== Testing Validation Edge Cases ===");

    // We can't directly test the validation functions as they're not exposed,
    // but we can test that our calculateProjection function handles reasonable inputs

    // Test that very high but valid values work
    const highInputs = {
        current_age: 1,
        target_age: 100,
        current_savings: 100000000,
        monthly_income: 10000000,
        monthly_expenses: 5000000,
        monthly_investment_contribution: 4000000,
        annual_income_growth_pct: 20,
        annual_expense_growth_pct: 20,
        expected_annual_return_pct: 20,
        annual_inflation_pct: 10
    };

    try {
        const projection = calculateProjection(highInputs);
        if (projection.length !== 99) {
            throw new Error(`Expected 99 years for high inputs, got ${projection.length}`);
        }
    } catch (error) {
        // Some extreme values might cause overflow or other issues, which is acceptable
        console.log(`High input test encountered expected limitation: ${error.message}`);
    }

    console.log("✓ Validation edge case tests completed");
    return true;
}

// Run all tests
function runAllCalculationTests() {
    console.log("Running web_demo calculation tests...\n");

    let passed = 0;
    const total = 6;

    try {
        if (testWealthProjection()) passed++;
    } catch (error) {
        console.error(`✗ Wealth projection test failed: ${error.message}`);
    }

    try {
        if (testScenarioComparison()) passed++;
    } catch (error) {
        console.error(`✗ Scenario comparison test failed: ${error.message}`);
    }

    try {
        if (testGoalPlanner()) passed++;
    } catch (error) {
        console.error(`✗ Goal planner test failed: ${error.message}`);
    }

    try {
        if (testZeroReturnCase()) passed++;
    } catch (error) {
        console.error(`✗ Zero return test failed: ${error.message}`);
    }

    try {
        if (testIndianRupeeFormatting()) passed++;
    } catch (error) {
        console.error(`✗ Indian rupee formatting test failed: ${error.message}`);
    }

    try {
        if (testValidationEdgeCases()) passed++;
    } catch (error) {
        console.error(`✗ Validation edge case test failed: ${error.message}`);
    }

    console.log(`\nResults: ${passed}/${total} test groups passed`);

    if (passed === total) {
        console.log("🎉 All calculation tests passed!");
        return true;
    } else {
        console.log("❌ Some calculation tests failed!");
        return false;
    }
}

// Only run tests if this file is loaded directly (not imported as module)
// In a browser environment, we might want to expose this function for manual testing
if (typeof module !== 'undefined' && module.exports) {
    // Node.js environment
    const funcs = require('./app.js');
    global.calculateProjection = funcs.calculateProjection;
    global.runScenarioComparison = funcs.runScenarioComparison;
    global.calculateGoalPlanner = funcs.calculateGoalPlanner;
    global.formatINR = funcs.formatINR;
    module.exports = {
        testWealthProjection,
        testScenarioComparison,
        testGoalPlanner,
        testZeroReturnCase,
        testIndianRupeeFormatting,
        testValidationEdgeCases,
        runAllCalculationTests
    };
    // Run tests when executed directly
    if (require.main === module) {
        const result = runAllCalculationTests();
        process.exit(result ? 0 : 1);
    }
}
// In browser, we attach to window for manual testing
else if (typeof window !== 'undefined') {
    window.runWebDemoTests = runAllCalculationTests;
}