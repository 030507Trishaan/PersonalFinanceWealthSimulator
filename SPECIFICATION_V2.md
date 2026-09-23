# Personal Finance & Wealth Simulator - V2 Specification

## Project Overview
Extend the V1 Personal Finance & Wealth Simulator with two new capabilities:
1. **Scenario Comparison** - Compare multiple financial assumption scenarios side-by-side
2. **Goal Planning** - Calculate required savings to reach specific financial goals

V2 builds upon the V1 financial engine without changing its core methodology. All V1 behavior is preserved and frozen.

## V2 Scope Only
Add exactly two capabilities:
1. Scenario Comparison module
2. Goal Planning module

Both modules interface with the existing V1 financial_engine.core.calculations module without modifying it.

## V2 Financial Methodology (Extension of V1)

### Core Principles (Same as V1)
1. **Separation of Concerns**: Financial calculation engine is completely separate from UI and extension modules
2. **Year-by-Year Projection**: Calculate values for each year from current age+1 to target age (inclusive)
3. **Clear Distinction**: Maintain both nominal (not inflation-adjusted) and real (inflation-adjusted) wealth values
4. **Conservative Assumptions**: Use simple, understandable formulas appropriate for finance students
5. **Immutability**: V1 financial engine behavior is frozen and unchanged

### V2 Extension Principles
1. **Scenario Isolation**: Each scenario runs independently using the same V1 engine
2. **Goal Calculation Mathematical Consistency**: Goal planning uses the same V1 equations solved for different variables
3. **No V1 Modification**: Zero changes to financial_engine/core/calculations.py
4. **Reusable Logic**: Scenario and goal calculations leverage shared helper functions where appropriate
5. **Defensive Validation**: All generated inputs validated against V1 rules before engine use

### V1 Input Parameters (Unchanged)
- `current_age`: User's current age (years)
- `target_age`: Target age for projection (years) - simulation runs for ages [current_age+1, target_age]
- `current_savings`: Starting wealth amount (currency)
- `monthly_income`: Monthly income (currency/month)
- `monthly_expenses`: Monthly expenses (currency/month)
- `monthly_investment_contribution`: Monthly amount dedicated to investments (currency/month)
- `annual_income_growth_pct`: Annual percentage increase in income (%/year)
- `annual_expense_growth_pct`: Annual percentage increase in expenses (%/year)
- `expected_annual_return_pct`: Expected annual investment return (%/year)
- `annual_inflation_pct`: Annual inflation rate (%/year)

### V2 Extension 1: Scenario Comparison

#### Purpose
Compare multiple financial assumption scenarios side-by-side to understand how different assumptions impact wealth outcomes.

#### Supported Scenario Types
1. **Base Scenario** - User's current assumptions (from V1 inputs)
2. **Conservative Scenario** - More cautious assumptions (lower returns, lower income growth, higher expenses, higher inflation)
3. **Optimistic Scenario** - More aggressive assumptions (higher returns, higher income growth, lower expenses, lower inflation)
4. **User-Defined/Custom Scenario** - Fully customizable assumptions by user

#### Scenario Assumption Modifications
Scenarios modify only these V1 financial assumptions (all other inputs remain identical to base):
- `expected_annual_return_pct`: Modified by delta (percentage points)
- `annual_income_growth_pct`: Modified by delta (percentage points)
- `annual_expense_growth_pct`: Modified by delta (percentage points)
- `annual_inflation_pct`: Modified by delta (percentage points)

#### Conservative/Optimistic Delta Definitions
- **Conservative Scenario**: 
  - Investment return: base - 2.0 percentage points (clamped to ≥ 0%)
  - Income growth: base - 1.0 percentage point (clamped to ≥ 0%)
  - Expense growth: base + 1.0 percentage point (no upper clamp, but validated)
  - Inflation: base + 1.0 percentage point (no upper clamp, but validated)
