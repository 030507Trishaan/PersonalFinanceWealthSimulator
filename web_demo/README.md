# Personal Finance & Wealth Simulator - Web Demo

This is a static, browser-based demo of the Personal Finance & Wealth Simulator that can be deployed through GitHub Pages. It reproduces the core functionality of the original Python/Streamlit implementation using pure HTML/CSS/JavaScript.

## Features

- **Wealth Simulator**: Projects wealth over time based on income, expenses, savings, investment returns, and inflation
- **Scenario Comparison**: Compares Base, Conservative, and Optimistic scenarios with customizable parameters
- **Goal Planner**: Calculates required monthly investment to reach a target corpus
- **Indian Rupee Formatting**: Displays currency values using Indian numbering system (₹1,00,000 format)
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Client-Side Only**: All calculations performed in the browser - no backend required

## Implementation Details

This static demo exactly replicates the financial logic from the original Python implementation:

### Wealth Simulation
- Annual income = monthly income × 12 × income growth factor
- Annual expenses = monthly expenses × 12 × expense growth factor
- Annual savings = income - expenses
- Annual investment contribution = fixed nominal monthly contribution × 12
- Uninvested cash savings = annual savings - annual investment contribution
- Investment return = (starting invested wealth + annual contribution) × return rate
- Ending invested wealth = starting invested wealth + annual contribution + investment return
- Ending cash wealth = starting cash wealth + uninvested cash savings
- Ending nominal wealth = ending invested wealth + ending cash wealth
- Real wealth = ending nominal wealth / (1 + inflation)^years elapsed

### Scenario Comparison
- Base: User-provided parameters
- Conservative: -2% return, -1% income growth, +1% expense growth, +1% inflation
- Optimistic: +2% return, +1% income growth, -1% expense growth, -1% inflation
- Custom: User-defined modifications to base parameters

### Goal Planner
Uses the future-value model:
```
FV = P × (1 + r/12)^(12n) + PMT × [((1 + r/12)^(12n) - 1) / (r/12)]
```
Where:
- P = current corpus
- r = annual return rate (decimal)
- n = number of years
- PMT = monthly payment (solved for)
- FV = target corpus

## Files

- `index.html`: Main HTML structure
- `styles.css`: Styling and responsive design
- `app.js`: All financial calculations and UI logic

## Browser Support

This demo works in all modern browsers:
- Chrome (recommended)
- Firefox
- Safari
- Edge
- Mobile browsers

## GitHub Pages Deployment

To deploy this demo to GitHub Pages:

1. Ensure the `web_demo/` directory exists at the root of your repository
2. Go to Repository Settings → Pages
3. Under "Source", select "Deploy from a branch"
4. Choose branch: `main` (or `master`)
5. Choose folder: `/web_demo`
6. Click "Save"

Your site will be published at: `https://username.github.io/repository-name/web_demo/`

## Validation

The demo includes the same input validation as the original Python implementation:
- Target age must be greater than current age
- Monetary inputs cannot be negative
- Monthly investment cannot exceed monthly surplus (income - expenses)
- Percentage inputs must be non-negative
- Proper error handling and user feedback

## Limitations

This is a static demo meant for demonstration purposes. Compared to the original Streamlit implementation:
- Charts are represented as placeholders (would require Chart.js or similar for full implementation)
- No data export functionality
- No persistent state between sessions
- Simplified UI interactions

However, all core financial calculations are identical to the original Python implementation.