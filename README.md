# Personal Finance & Wealth Simulator

A simple, professional financial planning simulator that models how a person's wealth changes over time based on income, expenses, savings/investment contributions, investment returns, and inflation.

## Project Status
This is a new project. Currently in the specification phase for V1.

## V1 Scope
Build a basic working wealth projection model with user inputs, year-by-year calculations, and visualization of nominal vs inflation-adjusted wealth.

## Directory Structure
```
PersonalFinanceWealthSimulator/
├── financial_engine/     # Financial calculation engine (separate from UI)
│   └── core/
├── tests/                # Unit and integration tests
│   ├── unit/
│   └── integration/
├── ui/                   # Streamlit web interface
├── SPECIFICATION.md      # Detailed V1 specification
├── README.md             # This file
└── requirements.txt      # Python dependencies
```

## Technology Stack
- Python 3.8+
- Streamlit for UI
- Pandas/Numpy for data handling (as needed)
- Plotly for charts
- Pytest for testing

## How to Contribute
See SPECIFICATION.md for detailed V1 requirements and methodology.