- **Optimistic Scenario**:
  - Investment return: base + 2.0 percentage points (clamped to ≤ 20.0% maximum)
  - Income growth: base + 1.0 percentage point (no upper clamp, but validated)
  - Expense growth: base - 1.0 percentage point (clamped to ≥ 0%)
  - Inflation: base - 1.0 percentage point (clamped to ≥ 0%)

#### Custom Scenario Modifications
Users can modify any/all of the four parameters by specifying deltas, which are applied then clamped/validated:
- Return delta: [-20.0, +20.0] percentage points (result clamped to [0.0, 20.0]%)
- Income growth delta: [-20.0, +20.0] percentage points (result clamped to [0.0, 20.0]%)
- Expense growth delta: [-20.0, +20.0] percentage points (result clamped to [0.0, 20.0]%)
- Inflation delta: [-20.0, +20.0] percentage points (result clamped to [0.0, 20.0]%)

#### Comparison Outputs
For each scenario, calculate and display:
- Projected wealth over time (nominal and real)
- Ending wealth values (nominal and real)
- Clear display of assumptions used by each scenario
- Difference analysis between scenarios

#### Mathematical Implementation
Each scenario creates a separate input dictionary by:
1. Copying base inputs
2. Applying scenario-specific deltas to the four modifiable parameters
3. Clamping modified values to valid ranges ([0.0, 20.0]% for percentages)
4. Validating the resulting inputs against V1 validation rules
5. Calling the existing V1 `calculate_projection()` function with validated inputs

### V2 Extension 2: Goal Planning

#### Purpose
Calculate the required monthly investment contribution needed to reach a specific financial goal by a target age.

#### Goal Parameters
- `goal_name`: Descriptive name for the goal (string, non-empty)
- `target_amount`: Desired future wealth amount (currency, nominal value, non-negative)
- `target_age`: Age by which to achieve the goal (years, integer > current_age)
- `current_age`: Current age (years, shared from base inputs)

#### Goal Calculation Outputs
- `required_monthly_investment`: Monthly investment needed to reach goal (currency/month)
- `projected_wealth_at_target`: Wealth projected at target age with current assumptions (currency)
- `surplus_or_shortfall`: Projected wealth minus target amount (currency) (positive = surplus)
- `goal_reached`: Boolean indicating if goal is achieved with current assumptions (surplus_or_shortfall ≥ -0.01)
- `calculation_method`: String indicating method used ('direct', 'binary_search', or 'boundary')
- `iterations`: Integer count of iterations if applicable
- `convergence_tolerance`: Achieved tolerance in currency units

#### Mathematical Implementation (Financially Consistent with V1)
Goal planning solves the V1 projection equations for the unknown variable using numerical methods with verification:

1. **Initial Checks**:
   - If `target_age` ≤ `current_age`: Validation error (handled by validation layer)
   - If `target_amount` ≤ `current_savings`: Goal already met (contribution = 0.0, method = 'direct')

