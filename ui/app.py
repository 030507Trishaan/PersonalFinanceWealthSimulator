"""
Personal Finance & Wealth Simulator - Streamlit UI
Interfaces with the financial calculation engine to provide a user-friendly
web interface for wealth projection modeling.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from financial_engine.core.calculations import validate_inputs, calculate_projection
from v2_extensions.scenario_comparison import run_scenario_comparison
from goal_planner.goal_calculations import calculate_goal_planner
def format_inr(value):
    """Format a numeric value using Indian numbering, rounded to whole rupees."""
    if value is None:
        return "N/A"

    try:
        number = int(round(float(value)))
    except (TypeError, ValueError):
        return "N/A"

    sign = "-" if number < 0 else ""
    digits = str(abs(number))

    if len(digits) <= 3:
        formatted = digits
    else:
        last_three = digits[-3:]
        remaining = digits[:-3]
        groups = []

        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]

        if remaining:
            groups.insert(0, remaining)

        formatted = ",".join(groups + [last_three])

    return f"{sign}₹{formatted}"


# Page configuration
st.set_page_config(
    page_title="Personal Finance & Wealth Simulator",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional fintech dashboard styling
st.markdown(
    """
    <style>

    /* =========================================================
       PERSONAL FINANCE & WEALTH SIMULATOR
       Clean, Professional Fintech Dashboard
       ========================================================= */

    :root {
        /* Light warm-gray/off-white background */
        --bg: #F8F9FA;
        /* White content surfaces */
        --surface: #FFFFFF;
        /* Subtle surface variations */
        --surface-soft: #F1F3F5;
        --surface-muted: #E9ECEF;
        /* Subtle borders */
        --border: #DEE2E6;
        --border-light: #E9ECEF;
        /* Dark navy primary text */
        --text: #212529;
        /* Gray secondary text */
        --text-secondary: #6C757D;
        --text-muted: #ADB5BD;
        /* Restrained blue primary accent */
        --primary: #0D6EFD;
        --primary-hover: #0B5ED7;
        /* Very limited green for success */
        --success: #198754;
        /* More restrained warning */
        --warning: #FFC107;
        /* Standard danger */
        --danger: #DC3545;
        /* Dark navy sidebar */
        --sidebar: #212529;
        --sidebar-border: #343A40;
        --sidebar-text: #E9ECEF;
    }

    /* =========================
       GLOBAL
       ========================= */

    .stApp {
        background: var(--bg) !important;
    }

    .stApp,
    .stApp p,
    .stApp label,
    .stApp div {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                     Roboto, Helvetica, Arial, sans-serif;
    }

    .stApp > header {
        display: none;
    }

    [data-testid="stAppViewContainer"] {
        background: var(--bg) !important;
    }

    [data-testid="stMain"] {
        background: var(--bg) !important;
    }

    [data-testid="stMainBlockContainer"] {
        /* Comfortable visual width */
        max-width: 1200px !important;
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }

    /* =========================
       TYPOGRAPHY
       ========================= */

    h1 {
        color: var(--text) !important;
        font-size: 2rem !important; /* Reduced from 2.25rem */
        font-weight: 600 !important; /* Reduced from 750 */
        letter-spacing: -0.02em !important;
        line-height: 1.2 !important;
        margin-bottom: 1rem !important;
        margin-top: 0 !important;
    }

    h2 {
        color: var(--text) !important;
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        letter-spacing: -0.01em !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.75rem !important;
    }

    h3 {
        color: var(--text) !important;
        font-size: 1.25rem !important;
        font-weight: 500 !important;
        margin-top: 1.25rem !important;
        margin-bottom: 0.5rem !important;
    }

    .stMarkdown p {
        color: var(--text-secondary);
        line-height: 1.6;
        margin-bottom: 1rem;
    }

    /* =========================
       SIDEBAR
       ========================= */

    [data-testid="stSidebar"] {
        background: var(--sidebar) !important;
        border-right: 1px solid var(--sidebar-border) !important;
        width: 280px !important; /* Reasonable width */
    }

    [data-testid="stSidebar"] > div:first-child {
        background: var(--sidebar) !important;
        padding: 1.5rem 1.25rem !important;
    }

    [data-testid="stSidebar"] * {
        color: var(--sidebar-text) !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebar"] label {
        color: var(--sidebar-text) !important;
        font-size: 0.875rem !important; /* Readable */
        font-weight: 500 !important;
        margin-bottom: 0.5rem !important;
    }

    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] small {
        color: var(--text-muted) !important;
    }

    /* Sidebar navigation - proper controls */
    [data-testid="stSidebar"] [role="radiogroup"] {
        gap: 0.5rem !important;
        margin-bottom: 1.5rem !important;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label {
        background: transparent !important;
        border-radius: 6px !important;
        padding: 0.6rem 0.8rem !important;
        transition: all 0.15s ease !important;
        font-weight: 500 !important;
        border: 1px solid transparent !important;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: rgba(255, 255, 255, 0.05) !important;
        border-color: rgba(255, 255, 255, 0.1) !important;
    }

    [data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"] {
        background: var(--primary) !important;
        border-color: var(--primary) !important;
        color: white !important;
    }

    /* Sidebar radio button label visibility - light text on dark background */
    [data-testid="stSidebar"] div[data-testid="stRadio"] label,
    [data-testid="stSidebar"] div[data-testid="stRadio"] label p,
    [data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label,
    [data-testid="stSidebar"] div[data-testid="stRadio"] [role="radiogroup"] label p {
        color: #F2F4F7 !important;
        opacity: 1 !important;
        visibility: visible !important;
        -webkit-text-fill-color: #F2F4F7 !important;
    }

    /* Sidebar inputs */
    [data-testid="stSidebar"] input {
        background: rgba(255, 255, 255, 0.08) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 6px !important;
        font-size: 0.875rem !important;
        padding: 0.5rem 0.75rem !important;
    }

    [data-testid="stSidebar"] input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 1px var(--primary) !important;
        background: rgba(255, 255, 255, 0.1) !important;
    }

    [data-testid="stSidebar"] [data-baseweb="input"] {
        background: rgba(255, 255, 255, 0.08) !important;
        border-radius: 6px !important;
    }

    [data-testid="stSidebar"] button {
        border-radius: 6px !important;
        font-weight: 500 !important;
        transition: all 0.15s ease !important;
    }

    /* Sidebar primary button */
    [data-testid="stSidebar"] button[kind="primary"] {
        background: var(--primary) !important;
        border: 1px solid var(--primary) !important;
        color: white !important;
        font-weight: 500 !important;
        padding: 0.5rem 1rem !important;
    }

    [data-testid="stSidebar"] button[kind="primary"]:hover {
        background: var(--primary-hover) !important;
        border-color: var(--primary-hover) !important;
    }

    /* =========================
       INPUTS
       ========================= */

    .stNumberInput input,
    .stTextInput input {
        background: var(--surface) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        border-radius: 6px !important; /* Reduced from 8px */
        font-size: 0.875rem !important;
        padding: 0.5rem 0.75rem !important;
        transition: border-color 0.15s ease !important;
    }

    .stNumberInput input:focus,
    .stTextInput input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 1px var(--primary) !important;
    }

    /* =========================
       BUTTONS
       ========================= */

    .stButton > button {
        border-radius: 6px !important; /* Medium radius */
        border: 1px solid var(--border) !important;
        background: var(--surface) !important;
        color: var(--text) !important;
        font-weight: 500 !important;
        min-height: 2.5rem !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.15s ease !important;
        font-size: 0.875rem !important;
    }

    .stButton > button:hover {
        border-color: var(--primary) !important;
        color: var(--primary) !important;
        background: var(--surface-soft) !important;
    }

    .stButton > button[kind="primary"] {
        background: var(--primary) !important;
        border-color: var(--primary) !important;
        color: #FFFFFF !important;
    }

    .stButton > button[kind="primary"]:hover {
        background: var(--primary-hover) !important;
        border-color: var(--primary-hover) !important;
    }

    /* Secondary buttons */
    .stButton > button:not([kind="primary"]) {
        border-color: var(--border) !important;
        color: var(--text) !important;
    }

    .stButton > button:not([kind="primary"]):hover {
        border-color: var(--primary) !important;
        color: var(--primary) !important;
        background: var(--surface-soft) !important;
    }

    /* =========================
       METRIC / KPI CARDS
       ========================= */

    [data-testid="stMetric"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important; /* Subtle shadow */
        min-height: 90px !important;
        transition: box-shadow 0.15s ease !important;
    }

    [data-testid="stMetric"]:hover {
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1) !important;
    }

    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }

    [data-testid="stMetricValue"] {
        color: var(--text) !important;
        font-size: 1.75rem !important; /* Prominent but not enormous */
        font-weight: 600 !important;
        line-height: 1.2 !important;
    }

    [data-testid="stMetricDelta"] {
        font-size: 0.875rem !important;
        font-weight: 500 !important;
    }


    /* =========================
       ALERTS / STATUS
       ========================= */

    [data-testid="stAlert"] {
        border-radius: 6px !important;
        border-width: 1px !important;
        border-style: solid !important;
    }

    /* Success alert - subtle */
    [data-testid="stAlert"][kind="success"] {
        background-color: rgba(25, 135, 84, 0.08) !important;
        border-color: rgba(25, 135, 84, 0.2) !important;
        color: var(--success) !important;
    }

    /* Info alert - subtle */
    [data-testid="stAlert"][kind="info"] {
        background-color: rgba(13, 111, 253, 0.08) !important;
        border-color: rgba(13, 111, 253, 0.2) !important;
        color: var(--primary) !important;
    }

    /* Warning alert - subtle */
    [data-testid="stAlert"][kind="warning"] {
        background-color: rgba(255, 193, 7, 0.08) !important;
        border-color: rgba(255, 193, 7, 0.2) !important;
        color: #664D03 !important; /* Darker yellow for readability */
    }

    /* Error alert - subtle */
    [data-testid="stAlert"][kind="error"] {
        background-color: rgba(220, 53, 69, 0.08) !important;
        border-color: rgba(220, 53, 69, 0.2) !important;
        color: var(--danger) !important;
    }

    /* =========================
       DATA TABLES
       ========================= */

    [data-testid="stDataFrame"] {
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        overflow: hidden !important;
        background: var(--surface) !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
    }

    [data-testid="stDataFrame"] * {
        font-size: 0.875rem !important;
    }

    /* Table header */
    [data-testid="stDataFrame"] thead th {
        background-color: var(--surface-muted) !important;
        color: var(--text) !important;
        font-weight: 600 !important;
        border-bottom: 1px solid var(--border) !important;
        padding: 0.75rem 1rem !important;
    }

    /* Table body */
    [data-testid="stDataFrame"] tbody td {
        background-color: var(--surface) !important;
        color: var(--text) !important;
        padding: 0.75rem 1rem !important;
        border-top: 1px solid var(--border-light) !important;
    }

    /* Hover state */
    [data-testid="stDataFrame"] tbody tr:hover td {
        background-color: var(--surface-soft) !important;
    }

    /* =========================
       DIVIDERS
       ========================= */

    hr {
        border: none !important;
        border-top: 1px solid var(--border-light) !important;
        margin: 1.75rem 0 !important;
        opacity: 0.5 !important;
    }

    /* =========================
       PLOTLY CONTAINERS
       ========================= */

    [data-testid="stPlotlyChart"] {
        background: var(--surface) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        padding: 0.5rem !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05) !important;
        margin-bottom: 1.5rem !important;
    }

    /* =========================
       COLUMNS / SPACING
       ========================= */

    [data-testid="stHorizontalBlock"] {
        gap: 1.25rem !important;
        margin-bottom: 1.5rem !important;
    }

    /* =========================
       SECTION SPACING
       ========================= */

    .stSubheader {
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
        color: var(--text) !important;
    }

    .stMarkdown:not(:has(> div[data-testid="stMetric"])) {
        margin-bottom: 1.5rem !important;
    }

    /* =========================
       MOBILE RESPONSIVE
       ========================= */

    @media (max-width: 900px) {
        [data-testid="stSidebar"] {
            width: 240px !important;
        }

        [data-testid="stMainBlockContainer"] {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
            max-width: 100% !important;
        }

        h1 {
            font-size: 1.75rem !important;
        }

        h2 {
            font-size: 1.35rem !important;
        }

        [data-testid="stMetricValue"] {
            font-size: 1.5rem !important;
        }

        .stButton > button {
            width: 100% !important;
            margin-bottom: 0.5rem !important;
        }
    }

    @media (max-width: 600px) {
        [data-testid="stSidebar"] {
            width: 100% !important;
            height: 60px !important;
            border-right: none !important;
            border-bottom: 1px solid var(--sidebar-border) !important;
        }

        [data-testid="stSidebar"] > div:first-child {
            padding: 0.75rem !important;
        }

        [data-testid="stMainBlockContainer"] {
            padding-top: 1rem !important;
        }
    }

    /* Main content radio button label visibility - dark text on light background */
    .stMain div[data-testid="stRadio"] label,
    .stMain div[data-testid="stRadio"] label p,
    .stMain div[data-testid="stRadio"] [role="radiogroup"] label,
    .stMain div[data-testid="stRadio"] [role="radiogroup"] label p {
        color: #344054 !important;
        opacity: 1 !important;
        visibility: visible !important;
        -webkit-text-fill-color: #344054 !important;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# Title and description (without emojis)
st.title("Personal Finance & Wealth Simulator")
st.markdown(
    """
    Model how income, expenses, savings, returns, and inflation affect your wealth over time.
    """
)

# Sidebar for navigation and inputs
st.sidebar.header("Navigation")
app_mode = st.sidebar.radio(
    "Select Tool",
    ["Wealth Simulator", "Goal Planner"],
    index=0,
    help="Choose between wealth simulator and goal planner"
)

if app_mode == "Wealth Simulator":
    # Show wealth simulator inputs and logic
    st.sidebar.header("Financial Parameters")
    st.sidebar.markdown("Enter your financial assumptions below:")

    # Age inputs
    st.sidebar.subheader("Age Information")
    current_age = st.sidebar.number_input(
        "Current Age (years)",
        min_value=1,
        max_value=100,
        value=30,
        step=1,
        help="Your current age"
    )

    target_age = st.sidebar.number_input(
        "Target Age (years)",
        min_value=current_age + 1,
        max_value=100,
        value=35,
        step=1,
        help="Target age for projection (simulation runs to this age, exclusive)"
    )

    # Financial inputs
    st.sidebar.subheader("Financial Information")
    current_savings = st.sidebar.number_input(
        "Current Savings (₹)",
        min_value=0.0,
        value=10000.0,
        step=1000.0,
        help="Your starting wealth amount"
    )

    col1, col2 = st.sidebar.columns(2)
    with col1:
        monthly_income = st.sidebar.number_input(
            "Monthly Income (₹/mo)",
            min_value=0.0,
            value=5000.0,
            step=100.0,
            help="Your monthly income"
        )
    with col2:
        monthly_expenses = st.sidebar.number_input(
            "Monthly Expenses (₹/mo)",
            min_value=0.0,
            value=3000.0,
            step=100.0,
            help="Your monthly expenses"
        )

    # Calculate available savings for validation
    available_savings = monthly_income - monthly_expenses
    st.sidebar.caption(f"Available monthly savings: {format_inr(available_savings)}")

    monthly_investment_contribution = st.sidebar.number_input(
        "Monthly Investment Contribution (₹/mo)",
        min_value=0.0,
        max_value=max(0.0, available_savings),  # Dynamic max based on validation
        value=min(1000.0, max(0.0, available_savings)),
        step=50.0,
        help="Monthly amount dedicated to investments (must be ≤ available savings)"
    )

    # Growth rates and returns
    st.sidebar.subheader("Growth Rates & Returns")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        annual_income_growth_pct = st.sidebar.number_input(
            "Annual Income Growth (%/yr)",
            min_value=0.0,
            max_value=20.0,
            value=0.0,
            step=0.1,
            help="Annual percentage increase in income"
        )
        annual_expense_growth_pct = st.sidebar.number_input(
            "Annual Expense Growth (%/yr)",
            min_value=0.0,
            max_value=20.0,
            value=0.0,
            step=0.1,
            help="Annual percentage increase in expenses"
        )
    with col2:
        expected_annual_return_pct = st.sidebar.number_input(
            "Expected Annual Return (%/yr)",
            min_value=0.0,
            max_value=20.0,
            value=5.0,
            step=0.1,
            help="Expected annual investment return"
        )
        annual_inflation_pct = st.sidebar.number_input(
            "Annual Inflation Rate (%/yr)",
            min_value=0.0,
            max_value=10.0,
            value=2.0,
            step=0.1,
            help="Annual inflation rate"
        )

    # Validate inputs and calculate projection
    if st.sidebar.button("Calculate Projection", type="primary") or 'validated_inputs' in st.session_state:
        # Prepare inputs dictionary
        inputs = {
            'current_age': current_age,
            'target_age': target_age,
            'current_savings': current_savings,
            'monthly_income': monthly_income,
            'monthly_expenses': monthly_expenses,
            'monthly_investment_contribution': monthly_investment_contribution,
            'annual_income_growth_pct': annual_income_growth_pct,
            'annual_expense_growth_pct': annual_expense_growth_pct,
            'expected_annual_return_pct': expected_annual_return_pct,
            'annual_inflation_pct': annual_inflation_pct
        }

        try:
            # Validate inputs
            validated_inputs = validate_inputs(inputs)

            # Calculate projection
            projection = calculate_projection(validated_inputs)

            # Convert to DataFrame for easier handling
            df = pd.DataFrame(projection)

            # Store in session state for use in tabs
            st.session_state.validated_inputs = validated_inputs
            st.session_state.v1_projection = projection
            st.session_state.v1_df = df

            # Display success message
            st.success(f"✅ Projection calculated successfully for {len(projection)} years!")

            # Display summary metrics
            st.subheader("Projection Summary")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric(
                    label="Final Nominal Wealth",
                    value=format_inr(df['ending_nominal_wealth'].iloc[-1])
                )
            with col2:
                st.metric(
                    label="Final Real Wealth",
                    value=format_inr(df['inflation_adjusted_wealth'].iloc[-1])
                )
            with col3:
                st.metric(
                    label="Total Contributions",
                    value=format_inr(df['cumulative_contributions'].iloc[-1])
                )
            with col4:
                st.metric(
                    label="Total Investment Returns",
                    value=format_inr(df['cumulative_investment_returns'].iloc[-1])
                )

            # Run scenario comparison
            with st.spinner("Running scenario comparison..."):
                st.session_state.scenario_results = run_scenario_comparison(validated_inputs)

            # Create tabs for different views (removed Goal Planning tab)
            # Create radio buttons for different views (replacing tabs for reliable visibility)
            selected_view = st.radio(
                "View",
                ["Wealth Over Time", "Annual Details", "Data Export", "Scenario Comparison"],
                horizontal=True,
                label_visibility="collapsed"
            )

            # Render content based on selected view
            if selected_view == "Wealth Over Time":
                st.subheader("Wealth Projection Over Time")

                # Create wealth over time chart
                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=df['age'],
                    y=df['ending_nominal_wealth'],
                    mode='lines+markers',
                    name='Nominal Wealth',
                    line=dict(color="#1565C0", width=3),
                    hovertemplate='Age: %{x}<br>Nominal Wealth: ₹%{y:,.0f}<extra></extra>'
                ))

                fig.add_trace(go.Scatter(
                    x=df['age'],
                    y=df['inflation_adjusted_wealth'],
                    mode='lines+markers',
                    name='Inflation-Adjusted Wealth',
                    line=dict(color="#2E7D32", width=3),
                    hovertemplate='Age: %{x}<br>Real Wealth: ₹%{y:,.0f}<extra></extra>'
                ))

                fig.update_layout(
                    template="plotly_white",
                    font=dict(color="#172033"),
                    title=dict(
                        text="Wealth Projection: Nominal vs Inflation-Adjusted",
                        font=dict(color="#172033")
                    ),
                    xaxis_title="Age (years)",
                    yaxis_title="Wealth (₹)",
                    hovermode='x unified',
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=0.01,
                        font=dict(color="#172033")
                    ),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    xaxis=dict(
                        showgrid=False,
                        zeroline=False,
                        showline=True,
                        linewidth=1,
                        linecolor='#E0E0E0',
                        title=dict(font=dict(color="#172033")),
                        tickfont=dict(color="#172033")
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor='#E5E7EB',
                        gridwidth=1,
                        zeroline=False,
                        showline=True,
                        linewidth=1,
                        linecolor='#E0E0E0',
                        title=dict(font=dict(color="#172033")),
                        tickfont=dict(color="#172033")
                    )
                )

                st.plotly_chart(fig, use_container_width=True)

                # Additional charts
                col1, col2 = st.columns(2)

                with col1:
                    # Investment vs Cash wealth breakdown
                    fig2 = go.Figure()
                    fig2.add_trace(go.Scatter(
                        x=df['age'],
                        y=df['ending_invested_wealth'],
                        mode='lines',
                        name='Invested Wealth',
                        fill='tonexty',
                        line=dict(color='#9C27B0')  # purple for invested wealth (not gradient)
                    ))
                    fig2.add_trace(go.Scatter(
                        x=df['age'],
                        y=df['ending_cash_wealth'],
                        mode='lines',
                        name='Cash Wealth',
                        fill='tozeroy',
                        line=dict(color='#FF9800')  # orange for cash wealth
                    ))
                    fig2.update_layout(
                    template="plotly_white",
                    font=dict(color="#172033"),
                    title=dict(
                        text="Wealth Composition: Invested vs Cash",
                        font=dict(color="#172033")
                    ),
                    xaxis_title="Age (years)",
                    yaxis_title="Wealth (₹)",
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    xaxis=dict(
                        showgrid=False,
                        zeroline=False,
                        showline=True,
                        linewidth=1,
                        linecolor='#E0E0E0',
                        title=dict(font=dict(color="#172033")),
                        tickfont=dict(color="#172033")
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor='#E5E7EB',
                        gridwidth=1,
                        zeroline=False,
                        showline=True,
                        linewidth=1,
                        linecolor='#E0E0E0',
                        title=dict(font=dict(color="#172033")),
                        tickfont=dict(color="#172033")
                    )
                )
                    st.plotly_chart(fig2, use_container_width=True)

                with col2:
                    # Annual savings breakdown
                    fig3 = go.Figure()
                    fig3.add_trace(go.Bar(
                        x=df['age'],
                        y=df['annual_investment_contribution'],
                        name='Invested Savings',
                        marker_color='#1976D2'  # blue
                    ))
                    fig3.add_trace(go.Bar(
                        x=df['age'],
                        y=df['uninvested_cash_savings'],
                        name='Cash Savings',
                        marker_color='#90CAF9'  # light blue
                    ))
                    fig3.update_layout(
                    title=dict(
                        text="Annual Savings Breakdown",
                        font=dict(color="#172033")
                    ),
                    xaxis_title="Age (years)",
                    yaxis_title="Amount (₹/year)",
                    barmode='stack',
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    xaxis=dict(
                        showgrid=False,
                        zeroline=False,
                        showline=True,
                        linewidth=1,
                        linecolor='#E0E0E0',
                        title=dict(font=dict(color="#172033")),
                        tickfont=dict(color="#172033")
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor='#E5E7EB',
                        gridwidth=1,
                        zeroline=False,
                        showline=True,
                        linewidth=1,
                        linecolor='#E0E0E0',
                        title=dict(font=dict(color="#172033")),
                        tickfont=dict(color="#172033")
                    )
                )
                    st.plotly_chart(fig3, use_container_width=True)

            elif selected_view == "Annual Details":
                st.subheader("Annual Projection Details")

                # Format the dataframe for display
                display_df = df.copy()
                # Format currency columns
                currency_columns = [
                    'starting_invested_wealth', 'starting_cash_wealth',
                    'annual_income', 'annual_expenses', 'annual_savings',
                    'annual_investment_contribution', 'uninvested_cash_savings',
                    'investment_returns', 'ending_invested_wealth', 'ending_cash_wealth',
                    'ending_nominal_wealth', 'inflation_adjusted_wealth',
                    'cumulative_contributions', 'cumulative_investment_returns'
                ]

                for col in currency_columns:
                    display_df[col] = display_df[col].apply(lambda x: format_inr(x))

                # Reorder columns for better readability
                display_columns = [
                    'age',
                    'starting_invested_wealth', 'starting_cash_wealth',
                    'annual_income', 'annual_expenses', 'annual_savings',
                    'annual_investment_contribution', 'uninvested_cash_savings',
                    'investment_returns',
                    'ending_invested_wealth', 'ending_cash_wealth', 'ending_nominal_wealth',
                    'inflation_adjusted_wealth',
                    'cumulative_contributions', 'cumulative_investment_returns'
                ]

                st.dataframe(
                    display_df[display_columns],
                    use_container_width=True,
                    hide_index=True
                )

                # Show some key insights
                st.subheader("Key Insights")

                # Calculate some insights
                total_years = len(df)
                total_contributions = df['cumulative_contributions'].iloc[-1]
                total_returns = df['cumulative_investment_returns'].iloc[-1]
                final_nominal = df['ending_nominal_wealth'].iloc[-1]
                final_real = df['inflation_adjusted_wealth'].iloc[-1]

                insight_col1, insight_col2 = st.columns(2)

                with insight_col1:
                    st.info(f"""
                    **Investment Performance:**
                    - Total contributions over {total_years} years: ₹{total_contributions:,.0f}
                    - Total investment returns: ₹{total_returns:,.0f}
                    - Return on contributions: {(total_returns/total_contributions*100) if total_contributions > 0 else 0:.1f}%
                    """)

                with insight_col2:
                    wealth_growth = ((final_nominal - validated_inputs['current_savings']) / validated_inputs['current_savings'] * 100) if validated_inputs['current_savings'] > 0 else 0
                    real_growth = ((final_real - validated_inputs['current_savings']) / validated_inputs['current_savings'] * 100) if validated_inputs['current_savings'] > 0 else 0
                    inflation_impact = ((final_nominal - final_real) / final_nominal * 100) if final_nominal > 0 else 0

                    st.info(f"""
                    **Wealth Growth:**
                    - Nominal wealth growth: {wealth_growth:.1f}%
                    - Real wealth growth: {real_growth:.1f}%
                    - Inflation impact on wealth: {inflation_impact:.1f}%
                    """)

            elif selected_view == "Data Export":
                st.subheader("Export Data")

                # Prepare CSV data
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="Download Projection Data (CSV)",
                    data=csv_data,
                    file_name=f"wealth_projection_{current_age}_to_{target_age}.csv",
                    mime="text/csv"
                )

                # Show raw data option
                with st.expander("View Raw Data"):
                    st.json({
                        "inputs": validated_inputs,
                        "projection": projection
                    })

            elif selected_view == "Scenario Comparison":
                st.subheader("Scenario Comparison")
                if 'scenario_results' in st.session_state:
                    results = st.session_state.scenario_results

                    # Display scenario assumptions comparison
                    st.write("**Scenario Assumptions**")
                    assumption_data = results['summary']['assumption_comparison']
                    # Convert to DataFrame for display
                    assumption_df = pd.DataFrame(assumption_data)
                    st.dataframe(assumption_df.style.format("{:.2f}"))

                    # Display wealth comparison
                    st.write("**Projected Wealth Comparison**")
                    wealth_data = results['summary']['wealth_comparison']
                    wealth_df = pd.DataFrame(list(wealth_data.items()), columns=['Scenario', 'Ending Wealth'])
                    wealth_df['Ending Wealth'] = wealth_df['Ending Wealth'].apply(lambda x: format_inr(x) if x is not None else "N/A")
                    st.dataframe(wealth_df)

                    # Optional: create a chart for wealth over time for each scenario
                    st.write("**Wealth Over Time by Scenario**")
                    # We'll create a line chart showing the ending nominal wealth for each scenario over time
                    # We have the projection for each scenario in results['scenarios']
                    scenario_projections = results['scenarios']

                    # Prepare data for chart
                    chart_data = []
                    for scenario_name, scenario_info in scenario_projections.items():
                        if 'projection' in scenario_info and scenario_info['projection']:
                            projection_df = pd.DataFrame(scenario_info['projection'])
                            projection_df['Scenario'] = scenario_name
                            chart_data.append(projection_df)

                    if chart_data:
                        combined_df = pd.concat(chart_data, ignore_index=True)
                        # Create line chart for nominal wealth over time
                        fig = go.Figure()
                        for scenario_name in combined_df['Scenario'].unique():
                            scenario_df = combined_df[combined_df['Scenario'] == scenario_name]
                            fig.add_trace(go.Scatter(
                                x=scenario_df['age'],
                                y=scenario_df['ending_nominal_wealth'],
                                mode='lines',
                                name=scenario_name
                            ))
                        fig.update_layout(
                            title=dict(
                                text="Wealth Projection by Scenario",
                                font=dict(color="#172033")
                            ),
                            xaxis_title="Age (years)",
                            yaxis_title="Nominal Wealth (₹)",
                            hovermode='x unified',
                            plot_bgcolor='white',
                            paper_bgcolor='white',
                            xaxis=dict(
                                showgrid=False,
                                zeroline=False,
                                showline=True,
                                linewidth=1,
                                linecolor='#E0E0E0',
                                title=dict(font=dict(color="#172033")),
                                tickfont=dict(color="#172033")
                            ),
                            yaxis=dict(
                                showgrid=True,
                                gridcolor='#E5E7EB',
                                gridwidth=1,
                                zeroline=False,
                                showline=True,
                                linewidth=1,
                                linecolor='#E0E0E0',
                                title=dict(font=dict(color="#172033")),
                                tickfont=dict(color="#172033")
                            )
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No scenario projection data available for charting.")
                else:
                    st.info("Run the projection to see scenario comparison.")

        except ValueError as e:
            st.error(f"❌ Validation Error: {str(e)}")
        except Exception as e:
            st.error(f"❌ An error: {str(e)}")
    else:
        # Show instructions when no calculation has been run yet
        st.info("💡 Enter your financial parameters in the sidebar and click 'Calculate Projection' to see your wealth projection.")

        # Show example visualization
        st.subheader("Example Projection")
        st.markdown(
            '<p style="color: #344054;">- <strong>Nominal Wealth</strong>: Your future wealth in today\'s rupees</p>'
            '<p style="color: #344054;">- <strong>Inflation-Adjusted Wealth</strong>: Your future wealth\'s purchasing power in today\'s rupees</p>'
            '<p style="color: #344054;">- <strong>Wealth Composition</strong>: Breakdown between invested assets and cash holdings</p>'
            '<p style="color: #344054;">- <strong>Savings Breakdown</strong>: How much of your savings goes to investments vs. cash</p>',
            unsafe_allow_html=True
        )

else:  # Goal Planner mode
    # Show goal planner interface
    st.header("Goal Planner")
    st.markdown("Find out how much you need to invest to reach your target.")

    # Goal planner inputs in sidebar
    st.sidebar.header("Goal Parameters")

    current_age = st.sidebar.number_input(
        "Current Age",
        min_value=0,
        max_value=100,
        value=20,
        step=1,
        help="Your current age"
    )

    goal_age = st.sidebar.number_input(
        "Goal/Retirement Age",
        min_value=current_age + 1,
        max_value=100,
        value=50,
        step=1,
        help="Age by which to achieve the goal"
    )

    target_corpus = st.sidebar.number_input(
        "Target Corpus (₹)",
        min_value=0.0,
        value=10000000.0,
        step=100000.0,
        help="Desired future wealth amount"
    )

    current_savings = st.sidebar.number_input(
        "Current Savings/Investments (₹)",
        min_value=0.0,
        value=0.0,
        step=10000.0,
        help="Your current savings/investments amount"
    )

    expected_annual_return_pct = st.sidebar.number_input(
        "Expected Annual Return (%/yr)",
        min_value=0.0,
        max_value=20.0,
        value=10.0,
        step=0.1,
        help="Expected annual investment return"
    )

    if st.sidebar.button("Calculate Goal", type="primary"):
        # Store inputs in session state
        st.session_state.goal_inputs = {
            'current_age': current_age,
            'goal_age': goal_age,
            'target_corpus': target_corpus,
            'current_savings': current_savings,
            'expected_annual_return_pct': expected_annual_return_pct
        }

        # Calculate goal requirements
        with st.spinner("Calculating goal requirements..."):
            try:
                goal_result = calculate_goal_planner(
                    current_age=current_age,
                    goal_age=goal_age,
                    target_corpus=target_corpus,
                    current_savings=current_savings,
                    expected_annual_return_pct=expected_annual_return_pct
                )
                # Store goal result in session state for display
                st.session_state.goal_result = goal_result
            except Exception as e:
                st.error(f"Error calculating goal requirements: {str(e)}")

    # Display goal result if available
    if 'goal_result' in st.session_state:
        goal_result = st.session_state.goal_result

        # Display prominent results
        st.subheader("Goal Calculation Results")

        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label="Required Monthly Investment",
                value=format_inr(goal_result['required_monthly_investment'])
            )
        with col2:
            st.metric(
                label="Required Annual Investment",
                value=format_inr(goal_result['required_annual_investment'])
            )

        # Additional details
        st.subheader("Goal Details")

        detail_col1, detail_col2, detail_col3 = st.columns(3)
        with detail_col1:
            st.metric(
                label="Target Corpus",
                value=format_inr(goal_result['target_corpus'])
            )
        with detail_col2:
            st.metric(
                label="Projected Corpus",
                value=format_inr(goal_result['projected_corpus'])
            )
        with detail_col3:
            st.metric(
                label="Years Available",
                value=f"{int(goal_result['years_available'])} years"
            )

        # More details
        detail_col4, detail_col5, detail_col6 = st.columns(3)
        with detail_col4:
            st.metric(
                label="Total Future Contributions",
                value=format_inr(goal_result['total_future_contributions'])
            )
        with detail_col5:
            st.metric(
                label="Estimated Investment Returns",
                value=format_inr(goal_result['estimated_investment_returns'])
            )
        with detail_col6:
            surplus_deficit = "Surplus" if goal_result['surplus_or_shortfall'] >= 0 else "Shortfall"
            surplus_amount = abs(goal_result['surplus_or_shortfall'])
            st.metric(
                label=f"{surplus_deficit}",
                value=format_inr(surplus_amount)
            )

        # Status indicator
        if goal_result['goal_reached']:
            st.success("✅ Goal Reached")
        else:
            st.warning("⚠️ Goal Not Reached")

        st.markdown("*Your monthly investment is based on the assumptions above. Actual investment returns will vary.*")

        # Create and display chart
        if goal_result['year_by_year_projection']:
            st.subheader("Corpus Growth Projection")

            # Prepare data for chart
            projection_df = pd.DataFrame(goal_result['year_by_year_projection'])

            # Create line chart
            fig = go.Figure()

            # Projected corpus line
            fig.add_trace(go.Scatter(
                x=projection_df['Age'],
                y=projection_df['Ending Corpus'],
                mode='lines+markers',
                name='Projected Corpus',
                line=dict(color="#1565C0", width=3),
                hovertemplate='Age: %{x}<br>Projected Corpus: ₹%{y:,.0f}<extra></extra>'
            ))

            # Target corpus line (constant) - saffron as per requirement
            fig.add_trace(go.Scatter(
                x=projection_df['Age'],
                y=projection_df['Target Corpus'],
                mode='lines',
                name='Target Corpus',
                line=dict(color="#F9A825", width=2, dash='dash'),
                hovertemplate='Age: %{x}<br>Target Corpus: ₹%{y:,.0f}<extra></extra>'
            ))

            fig.update_layout(
                template="plotly_white",
                font=dict(color="#172033"),
                title=dict(
                    text="Corpus Growth: Projected vs Target",
                    font=dict(color="#172033")
                ),
                xaxis_title="Age (years)",
                yaxis_title='Corpus Amount (₹)',
                hovermode='x unified',
                legend=dict(
                    yanchor="top",
                    y=0.99,
                    xanchor="left",
                    x=0.01,
                    font=dict(color="#172033")
                ),
                plot_bgcolor='white',
                paper_bgcolor='white',
                xaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    showline=True,
                    linewidth=1,
                    linecolor='#E0E0E0',
                    title=dict(font=dict(color="#172033")),
                    tickfont=dict(color="#172033")
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='#E5E7EB',
                    gridwidth=1,
                    zeroline=False,
                    showline=True,
                    linewidth=1,
                    linecolor='#E0E0E0',
                    title=dict(font=dict(color="#172033")),
                    tickfont=dict(color="#172033")
                )
            )

            st.plotly_chart(fig, use_container_width=True)

        # Year-by-year projection table
        if goal_result['year_by_year_projection']:
            st.subheader("Year-by-Year Projection")

            # Format the dataframe for display
            display_df = pd.DataFrame(goal_result['year_by_year_projection'])

            # Format currency columns
            currency_columns = ['Starting Corpus', 'Annual Contributions', 'Investment Returns', 'Ending Corpus', 'Target Corpus']
            for col in currency_columns:
                display_df[col] = display_df[col].apply(lambda x: format_inr(x))

            # Reorder columns for better readability
            display_columns = ['Age', 'Year', 'Starting Corpus', 'Annual Contributions', 'Investment Returns', 'Ending Corpus', 'Target Corpus']

            st.dataframe(
                display_df[display_columns],
                use_container_width=True,
                hide_index=True
            )

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>Built with Streamlit • Personal Finance & Wealth Simulator v2.1</p>
    </div>
    """,
    unsafe_allow_html=True
)










