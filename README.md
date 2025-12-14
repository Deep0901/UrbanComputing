# ⚡ Energy Price & Consumption Explainability Dashboard

A dual-explanation system research tool that compares **numerical machine learning explanations** with **natural language fuzzy reasoning** for energy market price predictions.

## 🎯 Project Overview

This dashboard demonstrates an innovative approach to AI explainability by presenting two complementary explanation methods:

- **Method A (Numerical)**: Statistical metrics, feature importance, and prediction error analysis using Linear Regression
- **Method B (Linguistic)**: Natural language explanations powered by fuzzy logic and real-time ENTSOE market context

The tool is designed for researchers and students to evaluate which explanation method is more effective for understanding energy price dynamics.

## ✨ Key Features

- **Dual Explanation System**: Side-by-side comparison of numerical vs. linguistic explanations
- **Multiple Data Sources**:
  - Pre-loaded sample data (7 days)
  - CSV upload capability
  - Real-time ENTSOE Transparency Platform API integration
- **Advanced Feature Engineering**: 
  - Cyclical encoding for temporal features
  - Peak hour detection
  - Energy consumption transformations
- **Fuzzy Logic Reasoning**: 
  - Natural language categorization of prices and consumption
  - Market trend analysis
  - Contextual insights from real-time energy data
- **Evaluation System**: Built-in student feedback collection form with export capability
- **Interactive Dashboard**: Real-time visualizations and metrics using Streamlit

## 📊 Technology Stack

| Component | Technology |
|-----------|-----------|
| **Web Framework** | Streamlit 1.50.0 |
| **ML Models** | Scikit-learn 1.7.2 |
| **Fuzzy Logic** | Scikit-fuzzy 0.5.0 |
| **Data Processing** | Pandas 2.3.3, NumPy 2.3.4 |
| **Data Visualization** | Matplotlib, Altair |
| **API Integration** | Requests 2.32.5 (ENTSOE) |
| **XML Parsing** | lxml 6.0.2 |
| **Environment Management** | Python-dotenv 1.2.1 |
| **Network Analysis** | NetworkX 3.5 |

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Virtual environment (recommended)
- ENTSOE API token (for real-time data) - Get it at: https://transparency.entsoe.eu/

### Installation

1. **Clone and navigate to project directory**:
   ```bash
   cd energy-explain
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/macOS
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your ENTSOE API token
   ```

5. **Generate sample data** (optional):
   ```bash
   python data/generate_sample_data.py
   ```

6. **Run the application**:
   ```bash
   streamlit run app.py
   ```

The dashboard will open at `http://localhost:8501`

## 📖 Usage Guide

### Step 1: Select Data Source
Choose from three options in the sidebar:
- **Sample Data**: Pre-loaded 7 days of hourly data
- **Upload CSV**: Provide your own dataset with columns: `datetime`, `energy_consumption`, `price`
- **Real-time ENTSOE Data**: Fetch live European energy market data (requires API token)

### Step 2: Train Model
Click "🚀 Train Model" to build the Linear Regression predictor with automated feature engineering.

### Step 3: View Explanations
Compare two methods side-by-side:
- **Method A**: Numerical analysis with metrics, feature importance, and prediction samples
- **Method B**: Linguistic explanations with fuzzy categorization and market context

### Step 4: Provide Feedback
Complete the evaluation form to help assess the effectiveness of each explanation method.

### Step 5: Export Results
Download all collected responses as CSV for further analysis.

## 🏗️ Project Structure