2. **Primary Approach (Binary Search for Contribution)**:
   - Search range: [0.0, max_contribution] where max_contribution = monthly_income - monthly_expenses
   - Tolerance: 0.01 currency units (absolute difference in ending wealth)
   - Maximum iterations: 100 (sufficient for 0.01 tolerance with reasonable ranges)
   - At each iteration:
     * Create test inputs with midpoint contribution
     * Validate inputs (ensures they're valid for V1 engine)
     * Call V1 `calculate_projection()`
     * Compare ending wealth at target_age to target_amount
     * Adjust search range based on comparison
   - After loop, verify solution by plugging result back into V1 engine
   - If verification fails within tolerance, use best effort result

3. **Boundary Solutions**:
   - If solution converges to 0.0 contribution: method = 'boundary'
   - If solution converges to max_contribution: method = 'boundary'

4. **Verification Step** (Critical):
   - After solving, create final inputs with solved contribution
   - Validate inputs
   - Call V1 `calculate_projection()`
   - Verify that |solved_wealth - target_amount| ≤ 0.01
   - If verification fails, return best result with warning flag

#### Key Mathematical Relationship
Goal planning uses the same fundamental equation as V1:
```
Ending Nominal Wealth = f(current_savings, monthly_income, monthly_expenses, 
                         monthly_investment_contribution, annual_income_growth_pct,
                         annual_expense_growth_pct, expected_annual_return_pct, 
                         annual_inflation_pct, current_age, target_age)
```

Where `f()` represents the V1 calculate_projection() function. Goal planning inverts this function to solve for monthly_investment_contribution given a target ending nominal wealth.

## V2 Project Structure
```
PersonalFinanceWealthSimulator/
├── financial_engine/
│   └── core/                 # Financial calculation engine (V1 - FROZEN)
│       ├── calculations.py   # V1 engine - NO CHANGES ALLOWED
│       ├── interface.md      # V1 interface documentation
│       └── __pycache__/
├── v2_extensions/            # V2-specific modules
│   ├── scenario_comparison.py
│   ├── goal_planning.py
│   ├── shared_utils.py       # Shared validation and helper functions
│   ├── __init__.py
│   └── __pycache__/
├── tests/
│   ├── unit/
│   │   ├── test_financial_engine.py      # V1 unit tests (UNCHANGED)
│   │   ├── test_scenario_comparison.py   # NEW: V2 scenario tests
│   │   ├── test_goal_planning.py         # NEW: V2 goal tests
│   │   └── test_shared_utils.py          # NEW: V2 shared utilities tests
│   ├── integration/
│   │   ├── test_integration_pipeline.py  # V1-MAY BE UPDATED ONLY FOR V2 UI INTEGRATION
│   │   ├── test_v2_scenario_integration.py  # NEW
│   │   ├── test_v2_goal_integration.py     # NEW
│   │   └── test_v2_combined_integration.py # NEW: Combined workflow tests
│   └── __pycache__/
├── ui/                       # Streamlit web interface
│   ├── app.py                # MAY BE UPDATED for V2 features
│   └── __pycache__/
├── SPECIFICATION.md          # V1 specification (frozen)
├── SPECIFICATION_V2.md       # V2 specification (this file)
├── README.md                 # Project overview and instructions
└── requirements.txt          # Python dependencies
```

## V2 Module Interfaces

### Shared Utilities (`v2_extensions/shared_utils.py`)
```python
def validate_and_clamp_scenario_inputs(base_inputs, modifications):
    """
    Apply modifications to base inputs, clamp to valid ranges, and validate.
    
    Parameters:
    -----------
    base_inputs : dict
        V1 validated inputs from user
    modifications : dict
        Modifications to apply to the four scenario parameters:
        - 'expected_annual_return_pct_delta': float
        - 'annual_income_growth_pct_delta': float
        - 'annual_expense_growth_pct_delta': float
        - 'annual_inflation_pct_delta': float
        
    Returns:
    --------
    tuple (dict, list):
        - Validated inputs ready for V1 financial engine
        - List of warnings generated during clamping/validation
        
    Raises:
    -------
    ValueError
        If modifications create inputs that fail V1 validation after clamping
    """
    
def validate_goal_inputs(goal_inputs):
    """
    Validate goal planning inputs according to V2 rules.
    
    Parameters:
    -----------
    goal_inputs : dict
        Dictionary containing:
        - 'goal_name': str
        - 'target_amount': float
        - 'target_age': int
        - Plus all base V1 input parameters
        
    Returns:
    --------
    dict
        Validated goal inputs
        
    Raises:
    -------
    ValueError
        For invalid goal inputs with descriptive messages
    """
    
def binary_search_contribution(base_inputs, target_amount, target_age):
    """
    Solve for monthly investment contribution using binary search.
    
    Parameters:
    -----------
    base_inputs : dict
        V1 validated inputs (excluding contribution which is solved for)
    target_amount : float
        Desired future wealth amount (nominal currency)
    target_age : int
        Age by which to achieve the goal
        
    Returns:
    --------
    dict
        {
            'required_monthly_investment': float,
            'projected_wealth_at_target': float,
            'surplus_or_shortfall': float,
            'calculation_method': str,
            'iterations': int,
            'convergence_tolerance': float,
            'verification_passed': bool
        }
    """
```

### Scenario Comparison Interface (`v2_extensions/scenario_comparison.py`)
```python
def create_scenario_inputs(base_inputs, scenario_type, custom_modifications=None):
    """
    Create input dictionary for a specific scenario based on base inputs.
    
    Parameters:
    -----------
    base_inputs : dict
        V1 validated inputs from user
    scenario_type : str
        One of: 'base', 'conservative', 'optimistic', 'custom'
    custom_modifications : dict, optional
        For custom scenario: modifications to apply (see shared_utils format)
        
    Returns:
    --------
    tuple (dict, list):
        - Modified inputs ready for V1 financial engine
        - List of warnings generated during processing
        
    Raises:
    -------
    ValueError
        If scenario_type is invalid or modifications create invalid inputs
    """
    
def run_scenario_comparison(base_inputs):
    """
    Run all four scenarios (base, conservative, optimistic, custom) and return results.
    
    Parameters:
    -----------
    base_inputs : dict
        V1 validated inputs from user
        
    Returns:
    --------
    dict
        {
            'scenarios': {
                'base': {
                    'inputs': dict,  # V1 inputs for base scenario
                    'projection': list  # Output from V1 calculate_projection(),
                    'warnings': list  # Any warnings from input processing
                },
                'conservative': {...},
                'optimistic': {...},
                'custom': {...}
            },
            'summary': {
                'wealth_comparison': dict,  # Ending wealth values for each scenario
                'assumption_comparison': dict  # Key assumption differences
            }
        }
    """
```

### Goal Planning Interface (`v2_extensions/goal_planning.py`)
```python
def calculate_goal_requirements(base_inputs, goal_name, target_amount, target_age):
    """
    Calculate the monthly investment needed to reach a financial goal.
    
    Parameters:
    -----------
    base_inputs : dict
        V1 validated inputs (current_age, target_age, etc. from base scenario)
    goal_name : str
        Descriptive name for the goal (non-empty)
    target_amount : float
        Desired future wealth amount (nominal currency, non-negative)
    target_age : int
        Age by which to achieve the goal (must be > current_age)
        
    Returns:
    --------
    dict
        {
            'goal_name': str,
            'target_amount': float,
            'target_age': int,
            'current_age': int,
            'required_monthly_investment': float,  # Monthly contribution needed
            'projected_wealth_at_target': float,   # Wealth with current assumptions
            'surplus_or_shortfall': float,         # target - projected 
            'goal_reached': bool,                  # True if surplus_or_shortfall >= -0.01
            'calculation_method': str,             # 'direct', 'binary_search', or 'boundary'
            'iterations': int                      # Number of iterations if applicable
            'verification_passed': bool            # Whether solution verified within tolerance
        }
        
    Raises:
    -------
    ValueError
        If inputs are invalid or goal is mathematically impossible
    """
```

## V2 Validation Rules (Extensions to V1)

### Shared Validation Principles
1. **Input Integrity**: All inputs to V1 engine must pass V1 validation
2. **Scenario Safety**: Modified inputs must remain economically reasonable
3. **Goal Feasibility**: Goals must be plausibly achievable or clearly identified as impossible
4. **Clear Error Messages**: All validation failures provide actionable feedback

### Scenario Comparison Validation
1. All base inputs must pass V1 validation (via shared validation)
2. Scenario modifications are clamped to [0.0, 20.0]% range for all parameters
3. After clamping, inputs validated against V1 validation rules
4. Custom scenario modifications limited to ±20.0 percentage points per parameter
5. Warnings generated when clamping occurs are returned to caller

### Goal Planning Validation
1. All base inputs must pass V1 validation (via shared validation)
2. `goal_name` must be non-empty string (after stripping whitespace)
3. `target_amount` must be non-negative (≥ 0)
4. `target_age` must be integer > `current_age` (validated separately)
5. Maximum reasonable target amount: 100 × (current_savings + 50 years of max contribution)
   - Prevents astronomical targets that would cause numerical issues
6. If target_amount is unverifiable (solution doesn't converge), returns best effort with warning

## V2 Specific Assumptions

### Scenario Comparison Assumptions
1. **Base Scenario**: Uses user-provided inputs exactly as entered
2. **Conservative Scenario**: 
   - Investment return: max(0.0, base_return - 2.0)
   - Income growth: max(0.0, base_income_growth - 1.0)
   - Expense growth: base_expense_growth + 1.0 (validated ≤ 20.0)
   - Inflation: base_inflation + 1.0 (validated ≤ 20.0)
3. **Optimistic Scenario**:
   - Investment return: min(20.0, base_return + 2.0)
   - Income growth: base_income_growth + 1.0 (validated ≤ 20.0)
   - Expense growth: max(0.0, base_expense_growth - 1.0)
   - Inflation: max(0.0, base_inflation - 1.0)
4. **Custom Scenario**: 
   - Each parameter: base_value + user_delta, clamped to [0.0, 20.0]%
   - User deltas limited to [-20.0, +20.0] percentage points
5. All scenarios share identical non-modified inputs (current_savings, monthly_income, etc.)
6. All generated scenario inputs validated against V1 rules before engine use

### Goal Planning Assumptions
1. Solves for monthly investment contribution using V1 projection model
2. Assumes goal target amount is nominal future value (not inflation-adjusted)
3. Uses same timing assumptions as V1 (contributions at beginning of year, end-of-year values)
4. Binary search tolerance: 0.01 currency units in ending wealth
5. Maximum iterations: 100 (prevents infinite loops)
6. If verification fails, returns best result with verification_passed = False
7. Preserves all V1 behavioral assumptions (wealth separation, inflation treatment, etc.)

## Boundary Conditions (V2 Extensions)

### Scenario Comparison Boundary Conditions
1. When base parameters are at 0% and negative deltas applied: clamped to 0.0%
2. When base parameters are at 20.0% and positive deltas applied: clamped to 20.0% (where applicable)
3. Conservative scenario never produces higher returns/growth than base after clamping
4. Optimistic scenario never produces lower returns/growth than base after clamping
5. All scenarios produce valid V1 inputs that pass validation
6. Warnings returned when clamping occurs at boundaries

### Goal Planning Boundary Conditions
1. When target_age = current_age + ε (approaching current_age): requires infinite contribution → treated as unreachable
2. When target_age = current_age: validation error (handled in validation layer)
3. When target_amount ≤ current_savings: required contribution = 0.0, method = 'direct'
4. When target_amount is unreachable even with maximum contribution: 
   - Returns max_contribution, projected wealth at target, negative surplus, method = 'boundary'
5. When required contribution calculation converges to boundary (0.0 or max):
   - method = 'boundary', verification performed on boundary value
6. When binary search fails to converge within iteration limit:
   - Returns best estimate after max iterations, verification_passed = False
7. When time horizon is very small (1-2 years): uses same algorithm, verification ensures accuracy

## Explicitly OUT of Scope for V2
- Monte Carlo simulations (still future phase)
- Probabilistic scenario analysis
- Tax modeling
- Social Security or pension modeling
- Estate planning
- Debt modeling beyond expenses
- Real investment data integration
- Authentication, databases, or user accounts
- AI features or financial product recommendations
- Changes to financial_engine/core/calculations.py (FROZEN)
- Modification of V1 test files (must remain unchanged for regression testing)

## Dependencies (Same as V1)
- Python 3.8+
- Streamlit (for UI)
- Pandas/Numpy (for data handling)
- Plotly (for charts)
- Pytest (for testing)

## Test Plan (V2 Extensions)

### Unit Tests Will Cover:

#### 1. Shared Utilities Tests
- Input clamping at boundaries (0%, 20%)
- Validation of economically nonsensical combinations
- Custom scenario modification limits
- Goal input validation (empty names, negative amounts, invalid ages)
- Binary search convergence properties
- Edge case handling in shared functions

#### 2. Scenario Comparison Tests
- Input creation for all scenario types
- Boundary condition handling (0% base values, 20% base values)
- Assumption modification correctness and clamping
- Input validation preservation and warning generation
- Conservative/Optimistic scenario relationship preservation
- Custom scenario with various user modifications
- Edge cases: all parameters at extremes, conflicting modifications

#### 3. Goal Planning Tests
- Direct calculation verification (goal already met: target_amount ≤ current_savings)
- Boundary condition handling (goal unreachable, zero time horizon approaches)
- Mathematical consistency: plug solved contribution back into V1 engine
- Binary search convergence testing with known tolerances
- Iteration counting and method reporting accuracy
- Verification pass/fail conditions
- Input validation and error handling
- Edge cases: very long time horizons, high inflation, zero/negative growth

### Integration Tests Will Verify:

#### 1. Scenario Comparison Integration
- Complete pipeline from base inputs to scenario results
- Data formatting for UI consumption (standardized output format)
- Chart data generation accuracy and completeness
- Regression testing against V1 baseline (V1 outputs unchanged)
- Warning propagation and handling
- Combined scenario analysis (wealth comparisons, assumption differences)

#### 2. Goal Planning Integration
- Complete pipeline from goal inputs to requirement outputs
- UI data preparation compatibility (standardized goal result format)
- Integration with V1 engine (uses unchanged calculate_projection)
- Verification of solution accuracy within tolerance
- Boundary condition handling in full pipeline
- Performance characteristics (reasonable solution time)

#### 3. Combined V2 Integration
- Using scenario results to inform goal planning (optional workflow)
- Using goal results to modify scenario assumptions (optional workflow)
- End-to-end workflow testing with realistic user journeys
- Cross-feature data consistency and compatibility

### Regression Test Requirements
- **Mandatory**: All V1 unit and integration tests must continue to pass unchanged
- **Isolation**: V2 tests must use separate test fixtures/data from V1 tests
- **Performance**: V2 implementation must not degrade V1 calculation speed by >10%
- **Import Safety**: V2 modules must not modify sys.path or global imports affecting V1
- **Test Protection**: V1 test files (tests/unit/test_financial_engine.py, tests/integration/test_integration_pipeline.py) must NOT be modified

## Formulas Summary (V2 Extensions)

### Scenario Comparison Formulas
For each scenario type and parameter, compute modified value:
```
raw_value = base_value + scenario_delta
clamped_value = min(max(raw_value, 0.0), 20.0)  # For return and income growth
clamped_value = min(max(raw_value, 0.0), 20.0)  # For expense growth and inflation (no negatives allowed)
```

Where scenario_delta is:
- Conservative: [-2.0, -1.0, +1.0, +1.0] for [return, income_growth, expense_growth, inflation]
- Optimistic: [+2.0, +1.0, -1.0, -1.0] for [return, income_growth, expense_growth, inflation]
- Custom: [user_return_delta, user_income_delta, user_expense_delta, user_inflation_delta]
  with each user_delta clamped to [-20.0, +20.0] before application

### Goal Planning Formulas
Use binary search to solve:
```
find contribution ∈ [0.0, max_contribution] such that:
|V1_projection(base_inputs_with_contribution)[target_year_index]['ending_nominal_wealth'] - target_amount| ≤ 0.01
```

Where:
- `max_contribution` = monthly_income - monthly_expenses (from validated inputs)
- `target_year_index` = target_age - current_age - 0 (adjusting for 0-based indexing and end-of-year values)
- `V1_projection()` is the existing calculate_projection() function
- Solution verified by plugging result back into V1 engine and checking tolerance

## V2 Compatibility Guarantee
1. **Zero V1 Changes**: financial_engine/core/calculations.py remains identical to V1
2. **Backward Compatibility**: All V1 inputs, outputs, and behavior preserved exactly
3. **Extension Isolation**: V2 modules only import and use V1 engine, never modify it
4. **Test Contract**: All V1 unit and integration tests must continue to pass unchanged (verified in CI)
5. **UI Separation**: V2 modules provide data structures to UI, UI handles presentation logic
6. **Fixture Isolation**: V2 tests use separate test data from V1 tests to prevent interference