```
energy-explain/
├── app.py                          # Main Streamlit application
├── main.py                         # Entry point
├── debug.py                        # ENTSOE API debug utility
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── pyproject.toml                  # Project configuration
│
├── app/                            # Application modules
│   ├── __init__.py                # Package initialization
│   ├── entsoe_client.py           # ENTSOE API client
│   ├── predictor.py               # ML predictor model
│   ├── fuzzy_explainer.py         # Fuzzy logic engine
│   └── reason_extractor.py        # Market reasoning engine
│
├── data/                           # Data directory
│   ├── energy_data.csv            # Sample energy data
│   └── generate_sample_data.py    # Sample data generator
│
└── docs/                           # Documentation (optional)
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file with:
```env
ENTSOE_API_TOKEN=your_api_token_here
```

### ENTSOE Supported Countries
- Germany, France, Italy, Spain
- Netherlands, Belgium, Austria, Poland
- Switzerland, Czech Republic, Denmark, Sweden
- Norway, UK, Ireland, Portugal, Greece

## 📚 Core Modules

### `entsoe_client.py`
Handles all communication with the ENTSOE Transparency Platform API:
- Fetches day-ahead prices (A44)
- Fetches actual prices (A25)
- Fetches actual load data (A65)
- Parses XML responses
- Provides fallback synthetic data

**Key Methods**:
- `fetch_complete_dataset(country, days)`: Gets combined price + load data
- `get_market_context(country, days)`: Returns structured market context dictionary

### `predictor.py`
Linear Regression model with automated feature engineering:
- Temporal feature extraction (hour, day-of-week, month)
- Cyclical encoding for circular features
- Peak hour detection
- Energy consumption transformations
- Generates metrics, feature importance, and prediction samples

**Key Methods**:
- `train(df)`: Trains the model
- `get_metrics()`: Returns R², MAE, RMSE
- `get_feature_importance()`: Returns feature coefficients

### `fuzzy_explainer.py`
Fuzzy logic-based linguistic explanation system:
- Converts numerical values to linguistic categories
- Analyzes price and consumption trends
- Generates natural language explanations
- Provides color-coded status indicators

**Key Methods**:
- `analyze_data(df)`: Creates fuzzy categorization
- `generate_explanation(analysis)`: Produces natural language output

### `reason_extractor.py`
Contextual reasoning engine for market insights:
- Extracts price drivers from market data
- Identifies demand patterns
- Generates market interpretation narratives
- Links numerical data to real-world energy market factors

## 🧪 Testing

To run debug scripts:

```bash
# Test ENTSOE API connection
python debug.py

# Run main entry point
python main.py
```

## 📊 Dashboard Components

### Data Summary
- Total records count
- Average price and consumption
- Model R² score

### Dual Explanation Display
**Left Column (Method A)**:
- Model performance metrics (R², MAE, RMSE)
- Feature importance ranking
- Sample predictions vs actual values
- Error distribution statistics

**Right Column (Method B)**:
- Fuzzy linguistic explanation
- Current classification (price & consumption levels)
- Real-time market context
- Fuzzy inference rules

### Evaluation Form
Collects user feedback on:
- Preference between methods
- Helpfulness ratings
- Understandability scores
- Optional comments

## 🔗 API Integration

### ENTSOE Transparency Platform
- **Base URL**: https://web-api.tp.entsoe.eu/api
- **Authentication**: securityToken (free registration required)
- **Data Types**: Price, Load, Generation
- **Rate Limits**: Reasonable limits for research use

### Domain Codes
Each country has a unique domain code for API queries. The system maintains a comprehensive mapping for 17 European countries.

## 📈 Model Details

### Linear Regression
- **Target Variable**: Electricity price (€/MWh)
- **Feature Count**: 15 automated features
- **Split Ratio**: 80% train / 20% test
- **Random State**: 42 (for reproducibility)

### Feature Engineering
```
Temporal Features:
- hour, day_of_week, month, day_of_month
- hour_sin, hour_cos (cyclical)
- dow_sin, dow_cos (cyclical)
- month_sin, month_cos (cyclical)
- is_weekend
- is_peak_hour

Consumption Features:
- consumption
- consumption_squared
- consumption_log
```

## 🎓 Educational Use

This project is designed for:
- **Research**: Comparing explainability methods
- **Teaching**: Understanding ML models and fuzzy logic
- **Learning**: Real-world energy market analysis
- **User Studies**: Evaluating explanation effectiveness

## 🐛 Troubleshooting

### ENTSOE API Errors
- Verify your API token is valid
- Check that you're within rate limits
- Ensure country name is spelled correctly
- Try sample data if API is unavailable

### Model Training Issues
- Ensure data has required columns: `datetime`, `energy_consumption`, `price`
- Check data types (datetime should be datetime, prices should be numeric)
- Verify no NaN values in critical columns

### Streamlit Display Issues
- Clear browser cache
- Try incognito/private window
- Restart Streamlit with `streamlit run app.py --logger.level=debug`

## 📝 File Format

### CSV Input Format
```csv
datetime,energy_consumption,price
2024-01-01 00:00:00,450.5,65.23
2024-01-01 01:00:00,440.2,62.15
...
```

## 🤝 Contributing

For improvements or bug reports, please:
1. Check existing issues
2. Create a clear bug report or feature request
3. Follow the code style of existing modules
4. Add docstrings to new functions

## 📄 License

This project is for educational and research purposes.

## 👤 Author

Developed as a research tool for energy market explainability analysis.

## 🔗 Resources

- [ENTSOE Transparency Platform](https://transparency.entsoe.eu/)
- [Scikit-fuzzy Documentation](https://scikit-fuzzy.github.io/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Scikit-learn Models](https://scikit-learn.org/)

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the debug output: `python debug.py`
3. Check Streamlit logs for detailed errors

---

**⚡ Making Energy Markets More Explainable** | Dual Explanation System Research Tool
